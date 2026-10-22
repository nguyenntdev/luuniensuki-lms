# -*- coding: utf-8 -*-
"""V5-T012: Token Status Strict Server Lookup Test Suite.

Audits and verifies:
1. Strict server token lookup:
   - Non-existent and random tokens return HTTP 404 NOT_FOUND.
   - Whitespace and malformed tokens return HTTP 404 NOT_FOUND.
   - Standard error envelope {"error": {"code": "RBPC_INQUIRY_NOT_FOUND", ...}} is returned.
2. TTL & Retention expiration enforcement:
   - Inquiries whose retention_due_at has passed return HTTP 404 NOT_FOUND.
   - Active inquiries with future retention_due_at return HTTP 200 OK.
3. Zero PII Invariant:
   - Valid status token lookup returns only non-sensitive lifecycle metadata
     (reference, experience_title, status, status_message, preferred_date, party_size, last_updated_at).
   - Zero visitor PII is returned (no contact name, email, phone, message, or internal notes).
   - Raw response payload contains zero sensitive substrings.
4. Elimination of client seed fallbacks:
   - All references and IDs from client seed data (INQ-7F89-A23C, INQ-6E21-B44D, etc.)
     are strictly rejected by the server with HTTP 404 NOT_FOUND.
   - Server never recognizes mock or seed data as valid status tokens.
5. Timing-safe nonce verification & wildcard rejection:
   - Partial token prefixes, appended tokens, and SQL wildcards (% / _) fail closed with 404.
6. Consent withdrawal status transition:
   - Withdrawing consent transitions lifecycle state to 'closed' while maintaining zero PII.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)

# Seed reference codes and IDs from client-side SEED_PARTNER_INQUIRIES
CLIENT_SEED_IDENTIFIERS = [
    "INQ-7F89-A23C",
    "INQ-6E21-B44D",
    "INQ-5B10-C89E",
    "INQ-4A02-D11F",
    "INQ-3C98-E52A",
    "inq-001",
    "inq-002",
    "inq-003",
    "inq-004",
    "inq-005",
]


def _create_test_experience(db_session) -> RbpcExperience:
    """Helper to persist a published cultural workshop experience."""
    creator = RbpcCreator(
        slug=f"creator-t012-{uuid.uuid4().hex[:8]}",
        public_name="Nghệ nhân Kiểm thử T012",
        craft_tradition="Đúc đồng thủ công Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử tích hợp T012.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-t012-{uuid.uuid4().hex[:8]}",
        creator_id=creator.id,
        provider_id=creator.id,
        provider_name="Xưởng Đúc Đồng Gia Tộc Nguyễn Văn",
        title_vi="Trải nghiệm Đúc Đồng Phường Đúc",
        title_en="Bronze Smelting Masterclass",
        description_vi="Khóa trải nghiệm nghệ thuật đúc đồng truyền thống.",
        area_public="Phường Đúc, Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


def _create_test_inquiry(
    db_session,
    exp_id: uuid.UUID,
    *,
    name: str = "Nguyễn An Nhiên",
    contact_value: str = "annhien.nguyen@example.com",
    contact_channel: str = "email",
    desired_date: date | None = None,
    party_size: int = 2,
    message: str | None = "Chúng tôi muốn tìm hiểu kỹ nghệ đúc chuông Huế.",
    internal_note: str | None = "Ghi chú nội bộ mật: Cần bố trí chỗ đậu xe.",
    state: str = RbpcInquiryStatus.new.value,
    retention_due_at: datetime | None = None,
    opaque_token: str | None = None,
) -> RbpcInquiry:
    """Helper to persist a test inquiry with specific PII and lifecycle parameters."""
    hex_ref = uuid.uuid4().hex[:8].upper()
    public_ref = f"INQ-{hex_ref[:4]}-{hex_ref[4:]}"
    tok = opaque_token or f"tok_sec_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)

    inquiry = RbpcInquiry(
        public_ref=public_ref,
        experience_id=exp_id,
        name=name,
        contact_channel=contact_channel,
        contact_value=contact_value,
        desired_date=desired_date or (date.today() + timedelta(days=14)),
        party_size=party_size,
        message=message,
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=state,
        internal_note=internal_note,
        idempotency_key=f"idem-t012-{uuid.uuid4().hex}",
        opaque_token=tok,
        retention_due_at=retention_due_at or (now + timedelta(days=90)),
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


# ==============================================================================
# 1. Non-existent and Random Token Lookup Rejection
# ==============================================================================


def test_nonexistent_and_random_tokens_return_404_not_found(client):
    """Unknown, random, and whitespace tokens return standard HTTP 404 error envelope."""
    # 1. Random 32-hex token that does not exist in DB
    random_token = f"tok_sec_{uuid.uuid4().hex}"
    res = client.get(f"/api/v1/rbpc/inquiries/status/{random_token}")
    assert res.status_code == 404, f"Expected 404 for random token, got: {res.status_code}"
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"
    assert "không tìm thấy" in body["error"]["message"].lower() or "not found" in body["error"]["message"].lower()

    # 2. Arbitrary formatted string
    res_arbitrary = client.get("/api/v1/rbpc/inquiries/status/arbitrary_nonexistent_token_xyz")
    assert res_arbitrary.status_code == 404
    assert res_arbitrary.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"

    # 3. Whitespace token fails closed
    res_whitespace = client.get("/api/v1/rbpc/inquiries/status/%20%20")
    assert res_whitespace.status_code == 404
    assert res_whitespace.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"


# ==============================================================================
# 2. TTL & Retention Expiration Enforcement
# ==============================================================================


def test_expired_tokens_return_404_not_found(client, db_session):
    """Inquiries whose retention window has elapsed return 404 NOT_FOUND."""
    exp = _create_test_experience(db_session)
    now = datetime.now(timezone.utc)

    # 1. Expired inquiry (retention expired 10 days ago)
    expired_token = f"tok_sec_expired_{uuid.uuid4().hex[:16]}"
    inquiry_expired = _create_test_inquiry(
        db_session,
        exp.id,
        retention_due_at=now - timedelta(days=10),
        opaque_token=expired_token,
    )

    res_expired = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry_expired.opaque_token}")
    assert res_expired.status_code == 404, (
        f"Expired inquiry token must return 404, got {res_expired.status_code}"
    )
    assert res_expired.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"

    # 2. Active inquiry with unexpired retention (due in 85 days)
    active_token = f"tok_sec_active_{uuid.uuid4().hex[:16]}"
    inquiry_active = _create_test_inquiry(
        db_session,
        exp.id,
        retention_due_at=now + timedelta(days=85),
        opaque_token=active_token,
    )

    res_active = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry_active.opaque_token}")
    assert res_active.status_code == 200
    assert res_active.json()["reference"] == inquiry_active.public_ref
    assert res_active.json()["status"] == "new"


# ==============================================================================
# 3. Valid Token Lookup with Strict Zero PII Audit
# ==============================================================================


def test_valid_token_status_lookup_redacted_zero_pii_audit(client, db_session):
    """Valid token returns non-sensitive status metadata and strictly redacts all visitor PII."""
    exp = _create_test_experience(db_session)
    future_date = date.today() + timedelta(days=21)

    # Inquire with high-sensitivity personal information
    inquiry = _create_test_inquiry(
        db_session,
        exp.id,
        name="Phạm Bích Thủy Tiên",
        contact_channel="phone",
        contact_value="0935123987",
        desired_date=future_date,
        party_size=3,
        message="Gia đình có 1 cụ già 80 tuổi, cần phòng mát và hỗ trợ lên bậc thềm.",
        internal_note="Ghi chú đối tác mật: Đã xác nhận chuẩn bị ghế chuyên dụng cho cụ bà.",
        state=RbpcInquiryStatus.contacted.value,
    )

    client.cookies.clear()
    res = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}")
    assert res.status_code == 200, res.text
    data = res.json()

    # Allowed non-sensitive lifecycle fields
    assert data["reference"] == inquiry.public_ref
    assert data["experience_title"] == exp.title_vi
    assert data["status"] == "contacted"
    assert "liên hệ" in data["status_message"]
    assert data["preferred_date"] == future_date.isoformat()
    assert data["party_size"] == 3
    assert "last_updated_at" in data

    # STRICT ZERO PII INVARIANT:
    # 1. Structural dictionary keys validation
    forbidden_keys = [
        "name",
        "contact_name",
        "email",
        "phone",
        "contact",
        "contact_value",
        "contact_channel",
        "message",
        "internal_note",
        "partner_notes",
        "user_id",
        "provider_id",
        "ip_address",
        "idempotency_key",
    ]
    for key in forbidden_keys:
        assert key not in data, f"PII Leak: key '{key}' was disclosed in status response!"

    # 2. Raw response text validation: sensitive submitted substrings must never leak
    raw_text = res.text.lower()
    assert "phạm bích thủy tiên" not in raw_text, "PII Leak: Visitor name leaked in response text!"
    assert "0935123987" not in raw_text, "PII Leak: Visitor phone number leaked in response text!"
    assert "80 tuổi" not in raw_text, "PII Leak: Visitor health/message details leaked!"
    assert "bậc thềm" not in raw_text, "PII Leak: Visitor message leaked!"
    assert "ghế chuyên dụng" not in raw_text, "PII Leak: Internal partner note leaked!"
    assert "đối tác mật" not in raw_text, "PII Leak: Internal note leaked!"


# ==============================================================================
# 4. Elimination of Client Seed Fallbacks on Server
# ==============================================================================


def test_client_seed_references_never_recognized_by_server(client, db_session):
    """Server strictly fails 404 for all mock client seed references and never accepts fake seeds."""
    for seed_id in CLIENT_SEED_IDENTIFIERS:
        res = client.get(f"/api/v1/rbpc/inquiries/status/{seed_id}")
        assert res.status_code == 404, (
            f"Client seed identifier '{seed_id}' was fraudulently recognized as a valid server token! "
            f"Status code: {res.status_code}"
        )
        assert res.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"


# ==============================================================================
# 5. Timing-Safe Nonce Verification & Wildcard Rejection
# ==============================================================================


def test_token_timing_safe_nonce_compare_and_wildcard_rejection(client, db_session):
    """Token lookup requires full exact matching and rejects prefixes, suffixes, and wildcards."""
    exp = _create_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp.id)
    real_token = inquiry.opaque_token

    # 1. Partial prefix of valid token fails with 404
    prefix_token = real_token[:16]
    res_prefix = client.get(f"/api/v1/rbpc/inquiries/status/{prefix_token}")
    assert res_prefix.status_code == 404
    assert res_prefix.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"

    # 2. Appended token fails with 404
    appended_token = f"{real_token}extra"
    res_appended = client.get(f"/api/v1/rbpc/inquiries/status/{appended_token}")
    assert res_appended.status_code == 404

    # 3. SQL wildcards fail closed with 404
    res_wildcard_pct = client.get("/api/v1/rbpc/inquiries/status/%25")
    assert res_wildcard_pct.status_code == 404
    res_wildcard_underscore = client.get("/api/v1/rbpc/inquiries/status/_")
    assert res_wildcard_underscore.status_code == 404


# ==============================================================================
# 6. Withdrawn Consent Status Zero PII
# ==============================================================================


def test_withdrawn_consent_status_retains_zero_pii(client, db_session):
    """Withdrawing consent transitions state to 'closed' and maintains strict zero PII."""
    exp = _create_test_experience(db_session)
    inquiry = _create_test_inquiry(
        db_session,
        exp.id,
        name="Vũ Đức Đam",
        contact_value="dam.vu@example.vn",
        message="Thông tin nhạy cảm cần xóa.",
        internal_note="Ghi chú nội bộ bí mật.",
    )

    # 1. Withdraw consent
    res_withdraw = client.post(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/withdraw")
    assert res_withdraw.status_code == 200
    assert res_withdraw.json()["status"] == "closed"
    assert res_withdraw.json()["privacy_accepted"] is False

    # 2. Status lookup on withdrawn inquiry
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "closed"
    assert "rút lại" in data["status_message"]

    # Verify zero PII in withdrawn status
    assert "vũ đức đam" not in res_status.text.lower()
    assert "dam.vu@example.vn" not in res_status.text.lower()
    assert "thông tin nhạy cảm" not in res_status.text.lower()
