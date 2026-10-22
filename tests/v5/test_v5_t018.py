# -*- coding: utf-8 -*-
"""V5-T018: Canonical Inquiry Event Ledger Test Suite.

Audits and verifies:
1. Canonical inquiry event ledger (append-only transitions, cryptographic hashes, deduplication on replay).
2. Creating an inquiry logs an immutable 'inquiry_created' audit entry in rbpc_content_audit.
3. Status transitions (new -> contacted -> confirmed -> declined -> closed) write sequential
   audit entries with valid cryptographic SHA-256 hash chains (previous_hash -> new_hash).
4. Replay prevention / Idempotency: Replaying the same PATCH with the same status does NOT
   duplicate audit log entries, returning cleanly with 200 OK.
5. Zero PII invariant: Audit diff payloads contain zero plain contact phone, email, visitor names,
   or credentials; any phone/email embedded in notes is strictly redacted.
6. Cryptographic chain integrity & tamper-evident verification.
"""
from __future__ import annotations

import copy
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.routers.rbpc import _inquiry_rate_limit_store
from backend.security import hash_password
from backend.services.rbpc_audit import (
    ACTION_INQUIRY_CREATED,
    ACTION_STATE_TRANSITION,
    ENTITY_INQUIRY,
    compute_audit_hash,
    get_audit_trail,
    get_latest_audit_entry,
    record_audit_entry,
    record_inquiry_state_transition,
    verify_audit_chain,
)


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _reset_inquiry_rate_limiter():
    """Reset rate limiter state before and after each test."""
    _inquiry_rate_limit_store.clear()
    yield
    _inquiry_rate_limit_store.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user for test scenarios."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> None:
    """Helper to log in a user and set cookies on TestClient."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"


def _create_creator_and_experience(
    db_session, partner_user: User
) -> tuple[RbpcCreator, RbpcExperience]:
    """Create and persist a consented artisan and workshop experience owned by partner."""
    creator = RbpcCreator(
        slug=f"artisan-ledger-{uuid.uuid4().hex[:8]}",
        public_name="Nghệ nhân Ledger Huế",
        craft_tradition="Pháp lam Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử audit ledger.",
        consent_status=RbpcConsentStatus.consented.value,
        display_consent_ref="REF-LEDGER-2026-001",
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-ledger-{uuid.uuid4().hex[:8]}",
        creator_id=creator.id,
        provider_id=partner_user.id,
        provider_name="Xưởng Pháp Lam Ledger",
        title_vi="Trải nghiệm Pháp Lam Cung Đình",
        description_vi="Thực hành tráng men ngũ sắc.",
        area_public="Huế",
        availability_mode="inquiry_only",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(creator)
    db_session.refresh(exp)
    return creator, exp


# --------------------------------------------------------------------------- #
# Tests: Inquiry Creation & Genesis Audit Entry
# --------------------------------------------------------------------------- #
def test_inquiry_creation_logs_audit_entry(client, db_session):
    """Test that creating an inquiry writes an append-only 'inquiry_created' audit entry."""
    partner = _create_user(db_session, f"partner_t018_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp = _create_creator_and_experience(db_session, partner)

    idem_key = f"idem-key-{uuid.uuid4()}"
    payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Nguyễn Văn An",
            "method": "email",
            "value": "nguyenvanan.hue@example.com",
        },
        "preferred_date": (date.today() + timedelta(days=5)).isoformat(),
        "party_size": 3,
        "message": "Tôi muốn tham gia cùng gia đình 3 người.",
        "consent": {
            "accepted": True,
            "privacy_accepted": True,
            "version": "rbpc-inquiry-v1",
        },
        "idempotency_key": idem_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 202, res.text
    data = res.json()
    assert data["status"] == "new"
    public_ref = data["reference"]

    # Verify inquiry row exists
    inquiry = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref))
    assert inquiry is not None
    assert inquiry.state == "new"

    # Verify audit entry in rbpc_content_audit
    audits = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry.id,
            )
        )
    )
    assert len(audits) == 1, f"Expected exactly 1 audit entry, got {len(audits)}"
    audit = audits[0]
    assert audit.action == ACTION_INQUIRY_CREATED
    assert audit.previous_hash is None, "Genesis audit entry must have previous_hash=None"
    assert audit.new_hash is not None
    assert len(audit.new_hash) == 64

    # Verify recomputed hash matches
    expected_hash = compute_audit_hash(
        previous_hash=None,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_INQUIRY_CREATED,
        actor_id=None,
        diff_payload=audit.diff_payload,
        approved_scope=audit.approved_scope,
        created_at=audit.created_at,
    )
    assert audit.new_hash == expected_hash

    # Verify diff_payload contents & zero PII
    assert audit.diff_payload["public_ref"] == inquiry.public_ref
    assert audit.diff_payload["state"] == "new"
    assert audit.diff_payload["party_size"] == 3
    assert audit.diff_payload["experience_id"] == str(exp.id)
    assert "name" not in audit.diff_payload
    assert "contact_value" not in audit.diff_payload
    assert "email" not in audit.diff_payload
    assert "message" not in audit.diff_payload


# --------------------------------------------------------------------------- #
# Tests: Sequential State Transitions & Cryptographic Hash Chain Linkage
# --------------------------------------------------------------------------- #
def test_status_transitions_write_sequential_audit_entries_with_valid_hash_chain(
    client, db_session
):
    """Test sequential transitions: new -> contacted -> confirmed -> closed with valid previous_hash -> new_hash links."""
    partner_email = f"partner_seq_{uuid.uuid4().hex[:6]}@example.com"
    partner = _create_user(db_session, partner_email)
    creator, exp = _create_creator_and_experience(db_session, partner)

    # 1. Create inquiry (state = 'new')
    idem_key = f"idem-key-{uuid.uuid4()}"
    res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Lê Thị Cúc",
                "method": "email",
                "value": "cuc.le@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=7)).isoformat(),
            "party_size": 2,
            "message": "Trải nghiệm văn hóa Huế",
            "consent": {
                "accepted": True,
                "privacy_accepted": True,
                "version": "rbpc-inquiry-v1",
            },
            "idempotency_key": idem_key,
        },
    )
    assert res.status_code == 202
    public_ref = res.json()["reference"]
    inquiry = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref))
    assert inquiry is not None

    _login_user(client, partner_email)

    # 2. Transition: new -> contacted
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted", "note": "Đã trao đổi sơ bộ qua tin nhắn."},
    )
    assert res1.status_code == 200, res1.text
    assert res1.json()["status"] == "contacted"

    # 3. Transition: contacted -> confirmed
    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "confirmed", "note": "Đã xác nhận lịch hẹn 2 người."},
    )
    assert res2.status_code == 200, res2.text
    assert res2.json()["status"] == "confirmed"

    # 4. Transition: confirmed -> closed
    res3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "closed", "note": "Khách đã hoàn thành trải nghiệm tráng men ngũ sắc."},
    )
    assert res3.status_code == 200, res3.text
    assert res3.json()["status"] == "closed"

    # 5. Fetch audit trail and verify exact sequential order and hash chaining
    trail, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert count == 4
    assert len(trail) == 4

    entry_created = trail[0]
    entry_contacted = trail[1]
    entry_confirmed = trail[2]
    entry_closed = trail[3]

    # Verify actions & states
    assert entry_created.action == ACTION_INQUIRY_CREATED
    assert entry_created.diff_payload["state"] == "new"

    assert entry_contacted.action == ACTION_STATE_TRANSITION
    assert entry_contacted.diff_payload["old_state"] == "new"
    assert entry_contacted.diff_payload["new_state"] == "contacted"

    assert entry_confirmed.action == ACTION_STATE_TRANSITION
    assert entry_confirmed.diff_payload["old_state"] == "contacted"
    assert entry_confirmed.diff_payload["new_state"] == "confirmed"

    assert entry_closed.action == ACTION_STATE_TRANSITION
    assert entry_closed.diff_payload["old_state"] == "confirmed"
    assert entry_closed.diff_payload["new_state"] == "closed"

    # Verify cryptographic previous_hash -> new_hash linkage
    assert entry_created.previous_hash is None
    assert entry_contacted.previous_hash == entry_created.new_hash
    assert entry_confirmed.previous_hash == entry_contacted.new_hash
    assert entry_closed.previous_hash == entry_confirmed.new_hash

    # Verify chain integrity using verify_audit_chain
    is_valid, errors = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id
    )
    assert is_valid is True, f"Hash chain verification failed: {errors}"
    assert len(errors) == 0


def test_alternative_transition_branch_declined_and_chain(client, db_session):
    """Test alternative transition path: new -> contacted -> declined -> closed."""
    partner_email = f"partner_dec_{uuid.uuid4().hex[:6]}@example.com"
    partner = _create_user(db_session, partner_email)
    creator, exp = _create_creator_and_experience(db_session, partner)

    idem_key = f"idem-key-{uuid.uuid4()}"
    res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Hoàng Minh",
                "method": "email",
                "value": "minh.hoang@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=3)).isoformat(),
            "party_size": 4,
            "message": "Cần xác nhận gấp",
            "consent": {
                "accepted": True,
                "privacy_accepted": True,
                "version": "rbpc-inquiry-v1",
            },
            "idempotency_key": idem_key,
        },
    )
    assert res.status_code == 202
    inquiry_id = db_session.scalar(
        select(RbpcInquiry.id).where(RbpcInquiry.public_ref == res.json()["reference"])
    )

    _login_user(client, partner_email)

    # new -> contacted
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Kiểm tra lịch xưởng."},
    )
    assert res1.status_code == 200

    # contacted -> declined
    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "declined", "note": "Xưởng đã kín chỗ vào ngày yêu cầu."},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "declined"

    # declined -> closed
    res3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "closed", "note": "Đã thông báo lý do cho khách."},
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "closed"

    # Verify unbroken hash chain
    is_valid, errors = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry_id
    )
    assert is_valid is True, f"Hash chain verification failed: {errors}"
    assert len(errors) == 0

    trail, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry_id)
    assert count == 4
    assert trail[2].diff_payload["new_state"] == "declined"


# --------------------------------------------------------------------------- #
# Tests: Replay Prevention & Idempotency on PATCH
# --------------------------------------------------------------------------- #
def test_replay_patch_does_not_create_duplicate_audit_events(client, db_session):
    """Test that replaying the same PATCH with same status does NOT duplicate audit events."""
    partner_email = f"partner_replay_{uuid.uuid4().hex[:6]}@example.com"
    partner = _create_user(db_session, partner_email)
    creator, exp = _create_creator_and_experience(db_session, partner)

    # Create inquiry (Audit 1: inquiry_created)
    idem_key = f"idem-key-{uuid.uuid4()}"
    res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Trần Văn Tươi",
                "method": "email",
                "value": "tuoi.tran@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=10)).isoformat(),
            "party_size": 1,
            "message": "Trải nghiệm cá nhân",
            "consent": {
                "accepted": True,
                "privacy_accepted": True,
                "version": "rbpc-inquiry-v1",
            },
            "idempotency_key": idem_key,
        },
    )
    assert res.status_code == 202
    inquiry_id = db_session.scalar(
        select(RbpcInquiry.id).where(RbpcInquiry.public_ref == res.json()["reference"])
    )

    _login_user(client, partner_email)

    # Transition: new -> contacted (Audit 2)
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Liên hệ lần đầu."},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "contacted"

    # Confirm audit count is 2
    audits_after_first = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_after_first) == 2

    # REPLAY 1: Send the exact same PATCH {"status": "contacted"}
    res_replay1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Liên hệ lần đầu."},
    )
    assert res_replay1.status_code == 200
    assert res_replay1.json()["status"] == "contacted"

    # Verify audit count remains 2 (ZERO new audit entry created!)
    audits_after_replay1 = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_after_replay1) == 2, "Replay MUST NOT create duplicate audit log entries"

    # REPLAY 2: Another replay of the same PATCH
    res_replay2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Liên hệ lần đầu (lặp lại)."},
    )
    assert res_replay2.status_code == 200
    assert res_replay2.json()["status"] == "contacted"

    audits_after_replay2 = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_after_replay2) == 2

    # Transition: contacted -> confirmed (Audit 3)
    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "confirmed", "note": "Xác nhận lịch hẹn."},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "confirmed"

    audits_after_confirmed = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_after_confirmed) == 3

    # REPLAY 3: Replay PATCH when status is already 'confirmed'
    res_replay3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "confirmed", "note": "Xác nhận lại."},
    )
    assert res_replay3.status_code == 200
    assert res_replay3.json()["status"] == "confirmed"

    audits_after_replay3 = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_after_replay3) == 3, "Replay of confirmed state MUST NOT duplicate audit"

    # Direct service-level replay test
    inquiry_obj = db_session.get(RbpcInquiry, inquiry_id)
    entry_service_replay = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry_obj,
        old_state="confirmed",
        new_state="confirmed",
    )
    assert entry_service_replay.id == audits_after_confirmed[-1].id

    audits_final = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_final) == 3

    # Cryptographic integrity check after all replays
    is_valid, errors = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry_id
    )
    assert is_valid is True, f"Hash chain verification failed: {errors}"
    assert len(errors) == 0


def test_post_inquiry_replay_no_duplicate_audit(client, db_session):
    """Test that replaying POST /api/v1/rbpc/inquiries with same idempotency key does not duplicate audit."""
    partner = _create_user(db_session, f"partner_post_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp = _create_creator_and_experience(db_session, partner)

    idem_key = f"idem-key-{uuid.uuid4()}"
    payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Đặng Thị Thảo",
            "method": "email",
            "value": "thao.dang@example.com",
        },
        "preferred_date": (date.today() + timedelta(days=14)).isoformat(),
        "party_size": 2,
        "message": "Đăng ký tham gia",
        "consent": {
            "accepted": True,
            "privacy_accepted": True,
            "version": "rbpc-inquiry-v1",
        },
        "idempotency_key": idem_key,
    }

    # Initial POST
    res1 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res1.status_code == 202
    public_ref = res1.json()["reference"]
    inquiry_id = db_session.scalar(
        select(RbpcInquiry.id).where(RbpcInquiry.public_ref == public_ref)
    )

    # Verify 1 audit
    audits_initial = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_initial) == 1

    # Replay POST with exact same idempotency key
    res2 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res2.status_code == 202
    assert res2.json()["reference"] == public_ref

    # Verify audit count is still 1
    audits_replay = list(
        db_session.scalars(
            select(RbpcContentAudit).where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
        )
    )
    assert len(audits_replay) == 1, "Idempotent POST replay must not duplicate audit entry"


# --------------------------------------------------------------------------- #
# Tests: Zero PII Invariant in Diff Payloads
# --------------------------------------------------------------------------- #
def test_diff_payload_zero_pii_strict_compliance(client, db_session):
    """Test that diff_payload contains zero visitor PII (phone, email, real name, passwords)."""
    partner_email = f"partner_pii_{uuid.uuid4().hex[:6]}@example.com"
    partner = _create_user(db_session, partner_email)
    creator, exp = _create_creator_and_experience(db_session, partner)

    pii_name = "Trần Thị Bích Ngọc"
    pii_email = "bichngoc.hue@example.com"
    pii_phone = "0905123456"
    pii_message = "Xin chào nghệ nhân, tôi muốn tìm hiểu kỹ thuật chạm bạc hoàng cung Huế."

    idem_key = f"idem-key-{uuid.uuid4()}"
    res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": pii_name,
                "method": "email",
                "value": pii_email,
            },
            "preferred_date": (date.today() + timedelta(days=6)).isoformat(),
            "party_size": 2,
            "message": pii_message,
            "consent": {
                "accepted": True,
                "privacy_accepted": True,
                "version": "rbpc-inquiry-v1",
            },
            "idempotency_key": idem_key,
        },
    )
    assert res.status_code == 202
    inquiry_id = db_session.scalar(
        select(RbpcInquiry.id).where(RbpcInquiry.public_ref == res.json()["reference"])
    )

    _login_user(client, partner_email)

    # Transition with partner note containing personal phone and email
    note_with_pii = (
        f"Đã gọi cho khách theo số {pii_phone} và gửi email tới {pii_email} để hẹn lịch."
    )
    res_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": note_with_pii},
    )
    assert res_patch.status_code == 200

    # Inspect all audit records for this inquiry
    audits = list(
        db_session.scalars(
            select(RbpcContentAudit)
            .where(
                RbpcContentAudit.entity_type == ENTITY_INQUIRY,
                RbpcContentAudit.entity_id == inquiry_id,
            )
            .order_by(RbpcContentAudit.created_at.asc())
        )
    )
    assert len(audits) == 2

    forbidden_keys = {
        "name",
        "visitor_name",
        "full_name",
        "contact_value",
        "contact_val",
        "email",
        "phone",
        "phone_number",
        "password",
        "password_hash",
        "message",
        "visitor_message",
        "token",
        "secret",
        "opaque_token",
    }

    for audit in audits:
        payload = audit.diff_payload or {}
        # 1. No forbidden PII key exists in payload
        for key in payload.keys():
            assert (
                key.lower() not in forbidden_keys
            ), f"Found forbidden PII key '{key}' in audit {audit.id}"

        # 2. Raw sensitive contact values do not exist in serialized diff_payload
        payload_str = str(payload)
        assert pii_name not in payload_str, f"Found visitor name in audit diff: {payload_str}"
        assert pii_email not in payload_str, f"Found email in audit diff: {payload_str}"
        assert pii_phone not in payload_str, f"Found phone in audit diff: {payload_str}"
        assert pii_message not in payload_str, f"Found visitor message in audit diff: {payload_str}"

    # Verify that the note in transition audit had email and phone masked to redaction tokens
    transition_audit = audits[1]
    assert "[PHONE_REDACTED]" in transition_audit.diff_payload["note"]
    assert "[EMAIL_REDACTED]" in transition_audit.diff_payload["note"]

    # Verify hash chain is intact despite redaction
    is_valid, errors = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry_id
    )
    assert is_valid is True, f"Audit chain verification failed: {errors}"


# --------------------------------------------------------------------------- #
# Tests: Cryptographic Tamper-Evident Verification
# --------------------------------------------------------------------------- #
def test_audit_ledger_tamper_detection(db_session):
    """Test that modifying an audit row's diff_payload or hash breaks chain verification."""
    partner = _create_user(db_session, f"partner_tamper_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp = _create_creator_and_experience(db_session, partner)

    inquiry = RbpcInquiry(
        public_ref=f"INQ-TAMP-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=partner.id,
        name="Khách Tamper Test",
        contact_channel="email",
        contact_value="tamper@example.com",
        desired_date=date.today() + timedelta(days=5),
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-key-{uuid.uuid4()}",
        opaque_token=f"tok_tamper_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.flush()

    # Create Genesis audit entry
    entry_1 = record_audit_entry(
        db_session,
        entity_type=ENTITY_INQUIRY,
        entity_id=inquiry.id,
        action=ACTION_INQUIRY_CREATED,
        diff_payload={"public_ref": inquiry.public_ref, "state": "new"},
    )

    # Create Transition audit entry
    entry_2 = record_inquiry_state_transition(
        db_session,
        inquiry=inquiry,
        old_state="new",
        new_state=RbpcInquiryStatus.contacted.value,
        note="Chuyển sang contacted",
    )
    db_session.commit()

    # Initial chain is valid
    is_valid_initial, errors_initial = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id
    )
    assert is_valid_initial is True
    assert len(errors_initial) == 0

    # Tamper with entry_1's diff_payload
    entry_1.diff_payload = {"public_ref": inquiry.public_ref, "state": "tampered_state"}
    db_session.commit()

    # Verification must catch the tampered content
    is_valid_tampered, errors_tampered = verify_audit_chain(
        db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id
    )
    assert is_valid_tampered is False
    assert len(errors_tampered) > 0
    assert any("Tampered content" in err for err in errors_tampered)
