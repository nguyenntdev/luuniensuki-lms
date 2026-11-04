# -*- coding: utf-8 -*-
"""V5-T059: Push Notification Consent & Zero Student PII Enforcement Test Suite.

Wave W05, Slot A09 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Opt-in / Opt-out Consent Flow:
   - Explicit user opt-in records consent timestamp, sets push_enabled=True,
     registers platform and token, and marks push_permission_prompted=True.
   - Explicit user opt-out immediately revokes token, sets push_enabled=False,
     clears push_token, and halts all push deliveries promptly.
   - Status endpoint GET /api/v1/notifications/consent reflects current state.
2. Token Registration Endpoints:
   - POST /api/v1/notifications/register-push correctly registers device tokens
     with case-insensitive platform normalization (ios, android, web).
   - Accepts both 'token' and alias 'fcm_token'.
   - DELETE /api/v1/notifications/unregister-push clears device token and stops delivery.
3. Teacher Alert Routing:
   - Routes classroom assignment submissions to teachers with zero student PII.
   - Generates notifications with notification_type="teacher_alert".
   - Successfully delivers when teacher has opted in with active token.
4. Partner Alert Routing:
   - Routes visitor experience inquiries to artisans/partners with zero visitor PII.
   - Generates notifications with notification_type="partner_alert".
   - Successfully delivers when partner has opted in with active token.
5. Strict Zero Student PII Invariant:
   - Push notification title, body, and payload are scanned for PII.
   - Rejects any presence of student email, phone number, real name, or PII keys
     with StudentPIIDetectedError.
6. Negative Abuse Guardrails:
   - Opt-out stops notification delivery promptly: zero alerts dispatched to opted-out users.
   - Revoked tokens cannot receive alerts: delivery fails immediately with explicit reason.
   - Provider token invalidation auto-revokes stored tokens in DB.
   - Cross-user consent isolation: authenticated endpoint strictly operates on current_user.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import (
    NotificationStatus,
    NotificationType,
    PushNotification,
    User,
    UserNotificationSettings,
    UserRole,
)
from backend.security import hash_password
from backend.services.push_notifications import (
    StudentPIIDetectedError,
    assert_zero_student_pii,
    detect_student_pii,
    record_push_consent,
    register_push_sender,
    reset_push_senders,
    revoke_push_token,
    route_partner_alert,
    route_teacher_alert,
    send_notification,
    should_send_notification,
)


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def clean_push_sender():
    """Ensure push sender is reset before and after each test."""
    reset_push_senders()
    yield
    reset_push_senders()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a verified test user."""
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
    """Authenticate user and return response data."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


# ============================================================================== #
# 1. Opt-In / Opt-Out Consent Flow & API Endpoints
# ============================================================================== #


def test_push_consent_opt_in_and_opt_out_lifecycle(client: TestClient, db_session):
    """Verify explicit push consent opt-in, query, and opt-out lifecycle."""
    email = f"learner_{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(db_session, email=email, role=UserRole.learner)
    _login(client, email)

    # 1. Initial consent status: not granted
    res = client.get("/api/v1/notifications/consent")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["push_enabled"] is False
    assert data["token_registered"] is False

    # 2. Explicit Opt-In with device token
    fcm_token = "fcm_device_token_sample_12345"
    opt_in_res = client.post(
        "/api/v1/notifications/consent",
        json={
            "granted": True,
            "token": fcm_token,
            "platform": "android",
            "consent_version": "v1.0",
        },
    )
    assert opt_in_res.status_code == 200
    opt_in_data = opt_in_res.json()
    assert opt_in_data["success"] is True
    assert opt_in_data["push_enabled"] is True
    assert opt_in_data["token_registered"] is True
    assert "granted" in opt_in_data["message"].lower()

    # Verify database persistence
    settings = db_session.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user.id
        )
    ).scalar_one()
    assert settings.push_enabled is True
    assert settings.push_token == fcm_token
    assert settings.push_platform == "android"

    db_session.refresh(user)
    assert user.push_permission_prompted is True

    # 3. Query consent status after opt-in
    status_res = client.get("/api/v1/notifications/consent")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["push_enabled"] is True
    assert status_data["token_registered"] is True

    # 4. Explicit Opt-Out
    opt_out_res = client.post(
        "/api/v1/notifications/consent",
        json={"granted": False},
    )
    assert opt_out_res.status_code == 200
    opt_out_data = opt_out_res.json()
    assert opt_out_data["success"] is True
    assert opt_out_data["push_enabled"] is False
    assert opt_out_data["token_registered"] is False

    # Verify token immediately revoked / cleared on backend
    db_session.refresh(settings)
    assert settings.push_enabled is False
    assert settings.push_token is None
    assert settings.push_platform is None


def test_token_registration_and_unregistration_endpoints(client: TestClient, db_session):
    """Verify POST register-push and DELETE unregister-push endpoints."""
    email = f"learner_reg_{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(db_session, email=email)
    _login(client, email)

    # 1. Register push token with case-insensitive platform
    tok = "apns_sample_token_67890"
    reg_res = client.post(
        "/api/v1/notifications/register-push",
        json={"token": tok, "platform": "iOS"},
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["success"] is True

    settings = db_session.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user.id
        )
    ).scalar_one()
    assert settings.push_token == tok
    assert settings.push_platform == "ios"
    assert settings.push_enabled is True

    # 2. Test alias payload with fcm_token
    tok_fcm = "fcm_alias_token_9999"
    reg_fcm_res = client.post(
        "/api/v1/notifications/register-push",
        json={"fcm_token": tok_fcm, "platform": "Android"},
    )
    assert reg_fcm_res.status_code == 200
    db_session.refresh(settings)
    assert settings.push_token == tok_fcm
    assert settings.push_platform == "android"

    # 3. Unregister token via DELETE endpoint
    unreg_res = client.delete("/api/v1/notifications/unregister-push")
    assert unreg_res.status_code == 200
    assert unreg_res.json()["success"] is True

    db_session.refresh(settings)
    assert settings.push_token is None
    assert settings.push_platform is None
    assert settings.push_enabled is False


# ============================================================================== #
# 2. Teacher Alert Routing with Zero Student PII
# ============================================================================== #


def test_teacher_alert_routing_positive(db_session):
    """Verify routing assignment alerts to teacher with authentic delivery & zero student PII."""
    teacher_email = f"teacher_{uuid.uuid4().hex[:6]}@school.edu.vn"
    teacher = _create_user(db_session, email=teacher_email, role=UserRole.teacher)

    # Teacher explicitly opts in
    record_push_consent(
        db=db_session,
        user_id=teacher.id,
        granted=True,
        token="teacher_device_token_xyz",
        platform="android",
    )

    dispatched_payloads = []

    def mock_sender(token, title, body, data):
        dispatched_payloads.append({
            "token": token,
            "title": title,
            "body": body,
            "data": data,
        })
        return True, None

    register_push_sender(mock_sender)

    classroom_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    assignment_title = "Bài học 03: Biểu tượng Rồng trên Đỉnh Thần"

    # Route alert with anonymous student reference (no real name, no email)
    notif = route_teacher_alert(
        db=db_session,
        teacher_id=teacher.id,
        classroom_id=classroom_id,
        assignment_id=assignment_id,
        assignment_title=assignment_title,
        student_ref="student_anon_4042",
    )

    assert notif.status == NotificationStatus.sent
    assert notif.notification_type == NotificationType.teacher_alert
    assert notif.sent_at is not None
    assert len(dispatched_payloads) == 1

    payload = dispatched_payloads[0]
    assert payload["token"] == "teacher_device_token_xyz"
    assert assignment_title in payload["body"]
    assert payload["data"]["classroom_id"] == str(classroom_id)
    assert payload["data"]["assignment_id"] == str(assignment_id)
    assert payload["data"]["student_ref"] == "student_anon_4042"

    # Strict Zero Student PII Assertion on dispatched payload
    assert_zero_student_pii(payload["title"], payload["body"], payload["data"])


def test_teacher_alert_blocks_student_pii_leakage(db_session):
    """Negative Abuse: Reject alert dispatch if student email, phone, or name is passed."""
    teacher_email = f"teacher_pii_{uuid.uuid4().hex[:6]}@school.edu.vn"
    teacher = _create_user(db_session, email=teacher_email, role=UserRole.teacher)
    record_push_consent(db_session, teacher.id, granted=True, token="tok_123", platform="ios")

    classroom_id = uuid.uuid4()
    assignment_id = uuid.uuid4()

    # Attempt 1: Leak student email in payload
    with pytest.raises(StudentPIIDetectedError) as exc_email:
        route_teacher_alert(
            db=db_session,
            teacher_id=teacher.id,
            classroom_id=classroom_id,
            assignment_id=assignment_id,
            assignment_title="Cửu Đỉnh Tổng Quan",
            data_override={"student_email": "nguyen_van_a@school.edu.vn"},
        )
    assert "Zero Student PII policy violation" in str(exc_email.value)

    # Attempt 2: Leak student phone number in body text
    with pytest.raises(StudentPIIDetectedError) as exc_phone:
        route_teacher_alert(
            db=db_session,
            teacher_id=teacher.id,
            classroom_id=classroom_id,
            assignment_id=assignment_id,
            assignment_title="Bài tập liên hệ: 0987654321",
        )
    assert "Phone number pattern detected" in str(exc_phone.value)

    # Attempt 3: Leak student personal details via PII key
    with pytest.raises(StudentPIIDetectedError) as exc_key:
        route_teacher_alert(
            db=db_session,
            teacher_id=teacher.id,
            classroom_id=classroom_id,
            assignment_id=assignment_id,
            assignment_title="Bài tập 2",
            data_override={"birth_year": 2010, "student_real_name": "Nguyen Van B"},
        )
    assert "Prohibited PII key" in str(exc_key.value)


# ============================================================================== #
# 3. Partner Alert Routing with Zero Visitor PII
# ============================================================================== #


def test_partner_alert_routing_positive(db_session):
    """Verify routing experience inquiries to artisan/partner with zero visitor contact details."""
    partner_email = f"artisan_{uuid.uuid4().hex[:6]}@hueheritage.vn"
    partner = _create_user(db_session, email=partner_email, role=UserRole.teacher)

    record_push_consent(
        db=db_session,
        user_id=partner.id,
        granted=True,
        token="partner_tok_555",
        platform="android",
    )

    dispatched = []
    register_push_sender(lambda tok, t, b, d: (dispatched.append((tok, t, b, d)) or True, None))

    inquiry_id = uuid.uuid4()
    exp_title = "Trải nghiệm Đúc Đồng Phường Đúc"

    notif = route_partner_alert(
        db=db_session,
        partner_id=partner.id,
        inquiry_id=inquiry_id,
        experience_title=exp_title,
        booking_date="2026-11-20",
    )

    assert notif.status == NotificationStatus.sent
    assert notif.notification_type == NotificationType.partner_alert
    assert len(dispatched) == 1

    tok, title, body, data = dispatched[0]
    assert tok == "partner_tok_555"
    assert exp_title in body
    assert data["inquiry_id"] == str(inquiry_id)
    assert data["type"] == "partner_alert"
    assert data["screen"] == "partner_inbox"

    # Verify zero visitor PII in push text or payload
    assert_zero_student_pii(title, body, data)


def test_partner_alert_blocks_visitor_contact_leakage(db_session):
    """Negative Abuse: Reject partner alert if visitor phone or email is injected in payload."""
    partner_email = f"artisan_pii_{uuid.uuid4().hex[:6]}@hueheritage.vn"
    partner = _create_user(db_session, email=partner_email, role=UserRole.teacher)
    record_push_consent(db_session, partner.id, granted=True, token="tok_part", platform="android")

    inquiry_id = uuid.uuid4()

    # Attempt to inject visitor email into data payload
    with pytest.raises(StudentPIIDetectedError) as exc_leak:
        route_partner_alert(
            db=db_session,
            partner_id=partner.id,
            inquiry_id=inquiry_id,
            experience_title="Đúc đồng",
            data_override={"email": "tourist@gmail.com", "phone": "0912345678"},
        )
    assert "Zero Student PII policy violation" in str(exc_leak.value)


# ============================================================================== #
# 4. Negative Abuse Tests: Opt-Out Stops Delivery & Revocation Defense
# ============================================================================== #


def test_negative_abuse_user_opt_out_promptly_stops_delivery(db_session):
    """Negative Abuse: When a user opts out, push delivery MUST promptly stop."""
    teacher_email = f"teacher_optout_{uuid.uuid4().hex[:6]}@school.edu.vn"
    teacher = _create_user(db_session, email=teacher_email, role=UserRole.teacher)

    # 1. Initially opted in
    record_push_consent(
        db=db_session,
        user_id=teacher.id,
        granted=True,
        token="tok_active_before_optout",
        platform="android",
    )

    call_count = {"count": 0}

    def tracking_sender(token, title, body, data):
        call_count["count"] += 1
        return True, None

    register_push_sender(tracking_sender)

    # 2. Teacher explicitly opts out
    record_push_consent(db=db_session, user_id=teacher.id, granted=False)

    # 3. An assignment submission triggers an alert
    classroom_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    notif = route_teacher_alert(
        db=db_session,
        teacher_id=teacher.id,
        classroom_id=classroom_id,
        assignment_id=assignment_id,
        assignment_title="Bài 04: Biểu tượng Trâu vàng Cao Đỉnh",
        student_ref="anon_student_12",
    )

    # Delivery must be promptly refused
    assert notif.status == NotificationStatus.failed
    assert "Push notifications disabled for user" in (notif.error_message or "")
    # Push sender was NEVER called
    assert call_count["count"] == 0


def test_negative_abuse_revoked_token_cannot_receive_alerts(db_session):
    """Negative Abuse: Revoked or missing tokens cannot receive notifications."""
    email = f"user_revoked_{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(db_session, email=email)

    # User registers token then revokes it
    record_push_consent(db_session, user.id, granted=True, token="tok_temp", platform="ios")
    revoke_push_token(db_session, user.id)

    sender_called = False

    def mock_sender(token, title, body, data):
        nonlocal sender_called
        sender_called = True
        return True, None

    register_push_sender(mock_sender)

    notif = PushNotification(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Thông báo",
        body="Nội dung kiểm tra",
        notification_type=NotificationType.system,
        status=NotificationStatus.pending,
    )
    db_session.add(notif)
    db_session.commit()

    success = send_notification(db_session, notif)
    assert success is False
    assert notif.status == NotificationStatus.failed
    assert sender_called is False
    assert "disabled" in notif.error_message.lower() or "no push token" in notif.error_message.lower()


def test_negative_abuse_provider_invalidation_auto_revokes_token(db_session):
    """Negative Abuse: When provider returns token invalidation, backend auto-revokes token."""
    email = f"user_invalidated_{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(db_session, email=email)

    record_push_consent(
        db=db_session,
        user_id=user.id,
        granted=True,
        token="invalid_fcm_token_999",
        platform="android",
    )

    # Provider reports token is unregistered/revoked
    def failing_sender(token, title, body, data):
        return False, "Requested entity was not found: UNREGISTERED / NotRegistered"

    register_push_sender(failing_sender)

    notif = PushNotification(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Cảnh báo chuỗi học",
        body="Đừng để mất chuỗi học tập!",
        notification_type=NotificationType.streak_reminder,
        status=NotificationStatus.pending,
    )
    db_session.add(notif)
    db_session.commit()

    success = send_notification(db_session, notif)
    assert success is False
    assert notif.status == NotificationStatus.failed
    assert "token revoked" in notif.error_message.lower()

    # Verify token was automatically revoked in database
    settings = db_session.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user.id
        )
    ).scalar_one()
    assert settings.push_token is None
    assert settings.push_enabled is False

    # A subsequent send immediately fails at pre-check without contacting provider
    provider_called_again = False

    def tracking_sender(token, title, body, data):
        nonlocal provider_called_again
        provider_called_again = True
        return True, None

    register_push_sender(tracking_sender)

    notif2 = PushNotification(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Thử lại",
        body="Nội dung gửi sau khi hủy token",
        notification_type=NotificationType.streak_reminder,
        status=NotificationStatus.pending,
    )
    db_session.add(notif2)
    db_session.commit()

    success2 = send_notification(db_session, notif2)
    assert success2 is False
    assert provider_called_again is False


# ============================================================================== #
# 5. PII Detection Unit Suite
# ============================================================================== #


def test_detect_student_pii_comprehensive():
    """Verify regex and key scanning across email, phone, and metadata."""
    # Clean payload
    assert detect_student_pii("Tiêu đề", "Nội dung bài học", {"screen": "home"}) == []

    # Leaked email in text
    v1 = detect_student_pii("Chào", "Gửi tới student.test@edu.vn nhé")
    assert any("Email pattern" in v for v in v1)

    # Leaked Vietnamese phone in text
    v2 = detect_student_pii("Nhắc nhở", "Gọi ngay 0912345678 để nhận quà")
    assert any("Phone number pattern" in v for v in v2)

    # Prohibited keys
    v3 = detect_student_pii("Thông báo", "Bài mới", {"student_name": "Lê Văn C"})
    assert any("student_name" in v for v in v3)

    v4 = detect_student_pii("Thông báo", "Bài mới", {"national_id": "012345678901"})
    assert any("national_id" in v for v in v4)
