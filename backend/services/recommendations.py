"""
Recommendation Service for Luuniensuki LMS.

This module provides personalized content recommendations using:
- Collaborative filtering (users who liked X also liked Y)
- Content-based filtering (similar content based on tags)
- User browsing history and patterns
- Skill levels and learning goals
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    ContentTag,
    InteractionType,
    LessonContent,
    Motif,
    Quest,
    Tag,
    UnlockStatus,
    User,
    UserContentInteraction,
    UserProgress,
)


class RecommendationType:
    """Recommendation type constants."""
    CONTINUE_LEARNING = "continue_learning"  # Lessons to continue
    DISCOVER_NEW = "discover_new"  # New content based on interests
    REVIEW_NEEDED = "review_needed"  # Content needing review
    POPULAR = "popular"  # Trending content


def get_personalized_recommendations(
    db: Session,
    user: User,
    limit: int = 10,
    recommendation_type: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get personalized recommendations for a user.

    Args:
        db: Database session
        user: User object
        limit: Maximum number of recommendations per type
        recommendation_type: Optional filter for specific recommendation type

    Returns:
        Dictionary with recommendation types as keys and list of content as values
    """
    recommendations = {}

    if not recommendation_type or recommendation_type == RecommendationType.CONTINUE_LEARNING:
        recommendations[RecommendationType.CONTINUE_LEARNING] = _get_continue_learning(
            db, user, limit
        )

    if not recommendation_type or recommendation_type == RecommendationType.DISCOVER_NEW:
        recommendations[RecommendationType.DISCOVER_NEW] = _get_discover_new(
            db, user, limit
        )

    if not recommendation_type or recommendation_type == RecommendationType.REVIEW_NEEDED:
        recommendations[RecommendationType.REVIEW_NEEDED] = _get_review_needed(
            db, user, limit
        )

    if not recommendation_type or recommendation_type == RecommendationType.POPULAR:
        recommendations[RecommendationType.POPULAR] = _get_popular_content(
            db, user, limit
        )

    return recommendations


def _get_continue_learning(
    db: Session, user: User, limit: int
) -> List[Dict[str, Any]]:
    """Get lessons that user started but hasn't completed."""
    # Find motifs that are discovered or learned but not mastered
    progress_entries = db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.motif).selectinload(Motif.lesson))
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status.in_([UnlockStatus.discovered, UnlockStatus.learned]),
        )
        .order_by(UserProgress.updated_at.desc())
        .limit(limit)
    ).scalars().all()

    results = []
    for progress in progress_entries:
        if progress.motif and progress.motif.lesson:
            results.append({
                "content_type": "lesson",
                "content_id": str(progress.motif.lesson.id),
                "motif_id": str(progress.motif.id),
                "title": progress.motif.name,  # Use motif name instead of lesson.title
                "description": progress.motif.lesson.description,
                "status": progress.status.value,
                "reason": "continue_learning",
                "score": 1.0,  # Highest priority
            })

    return results


def _get_discover_new(
    db: Session, user: User, limit: int
) -> List[Dict[str, Any]]:
    """Get new content based on user's interests and browsing history."""
    # Get user's interaction history to understand preferences
    user_interactions = db.execute(
        select(UserContentInteraction)
        .where(UserContentInteraction.user_id == user.id)
        .order_by(UserContentInteraction.created_at.desc())
        .limit(50)
    ).scalars().all()

    # Get content IDs user has already interacted with
    interacted_content_ids = {
        interaction.content_id for interaction in user_interactions
    }

    # Get tags from user's completed/liked content
    user_tag_ids = set()
    for interaction in user_interactions:
        if interaction.interaction_type in [InteractionType.complete, InteractionType.like]:
            # Get tags for this content
            content_tags = db.execute(
                select(ContentTag.tag_id)
                .where(
                    ContentTag.content_type == interaction.content_type,
                    ContentTag.content_id == interaction.content_id,
                )
            ).scalars().all()
            user_tag_ids.update(content_tags)

    # Find motifs with similar tags that user hasn't seen
    if user_tag_ids:
        similar_motifs = db.execute(
            select(Motif)
            .join(ContentTag, and_(
                ContentTag.content_type == "motif",
                ContentTag.content_id == Motif.id,
            ))
            .options(selectinload(Motif.lesson))
            .where(
                Motif.is_active.is_(True),
                Motif.id.notin_(interacted_content_ids) if interacted_content_ids else True,
                ContentTag.tag_id.in_(user_tag_ids),
            )
            .group_by(Motif.id)
            .order_by(func.count(ContentTag.tag_id).desc())
            .limit(limit)
        ).scalars().all()
    else:
        # Fallback: Get recent popular motifs
        similar_motifs = db.execute(
            select(Motif)
            .options(selectinload(Motif.lesson))
            .where(
                Motif.is_active.is_(True),
                Motif.id.notin_(interacted_content_ids) if interacted_content_ids else True,
            )
            .limit(limit)
        ).scalars().all()

    results = []
    for motif in similar_motifs:
        if motif.lesson:
            results.append({
                "content_type": "motif",
                "content_id": str(motif.id),
                "title": motif.name,
                "description": motif.lesson.description if motif.lesson else motif.name,
                "reason": "discover_new",
                "score": 0.8,
            })

    return results


def _get_review_needed(
    db: Session, user: User, limit: int
) -> List[Dict[str, Any]]:
    """Get content that user completed but might need to review."""
    # Find content completed more than 7 days ago
    review_threshold = datetime.now(timezone.utc) - timedelta(days=7)

    old_completions = db.execute(
        select(UserContentInteraction)
        .where(
            UserContentInteraction.user_id == user.id,
            UserContentInteraction.interaction_type == InteractionType.complete,
            UserContentInteraction.created_at < review_threshold,
        )
        .order_by(UserContentInteraction.created_at.asc())
        .limit(limit)
    ).scalars().all()

    results = []
    for interaction in old_completions:
        # Get the actual content details
        if interaction.content_type == "motif":
            motif = db.get(Motif, interaction.content_id)
            if motif and motif.is_active:
                results.append({
                    "content_type": "motif",
                    "content_id": str(motif.id),
                    "title": motif.name,
                    "description": motif.lesson.description if motif.lesson else motif.name,
                    "last_completed": interaction.created_at.isoformat(),
                    "reason": "review_needed",
                    "score": 0.6,
                })

    return results


def _get_popular_content(
    db: Session, user: User, limit: int
) -> List[Dict[str, Any]]:
    """Get trending/popular content based on recent interactions."""
    # Get content with most interactions in the last 30 days
    popularity_threshold = datetime.now(timezone.utc) - timedelta(days=30)

    popular_content = db.execute(
        select(
            UserContentInteraction.content_type,
            UserContentInteraction.content_id,
            func.count(UserContentInteraction.id).label("interaction_count"),
        )
        .where(UserContentInteraction.created_at >= popularity_threshold)
        .group_by(
            UserContentInteraction.content_type,
            UserContentInteraction.content_id,
        )
        .order_by(desc("interaction_count"))
        .limit(limit * 2)  # Get more to filter out user's own interactions
    ).all()

    results = []
    for content_type, content_id, count in popular_content:
        # Skip content user has already interacted with
        user_interaction = db.execute(
            select(UserContentInteraction)
            .where(
                UserContentInteraction.user_id == user.id,
                UserContentInteraction.content_type == content_type,
                UserContentInteraction.content_id == content_id,
            )
        ).scalar_one_or_none()

        if user_interaction:
            continue

        # Get content details
        if content_type == "motif":
            motif = db.get(Motif, content_id)
            if motif and motif.is_active:
                results.append({
                    "content_type": "motif",
                    "content_id": str(motif.id),
                    "title": motif.name,
                    "description": motif.lesson.description if motif.lesson else motif.name,
                    "popularity_score": int(count),
                    "reason": "popular",
                    "score": 0.7,
                })

        if len(results) >= limit:
            break

    return results



def get_similar_content(
    db: Session,
    content_type: str,
    content_id: UUID,
    user: User,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get similar content based on tags and collaborative filtering.

    Args:
        db: Database session
        content_type: Type of content (lesson, motif, quest)
        content_id: ID of the content
        user: User object
        limit: Maximum number of recommendations

    Returns:
        List of similar content items
    """
    # Get tags for the source content
    source_tags = db.execute(
        select(ContentTag.tag_id)
        .where(
            ContentTag.content_type == content_type,
            ContentTag.content_id == content_id,
        )
    ).scalars().all()

    if not source_tags:
        return []

    # Find content with overlapping tags
    similar_content = db.execute(
        select(
            ContentTag.content_type,
            ContentTag.content_id,
            func.count(ContentTag.tag_id).label("tag_overlap"),
        )
        .where(
            ContentTag.tag_id.in_(source_tags),
            or_(
                ContentTag.content_type != content_type,
                ContentTag.content_id != content_id,
            ),
        )
        .group_by(ContentTag.content_type, ContentTag.content_id)
        .order_by(desc("tag_overlap"))
        .limit(limit)
    ).all()

    results = []
    for similar_type, similar_id, overlap_count in similar_content:
        # Get content details
        if similar_type == "motif":
            motif = db.get(Motif, similar_id)
            if motif and motif.is_active:
                results.append({
                    "content_type": "motif",
                    "content_id": str(motif.id),
                    "title": motif.name,
                    "description": motif.lesson.description if motif.lesson else motif.name,
                    "similarity_score": float(overlap_count) / len(source_tags),
                    "reason": "similar_tags",
                })
        elif similar_type == "quest":
            quest = db.get(Quest, similar_id)
            if quest and quest.is_active:
                results.append({
                    "content_type": "quest",
                    "content_id": str(quest.id),
                    "title": quest.name,
                    "description": quest.description,
                    "similarity_score": float(overlap_count) / len(source_tags),
                    "reason": "similar_tags",
                })

    return results


def get_collaborative_filtering_recommendations(
    db: Session,
    user: User,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get recommendations based on collaborative filtering.

    Find users with similar interaction patterns and recommend content they liked.

    Args:
        db: Database session
        user: User object
        limit: Maximum number of recommendations

    Returns:
        List of recommended content items
    """
    # Get user's liked/completed content
    user_liked_content = db.execute(
        select(UserContentInteraction.content_id)
        .where(
            UserContentInteraction.user_id == user.id,
            UserContentInteraction.interaction_type.in_([
                InteractionType.complete,
                InteractionType.like,
            ]),
        )
    ).scalars().all()

    if not user_liked_content:
        return []

    # Find other users who liked similar content
    similar_users = db.execute(
        select(
            UserContentInteraction.user_id,
            func.count(UserContentInteraction.id).label("overlap_count"),
        )
        .where(
            UserContentInteraction.content_id.in_(user_liked_content),
            UserContentInteraction.user_id != user.id,
            UserContentInteraction.interaction_type.in_([
                InteractionType.complete,
                InteractionType.like,
            ]),
        )
        .group_by(UserContentInteraction.user_id)
        .order_by(desc("overlap_count"))
        .limit(10)  # Top 10 similar users
    ).all()

    if not similar_users:
        return []

    similar_user_ids = [user_id for user_id, _ in similar_users]

    # Get content that similar users liked but current user hasn't interacted with
    recommended_content = db.execute(
        select(
            UserContentInteraction.content_type,
            UserContentInteraction.content_id,
            func.count(UserContentInteraction.id).label("recommendation_score"),
        )
        .where(
            UserContentInteraction.user_id.in_(similar_user_ids),
            UserContentInteraction.content_id.notin_(user_liked_content),
            UserContentInteraction.interaction_type.in_([
                InteractionType.complete,
                InteractionType.like,
            ]),
        )
        .group_by(UserContentInteraction.content_type, UserContentInteraction.content_id)
        .order_by(desc("recommendation_score"))
        .limit(limit)
    ).all()

    results = []
    for content_type, content_id, score in recommended_content:
        if content_type == "motif":
            motif = db.get(Motif, content_id)
            if motif and motif.is_active:
                results.append({
                    "content_type": "motif",
                    "content_id": str(motif.id),
                    "title": motif.name,
                    "description": motif.lesson.description if motif.lesson else motif.name,
                    "recommendation_score": int(score),
                    "reason": "collaborative_filtering",
                })

    return results


def record_interaction(
    db: Session,
    user: User,
    content_type: str,
    content_id: UUID,
    interaction_type: InteractionType,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> UserContentInteraction:
    """
    Record a user content interaction.

    Args:
        db: Database session
        user: User object
        content_type: Type of content (lesson, motif, quest)
        content_id: ID of the content
        interaction_type: Type of interaction (view, complete, like, save)
        duration_seconds: Optional duration in seconds
        metadata: Optional additional metadata

    Returns:
        The created UserContentInteraction object
    """
    interaction = UserContentInteraction(
        user_id=user.id,
        content_type=content_type,
        content_id=content_id,
        interaction_type=interaction_type,
        duration_seconds=duration_seconds,
        metadata_json=metadata,
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return interaction
