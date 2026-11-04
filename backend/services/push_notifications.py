"""
Push Notification Service for FCM and APNs.

This service handles:
- Sending push notifications via Firebase Cloud Messaging (FCM)
- Support for Apple Push Notification service (APNs)
- Batch sending for efficiency
- Retry logic for failed notifications
- Quiet hours checking
- Notification history tracking
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional, Any, Callable
from uuid import UUID
import uuid as uuid_module

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..models import (
    PushNotification,
    User,
    UserNotificationSettings,
    NotificationType,
    NotificationStatus,
)
from ..config import settings as app_settings

logger = logging.getLogger(__name__)

# Firebase Admin SDK (lazy loaded)
_firebase_app = None
_firebase_initialized = False

# Pluggable Push Sender Registry (for tests and alternate push providers)
_custom_push_sender: Optional[Callable[[str, str, str, Optional[dict[str, Any]]], tuple[bool, Optional[str]]]] = None


def register_push_sender(
    sender_fn: Callable[[str, str, str, Optional[dict[str, Any]]], tuple[bool, Optional[str]]]
) -> None:
    """Register custom push sender: fn(token, title, body, data) -> tuple[bool, Optional[str]]."""
    global _custom_push_sender
    _custom_push_sender = sender_fn


def reset_push_senders() -> None:
    """Reset to default FCM sender."""
    global _custom_push_sender
    _custom_push_sender = None


# =============================================================================
# Zero Student PII Protection & Policy Enforcement
# =============================================================================


class StudentPIIDetectedError(ValueError):
    """Raised when student personally identifiable information is detected in a push notification payload."""
    pass


STUDENT_PII_KEYS = {
    "student_email",
    "student_phone",
    "student_name",
    "student_real_name",
    "real_name",
    "phone",
    "phone_number",
    "email",
    "birth_year",
    "date_of_birth",
    "dob",
    "national_id",
    "citizen_id",
    "address",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+84|0)[35789]\d{8}\b")


def detect_student_pii(
    title: str,
    body: str,
    data_payload: Optional[dict[str, Any]] = None,
) -> list[str]:
    """Scan notification title, body, and payload for student PII patterns."""
    violations: list[str] = []
    text_content = f"{title} {body}"

    if EMAIL_REGEX.search(text_content):
        violations.append("Email pattern detected in notification text")

    if PHONE_REGEX.search(text_content):
        violations.append("Phone number pattern detected in notification text")

    if data_payload and isinstance(data_payload, dict):
        for k, v in data_payload.items():
            k_lower = str(k).lower()
            if k_lower in STUDENT_PII_KEYS:
                violations.append(f"Prohibited PII key '{k}' found in data payload")
            elif isinstance(v, str):
                if EMAIL_REGEX.search(v):
                    violations.append(f"Email pattern detected in payload key '{k}'")
                elif PHONE_REGEX.search(v):
                    violations.append(f"Phone pattern detected in payload key '{k}'")

    return violations


def assert_zero_student_pii(
    title: str,
    body: str,
    data_payload: Optional[dict[str, Any]] = None,
) -> None:
    """Strictly assert that no student PII is present in push notification text or data payload."""
    violations = detect_student_pii(title, body, data_payload)
    if violations:
        raise StudentPIIDetectedError(
            f"Zero Student PII policy violation: {'; '.join(violations)}"
        )


def is_token_revoked_error(err: Optional[str]) -> bool:
    """Check if an error string indicates an invalidated/revoked device token."""
    if not err:
        return False
    msg = str(err).lower()
    return any(
        sub in msg
        for sub in [
            "notregistered",
            "invalidregistration",
            "unregistered",
            "token revoked",
            "token expired",
            "invalid_argument",
            "bad_device_token",
        ]
    )


# =============================================================================
# Push Notification Consent & Device Token Lifecycle
# =============================================================================


def record_push_consent(
    db: Session,
    user_id: UUID,
    granted: bool,
    token: Optional[str] = None,
    platform: Optional[str] = None,
) -> UserNotificationSettings:
    """Explicitly record user opt-in or opt-out consent for push notifications.

    If granted is True:
        - push_enabled is set to True
        - push_token and push_platform updated if provided
        - user.push_permission_prompted set to True
    If granted is False (opt-out):
        - push_enabled is set to False
        - push_token is immediately revoked / cleared to None
        - push_platform is cleared to None
        - Delivery promptly stops for any alerts directed to this user
    """
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user_id
        )
    ).scalar_one_or_none()

    if settings is None:
        settings = UserNotificationSettings(
            id=uuid_module.uuid4(),
            user_id=user_id,
        )
        db.add(settings)

    if granted:
        settings.push_enabled = True
        if token:
            settings.push_token = token
        if platform:
            settings.push_platform = platform.lower()
        user.push_permission_prompted = True
    else:
        # Prompt opt-out revocation: clear token and turn off push
        settings.push_enabled = False
        settings.push_token = None
        settings.push_platform = None

    db.commit()
    db.refresh(settings)
    return settings


def revoke_push_token(
    db: Session,
    user_id: UUID,
) -> UserNotificationSettings:
    """Revoke user's push token and disable push delivery promptly."""
    return record_push_consent(db, user_id, granted=False)


def _init_firebase() -> bool:
    """Initialize Firebase Admin SDK if credentials are available."""
    global _firebase_app, _firebase_initialized

    if _firebase_initialized:
        return _firebase_app is not None

    _firebase_initialized = True

    if not app_settings.fcm_credentials_path:
        logger.warning("FCM credentials path not configured. Push notifications will be disabled.")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(app_settings.fcm_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return False


def is_in_quiet_hours(user_settings: UserNotificationSettings, now: datetime) -> bool:
    """
    Check if current time is within user's quiet hours.

    Args:
        user_settings: User's notification settings
        now: Current datetime (timezone-aware)

    Returns:
        True if in quiet hours, False otherwise
    """
    if user_settings.quiet_hours_start is None or user_settings.quiet_hours_end is None:
        return False

    # Get hour in UTC (we'll need to convert based on user's timezone eventually)
    current_hour = now.hour
    start = user_settings.quiet_hours_start
    end = user_settings.quiet_hours_end

    # Handle cases where quiet hours span midnight
    if start < end:
        return start <= current_hour < end
    else:
        return current_hour >= start or current_hour < end


def should_send_notification(
    db: Session,
    user: User,
    notification_type: NotificationType,
) -> tuple[bool, Optional[str]]:
    """
    Check if a notification should be sent to a user.

    Args:
        db: Database session
        user: User to send notification to
        notification_type: Type of notification

    Returns:
        Tuple of (should_send, reason_if_not)
    """
    # Get user's notification settings
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user.id
        )
    ).scalar_one_or_none()

    if not settings:
        return False, "User has no notification settings"

    if not settings.push_enabled:
        return False, "Push notifications disabled for user"

    if not settings.push_token:
        return False, "No push token registered"

    # Check quiet hours
    now = datetime.now(timezone.utc)
    if is_in_quiet_hours(settings, now):
        return False, "User is in quiet hours"

    # Check type-specific preferences
    if notification_type == NotificationType.streak_reminder and not settings.streak_reminders:
        return False, "Streak reminders disabled"

    if notification_type == NotificationType.daily_mission and not settings.daily_mission_reminders:
        return False, "Daily mission reminders disabled"

    return True, None


def create_notification(
    db: Session,
    user_id: UUID,
    title: str,
    body: str,
    notification_type: NotificationType,
    data_payload: Optional[dict[str, Any]] = None,
    scheduled_for: Optional[datetime] = None,
) -> PushNotification:
    """
    Create a new push notification record.

    Args:
        db: Database session
        user_id: User to send notification to
        title: Notification title
        body: Notification body text
        notification_type: Type of notification
        data_payload: Optional custom data for the app
        scheduled_for: Optional scheduled time (None = send immediately)

    Returns:
        Created PushNotification instance
    """
    notification = PushNotification(
        id=uuid_module.uuid4(),
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        data_payload=data_payload,
        status=NotificationStatus.pending,
        scheduled_for=scheduled_for,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


async def send_notification_fcm(
    token: str,
    title: str,
    body: str,
    data: Optional[dict[str, str]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Send a push notification via Firebase Cloud Messaging.

    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional data payload (must be string values)

    Returns:
        Tuple of (success, error_message)
    """
    if not _init_firebase():
        return False, "Firebase not initialized"

    try:
        from firebase_admin import messaging

        # Convert data values to strings if present
        string_data = None
        if data:
            string_data = {k: str(v) for k, v in data.items()}

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=string_data,
            token=token,
        )

        response = messaging.send(message)
        logger.info(f"Successfully sent FCM notification: {response}")
        return True, None

    except Exception as e:
        error_msg = f"FCM send failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def send_notification(
    db: Session,
    notification: PushNotification,
    retry_count: int = 0,
) -> bool:
    """
    Send a push notification to a user.

    Args:
        db: Database session
        notification: PushNotification to send
        retry_count: Current retry attempt

    Returns:
        True if sent successfully, False otherwise
    """
    # Get user
    user = db.execute(
        select(User).where(User.id == notification.user_id)
    ).scalar_one_or_none()

    if not user:
        notification.status = NotificationStatus.failed
        notification.error_message = "User not found"
        db.commit()
        return False

    # Check if should send
    should_send, reason = should_send_notification(db, user, notification.notification_type)
    if not should_send:
        notification.status = NotificationStatus.failed
        notification.error_message = reason
        db.commit()
        return False

    # Get user settings for token
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user.id
        )
    ).scalar_one_or_none()

    if not settings or not settings.push_token:
        notification.status = NotificationStatus.failed
        notification.error_message = "No push token available"
        db.commit()
        return False

    # Send via registered custom sender or default FCM
    if _custom_push_sender is not None:
        try:
            success, error = _custom_push_sender(
                settings.push_token,
                notification.title,
                notification.body,
                notification.data_payload,
            )
        except Exception as e:
            success, error = False, str(e)
    else:
        # Send via FCM (iOS and Android both use FCM in this implementation)
        import asyncio
        success, error = asyncio.run(send_notification_fcm(
            token=settings.push_token,
            title=notification.title,
            body=notification.body,
            data=notification.data_payload,
        ))

    if success:
        notification.status = NotificationStatus.sent
        notification.sent_at = datetime.now(timezone.utc)
        notification.error_message = None
        db.commit()
        return True
    else:
        # Promptly revoke invalid/unregistered tokens so they cannot receive future alerts
        if is_token_revoked_error(error):
            logger.warning(
                "Push token for user %s was invalidated by provider: %s. Auto-revoking token.",
                user.id,
                error,
            )
            settings.push_token = None
            settings.push_enabled = False
            notification.status = NotificationStatus.failed
            notification.error_message = f"Push token revoked by provider: {error}"
            db.commit()
            return False

        # Retry logic
        max_retries = getattr(app_settings, "push_notification_max_retries", 3)
        if retry_count < max_retries:
            logger.info(f"Retrying notification {notification.id} (attempt {retry_count + 1})")
            return send_notification(db, notification, retry_count + 1)
        else:
            notification.status = NotificationStatus.failed
            notification.error_message = error
            db.commit()
            return False


def send_batch_notifications(
    db: Session,
    notifications: list[PushNotification],
) -> dict[str, int]:
    """
    Send multiple notifications in batch.

    Args:
        db: Database session
        notifications: List of notifications to send

    Returns:
        Dict with counts: {"sent": int, "failed": int}
    """
    results = {"sent": 0, "failed": 0}

    for notification in notifications:
        if send_notification(db, notification):
            results["sent"] += 1
        else:
            results["failed"] += 1

    return results


def broadcast_notification(
    db: Session,
    title: str,
    body: str,
    notification_type: NotificationType,
    data_payload: Optional[dict[str, Any]] = None,
    user_role: Optional[str] = None,
) -> dict[str, Any]:
    """
    Broadcast a notification to all eligible users.

    Args:
        db: Database session
        title: Notification title
        body: Notification body
        notification_type: Type of notification
        data_payload: Optional custom data
        user_role: Optional filter by user role

    Returns:
        Dict with results
    """
    # Build query for eligible users
    query = select(User).join(
        UserNotificationSettings,
        User.id == UserNotificationSettings.user_id,
    ).where(
        UserNotificationSettings.push_enabled == True,
        UserNotificationSettings.push_token.is_not(None),
    )

    # Filter by role if specified
    if user_role:
        query = query.where(User.role == user_role)

    users = db.execute(query).scalars().all()

    # Create notifications for all users
    notifications = []
    for user in users:
        notification = create_notification(
            db=db,
            user_id=user.id,
            title=title,
            body=body,
            notification_type=notification_type,
            data_payload=data_payload,
        )
        notifications.append(notification)

    # Send in batches
    total_created = len(notifications)
    results = send_batch_notifications(db, notifications)

    return {
        "total_users": len(users),
        "total_created": total_created,
        "sent": results["sent"],
        "failed": results["failed"],
    }


def get_user_notification_history(
    db: Session,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PushNotification], int]:
    """
    Get notification history for a user.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip

    Returns:
        Tuple of (notifications, total_count)
    """
    # Get total count
    count_query = select(PushNotification).where(
        PushNotification.user_id == user_id
    )
    total = len(db.execute(count_query).scalars().all())

    # Get notifications
    query = select(PushNotification).where(
        PushNotification.user_id == user_id
    ).order_by(
        PushNotification.created_at.desc()
    ).limit(limit).offset(offset)

    notifications = db.execute(query).scalars().all()

    return list(notifications), total


def get_pending_scheduled_notifications(
    db: Session,
    now: Optional[datetime] = None,
) -> list[PushNotification]:
    """
    Get notifications that are scheduled to be sent now.

    Args:
        db: Database session
        now: Current time (defaults to now)

    Returns:
        List of notifications to send
    """
    if now is None:
        now = datetime.now(timezone.utc)

    query = select(PushNotification).where(
        PushNotification.status == NotificationStatus.pending,
        PushNotification.scheduled_for.is_not(None),
        PushNotification.scheduled_for <= now,
    ).order_by(
        PushNotification.scheduled_for
    )

    return list(db.execute(query).scalars().all())


# Helper functions for common notification types

def send_streak_reminder(
    db: Session,
    user_id: UUID,
    current_streak: int,
) -> PushNotification:
    """Send a streak reminder notification."""
    return create_notification(
        db=db,
        user_id=user_id,
        title="Don't lose your streak! 🔥",
        body=f"You're on a {current_streak}-day streak! Keep it going!",
        notification_type=NotificationType.streak_reminder,
        data_payload={"current_streak": current_streak},
    )


def send_daily_mission_notification(
    db: Session,
    user_id: UUID,
) -> PushNotification:
    """Send a daily mission notification."""
    return create_notification(
        db=db,
        user_id=user_id,
        title="New daily missions available! 📋",
        body="Complete today's missions to earn rewards!",
        notification_type=NotificationType.daily_mission,
        data_payload={"screen": "daily_missions"},
    )


def send_achievement_notification(
    db: Session,
    user_id: UUID,
    achievement_name: str,
    achievement_id: UUID,
) -> PushNotification:
    """Send an achievement unlocked notification."""
    return create_notification(
        db=db,
        user_id=user_id,
        title="Achievement unlocked! 🎉",
        body=f"You earned: {achievement_name}",
        notification_type=NotificationType.achievement,
        data_payload={
            "achievement_id": str(achievement_id),
            "achievement_name": achievement_name,
            "screen": "achievements",
        },
    )


def send_social_notification(
    db: Session,
    user_id: UUID,
    message: str,
    data: Optional[dict[str, Any]] = None,
) -> PushNotification:
    """Send a social interaction notification."""
    return create_notification(
        db=db,
        user_id=user_id,
        title="Social activity 👥",
        body=message,
        notification_type=NotificationType.social,
        data_payload=data or {},
    )


def send_system_notification(
    db: Session,
    user_id: UUID,
    title: str,
    body: str,
    data: Optional[dict[str, Any]] = None,
) -> PushNotification:
    """Send a system notification."""
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        body=body,
        notification_type=NotificationType.system,
        data_payload=data or {},
    )


def route_teacher_alert(
    db: Session,
    teacher_id: UUID,
    classroom_id: UUID,
    assignment_id: UUID,
    assignment_title: str,
    student_ref: Optional[str] = None,
    data_override: Optional[dict[str, Any]] = None,
) -> PushNotification:
    """Route an alert to a teacher regarding classroom activity with STRICT ZERO STUDENT PII.

    CRITICAL INVARIANT: ZERO student PII (email, phone, real name, birth year) is permitted
    in the push notification title, body, or payload. Any detected PII immediately halts
    execution with StudentPIIDetectedError before creating the notification.
    """
    title = "Bài tập mới đã nộp"
    body = f"Có bài nộp mới cho bài tập: {assignment_title}."

    payload: dict[str, Any] = {
        "type": "teacher_alert",
        "screen": "classroom_grading",
        "classroom_id": str(classroom_id),
        "assignment_id": str(assignment_id),
    }
    if student_ref:
        payload["student_ref"] = str(student_ref)
    if data_override:
        payload.update(data_override)

    # Enforce Zero Student PII Policy
    assert_zero_student_pii(title, body, payload)

    notification = create_notification(
        db=db,
        user_id=teacher_id,
        title=title,
        body=body,
        notification_type=NotificationType.teacher_alert,
        data_payload=payload,
    )

    # Attempt delivery (respecting teacher's opt-in/opt-out consent & token state)
    send_notification(db, notification)
    return notification


def route_partner_alert(
    db: Session,
    partner_id: UUID,
    inquiry_id: UUID,
    experience_title: str,
    booking_date: Optional[str] = None,
    data_override: Optional[dict[str, Any]] = None,
) -> PushNotification:
    """Route an alert to a partner/artisan regarding a new inquiry or booking with zero visitor contact PII.

    CRITICAL INVARIANT: ZERO visitor PII (phone, email, real contact info) is routed via push.
    Push notification contains only generic operational reference tokens.
    """
    title = "Yêu cầu trải nghiệm mới"
    body = f"Bạn nhận được yêu cầu đặt chỗ mới cho trải nghiệm: {experience_title}."

    payload: dict[str, Any] = {
        "type": "partner_alert",
        "screen": "partner_inbox",
        "inquiry_id": str(inquiry_id),
    }
    if booking_date:
        payload["booking_date"] = str(booking_date)
    if data_override:
        payload.update(data_override)

    # Enforce Zero PII
    assert_zero_student_pii(title, body, payload)

    notification = create_notification(
        db=db,
        user_id=partner_id,
        title=title,
        body=body,
        notification_type=NotificationType.partner_alert,
        data_payload=payload,
    )

    # Attempt delivery (respecting partner's opt-in/opt-out consent & token state)
    send_notification(db, notification)
    return notification

