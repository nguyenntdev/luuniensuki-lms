# -*- coding: utf-8 -*-
"""V5-T045: AR Fallback and Device Capability Checks Test Suite.

Wave W04, Slot A05 (Priority: P1, Classification: PRODUCTION_COMPLETION).

Audits and verifies:
1. AR capability checking & mobile performance budget telemetry:
   - Detects camera and WebXR capabilities.
   - Evaluates performance budget (RAM, connection, saveData, CPU cores).
   - Resolves appropriate inspection mode (WebXR AR, QuickLook, or 2D turntable/rubbing).
2. CRITICAL INVARIANT & NEGATIVE ABUSE TEST:
   - Denied camera permission (or 2D turntable fallback due to device/network constraints)
     MUST allow the learner to complete the 100% equivalent learning/inspection task.
   - Awards the exact same XP (+25 XP) and server-verified completion status.
   - Learners who deny camera are NEVER blocked, penalized, or degraded.
3. Server/database interaction:
   - POST /api/v1/imperial/inspections/complete
   - GET /api/v1/imperial/inspections/{target_slug}
   - Persistent database rows in `imperial_relic_inspections`.
   - Synchronizes with `user_progress` (hidden -> discovered) for motifs.
4. Anti-replay & Idempotency:
   - Idempotency key replay returns cached completion with 0 additional XP.
   - Repeated attempts by the same student on the same relic return already_completed=True and 0 additional XP.
5. Quality gates (Anti-abuse):
   - Inspection time < 3 seconds rejected with HTTP 400 (INSUFFICIENT_INSPECTION_TIME).
   - Zero angles and zero hotspots examined rejected with HTTP 400 (INCOMPLETE_INSPECTION_TASK).
6. Security & RBAC:
   - Unauthenticated requests rejected with HTTP 401.
   - Non-existent relic targets return HTTP 404 (TARGET_NOT_FOUND).
   - Guests attempting non-demo relics return HTTP 403 (FORBIDDEN_GUEST_ACCESS).
"""
from __future__ import annotations

import json
from pathlib import Path
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialSite,
    ImperialZone,
)
from backend.imperial_v51_models import (
    ImperialArtDetail,
    ImperialRelicInspection,
)
from backend.models import (
    Motif,
    MotifCategory,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        total_xp=0,
        current_streak=0,
        longest_streak=0,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_test_art_detail(db_session, slug: str = "ngai-vang-hoang-de") -> ImperialArtDetail:
    """Seed an imperial art detail for inspection testing."""
    zone = db_session.execute(
        select(ImperialZone).where(ImperialZone.content_scope == CONTENT_SCOPE_IMPERIAL)
    ).scalars().first()
    if not zone:
        zone = ImperialZone(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug="khu-dai-trieu",
            title_vi="Khu Vực Đại Triều Nghi",
            display_order=1,
            row_version=1,
        )
        db_session.add(zone)
        db_session.flush()

    site = db_session.execute(
        select(ImperialSite).where(ImperialSite.slug == "dien-thai-hoa")
    ).scalar_one_or_none()
    if not site:
        site = ImperialSite(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            zone_id=zone.id,
            slug="dien-thai-hoa",
            name_vi="Điện Thái Hòa",
            display_order=1,
            row_version=1,
        )
        db_session.add(site)
        db_session.flush()

    detail = db_session.execute(
        select(ImperialArtDetail).where(
            ImperialArtDetail.slug == slug,
            ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
    ).scalar_one_or_none()

    if not detail:
        detail = ImperialArtDetail(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            site_id=site.id,
            title="Ngai Vàng Triều Nguyễn tại Điện Thái Hòa",
            slug=slug,
            kind="carving",
            motif="Cửu Long tranh châu & Bát bửu mây lành",
            material="Gỗ quý dát vàng",
            technique="Chạm lộng sơn thếp",
            description_observation="Ngai vàng đặt uy nghiêm trên bệ gỗ tam cấp.",
            story_body="Ngai vàng được chế tác từ thời Gia Long.",
            story_type="documented_event",
            review_status="published",
            row_version=1,
        )
        db_session.add(detail)
        db_session.commit()
        db_session.refresh(detail)

    return detail


def _seed_test_motif(
    db_session,
    name: str = "Mặt trời (Nhật)",
    mesh_name: str = "relief_cao_nhat",
    is_demo: bool = True,
) -> tuple[Urn, Motif]:
    """Seed an urn and motif for progress synchronization testing."""
    urn = db_session.execute(
        select(Urn).where(Urn.slug == "cao-dinh")
    ).scalar_one_or_none()
    if not urn:
        urn = Urn(
            name="Cao Đỉnh",
            slug="cao-dinh",
            model_url="/models/cao-dinh.glb",
            display_order=1,
            is_demo=True,
        )
        db_session.add(urn)
        db_session.flush()

    motif = db_session.execute(
        select(Motif).where(Motif.mesh_name == mesh_name)
    ).scalar_one_or_none()
    if not motif:
        motif = Motif(
            urn_id=urn.id,
            name=name,
            category=MotifCategory.thien_van,
            mesh_name=mesh_name,
            pos_x=0.0,
            pos_y=0.0,
            pos_z=0.0,
            bounding_radius=0.1,
            is_active=True,
            is_demo=is_demo,
        )
        db_session.add(motif)
        db_session.commit()
        db_session.refresh(motif)

    return urn, motif


# ==============================================================================
# 1. Unauthenticated and Security Guardrail Tests
# ==============================================================================

def test_unauthenticated_inspection_rejected(client):
    """Unauthenticated call to /api/v1/imperial/inspections/complete must return HTTP 401."""
    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 15,
            "angles_inspected": ["front", "right"],
            "hotspots_examined": ["h1"],
        },
    )
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_non_existent_target_returns_404(client, db_session):
    """Submitting inspection for unknown target returns HTTP 404 (TARGET_NOT_FOUND)."""
    student = _create_user(db_session, "stu_404@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "non-existent-relic-xyz-999",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 10,
            "angles_inspected": ["front"],
        },
    )
    assert res.status_code == 404, f"Expected 404, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["error"]["code"] == "TARGET_NOT_FOUND"


def test_guest_role_forbidden_from_non_demo_target(client, db_session):
    """Guest users are rejected with HTTP 403 when inspecting non-demo relics."""
    guest = _create_user(db_session, "guest_user@school.edu", role=UserRole.guest)
    _login_user(client, guest.email)

    # Seed a non-demo motif
    _seed_test_motif(
        db_session,
        name="Long Mã Hà Đồ (Non-Demo)",
        mesh_name="relief_long_ma_non_demo",
        is_demo=False,
    )

    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "relief_long_ma_non_demo",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 12,
            "angles_inspected": ["front"],
        },
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["error"]["code"] == "FORBIDDEN_GUEST_ACCESS"


# ==============================================================================
# 2. Positive Flow & Negative Abuse Equivalence Tests
# ==============================================================================

def test_positive_inspection_with_camera_granted_awards_xp(client, db_session):
    """Positive test: WebXR AR inspection with camera granted awards 25 XP and records session."""
    _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
    student = _create_user(db_session, "stu_ar_granted@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "webxr_ar",
            "camera_permission_granted": True,
            "device_tier": "high_end_mobile",
            "time_spent_seconds": 25,
            "angles_inspected": ["front", "right", "back"],
            "hotspots_examined": ["h1", "h2"],
        },
    )
    assert res.status_code == 200, f"Inspection failed: {res.text}"
    data = res.json()

    assert data["success"] is True
    assert data["target_slug"] == "ngai-vang-hoang-de"
    assert data["inspection_mode"] == "webxr_ar"
    assert data["camera_permission_granted"] is True
    assert data["equivalent_learning_completed"] is True
    assert data["xp_awarded"] == 25
    assert data["already_completed"] is False
    assert "WebXR AR" in data["feedback"] or "Thực tế tăng cường" in data["feedback"]

    # Verify user state in DB
    db_session.refresh(student)
    assert student.total_xp == 25


def test_negative_abuse_denied_camera_permission_completes_equivalent_learning_task(client, db_session):
    """CRITICAL NEGATIVE TEST (V5-T045):
    A learner who denies camera permission (camera_permission_granted=False) or whose device
    forces 2D turntable fallback MUST complete the exact same equivalent learning task
    and receive the exact same 25 XP and completion status.
    """
    _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
    student = _create_user(db_session, "stu_cam_denied@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    # Student denied camera permission and completed inspection in turntable_2d mode
    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False, # CAMERA PERMISSION DENIED!
            "device_tier": "low_end_mobile",
            "time_spent_seconds": 20,
            "angles_inspected": ["front", "left", "back", "right"],
            "hotspots_examined": ["h1"],
        },
    )
    assert res.status_code == 200, f"Expected 200 despite denied camera, got: {res.text}"
    data = res.json()

    # Verify that equivalent learning completed is True and XP is identical to AR (+25)
    assert data["success"] is True
    assert data["target_slug"] == "ngai-vang-hoang-de"
    assert data["inspection_mode"] == "turntable_2d"
    assert data["camera_permission_granted"] is False
    assert data["equivalent_learning_completed"] is True
    assert data["xp_awarded"] == 25
    assert data["already_completed"] is False

    # Check user DB total_xp
    db_session.refresh(student)
    assert student.total_xp == 25

    # Check status endpoint
    status_res = client.get("/api/v1/imperial/inspections/ngai-vang-hoang-de")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["is_completed"] is True
    assert st_data["camera_permission_granted"] is False
    assert st_data["completed_mode"] == "turntable_2d"


# ==============================================================================
# 3. Anti-Replay and Idempotency Guardrail Tests
# ==============================================================================

def test_anti_replay_and_idempotency_prevents_duplicate_xp(client, db_session):
    """Repeated inspections on the same relic or with same idempotency key award 0 extra XP."""
    _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
    student = _create_user(db_session, "stu_replay@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    idemp_key = f"key-{uuid.uuid4().hex}"
    payload = {
        "target_slug": "ngai-vang-hoang-de",
        "inspection_mode": "turntable_2d",
        "camera_permission_granted": False,
        "time_spent_seconds": 15,
        "angles_inspected": ["front", "back"],
        "hotspots_examined": ["h1"],
        "idempotency_key": idemp_key,
    }

    # First attempt: succeeds, awards 25 XP
    res1 = client.post("/api/v1/imperial/inspections/complete", json=payload)
    assert res1.status_code == 200
    assert res1.json()["xp_awarded"] == 25
    assert res1.json()["already_completed"] is False

    db_session.refresh(student)
    assert student.total_xp == 25

    # Second attempt with same idempotency key: returns cached 0 XP
    res2 = client.post("/api/v1/imperial/inspections/complete", json=payload)
    assert res2.status_code == 200
    assert res2.json()["xp_awarded"] == 0
    assert res2.json()["already_completed"] is True

    # Third attempt without idempotency key but same target: returns 0 XP (anti-replay)
    payload_no_key = dict(payload)
    payload_no_key.pop("idempotency_key")
    res3 = client.post("/api/v1/imperial/inspections/complete", json=payload_no_key)
    assert res3.status_code == 200
    assert res3.json()["xp_awarded"] == 0
    assert res3.json()["already_completed"] is True

    # User XP remains capped at 25 XP
    db_session.refresh(student)
    assert student.total_xp == 25


# ==============================================================================
# 4. Quality Gate Tests (Superficial Click Rejection)
# ==============================================================================

def test_quality_gate_rejects_insufficient_time(client, db_session):
    """Inspecting for less than 3 seconds is rejected with HTTP 400 (INSUFFICIENT_INSPECTION_TIME)."""
    _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
    student = _create_user(db_session, "stu_speed@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 1, # Only 1s!
            "angles_inspected": ["front"],
        },
    )
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["error"]["code"] == "INSUFFICIENT_INSPECTION_TIME"


def test_quality_gate_rejects_zero_interaction(client, db_session):
    """Inspecting with 0 angles viewed and 0 hotspots scrutinized is rejected with HTTP 400."""
    _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
    student = _create_user(db_session, "stu_passive@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 20,
            "angles_inspected": [], # Empty!
            "hotspots_examined": [], # Empty!
        },
    )
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["error"]["code"] == "INCOMPLETE_INSPECTION_TASK"


# ==============================================================================
# 5. Motif Progression Synchronization Test
# ==============================================================================

def test_motif_progress_synchronization(client, db_session):
    """Inspecting a motif advances UserProgress from hidden to discovered."""
    urn, motif = _seed_test_motif(
        db_session,
        name="Mặt trời (Nhật)",
        mesh_name="relief_cao_nhat_sync",
        is_demo=True,
    )
    student = _create_user(db_session, "stu_motif_sync@school.edu", role=UserRole.learner)
    _login_user(client, student.email)

    # Initial UserProgress: None or hidden
    prog_before = db_session.execute(
        select(UserProgress).where(
            UserProgress.user_id == student.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()
    assert prog_before is None

    # Complete inspection via 2D turntable fallback
    res = client.post(
        "/api/v1/imperial/inspections/complete",
        json={
            "target_slug": "relief_cao_nhat_sync",
            "inspection_mode": "turntable_2d",
            "camera_permission_granted": False,
            "time_spent_seconds": 15,
            "angles_inspected": ["front", "back"],
        },
    )
    assert res.status_code == 200

    # UserProgress must now be discovered
    prog_after = db_session.execute(
        select(UserProgress).where(
            UserProgress.user_id == student.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()
    assert prog_after is not None
    assert prog_after.status == UnlockStatus.discovered
    assert prog_after.xp_earned == 25


# ==============================================================================
# 6. Frontend Contract & File Verification Test
# ==============================================================================

def test_frontend_ar_capabilities_and_fallback_contract():
    """Verify that frontend modules and components exist and export required contracts."""
    frontend_dir = REPO_ROOT / "frontend" / "src"

    # 1. ar-capabilities.ts
    lib_path = frontend_dir / "lib" / "imperial" / "ar-capabilities.ts"
    assert lib_path.exists(), f"Missing {lib_path}"
    lib_text = lib_path.read_text(encoding="utf-8")
    assert "checkWebXRSupport" in lib_text
    assert "checkCameraPermission" in lib_text
    assert "evaluateMobilePerformanceBudget" in lib_text
    assert "resolveInspectionMode" in lib_text
    assert "createEquivalentInspectionSession" in lib_text

    # 2. ARCapabilityGate.tsx
    gate_path = frontend_dir / "components" / "imperial" / "ar" / "ARCapabilityGate.tsx"
    assert gate_path.exists(), f"Missing {gate_path}"
    gate_text = gate_path.read_text(encoding="utf-8")
    assert "ARCapabilityGate" in gate_text
    assert "showConsentPrompt" in gate_text
    assert "handleRequestCamera" in gate_text
    assert "handleContinueWithTurntable" in gate_text

    # 3. RelicTurntableInspector.tsx
    inspector_path = frontend_dir / "components" / "imperial" / "ar" / "RelicTurntableInspector.tsx"
    assert inspector_path.exists(), f"Missing {inspector_path}"
    inspector_text = inspector_path.read_text(encoding="utf-8")
    assert "RelicTurntableInspector" in inspector_text
    assert "handleAngleChange" in inspector_text
    assert "handleCompleteInspection" in inspector_text
    assert "zoomLevel" in inspector_text
