# -*- coding: utf-8 -*-
"""V5-T096: Low-Bandwidth Printable / Offline Kit Test Suite.

Wave W09, Slot A06 (Priority: P2, Classification: NEW_PRODUCT_FEATURE).
Audits and verifies:
1. Low-Bandwidth Printable / Offline Kit Data & API:
   - GET /api/v1/imperial/offline-kit returns full offline kit bundle.
   - Includes verified primary source excerpts with rights citations (ĐNTL, Hội Điển, Nhất Thống Chí).
   - High-contrast 2D rubbings with disk existence verification and print-optimized CSS filters.
   - Scannable QR codes for offline verification and digital twin follow-up.
   - 100% paper-executable offline inspection tasks.
   - Verbatim audio guide transcripts eliminating streaming network bandwidth.
2. Negative Abuse Invariant & Equity Guarantee:
   - No AR, WebXR, camera permission, or smartphone is mandatory to complete learning assignments.
   - Submissions via paper_handout / offline_rubbing achieve 100% full credit (12/12 Rubric, +25 XP).
   - Any system penalty or gate for absence of AR strictly raises an equity violation.
3. Frontend and Mobile Component Parity:
   - frontend/src/components/imperial/print/ (PrintableFieldworkWorksheet, LowBandwidthOfflineKit, etc.)
   - mobile/lib/features/offline_kit/ (offline_kit_model.dart, low_bandwidth_kit_screen.dart, app_router.dart)
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.apischemas.relic_inspection import RelicInspectionCompleteRequest
from backend.errors import AppError
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
    ClassMember,
    Classroom,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
    LessonContent,
    User,
    UserRole,
)
from backend.security import hash_password
from backend.services import offline_kit_service, relic_inspection
from backend.services.offline_kit_service import (
    MONUMENT_RUBBINGS_MAP,
    STANDARD_4_SLUGS,
    build_offline_kit,
    validate_offline_submission_fairness,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
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


def _login_user(client: TestClient, email: str, password: str = "Password123!") -> dict:
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
        select(ImperialArtDetail).where(ImperialArtDetail.slug == slug)
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


# --------------------------------------------------------------------------- #
# 1. Backend Service & Endpoint Tests
# --------------------------------------------------------------------------- #

class TestLowBandwidthOfflineKitBackend:
    """Validates offline kit data structure, endpoints, rubbings, and transcripts."""

    def test_build_offline_kit_standard_4(self):
        kit = build_offline_kit(cluster_id="standard_4")

        assert kit.kit_id == "kit-low-bandwidth-standard_4"
        assert kit.zero_device_guarantee is True
        assert kit.paper_achievable_percent == 100
        assert kit.ar_or_smartphone_mandatory is False
        assert len(kit.stations) == 4

        slugs = [s.monument_slug for s in kit.stations]
        assert slugs == STANDARD_4_SLUGS

        for station in kit.stations:
            # Source excerpts within rights
            assert station.primary_source.source_title
            assert station.primary_source.citation
            assert "HMCC" in station.primary_source.rights_owner
            assert "CC BY" in station.primary_source.license

            # 2D rubbing asset with contrast CSS
            assert station.rubbing_asset.asset_url
            assert station.rubbing_asset.local_path
            assert "contrast" in station.rubbing_asset.high_contrast_css
            assert "HMCC" in station.rubbing_asset.rights_attribution

            # Offline inspection task
            assert station.offline_task.paper_achievable is True
            assert station.offline_task.ar_or_smartphone_required is False
            assert len(station.offline_task.checkpoints) >= 2
            assert station.offline_task.sketch_prompt_vi

            # Audio guide transcript (zero streaming)
            assert station.audio_transcript.script_text
            assert station.audio_transcript.narrator
            assert station.audio_transcript.duration_seconds > 0

            # QR code verification url
            assert station.qr_code_url.startswith("https://")

            # M-E-E samples
            assert station.mee_claim_sample_vi
            assert station.mee_evidence_sample_vi
            assert station.mee_uncertainty_sample_vi

        # Rubric dimensions (S1-S4)
        assert len(kit.rubric_dimensions) == 4
        dim_ids = [d["id"] for d in kit.rubric_dimensions]
        assert dim_ids == ["S1", "S2", "S3", "S4"]
        for dim in kit.rubric_dimensions:
            assert dim["paper_evaluable"] is True

        # Exit tickets
        assert len(kit.exit_ticket_questions) >= 2
        for et in kit.exit_ticket_questions:
            assert et["paper_only"] is True

    def test_build_offline_kit_all_16_monuments(self):
        kit = build_offline_kit(cluster_id="all_16")

        assert kit.kit_id == "kit-low-bandwidth-all_16"
        assert len(kit.stations) == 16
        for station in kit.stations:
            assert station.monument_slug
            assert station.monument_name_vi
            assert station.offline_task.paper_achievable is True
            assert station.offline_task.ar_or_smartphone_required is False
            assert station.audio_transcript.script_text

    def test_get_offline_kit_api_endpoint(self, client: TestClient):
        response = client.get("/api/v1/imperial/offline-kit?cluster_id=standard_4")
        assert response.status_code == 200
        data = response.json()

        assert data["kit_id"] == "kit-low-bandwidth-standard_4"
        assert data["zero_device_guarantee"] is True
        assert data["paper_achievable_percent"] == 100
        assert data["ar_or_smartphone_mandatory"] is False
        assert len(data["stations"]) == 4

        # Check first station structure
        st1 = data["stations"][0]
        assert st1["monument_slug"] == "ngo-mon"
        assert st1["primary_source"]["source_title"]
        assert st1["rubbing_asset"]["high_contrast_css"]
        assert st1["offline_task"]["paper_achievable"] is True
        assert st1["offline_task"]["ar_or_smartphone_required"] is False
        assert st1["audio_transcript"]["script_text"]

    def test_rubbing_assets_on_disk_and_integrity(self):
        """Verifies that 2D rubbing files referenced in the kit exist on disk with valid size."""
        for slug, meta in MONUMENT_RUBBINGS_MAP.items():
            rel_path = meta["local_path"]
            file_path = REPO_ROOT / rel_path
            assert file_path.is_file(), f"Missing rubbing file on disk: {file_path}"
            stat = file_path.stat()
            assert stat.st_size > 5000, f"Rubbing file too small ({stat.st_size} bytes): {file_path}"

            # Verify sha256 checksum if declared
            if meta.get("sha256"):
                hasher = hashlib.sha256()
                with open(file_path, "rb") as f:
                    hasher.update(f.read())
                assert hasher.hexdigest() == meta["sha256"], f"Checksum mismatch for {slug}"


# --------------------------------------------------------------------------- #
# 2. Negative Abuse Invariant: No AR or Smartphone Mandatory
# --------------------------------------------------------------------------- #

class TestNegativeAbuseZeroDeviceMandatory:
    """Verifies that no AR or smartphone is required to complete learning tasks."""

    def test_relic_inspection_succeeds_with_paper_handout_mode(self, db_session, client: TestClient):
        """CRITICAL: Student using paper_handout mode without camera receives full credit."""
        learner = _create_user(db_session, f"student_{uuid.uuid4().hex[:6]}@edu.vn", UserRole.learner)
        _seed_test_art_detail(db_session, "ngai-vang-hoang-de")
        _login_user(client, learner.email)

        # Inspect using paper_handout mode (zero camera, zero AR)
        req_payload = {
            "target_slug": "ngai-vang-hoang-de",
            "inspection_mode": "paper_handout",
            "camera_permission_granted": False,
            "device_tier": "paper_only",
            "time_spent_seconds": 15,
            "angles_inspected": ["front_rubbing", "top_sketch"],
            "hotspots_examined": ["dragon_engraving_rubbing"],
            "idempotency_key": f"idem_paper_{uuid.uuid4().hex[:12]}",
        }

        res = client.post("/api/v1/imperial/inspections/complete", json=req_payload)
        assert res.status_code == 200, f"Inspection failed: {res.text}"
        data = res.json()

        assert data["success"] is True
        assert data["equivalent_learning_completed"] is True
        assert data["xp_awarded"] == 25
        assert data["camera_permission_granted"] is False
        assert data["inspection_mode"] == "paper_handout"

        # Verify DB row persistence
        row = db_session.execute(
            select(ImperialRelicInspection).where(
                ImperialRelicInspection.user_id == learner.id,
                ImperialRelicInspection.target_slug == "ngai-vang-hoang-de",
            )
        ).scalar_one()

        assert row.inspection_mode == "paper_handout"
        assert row.camera_permission_granted is False
        assert row.xp_awarded == 25

    def test_relic_inspection_succeeds_with_offline_rubbing_mode(self, db_session, client: TestClient):
        """Student using offline_rubbing receives identical full marks and XP."""
        learner = _create_user(db_session, f"student_rubbing_{uuid.uuid4().hex[:6]}@edu.vn", UserRole.learner)
        _login_user(client, learner.email)

        req_payload = {
            "target_slug": "cao-dinh",
            "inspection_mode": "offline_rubbing",
            "camera_permission_granted": False,
            "device_tier": "desktop",
            "time_spent_seconds": 20,
            "angles_inspected": ["high_contrast_rubbing_plate"],
            "hotspots_examined": ["motif_rubbing_01"],
            "idempotency_key": f"idem_rubbing_{uuid.uuid4().hex[:12]}",
        }

        res = client.post("/api/v1/imperial/inspections/complete", json=req_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["equivalent_learning_completed"] is True
        assert data["xp_awarded"] == 25

    def test_equity_violation_when_penalizing_non_ar_students(self):
        """Any attempt to penalize students for lacking AR or camera must be strictly blocked."""
        # 1. Fair submission passes
        fair_res = validate_offline_submission_fairness({
            "submission_medium": "paper_handout",
            "camera_permission_granted": False,
            "has_smartphone": False,
        })
        assert fair_res["status"] == "fairness_verified"
        assert fair_res["eligible_for_full_score"] is True
        assert fair_res["max_score_accessible"] == 12
        assert fair_res["xp_accessible"] == 25

        # 2. Penalizing student for no camera raises equity violation
        with pytest.raises(AppError) as exc_info:
            validate_offline_submission_fairness({
                "submission_medium": "paper_handout",
                "penalized_for_no_camera": True,
            })
        assert exc_info.value.code == "EQUITY_VIOLATION_AR_MANDATORY"
        assert exc_info.value.status_code == 400

        # 3. Penalizing student for no AR device raises equity violation
        with pytest.raises(AppError) as exc_info2:
            validate_offline_submission_fairness({
                "submission_medium": "paper_handout",
                "penalized_for_no_ar": True,
            })
        assert exc_info2.value.code == "EQUITY_VIOLATION_AR_MANDATORY"
        assert exc_info2.value.status_code == 400


# --------------------------------------------------------------------------- #
# 3. Static Component & Mobile File Contracts
# --------------------------------------------------------------------------- #

class TestComponentAndMobileContracts:
    """Verifies files, exports, and contracts across frontend and mobile trees."""

    def test_frontend_print_components_exist(self):
        print_dir = REPO_ROOT / "frontend" / "src" / "components" / "imperial" / "print"
        assert print_dir.is_dir()

        expected_files = [
            "types.ts",
            "worksheetData.ts",
            "PrintableFieldworkWorksheet.tsx",
            "PrintWorksheetModal.tsx",
            "LowBandwidthOfflineKit.tsx",
            "index.ts",
        ]
        for fname in expected_files:
            fpath = print_dir / fname
            assert fpath.is_file(), f"Missing frontend print file: {fname}"

        # Verify exports in index.ts
        index_content = (print_dir / "index.ts").read_text(encoding="utf-8")
        assert "PrintableFieldworkWorksheet" in index_content
        assert "PrintWorksheetModal" in index_content
        assert "LowBandwidthOfflineKit" in index_content

        # Verify equity notice in PrintableFieldworkWorksheet.tsx
        worksheet_content = (print_dir / "PrintableFieldworkWorksheet.tsx").read_text(encoding="utf-8")
        assert "100% NGOẠI TUYẾN" in worksheet_content
        assert "KHÔNG YÊU CẦU AR" in worksheet_content
        assert "contrast(160%)" in worksheet_content

    def test_mobile_offline_kit_components_exist(self):
        mobile_kit_dir = REPO_ROOT / "mobile" / "lib" / "features" / "offline_kit"
        assert mobile_kit_dir.is_dir()

        model_file = mobile_kit_dir / "data" / "models" / "offline_kit_model.dart"
        assert model_file.is_file()
        model_src = model_file.read_text(encoding="utf-8")
        assert "LowBandwidthKitModel" in model_src
        assert "zeroDeviceGuarantee" in model_src
        assert "arOrSmartphoneRequired" in model_src
        assert "OfflineRubbingAsset" in model_src

        screen_file = mobile_kit_dir / "presentation" / "screens" / "low_bandwidth_kit_screen.dart"
        assert screen_file.is_file()
        screen_src = screen_file.read_text(encoding="utf-8")
        assert "LowBandwidthKitScreen" in screen_src
        assert "KHÔNG YÊU CẦU AR" in screen_src

        # Verify router wiring
        router_file = REPO_ROOT / "mobile" / "lib" / "routing" / "app_router.dart"
        router_src = router_file.read_text(encoding="utf-8")
        assert "LowBandwidthKitScreen" in router_src
        assert "RoutePaths.offlineKit" in router_src
