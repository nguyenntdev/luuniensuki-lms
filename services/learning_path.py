"""
Learning Path Service for personalized daily learning recommendations.

This service handles:
- Generating daily learning paths based on user progress and goals
- Spaced repetition scheduling for reviews
- Skill-level based recommendations
- Learning path progress tracking
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models import (
    LessonContent,
    Motif,
    QuizAttempt,
    User,
    UserLearningPath,
    UserProgress,
    UnlockStatus,
)

# Learning path configuration
MAX_LESSONS_PER_DAY = 3
MAX_REVIEWS_PER_DAY = 10
MAX_QUIZZES_PER_DAY = 5
LESSON_TIME_MINUTES = 10
REVIEW_TIME_MINUTES = 3
QUIZ_TIME_MINUTES = 5


def get_todays_learning_path(
    db: Session, user: User, now: datetime
) -> Optional[UserLearningPath]:
    """
    Get or generate today's learning path for a user.
    
    Args:
        db: Database session
        user: The user to get path for
        now: Current datetime
        
    Returns:
        UserLearningPath for today
    """
    # Get start of today in UTC
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if path already exists for today
    existing_path = db.execute(
        select(UserLearningPath).where(
            and_(
                UserLearningPath.user_id == user.id,
                UserLearningPath.path_date == today_start,
            )
        )
    ).scalar_one_or_none()
    
    if existing_path:
        return existing_path
    
    # Generate new path
    return generate_learning_path(db, user, today_start, now)


def generate_learning_path(
    db: Session, user: User, path_date: datetime, now: datetime
) -> UserLearningPath:
    """
    Generate a personalized learning path for a user.
    
    Args:
        db: Database session
        user: The user to generate path for
        path_date: The date to generate path for (should be start of day)
        now: Current datetime
        
    Returns:
        Newly created UserLearningPath
    """
    # Get due reviews based on spaced repetition
    reviews = _get_due_reviews(db, user, now)
    
    # Get recommended lessons based on progress and goals
    lessons = _get_recommended_lessons(db, user)
    
    # Get recommended quizzes for practice
    quizzes = _get_recommended_quizzes(db, user)
    
    # Calculate estimated time
    estimated_time = (
        len(lessons) * LESSON_TIME_MINUTES +
        len(reviews) * REVIEW_TIME_MINUTES +
        len(quizzes) * QUIZ_TIME_MINUTES
    )
    
    # Create learning path
    learning_path = UserLearningPath(
        user_id=user.id,
        path_date=path_date,
        recommended_lessons=lessons,
        recommended_reviews=reviews,
        recommended_quizzes=quizzes,
        estimated_time_minutes=estimated_time,
        generated_at=now,
    )
    
    db.add(learning_path)
    db.commit()
    db.refresh(learning_path)
    
    return learning_path


def _get_due_reviews(db: Session, user: User, now: datetime) -> list[dict[str, Any]]:
    """
    Get motifs that are due for spaced repetition review.
    
    Args:
        db: Database session
        user: The user
        now: Current datetime
        
    Returns:
        List of review items with motif_id, order, priority, and due_date
    """
    # Get all learned/mastered motifs
    progress_rows = db.execute(
        select(UserProgress, Motif)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status.in_([UnlockStatus.learned, UnlockStatus.mastered]),
        )
        .order_by(UserProgress.learned_at.asc())
    ).all()
    
    reviews = []
    for progress, motif in progress_rows:
        # Get last quiz attempt to calculate review interval
        last_attempt = db.execute(
            select(
                func.max(QuizAttempt.created_at),
                func.max(QuizAttempt.percentage)
            ).where(
                QuizAttempt.user_id == user.id,
                QuizAttempt.motif_id == motif.id,
            )
        ).first()

        last_date = last_attempt[0] if last_attempt else None
        score = last_attempt[1] if last_attempt else None

        if last_date is None:
            last_date = (
                progress.mastered_at
                or progress.learned_at
                or progress.lesson_viewed_at
                or progress.discovered_at
            )

        # Calculate review interval based on performance
        interval_days = 1
        if score is not None:
            if score >= 90:
                interval_days = 14  # 2 weeks for excellent retention
            elif score >= 80:
                interval_days = 7   # 1 week for good retention
            elif score >= 60:
                interval_days = 3   # 3 days for moderate retention
            else:
                interval_days = 1   # 1 day for poor retention

        # Check if review is due
        if last_date:
            days_since_review = (now - last_date).days
            if days_since_review >= interval_days:
                # Determine priority
                priority = "low"
                if days_since_review >= interval_days * 2:
                    priority = "high"
                elif days_since_review >= interval_days * 1.5:
                    priority = "medium"

                reviews.append({
                    "motif_id": str(motif.id),
                    "order": len(reviews),
                    "priority": priority,
                    "due_date": last_date.isoformat() if isinstance(last_date, datetime) else str(last_date),
                    "days_overdue": days_since_review - interval_days,
                })

        # Limit to max reviews per day
        if len(reviews) >= MAX_REVIEWS_PER_DAY:
            break

    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    reviews.sort(key=lambda x: (priority_order[x["priority"]], x["days_overdue"]))

    # Update order after sorting
    for i, review in enumerate(reviews):
        review["order"] = i

    return reviews


def _get_recommended_lessons(db: Session, user: User) -> list[dict[str, Any]]:
    """
    Get recommended lessons based on user progress and goals.

    Args:
        db: Database session
        user: The user

    Returns:
        List of lesson items with lesson_id, order, and reason
    """
    # Get user's discovered but not learned motifs
    not_learned_progress = db.execute(
        select(UserProgress, Motif)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status == UnlockStatus.discovered,
        )
        .order_by(UserProgress.discovered_at.asc())
    ).all()

    lessons = []
    for progress, motif in not_learned_progress:
        # Get lesson content for this motif
        lesson = db.execute(
            select(LessonContent).where(LessonContent.motif_id == motif.id)
        ).scalar_one_or_none()

        if lesson:
            reason = "Continue learning discovered motifs"
            if user.onboarding_goal:
                reason = f"Aligned with your goal: {user.onboarding_goal}"

            lessons.append({
                "lesson_id": str(lesson.id),
                "motif_id": str(motif.id),
                "order": len(lessons),
                "reason": reason,
            })

        if len(lessons) >= MAX_LESSONS_PER_DAY:
            break

    # If we don't have enough lessons, get some new undiscovered ones
    if len(lessons) < MAX_LESSONS_PER_DAY:
        undiscovered_motifs = db.execute(
            select(Motif)
            .outerjoin(UserProgress, and_(
                UserProgress.motif_id == Motif.id,
                UserProgress.user_id == user.id
            ))
            .where(UserProgress.id.is_(None))
            .order_by(Motif.created_at.asc())
            .limit(MAX_LESSONS_PER_DAY - len(lessons))
        ).scalars().all()

        for motif in undiscovered_motifs:
            lesson = db.execute(
                select(LessonContent).where(LessonContent.motif_id == motif.id)
            ).scalar_one_or_none()

            if lesson:
                lessons.append({
                    "lesson_id": str(lesson.id),
                    "motif_id": str(motif.id),
                    "order": len(lessons),
                    "reason": "Discover new motifs",
                })

    return lessons


def _get_recommended_quizzes(db: Session, user: User) -> list[dict[str, Any]]:
    """
    Get recommended quizzes for practice.

    Args:
        db: Database session
        user: The user

    Returns:
        List of quiz items with motif_id, order, and difficulty
    """
    # Get learned motifs that could use more practice
    learned_progress = db.execute(
        select(UserProgress, Motif)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status == UnlockStatus.learned,
            UserProgress.quiz_best_score < 90,  # Haven't mastered yet
        )
        .order_by(UserProgress.quiz_best_score.asc())  # Prioritize lower scores
        .limit(MAX_QUIZZES_PER_DAY)
    ).all()

    quizzes = []
    for progress, motif in learned_progress:
        difficulty = 1  # Easy
        if progress.quiz_best_score >= 60:
            difficulty = 2  # Medium
        if progress.quiz_best_score >= 75:
            difficulty = 3  # Hard

        quizzes.append({
            "motif_id": str(motif.id),
            "order": len(quizzes),
            "difficulty": difficulty,
            "best_score": progress.quiz_best_score,
        })

    return quizzes


def complete_path_item(
    db: Session,
    learning_path: UserLearningPath,
    item_type: str,
    item_id: UUID,
    now: datetime
) -> dict[str, Any]:
    """
    Mark an item in the learning path as completed.

    Args:
        db: Database session
        learning_path: The learning path
        item_type: Type of item ("lesson", "review", "quiz")
        item_id: ID of the item
        now: Current datetime

    Returns:
        Dictionary with completion info
    """
    # Check if already completed
    for completed in learning_path.completed_items:
        if completed["item_id"] == str(item_id) and completed["item_type"] == item_type:
            return {
                "already_completed": True,
                "completed_at": completed["completed_at"],
            }

    # Add to completed items
    learning_path.completed_items.append({
        "item_type": item_type,
        "item_id": str(item_id),
        "completed_at": now.isoformat(),
    })

    # Check if entire path is completed
    total_items = (
        len(learning_path.recommended_lessons) +
        len(learning_path.recommended_reviews) +
        len(learning_path.recommended_quizzes)
    )

    if len(learning_path.completed_items) >= total_items:
        learning_path.is_completed = True
        learning_path.completed_at = now

    db.commit()
    db.refresh(learning_path)

    return {
        "already_completed": False,
        "completed_at": now.isoformat(),
        "path_completed": learning_path.is_completed,
        "progress": len(learning_path.completed_items),
        "total": total_items,
    }


def get_path_history(
    db: Session,
    user: User,
    limit: int = 30
) -> list[UserLearningPath]:
    """
    Get historical learning paths for a user.

    Args:
        db: Database session
        user: The user
        limit: Maximum number of paths to return

    Returns:
        List of UserLearningPath objects
    """
    paths = db.execute(
        select(UserLearningPath)
        .where(UserLearningPath.user_id == user.id)
        .order_by(UserLearningPath.path_date.desc())
        .limit(limit)
    ).scalars().all()

    return paths


def get_path_statistics(db: Session, user: User, days: int = 30) -> dict[str, Any]:
    """
    Get learning path statistics for a user.

    Args:
        db: Database session
        user: The user
        days: Number of days to look back

    Returns:
        Dictionary with statistics
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    paths = db.execute(
        select(UserLearningPath)
        .where(
            UserLearningPath.user_id == user.id,
            UserLearningPath.path_date >= cutoff_date,
        )
    ).scalars().all()

    total_paths = len(paths)
    completed_paths = sum(1 for p in paths if p.is_completed)
    total_lessons = sum(len(p.recommended_lessons) for p in paths)
    total_reviews = sum(len(p.recommended_reviews) for p in paths)
    total_quizzes = sum(len(p.recommended_quizzes) for p in paths)

    completed_lessons = 0
    completed_reviews = 0
    completed_quizzes = 0

    for path in paths:
        for item in path.completed_items:
            if item["item_type"] == "lesson":
                completed_lessons += 1
            elif item["item_type"] == "review":
                completed_reviews += 1
            elif item["item_type"] == "quiz":
                completed_quizzes += 1

    return {
        "total_paths_generated": total_paths,
        "completed_paths": completed_paths,
        "completion_rate": (completed_paths / total_paths * 100) if total_paths > 0 else 0,
        "lessons": {
            "recommended": total_lessons,
            "completed": completed_lessons,
            "completion_rate": (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
        },
        "reviews": {
            "recommended": total_reviews,
            "completed": completed_reviews,
            "completion_rate": (completed_reviews / total_reviews * 100) if total_reviews > 0 else 0,
        },
        "quizzes": {
            "recommended": total_quizzes,
            "completed": completed_quizzes,
            "completion_rate": (completed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0,
        },
        "days_analyzed": days,
    }


