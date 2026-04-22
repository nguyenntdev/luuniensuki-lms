"""
Streak Service for managing user learning streaks and rewards.

This service handles:
- Streak calculation based on activity dates
- Daily streak check-ins
- Streak freeze logic
- Milestone rewards (7-day, 30-day, 100-day streaks)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import StreakReward, User, UserBadge, Badge

# Streak milestone configurations
STREAK_MILESTONES = {
    7: {"xp": 100, "badge_slug": "streak-7", "freeze": 0},
    30: {"xp": 500, "badge_slug": "streak-30-days", "freeze": 0},
    100: {"xp": 2000, "badge_slug": "streak-100-days", "freeze": 1},
}

# Daily streak completion reward
DAILY_STREAK_XP = 10


def calculate_current_streak(user: User, now: datetime) -> int:
    """
    Calculate current streak based on last_active_at.
    
    Args:
        user: The user to calculate streak for
        now: Current datetime
        
    Returns:
        Current streak count
    """
    if user.last_active_at is None:
        return 0
    
    last_date = user.last_active_at.astimezone(timezone.utc).date()
    today = now.astimezone(timezone.utc).date()
    diff_days = (today - last_date).days
    
    # Same day - return current streak
    if diff_days <= 0:
        return user.current_streak
    
    # Next day - streak continues
    if diff_days == 1:
        return user.current_streak
    
    # More than 1 day - streak broken
    return 0


def is_streak_maintained_today(user: User, now: datetime) -> bool:
    """
    Check if user has maintained their streak today.
    
    Args:
        user: The user to check
        now: Current datetime
        
    Returns:
        True if user was active today, False otherwise
    """
    if user.last_active_at is None:
        return False
    
    last_date = user.last_active_at.astimezone(timezone.utc).date()
    today = now.astimezone(timezone.utc).date()
    
    return last_date == today


def is_streak_at_risk(user: User, now: datetime) -> bool:
    """
    Check if user's streak is at risk (hasn't been active today).
    
    Args:
        user: The user to check
        now: Current datetime
        
    Returns:
        True if streak is at risk, False otherwise
    """
    if user.current_streak == 0:
        return False
    
    return not is_streak_maintained_today(user, now)


def use_streak_freeze(db: Session, user: User, now: datetime) -> bool:
    """
    Use a streak freeze to protect the streak.
    
    Args:
        db: Database session
        user: The user using the freeze
        now: Current datetime
        
    Returns:
        True if freeze was successfully used, False otherwise
    """
    if user.streak_freezes <= 0:
        return False
    
    # Can only use if streak is at risk
    if not is_streak_at_risk(user, now):
        return False
    
    # Use one freeze
    user.streak_freezes -= 1
    
    # Update last_active_at to today to maintain streak
    user.last_active_at = now
    
    db.commit()
    return True


def award_daily_streak_reward(db: Session, user: User, now: datetime) -> int:
    """
    Award XP for daily streak completion.

    Args:
        db: Database session
        user: The user to award
        now: Current datetime

    Returns:
        XP awarded
    """
    # Only award if already active today
    if not is_streak_maintained_today(user, now):
        return 0

    # Award daily XP
    user.total_xp += DAILY_STREAK_XP
    db.commit()

    return DAILY_STREAK_XP


def award_milestone_rewards(
    db: Session, user: User, now: datetime
) -> dict[str, any]:
    """
    Award milestone rewards for reaching streak goals.

    Args:
        db: Database session
        user: The user to check for milestones
        now: Current datetime

    Returns:
        Dictionary with awarded milestones info
    """
    awarded_milestones = []
    total_xp = 0
    total_freezes = 0
    badges_awarded = []

    for milestone_day, rewards in STREAK_MILESTONES.items():
        # Check if user has reached this milestone
        if user.current_streak < milestone_day:
            continue

        # Check if already awarded
        existing = db.execute(
            select(StreakReward).where(
                StreakReward.user_id == user.id,
                StreakReward.streak_day == milestone_day
            )
        ).scalar_one_or_none()

        if existing:
            continue

        # Award XP
        if rewards["xp"] > 0:
            user.total_xp += rewards["xp"]
            total_xp += rewards["xp"]

            # Record reward
            db.add(
                StreakReward(
                    user_id=user.id,
                    streak_day=milestone_day,
                    reward_type="xp",
                    reward_amount=rewards["xp"],
                    awarded_at=now,
                )
            )

        # Award badge
        badge_slug = rewards.get("badge_slug")
        if badge_slug:
            badge = db.execute(
                select(Badge).where(Badge.slug == badge_slug)
            ).scalar_one_or_none()

            if badge:
                # Check if user already has this badge
                existing_badge = db.execute(
                    select(UserBadge).where(
                        UserBadge.user_id == user.id,
                        UserBadge.badge_id == badge.id
                    )
                ).scalar_one_or_none()

                if not existing_badge:
                    db.add(
                        UserBadge(
                            user_id=user.id,
                            badge_id=badge.id,
                            earned_at=now,
                        )
                    )
                    badges_awarded.append({
                        "slug": badge_slug,
                        "name": badge.name,
                        "xp_bonus": badge.xp_bonus,
                    })

                    # Award badge XP bonus
                    if badge.xp_bonus > 0:
                        user.total_xp += badge.xp_bonus
                        total_xp += badge.xp_bonus

        # Award streak freezes
        if rewards["freeze"] > 0:
            user.streak_freezes += rewards["freeze"]
            total_freezes += rewards["freeze"]

            # Record reward
            db.add(
                StreakReward(
                    user_id=user.id,
                    streak_day=milestone_day,
                    reward_type="streak_freeze",
                    reward_amount=rewards["freeze"],
                    awarded_at=now,
                )
            )

        awarded_milestones.append({
            "day": milestone_day,
            "xp": rewards["xp"],
            "freezes": rewards["freeze"],
        })

    if awarded_milestones:
        db.commit()

    return {
        "milestones": awarded_milestones,
        "total_xp": total_xp,
        "total_freezes": total_freezes,
        "badges": badges_awarded,
    }


def get_next_milestone(current_streak: int) -> Optional[dict]:
    """
    Get the next milestone to reach.

    Args:
        current_streak: Current streak count

    Returns:
        Next milestone info or None if no more milestones
    """
    for day in sorted(STREAK_MILESTONES.keys()):
        if current_streak < day:
            return {
                "day": day,
                "days_remaining": day - current_streak,
                "rewards": STREAK_MILESTONES[day],
            }

    return None


