"""
Weekly Quest Service.

Handles auto-assignment of recurring weekly quests to users.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import User, UserWeeklyQuest, WeeklyQuest


def get_week_start_date(dt: Optional[datetime] = None) -> datetime:
    """
    Get the Monday (start) of the week for the given datetime.
    
    Args:
        dt: Datetime to get week start for. Defaults to now.
        
    Returns:
        Datetime representing Monday at 00:00:00 of the week.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Get to midnight
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Go back to Monday (weekday() returns 0 for Monday)
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    
    # Return as naive datetime for database storage
    return monday.replace(tzinfo=None)


def get_week_end_date(week_start: datetime) -> datetime:
    """
    Get the Sunday (end) of the week for the given week start.
    
    Args:
        week_start: Monday of the week.
        
    Returns:
        Datetime representing Sunday at 23:59:59 of the week.
    """
    sunday = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return sunday


def ensure_weekly_quests_for_user(
    db: Session,
    user_id: UUID,
    current_time: Optional[datetime] = None,
) -> list[UserWeeklyQuest]:
    """
    Ensure user has all active recurring weekly quests assigned for the current week.
    
    This function should be called:
    - When a user logs in
    - When weekly quest endpoints are accessed
    - Via a scheduled job at the start of each week
    
    Args:
        db: Database session
        user_id: User ID to assign quests to
        current_time: Current time (defaults to now UTC)
        
    Returns:
        List of UserWeeklyQuest records for the current week
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    week_start = get_week_start_date(current_time)
    
    # Get all active recurring weekly quests
    active_quests = db.execute(
        select(WeeklyQuest).where(
            WeeklyQuest.is_active == True,  # noqa: E712
            WeeklyQuest.is_recurring == True,  # noqa: E712
        )
    ).scalars().all()
    
    # Check which quests user already has for this week
    existing_user_quests = db.execute(
        select(UserWeeklyQuest).where(
            UserWeeklyQuest.user_id == user_id,
            UserWeeklyQuest.week_start_date == week_start,
        )
    ).scalars().all()
    
    existing_quest_ids = {uq.quest_id for uq in existing_user_quests}
    
    # Create missing quest assignments
    new_user_quests = []
    for quest in active_quests:
        if quest.id not in existing_quest_ids:
            user_quest = UserWeeklyQuest(
                user_id=user_id,
                quest_id=quest.id,
                week_start_date=week_start,
                current_count=0,
                is_completed=False,
                xp_awarded=0,
            )
            db.add(user_quest)
            new_user_quests.append(user_quest)
    
    if new_user_quests:
        db.flush()
    
    return existing_user_quests + new_user_quests


def assign_weekly_quests_to_all_users(db: Session) -> int:
    """
    Assign active recurring weekly quests to all users for the current week.
    
    This is typically called by a scheduled job at the start of each week.
    
    Args:
        db: Database session
        
    Returns:
        Number of quest assignments created
    """
    current_time = datetime.now(timezone.utc)
    
    # Get all users
    users = db.execute(select(User.id)).scalars().all()
    
    total_assigned = 0
    for user_id in users:
        user_quests = ensure_weekly_quests_for_user(db, user_id, current_time)
        # Count newly created quests
        new_count = len([uq for uq in user_quests if uq.id is None])
        total_assigned += new_count
    
    db.commit()
    return total_assigned

