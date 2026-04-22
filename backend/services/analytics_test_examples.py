"""
Test examples for the analytics event taxonomy.

This file demonstrates how to use the analytics service and event taxonomy.
"""

from uuid import uuid4
from services.analytics import (
    EventType,
    EventCategory,
    get_event_category,
    validate_event_payload,
    create_event_record,
)


def test_event_categorization():
    """Test that events are correctly categorized."""
    
    # Test activation events
    assert get_event_category(EventType.APP_OPENED) == EventCategory.ACTIVATION
    assert get_event_category(EventType.ONBOARDING_COMPLETED) == EventCategory.ACTIVATION
    
    # Test lesson events
    assert get_event_category(EventType.LESSON_STARTED) == EventCategory.LESSON
    assert get_event_category(EventType.LESSON_COMPLETED) == EventCategory.LESSON
    
    # Test quiz events
    assert get_event_category(EventType.QUIZ_PASSED) == EventCategory.QUIZ
    assert get_event_category(EventType.QUESTION_ANSWERED) == EventCategory.QUIZ
    
    # Test streak events
    assert get_event_category(EventType.STREAK_CONTINUED) == EventCategory.STREAK
    assert get_event_category(EventType.STREAK_MILESTONE_REACHED) == EventCategory.STREAK
    
    # Test discovery events
    assert get_event_category(EventType.MOTIF_MASTERED) == EventCategory.DISCOVERY
    
    # Test engagement events
    assert get_event_category(EventType.SESSION_STARTED) == EventCategory.ENGAGEMENT
    assert get_event_category(EventType.BADGE_EARNED) == EventCategory.ENGAGEMENT
    
    print("✓ Event categorization tests passed")


def test_payload_validation():
    """Test payload validation for different event types."""
    
    # Test lesson event payload
    lesson_payload = {
        "source": "mobile",
        "motif_id": str(uuid4()),
        "urn_id": str(uuid4()),
        "duration_seconds": 120,
    }
    validated = validate_event_payload(EventType.LESSON_COMPLETED, lesson_payload)
    assert "source" in validated
    assert "motif_id" in validated
    assert "duration_seconds" in validated
    
    # Test quiz event payload
    quiz_payload = {
        "source": "web",
        "motif_id": str(uuid4()),
        "score": 8,
        "max_score": 10,
        "percentage": 80.0,
        "passed": True,
    }
    validated = validate_event_payload(EventType.QUIZ_PASSED, quiz_payload)
    assert "score" in validated
    assert "passed" in validated
    
    # Test activation event payload
    activation_payload = {
        "source": "mobile",
        "screen": "welcome",
        "step": 1,
    }
    validated = validate_event_payload(EventType.ONBOARDING_STARTED, activation_payload)
    assert "screen" in validated
    assert "step" in validated
    
    print("✓ Payload validation tests passed")


def test_create_event_record():
    """Test creating event records with full context."""
    
    user_id = uuid4()
    session_id = uuid4()
    
    # Test creating a lesson completion event
    event_data = create_event_record(
        user_id=user_id,
        event_name=EventType.LESSON_COMPLETED,
        payload={
            "source": "mobile",
            "motif_id": str(uuid4()),
            "duration_seconds": 180,
        },
        path="/lesson/123",
        session_id=session_id,
        cohort="2024-W01",
        device_info={
            "platform": "ios",
            "app_version": "1.5.0",
            "os_version": "17.2",
        }
    )
    
    assert event_data["user_id"] == user_id
    assert event_data["event_name"] == EventType.LESSON_COMPLETED
    assert event_data["event_category"] == EventCategory.LESSON
    assert event_data["session_id"] == session_id
    assert event_data["cohort"] == "2024-W01"
    assert event_data["device_info"] is not None
    assert event_data["payload"]["source"] == "mobile"
    
    print("✓ Event record creation tests passed")


def example_usage_activation():
    """Example: Recording activation events."""
    
    user_id = uuid4()
    
    # App opened
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.APP_OPENED,
        payload={"source": "mobile"},
        cohort="2024-W01",
        device_info={"platform": "ios", "app_version": "1.5.0"}
    )
    print("Activation event:", event["event_name"], "→", event["event_category"])
    
    # Onboarding started
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.ONBOARDING_STARTED,
        payload={"source": "mobile", "screen": "welcome", "step": 1}
    )
    print("Onboarding event:", event["event_name"], "→", event["event_category"])


def example_usage_lesson():
    """Example: Recording lesson events."""
    
    user_id = uuid4()
    session_id = uuid4()
    motif_id = uuid4()
    
    # Lesson started
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.LESSON_STARTED,
        payload={
            "source": "mobile",
            "motif_id": str(motif_id),
        },
        session_id=session_id,
    )
    print("Lesson started:", event["event_name"], "→", event["event_category"])
    
    # Lesson completed
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.LESSON_COMPLETED,
        payload={
            "source": "mobile",
            "motif_id": str(motif_id),
            "duration_seconds": 180,
            "completion_percentage": 100.0,
        },
        session_id=session_id,
    )
    print("Lesson completed:", event["event_name"], "→", event["event_category"])


def example_usage_quiz():
    """Example: Recording quiz events."""

    user_id = uuid4()
    session_id = uuid4()
    motif_id = uuid4()

    # Quiz started
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.QUIZ_STARTED,
        payload={
            "source": "mobile",
            "motif_id": str(motif_id),
        },
        session_id=session_id,
    )
    print("Quiz started:", event["event_name"], "→", event["event_category"])

    # Quiz passed
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.QUIZ_PASSED,
        payload={
            "source": "mobile",
            "motif_id": str(motif_id),
            "score": 9,
            "max_score": 10,
            "percentage": 90.0,
            "passed": True,
            "time_taken_seconds": 45,
        },
        session_id=session_id,
    )
    print("Quiz passed:", event["event_name"], "→", event["event_category"])


def example_usage_streak():
    """Example: Recording streak events."""

    user_id = uuid4()

    # Streak continued
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.STREAK_CONTINUED,
        payload={
            "current_streak": 7,
            "previous_streak": 6,
        }
    )
    print("Streak continued:", event["event_name"], "→", event["event_category"])

    # Streak milestone
    event = create_event_record(
        user_id=user_id,
        event_name=EventType.STREAK_MILESTONE_REACHED,
        payload={
            "current_streak": 7,
            "milestone": 7,
        }
    )
    print("Streak milestone:", event["event_name"], "→", event["event_category"])


if __name__ == "__main__":
    print("\n=== Running Analytics Taxonomy Tests ===\n")

    test_event_categorization()
    test_payload_validation()
    test_create_event_record()

    print("\n=== Usage Examples ===\n")

    example_usage_activation()
    example_usage_lesson()
    example_usage_quiz()
    example_usage_streak()

    print("\n✅ All tests passed!\n")


