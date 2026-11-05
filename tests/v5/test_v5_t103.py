# -*- coding: utf-8 -*-
"""V5-T103: Inquiry Customer Notification Center & Partner SLA Escalation Test Suite.

Audits and verifies:
1. Real tracking status updates with zero PII disclosure:
   - Returns sanitized lifecycle metadata (reference, experience title, status, last updated).
   - Zero contact details (no name, email, phone, message, or internal note leaked).
2. Email and SMS opt-in preferences:
   - Default preferences upon inquiry creation: email_opt_in=True, sms_opt_in=False.
   - Visitor can update preferences via bearer token: POST /preferences.
3. Unsubscribe capabilities:
   - Visitor can opt out of all automatic notifications: POST /unsubscribe.
   - Sets email_opt_in=False, sms_opt_in=False, and stores timestamp in preferences.
4. Partner late response escalation:
   - If inquiry is still 'new' and SLA is overdue (>24h), customer can escalate: POST /escalate.
   - Records escalated_at, increments escalation_count, and stores customer's escalation reason.
   - Rejects escalation if inquiry is still within standard 24h SLA.
   - Rejects escalation if inquiry has already been resolved/closed.
   - Rate limit cooldown protects partner from escalation spam.
5. Negative abuse invariant:
   - Network or provider error during escalation never returns or records fake confirmed/delivered status.
   - Inquiries with withdrawn consent cannot update preferences or escalate.
   - Expired or nonexistent tokens fail closed with HTTP 404 NOT_FOUND.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import select

from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcNotificationOutbox,
    RbpcNotificationStatus,
)
from backend.services.rbpc_notification import (
    NotificationProvider,
    check_partner_sla_status,
    register_notification_provider,
    reset_notification_providers,
)


@pytest.fixture(autouse=True)
def clean_notification_environment():
    """Ensure notification provider registry and rate limit store are clean."""
    reset_notification_providers()
    from backend.routers.rbpc import _inquiry_rate_limit_store
    _inquiry_rate_limit_store.clear()
    yield
    reset_notification_providers()
    _inquiry_rate_limit_store.clear()


def _seed_test_experience(db_session, suffix: str = "") -> RbpcExperience:
    """Helper to persist a test artisan creator and workshop experience."""
    uid = suffix or uuid.uuid4().hex[:6]
    creator = RbpcCreator(
        slug=f"artisan-t103-{uid}",
        public_name=f"Nghệ nhân T103 {uid}",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử trung tâm thông báo.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-t103-{uid}",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Mẫu T103",
        title_vi=f"Workshop Đúc Đồng T103 {uid}",
        description_vi="Trải nghiệm tạo tác khuôn đúc truyền thống.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


def _create_test_inquiry(
    db_session,
    exp: RbpcExperience,
    *,
    hours_ago: float = 0.0,
    state: str = RbpcInquiryStatus.new.value,
    email_opt_in: bool = True,
    sms_opt_in: bool = False,
    privacy_accepted: bool = True,
) -> RbpcInquiry:
    """Helper to seed an inquiry with adjustable creation and SLA timestamps."""
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(hours=hours_ago)
    sla_due_at = created_at + timedelta(hours=24)
    token = f"tok_sec_t103_{uuid.uuid4().hex}"

    inquiry = RbpcInquiry(
        public_ref=f"INQ-T103-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        name="Nguyễn Nhật Nam",
        contact_channel="email",
        contact_value="nhatnam@example.com",
        desired_date=date.today() + timedelta(days=5),
        party_size=2,
        message="Yêu cầu tham quan kèm phiên dịch tiếng Pháp.",
        internal_note="Ghi chú nội bộ mật: không được rò rỉ cho khách.",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=privacy_accepted,
        state=state,
        idempotency_key=f"idem-t103-{uuid.uuid4().hex}",
        opaque_token=token,
        retention_due_at=now + timedelta(days=90),
        sla_due_at=sla_due_at,
        email_opt_in=email_opt_in,
        sms_opt_in=sms_opt_in,
        notification_preferences={"frequency": "immediate"},
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


# ==============================================================================
# 1. Real Tracking Status Updates & Zero PII Invariant
# ==============================================================================
def test_tracking_status_includes_notification_center_metadata_with_zero_pii(client, db_session):
    """Verify GET /api/v1/rbpc/inquiries/status/{opaqueToken} provides notification metadata without PII."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp, hours_ago=5.0)

    res = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}")
    assert res.status_code == 200, res.text
    data = res.json()

    # Public metadata
    assert data["reference"] == inquiry.public_ref
    assert data["status"] == "new"
    assert data["experience_title"] == exp.title_vi

    # Notification center fields
    assert data["email_opt_in"] is True
    assert data["sms_opt_in"] is False
    assert data["is_overdue"] is False
    assert data["can_escalate"] is False
    assert data["escalation_count"] == 0

    # ZERO PII Invariant
    raw_text = res.text
    assert "nhatnam@example.com" not in raw_text
    assert "Nguyễn Nhật Nam" not in raw_text
    assert "Ghi chú nội bộ mật" not in raw_text
    assert "internal_note" not in data


# ==============================================================================
# 2. Update Notification Preferences (Email & SMS Opt-in)
# ==============================================================================
def test_update_notification_preferences(client, db_session):
    """Verify visitor can toggle email and SMS notification preferences."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp)

    # Enable SMS and disable Email
    res = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/preferences",
        json={"email_opt_in": False, "sms_opt_in": True, "frequency": "immediate"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["reference"] == inquiry.public_ref
    assert data["email_opt_in"] is False
    assert data["sms_opt_in"] is True
    assert data["unsubscribed"] is False

    # Verify database persistence
    db_session.refresh(inquiry)
    assert inquiry.email_opt_in is False
    assert inquiry.sms_opt_in is True


# ==============================================================================
# 3. Unsubscribe from All Notifications
# ==============================================================================
def test_unsubscribe_all_notifications(client, db_session):
    """Verify visitor can unsubscribe from both email and SMS updates."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp, email_opt_in=True, sms_opt_in=True)

    res = client.post(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/unsubscribe")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["email_opt_in"] is False
    assert data["sms_opt_in"] is False
    assert data["unsubscribed"] is True

    # Verify status query reflects unsubscribed state
    status_res = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}")
    assert status_res.status_code == 200
    assert status_res.json()["email_opt_in"] is False
    assert status_res.json()["sms_opt_in"] is False


# ==============================================================================
# 4. Partner Late Response Escalation (SLA Overdue)
# ==============================================================================
def test_partner_escalation_succeeds_when_overdue(client, db_session):
    """Verify customer can escalate when inquiry is >24h overdue."""
    exp = _seed_test_experience(db_session)
    # Seed inquiry created 28 hours ago (overdue by 4 hours)
    inquiry = _create_test_inquiry(db_session, exp, hours_ago=28.0)

    # Check status endpoint flags it as overdue and can_escalate=True
    status_res = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}")
    assert status_res.status_code == 200
    assert status_res.json()["is_overdue"] is True
    assert status_res.json()["can_escalate"] is True

    # Dispatch escalation
    res = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Đã 28 giờ chưa nhận được phản hồi, gia đình tôi cần sắp xếp vé xe."},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["reference"] == inquiry.public_ref
    assert data["escalation_count"] == 1
    assert data["sla_overdue_seconds"] > 0

    # Verify database persistence
    db_session.refresh(inquiry)
    assert inquiry.escalated_at is not None
    assert inquiry.escalation_count == 1
    assert "28 giờ chưa nhận được phản hồi" in (inquiry.escalation_reason or "")


def test_escalation_fails_when_within_sla(client, db_session):
    """Verify escalation is rejected when inquiry is within 24h SLA."""
    exp = _seed_test_experience(db_session)
    # Inquiry created only 2 hours ago (22 hours remaining)
    inquiry = _create_test_inquiry(db_session, exp, hours_ago=2.0)

    res = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Tôi muốn trả lời ngay."},
    )
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "RBPC_INQUIRY_SLA_NOT_OVERDUE"


def test_escalation_fails_when_inquiry_already_resolved(client, db_session):
    """Verify escalation is rejected if inquiry is already confirmed or closed."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(
        db_session, exp, hours_ago=30.0, state=RbpcInquiryStatus.confirmed.value
    )

    res = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Nhắc nhở xưởng."},
    )
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "RBPC_INQUIRY_ALREADY_RESOLVED"


def test_escalation_cooldown_rate_limit(client, db_session):
    """Verify repeated escalations within 1 hour are rejected with 429."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp, hours_ago=30.0)

    # First escalation succeeds
    res1 = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Lần nhắc 1."},
    )
    assert res1.status_code == 200

    # Second immediate escalation is throttled
    res2 = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Lần nhắc 2 ngay tức thì."},
    )
    assert res2.status_code == 429
    assert res2.json()["error"]["code"] == "RBPC_ESCALATION_COOLDOWN"


# ==============================================================================
# 5. Negative Abuse Test: Network or Provider Error Never Reports Fake Success
# ==============================================================================
class FailingDeliveryProvider(NotificationProvider):
    """Mock notification provider that throws network drop exceptions."""

    def is_configured(self) -> bool:
        return True

    def send(self, outbox: RbpcNotificationOutbox) -> dict[str, Any]:
        raise ConnectionResetError("502 Bad Gateway: Upstream mail transport unreachable")


def test_negative_abuse_provider_network_failure_never_reports_fake_sent(client, db_session):
    """Negative Abuse Invariant (V5-T103):

    When an upstream network timeout or connection reset occurs during partner escalation,
    the escalation response MUST NOT report notification_dispatched=True or fake 'sent' status.
    The outbox record is marked 'failed_retryable' with the true error message.
    """
    failing_provider = FailingDeliveryProvider()
    register_notification_provider("email", failing_provider)

    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(db_session, exp, hours_ago=35.0)

    res = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Khẩn cấp: Đối tác chậm trễ nghiêm trọng."},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Invariant: notification_dispatched MUST BE FALSE on delivery failure
    assert data["notification_dispatched"] is False

    # Outbox table must record failed_retryable, NEVER fake 'sent'
    outbox = db_session.scalar(
        select(RbpcNotificationOutbox)
        .where(
            RbpcNotificationOutbox.inquiry_id == inquiry.id,
            RbpcNotificationOutbox.event_type == "partner_late_escalation",
        )
    )
    assert outbox is not None
    assert outbox.status == RbpcNotificationStatus.failed_retryable.value
    assert outbox.status != RbpcNotificationStatus.sent.value
    assert outbox.sent_at is None
    assert "ConnectionResetError" in (outbox.last_error or "")


def test_withdrawn_consent_blocks_preferences_and_escalations(client, db_session):
    """Inquiries where visitor has exercised Right to Erasure / Withdrawn Consent fail modifications."""
    exp = _seed_test_experience(db_session)
    inquiry = _create_test_inquiry(
        db_session,
        exp,
        hours_ago=30.0,
        privacy_accepted=False,
        state=RbpcInquiryStatus.closed.value,
    )

    # Preferences update fails
    res_pref = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/preferences",
        json={"email_opt_in": True},
    )
    assert res_pref.status_code == 400
    assert res_pref.json()["error"]["code"] == "RBPC_INQUIRY_WITHDRAWN"

    # Escalation fails
    res_esc = client.post(
        f"/api/v1/rbpc/inquiries/status/{inquiry.opaque_token}/escalate",
        json={"reason": "Thử khiếu nại."},
    )
    assert res_esc.status_code == 400
    assert res_esc.json()["error"]["code"] == "RBPC_INQUIRY_WITHDRAWN"


def test_invalid_status_tokens_fail_closed_with_404(client):
    """Random or malformed tokens return 404 NOT_FOUND."""
    res_get = client.get("/api/v1/rbpc/inquiries/status/non-existent-token-xyz")
    assert res_get.status_code == 404
    assert res_get.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"

    res_post = client.post(
        "/api/v1/rbpc/inquiries/status/non-existent-token-xyz/preferences",
        json={"email_opt_in": True},
    )
    assert res_post.status_code == 404

    res_esc = client.post(
        "/api/v1/rbpc/inquiries/status/non-existent-token-xyz/escalate",
        json={"reason": "Invalid token"},
    )
    assert res_esc.status_code == 404
