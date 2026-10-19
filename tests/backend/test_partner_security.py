# -*- coding: utf-8 -*-
"""Automated security and integrity tests for RBPC Partner & Creator Consent APIs.

Covers AGENT 02 Phase 4 Requirements:
1. Unauthenticated requests to partner endpoints return HTTP 401.
2. Cross-provider access returns HTTP 403 (FORBIDDEN_SCOPE).
3. Provider ownership scoping (provider_id or linked experience.provider_id) strictly limits
   GET /api/v1/rbpc/partner/inquiries results.
4. Valid inquiry state transitions (new -> contacted -> confirmed/declined/closed) succeed
   and append immutable cryptographic audit records to rbpc_content_audit.
5. Invalid state transitions (e.g. new -> confirmed, closed -> new) are rejected with HTTP 400.
6. Non-staff/unauthenticated callers to POST /api/v1/rbpc/editor/creators/{id}/consent are rejected
   with HTTP 401 / 403.
7. Editor consent updates (consented, pending_review, revoked) update creator state, record audit
   entries in rbpc_content_audit, and revoked consent immediately fails closed on public creator
   lookups (HTTP 404 RBPC_CREATOR_NOT_FOUND).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password


def _create_user(db_session, email: str, role: UserRole = UserRole.learner) -> User:
    """Helper to create and persist a test user."""
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        display_name=f"User {email.split('@')[0]}",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str) -> None:
    """Helper to log in a user and set access session cookies on client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 200, res.text


def _setup_partner_fixtures(db_session):
    """Seed two distinct providers, creators, experiences, and inquiries."""
    partner_a = _create_user(db_session, "partner_sec_a@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, "partner_sec_b@example.com", role=UserRole.teacher)
    editor_user = _create_user(db_session, "editor_sec@example.com", role=UserRole.admin)
    guest_user = _create_user(db_session, "guest_sec@example.com", role=UserRole.learner)

    creator_a = RbpcCreator(
        slug=f"artisan-sec-a-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng A",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân bậc thầy Phường Đúc.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_b = RbpcCreator(
        slug=f"artisan-sec-b-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Hoa Giấy B",
        craft_tradition="Hoa giấy Thanh Tiên",
        approved_bio_vi="Nghệ nhân ưu tú Thanh Tiên.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"exp-sec-a-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="Hợp tác xã Đúc Đồng A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm Đúc Đồng A",
        description_vi="Mô tả trải nghiệm A",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug=f"exp-sec-b-{uuid.uuid4().hex[:6]}",
        creator_id=creator_b.id,
        provider_name="Cơ sở Hoa Giấy B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm Hoa Giấy B",
        description_vi="Mô tả trải nghiệm B",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    inquiry_a = RbpcInquiry(
        public_ref="INQ-SEC-A-001",
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Khách Hàng A",
        contact_channel="email",
        contact_value="khach_a@example.com",
        desired_date=date.today() + timedelta(days=10),
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-sec-a-{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_a_{uuid.uuid4().hex}",
    )
    inquiry_b = RbpcInquiry(
        public_ref="INQ-SEC-B-002",
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Khách Hàng B",
        contact_channel="email",
        contact_value="khach_b@example.com",
        desired_date=date.today() + timedelta(days=15),
        party_size=4,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-sec-b-{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    return {
        "partner_a": partner_a,
        "partner_b": partner_b,
        "editor": editor_user,
        "guest": guest_user,
        "creator_a": creator_a,
        "creator_b": creator_b,
        "exp_a": exp_a,
        "exp_b": exp_b,
        "inquiry_a": inquiry_a,
        "inquiry_b": inquiry_b,
    }


# --------------------------------------------------------------------------- #
# 1. Authentication & Authorization Gate Tests (HTTP 401 & 403)
# --------------------------------------------------------------------------- #
def test_unauthenticated_partner_endpoints_return_401(client, db_session):
    """Verify that unauthenticated requests to partner endpoints return HTTP 401."""
    fixtures = _setup_partner_fixtures(db_session)
    client.cookies.clear()

    # GET /api/v1/rbpc/partner/inquiries without credentials -> 401
    res_get = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_get.status_code == 401

    # PATCH /api/v1/rbpc/partner/inquiries/{id} without credentials -> 401
    res_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{fixtures['inquiry_a'].id}",
        json={"status": "contacted", "note": "Unauth attempt"},
    )
    assert res_patch.status_code == 401

    # POST /api/v1/rbpc/editor/creators/{id}/consent without credentials -> 401
    res_consent = client.post(
        f"/api/v1/rbpc/editor/creators/{fixtures['creator_a'].id}/consent",
        json={"consent_status": "revoked", "notes": "Unauth attempt"},
    )
    assert res_consent.status_code == 401


def test_cross_provider_access_returns_403(client, db_session):
    """Verify that cross-provider access to an inquiry returns HTTP 403 FORBIDDEN_SCOPE."""
    fixtures = _setup_partner_fixtures(db_session)

    # Login as Partner A
    _login_user(client, fixtures["partner_a"].email)

    # Partner A attempts to modify inquiry belonging to Partner B -> 403
    res_cross = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{fixtures['inquiry_b'].id}",
        json={"status": "contacted", "note": "Partner A spying on Partner B"},
    )
    assert res_cross.status_code == 403
    err = res_cross.json().get("error", {})
    assert err.get("code") == "FORBIDDEN_SCOPE"


def test_non_staff_editor_consent_returns_403(client, db_session):
    """Verify that non-staff callers (learners/teachers) cannot update creator consent."""
    fixtures = _setup_partner_fixtures(db_session)

    # Login as standard learner
    _login_user(client, fixtures["guest"].email)

    res = client.post(
        f"/api/v1/rbpc/editor/creators/{fixtures['creator_a'].id}/consent",
        json={"consent_status": "revoked", "notes": "Learner tampering"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_SCOPE"


# --------------------------------------------------------------------------- #
# 2. Strict Provider Scoping Verification
# --------------------------------------------------------------------------- #
def test_provider_inquiry_scoping(client, db_session):
    """Verify GET /api/v1/rbpc/partner/inquiries strictly filters by provider ownership."""
    fixtures = _setup_partner_fixtures(db_session)

    # 1. Authenticate as Partner A
    _login_user(client, fixtures["partner_a"].email)
    res_a = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_a.status_code == 200
    data_a = res_a.json()
    items_a = data_a["items"]
    refs_a = [item["reference"] for item in items_a]
    assert "INQ-SEC-A-001" in refs_a
    assert "INQ-SEC-B-002" not in refs_a

    # 2. Authenticate as Partner B
    _login_user(client, fixtures["partner_b"].email)
    res_b = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_b.status_code == 200
    data_b = res_b.json()
    items_b = data_b["items"]
    refs_b = [item["reference"] for item in items_b]
    assert "INQ-SEC-B-002" in refs_b
    assert "INQ-SEC-A-001" not in refs_b

    # 3. Authenticate as Admin/Editor: sees all inquiries across all providers
    _login_user(client, fixtures["editor"].email)
    res_admin = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_admin.status_code == 200
    refs_admin = [item["reference"] for item in res_admin.json()["items"]]
    assert "INQ-SEC-A-001" in refs_admin
    assert "INQ-SEC-B-002" in refs_admin


# --------------------------------------------------------------------------- #
# 3. Inquiry State Transitions & rbpc_content_audit Verification
# --------------------------------------------------------------------------- #
def test_valid_inquiry_state_transitions_and_audit(client, db_session):
    """Verify sequential transitions new -> contacted -> confirmed -> closed and audit logging."""
    fixtures = _setup_partner_fixtures(db_session)
    inquiry_a = fixtures["inquiry_a"]

    _login_user(client, fixtures["partner_a"].email)

    # Transition 1: new -> contacted
    res_1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Called guest via phone"},
    )
    assert res_1.status_code == 200
    assert res_1.json()["status"] == "contacted"

    # Transition 2: contacted -> confirmed
    res_2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "confirmed", "note": "Slot booked for Saturday morning"},
    )
    assert res_2.status_code == 200
    assert res_2.json()["status"] == "confirmed"

    # Transition 3: confirmed -> closed
    res_3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "closed", "note": "Workshop successfully held"},
    )
    assert res_3.status_code == 200
    assert res_3.json()["status"] == "closed"

    # Verify audit entries in rbpc_content_audit table
    audits = list(
        db_session.scalars(
            select(RbpcContentAudit)
            .where(
                RbpcContentAudit.entity_type == "inquiry",
                RbpcContentAudit.entity_id == inquiry_a.id,
            )
            .order_by(RbpcContentAudit.created_at.asc())
        )
    )
    assert len(audits) == 3
    # First transition
    assert audits[0].diff_payload["old_state"] == "new"
    assert audits[0].diff_payload["new_state"] == "contacted"
    assert audits[0].actor_id == fixtures["partner_a"].id
    # Second transition
    assert audits[1].diff_payload["old_state"] == "contacted"
    assert audits[1].diff_payload["new_state"] == "confirmed"
    assert audits[1].previous_hash == audits[0].new_hash  # Cryptographic hash chaining
    # Third transition
    assert audits[2].diff_payload["old_state"] == "confirmed"
    assert audits[2].diff_payload["new_state"] == "closed"
    assert audits[2].previous_hash == audits[1].new_hash


def test_invalid_inquiry_state_transitions(client, db_session):
    """Verify invalid state transitions (e.g., new -> confirmed, closed -> contacted) are rejected."""
    fixtures = _setup_partner_fixtures(db_session)
    inquiry_a = fixtures["inquiry_a"]

    _login_user(client, fixtures["partner_a"].email)

    # Invalid: new -> confirmed directly (skipping contacted)
    res_invalid_1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "confirmed", "note": "Direct confirmation attempt"},
    )
    assert res_invalid_1.status_code == 400
    assert res_invalid_1.json()["error"]["code"] == "RBPC_INVALID_TRANSITION"

    # Advance to contacted -> declined -> closed
    res_contacted = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Reached out"},
    )
    assert res_contacted.status_code == 200

    res_declined = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "declined", "note": "Overbooked"},
    )
    assert res_declined.status_code == 200

    res_closed = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "closed", "note": "Archived"},
    )
    assert res_closed.status_code == 200

    # Invalid: closed is a terminal state, cannot reopen or move back
    res_reopen = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Reopen attempt"},
    )
    assert res_reopen.status_code == 400
    assert res_reopen.json()["error"]["code"] == "RBPC_INVALID_TRANSITION"


# --------------------------------------------------------------------------- #
# 4. Creator Consent Management & Fail-Closed Revocation Effect
# --------------------------------------------------------------------------- #
def test_editor_creator_consent_workflow_and_revocation_effect(client, db_session):
    """Verify editor can update artisan consent and revoked consent immediately fails closed."""
    fixtures = _setup_partner_fixtures(db_session)
    creator_a = fixtures["creator_a"]

    # 1. Public lookup initially succeeds for consented creator and associated workshop experience
    res_pub_initial = client.get(f"/api/v1/rbpc/creators/{creator_a.slug}")
    assert res_pub_initial.status_code == 200
    assert res_pub_initial.json()["public_name"] == creator_a.public_name
    assert res_pub_initial.json()["consent_status"] == "consented"

    res_exp_initial = client.get(f"/api/v1/rbpc/experiences/{fixtures['exp_a'].slug}")
    assert res_exp_initial.status_code == 200
    assert res_exp_initial.json()["slug"] == fixtures["exp_a"].slug

    # 2. Login as Editor/Staff and update consent to pending_review
    _login_user(client, fixtures["editor"].email)
    res_update_pending = client.post(
        f"/api/v1/rbpc/editor/creators/{creator_a.id}/consent",
        json={
            "consent_status": "pending_review",
            "notes": "Annual consent audit renewal required",
        },
    )
    assert res_update_pending.status_code == 200
    assert res_update_pending.json()["consent_status"] == "pending_review"

    # Public lookup immediately fails closed (404) while pending_review
    res_pub_pending = client.get(f"/api/v1/rbpc/creators/{creator_a.slug}")
    assert res_pub_pending.status_code == 404
    assert res_pub_pending.json()["error"]["code"] == "RBPC_CREATOR_NOT_FOUND"

    # Associated workshop experience also immediately fails closed (404)
    res_exp_pending = client.get(f"/api/v1/rbpc/experiences/{fixtures['exp_a'].slug}")
    assert res_exp_pending.status_code == 404
    assert res_exp_pending.json()["error"]["code"] == "RBPC_EXPERIENCE_NOT_FOUND"

    # 3. Editor updates consent to revoked
    res_update_revoked = client.post(
        f"/api/v1/rbpc/editor/creators/{creator_a.id}/consent",
        json={
            "consent_status": "revoked",
            "notes": "Artisan requested right to be forgotten per Dignity Charter",
        },
    )
    assert res_update_revoked.status_code == 200
    assert res_update_revoked.json()["consent_status"] == "revoked"

    # Public lookup fails closed (404) for revoked creator
    res_pub_revoked = client.get(f"/api/v1/rbpc/creators/{creator_a.slug}")
    assert res_pub_revoked.status_code == 404
    assert res_pub_revoked.json()["error"]["code"] == "RBPC_CREATOR_NOT_FOUND"

    # Associated workshop experience also immediately fails closed (404)
    res_exp_revoked = client.get(f"/api/v1/rbpc/experiences/{fixtures['exp_a'].slug}")
    assert res_exp_revoked.status_code == 404
    assert res_exp_revoked.json()["error"]["code"] == "RBPC_EXPERIENCE_NOT_FOUND"

    # Attempting to submit a booking inquiry for the workshop fails closed (400)
    res_inq_revoked = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": fixtures["exp_a"].slug,
            "contact": {
                "name": "Khách Thử Nghiệm",
                "method": "email",
                "value": "khach@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=5)).isoformat(),
            "party_size": 2,
            "idempotency_key": str(uuid.uuid4()),
            "consent": {"version": "2026-v1", "accepted": True, "privacy_accepted": True},
        },
    )
    assert res_inq_revoked.status_code == 400
    assert res_inq_revoked.json()["error"]["code"] == "RBPC_CREATOR_CONSENT_UNAVAILABLE"

    # 4. Verify audit entries in rbpc_content_audit for creator
    creator_audits = list(
        db_session.scalars(
            select(RbpcContentAudit)
            .where(
                RbpcContentAudit.entity_type == "creator",
                RbpcContentAudit.entity_id == creator_a.id,
            )
            .order_by(RbpcContentAudit.created_at.asc())
        )
    )
    assert len(creator_audits) == 2
    # First update: consented -> pending_review
    assert creator_audits[0].diff_payload["old_status"] == "consented"
    assert creator_audits[0].diff_payload["new_status"] == "pending_review"
    assert creator_audits[0].diff_payload["reason"] == "Annual consent audit renewal required"
    assert creator_audits[0].actor_id == fixtures["editor"].id
    # Second update: pending_review -> revoked
    assert creator_audits[1].diff_payload["old_status"] == "pending_review"
    assert creator_audits[1].diff_payload["new_status"] == "revoked"
    assert creator_audits[1].previous_hash == creator_audits[0].new_hash

    # 5. Editor re-consents the creator -> Public endpoint is immediately accessible again
    res_reconsent = client.post(
        f"/api/v1/rbpc/editor/creators/{creator_a.id}/consent",
        json={
            "consent_status": "consented",
            "notes": "Signed new bilateral agreement CF-2026-099",
        },
    )
    assert res_reconsent.status_code == 200
    assert res_reconsent.json()["consent_status"] == "consented"

    res_pub_restored = client.get(f"/api/v1/rbpc/creators/{creator_a.slug}")
    assert res_pub_restored.status_code == 200
    assert res_pub_restored.json()["consent_status"] == "consented"

    res_exp_restored = client.get(f"/api/v1/rbpc/experiences/{fixtures['exp_a'].slug}")
    assert res_exp_restored.status_code == 200
    assert res_exp_restored.json()["slug"] == fixtures["exp_a"].slug
