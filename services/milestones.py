"""
Milestone Service for Luuniensuki LMS.

This module provides utilities for tracking and managing user milestones.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import MilestoneType, User, UserMilestone


def create_milestone(
    db: Session,
    user_id: UUID,
    milestone_type: MilestoneType,
    context_data: Optional[dict[str, Any]] = None,
    achieved_at: Optional[datetime] = None,
) -> Optional[UserMilestone]:
    """
    Create a milestone for a user if it doesn't already exist.

    Args:
        db: Database session
        user_id: User ID
        milestone_type: Type of milestone
        context_data: Optional context data (e.g., which motif, which quiz)
        achieved_at: Optional achievement timestamp (defaults to now)

    Returns:
        Created UserMilestone or None if it already exists
    """
    # Check if milestone already exists
    existing = db.execute(
        select(UserMilestone).where(
            UserMilestone.user_id == user_id,
            UserMilestone.milestone_type == milestone_type,
        )
    ).scalar_one_or_none()

    if existing:
        return None

    # Create new milestone
    milestone = UserMilestone(
        user_id=user_id,
        milestone_type=milestone_type,
        context_data=context_data,
        achieved_at=achieved_at or datetime.now(timezone.utc),
        celebrated=False,
    )
    db.add(milestone)

    return milestone


def check_and_create_first_motif_discovered(
    db: Session,
    user_id: UUID,
    motif_id: UUID,
) -> Optional[UserMilestone]:
    """
    Check if this is the user's first motif discovery and create milestone.

    Args:
        db: Database session
        user_id: User ID
        motif_id: Motif ID that was discovered

    Returns:
        Created milestone or None
    """
    return create_milestone(
        db,
        user_id,
        MilestoneType.first_motif_discovered,
        context_data={"motif_id": str(motif_id)},
    )


def check_and_create_first_lesson_completed(
    db: Session,
    user_id: UUID,
    motif_id: UUID,
) -> Optional[UserMilestone]:
    """
    Check if this is the user's first lesson completion and create milestone.

    Args:
        db: Database session
        user_id: User ID
        motif_id: Motif ID whose lesson was completed

    Returns:
        Created milestone or None
    """
    return create_milestone(
        db,
        user_id,
        MilestoneType.first_lesson_completed,
        context_data={"motif_id": str(motif_id)},
    )


def check_and_create_first_quiz_passed(
    db: Session,
    user_id: UUID,
    motif_id: UUID,
    score: int,
    max_score: int,
    percentage: int,
) -> Optional[UserMilestone]:
    """
    Check if this is the user's first quiz pass and create milestone.

    Args:
        db: Database session
        user_id: User ID
        motif_id: Motif ID whose quiz was passed
        score: Score achieved
        max_score: Maximum possible score
        percentage: Percentage score

    Returns:
        Created milestone or None
    """
    return create_milestone(
        db,
        user_id,
        MilestoneType.first_quiz_passed,
        context_data={
            "motif_id": str(motif_id),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
        },
    )


def check_and_create_first_badge_earned(
    db: Session,
    user_id: UUID,
    badge_slug: str,
) -> Optional[UserMilestone]:
    """
    Check if this is the user's first badge and create milestone.

    Args:
        db: Database session
        user_id: User ID
        badge_slug: Badge slug that was earned

    Returns:
        Created milestone or None
    """
    return create_milestone(
        db,
        user_id,
        MilestoneType.first_badge_earned,
        context_data={"badge_slug": badge_slug},
    )





def check_and_create_first_streak_7(
    db: Session,
    user_id: UUID,
    current_streak: int,
) -> Optional[UserMilestone]:
    """
    Check if user has reached 7-day streak for the first time and create milestone.

    Args:
        db: Database session
        user_id: User ID
        current_streak: Current streak count

    Returns:
        Created milestone or None
    """
    if current_streak >= 7:
        return create_milestone(
            db,
            user_id,
            MilestoneType.first_streak_7,
            context_data={"streak_count": current_streak},
        )
    return None


def check_and_create_onboarding_completed(
    db: Session,
    user_id: UUID,
) -> Optional[UserMilestone]:
    """
    Create onboarding completion milestone.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Created milestone or None
    """
    return create_milestone(
        db,
        user_id,
        MilestoneType.onboarding_completed,
    )


def get_user_milestones(
    db: Session,
    user_id: UUID,
) -> list[UserMilestone]:
    """
    Get all milestones for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of user milestones
    """
    return list(
        db.execute(
            select(UserMilestone)
            .where(UserMilestone.user_id == user_id)
            .order_by(UserMilestone.achieved_at.desc())
        ).scalars()
    )


def get_pending_milestones(
    db: Session,
    user_id: UUID,
) -> list[UserMilestone]:
    """
    Get milestones that haven't been celebrated yet.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of uncelebrated milestones
    """
    return list(
        db.execute(
            select(UserMilestone)
            .where(
                UserMilestone.user_id == user_id,
                UserMilestone.celebrated == False,  # noqa: E712
            )
            .order_by(UserMilestone.achieved_at.asc())
        ).scalars()
    )


def mark_milestone_celebrated(
    db: Session,
    milestone_id: UUID,
    user_id: UUID,
) -> Optional[UserMilestone]:
    """
    Mark a milestone as celebrated.

    Args:
        db: Database session
        milestone_id: Milestone ID
        user_id: User ID (for security check)

    Returns:
        Updated milestone or None if not found
    """
    milestone = db.execute(
        select(UserMilestone).where(
            UserMilestone.id == milestone_id,
            UserMilestone.user_id == user_id,
        )
    ).scalar_one_or_none()

    if milestone:
        milestone.celebrated = True
        db.flush()

    return milestone
