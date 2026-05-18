"""
Hearts Service for managing user hearts/energy system.

This service handles:
- Heart deduction on wrong quiz answers
- Heart refilling (automatic, purchase, ad watch, rewards)
- Streak freeze usage for heart restoration
- Heart transaction logging
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..models import User, UserHearts, HeartTransaction, HeartTransactionReason

# Hearts configuration
MAX_HEARTS = 5
HEARTS_REFILL_INTERVAL_MINUTES = 240  # 4 hours per heart
STREAK_FREEZE_HEARTS_RESTORE = 5  # Restore all hearts when using streak freeze


def get_or_create_user_hearts(db: Session, user: User) -> UserHearts:
    """
    Get or create UserHearts record for a user.

    Args:
        db: Database session
        user: The user

    Returns:
        UserHearts instance
    """
    user_hearts = db.execute(
        select(UserHearts).where(UserHearts.user_id == user.id)
    ).scalar_one_or_none()

    if user_hearts is None:
        user_hearts = UserHearts(
            user_id=user.id,
            current_hearts=MAX_HEARTS,
            max_hearts=MAX_HEARTS,
            streak_freezes=user.streak_freezes,
        )
        db.add(user_hearts)
        db.commit()
        db.refresh(user_hearts)

    return user_hearts


def calculate_refill_hearts(user_hearts: UserHearts, now: datetime) -> int:
    """
    Calculate how many hearts should be refilled based on time passed.

    Args:
        user_hearts: UserHearts instance
        now: Current datetime

    Returns:
        Number of hearts to refill
    """
    # If hearts are full or unlimited, no refill needed
    if user_hearts.current_hearts >= user_hearts.max_hearts:
        return 0

    if user_hearts.unlimited_until and now < user_hearts.unlimited_until:
        return 0

    # If no hearts lost yet, no refill
    if user_hearts.last_heart_lost_at is None:
        return 0

    # Calculate time passed since last heart lost
    time_passed = now - user_hearts.last_heart_lost_at
    minutes_passed = time_passed.total_seconds() / 60

    # Calculate how many hearts should be refilled
    hearts_to_refill = int(minutes_passed // HEARTS_REFILL_INTERVAL_MINUTES)

    # Don't exceed max hearts
    max_refillable = user_hearts.max_hearts - user_hearts.current_hearts
    return min(hearts_to_refill, max_refillable)


def auto_refill_hearts(db: Session, user_hearts: UserHearts, now: datetime) -> int:
    """
    Automatically refill hearts based on time passed.

    Args:
        db: Database session
        user_hearts: UserHearts instance
        now: Current datetime

    Returns:
        Number of hearts refilled
    """
    hearts_to_refill = calculate_refill_hearts(user_hearts, now)

    if hearts_to_refill > 0:
        user_hearts.current_hearts += hearts_to_refill
        user_hearts.updated_at = now

        # If hearts are now full, clear the refill timer
        if user_hearts.current_hearts >= user_hearts.max_hearts:
            user_hearts.hearts_refill_at = None
        else:
            # Calculate next refill time
            user_hearts.hearts_refill_at = now + timedelta(
                minutes=HEARTS_REFILL_INTERVAL_MINUTES
            )

        # Log the refill transaction
        transaction = HeartTransaction(
            user_id=user_hearts.user_id,
            user_hearts_id=user_hearts.id,
            amount=hearts_to_refill,
            reason=HeartTransactionReason.daily_refill,
            balance_after=user_hearts.current_hearts,
        )
        db.add(transaction)
        db.commit()
        db.refresh(user_hearts)

    return hearts_to_refill


def calculate_time_until_refill(user_hearts: UserHearts, now: datetime) -> Optional[int]:
    """
    Calculate seconds until next heart refill.

    Args:
        user_hearts: UserHearts instance
        now: Current datetime

    Returns:
        Seconds until next refill, or None if hearts are full
    """
    if user_hearts.current_hearts >= user_hearts.max_hearts:
        return None

    if user_hearts.unlimited_until and now < user_hearts.unlimited_until:
        return None

    if user_hearts.last_heart_lost_at is None:
        return None

    # Calculate next refill time
    next_refill = user_hearts.last_heart_lost_at + timedelta(
        minutes=HEARTS_REFILL_INTERVAL_MINUTES * (
            (user_hearts.max_hearts - user_hearts.current_hearts)
        )
    )

    if now >= next_refill:
        return 0

    return int((next_refill - now).total_seconds())


def has_hearts(db: Session, user: User, now: datetime) -> bool:
    """
    Check if user has hearts available.

    Args:
        db: Database session
        user: The user
        now: Current datetime

    Returns:
        True if user has hearts, False otherwise
    """
    user_hearts = get_or_create_user_hearts(db, user)

    # Auto-refill hearts if applicable
    auto_refill_hearts(db, user_hearts, now)

    # Check if unlimited
    if user_hearts.unlimited_until and now < user_hearts.unlimited_until:
        return True

    return user_hearts.current_hearts > 0


def use_heart(
    db: Session,
    user: User,
    now: datetime,
    reason: HeartTransactionReason = HeartTransactionReason.quiz_wrong,
    metadata: Optional[dict] = None
) -> tuple[bool, UserHearts]:
    """
    Use a heart (deduct one heart).

    Args:
        db: Database session
        user: The user
        now: Current datetime
        reason: Reason for using the heart
        metadata: Additional context

    Returns:
        Tuple of (success, user_hearts)
    """
    user_hearts = get_or_create_user_hearts(db, user)

    # Auto-refill hearts first
    auto_refill_hearts(db, user_hearts, now)

    # Check if unlimited
    if user_hearts.unlimited_until and now < user_hearts.unlimited_until:
        return True, user_hearts

    # Check if has hearts
    if user_hearts.current_hearts <= 0:
        return False, user_hearts

    # Deduct heart
    user_hearts.current_hearts -= 1
    user_hearts.last_heart_lost_at = now
    user_hearts.updated_at = now

    # Set refill time
    if user_hearts.current_hearts < user_hearts.max_hearts:
        user_hearts.hearts_refill_at = now + timedelta(
            minutes=HEARTS_REFILL_INTERVAL_MINUTES
        )

    # Log transaction
    transaction = HeartTransaction(
        user_id=user.id,
        user_hearts_id=user_hearts.id,
        amount=-1,
        reason=reason,
        balance_after=user_hearts.current_hearts,
        metadata_json=metadata,
    )
    db.add(transaction)
    db.commit()
    db.refresh(user_hearts)

    return True, user_hearts


def refill_hearts(
    db: Session,
    user: User,
    now: datetime,
    amount: Optional[int] = None,
    reason: HeartTransactionReason = HeartTransactionReason.heart_purchase,
    metadata: Optional[dict] = None
) -> tuple[int, UserHearts]:
    """
    Refill hearts (add hearts back).

    Args:
        db: Database session
        user: The user
        now: Current datetime
        amount: Number of hearts to add (None = refill to max)
        reason: Reason for refilling
        metadata: Additional context

    Returns:
        Tuple of (hearts_added, user_hearts)
    """
    user_hearts = get_or_create_user_hearts(db, user)

    # Calculate amount to add
    if amount is None:
        hearts_to_add = user_hearts.max_hearts - user_hearts.current_hearts
    else:
        hearts_to_add = min(amount, user_hearts.max_hearts - user_hearts.current_hearts)

    if hearts_to_add <= 0:
        return 0, user_hearts

    # Add hearts
    user_hearts.current_hearts += hearts_to_add
    user_hearts.updated_at = now

    # Clear refill timer if hearts are full
    if user_hearts.current_hearts >= user_hearts.max_hearts:
        user_hearts.hearts_refill_at = None

    # Log transaction
    transaction = HeartTransaction(
        user_id=user.id,
        user_hearts_id=user_hearts.id,
        amount=hearts_to_add,
        reason=reason,
        balance_after=user_hearts.current_hearts,
        metadata_json=metadata,
    )
    db.add(transaction)
    db.commit()
    db.refresh(user_hearts)

    return hearts_to_add, user_hearts


def use_streak_freeze_for_hearts(
    db: Session,
    user: User,
    now: datetime
) -> tuple[bool, UserHearts]:
    """
    Use a streak freeze to restore all hearts.

    Args:
        db: Database session
        user: The user
        now: Current datetime

    Returns:
        Tuple of (success, user_hearts)
    """
    user_hearts = get_or_create_user_hearts(db, user)

    # Check if user has streak freezes
    if user.streak_freezes <= 0:
        return False, user_hearts

    # Deduct streak freeze from user
    user.streak_freezes -= 1

    # Restore all hearts
    hearts_added = user_hearts.max_hearts - user_hearts.current_hearts
    user_hearts.current_hearts = user_hearts.max_hearts
    user_hearts.hearts_refill_at = None
    user_hearts.streak_freezes = user.streak_freezes
    user_hearts.updated_at = now

    # Log transaction
    transaction = HeartTransaction(
        user_id=user.id,
        user_hearts_id=user_hearts.id,
        amount=hearts_added,
        reason=HeartTransactionReason.streak_freeze_used,
        balance_after=user_hearts.current_hearts,
        metadata_json={"streak_freezes_remaining": user.streak_freezes},
    )
    db.add(transaction)
    db.commit()
    db.refresh(user_hearts)

    return True, user_hearts


def get_heart_transactions(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20
) -> tuple[list[HeartTransaction], int]:
    """
    Get heart transaction history for a user.

    Args:
        db: Database session
        user: The user
        page: Page number (1-indexed)
        page_size: Number of transactions per page

    Returns:
        Tuple of (transactions, total_count)
    """
    # Get total count
    total = db.execute(
        select(func.count(HeartTransaction.id)).where(
            HeartTransaction.user_id == user.id
        )
    ).scalar() or 0

    # Get paginated transactions
    offset = (page - 1) * page_size
    transactions = db.execute(
        select(HeartTransaction)
        .where(HeartTransaction.user_id == user.id)
        .order_by(HeartTransaction.created_at.desc())
        .limit(page_size)
        .offset(offset)
    ).scalars().all()

    return list(transactions), total


def set_unlimited_hearts(
    db: Session,
    user: User,
    until: datetime,
    now: datetime
) -> UserHearts:
    """
    Set unlimited hearts for a user until a specific time.

    Args:
        db: Database session
        user: The user
        until: When unlimited hearts expire
        now: Current datetime

    Returns:
        UserHearts instance
    """
    user_hearts = get_or_create_user_hearts(db, user)

    user_hearts.unlimited_until = until
    user_hearts.updated_at = now

    db.commit()
    db.refresh(user_hearts)

    return user_hearts
