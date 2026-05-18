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

from backend.models import Badge, BadgeTier, MilestoneType, User, UserBadge, UserMilestone


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




def get_tier_xp_multiplier(tier: BadgeTier) -> float:
    """
    Get XP multiplier for a specific badge tier.

    Args:
        tier: Badge tier

    Returns:
        XP multiplier (bronze: 1x, silver: 1.5x, gold: 2x, platinum: 3x)
    """
    multipliers = {
        BadgeTier.bronze: 1.0,
        BadgeTier.silver: 1.5,
        BadgeTier.gold: 2.0,
        BadgeTier.platinum: 3.0,
    }
    return multipliers.get(tier, 1.0)


def get_next_tier(current_tier: BadgeTier) -> Optional[BadgeTier]:
    """
    Get the next tier after the current one.

    Args:
        current_tier: Current badge tier

    Returns:
        Next tier or None if already at platinum
    """
    tier_progression = {
        BadgeTier.bronze: BadgeTier.silver,
        BadgeTier.silver: BadgeTier.gold,
        BadgeTier.gold: BadgeTier.platinum,
        BadgeTier.platinum: None,
    }
    return tier_progression.get(current_tier)


def calculate_tier_xp_bonus(base_xp: int, tier: BadgeTier) -> int:
    """
    Calculate the XP bonus for a badge tier.

    Args:
        base_xp: Base XP bonus from the badge
        tier: Badge tier

    Returns:
        Total XP bonus including tier multiplier
    """
    multiplier = get_tier_xp_multiplier(tier)
    return int(base_xp * multiplier)


def check_badge_tier_upgrade(
    db: Session,
    user_id: UUID,
    badge_slug: str,
    current_progress: int,
) -> Optional[UserBadge]:
    """
    Check if a user's badge can be upgraded to the next tier and perform the upgrade.

    This function evaluates the user's progress against tier-specific thresholds
    and upgrades the badge tier if criteria are met.

    Args:
        db: Database session
        user_id: User ID
        badge_slug: Badge slug to check
        current_progress: Current progress count (e.g., streak days, quizzes passed)

    Returns:
        Updated UserBadge if upgrade occurred, None otherwise
    """
    # Get the badge
    badge = db.execute(
        select(Badge).where(Badge.slug == badge_slug)
    ).scalar_one_or_none()

    if not badge:
        return None

    # Get the user's badge record
    user_badge = db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
    ).scalar_one_or_none()

    if not user_badge:
        return None

    # Check if can upgrade to next tier
    next_tier = get_next_tier(user_badge.current_tier)
    if not next_tier:
        # Already at platinum tier
        return None

    # Define tier thresholds based on badge unlock criteria
    # These thresholds determine when a badge upgrades to the next tier
    tier_thresholds = _get_tier_thresholds(badge)

    threshold = tier_thresholds.get(next_tier)
    if threshold and current_progress >= threshold:
        # Upgrade the tier
        old_tier = user_badge.current_tier
        user_badge.current_tier = next_tier

        # Award tier upgrade XP bonus
        user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if user and badge.tier_xp_bonus > 0:
            tier_bonus = calculate_tier_xp_bonus(badge.tier_xp_bonus, next_tier)
            user.total_xp += tier_bonus

        db.flush()
        return user_badge

    return None


def _get_tier_thresholds(badge: Badge) -> dict[BadgeTier, int]:
    """
    Get tier upgrade thresholds for a badge based on its unlock criteria.

    Args:
        badge: Badge model

    Returns:
        Dictionary mapping tiers to progress thresholds
    """
    unlock_criteria = badge.unlock_criteria or {}

    # Extract base threshold from unlock criteria
    base_threshold = unlock_criteria.get("count", 1)

    # Define tier multipliers for progression
    # Silver: 2x base, Gold: 5x base, Platinum: 10x base
    return {
        BadgeTier.silver: base_threshold * 2,
        BadgeTier.gold: base_threshold * 5,
        BadgeTier.platinum: base_threshold * 10,
    }


def award_tiered_badge(
    db: Session,
    user_id: UUID,
    badge_slug: str,
    initial_tier: BadgeTier = BadgeTier.bronze,
) -> Optional[UserBadge]:
    """
    Award a badge to a user with a specific tier.

    Args:
        db: Database session
        user_id: User ID
        badge_slug: Badge slug to award
        initial_tier: Initial tier to award (default: bronze)

    Returns:
        Created UserBadge or None if already exists
    """
    badge = db.execute(
        select(Badge).where(Badge.slug == badge_slug)
    ).scalar_one_or_none()

    if not badge:
        return None

    # Check if user already has this badge
    existing = db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
    ).scalar_one_or_none()

    if existing:
        return None

    # Create new badge award
    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id,
        current_tier=initial_tier,
        earned_at=datetime.now(timezone.utc),
    )
    db.add(user_badge)

    # Award XP bonus
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if user and badge.xp_bonus > 0:
        tier_bonus = calculate_tier_xp_bonus(badge.xp_bonus, initial_tier)
        user.total_xp += tier_bonus

    db.flush()
    return user_badge
