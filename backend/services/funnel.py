"""
Funnel Analysis Service for Luuniensuki LMS.

This module provides funnel tracking and conversion analysis for user journeys.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session

# =============================================================================
# Funnel Stage Constants
# =============================================================================


class FunnelType:
    """Funnel type constants."""
    LESSON = "lesson"
    ONBOARDING = "onboarding"
    QUIZ = "quiz"


class LessonFunnelStage:
    """Lesson funnel stages in order."""
    VIEW_LESSON = "view_lesson"
    START_LESSON = "start_lesson"
    COMPLETE_LESSON = "complete_lesson"
    START_QUIZ = "start_quiz"
    COMPLETE_QUIZ = "complete_quiz"
    PASS_QUIZ = "pass_quiz"


class OnboardingFunnelStage:
    """Onboarding funnel stages in order."""
    APP_OPENED = "app_opened"
    ONBOARDING_STARTED = "onboarding_started"
    PROFILE_CREATED = "profile_created"
    FIRST_LESSON_VIEWED = "first_lesson_viewed"
    ONBOARDING_COMPLETED = "onboarding_completed"


class QuizFunnelStage:
    """Quiz funnel stages in order."""
    QUIZ_VIEWED = "quiz_viewed"
    QUIZ_STARTED = "quiz_started"
    QUIZ_SUBMITTED = "quiz_submitted"
    QUIZ_PASSED = "quiz_passed"


# Ordered funnel stages for each funnel type
FUNNEL_STAGES: Dict[str, List[str]] = {
    FunnelType.LESSON: [
        LessonFunnelStage.VIEW_LESSON,
        LessonFunnelStage.START_LESSON,
        LessonFunnelStage.COMPLETE_LESSON,
        LessonFunnelStage.START_QUIZ,
        LessonFunnelStage.COMPLETE_QUIZ,
        LessonFunnelStage.PASS_QUIZ,
    ],
    FunnelType.ONBOARDING: [
        OnboardingFunnelStage.APP_OPENED,
        OnboardingFunnelStage.ONBOARDING_STARTED,
        OnboardingFunnelStage.PROFILE_CREATED,
        OnboardingFunnelStage.FIRST_LESSON_VIEWED,
        OnboardingFunnelStage.ONBOARDING_COMPLETED,
    ],
    FunnelType.QUIZ: [
        QuizFunnelStage.QUIZ_VIEWED,
        QuizFunnelStage.QUIZ_STARTED,
        QuizFunnelStage.QUIZ_SUBMITTED,
        QuizFunnelStage.QUIZ_PASSED,
    ],
}


# =============================================================================
# Funnel Tracking Functions
# =============================================================================


def create_funnel_record(
    user_id: UUID,
    funnel_type: str,
    stage: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a validated funnel record for database insertion.

    Args:
        user_id: User ID
        funnel_type: Type of funnel (lesson, onboarding, quiz)
        stage: Current stage in the funnel
        metadata: Optional metadata (motif_id, urn_id, etc.)

    Returns:
        Dictionary with validated funnel data
    """
    if funnel_type not in FUNNEL_STAGES:
        raise ValueError(f"Invalid funnel_type: {funnel_type}")

    stages = FUNNEL_STAGES[funnel_type]
    if stage not in stages:
        raise ValueError(f"Invalid stage '{stage}' for funnel_type '{funnel_type}'")

    now = datetime.now(timezone.utc)

    return {
        "user_id": user_id,
        "funnel_type": funnel_type,
        "stage": stage,
        "started_at": now,
        "stage_timestamps": {stage: now.isoformat()},
        "completed_at": None if stage != stages[-1] else now,
        "metadata": metadata or {},
    }


def update_funnel_stage(
    funnel_record: Dict[str, Any],
    new_stage: str,
) -> Dict[str, Any]:
    """
    Update a funnel record with a new stage.

    Args:
        funnel_record: Existing funnel record
        new_stage: New stage to update to

    Returns:
        Updated funnel record
    """
    funnel_type = funnel_record["funnel_type"]
    stages = FUNNEL_STAGES[funnel_type]

    if new_stage not in stages:
        raise ValueError(f"Invalid stage '{new_stage}' for funnel_type '{funnel_type}'")

    now = datetime.now(timezone.utc)

    # Update stage timestamps
    stage_timestamps = funnel_record.get("stage_timestamps", {})
    stage_timestamps[new_stage] = now.isoformat()

    # Update current stage
    funnel_record["stage"] = new_stage
    funnel_record["stage_timestamps"] = stage_timestamps

    # Mark as completed if this is the final stage
    if new_stage == stages[-1]:
        funnel_record["completed_at"] = now

    return funnel_record


# =============================================================================
# Funnel Analysis Functions
# =============================================================================


def calculate_conversion_rates(
    db: Session,
    funnel_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Calculate conversion rates between funnel stages.

    Args:
        db: Database session
        funnel_type: Type of funnel to analyze
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dictionary with conversion rates and counts per stage
    """
    from backend.models import Funnel

    if funnel_type not in FUNNEL_STAGES:
        raise ValueError(f"Invalid funnel_type: {funnel_type}")

    stages = FUNNEL_STAGES[funnel_type]

    # Build base query
    query = select(Funnel).where(Funnel.funnel_type == funnel_type)

    if start_date:
        query = query.where(Funnel.started_at >= start_date)
    if end_date:
        query = query.where(Funnel.started_at <= end_date)

    funnels = db.execute(query).scalars().all()

    # Count users at each stage
    stage_counts: Dict[str, int] = {stage: 0 for stage in stages}
    unique_users_per_stage: Dict[str, set] = {stage: set() for stage in stages}

    for funnel in funnels:
        timestamps = funnel.stage_timestamps or {}
        for stage in stages:
            if stage in timestamps:
                stage_counts[stage] += 1
                unique_users_per_stage[stage].add(str(funnel.user_id))

    # Calculate conversion rates
    conversion_rates = []
    for i, stage in enumerate(stages):
        count = len(unique_users_per_stage[stage])

        # Calculate conversion from previous stage
        conversion_rate = None
        if i > 0:
            prev_count = len(unique_users_per_stage[stages[i - 1]])
            if prev_count > 0:
                conversion_rate = (count / prev_count) * 100

        conversion_rates.append({
            "stage": stage,
            "count": count,
            "conversion_rate": round(conversion_rate, 2) if conversion_rate is not None else None,
        })

    # Calculate overall conversion rate (first stage to last stage)
    overall_conversion = None
    if len(unique_users_per_stage[stages[0]]) > 0:
        overall_conversion = (
            len(unique_users_per_stage[stages[-1]]) /
            len(unique_users_per_stage[stages[0]])
        ) * 100

    return {
        "funnel_type": funnel_type,
        "stages": conversion_rates,
        "overall_conversion": round(overall_conversion, 2) if overall_conversion is not None else None,
        "total_started": len(unique_users_per_stage[stages[0]]),
        "total_completed": len(unique_users_per_stage[stages[-1]]),
    }


def identify_dropoff_points(
    db: Session,
    funnel_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    threshold: float = 20.0,
) -> Dict[str, Any]:
    """
    Identify significant drop-off points in a funnel.

    Args:
        db: Database session
        funnel_type: Type of funnel to analyze
        start_date: Optional start date filter
        end_date: Optional end date filter
        threshold: Drop-off percentage threshold to flag (default: 20%)

    Returns:
        Dictionary with drop-off analysis
    """
    conversion_data = calculate_conversion_rates(db, funnel_type, start_date, end_date)

    dropoff_points = []
    stages = conversion_data["stages"]

    for i in range(1, len(stages)):
        current_stage = stages[i]
        previous_stage = stages[i - 1]

        drop_count = previous_stage["count"] - current_stage["count"]
        drop_rate = 100 - current_stage["conversion_rate"] if current_stage["conversion_rate"] else 100

        if drop_rate >= threshold:
            dropoff_points.append({
                "from_stage": previous_stage["stage"],
                "to_stage": current_stage["stage"],
                "drop_count": drop_count,
                "drop_rate": round(drop_rate, 2),
                "severity": "high" if drop_rate >= 50 else "medium",
            })

    return {
        "funnel_type": funnel_type,
        "dropoff_threshold": threshold,
        "dropoff_points": dropoff_points,
        "total_dropoff_points": len(dropoff_points),
    }


def get_user_funnel_progress(
    db: Session,
    user_id: UUID,
    funnel_type: str,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Get a user's progress through a specific funnel type.

    Args:
        db: Database session
        user_id: User ID to track
        funnel_type: Type of funnel
        metadata_filter: Optional metadata filter (e.g., {"motif_id": "..."})

    Returns:
        List of funnel records for the user
    """
    from backend.models import Funnel

    query = select(Funnel).where(
        and_(
            Funnel.user_id == user_id,
            Funnel.funnel_type == funnel_type,
        )
    )

    funnels = db.execute(query.order_by(Funnel.started_at.desc())).scalars().all()

    result = []
    for funnel in funnels:
        # Apply metadata filter if provided
        if metadata_filter:
            funnel_metadata = funnel.metadata_json or {}
            match = all(
                funnel_metadata.get(k) == v for k, v in metadata_filter.items()
            )
            if not match:
                continue

        result.append({
            "id": str(funnel.id),
            "funnel_type": funnel.funnel_type,
            "current_stage": funnel.stage,
            "started_at": funnel.started_at.isoformat(),
            "completed_at": funnel.completed_at.isoformat() if funnel.completed_at else None,
            "stage_timestamps": funnel.stage_timestamps,
            "metadata": funnel.metadata_json,
        })

    return result
