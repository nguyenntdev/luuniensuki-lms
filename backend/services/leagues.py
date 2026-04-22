"""
Weekly League Service for Duolingo-style competitive gamification.

This service handles:
- Creating and managing weekly league entries for users
- Tracking weekly XP within league tiers
- Calculating league standings and rankings
- Processing weekly promotions and demotions
- League tier progression (Bronze -> Silver -> Gold -> Platinum -> Diamond -> Obsidian)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from ..models import User, UserLeague, LeagueTier

# League configuration
PROMOTION_THRESHOLD = 10  # Top 10 users in a tier get promoted
DEMOTION_THRESHOLD = 5   # Bottom 5 users in a tier get demoted (except Bronze)
LEAGUE_SIZE = 50         # Target number of users per league group

# Tier progression order (lowest to highest)
TIER_ORDER = [
    LeagueTier.bronze,
    LeagueTier.silver,
    LeagueTier.gold,
    LeagueTier.platinum,
    LeagueTier.diamond,
    LeagueTier.obsidian,
]


def get_week_start_end(dt: Optional[datetime] = None) -> tuple[date, date]:
    """
    Get the Monday (start) and Sunday (end) of the week for the given datetime.
    
    Args:
        dt: Datetime to get week for. Defaults to now.
        
    Returns:
        Tuple of (week_start_date, week_end_date)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Get to midnight
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Go back to Monday (weekday() returns 0 for Monday)
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    
    # Sunday of the same week
    sunday = monday + timedelta(days=6)
    
    return monday.date(), sunday.date()


def get_or_create_weekly_league(
    db: Session,
    user_id: UUID,
    current_time: Optional[datetime] = None,
) -> UserLeague:
    """
    Get or create the user's league entry for the current week.
    
    Args:
        db: Database session
        user_id: User ID
        current_time: Current time (defaults to now UTC)
        
    Returns:
        UserLeague entry for the current week
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    week_start, week_end = get_week_start_end(current_time)
    
    # Try to find existing entry
    existing = db.execute(
        select(UserLeague).where(
            UserLeague.user_id == user_id,
            UserLeague.week_start == week_start,
        )
    ).scalar_one_or_none()
    
    if existing:
        return existing
    
    # Get user's current tier (from last week or default to bronze)
    last_week_start = week_start - timedelta(days=7)
    last_entry = db.execute(
        select(UserLeague)
        .where(UserLeague.user_id == user_id)
        .order_by(UserLeague.week_start.desc())
        .limit(1)
    ).scalar_one_or_none()
    
    # Determine starting tier
    if last_entry:
        # Continue from last week's tier (accounting for promotion/demotion)
        current_tier = last_entry.tier
        if last_entry.promoted and current_tier != LeagueTier.obsidian:
            # Move up one tier
            tier_index = TIER_ORDER.index(current_tier)
            current_tier = TIER_ORDER[min(tier_index + 1, len(TIER_ORDER) - 1)]
        elif last_entry.demoted and current_tier != LeagueTier.bronze:
            # Move down one tier
            tier_index = TIER_ORDER.index(current_tier)
            current_tier = TIER_ORDER[max(tier_index - 1, 0)]
    else:
        # New user starts in Bronze
        current_tier = LeagueTier.bronze
    
    # Create new entry for this week
    new_entry = UserLeague(
        user_id=user_id,
        tier=current_tier,
        weekly_xp=0,
        week_start=week_start,
        week_end=week_end,
        rank_in_tier=None,
        promoted=False,
        demoted=False,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    return new_entry


def add_xp_to_weekly_league(
    db: Session,
    user_id: UUID,
    xp_amount: int,
    current_time: Optional[datetime] = None,
) -> UserLeague:
    """
    Add XP to the user's weekly league entry.

    Args:
        db: Database session
        user_id: User ID
        xp_amount: Amount of XP to add
        current_time: Current time (defaults to now UTC)

    Returns:
        Updated UserLeague entry
    """
    # Get or create league entry for this week
    league_entry = get_or_create_weekly_league(db, user_id, current_time)

    # Add XP
    league_entry.weekly_xp += xp_amount
    db.commit()
    db.refresh(league_entry)

    return league_entry


def get_league_standings(
    db: Session,
    tier: LeagueTier,
    week_start: date,
    limit: Optional[int] = None,
) -> list[UserLeague]:
    """
    Get sorted league standings for a specific tier and week.

    Args:
        db: Database session
        tier: League tier
        week_start: Week start date
        limit: Optional limit on number of results

    Returns:
        List of UserLeague entries sorted by weekly_xp (descending)
    """
    query = (
        select(UserLeague)
        .where(
            UserLeague.tier == tier,
            UserLeague.week_start == week_start,
        )
        .order_by(desc(UserLeague.weekly_xp), UserLeague.created_at.asc())
    )

    if limit:
        query = query.limit(limit)

    results = db.execute(query).scalars().all()
    return list(results)


def get_user_league_rank(
    db: Session,
    user_id: UUID,
    week_start: date,
) -> Optional[int]:
    """
    Get the user's rank within their tier for the specified week.

    Args:
        db: Database session
        user_id: User ID
        week_start: Week start date

    Returns:
        Rank (1-based) or None if user not in league
    """
    # Get user's league entry
    user_entry = db.execute(
        select(UserLeague).where(
            UserLeague.user_id == user_id,
            UserLeague.week_start == week_start,
        )
    ).scalar_one_or_none()

    if not user_entry:
        return None

    # Count how many users have more XP in the same tier
    higher_count = db.execute(
        select(func.count())
        .select_from(UserLeague)
        .where(
            UserLeague.tier == user_entry.tier,
            UserLeague.week_start == week_start,
            UserLeague.weekly_xp > user_entry.weekly_xp,
        )
    ).scalar_one()

    # Rank is count + 1
    return higher_count + 1


def update_league_rankings(
    db: Session,
    tier: LeagueTier,
    week_start: date,
) -> None:
    """
    Update the rank_in_tier field for all users in a specific tier and week.

    Args:
        db: Database session
        tier: League tier
        week_start: Week start date
    """
    standings = get_league_standings(db, tier, week_start)

    for rank, entry in enumerate(standings, start=1):
        entry.rank_in_tier = rank

    db.commit()


def process_weekly_promotions(
    db: Session,
    week_start: date,
) -> dict[str, int]:
    """
    Process weekly promotions and demotions for all tiers.

    This should be run at the end of each week (e.g., Sunday night or Monday morning)
    to determine which users get promoted or demoted based on their performance.

    Args:
        db: Database session
        week_start: Week start date to process

    Returns:
        Dictionary with counts of promotions, demotions, and stays
    """
    promotions = 0
    demotions = 0
    stays = 0

    # Process each tier
    for tier in TIER_ORDER:
        # Update rankings first
        update_league_rankings(db, tier, week_start)

        # Get all standings for this tier
        standings = get_league_standings(db, tier, week_start)
        total_users = len(standings)

        if total_users == 0:
            continue

        # Determine promotion and demotion cutoffs
        for rank, entry in enumerate(standings, start=1):
            # Promotion logic (top performers, not already at max tier)
            if rank <= PROMOTION_THRESHOLD and tier != LeagueTier.obsidian:
                entry.promoted = True
                promotions += 1

            # Demotion logic (bottom performers, not in bronze tier)
            elif rank > (total_users - DEMOTION_THRESHOLD) and tier != LeagueTier.bronze:
                entry.demoted = True
                demotions += 1

            # Everyone else stays
            else:
                stays += 1

    db.commit()

    return {
        "promotions": promotions,
        "demotions": demotions,
        "stays": stays,
    }


def get_next_tier(current_tier: LeagueTier) -> Optional[LeagueTier]:
    """
    Get the next higher tier.

    Args:
        current_tier: Current league tier

    Returns:
        Next tier or None if already at max
    """
    try:
        tier_index = TIER_ORDER.index(current_tier)
        if tier_index < len(TIER_ORDER) - 1:
            return TIER_ORDER[tier_index + 1]
    except (ValueError, IndexError):
        pass
    return None


def get_previous_tier(current_tier: LeagueTier) -> Optional[LeagueTier]:
    """
    Get the previous lower tier.

    Args:
        current_tier: Current league tier

    Returns:
        Previous tier or None if already at min
    """
    try:
        tier_index = TIER_ORDER.index(current_tier)
        if tier_index > 0:
            return TIER_ORDER[tier_index - 1]
    except (ValueError, IndexError):
        pass
    return None


def get_league_summary(
    db: Session,
    user_id: UUID,
    current_time: Optional[datetime] = None,
) -> dict:
    """
    Get a summary of the user's current league status.

    Args:
        db: Database session
        user_id: User ID
        current_time: Current time (defaults to now UTC)

    Returns:
        Dictionary with league summary information
    """
    league_entry = get_or_create_weekly_league(db, user_id, current_time)

    # Get total users in tier
    total_in_tier = db.execute(
        select(func.count())
        .select_from(UserLeague)
        .where(
            UserLeague.tier == league_entry.tier,
            UserLeague.week_start == league_entry.week_start,
        )
    ).scalar_one()

    # Get user's rank
    rank = get_user_league_rank(db, user_id, league_entry.week_start)

    return {
        "current_tier": league_entry.tier,
        "weekly_xp": league_entry.weekly_xp,
        "rank_in_tier": rank,
        "total_in_tier": total_in_tier,
        "week_start": league_entry.week_start,
        "week_end": league_entry.week_end,
        "promotion_threshold": PROMOTION_THRESHOLD,
        "demotion_threshold": DEMOTION_THRESHOLD,
        "can_promote": league_entry.tier != LeagueTier.obsidian,
        "can_demote": league_entry.tier != LeagueTier.bronze,
    }

