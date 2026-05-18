"""
Leaderboard service - manage leaderboard data and user settings.

This module handles:
- Global leaderboard (all users)
- Friend leaderboard (mutual follows only)
- Class leaderboard (classroom members)
- User leaderboard settings
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..models import User, UserFollow, UserLeaderboardSettings, UserRole


def get_or_create_leaderboard_settings(
    db: Session, user_id: UUID
) -> UserLeaderboardSettings:
    """Get or create user leaderboard settings."""
    settings = db.execute(
        select(UserLeaderboardSettings).where(
            UserLeaderboardSettings.user_id == user_id
        )
    ).scalar_one_or_none()
    
    if not settings:
        settings = UserLeaderboardSettings(
            user_id=user_id,
            show_on_global=True,
            show_real_name=False,
            preferred_leaderboard="global",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


def update_leaderboard_settings(
    db: Session,
    user_id: UUID,
    show_on_global: Optional[bool] = None,
    show_real_name: Optional[bool] = None,
    preferred_leaderboard: Optional[str] = None,
) -> UserLeaderboardSettings:
    """Update user leaderboard settings."""
    settings = get_or_create_leaderboard_settings(db, user_id)
    
    if show_on_global is not None:
        settings.show_on_global = show_on_global
    if show_real_name is not None:
        settings.show_real_name = show_real_name
    if preferred_leaderboard is not None:
        settings.preferred_leaderboard = preferred_leaderboard
    
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


def get_global_leaderboard(
    db: Session,
    current_user_id: Optional[UUID] = None,
    limit: int = 50,
    order_by: str = "xp",
) -> tuple[list[dict], Optional[int], int]:
    """
    Get global leaderboard.

    Args:
        db: Database session
        current_user_id: Current user ID to find their rank
        limit: Maximum number of entries to return
        order_by: Metric to sort by ('xp', 'streak')

    Returns:
        Tuple of (entries, user_rank, total_users)
    """
    # Get all users with leaderboard settings
    settings_map = {}
    all_settings = db.execute(select(UserLeaderboardSettings)).scalars().all()
    for s in all_settings:
        settings_map[s.user_id] = s

    # Build base query - include all users (guest excluded as they have no XP)
    base_query = select(User).where(User.role != UserRole.guest)

    # Apply ordering
    if order_by == "streak":
        base_query = base_query.order_by(
            User.current_streak.desc(),
            User.total_xp.desc(),
            User.created_at.asc()
        )
    else:  # default to xp
        base_query = base_query.order_by(
            User.total_xp.desc(),
            User.created_at.asc()
        )

    # Get all users
    all_users = db.execute(base_query).scalars().all()

    # Filter by visibility settings (show_on_global)
    visible_users = []
    for user in all_users:
        settings = settings_map.get(user.id)
        # Default to visible if no settings
        if settings is None or settings.show_on_global:
            visible_users.append(user)

    total_users = len(visible_users)

    # Build entries
    entries = []
    user_rank = None
    for rank, user in enumerate(visible_users[:limit], start=1):
        entries.append({
            "rank": rank,
            "user_id": user.id,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "total_xp": user.total_xp,
            "current_streak": user.current_streak,
        })
        if current_user_id and user.id == current_user_id:
            user_rank = rank

    # If user not in top results, find their rank
    if current_user_id and user_rank is None:
        for rank, user in enumerate(visible_users, start=1):
            if user.id == current_user_id:
                user_rank = rank
                break

    return entries, user_rank, total_users


def get_friends_leaderboard(
    db: Session,
    user_id: UUID,
    limit: int = 50,
    order_by: str = "xp",
) -> tuple[list[dict], Optional[int], int]:
    """
    Get leaderboard of user's friends (mutual follows).

    Args:
        db: Database session
        user_id: Current user ID
        limit: Maximum number of entries to return
        order_by: Metric to sort by ('xp', 'streak')

    Returns:
        Tuple of (entries, user_rank, total_users)
    """
    # Find mutual follows (friends)
    friends_subquery = (
        select(UserFollow.following_id)
        .where(UserFollow.follower_id == user_id)
        .subquery()
    )

    mutual_follows_query = (
        select(User)
        .join(UserFollow, User.id == UserFollow.follower_id)
        .where(
            and_(
                UserFollow.following_id == user_id,
                UserFollow.follower_id.in_(select(friends_subquery))
            )
        )
    )

    # Add current user to the list
    current_user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not current_user:
        return [], None, 0

    # Get all friends
    friends = db.execute(mutual_follows_query).scalars().all()
    all_users = [current_user] + list(friends)

    # Sort by requested metric
    if order_by == "streak":
        all_users.sort(
            key=lambda u: (u.current_streak, u.total_xp, -u.created_at.timestamp()),
            reverse=True
        )
    else:  # default to xp
        all_users.sort(
            key=lambda u: (u.total_xp, -u.created_at.timestamp()),
            reverse=True
        )

    total_users = len(all_users)

    # Build entries and find user rank
    entries = []
    user_rank = None
    for rank, user in enumerate(all_users[:limit], start=1):
        entries.append({
            "rank": rank,
            "user_id": user.id,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "total_xp": user.total_xp,
            "current_streak": user.current_streak,
        })
        if user.id == user_id:
            user_rank = rank

    # If user not in limited results, find their rank
    if user_rank is None:
        for rank, user in enumerate(all_users, start=1):
            if user.id == user_id:
                user_rank = rank
                break

    return entries, user_rank, total_users

