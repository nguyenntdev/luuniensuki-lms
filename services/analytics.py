"""
Analytics Service for Luuniensuki LMS.

This module defines the event taxonomy and provides utilities for recording
analytics events with proper validation and categorization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
}


# =============================================================================
# Event Schema Definitions
# =============================================================================

class BaseEventPayload(BaseModel):
    """Base event payload with common fields."""
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
    user_id: UUID,
    event_name: str,
    payload: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
    session_id: Optional[UUID] = None,
    cohort: Optional[str] = None,
    device_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a validated event record for database insertion.

    Args:
        user_id: User ID
        event_name: Event name/type
        payload: Event payload
        path: URL path or screen name
        session_id: Session identifier
        cohort: User cohort (e.g., "2024-W01")
        device_info: Device metadata

    Returns:
        Dictionary with validated event data
    """
    validated_payload = validate_event_payload(event_name, payload or {})
    event_category = get_event_category(event_name)

    # Validate device info if provided
    validated_device_info = None
    if device_info:
        try:
            device = DeviceInfo(**device_info)
            validated_device_info = device.model_dump(exclude_none=True)
        except Exception:
            validated_device_info = device_info

    return {
        "user_id": user_id,
        "event_name": event_name,
        "payload": validated_payload,
        "path": path,
        "session_id": session_id,
        "cohort": cohort,
        "event_category": event_category,
        "device_info": validated_device_info,
    }

