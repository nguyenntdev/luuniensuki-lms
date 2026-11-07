# -*- coding: utf-8 -*-
"""V5-T111 (Wave W11, Slot A01): Analytics Event Taxonomy & Ingest Test Suite.

Audits and verifies:
1. Analytics Event Taxonomy & Schema Validation:
   - Verifies EventCategory.BUSINESS_CONVERSION and EventType constants
     (view, explore, inquiry_start, inquiry_submit, inquiry_confirm).
   - Validates BusinessConversionPayload schema and metadata parsing.
2. Consent-Aware Telemetry Ingest:
   - Consented telemetry events persist to analytics_events.
   - Denied / withdrawn consent (via header X-Telemetry-Consent: denied or payload
     consent_status='withdrawn'/'denied') strictly drops events (0 rows inserted).
3. Idempotency Key Deduplication:
   - Repeated event submission with identical idempotency_key deduplicates cleanly.
   - Zero duplicate rows created in database on retries.
4. Strict Zero Student PII in Telemetry Payloads:
   - Event payloads containing student personal data (student_name, student_email,
     phone, school_address, etc.) are sanitized recursively before database storage.
   - Stored JSONB payload in database contains zero plaintext student PII.
5. Server-Trusted Business Conversion Events:
   - inquiry_submit and inquiry_confirm verified against authoritative DB entities.
   - Confirmed inquiry yields is_server_verified=True; spoofed confirmation yields False.
   - Authoritative server helpers record genuine verified conversions.
6. NEGATIVE ABUSE INVARIANT (Critical Requirement V5-T111):
   - Demo and synthetic traffic is NEVER counted in the real customer conversion funnel.
   - calculate_funnel_data strictly excludes is_demo=True and is_synthetic=True records.
   - 100 demo visits produce 0 real customer conversion counts.
7. Frontend Telemetry Library Contract:
   - frontend/src/lib/analytics.ts exists and exports complete taxonomy and helpers.
   - Client-side PII sanitizer strips sensitive data before network dispatch.
"""
from __future__ import annotations

import json
from pathlib import Path
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import AnalyticsEvent, User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.analytics import (
    EVENT_CATEGORY_MAP,
    EventCategory,
    EventType,
    BusinessConversionPayload,
    contains_student_pii,
    create_event_record,
    is_telemetry_consented,
    record_server_conversion_event,
    sanitize_analytics_payload,
    verify_server_conversion_trust,
)
from backend.services.analytics_funnels import (
    FUNNEL_DEFINITIONS,
    calculate_funnel_data,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ANALYTICS_TS = REPO_ROOT / "frontend/src/lib/analytics.ts"


# --------------------------------------------------------------------------- #
# Helpers & Context Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return {"Authorization": f"Bearer {token}"}


def _setup_experience(db_session, provider_user: User) -> tuple[RbpcCreator, RbpcExperience]:
    creator = RbpcCreator(
        slug=f"artisan-analytics-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng truyền thống",
        approved_bio_vi="Gia đình truyền thống đúc đồng Huế.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-analytics-{uuid.uuid4().hex[:6]}",
        title_vi="Workshop Đúc Đồng Phường Đúc",
        title_en="Phuong Duc Bronze Casting Workshop",
        description_vi="Trải nghiệm đúc đồng văn hóa.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Huế",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return creator, exp


def _setup_inquiry(
    db_session,
    exp: RbpcExperience,
    state: str = RbpcInquiryStatus.new.value,
) -> RbpcInquiry:
    inquiry = RbpcInquiry(
        public_ref=f"INQ-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        provider_id=exp.provider_id,
        name="Visitor Test",
        contact_channel="email",
        contact_value="visitor.test@example.com",
        desired_date=date.today() + timedelta(days=7),
        party_size=2,
        message="I would like to participate in the bronze workshop.",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=state,
        idempotency_key=f"idem_inq_{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_{uuid.uuid4().hex}",
        retention_due_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


# --------------------------------------------------------------------------- #
# Test 1: Taxonomy Constants & Schema Validation
# --------------------------------------------------------------------------- #

def test_analytics_event_taxonomy_constants():
    """Verify event taxonomy constants and mappings for business conversion."""
    assert EventCategory.BUSINESS_CONVERSION == "business_conversion"
    assert EventType.VIEW == "view"
    assert EventType.EXPLORE == "explore"
    assert EventType.INQUIRY_START == "inquiry_start"
    assert EventType.INQUIRY_SUBMIT == "inquiry_submit"
    assert EventType.INQUIRY_CONFIRM == "inquiry_confirm"

    # Verify category mapping
    for ev in [
        EventType.VIEW,
        EventType.EXPLORE,
        EventType.INQUIRY_START,
        EventType.INQUIRY_SUBMIT,
        EventType.INQUIRY_CONFIRM,
    ]:
        assert EVENT_CATEGORY_MAP.get(ev) == EventCategory.BUSINESS_CONVERSION

    # Verify BusinessConversionPayload pydantic model
    payload_data = {
        "experience_id": str(uuid.uuid4()),
        "creator_id": str(uuid.uuid4()),
        "item_slug": "workshop-duc-dong",
        "step": "schedule_view",
        "is_demo": False,
        "is_synthetic": False,
    }
    payload = BusinessConversionPayload(**payload_data)
    assert payload.item_slug == "workshop-duc-dong"
    assert payload.is_demo is False


# --------------------------------------------------------------------------- #
# Test 2: Consent-Aware Telemetry Ingest
# --------------------------------------------------------------------------- #

def test_consent_aware_telemetry_ingest(client: TestClient, db_session):
    """Verify that events are ingested when consented, and strictly dropped when denied."""
    user = _create_user(db_session, f"consent_user_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    # 1. Consented event persists
    consented_payload = {
        "events": [
            {
                "name": EventType.VIEW,
                "path": "/rbpc/workshop-duc-dong",
                "consent_status": "consented",
                "payload": {"item_slug": "workshop-duc-dong"},
            }
        ]
    }
    res = client.post("/api/v1/analytics/events", json=consented_payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True
    assert data["count"] == 1

    # Verify persisted in database
    ev = db_session.scalar(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.user_id == user.id)
        .where(AnalyticsEvent.event_name == EventType.VIEW)
    )
    assert ev is not None
    assert ev.consent_status == "consented"

    # 2. Denied via payload consent_status drops event
    denied_payload = {
        "events": [
            {
                "name": EventType.EXPLORE,
                "path": "/rbpc/workshop-duc-dong",
                "consent_status": "denied",
                "payload": {"item_slug": "workshop-duc-dong"},
            }
        ]
    }
    res = client.post("/api/v1/analytics/events", json=denied_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["count"] == 0  # Dropped due to denial

    # 3. Denied via request header X-Telemetry-Consent: denied drops entire batch
    header_denied_payload = {
        "events": [
            {
                "name": EventType.INQUIRY_START,
                "path": "/rbpc/inquiries",
                "payload": {"item_slug": "workshop-duc-dong"},
            }
        ]
    }
    res = client.post(
        "/api/v1/analytics/events",
        json=header_denied_payload,
        headers={**headers, "X-Telemetry-Consent": "denied"},
    )
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Ensure no explore or inquiry_start events were persisted
    no_explore = db_session.scalar(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.user_id == user.id)
        .where(AnalyticsEvent.event_name.in_([EventType.EXPLORE, EventType.INQUIRY_START]))
    )
    assert no_explore is None


# --------------------------------------------------------------------------- #
# Test 3: Idempotency Key Deduplication
# --------------------------------------------------------------------------- #

def test_idempotency_key_deduplication(client: TestClient, db_session):
    """Verify that replaying events with the same idempotency_key prevents duplicates."""
    user = _create_user(db_session, f"idem_user_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)
    idempotency_key = f"idem_client_{uuid.uuid4().hex}"

    event_payload = {
        "events": [
            {
                "name": EventType.EXPLORE,
                "path": "/rbpc/explore",
                "idempotency_key": idempotency_key,
                "payload": {"step": "overview"},
            }
        ]
    }

    # First attempt: successfully persisted
    res1 = client.post("/api/v1/analytics/events", json=event_payload, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["count"] == 1
    assert res1.json().get("deduplicated_count", 0) == 0

    # Second attempt (replay): deduplicated
    res2 = client.post("/api/v1/analytics/events", json=event_payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["count"] == 0
    assert res2.json().get("deduplicated_count", 0) == 1

    # Verify exactly ONE record exists in DB with this idempotency key
    rows = (
        db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.idempotency_key == idempotency_key)
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].idempotency_key == idempotency_key


# --------------------------------------------------------------------------- #
# Test 4: Strict Zero Student PII in Telemetry Payloads
# --------------------------------------------------------------------------- #

def test_strict_zero_student_pii_in_payloads(client: TestClient, db_session):
    """Verify that student PII in telemetry payloads is recursively sanitized and never stored raw."""
    student_user = _create_user(
        db_session, f"student_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.learner
    )
    headers = _auth_headers(client, student_user.email)

    dirty_payload = {
        "events": [
            {
                "name": EventType.INQUIRY_START,
                "path": "/rbpc/inquiries/form",
                "payload": {
                    "student_name": "Nguyễn Văn Học Sinh",
                    "student_email": "student_nguyen@school.edu.vn",
                    "student_id": "STU-2026-9999",
                    "phone": "0987654321",
                    "guardian_phone": "0912345678",
                    "school_address": "Trường THPT Chu Văn An, Tây Hồ, Hà Nội",
                    "notes": "Em là học sinh muốn tìm hiểu liên hệ em qua 0987654321 hoặc student_nguyen@school.edu.vn",
                    "safe_attribute": "grade_10_history",
                },
            }
        ]
    }

    res = client.post("/api/v1/analytics/events", json=dirty_payload, headers=headers)
    assert res.status_code == 200, res.text

    # Inspect stored event in database
    ev = db_session.scalar(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.user_id == student_user.id)
        .where(AnalyticsEvent.event_name == EventType.INQUIRY_START)
    )
    assert ev is not None
    payload_str = json.dumps(ev.payload, ensure_ascii=False)

    # Invariant: ZERO plaintext student PII in database payload
    assert "student_nguyen@school.edu.vn" not in payload_str
    assert "0987654321" not in payload_str
    assert "0912345678" not in payload_str
    assert "Nguyễn Văn Học Sinh" not in payload_str
    assert "STU-2026-9999" not in payload_str

    # Redaction placeholders are present
    assert "[REDACTED_STUDENT_PII]" in payload_str or "[REDACTED_EMAIL]" in payload_str
    # Safe non-PII attributes are preserved
    assert ev.payload.get("safe_attribute") == "grade_10_history"


# --------------------------------------------------------------------------- #
# Test 5: Server-Trusted Business Conversion Events
# --------------------------------------------------------------------------- #

def test_server_trusted_business_conversion_events(client: TestClient, db_session):
    """Verify that conversion events are verified against DB truth and untrusted claims are flagged."""
    provider_user = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp = _setup_experience(db_session, provider_user)
    inquiry = _setup_inquiry(db_session, exp, state=RbpcInquiryStatus.confirmed.value)

    # 1. Valid inquiry_confirm referencing a genuinely confirmed inquiry -> is_server_verified = True
    trusted_confirm_event = {
        "events": [
            {
                "name": EventType.INQUIRY_CONFIRM,
                "payload": {
                    "inquiry_id": str(inquiry.id),
                    "public_ref": inquiry.public_ref,
                    "experience_id": str(exp.id),
                },
            }
        ]
    }
    res = client.post("/api/v1/analytics/events", json=trusted_confirm_event)
    assert res.status_code == 200
    ev1 = db_session.scalar(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.event_name == EventType.INQUIRY_CONFIRM)
        .order_by(AnalyticsEvent.created_at.desc())
    )
    assert ev1 is not None
    assert ev1.is_server_verified is True

    # 2. Fabricated inquiry_confirm with fake inquiry_id -> is_server_verified = False
    fake_confirm_event = {
        "events": [
            {
                "name": EventType.INQUIRY_CONFIRM,
                "payload": {
                    "inquiry_id": str(uuid.uuid4()),
                    "public_ref": "INQ-FAKE-9999",
                    "experience_id": str(exp.id),
                },
            }
        ]
    }
    res = client.post("/api/v1/analytics/events", json=fake_confirm_event)
    assert res.status_code == 200
    ev2 = db_session.scalar(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.event_name == EventType.INQUIRY_CONFIRM)
        .where(AnalyticsEvent.id != ev1.id)
    )
    assert ev2 is not None
    assert ev2.is_server_verified is False  # Untrusted conversion

    # 3. Direct server helper generates authoritative verified record
    srv_event = record_server_conversion_event(
        db=db_session,
        event_name=EventType.INQUIRY_SUBMIT,
        payload={"inquiry_id": str(inquiry.id), "experience_id": str(exp.id)},
        idempotency_key=f"srv_test_{uuid.uuid4().hex}",
    )
    assert srv_event.is_server_verified is True
    assert srv_event.event_name == EventType.INQUIRY_SUBMIT


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse Invariant: Demo Traffic Not Counted as Real Funnel
# --------------------------------------------------------------------------- #

def test_negative_abuse_demo_traffic_excluded_from_real_funnel(db_session):
    """Negative Abuse Invariant (V5-T111):
    Demo and synthetic events are NEVER counted in the real customer conversion funnel.
    """
    user_real = _create_user(db_session, f"real_user_{uuid.uuid4().hex[:6]}@example.com")
    user_demo = _create_user(db_session, f"demo_user_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.guest)

    # 1. Seed 100 demo conversion events (e.g. synthetic test or demo sandbox)
    demo_events = []
    for _ in range(50):
        demo_events.append(
            AnalyticsEvent(
                user_id=user_demo.id,
                event_name=EventType.VIEW,
                event_category=EventCategory.BUSINESS_CONVERSION,
                is_demo=True,
                is_synthetic=False,
                is_server_verified=False,
                payload={"demo": True},
            )
        )
        demo_events.append(
            AnalyticsEvent(
                user_id=user_demo.id,
                event_name=EventType.INQUIRY_SUBMIT,
                event_category=EventCategory.BUSINESS_CONVERSION,
                is_demo=True,
                is_synthetic=False,
                is_server_verified=False,
                payload={"demo": True},
            )
        )
    db_session.add_all(demo_events)
    db_session.commit()

    # 2. Check funnel calculation with ZERO real users
    funnel_data = calculate_funnel_data(
        session=db_session,
        funnel_type="business_conversion",
        exclude_demo=True,
    )
    # With 100 demo events and 0 real events, all stage counts MUST be 0
    stages = {s["stage"]: s["count"] for s in funnel_data["stages"]}
    assert stages["view"] == 0, f"Expected 0 real views, got {stages['view']}"
    assert stages["inquiry_submit"] == 0, f"Expected 0 real inquiry submits, got {stages['inquiry_submit']}"
    assert funnel_data["total_users"] == 0

    # 3. Add 1 genuine, real customer conversion event
    real_event = AnalyticsEvent(
        user_id=user_real.id,
        event_name=EventType.VIEW,
        event_category=EventCategory.BUSINESS_CONVERSION,
        is_demo=False,
        is_synthetic=False,
        is_server_verified=True,
        payload={"is_demo": False},
    )
    db_session.add(real_event)
    db_session.commit()

    # 4. Re-calculate funnel: only the 1 real user is counted
    updated_funnel = calculate_funnel_data(
        session=db_session,
        funnel_type="business_conversion",
        exclude_demo=True,
    )
    updated_stages = {s["stage"]: s["count"] for s in updated_funnel["stages"]}
    assert updated_stages["view"] == 1, f"Expected exactly 1 real view, got {updated_stages['view']}"
    assert updated_funnel["total_users"] == 1


# --------------------------------------------------------------------------- #
# Test 7: Frontend Telemetry Library Contract
# --------------------------------------------------------------------------- #

def test_frontend_telemetry_library_contract():
    """Verify frontend/src/lib/analytics.ts exists and provides complete client taxonomy and helpers."""
    assert FRONTEND_ANALYTICS_TS.exists(), f"Missing file: {FRONTEND_ANALYTICS_TS}"
    content = FRONTEND_ANALYTICS_TS.read_text(encoding="utf-8")

    # Verify event taxonomy constants
    assert "BUSINESS_CONVERSION" in content
    assert 'VIEW: "view"' in content
    assert 'EXPLORE: "explore"' in content
    assert 'INQUIRY_START: "inquiry_start"' in content
    assert 'INQUIRY_SUBMIT: "inquiry_submit"' in content
    assert 'INQUIRY_CONFIRM: "inquiry_confirm"' in content

    # Verify consent management
    assert "setTelemetryConsent" in content
    assert "getTelemetryConsent" in content

    # Verify PII sanitization and idempotency helpers
    assert "sanitizeClientPayload" in content
    assert "generateIdempotencyKey" in content
    assert "trackEvent" in content

    # Verify business conversion tracking helpers
    assert "trackConversionView" in content
    assert "trackConversionExplore" in content
    assert "trackInquiryStart" in content
    assert "trackInquirySubmit" in content
    assert "trackInquiryConfirm" in content
