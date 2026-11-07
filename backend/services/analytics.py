"""
Analytics Service for Luuniensuki LMS.

This module defines the event taxonomy and provides utilities for recording
analytics events with proper validation and categorization.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session


# =============================================================================
# Event Taxonomy Constants
# =============================================================================

class EventCategory:
    """Event category constants."""
    ACTIVATION = "activation"
    LESSON = "lesson"
    QUIZ = "quiz"
    STREAK = "streak"
    DISCOVERY = "discovery"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    BUSINESS_CONVERSION = "business_conversion"
    CONVERSION = "business_conversion"  # Canonical alias


class EventType:
    """Event type constants organized by category."""
    
    # ACTIVATION events
    APP_OPENED = "app_opened"
    ONBOARDING_STARTED = "onboarding_started"
    ONBOARDING_COMPLETED = "onboarding_completed"
    FIRST_LESSON_STARTED = "first_lesson_started"
    FIRST_QUIZ_COMPLETED = "first_quiz_completed"
    
    # LESSON events
    LESSON_VIEWED = "lesson_viewed"
    LESSON_STARTED = "lesson_started"
    LESSON_COMPLETED = "lesson_completed"
    LESSON_TIME_SPENT = "lesson_time_spent"
    
    # QUIZ events
    QUIZ_STARTED = "quiz_started"
    QUIZ_SUBMITTED = "quiz_submitted"
    QUIZ_PASSED = "quiz_passed"
    QUIZ_FAILED = "quiz_failed"
    QUESTION_ANSWERED = "question_answered"
    
    # STREAK events
    STREAK_CONTINUED = "streak_continued"
    STREAK_BROKEN = "streak_broken"
    STREAK_FREEZE_USED = "streak_freeze_used"
    STREAK_MILESTONE_REACHED = "streak_milestone_reached"
    
    # DISCOVERY events
    MOTIF_DISCOVERED = "motif_discovered"
    MOTIF_LEARNED = "motif_learned"
    MOTIF_MASTERED = "motif_mastered"
    
    # ENGAGEMENT events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    DAILY_MISSION_COMPLETED = "daily_mission_completed"
    BADGE_EARNED = "badge_earned"

    # PERFORMANCE events
    RENDER_PERFORMANCE = "render_performance"

    # BUSINESS CONVERSION events (V5-T111 / Wave W11)
    VIEW = "view"
    EXPLORE = "explore"
    INQUIRY_START = "inquiry_start"
    INQUIRY_SUBMIT = "inquiry_submit"
    INQUIRY_CONFIRM = "inquiry_confirm"


# Mapping of event types to their categories
EVENT_CATEGORY_MAP: Dict[str, str] = {
    # Activation
    EventType.APP_OPENED: EventCategory.ACTIVATION,
    EventType.ONBOARDING_STARTED: EventCategory.ACTIVATION,
    EventType.ONBOARDING_COMPLETED: EventCategory.ACTIVATION,
    EventType.FIRST_LESSON_STARTED: EventCategory.ACTIVATION,
    EventType.FIRST_QUIZ_COMPLETED: EventCategory.ACTIVATION,
    
    # Lesson
    EventType.LESSON_VIEWED: EventCategory.LESSON,
    EventType.LESSON_STARTED: EventCategory.LESSON,
    EventType.LESSON_COMPLETED: EventCategory.LESSON,
    EventType.LESSON_TIME_SPENT: EventCategory.LESSON,
    
    # Quiz
    EventType.QUIZ_STARTED: EventCategory.QUIZ,
    EventType.QUIZ_SUBMITTED: EventCategory.QUIZ,
    EventType.QUIZ_PASSED: EventCategory.QUIZ,
    EventType.QUIZ_FAILED: EventCategory.QUIZ,
    EventType.QUESTION_ANSWERED: EventCategory.QUIZ,
    
    # Streak
    EventType.STREAK_CONTINUED: EventCategory.STREAK,
    EventType.STREAK_BROKEN: EventCategory.STREAK,
    EventType.STREAK_FREEZE_USED: EventCategory.STREAK,
    EventType.STREAK_MILESTONE_REACHED: EventCategory.STREAK,
    
    # Discovery
    EventType.MOTIF_DISCOVERED: EventCategory.DISCOVERY,
    EventType.MOTIF_LEARNED: EventCategory.DISCOVERY,
    EventType.MOTIF_MASTERED: EventCategory.DISCOVERY,
    
    # Engagement
    EventType.SESSION_STARTED: EventCategory.ENGAGEMENT,
    EventType.SESSION_ENDED: EventCategory.ENGAGEMENT,
    EventType.DAILY_MISSION_COMPLETED: EventCategory.ENGAGEMENT,
    EventType.BADGE_EARNED: EventCategory.ENGAGEMENT,

    # Performance
    EventType.RENDER_PERFORMANCE: EventCategory.PERFORMANCE,

    # Business Conversion (V5-T111)
    EventType.VIEW: EventCategory.BUSINESS_CONVERSION,
    EventType.EXPLORE: EventCategory.BUSINESS_CONVERSION,
    EventType.INQUIRY_START: EventCategory.BUSINESS_CONVERSION,
    EventType.INQUIRY_SUBMIT: EventCategory.BUSINESS_CONVERSION,
    EventType.INQUIRY_CONFIRM: EventCategory.BUSINESS_CONVERSION,
    # Common aliases
    "experience_view": EventCategory.BUSINESS_CONVERSION,
    "experience_explore": EventCategory.BUSINESS_CONVERSION,
}


# =============================================================================
# Event Schema Definitions
# =============================================================================

class BaseEventPayload(BaseModel):
    """Base event payload with common fields."""
    model_config = ConfigDict(extra="allow")
    source: Optional[str] = Field(None, description="Event source (e.g., 'mobile', 'web', 'server')")
    timestamp: Optional[datetime] = Field(None, description="Client-side timestamp")


class ActivationEventPayload(BaseEventPayload):
    """Payload for activation events."""
    screen: Optional[str] = None
    step: Optional[int] = None


class LessonEventPayload(BaseEventPayload):
    """Payload for lesson events."""
    motif_id: Optional[str] = None
    urn_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    completion_percentage: Optional[float] = None


class QuizEventPayload(BaseEventPayload):
    """Payload for quiz events."""
    motif_id: Optional[str] = None
    urn_id: Optional[str] = None
    score: Optional[int] = None
    max_score: Optional[int] = None
    percentage: Optional[float] = None
    passed: Optional[bool] = None
    time_taken_seconds: Optional[int] = None
    question_id: Optional[str] = None
    answer: Optional[Any] = None
    correct: Optional[bool] = None


class StreakEventPayload(BaseEventPayload):
    """Payload for streak events."""
    current_streak: Optional[int] = None
    previous_streak: Optional[int] = None
    milestone: Optional[int] = None
    freeze_count: Optional[int] = None


class DiscoveryEventPayload(BaseEventPayload):
    """Payload for discovery events."""
    motif_id: Optional[str] = None
    urn_id: Optional[str] = None
    status: Optional[str] = None
    xp_awarded: Optional[int] = None


class EngagementEventPayload(BaseEventPayload):
    """Payload for engagement events."""
    session_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    badge_slug: Optional[str] = None
    badge_name: Optional[str] = None
    mission_type: Optional[str] = None
    xp_awarded: Optional[int] = None


class PerformanceEventPayload(BaseEventPayload):
    """Payload for render and client performance events."""
    model_url: Optional[str] = None
    lod_label: Optional[str] = None
    file_size_bytes: Optional[int] = None
    ttf_ms: Optional[float] = None
    ttfi_ms: Optional[float] = None
    avg_fps: Optional[float] = None
    gpu_renderer: Optional[str] = None
    device_pixel_ratio: Optional[float] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    iteration: Optional[int] = None


class BusinessConversionPayload(BaseEventPayload):
    """Payload for business conversion funnel events (V5-T111 / Wave W11)."""
    experience_id: Optional[str] = None
    creator_id: Optional[str] = None
    inquiry_id: Optional[str] = None
    item_slug: Optional[str] = None
    step: Optional[str] = None
    interaction_type: Optional[str] = None
    is_demo: Optional[bool] = False
    is_synthetic: Optional[bool] = False
    is_server_verified: Optional[bool] = False
    idempotency_key: Optional[str] = None
    consent_status: Optional[str] = "consented"
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Zero Student PII Safeguards & Telemetry Consent
# =============================================================================

STUDENT_PII_KEYS = {
    "student_name",
    "student_email",
    "student_id",
    "guardian_name",
    "guardian_phone",
    "guardian_email",
    "school_address",
    "full_name",
    "phone",
    "email",
    "phone_number",
    "contact_phone",
    "national_id",
    "citizen_id",
    "cccd",
    "cmnd",
    "password",
    "token",
    "jwt",
}

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
PHONE_REGEX = re.compile(
    r"(?:(?:\+84|84|0)(?:\s*[\.\-]?\s*\d){8,10}\b|\b\(?0\d{1,3}\)?[\s\.\-]?\d{3,4}[\s\.\-]?\d{3,4}\b)"
)

REDACTED_PII = "[REDACTED_STUDENT_PII]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_PHONE = "[REDACTED_PHONE]"


def contains_student_pii(data: Any) -> bool:
    """Check if arbitrary data structure contains raw student PII."""
    if isinstance(data, dict):
        for k, v in data.items():
            k_lower = str(k).lower().strip()
            if k_lower in STUDENT_PII_KEYS:
                if v and str(v).strip() not in (REDACTED_PII, REDACTED_EMAIL, REDACTED_PHONE):
                    return True
            if contains_student_pii(v):
                return True
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            if contains_student_pii(item):
                return True
    elif isinstance(data, str):
        if EMAIL_REGEX.search(data) or PHONE_REGEX.search(data):
            return True
    return False


def sanitize_analytics_payload(data: Any) -> tuple[Any, bool]:
    """Recursively scrub sensitive student PII from analytics payloads.
    
    Guarantees:
    - Sensitive student keys redacted to [REDACTED_STUDENT_PII]
    - Emails redacted to [REDACTED_EMAIL]
    - Phone numbers redacted to [REDACTED_PHONE]
    - Returns (sanitized_data, had_pii_flag)
    """
    had_pii = False
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower().strip()
            if k_lower in STUDENT_PII_KEYS:
                sanitized[k] = REDACTED_PII
                had_pii = True
            else:
                san_val, sub_had = sanitize_analytics_payload(v)
                sanitized[k] = san_val
                if sub_had:
                    had_pii = True
        return sanitized, had_pii
    elif isinstance(data, list):
        sanitized_list = []
        for item in data:
            san_item, sub_had = sanitize_analytics_payload(item)
            sanitized_list.append(san_item)
            if sub_had:
                had_pii = True
        return sanitized_list, had_pii
    elif isinstance(data, tuple):
        sanitized_items = []
        for item in data:
            san_item, sub_had = sanitize_analytics_payload(item)
            sanitized_items.append(san_item)
            if sub_had:
                had_pii = True
        return tuple(sanitized_items), had_pii
    elif isinstance(data, str):
        text = data
        if EMAIL_REGEX.search(text):
            text = EMAIL_REGEX.sub(REDACTED_EMAIL, text)
            had_pii = True
        if PHONE_REGEX.search(text):
            text = PHONE_REGEX.sub(REDACTED_PHONE, text)
            had_pii = True
        return text, had_pii
    return data, had_pii


def is_telemetry_consented(
    consent_status: Optional[str] = None,
    header_consent: Optional[str] = None,
    user_consent: Optional[bool] = None,
) -> bool:
    """Evaluate if telemetry tracking is consented.
    
    Returns False if user or request explicitly opted out / denied / revoked consent.
    """
    if header_consent:
        norm_h = header_consent.strip().lower()
        if norm_h in ("denied", "withdrawn", "opt_out", "optout", "0", "false", "revoked"):
            return False
    if consent_status:
        norm_s = consent_status.strip().lower()
        if norm_s in ("denied", "withdrawn", "opted_out", "opt_out", "revoked", "false", "0"):
            return False
    if user_consent is False:
        return False
    return True


def verify_server_conversion_trust(
    db: Session,
    event_name: str,
    payload: Dict[str, Any],
    current_user: Optional[Any] = None,
) -> bool:
    """Verify whether a business conversion event is server-trusted.
    
    Rules:
    - view / explore / inquiry_start: Must reference an existing RbpcExperience.
    - inquiry_submit: Must reference a genuine existing RbpcInquiry in DB.
    - inquiry_confirm: Must reference a genuine existing RbpcInquiry in 'confirmed' or 'closed' state.
    """
    from backend.models_rbpc import RbpcExperience, RbpcInquiry

    norm_event = event_name.lower().strip()
    exp_id = payload.get("experience_id")
    slug = payload.get("item_slug")
    inq_id = payload.get("inquiry_id") or payload.get("public_ref")

    if norm_event in (EventType.VIEW, EventType.EXPLORE, EventType.INQUIRY_START, "experience_view", "experience_explore"):
        if exp_id:
            try:
                exp_uuid = UUID(str(exp_id))
                exists = db.scalar(select(RbpcExperience.id).where(RbpcExperience.id == exp_uuid))
                return exists is not None
            except Exception:
                return False
        if slug:
            exists = db.scalar(select(RbpcExperience.id).where(RbpcExperience.slug == str(slug)))
            return exists is not None
        return False

    elif norm_event == EventType.INQUIRY_SUBMIT:
        if not inq_id:
            return False
        try:
            # Check UUID id or public_ref
            query = select(RbpcInquiry).where(
                or_(
                    RbpcInquiry.public_ref == str(inq_id),
                    RbpcInquiry.id == UUID(str(inq_id)) if _is_valid_uuid(str(inq_id)) else False,
                )
            )
            inquiry = db.scalar(query)
            return inquiry is not None
        except Exception:
            return False

    elif norm_event == EventType.INQUIRY_CONFIRM:
        if not inq_id:
            return False
        try:
            query = select(RbpcInquiry).where(
                or_(
                    RbpcInquiry.public_ref == str(inq_id),
                    RbpcInquiry.id == UUID(str(inq_id)) if _is_valid_uuid(str(inq_id)) else False,
                )
            )
            inquiry = db.scalar(query)
            if not inquiry:
                return False
            # Confirmation is only trusted if inquiry state is actually confirmed or closed
            return str(inquiry.state).lower() in ("confirmed", "closed")
        except Exception:
            return False

    return False


def _is_valid_uuid(val: str) -> bool:
    try:
        UUID(str(val))
        return True
    except Exception:
        return False


class DeviceInfo(BaseModel):
    """Device metadata for analytics."""
    platform: Optional[str] = Field(None, description="Platform (ios, android, web)")
    os_version: Optional[str] = Field(None, description="Operating system version")
    app_version: Optional[str] = Field(None, description="Application version")
    device_model: Optional[str] = Field(None, description="Device model")
    screen_width: Optional[int] = Field(None, description="Screen width in pixels")
    screen_height: Optional[int] = Field(None, description="Screen height in pixels")
    language: Optional[str] = Field(None, description="Device language")


# =============================================================================
# Event Validation & Recording
# =============================================================================

def get_event_category(event_name: str) -> Optional[str]:
    """
    Get the category for an event type.

    Args:
        event_name: The event name/type

    Returns:
        The event category or None if not found
    """
    return EVENT_CATEGORY_MAP.get(event_name)


def validate_event_payload(event_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize event payload based on event type.

    Args:
        event_name: The event name/type
        payload: The event payload to validate

    Returns:
        Validated and normalized payload
    """
    if not payload:
        return {}

    category = get_event_category(event_name)

    # Select appropriate payload schema based on category
    if category == EventCategory.ACTIVATION:
        schema = ActivationEventPayload
    elif category == EventCategory.LESSON:
        schema = LessonEventPayload
    elif category == EventCategory.QUIZ:
        schema = QuizEventPayload
    elif category == EventCategory.STREAK:
        schema = StreakEventPayload
    elif category == EventCategory.DISCOVERY:
        schema = DiscoveryEventPayload
    elif category == EventCategory.ENGAGEMENT:
        schema = EngagementEventPayload
    elif category == EventCategory.PERFORMANCE:
        schema = PerformanceEventPayload
    elif category == EventCategory.BUSINESS_CONVERSION:
        schema = BusinessConversionPayload
    else:
        # For unknown event types, use base payload
        schema = BaseEventPayload

    try:
        validated = schema(**payload)
        return validated.model_dump(exclude_none=True)
    except Exception:
        # If validation fails, return original payload
        return payload


def create_event_record(
    user_id: Optional[UUID] = None,
    event_name: str = "",
    payload: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
    session_id: Optional[UUID] = None,
    cohort: Optional[str] = None,
    device_info: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    consent_status: Optional[str] = "consented",
    is_server_verified: bool = False,
    is_demo: bool = False,
    is_synthetic: bool = False,
) -> Dict[str, Any]:
    """
    Create a validated event record for database insertion with strict zero student PII.

    Args:
        user_id: User ID (optional for anonymous visitor sessions)
        event_name: Event name/type
        payload: Event payload (will be sanitized to redact student PII)
        path: URL path or screen name
        session_id: Session identifier
        cohort: User cohort (e.g., "2024-W01")
        device_info: Device metadata
        idempotency_key: Unique client idempotency key
        consent_status: Consent lifecycle state
        is_server_verified: True if verified by authoritative server record
        is_demo: True if demo traffic
        is_synthetic: True if benchmark/synthetic traffic

    Returns:
        Dictionary with validated event data ready for AnalyticsEvent model
    """
    # 1. Scrub student PII recursively before validation and persistence
    raw_payload = payload or {}
    sanitized_payload, _ = sanitize_analytics_payload(raw_payload)

    # If payload contained metadata keys for demo / synthetic / idempotency, inherit if not explicitly set
    if not is_demo and (sanitized_payload.get("is_demo") or sanitized_payload.get("demo")):
        is_demo = True
    if not is_synthetic and (sanitized_payload.get("is_synthetic") or sanitized_payload.get("synthetic")):
        is_synthetic = True
    if not idempotency_key and sanitized_payload.get("idempotency_key"):
        idempotency_key = str(sanitized_payload.get("idempotency_key"))
    if consent_status == "consented" and sanitized_payload.get("consent_status"):
        consent_status = str(sanitized_payload.get("consent_status"))

    validated_payload = validate_event_payload(event_name, sanitized_payload)
    event_category = get_event_category(event_name)

    # Validate device info if provided (also scrub PII)
    validated_device_info = None
    if device_info:
        sanitized_device, _ = sanitize_analytics_payload(device_info)
        try:
            device = DeviceInfo(**sanitized_device)
            validated_device_info = device.model_dump(exclude_none=True)
        except Exception:
            validated_device_info = sanitized_device

    return {
        "user_id": user_id,
        "event_name": event_name,
        "payload": validated_payload,
        "path": path,
        "session_id": session_id,
        "cohort": cohort,
        "event_category": event_category,
        "device_info": validated_device_info,
        "idempotency_key": idempotency_key,
        "consent_status": consent_status,
        "is_server_verified": is_server_verified,
        "is_demo": is_demo,
        "is_synthetic": is_synthetic,
    }


def record_server_conversion_event(
    db: Session,
    event_name: str,
    payload: Optional[Dict[str, Any]] = None,
    user_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    path: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    cohort: Optional[str] = None,
    is_demo: bool = False,
    is_synthetic: bool = False,
) -> Any:
    """Record an authoritative, server-verified business conversion event directly in DB."""
    from backend.models import AnalyticsEvent

    # Check for existing idempotency key to avoid duplicate insertion
    if idempotency_key:
        existing = db.scalar(
            select(AnalyticsEvent).where(AnalyticsEvent.idempotency_key == str(idempotency_key))
        )
        if existing:
            return existing

    event_data = create_event_record(
        user_id=user_id,
        event_name=event_name,
        payload=payload,
        path=path,
        session_id=session_id,
        cohort=cohort,
        idempotency_key=idempotency_key,
        consent_status="consented",
        is_server_verified=True,
        is_demo=is_demo,
        is_synthetic=is_synthetic,
    )
    event_row = AnalyticsEvent(**event_data)
    db.add(event_row)
    db.commit()
    db.refresh(event_row)
    return event_row

