"""
Sharing service for social features.

This module handles:
- Creating shares
- Generating shareable links
- Tracking views
- Building activity feeds
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from ..models import Badge, Certificate, User, UserBadge, UserFollow, UserShare


def generate_share_url(
    share_id: UUID, base_url: str = "https://lms.luuniensuki.com"
) -> str:
    """
    Generate a shareable URL for a share.

    Args:
        share_id: UUID of the share
        base_url: Base URL of the application

    Returns:
        Shareable URL
    """
    return f"{base_url}/share/{share_id}"


def _is_following(db: Session, follower_id: Optional[UUID], following_id: UUID) -> bool:
    if not follower_id:
        return False

    return (
        db.query(UserFollow.id)
        .filter(
            and_(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
        .first()
        is not None
    )


def create_share(
    db: Session,
    user_id: UUID,
    share_type: str,
    content_id: Optional[UUID],
    caption: Optional[str],
    visibility: str,
) -> UserShare:
    """
    Create a new share.

    Args:
        db: Database session
        user_id: ID of the user creating the share
        share_type: Type of content being shared
        content_id: ID of the shared item (optional)
        caption: User's custom message (optional)
        visibility: Who can view this share

    Returns:
        Created UserShare instance
    """
    share = UserShare(
        user_id=user_id,
        share_type=share_type,
        content_id=content_id,
        caption=caption,
        visibility=visibility,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    # Generate shareable URL
    share.share_url = generate_share_url(share.id)
    db.commit()
    db.refresh(share)

    return share


def get_share_by_id(
    db: Session, share_id: UUID, current_user_id: Optional[UUID] = None
) -> Optional[UserShare]:
    """
    Get a share by ID with visibility check.

    Args:
        db: Database session
        share_id: ID of the share
        current_user_id: ID of the current user (optional, for visibility check)

    Returns:
        UserShare instance or None
    """
    share = db.query(UserShare).filter(UserShare.id == share_id).first()

    if not share:
        return None

    # Check visibility
    if share.visibility == "private" and share.user_id != current_user_id:
        return None

    if share.visibility == "followers":
        if share.user_id != current_user_id and not _is_following(
            db, current_user_id, share.user_id
        ):
            return None

    return share


def increment_view_count(db: Session, share_id: UUID) -> None:
    """
    Increment view count for a share.

    Args:
        db: Database session
        share_id: ID of the share
    """
    share = db.query(UserShare).filter(UserShare.id == share_id).first()
    if share:
        share.view_count += 1
        db.commit()


def get_user_shares(
    db: Session, user_id: UUID, page: int = 1, page_size: int = 20
) -> tuple[list[UserShare], int]:
    """
    Get shares by a specific user.

    Args:
        db: Database session
        user_id: ID of the user
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (list of shares, total count)
    """
    query = db.query(UserShare).filter(UserShare.user_id == user_id)
    total = query.count()

    shares = (
        query.order_by(desc(UserShare.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return shares, total


def get_activity_feed(
    db: Session, current_user_id: UUID, page: int = 1, page_size: int = 20
) -> tuple[list[UserShare], int]:
    """
    Get activity feed from followed users (public shares for now).

    Returns shares from users the current user follows.

    Args:
        db: Database session
        current_user_id: ID of the current user
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (list of shares, total count)
    """
    following_ids = (
        db.query(UserFollow.following_id)
        .filter(UserFollow.follower_id == current_user_id)
        .subquery()
    )
    query = db.query(UserShare).filter(
        and_(
            UserShare.user_id.in_(select(following_ids)),
            UserShare.user_id != current_user_id,
            UserShare.visibility.in_(["public", "followers"]),
        )
    )

    total = query.count()
    shares = (
        query.order_by(desc(UserShare.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return shares, total


def get_public_user_activity(
    db: Session, user_id: UUID, page: int = 1, page_size: int = 20
) -> tuple[list[UserShare], int]:
    """
    Get public activity for a specific user.

    Args:
        db: Database session
        user_id: ID of the user
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (list of shares, total count)
    """
    query = db.query(UserShare).filter(
        and_(UserShare.user_id == user_id, UserShare.visibility == "public")
    )

    total = query.count()
    shares = (
        query.order_by(desc(UserShare.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return shares, total


def delete_share(db: Session, share_id: UUID, user_id: UUID) -> bool:
    """
    Delete a share (user can only delete their own shares).

    Args:
        db: Database session
        share_id: ID of the share
        user_id: ID of the user attempting deletion

    Returns:
        True if deleted, False if not found or not authorized
    """
    share = (
        db.query(UserShare)
        .filter(and_(UserShare.id == share_id, UserShare.user_id == user_id))
        .first()
    )

    if not share:
        return False

    db.delete(share)
    db.commit()
    return True


def get_content_data_for_share(
    db: Session, share: UserShare
) -> Optional[dict[str, Any]]:
    """
    Get the content data for a share (badge info, certificate info, etc.).

    Args:
        db: Database session
        share: UserShare instance

    Returns:
        Dictionary with content data or None
    """
    if share.share_type == "badge" and share.content_id:
        # Get badge info
        user_badge = (
            db.query(UserBadge)
            .filter(
                and_(
                    UserBadge.user_id == share.user_id,
                    UserBadge.badge_id == share.content_id,
                )
            )
            .first()
        )

        if user_badge and user_badge.badge:
            return {
                "badge_name": user_badge.badge.name,
                "badge_slug": user_badge.badge.slug,
                "badge_icon_url": user_badge.badge.icon_url,
                "badge_description": user_badge.badge.description,
                "earned_at": user_badge.earned_at.isoformat()
                if user_badge.earned_at
                else None,
            }

    elif share.share_type == "certificate" and share.content_id:
        # Get certificate info
        certificate = (
            db.query(Certificate).filter(Certificate.id == share.content_id).first()
        )

        if certificate:
            return {
                "certificate_code": certificate.code,
                "issuer_name": certificate.issuer_name,
                "issued_at": certificate.issued_at.isoformat()
                if certificate.issued_at
                else None,
                "reason_type": certificate.reason_type,
            }

    elif share.share_type == "streak":
        # Get current user streak
        user = db.query(User).filter(User.id == share.user_id).first()
        if user:
            from .streak import get_user_streak

            streak = get_user_streak(db, share.user_id)
            return {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
            }

    elif share.share_type == "level_up":
        # Get user level info
        user = db.query(User).filter(User.id == share.user_id).first()
        if user:
            from ..config import XP_RANKS

            rank_info = next(
                (
                    r
                    for r in XP_RANKS
                    if user.total_xp >= r["min_xp"]
                    and (r["max_xp"] is None or user.total_xp <= r["max_xp"])
                ),
                None,
            )
            return {
                "total_xp": user.total_xp,
                "rank_title": rank_info["title"] if rank_info else "Người mới",
                "rank_min_xp": rank_info["min_xp"] if rank_info else 0,
            }

    return None
