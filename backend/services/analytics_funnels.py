"""
Analytics Funnel Service for Luuniensuki LMS.

This module provides functions to calculate funnel metrics for different user journeys
including onboarding, lesson progression, and quiz completion.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, distinct
from sqlalchemy.orm import Session

from backend.models import AnalyticsEvent, User, UserProgress, QuizAttempt


# =============================================================================
# Funnel Stage Definitions
# =============================================================================

FUNNEL_DEFINITIONS = {
    "onboarding": {
        "name": "Onboarding Funnel",
        "description": "User journey from first app open to first lesson completion",
        "stages": [
            {
                "name": "app_opened",
                "display_name": "App Opened",
                "event_name": "app_opened",
            },
            {
                "name": "onboarding_started",
                "display_name": "Onboarding Started",
                "event_name": "onboarding_started",
            },
            {
                "name": "goal_selected",
                "display_name": "Goal Selected",
                "event_name": "onboarding_completed",
            },
            {
                "name": "first_lesson_started",
                "display_name": "First Lesson Started",
                "event_name": "first_lesson_started",
            },
            {
                "name": "first_lesson_completed",
                "display_name": "First Lesson Completed",
                "event_name": "lesson_completed",
            },
        ],
    },
    "lesson": {
        "name": "Lesson Funnel",
        "description": "User journey through lesson content",
        "stages": [
            {
                "name": "lesson_viewed",
                "display_name": "Lesson Viewed",
                "event_name": "lesson_viewed",
            },
            {
                "name": "lesson_started",
                "display_name": "Lesson Started",
                "event_name": "lesson_started",
            },
            {
                "name": "lesson_50_percent",
                "display_name": "50% Progress",
                "event_name": "lesson_time_spent",
                "filter": {"min_completion_percentage": 50},
            },
            {
                "name": "lesson_completed",
                "display_name": "Lesson Completed",
                "event_name": "lesson_completed",
            },
        ],
    },
    "quiz": {
        "name": "Quiz Funnel",
        "description": "User journey through quiz attempts",
        "stages": [
            {
                "name": "quiz_started",
                "display_name": "Quiz Started",
                "event_name": "quiz_started",
            },
            {
                "name": "quiz_submitted",
                "display_name": "Quiz Submitted",
                "event_name": "quiz_submitted",
            },
            {
                "name": "quiz_passed",
                "display_name": "Quiz Passed",
                "event_name": "quiz_passed",
            },
        ],
    },
}


# =============================================================================
# Funnel Calculation Functions
# =============================================================================


def _count_users_in_stage(
    session: Session,
    stage: dict[str, Any],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    cohort: Optional[str],
) -> int:
    """
    Count unique users who reached a specific funnel stage.

    Args:
        session: Database session
        stage: Stage definition dict
        start_date: Optional start date filter
        end_date: Optional end date filter
        cohort: Optional cohort filter

    Returns:
        Count of unique users
    """
    event_name = stage["event_name"]
    stage_filter = stage.get("filter", {})

    query = select(func.count(distinct(AnalyticsEvent.user_id))).where(
        AnalyticsEvent.event_name == event_name
    )

    if start_date:
        query = query.where(AnalyticsEvent.created_at >= start_date)
    if end_date:
        query = query.where(AnalyticsEvent.created_at <= end_date)
    if cohort:
        query = query.where(AnalyticsEvent.cohort == cohort)

    # Apply stage-specific filters
    if "min_completion_percentage" in stage_filter:
        min_pct = stage_filter["min_completion_percentage"]
        query = query.where(
            func.cast(
                AnalyticsEvent.payload["completion_percentage"].astext,
                func.numeric()
            ) >= min_pct
        )

    count = session.execute(query).scalar() or 0
    return count


def calculate_funnel_data(
    session: Session,
    funnel_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    cohort: Optional[str] = None,
) -> dict[str, Any]:
    """
    Calculate funnel metrics for a specific funnel type.

    Args:
        session: Database session
        funnel_type: Type of funnel (onboarding, lesson, quiz)
        start_date: Optional start date for filtering events
        end_date: Optional end date for filtering events
        cohort: Optional cohort identifier for filtering users

    Returns:
        Dictionary with funnel metrics
    """
    if funnel_type not in FUNNEL_DEFINITIONS:
        raise ValueError(f"Unknown funnel type: {funnel_type}")

    funnel_def = FUNNEL_DEFINITIONS[funnel_type]
    stages = funnel_def["stages"]

    # Calculate counts for each stage
    stage_counts = []
    for stage in stages:
        count = _count_users_in_stage(session, stage, start_date, end_date, cohort)
        stage_counts.append({
            "stage": stage["name"],
            "display_name": stage["display_name"],
            "count": count,
        })

    # Calculate conversion rates
    for i in range(len(stage_counts)):
        if i == 0:
            stage_counts[i]["conversion_from_previous"] = 100.0
        else:
            prev_count = stage_counts[i - 1]["count"]
            curr_count = stage_counts[i]["count"]
            if prev_count > 0:
                rate = (curr_count / prev_count) * 100
                stage_counts[i]["conversion_from_previous"] = round(rate, 2)
            else:
                stage_counts[i]["conversion_from_previous"] = 0.0

    # Calculate overall conversion (first to last stage)
    overall_conversion = 0.0
    if stage_counts and stage_counts[0]["count"] > 0:
        first_count = stage_counts[0]["count"]
        last_count = stage_counts[-1]["count"]
        overall_conversion = round((last_count / first_count) * 100, 2)

    # Get total users in funnel (first stage count)
    total_users = stage_counts[0]["count"] if stage_counts else 0

    return {
        "funnel_type": funnel_type,
        "funnel_name": funnel_def["name"],
        "description": funnel_def["description"],
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
        "cohort": cohort,
        "total_users": total_users,
        "stages": stage_counts,
        "overall_conversion": overall_conversion,
    }


def list_available_funnels() -> list[dict[str, Any]]:
    """
    List all available funnel types.

    Returns:
        List of funnel definitions
    """
    return [
        {
            "funnel_type": funnel_type,
            "name": definition["name"],
            "description": definition["description"],
            "stage_count": len(definition["stages"]),
            "stages": [stage["display_name"] for stage in definition["stages"]],
        }
        for funnel_type, definition in FUNNEL_DEFINITIONS.items()
    ]
