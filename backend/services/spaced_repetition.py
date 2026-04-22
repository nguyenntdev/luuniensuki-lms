"""
Spaced Repetition Service for motif review using the SM-2 algorithm.

This service implements the SuperMemo-2 (SM-2) algorithm for spaced repetition learning:
- Calculates optimal review intervals based on user performance
- Manages ease factors and review schedules
- Tracks review history for analytics
- Provides due cards and statistics

SM-2 Algorithm:
- Quality rating: 0-5 (0=complete blackout, 5=perfect recall)
- Quality >= 3 is considered a successful review
- Ease factor adjusts based on quality (min 1.3)
- Intervals increase exponentially for successful reviews
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import Motif, SpacedRepetitionCard, User


# SM-2 algorithm constants
MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5
INITIAL_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6


def calculate_sm2_parameters(
    quality: int,
    current_ease: float,
    current_interval: int,
    current_repetitions: int,
) -> tuple[float, int, int]:
    """
    Calculate SM-2 parameters for the next review.
    
    Args:
        quality: Quality rating (0-5)
        current_ease: Current ease factor
        current_interval: Current interval in days
        current_repetitions: Current repetition count
        
    Returns:
        Tuple of (new_ease_factor, new_interval_days, new_repetitions)
    """
    # Calculate new ease factor
    new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(new_ease, MIN_EASE_FACTOR)
    
    # Calculate new interval and repetitions
    if quality < 3:
        # Failed review - reset to start
        new_interval = INITIAL_INTERVAL_DAYS
        new_repetitions = 0
    else:
        # Successful review
        new_repetitions = current_repetitions + 1
        
        if new_repetitions == 1:
            new_interval = INITIAL_INTERVAL_DAYS
        elif new_repetitions == 2:
            new_interval = SECOND_INTERVAL_DAYS
        else:
            new_interval = int(current_interval * new_ease)
    
    return new_ease, new_interval, new_repetitions


def get_due_cards(
    db: Session,
    user_id: UUID,
    limit: Optional[int] = None,
    now: Optional[datetime] = None,
) -> list[SpacedRepetitionCard]:
    """
    Get cards due for review.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of cards to return
        now: Current datetime (defaults to now)
        
    Returns:
        List of due cards ordered by next_review_at
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    query = (
        select(SpacedRepetitionCard)
        .where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.next_review_at <= now,
        )
        .options(selectinload(SpacedRepetitionCard.motif))
        .order_by(SpacedRepetitionCard.next_review_at)
    )
    
    if limit:
        query = query.limit(limit)
    
    result = db.execute(query)
    return list(result.scalars().all())


def process_review(
    db: Session,
    card_id: UUID,
    quality: int,
    now: Optional[datetime] = None,
) -> SpacedRepetitionCard:
    """
    Process a review result and update the card.
    
    Args:
        db: Database session
        card_id: Card ID to review
        quality: Quality rating (0-5)
        now: Current datetime (defaults to now)
        
    Returns:
        Updated card
        
    Raises:
        ValueError: If card not found or quality is invalid
    """
    if not (0 <= quality <= 5):
        raise ValueError("Quality must be between 0 and 5")
    
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Get the card
    card = db.get(SpacedRepetitionCard, card_id)
    if not card:
        raise ValueError("Card not found")
    
    # Calculate new parameters
    new_ease, new_interval, new_repetitions = calculate_sm2_parameters(
        quality=quality,
        current_ease=card.ease_factor,
        current_interval=card.interval_days,
        current_repetitions=card.repetitions,
    )

    # Update card
    card.ease_factor = new_ease
    card.interval_days = new_interval
    card.repetitions = new_repetitions
    card.last_reviewed_at = now
    card.next_review_at = now + timedelta(days=new_interval)

    # Add to review history
    history_entry = {
        "quality": quality,
        "reviewed_at": now.isoformat(),
        "ease_factor": new_ease,
        "interval_days": new_interval,
        "repetitions": new_repetitions,
    }

    if card.review_history is None:
        card.review_history = []

    card.review_history = list(card.review_history) + [history_entry]

    db.commit()
    db.refresh(card)

    return card


def add_card_to_deck(
    db: Session,
    user_id: UUID,
    motif_id: UUID,
    now: Optional[datetime] = None,
) -> SpacedRepetitionCard:
    """
    Add a motif to the user's review deck.

    Args:
        db: Database session
        user_id: User ID
        motif_id: Motif ID to add
        now: Current datetime (defaults to now)

    Returns:
        Created or existing card
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Check if card already exists
    existing = db.execute(
        select(SpacedRepetitionCard).where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.motif_id == motif_id,
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    # Verify motif exists
    motif = db.get(Motif, motif_id)
    if not motif:
        raise ValueError("Motif not found")

    # Create new card
    card = SpacedRepetitionCard(
        user_id=user_id,
        motif_id=motif_id,
        ease_factor=DEFAULT_EASE_FACTOR,
        interval_days=0,
        repetitions=0,
        next_review_at=now,  # Available for immediate review
        review_history=[],
    )

    db.add(card)
    db.commit()
    db.refresh(card)

    return card


def get_user_review_stats(
    db: Session,
    user_id: UUID,
    now: Optional[datetime] = None,
) -> dict:
    """
    Get user's review statistics.

    Args:
        db: Database session
        user_id: User ID
        now: Current datetime (defaults to now)

    Returns:
        Dictionary with review statistics
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Total cards
    total_cards = db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(
            SpacedRepetitionCard.user_id == user_id
        )
    ).scalar_one()

    # Due cards
    due_cards = db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.next_review_at <= now,
        )
    ).scalar_one()

    # Cards reviewed today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    reviewed_today = db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.last_reviewed_at >= today_start,
        )
    ).scalar_one()

    # Mastered cards (repetitions >= 3 with ease >= 2.5)
    mastered_cards = db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.repetitions >= 3,
            SpacedRepetitionCard.ease_factor >= 2.5,
        )
    ).scalar_one()

    # Learning cards (repetitions < 3)
    learning_cards = db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(
            SpacedRepetitionCard.user_id == user_id,
            SpacedRepetitionCard.repetitions < 3,
        )
    ).scalar_one()

    # Get total reviews from history
    cards_with_history = db.execute(
        select(SpacedRepetitionCard).where(
            SpacedRepetitionCard.user_id == user_id
        )
    ).scalars().all()

    total_reviews = sum(
        len(card.review_history or []) for card in cards_with_history
    )

    return {
        "total_cards": total_cards,
        "due_cards": due_cards,
        "reviewed_today": reviewed_today,
        "mastered_cards": mastered_cards,
        "learning_cards": learning_cards,
        "total_reviews": total_reviews,
    }

