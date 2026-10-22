# -*- coding: utf-8 -*-
"""V5-T016: RBPC Inquiry Consent Lifecycle & Retention Privacy Enforcement Test Suite.

Audits and verifies:
1. Consent Tracking & Explicit Opt-In:
   - Inquiry creation fails (HTTP 422) when consent.accepted is False or consent.privacy_accepted is False.
   - Successful creation records consent_version, consent_time_utc, and privacy_accepted=True.
   - Default retention window is set to 90 days (retention_due_at = now + 90 days).
2. Retention Policy Enforcement (Decree 13/2023/ND-CP):
   - Inquiries past retention_due_at (or closed past retention) are anonymized by
     enforce_inquiry_retention_policy().
   - Redacts PII: name="[ANONYMIZED]", contact_value="[REDACTED]", message=None, internal_note=None.
   - Transitions state to "closed" and preserves aggregate metrics (reference, party_size, experience_id).
   - Generates immutable cryptographic audit trail with zero PII in diff_payload.
   - Active inquiries within the 90-day retention window are untouched.
   - Enforcement execution is idempotent.
3. Consent Withdrawal Endpoint (Decree 13/2023/ND-CP Article 11):
   - POST /api/v1/rbpc/inquiries/status/{opaqueToken}/withdraw scrubs visitor PII immediately.
   - Sets privacy_accepted=False and state="closed".
   - Appends append-only audit entry (action="consent_withdrawn").
   - Status lookup endpoint returns state="closed" with zero PII leakage.
   - Non-existent status tokens return HTTP 404 RBPC_INQUIRY_NOT_FOUND.
4. Partner Inbox PII Redaction Shielding:
   - Authenticated partner inbox displays anonymized/redacted values for scrubbed inquiries.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.rbpc_audit import (
    ACTION_RETENTION_PURGE,
    ENTITY_INQUIRY,
    get_audit_trail,
)
from backend.services.rbpc_retention import (
    ACTION_CONSENT_WITHDRAWN,
    ANONYMIZED_NAME,
    REDACTED_CONTACT,
    enforce_inquiry_retention_policy,
    withdraw_inquiry_consent,
)


def _create_test_artisan_and_experience(
    db_session,
    provider_id: uuid.UUID | None = None,
) -> tuple[RbpcCreator, RbpcExperience]:
    """Helper to persist a consented artisan creator and published experience."""
    creator = RbpcCreator(
        slug=f"artisan-consent-{uuid.uuid4().hex[:8]}",
        public_name="Nghệ nhân Thử Nghiệm Đồng Thuận",
        craft_tradition="Đúc đồng Ngũ Xã - Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử vòng đời đồng thuận.",
        consent_status=RbpcConsentStatus.consented.value,
        display_consent_ref="REF-CONSENT-2026-T016",
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-consent-{uuid.uuid4().hex[:8]}",
        creator_id=creator.id,
        provider_id=provider_id or creator.id,
        provider_name="Xưởng Đúc Đồng Thử Nghiệm",
        title_vi="Trải nghiệm đúc đồng di sản",
        description_vi="Thực hành kỹ thuật đúc đồng truyền thống Cố đô.",
        area_public="Huế",
        availability_mode="inquiry_only",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.flush()
    return creator, exp


def _create_test_inquiry(
    db_session,
    experience_id: uuid.UUID,
    *,
    name: str = "Nguyễn Văn Thử Nghiệm",
    contact_value: str = "test.visitor@example.com",
    contact_channel: str = "email",
    message: str | None = "Ghi chú bảo lưu thông tin cá nhân",
    retention_due_at: datetime | None = None,
    state: str = RbpcInquiryStatus.new.value,
    privacy_accepted: bool = True,
    consent_version: str = "rbpc-inquiry-v1",
) -> RbpcInquiry:
    """Helper to insert an inquiry record with explicit retention and consent state."""
    hex_ref = uuid.uuid4().hex[:8].upper()
    inquiry = RbpcInquiry(
        public_ref=f"INQ-{hex_ref[:4]}-{hex_ref[4:]}",
        experience_id=experience_id,
        name=name,
        contact_channel=contact_channel,
        contact_value=contact_value,
        desired_date=date.today() + timedelta(days=14),
        party_size=2,
        message=message,
        consent_version=consent_version,
        consent_time_utc=datetime.now(timezone.utc),
        privacy_accepted=privacy_accepted,
        state=state,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_sec_{uuid.uuid4().hex}",
        retention_due_at=retention_due_at or (datetime.now(timezone.utc) + timedelta(days=90)),
    )
    db_session.add(inquiry)
    db_session.flush()
    return inquiry


# ==============================================================================
# 1. Inquiry Creation Consent Verification Tests
# ==============================================================================

def test_inquiry_creation_consent_verification_rejected_when_not_accepted(client, db_session):
    """POST /api/v1/rbpc/inquiries fails with HTTP 422 if consent.accepted is False."""
    _, exp = _create_test_artisan_and_experience(db_session)

    payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Trần Văn A",
            "method": "email",
            "value": "tranvana@example.com",
        },
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": False,
            "privacy_accepted": True,
        },
        "idempotency_key": str(uuid.uuid4()),
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 422
    # Verify error envelope standard
    data = res.json()
    assert "detail" in data or "error" in data


def test_inquiry_creation_consent_verification_rejected_when_privacy_not_accepted(client, db_session):
    """POST /api/v1/rbpc/inquiries fails with HTTP 422 if privacy_accepted is False."""
    _, exp = _create_test_artisan_and_experience(db_session)

    payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Trần Văn B",
            "method": "phone",
            "value": "0912345678",
        },
        "party_size": 1,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": False,
        },
        "idempotency_key": str(uuid.uuid4()),
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 422


def test_inquiry_creation_consent_and_retention_persisted(client, db_session):
    """POST /api/v1/rbpc/inquiries tracks consent version, privacy acceptance, and 90d retention."""
    _, exp = _create_test_artisan_and_experience(db_session)
    client_key = str(uuid.uuid4())

    payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Lê Thị Cẩm",
            "method": "email",
            "value": "lethicam@example.com",
        },
        "party_size": 3,
        "preferred_date": (date.today() + timedelta(days=20)).isoformat(),
        "message": "Quan tâm kỹ thuật chạm khắc nổi truyền thống.",
        "consent": {
            "version": "rbpc-consent-v2.1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": client_key,
    }

    before_creation = datetime.now(timezone.utc)
    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 202

    data = res.json()
    assert "reference" in data
    assert "status_token" in data
    assert data["status"] == "new"

    # Query DB to inspect consent lifecycle fields and retention
    inq = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == client_key)
    )
    assert inq is not None
    assert inq.consent_version == "rbpc-consent-v2.1"
    assert inq.privacy_accepted is True
    assert inq.consent_time_utc is not None
    assert inq.retention_due_at is not None

    # Verify retention_due_at is roughly 90 days from creation
    expected_retention_min = before_creation + timedelta(days=89)
    expected_retention_max = datetime.now(timezone.utc) + timedelta(days=91)
    assert expected_retention_min <= inq.retention_due_at <= expected_retention_max


# ==============================================================================
# 2. Retention Policy Enforcement Service Tests
# ==============================================================================

def test_retention_policy_enforcement_anonymizes_expired_inquiries(db_session):
    """enforce_inquiry_retention_policy() scrubs PII for inquiries past retention_due_at."""
    _, exp = _create_test_artisan_and_experience(db_session)
    now = datetime.now(timezone.utc)

    # 1. Active inquiry (retention in 80 days) — MUST NOT be touched
    active_inq = _create_test_inquiry(
        db_session,
        exp.id,
        name="Khách Đang Chờ Liên Hệ",
        contact_value="dangcho@example.com",
        message="Yêu cầu đang tiến hành trao đổi.",
        retention_due_at=now + timedelta(days=80),
    )

    # 2. Expired inquiry (retention expired 5 days ago)
    expired_inq_1 = _create_test_inquiry(
        db_session,
        exp.id,
        name="Hoàng Nam Định",
        contact_value="namdinh@example.com",
        message="Thông tin thẻ cá nhân và nhu cầu riêng.",
        retention_due_at=now - timedelta(days=5),
        state=RbpcInquiryStatus.contacted.value,
    )

    # 3. Closed inquiry past retention (expired 20 days ago)
    expired_inq_2 = _create_test_inquiry(
        db_session,
        exp.id,
        name="Phạm Bích Thủy",
        contact_value="0987654321",
        contact_channel="phone",
        message="Chi tiết đặt phòng bảo mật.",
        retention_due_at=now - timedelta(days=20),
        state=RbpcInquiryStatus.closed.value,
    )

    # Execute retention policy enforcement
    result = enforce_inquiry_retention_policy(db_session, reference_time=now)
    assert result["anonymized_count"] >= 2
    assert expired_inq_1.public_ref in result["anonymized_references"]
    assert expired_inq_2.public_ref in result["anonymized_references"]
    assert active_inq.public_ref not in result["anonymized_references"]

    # Verify expired_inq_1 is anonymized
    db_session.refresh(expired_inq_1)
    assert expired_inq_1.name == ANONYMIZED_NAME
    assert expired_inq_1.contact_value == REDACTED_CONTACT
    assert expired_inq_1.message is None
    assert expired_inq_1.internal_note is None
    assert expired_inq_1.state == RbpcInquiryStatus.closed.value
    # Aggregate metrics preserved
    assert expired_inq_1.party_size == 2
    assert expired_inq_1.experience_id == exp.id

    # Verify expired_inq_2 is anonymized
    db_session.refresh(expired_inq_2)
    assert expired_inq_2.name == ANONYMIZED_NAME
    assert expired_inq_2.contact_value == REDACTED_CONTACT
    assert expired_inq_2.message is None
    assert expired_inq_2.state == RbpcInquiryStatus.closed.value

    # Verify active inquiry was completely untouched
    db_session.refresh(active_inq)
    assert active_inq.name == "Khách Đang Chờ Liên Hệ"
    assert active_inq.contact_value == "dangcho@example.com"
    assert active_inq.message == "Yêu cầu đang tiến hành trao đổi."
    assert active_inq.state == RbpcInquiryStatus.new.value

    # Verify cryptographic audit trail exists with zero PII
    audit_entries, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=expired_inq_1.id)
    assert count >= 1
    purge_audit = audit_entries[0]
    assert purge_audit.action == ACTION_RETENTION_PURGE
    payload_str = str(purge_audit.diff_payload)
    assert "Hoàng Nam Định" not in payload_str
    assert "namdinh@example.com" not in payload_str
    assert purge_audit.diff_payload["public_ref"] == expired_inq_1.public_ref

    # Verify idempotency: second enforcement run produces 0 additional anonymizations
    second_result = enforce_inquiry_retention_policy(db_session, reference_time=now)
    assert expired_inq_1.public_ref not in second_result["anonymized_references"]
    assert expired_inq_2.public_ref not in second_result["anonymized_references"]


# ==============================================================================
# 3. Visitor Consent Withdrawal Endpoint Tests
# ==============================================================================

def test_consent_withdrawal_endpoint_redacts_pii_and_marks_state(client, db_session):
    """POST /api/v1/rbpc/inquiries/status/{opaqueToken}/withdraw redacts contact PII immediately."""
    _, exp = _create_test_artisan_and_experience(db_session)
    inquiry = _create_test_inquiry(
        db_session,
        exp.id,
        name="Vũ Đức Đam",
        contact_value="vuducdam@example.com",
        contact_channel="email",
        message="Đề nghị xóa dữ liệu liên hệ cá nhân theo điều 11 Nghị định 13.",
        state=RbpcInquiryStatus.contacted.value,
        privacy_accepted=True,
    )
    token = inquiry.opaque_token

    # Call consent withdrawal endpoint
    res = client.post(f"/api/v1/rbpc/inquiries/status/{token}/withdraw")
    assert res.status_code == 200

    data = res.json()
    assert data["reference"] == inquiry.public_ref
    assert data["status"] == "closed"
    assert data["privacy_accepted"] is False
    assert "Đồng thuận đã được rút lại" in data["status_message"]

    # Verify database state
    db_session.refresh(inquiry)
    assert inquiry.name == ANONYMIZED_NAME
    assert inquiry.contact_value == REDACTED_CONTACT
    assert inquiry.message is None
    assert inquiry.internal_note is None
    assert inquiry.privacy_accepted is False
    assert inquiry.state == RbpcInquiryStatus.closed.value

    # Verify audit entry for consent withdrawal
    audit_entries, count = get_audit_trail(db_session, entity_type=ENTITY_INQUIRY, entity_id=inquiry.id)
    assert count >= 1
    withdrawal_audit = audit_entries[0]
    assert withdrawal_audit.action == ACTION_CONSENT_WITHDRAWN
    payload_str = str(withdrawal_audit.diff_payload)
    assert "Vũ Đức Đam" not in payload_str
    assert "vuducdam@example.com" not in payload_str
    assert withdrawal_audit.diff_payload["privacy_accepted"] is False
    assert withdrawal_audit.diff_payload["new_state"] == "closed"

    # Idempotent re-withdrawal: calling again succeeds without crashing
    res_repeat = client.post(f"/api/v1/rbpc/inquiries/status/{token}/withdraw")
    assert res_repeat.status_code == 200
    assert res_repeat.json()["status"] == "closed"
    assert res_repeat.json()["privacy_accepted"] is False

    # Status check endpoint verification: returns closed status, zero PII leaked
    status_res = client.get(f"/api/v1/rbpc/inquiries/status/{token}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "closed"
    assert "rút lại" in status_data["status_message"]
    # Check zero PII invariant
    assert "vuducdam" not in str(status_data).lower()


def test_consent_withdrawal_non_existent_token_returns_404(client):
    """POST /api/v1/rbpc/inquiries/status/{opaqueToken}/withdraw fails 404 for unknown token."""
    res = client.post("/api/v1/rbpc/inquiries/status/tok_sec_nonexistent12345/withdraw")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"


# ==============================================================================
# 4. Partner Inbox Shielding after Retention & Withdrawal
# ==============================================================================

def test_partner_inbox_pii_shielded_after_retention_and_withdrawal(client, db_session):
    """Authenticated partner inbox displays [ANONYMIZED] and [REDACTED] for scrubbed inquiries."""
    # 1. Create provider user
    provider = User(
        email=f"provider_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("PartnerPassword123!"),
        display_name="Nhà Cung Cấp Di Sản Huế",
        username=f"prov_{uuid.uuid4().hex[:8]}",
        role=UserRole.teacher,
        is_profile_public=True,
    )
    db_session.add(provider)
    db_session.flush()

    _, exp = _create_test_artisan_and_experience(db_session, provider_id=provider.id)

    # 2. Create inquiry and withdraw consent
    inquiry = _create_test_inquiry(
        db_session,
        exp.id,
        name="Khách Hàng Rút Đơn",
        contact_value="rutdon@example.com",
        message="Thông tin nhạy cảm đã bị gỡ.",
    )
    withdraw_inquiry_consent(db_session, opaque_token=inquiry.opaque_token)
    db_session.commit()

    # 3. Log in as partner
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": provider.email, "password": "PartnerPassword123!"},
    )
    assert login_res.status_code == 200

    # 4. Fetch partner inquiries
    inbox_res = client.get("/api/v1/rbpc/partner/inquiries")
    assert inbox_res.status_code == 200
    inbox_data = inbox_res.json()

    target_item = next(
        (item for item in inbox_data["items"] if item["reference"] == inquiry.public_ref),
        None,
    )
    assert target_item is not None
    assert target_item["contact_name"] == ANONYMIZED_NAME
    assert target_item["contact_value"] == REDACTED_CONTACT
    assert target_item["message"] is None
    assert target_item["status"] == "closed"
