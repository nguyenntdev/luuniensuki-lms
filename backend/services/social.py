"""
Social features service - friend list and follow system.

This module handles:
- Following/unfollowing users
- Friend requests (mutual follows)
- Listing followers and following
- Listing friends (mutual follows)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import FriendRequest, FriendRequestStatus, User, UserFollow, UserSession


def follow_user(db: Session, follower_id: UUID, following_id: UUID) -> UserFollow:
    """Follow a user."""
    if follower_id == following_id:
        raise ValueError("Cannot follow yourself")

    # Check if already following
    existing = db.execute(
        select(UserFollow).where(
            and_(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    follow = UserFollow(
        follower_id=follower_id,
        following_id=following_id,
    )
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


def unfollow_user(db: Session, follower_id: UUID, following_id: UUID) -> bool:
    """Unfollow a user. Returns True if unfollowed, False if not following."""
    result = db.execute(
        select(UserFollow).where(
            and_(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
    ).scalar_one_or_none()

    if not result:
        return False

    db.delete(result)
    db.commit()
    return True


def get_following(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[UserFollow], int]:
    """Get list of follow records that this user is following."""
    # Get total count
    total = db.execute(
        select(func.count())
        .select_from(UserFollow)
        .where(UserFollow.follower_id == user_id)
    ).scalar_one()

    # Get paginated results
    follows = (
        db.execute(
            select(UserFollow)
            .where(UserFollow.follower_id == user_id)
            .order_by(UserFollow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(UserFollow.following))
        )
        .scalars()
        .all()
    )

    return follows, total


def get_followers(
    db: Session, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[UserFollow], int]:
    """Get list of follow records for users following this user."""
    # Get total count
    total = db.execute(
        select(func.count())
        .select_from(UserFollow)
        .where(UserFollow.following_id == user_id)
    ).scalar_one()

    # Get paginated results
    follows = (
        db.execute(
            select(UserFollow)
            .where(UserFollow.following_id == user_id)
            .order_by(UserFollow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(UserFollow.follower))
        )
        .scalars()
        .all()
    )

    return follows, total


def is_following(db: Session, follower_id: UUID, following_id: UUID) -> bool:
    """Return True if follower_id is following following_id."""
    if follower_id is None:
        return False

    exists = db.execute(
        select(UserFollow.id).where(
            and_(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
    ).scalar_one_or_none()
    return exists is not None


def get_online_status_map(
    db: Session,
    user_ids: list[UUID],
    window_minutes: int = 5,
) -> dict[UUID, bool]:
    """Return a map of user_id -> online status based on recent sessions."""
    if not user_ids:
        return {}

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)

    rows = db.execute(
        select(UserSession.user_id)
        .where(
            UserSession.user_id.in_(user_ids),
            UserSession.is_active.is_(True),
            UserSession.last_active_at >= cutoff,
        )
        .distinct()
    ).all()
    online_ids = {row[0] for row in rows if row[0] is not None}

    return {user_id: user_id in online_ids for user_id in user_ids}


def get_friends(db: Session, user_id: UUID) -> list[User]:
    """Get list of friends (mutual follows)."""
    # Find users where both follow each other
    friends_subquery = (
        select(UserFollow.following_id)
        .where(UserFollow.follower_id == user_id)
        .subquery()
    )

    mutual_follows = (
        db.execute(
            select(User)
            .join(UserFollow, User.id == UserFollow.follower_id)
            .where(
                and_(
                    UserFollow.following_id == user_id,
                    UserFollow.follower_id.in_(select(friends_subquery)),
                )
            )
            .order_by(User.display_name)
        )
        .scalars()
        .all()
    )

    return mutual_follows


def create_friend_request(
    db: Session, from_user_id: UUID, to_user_id: UUID
) -> FriendRequest:
    """Create a friend request."""
    if from_user_id == to_user_id:
        raise ValueError("Cannot send friend request to yourself")

    # Check if request already exists
    existing = db.execute(
        select(FriendRequest).where(
            and_(
                FriendRequest.from_user_id == from_user_id,
                FriendRequest.to_user_id == to_user_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        if existing.status == FriendRequestStatus.pending:
            raise ValueError("Friend request already pending")
        elif existing.status == FriendRequestStatus.accepted:
            raise ValueError("Users are already friends")
        else:
            # Rejected - allow creating new request
            existing.status = FriendRequestStatus.pending
            existing.created_at = datetime.now(timezone.utc)
            existing.responded_at = None
            db.commit()
            db.refresh(existing)
            return existing

    # Create new request
    request = FriendRequest(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        status=FriendRequestStatus.pending,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_friend_requests(
    db: Session, user_id: UUID, status: Optional[str] = None
) -> list[FriendRequest]:
    """Get friend requests received by this user."""
    query = select(FriendRequest).where(FriendRequest.to_user_id == user_id)

    if status:
        query = query.where(FriendRequest.status == status)

    query = query.order_by(FriendRequest.created_at.desc()).options(
        selectinload(FriendRequest.from_user), selectinload(FriendRequest.to_user)
    )

    return db.execute(query).scalars().all()


def get_sent_friend_requests(
    db: Session, user_id: UUID, status: Optional[str] = None
) -> list[FriendRequest]:
    """Get friend requests sent by this user."""
    query = select(FriendRequest).where(FriendRequest.from_user_id == user_id)

    if status:
        query = query.where(FriendRequest.status == status)

    query = query.order_by(FriendRequest.created_at.desc()).options(
        selectinload(FriendRequest.from_user), selectinload(FriendRequest.to_user)
    )

    return db.execute(query).scalars().all()


def accept_friend_request(
    db: Session, request_id: UUID, user_id: UUID
) -> FriendRequest:
    """Accept a friend request."""
    request = db.execute(
        select(FriendRequest)
        .where(FriendRequest.id == request_id)
        .options(
            selectinload(FriendRequest.from_user), selectinload(FriendRequest.to_user)
        )
    ).scalar_one_or_none()

    if not request:
        raise ValueError("Friend request not found")

    if request.to_user_id != user_id:
        raise ValueError("Not authorized to accept this request")

    if request.status != FriendRequestStatus.pending:
        raise ValueError("Request is not pending")

    # Update request status
    request.status = FriendRequestStatus.accepted
    request.responded_at = datetime.now(timezone.utc)

    # Create mutual follows
    follow_user(db, request.from_user_id, request.to_user_id)
    follow_user(db, request.to_user_id, request.from_user_id)

    db.commit()
    db.refresh(request)
    return request


def reject_friend_request(
    db: Session, request_id: UUID, user_id: UUID
) -> FriendRequest:
    """Reject a friend request."""
    request = db.execute(
        select(FriendRequest)
        .where(FriendRequest.id == request_id)
        .options(
            selectinload(FriendRequest.from_user), selectinload(FriendRequest.to_user)
        )
    ).scalar_one_or_none()

    if not request:
        raise ValueError("Friend request not found")

    if request.to_user_id != user_id:
        raise ValueError("Not authorized to reject this request")

    if request.status != FriendRequestStatus.pending:
        raise ValueError("Request is not pending")

    # Update request status
    request.status = FriendRequestStatus.rejected
    request.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)
    return request
