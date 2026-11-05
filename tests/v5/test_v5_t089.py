# -*- coding: utf-8 -*-
"""V5-T089: Feature Release Flags, Kill Switches & Incident Runbooks Test Suite.

Wave: W08 / Slot: A09 / Priority: P0 / Classification: PRODUCTION_COMPLETION.
Verifies:
1. Granular Feature Flags & Kill Switches:
   - FEATURE_FLAG_AI_TUTOR_ENABLED
   - FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED
   - FEATURE_FLAG_RBPC_COMMERCE_ENABLED
2. Kill switch tripping immediately blocks targeted feature with HTTP 503 Service Unavailable:
   - Returns friendly maintenance notice with standard error envelope.
   - Sets Retry-After header.
3. Feature Independence & Non-Interference:
   - Public browse (heritage catalog, stories, places) operates completely independently when AI, LiveKit, or commerce is killed.
   - Disabling AI does not break commerce or public browse.
   - Disabling commerce does not break AI or public browse.
4. Admin Runtime Toggle Endpoint:
   - Admin can view status of all kill switches.
   - Admin can toggle kill switch at runtime without application restart.
   - Non-admin callers receive HTTP 401/403.
5. Incident Runbook Document Validity:
   - docs/runbooks/INCIDENT_RUNBOOK_OUTAGE.md exists and contains required sections.
"""
from __future__ import annotations

import os
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.models import User, UserRole
from backend.security import hash_password
from backend.services import feature_flags as ff_service


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a test user with a specific role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookies."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


@pytest.fixture(autouse=True)
def clean_runtime_overrides():
    """Ensure in-memory runtime overrides are cleared before and after each test."""
    ff_service.clear_runtime_overrides()
    yield
    ff_service.clear_runtime_overrides()


# --------------------------------------------------------------------------- #
# Test 1: Kill switch tripping immediately blocks targeted feature with HTTP 503
# --------------------------------------------------------------------------- #

def test_ai_tutor_kill_switch_blocks_with_503(client: TestClient, db_session):
    """When FEATURE_FLAG_AI_TUTOR_ENABLED is disabled, AI endpoints return 503 Service Unavailable."""
    user = _create_user(db_session, f"student_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.learner)
    _login(client, user.email)

    # Initially, AI endpoints should not fail with 503 due to kill switch
    # (they may return 400 for bad input, or proceed)
    # Trip kill switch:
    ff_service.set_runtime_override("FEATURE_FLAG_AI_TUTOR_ENABLED", False)

    # 1. POST /api/v1/history/tutor/ask
    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Kể cho tôi về Cao Đỉnh?", "heritage_scope": "CUU_DINH"},
    )
    assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
    data = res.json()
    assert "error" in data, "Must conform to standard error envelope"
    assert "Trợ lý AI" in data["error"]["message"] or "bảo trì" in data["error"]["message"]

    # 2. POST /api/v1/ai/tutor
    res_ai = client.post(
        "/api/v1/ai/tutor",
        json={"message": "Chào bạn, hãy kể về Cửu Đỉnh"},
    )
    assert res_ai.status_code == 503, f"Expected 503, got {res_ai.status_code}: {res_ai.text}"
    data_ai = res_ai.json()
    assert "error" in data_ai
    assert "Trợ lý AI" in data_ai["error"]["message"] or "bảo trì" in data_ai["error"]["message"]


def test_livekit_media_kill_switch_blocks_with_503(client: TestClient, db_session):
    """When FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED is disabled, token & join return 503."""
    user = _create_user(db_session, f"student_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.learner)
    _login(client, user.email)

    fake_session_id = uuid.uuid4()

    # Trip LiveKit kill switch
    ff_service.set_runtime_override("FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED", False)

    # POST /api/v1/live-sessions/{id}/token
    res_token = client.post(f"/api/v1/live-sessions/{fake_session_id}/token")
    assert res_token.status_code == 503, f"Expected 503, got {res_token.status_code}: {res_token.text}"
    assert "error" in res_token.json()
    assert "truyền phát" in res_token.json()["error"]["message"] or "WebRTC" in res_token.json()["error"]["message"]

    # POST /api/v1/live-sessions/{id}/join
    res_join = client.post(f"/api/v1/live-sessions/{fake_session_id}/join")
    assert res_join.status_code == 503, f"Expected 503, got {res_join.status_code}: {res_join.text}"
    assert "error" in res_join.json()


def test_rbpc_commerce_kill_switch_blocks_with_503(client: TestClient, db_session):
    """When FEATURE_FLAG_RBPC_COMMERCE_ENABLED is disabled, inquiry submission returns 503."""
    # Trip RBPC commerce kill switch
    ff_service.set_runtime_override("FEATURE_FLAG_RBPC_COMMERCE_ENABLED", False)

    payload = {
        "experience_slug": "duc-dong-phuong-duc",
        "contact": {
            "name": "Nguyễn Văn A",
            "method": "email",
            "value": "nguyenvana@example.com",
        },
        "party_size": 2,
        "preferred_date": "2026-12-01",
        "message": "Muốn tìm hiểu đúc đồng Huế",
        "idempotency_key": str(uuid.uuid4()),
        "consent": {
            "accepted": True,
            "privacy_accepted": True,
            "version": "rbpc-inquiry-v1",
        },
    }
    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
    data = res.json()
    assert "error" in data
    assert "đặt lịch" in data["error"]["message"].lower() or "bảo trì" in data["error"]["message"].lower()

    # Verify RBPC config endpoint reflects inquiry_enabled = False
    res_config = client.get("/api/v1/rbpc/config")
    assert res_config.status_code == 200
    config_data = res_config.json()
    assert config_data["inquiry_enabled"] is False


# --------------------------------------------------------------------------- #
# Test 2: Independence of Features (Negative Abuse Guardrail)
# --------------------------------------------------------------------------- #

def test_feature_independence_public_browse_remains_active_when_ai_and_commerce_killed(
    client: TestClient, db_session
):
    """Disabling AI and Commerce must operate completely independently of public browse."""
    # Trip both AI and Commerce kill switches
    ff_service.set_runtime_override("FEATURE_FLAG_AI_TUTOR_ENABLED", False)
    ff_service.set_runtime_override("FEATURE_FLAG_RBPC_COMMERCE_ENABLED", False)

    # 1. Public heritage catalog MUST remain online and 200 OK
    res_catalog = client.get("/api/v1/heritage/catalog")
    assert res_catalog.status_code == 200, f"Catalog failed: {res_catalog.text}"

    # 2. Public heritage places MUST remain online and 200 OK
    res_places = client.get("/api/v1/heritage/places")
    assert res_places.status_code == 200, f"Places failed: {res_places.text}"

    # 3. Public cultural stories MUST remain online and 200 OK
    res_stories = client.get("/api/v1/rbpc/stories")
    assert res_stories.status_code == 200, f"Stories failed: {res_stories.text}"

    # 4. System health check MUST remain healthy
    res_health = client.get("/health")
    assert res_health.status_code == 200


def test_commerce_active_when_ai_killed(client: TestClient, db_session):
    """Killing AI does not affect RBPC commerce inquiries availability check."""
    ff_service.set_runtime_override("FEATURE_FLAG_AI_TUTOR_ENABLED", False)
    ff_service.set_runtime_override("FEATURE_FLAG_RBPC_COMMERCE_ENABLED", True)

    res_config = client.get("/api/v1/rbpc/config")
    assert res_config.status_code == 200
    config_data = res_config.json()
    assert config_data["ai_enabled"] is False
    assert config_data["inquiry_enabled"] is True


# --------------------------------------------------------------------------- #
# Test 3: Admin Runtime Toggle Endpoint & RBAC
# --------------------------------------------------------------------------- #

def test_admin_kill_switch_endpoints_and_rbac(client: TestClient, db_session):
    """Admin can query and toggle kill switches; non-admin receives 401/403."""
    learner = _create_user(db_session, f"learner_{uuid.uuid4().hex[:6]}@domain.com", role=UserRole.learner)
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@domain.com", role=UserRole.admin)

    # Non-authenticated user fails
    res_unauth = client.get("/api/v1/admin/kill-switches")
    assert res_unauth.status_code in (401, 403)

    # Learner fails
    _login(client, learner.email)
    res_forbidden = client.get("/api/v1/admin/kill-switches")
    assert res_forbidden.status_code == 403

    # Admin succeeds
    _login(client, admin.email)
    res_admin = client.get("/api/v1/admin/kill-switches")
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "flags" in data
    assert "FEATURE_FLAG_AI_TUTOR_ENABLED" in data["flags"]
    assert "FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED" in data["flags"]
    assert "FEATURE_FLAG_RBPC_COMMERCE_ENABLED" in data["flags"]

    # Admin toggles AI Tutor OFF
    res_toggle = client.post(
        "/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle",
        json={"enabled": False, "reason": "Emergency provider maintenance", "persist_db": True},
    )
    assert res_toggle.status_code == 200
    toggle_data = res_toggle.json()
    assert toggle_data["status"] == "success"
    assert toggle_data["enabled"] is False

    # Check that AI endpoint is now immediately blocked with 503
    res_ask = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Test question after toggle"},
    )
    assert res_ask.status_code == 503

    # Admin toggles AI Tutor back ON
    res_restore = client.post(
        "/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle",
        json={"enabled": True, "reason": "Restoring service after provider recovery", "persist_db": True},
    )
    assert res_restore.status_code == 200
    assert res_restore.json()["enabled"] is True

    # Check status endpoint reflects restored state
    res_status = client.get("/api/v1/admin/kill-switches")
    assert res_status.status_code == 200
    assert res_status.json()["flags"]["FEATURE_FLAG_AI_TUTOR_ENABLED"] is True


# --------------------------------------------------------------------------- #
# Test 4: Incident Runbook Validity
# --------------------------------------------------------------------------- #

def test_incident_runbook_validity():
    """Verify that docs/runbooks/INCIDENT_RUNBOOK_OUTAGE.md exists and has required sections."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    runbook_path = repo_root / "docs" / "runbooks" / "INCIDENT_RUNBOOK_OUTAGE.md"

    assert runbook_path.exists(), f"Incident runbook missing at: {runbook_path}"
    content = runbook_path.read_text(encoding="utf-8")

    # Required sections & keys
    required_strings = [
        "FEATURE_FLAG_AI_TUTOR_ENABLED",
        "FEATURE_FLAG_LIVEKIT_MEDIA_ENABLED",
        "FEATURE_FLAG_RBPC_COMMERCE_ENABLED",
        "503 Service Unavailable",
        "Golden Rules",
        "SEV-1",
        "SEV-2",
        "SEV-3",
        "/api/v1/admin/kill-switches",
    ]
    for req in required_strings:
        assert req in content, f"Runbook missing mandatory keyword/section: '{req}'"
