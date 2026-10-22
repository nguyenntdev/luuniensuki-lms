# -*- coding: utf-8 -*-
"""V5-T019: Real Notification Outbox Queue and Partner SLA Tracking Test Suite.

Audits and verifies:
1. Inquiry creation queues a partner alert in the durable outbox table (rbpc_notification_outbox).
2. Negative abuse test:
   When notification provider is unconfigured, down, or throws network exceptions
   (SMTP gateway timeout, Zalo API connection drop), the inquiry creation transaction
   MUST NOT FAIL. The inquiry commits successfully, and the outbox record is stored with
   status 'queued' or 'failed_retryable'. Zero fake 'sent' confirmations are tolerated.
3. Partner SLA calculation:
   SLA response deadline is correctly computed as 24h from created_at (sla_due_at).
   check_partner_sla_status returns accurate within_sla, overdue, and met states.
4. Positive verified delivery:
   Authentic provider confirmation records status 'sent' with sent_at timestamp.
5. Strict Zero-PII sanitization:
   Masked recipients and clean operational payloads without visitor contact details.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import select

from backend.models import User, UserRole
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
    DEFAULT_PARTNER_SLA_HOURS,
    NotificationProvider,
    check_partner_sla_status,
    compute_next_retry,
    compute_sla_deadline,
    mask_email,
    mask_phone,
    mask_recipient,
    queue_inquiry_notification,
    register_notification_provider,
    reset_notification_providers,
)


@pytest.fixture(autouse=True)
def clean_provider_registry():
    """Ensure provider registry and rate limit store are clean before and after each test."""
    reset_notification_providers()
    from backend.routers.rbpc import _inquiry_rate_limit_store
    _inquiry_rate_limit_store.clear()
    yield
    reset_notification_providers()
    _inquiry_rate_limit_store.clear()


def _seed_test_experience(db_session, slug_suffix: str = "") -> tuple[RbpcCreator, RbpcExperience]:
    """Helper to seed a consented creator and published experience."""
    suffix = slug_suffix or uuid.uuid4().hex[:6]
    creator = RbpcCreator(
        slug=f"artisan-notif-{suffix}",
        public_name=f"Nghệ nhân Thông Báo {suffix}",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân phục vụ kiểm thử thông báo.",
        consent_status=RbpcConsentStatus.consented.value,
        public_region="Huế",
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-notif-{suffix}",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Mẫu",
        title_vi=f"Workshop Đúc Đồng {suffix}",
        description_vi="Trải nghiệm tạo tác khuôn đúc.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    return creator, exp


# ==============================================================================
# 1. Inquiry Creation Queues Notification in Outbox
# ==============================================================================
def test_inquiry_creation_queues_notification_in_outbox(client, db_session):
    """Test that POST /api/v1/rbpc/inquiries creates inquiry and queues an outbox record."""
    _, exp = _seed_test_experience(db_session)

    future_date = (date.today() + timedelta(days=7)).isoformat()
    unique_key = f"idem-key-{uuid.uuid4().hex}"

    payload = {
        "experience_slug": exp.slug,
        "contact": {"name": "Nguyễn Hoàng Nam", "method": "email", "value": "nam@example.com"},
        "preferred_date": future_date,
        "party_size": 3,
        "message": "Cần hỗ trợ hướng dẫn viên tiếng Anh.",
        "consent": {"version": "rbpc-inquiry-v1", "accepted": True, "privacy_accepted": True},
        "idempotency_key": unique_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 202, res.text
    data = res.json()
    assert data["status"] == "new"
    public_ref = data["reference"]

    # Verify inquiry committed in database with SLA deadline
    inquiry = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref)
    )
    assert inquiry is not None
    assert inquiry.state == RbpcInquiryStatus.new.value
    assert inquiry.sla_due_at is not None

    # Verify SLA deadline is set to approximately 24h from created_at
    created_time = inquiry.created_at
    sla_diff = (inquiry.sla_due_at - created_time).total_seconds()
    assert abs(sla_diff - 86400.0) < 10.0  # Exactly 24 hours within 10s tolerance

    # Verify outbox table has corresponding partner alert
    outbox = db_session.scalar(
        select(RbpcNotificationOutbox).where(RbpcNotificationOutbox.inquiry_id == inquiry.id)
    )
    assert outbox is not None
    assert outbox.event_type == "inquiry_created"
    assert outbox.channel == "email"
    assert outbox.status in (
        RbpcNotificationStatus.queued.value,
        RbpcNotificationStatus.failed_retryable.value,
    )
    # Never fake "sent" when unconfigured
    assert outbox.status != RbpcNotificationStatus.sent.value
    assert outbox.sent_at is None

    # Verify clean operational payload (zero raw visitor contact details)
    clean = outbox.payload_clean
    assert clean["public_ref"] == public_ref
    assert clean["experience_slug"] == exp.slug
    assert clean["party_size"] == 3
    assert clean["preferred_date"] == future_date
    assert "email" not in clean
    assert "phone" not in clean
    assert "contact_value" not in clean


# ==============================================================================
# 2. Negative Abuse Test: Provider Network Failure / Outage
# ==============================================================================
class FailingNetworkProvider(NotificationProvider):
    """Mock provider simulating upstream network timeout or connection reset."""

    def __init__(self, error_type: str = "timeout"):
        self.error_type = error_type

    def is_configured(self) -> bool:
        return True

    def send(self, outbox: RbpcNotificationOutbox) -> dict[str, Any]:
        if self.error_type == "timeout":
            raise TimeoutError("Upstream SMTP/Zalo gateway 504 Gateway Timeout (socket dropped)")
        elif self.error_type == "connection":
            raise ConnectionError("Connection refused: smtp.sendgrid.net:587")
        else:
            return {"success": False, "error": "Zalo ZNS quota exceeded (HTTP 429)"}


def test_negative_abuse_provider_network_failure_retains_inquiry_and_outbox_failed(client, db_session):
    """Negative Abuse Test:

    When notification provider throws network exception or returns failure,
    inquiry transaction MUST NOT FAIL: inquiry commits successfully,
    and notification record is marked 'failed_retryable' or 'failed',
    NEVER fake 'sent'.
    """
    # 1. Register a provider that throws socket TimeoutError
    failing_provider = FailingNetworkProvider(error_type="timeout")
    register_notification_provider("email", failing_provider)

    _, exp = _seed_test_experience(db_session)
    future_date = (date.today() + timedelta(days=14)).isoformat()
    unique_key = f"idem-key-{uuid.uuid4().hex}"

    payload = {
        "experience_slug": exp.slug,
        "contact": {"name": "Lê Văn Cường", "method": "email", "value": "cuong@example.com"},
        "preferred_date": future_date,
        "party_size": 2,
        "consent": {"version": "rbpc-inquiry-v1", "accepted": True, "privacy_accepted": True},
        "idempotency_key": unique_key,
    }

    # 2. Submit inquiry: must return 202 Accepted despite provider network outage
    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 202, f"Inquiry submission should not fail when provider is down: {res.text}"
    data = res.json()
    public_ref = data["reference"]

    # 3. Verify inquiry was committed successfully to database
    inquiry = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref)
    )
    assert inquiry is not None
    assert inquiry.state == RbpcInquiryStatus.new.value

    # 4. Verify notification outbox record exists
    outbox = db_session.scalar(
        select(RbpcNotificationOutbox).where(RbpcNotificationOutbox.inquiry_id == inquiry.id)
    )
    assert outbox is not None

    # CRITICAL INVARIANT: NEVER report fake 'sent' status
    assert outbox.status != RbpcNotificationStatus.sent.value
    assert outbox.status == RbpcNotificationStatus.failed_retryable.value
    assert outbox.sent_at is None
    assert outbox.attempts == 1
    assert "TimeoutError" in (outbox.last_error or "")
    assert outbox.next_retry_at is not None
    assert outbox.next_retry_at > datetime.now(timezone.utc)


def test_negative_abuse_provider_429_quota_failure_retains_inquiry(client, db_session):
    """Negative Abuse Test: Provider returns upstream 429 rate limit or schema rejection."""
    failing_provider = FailingNetworkProvider(error_type="rate_limit")
    register_notification_provider("email", failing_provider)

    _, exp = _seed_test_experience(db_session)
    future_date = (date.today() + timedelta(days=5)).isoformat()
    unique_key = f"idem-key-{uuid.uuid4().hex}"

    payload = {
        "experience_slug": exp.slug,
        "contact": {"name": "Trần Thị Mai", "method": "email", "value": "mai@example.com"},
        "preferred_date": future_date,
        "party_size": 1,
        "consent": {"version": "rbpc-inquiry-v1", "accepted": True, "privacy_accepted": True},
        "idempotency_key": unique_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 202
    public_ref = res.json()["reference"]

    inquiry = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref))
    assert inquiry is not None

    outbox = db_session.scalar(select(RbpcNotificationOutbox).where(RbpcNotificationOutbox.inquiry_id == inquiry.id))
    assert outbox is not None
    assert outbox.status == RbpcNotificationStatus.failed_retryable.value
    assert "quota exceeded" in (outbox.last_error or "")
    assert outbox.sent_at is None


# ==============================================================================
# 3. Partner SLA Response Deadline Calculation & Status Checks
# ==============================================================================
def test_sla_deadline_computation():
    """Verify compute_sla_deadline sets deadline to exactly 24 hours from creation."""
    fixed_created = datetime(2026, 10, 21, 10, 0, 0, tzinfo=timezone.utc)
    deadline = compute_sla_deadline(fixed_created, hours=24)
    expected = datetime(2026, 10, 22, 10, 0, 0, tzinfo=timezone.utc)
    assert deadline == expected
    assert (deadline - fixed_created).total_seconds() == 86400.0


def test_check_partner_sla_status_within_sla():
    """Verify check_partner_sla_status evaluates within_sla when time has not elapsed."""
    created = datetime(2026, 10, 21, 8, 0, 0, tzinfo=timezone.utc)
    sla_due = created + timedelta(hours=24)

    mock_inquiry = type("MockInquiry", (), {
        "created_at": created,
        "sla_due_at": sla_due,
        "state": "new",
    })()

    # Evaluated 4 hours after creation (20 hours remaining)
    as_of = created + timedelta(hours=4)
    res = check_partner_sla_status(mock_inquiry, as_of=as_of)

    assert res.is_within_sla is True
    assert res.is_overdue is False
    assert res.status == "within_sla"
    assert res == "within_sla"
    assert res["is_within_sla"] is True
    assert res["is_overdue"] is False
    assert res.hours_remaining == 20.0
    assert res.overdue_by_seconds == 0.0


def test_check_partner_sla_status_overdue():
    """Verify check_partner_sla_status identifies overdue inquiries (> 24 hours)."""
    created = datetime(2026, 10, 21, 8, 0, 0, tzinfo=timezone.utc)
    sla_due = created + timedelta(hours=24)

    mock_inquiry = type("MockInquiry", (), {
        "created_at": created,
        "sla_due_at": sla_due,
        "state": "new",
    })()

    # Evaluated 26 hours after creation (2 hours overdue)
    as_of = created + timedelta(hours=26)
    res = check_partner_sla_status(mock_inquiry, as_of=as_of)

    assert res.is_within_sla is False
    assert res.is_overdue is True
    assert res.status == "overdue"
    assert res == "overdue"
    assert res["is_within_sla"] is False
    assert res["is_overdue"] is True
    assert res.hours_remaining == 0.0
    assert res.overdue_by_seconds == 7200.0


def test_check_partner_sla_status_met_when_responded():
    """Verify check_partner_sla_status evaluates 'met' when partner has contacted/confirmed."""
    created = datetime(2026, 10, 21, 8, 0, 0, tzinfo=timezone.utc)
    sla_due = created + timedelta(hours=24)

    for state in ("contacted", "confirmed", "declined", "closed"):
        mock_inquiry = type("MockInquiry", (), {
            "created_at": created,
            "sla_due_at": sla_due,
            "state": state,
        })()
        # Even if 48 hours passed, if partner already actioned it, SLA is met
        as_of = created + timedelta(hours=48)
        res = check_partner_sla_status(mock_inquiry, as_of=as_of)
        assert res.is_within_sla is True
        assert res.is_overdue is False
        assert res.status == "met"
        assert res == "met"


# ==============================================================================
# 4. Positive Verified Provider Dispatch
# ==============================================================================
class VerifiedSuccessProvider(NotificationProvider):
    """Mock provider simulating confirmed live delivery."""

    def is_configured(self) -> bool:
        return True

    def send(self, outbox: RbpcNotificationOutbox) -> dict[str, Any]:
        return {
            "success": True,
            "provider_ref": "smtp-sg-live-98234",
        }


def test_positive_provider_dispatch_marks_sent(db_session):
    """Verify that only an authentically confirmed provider marks status 'sent'."""
    success_provider = VerifiedSuccessProvider()
    register_notification_provider("email", success_provider)

    _, exp = _seed_test_experience(db_session)
    now = datetime.now(timezone.utc)
    inquiry = RbpcInquiry(
        public_ref="INQ-TEST-SUCCESS",
        experience_id=exp.id,
        name="Đỗ Kỳ",
        contact_channel="email",
        contact_value="doky@example.com",
        desired_date=date.today() + timedelta(days=3),
        party_size=4,
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-success-{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_success_{uuid.uuid4().hex}",
        created_at=now,
        sla_due_at=now + timedelta(hours=24),
    )
    db_session.add(inquiry)
    db_session.flush()

    outbox = queue_inquiry_notification(db_session, inquiry, event_type="inquiry_created", channel="email")
    db_session.commit()
    db_session.refresh(outbox)

    # When provider confirms delivery, record status 'sent' with sent_at populated
    assert outbox.status == RbpcNotificationStatus.sent.value
    assert outbox.sent_at is not None
    assert outbox.attempts == 1
    assert outbox.last_error is None


# ==============================================================================
# 5. Masking & Zero-PII Verification
# ==============================================================================
def test_masking_utilities():
    """Verify email and phone masking sanitize PII."""
    assert mask_email("artisan.phuongduc@gmail.com") == "a***c@gmail.com"
    assert mask_email("me@domain.com") == "m***@domain.com"
    assert mask_phone("0988123456") == "0988 ••• 456"
    assert mask_phone("+84905123789") == "+849 ••• 789"
    assert mask_recipient("test@hue.vn", "email") == "t***t@hue.vn"
    assert mask_recipient("0912345678", "sms") == "0912 ••• 678"


def test_backoff_calculation_limits():
    """Verify exponential backoff calculation remains within bounds."""
    t1 = compute_next_retry(attempts=1, base_seconds=2.0, max_seconds=60.0)
    t2 = compute_next_retry(attempts=2, base_seconds=2.0, max_seconds=60.0)
    t5 = compute_next_retry(attempts=5, base_seconds=2.0, max_seconds=60.0)
    t10 = compute_next_retry(attempts=10, base_seconds=2.0, max_seconds=60.0)

    now = datetime.now(timezone.utc)
    assert (t1 - now).total_seconds() >= 1.9
    assert (t2 - now).total_seconds() >= 3.9
    assert (t5 - now).total_seconds() >= 31.9
    # Must cap at max_seconds (60s)
    assert (t10 - now).total_seconds() <= 61.0
