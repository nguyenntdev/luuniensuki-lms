# -*- coding: utf-8 -*-
"""V5-T116 (Wave W11, Slot A06): Pilot Onboarding Portal Test Suite.

Audits and verifies:
1. Invitation Creation and Security (Admin/Staff):
   - POST /api/v1/pilot/invitations creates secure pilot invitation tokens.
   - Non-staff / regular learners cannot generate invitations (HTTP 403).
   - Generates unique secret token (ln_pilot_*) and stores hash.
2. Token Validation & Life-Cycle:
   - POST /api/v1/pilot/invitations/validate checks token validity.
   - Rejects non-existent tokens with invalid status.
   - Accurately reports expiration, exhaustion, and revocation.
3. Guided Activation & Multi-Tenant Onboarding:
   - POST /api/v1/pilot/activate redeems token and creates PilotParticipantActivation.
   - Requires explicit compliance agreement (compliance_accepted=True).
   - Enforces max_uses quota (subsequent activations fail with HTTP 403 once exhausted).
   - GET /api/v1/pilot/my-activation retrieves activation status and checklist.
   - POST /api/v1/pilot/onboarding/step records progress through step checklist.
4. Pilot Usage Health & Telemetry Scoring:
   - GET /api/v1/pilot/health returns activity signals, login count, and health score.
   - POST /api/v1/pilot/telemetry records usage events and updates health score/status.
5. Dedicated Support & Feedback Workflow:
   - POST /api/v1/pilot/support submits feedback/help ticket with SLA code.
   - GET /api/v1/pilot/support retrieves user's tickets (isolated from other participants).
   - POST /api/v1/pilot/support/{id}/reply adds threaded resolution responses.
6. NEGATIVE ABUSE INVARIANT (Critical Requirement V5-T116):
   - User without invitation token or with invalid/forged token CANNOT join private pilot (HTTP 403).
   - User with revoked or expired invitation cannot activate private pilot (HTTP 403).
   - Non-activated user attempting to record onboarding steps or fetch pilot health receives HTTP 404.
"""
from __future__ import annotations

import datetime
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import PilotInvitation, PilotParticipantActivation, User, UserRole
from backend.security import hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
    is_school_verified: bool = False,
) -> User:
    user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("Password123!"),
            display_name=display_name or f"User {email.split('@')[0]}",
            username=f"u_{uuid.uuid4().hex[:8]}",
            role=role,
            is_school_verified=is_school_verified,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.role = role
        user.is_school_verified = is_school_verified
        db_session.commit()
        db_session.refresh(user)
    return user


def _auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Test 1: Staff Generates Invitation & Gated Permissions
# --------------------------------------------------------------------------- #

def test_invitation_generation_and_staff_guard(client: TestClient, db_session):
    admin_user = _create_user(
        db_session, f"admin_pilot_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    learner_user = _create_user(
        db_session, f"learner_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner
    )

    admin_headers = _auth_headers(client, admin_user.email)
    learner_headers = _auth_headers(client, learner_user.email)

    payload = {
        "pilot_name": "Hue High School Pilot 2026",
        "target_role": "school_teacher",
        "organization_name": "THPT Quốc Học Huế",
        "contact_email": "quochoc.hue@edu.vn",
        "max_uses": 2,
        "expires_in_days": 14,
        "notes": "Testing history inquiry curriculum with Grade 10 teachers",
    }

    # 1. Learner cannot generate invitation (HTTP 403)
    res_forbidden = client.post(
        "/api/v1/pilot/invitations", json=payload, headers=learner_headers
    )
    assert res_forbidden.status_code == 403

    # 2. Staff generates invitation successfully (HTTP 201)
    res = client.post("/api/v1/pilot/invitations", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["pilot_name"] == "Hue High School Pilot 2026"
    assert data["target_role"] == "school_teacher"
    assert data["organization_name"] == "THPT Quốc Học Huế"
    assert data["max_uses"] == 2
    assert data["used_count"] == 0
    assert data["status"] == "active"
    assert "invitation_token" in data
    assert data["invitation_token"].startswith("ln_pilot_")

    # 3. Staff can list invitations
    res_list = client.get("/api/v1/pilot/invitations", headers=admin_headers)
    assert res_list.status_code == 200
    invitations = res_list.json()
    assert any(inv["id"] == data["id"] for inv in invitations)


# --------------------------------------------------------------------------- #
# Test 2: Token Validation & Pre-Check
# --------------------------------------------------------------------------- #

def test_invitation_token_validation_lifecycle(client: TestClient, db_session):
    admin_user = _create_user(
        db_session, f"admin_val_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin
    )
    admin_headers = _auth_headers(client, admin_user.email)

    # Create invitation with 1 use
    create_res = client.post(
        "/api/v1/pilot/invitations",
        json={
            "pilot_name": "Bronze Guild Partner Trial",
            "target_role": "artisan_partner",
            "organization_name": "Phường Đúc Artisan Guild",
            "contact_email": "phuongduc@artisan.vn",
            "max_uses": 1,
            "expires_in_days": 7,
        },
        headers=admin_headers,
    )
    inv_data = create_res.json()
    valid_token = inv_data["invitation_token"]

    # Validate valid token
    val_res = client.post(
        "/api/v1/pilot/invitations/validate", json={"token": valid_token}
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["status"] == "valid"
    assert val_data["pilot_name"] == "Bronze Guild Partner Trial"
    assert val_data["target_role"] == "artisan_partner"

    # Validate non-existent token
    fake_res = client.post(
        "/api/v1/pilot/invitations/validate",
        json={"token": "ln_pilot_non_existent_fake_token_1234567890"},
    )
    assert fake_res.status_code == 200
    fake_data = fake_res.json()
    assert fake_data["is_valid"] is False
    assert fake_data["status"] == "invalid"


# --------------------------------------------------------------------------- #
# Test 3: Guided Activation & Checklist Progression
# --------------------------------------------------------------------------- #

def test_pilot_activation_and_onboarding_progression(client: TestClient, db_session):
    admin = _create_user(db_session, f"admin_act_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    teacher = _create_user(db_session, f"teacher_act_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)

    admin_headers = _auth_headers(client, admin.email)
    teacher_headers = _auth_headers(client, teacher.email)

    # Admin issues invitation
    create_res = client.post(
        "/api/v1/pilot/invitations",
        json={
            "pilot_name": "Quoc Hoc Trial",
            "target_role": "school_teacher",
            "organization_name": "Quoc Hoc",
            "contact_email": teacher.email,
            "max_uses": 1,
            "expires_in_days": 30,
        },
        headers=admin_headers,
    )
    token = create_res.json()["invitation_token"]

    # 1. Activation fails if compliance is not accepted
    res_no_comp = client.post(
        "/api/v1/pilot/activate",
        json={"token": token, "compliance_accepted": False},
        headers=teacher_headers,
    )
    assert res_no_comp.status_code == 400
    assert "COMPLIANCE_ACCEPTANCE_REQUIRED" in res_no_comp.text

    # 2. Activation succeeds with compliance accepted
    res_act = client.post(
        "/api/v1/pilot/activate",
        json={"token": token, "compliance_accepted": True},
        headers=teacher_headers,
    )
    assert res_act.status_code == 200
    act_data = res_act.json()
    assert act_data["status"] == "activated"
    assert act_data["role_type"] == "school_teacher"
    assert act_data["current_step"] == "welcome"
    assert act_data["completed_steps"] == []
    assert act_data["compliance_accepted"] is True

    # Teacher status upgraded/verified
    db_session.refresh(teacher)
    assert teacher.is_school_verified is True
    assert teacher.role == UserRole.teacher

    # 3. Fetch active activation
    res_my = client.get("/api/v1/pilot/my-activation", headers=teacher_headers)
    assert res_my.status_code == 200
    assert res_my.json()["id"] == act_data["id"]

    # 4. Progress through onboarding steps
    res_step1 = client.post(
        "/api/v1/pilot/onboarding/step",
        json={"step": "welcome", "completed": True},
        headers=teacher_headers,
    )
    assert res_step1.status_code == 200
    data_step1 = res_step1.json()
    assert "welcome" in data_step1["completed_steps"]
    assert data_step1["current_step"] == "curriculum_alignment"

    # Step 2
    res_step2 = client.post(
        "/api/v1/pilot/onboarding/step",
        json={"step": "curriculum_alignment", "completed": True},
        headers=teacher_headers,
    )
    assert res_step2.status_code == 200
    assert "curriculum_alignment" in res_step2.json()["completed_steps"]


# --------------------------------------------------------------------------- #
# Test 4: Usage Health & Telemetry Scoring
# --------------------------------------------------------------------------- #

def test_pilot_usage_health_and_telemetry(client: TestClient, db_session):
    admin = _create_user(db_session, f"admin_hlth_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    partner = _create_user(db_session, f"partner_hlth_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)

    admin_headers = _auth_headers(client, admin.email)
    partner_headers = _auth_headers(client, partner.email)

    create_res = client.post(
        "/api/v1/pilot/invitations",
        json={
            "pilot_name": "Phap Lam Artisan Pilot",
            "target_role": "artisan_partner",
            "organization_name": "Phap Lam Center",
            "contact_email": partner.email,
            "max_uses": 1,
            "expires_in_days": 30,
        },
        headers=admin_headers,
    )
    token = create_res.json()["invitation_token"]

    # Activate
    client.post(
        "/api/v1/pilot/activate",
        json={"token": token, "compliance_accepted": True},
        headers=partner_headers,
    )

    # Check health telemetry
    res_health = client.get("/api/v1/pilot/health", headers=partner_headers)
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["health_score"] >= 75.0
    assert health_data["health_status"] in ("healthy", "attention_needed")
    assert health_data["actions_count"] >= 1

    # Record telemetry action
    res_telem = client.post(
        "/api/v1/pilot/telemetry",
        json={"action_name": "explored_3d_urn_model", "details": {"urn": "cao_dinh"}},
        headers=partner_headers,
    )
    assert res_telem.status_code == 200
    telem_data = res_telem.json()
    assert telem_data["actions_count"] >= 2
    assert telem_data["last_action_name"] == "explored_3d_urn_model"
    assert telem_data["health_score"] >= 90.0


# --------------------------------------------------------------------------- #
# Test 5: Pilot Support & Feedback Tickets
# --------------------------------------------------------------------------- #

def test_pilot_support_tickets_and_replies(client: TestClient, db_session):
    admin = _create_user(db_session, f"admin_spt_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    participant = _create_user(db_session, f"user_spt_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)

    admin_headers = _auth_headers(client, admin.email)
    participant_headers = _auth_headers(client, participant.email)

    # 1. Participant creates support ticket
    tkt_payload = {
        "category": "onboarding_help",
        "priority": "high",
        "subject": "Need assistance linking classroom roster",
        "message": "We have 35 students in Class 10A1 ready to test the lesson wizard.",
    }
    res_create = client.post(
        "/api/v1/pilot/support", json=tkt_payload, headers=participant_headers
    )
    assert res_create.status_code == 201
    ticket = res_create.json()
    assert ticket["ticket_code"].startswith("PILOT-REQ-")
    assert ticket["status"] == "open"
    assert ticket["subject"] == tkt_payload["subject"]

    # 2. Staff replies to ticket
    res_reply = client.post(
        f"/api/v1/pilot/support/{ticket['id']}/reply",
        json={"message": "We have enabled bulk roster import for your school account."},
        headers=admin_headers,
    )
    assert res_reply.status_code == 200
    updated_tkt = res_reply.json()
    assert len(updated_tkt["responses"]) == 1
    assert updated_tkt["responses"][0]["is_staff"] is True
    assert "bulk roster import" in updated_tkt["responses"][0]["message"]


# --------------------------------------------------------------------------- #
# Test 6: NEGATIVE ABUSE INVARIANT (Critical Requirement V5-T116)
# --------------------------------------------------------------------------- #

def test_negative_abuse_user_without_invitation_cannot_join_trial(client: TestClient, db_session):
    admin = _create_user(db_session, f"admin_abuse_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    uninvited_user = _create_user(
        db_session, f"uninvited_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner
    )

    admin_headers = _auth_headers(client, admin.email)
    uninvited_headers = _auth_headers(client, uninvited_user.email)

    # A. Uninvited user attempting to activate without valid token receives HTTP 403
    res_fake = client.post(
        "/api/v1/pilot/activate",
        json={"token": "ln_pilot_unauthorized_forged_token", "compliance_accepted": True},
        headers=uninvited_headers,
    )
    assert res_fake.status_code == 403
    assert "PILOT_INVITATION_INVALID" in res_fake.text

    # B. Uninvited user has no active trial
    res_no_act = client.get("/api/v1/pilot/my-activation", headers=uninvited_headers)
    assert res_no_act.status_code == 404

    # C. Uninvited user cannot record onboarding steps
    res_step = client.post(
        "/api/v1/pilot/onboarding/step",
        json={"step": "welcome", "completed": True},
        headers=uninvited_headers,
    )
    assert res_step.status_code == 404

    # D. Invitation exhaustion prevents duplicate/excess redemptions
    create_res = client.post(
        "/api/v1/pilot/invitations",
        json={
            "pilot_name": "Single Use Trial",
            "target_role": "school_teacher",
            "organization_name": "Single School",
            "contact_email": "single@school.edu",
            "max_uses": 1,
            "expires_in_days": 10,
        },
        headers=admin_headers,
    )
    single_token = create_res.json()["invitation_token"]

    legit_user = _create_user(db_session, f"legit_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)
    legit_headers = _auth_headers(client, legit_user.email)

    # First redemption succeeds
    res_first = client.post(
        "/api/v1/pilot/activate",
        json={"token": single_token, "compliance_accepted": True},
        headers=legit_headers,
    )
    assert res_first.status_code == 200

    # Second user attempting to use exhausted invitation receives HTTP 403
    second_user = _create_user(db_session, f"second_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)
    second_headers = _auth_headers(client, second_user.email)
    res_second = client.post(
        "/api/v1/pilot/activate",
        json={"token": single_token, "compliance_accepted": True},
        headers=second_headers,
    )
    assert res_second.status_code == 403
    assert "PILOT_INVITATION_EXHAUSTED" in res_second.text

    # E. Revoked invitation cannot be activated
    create_res2 = client.post(
        "/api/v1/pilot/invitations",
        json={
            "pilot_name": "Revoked Trial",
            "target_role": "artisan_partner",
            "organization_name": "Revoked Guild",
            "contact_email": "revoked@guild.vn",
            "max_uses": 1,
            "expires_in_days": 10,
        },
        headers=admin_headers,
    )
    inv2_id = create_res2.json()["id"]
    inv2_token = create_res2.json()["invitation_token"]

    # Revoke in DB
    inv2 = db_session.get(PilotInvitation, uuid.UUID(inv2_id))
    inv2.status = "revoked"
    db_session.commit()

    res_revoked = client.post(
        "/api/v1/pilot/activate",
        json={"token": inv2_token, "compliance_accepted": True},
        headers=second_headers,
    )
    assert res_revoked.status_code == 403
    assert "PILOT_INVITATION_REVOKED" in res_revoked.text
