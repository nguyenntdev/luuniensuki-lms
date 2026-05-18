"""
Lesson Sequence Service for Luuniensuki LMS.

This service provides functionality for:
- Determining the next lesson for a user to take
- Checking if a lesson is unlocked based on prerequisites
- Getting the full learning sequence/path
- Managing prerequisite relationships
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import Session, selectinload

from ..models import (
    LessonContent,
    LessonPrerequisite,
    Motif,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
)


def check_lesson_unlocked(
    db: Session,
    user: User,
    lesson_id: UUID,
) -> tuple[bool, list[LessonContent], list[LessonContent]]:
    """
    Check if a lesson is unlocked for a user based on prerequisites.

    Args:
        db: Database session
        user: User object
        lesson_id: ID of the lesson to check

    Returns:
        Tuple of (is_unlocked, missing_strict_prerequisites, missing_recommended_prerequisites)
    """
    # Get all prerequisites for this lesson
    prerequisites = db.execute(
        select(LessonPrerequisite)
        .options(
            selectinload(LessonPrerequisite.prerequisite_lesson)
            .selectinload(LessonContent.motif)
        )
        .where(LessonPrerequisite.lesson_id == lesson_id)
    ).scalars().all()

    if not prerequisites:
        # No prerequisites, lesson is unlocked
        return True, [], []

    # Get user's completed lessons
    completed_progress = db.execute(
        select(UserProgress.motif_id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status == UnlockStatus.mastered
        )
    ).scalars().all()

    # Get motif IDs for completed lessons
    completed_lesson_ids = db.execute(
        select(LessonContent.id)
        .where(LessonContent.motif_id.in_(completed_progress))
    ).scalars().all() if completed_progress else []

    completed_lesson_ids_set = set(completed_lesson_ids)

    missing_strict = []
    missing_recommended = []

    for prereq in prerequisites:
        if prereq.prerequisite_lesson_id not in completed_lesson_ids_set:
            if prereq.is_strict:
                missing_strict.append(prereq.prerequisite_lesson)
            else:
                missing_recommended.append(prereq.prerequisite_lesson)

    is_unlocked = len(missing_strict) == 0
    return is_unlocked, missing_strict, missing_recommended


def get_next_lesson(
    db: Session,
    user: User,
    urn_id: Optional[UUID] = None,
) -> Optional[dict]:
    """
    Get the next recommended lesson for a user.
    
    Priority order:
    1. Started but not completed lessons (discovered or learned status)
    2. Unlocked lessons in the same urn (if urn_id provided)
    3. Unlocked lessons ordered by difficulty
    
    Args:
        db: Database session
        user: User object
        urn_id: Optional urn context for filtering lessons
        
    Returns:
        Dictionary with next lesson info or None if no suitable lesson found
    """
    # Get user's progress
    user_progress = db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user.id)
    ).scalars().all()
    
    progress_by_motif = {p.motif_id: p for p in user_progress}
    
    # Strategy 1: Continue in-progress lessons
    in_progress_motifs = [
        p.motif_id for p in user_progress
        if p.status in [UnlockStatus.discovered, UnlockStatus.learned]
    ]
    
    if in_progress_motifs:
        lesson = db.execute(
            select(LessonContent)
            .options(
                selectinload(LessonContent.motif).selectinload(Motif.urn)
            )
            .where(
                LessonContent.motif_id.in_(in_progress_motifs),
                LessonContent.is_published.is_(True)
            )
            .order_by(LessonContent.difficulty_level.asc().nullslast())
            .limit(1)
        ).scalar_one_or_none()
        
        if lesson:
            progress = progress_by_motif.get(lesson.motif_id)
            return {
                "lesson_id": lesson.id,
                "motif_id": lesson.motif_id,
                "motif_name": lesson.motif.name,
                "motif_slug": lesson.motif.slug,
                "urn_id": lesson.motif.urn_id,
                "urn_name": lesson.motif.urn.name if lesson.motif.urn else None,
                "difficulty_level": lesson.difficulty_level,
                "estimated_time_minutes": lesson.estimated_time_minutes,
                "reason": "continue_learning",
                "has_prerequisites": False,
                "progress_status": progress.status.value if progress else None,
            }
    
    # Strategy 2: Find next unlocked lesson
    query = (
        select(LessonContent)
        .join(Motif, LessonContent.motif_id == Motif.id)
        .options(
            selectinload(LessonContent.motif).selectinload(Motif.urn)
        )
        .where(LessonContent.is_published.is_(True))
    )

    # Filter by urn if provided
    if urn_id:
        query = query.where(Motif.urn_id == urn_id)

    # Exclude already mastered lessons
    mastered_motif_ids = [
        p.motif_id for p in user_progress
        if p.status == UnlockStatus.mastered
    ]
    if mastered_motif_ids:
        query = query.where(LessonContent.motif_id.notin_(mastered_motif_ids))

    # Order by difficulty
    query = query.order_by(
        LessonContent.difficulty_level.asc().nullslast(),
        LessonContent.created_at.asc()
    )

    # Get candidate lessons
    candidate_lessons = db.execute(query.limit(20)).scalars().all()

    # Find first unlocked lesson
    for lesson in candidate_lessons:
        is_unlocked, _, _ = check_lesson_unlocked(db, user, lesson.id)
        if is_unlocked:
            progress = progress_by_motif.get(lesson.motif_id)
            return {
                "lesson_id": lesson.id,
                "motif_id": lesson.motif_id,
                "motif_name": lesson.motif.name,
                "motif_slug": lesson.motif.slug,
                "urn_id": lesson.motif.urn_id,
                "urn_name": lesson.motif.urn.name if lesson.motif.urn else None,
                "difficulty_level": lesson.difficulty_level,
                "estimated_time_minutes": lesson.estimated_time_minutes,
                "reason": "next_in_sequence",
                "has_prerequisites": False,
                "progress_status": progress.status.value if progress else None,
            }

    # No suitable lesson found
    return None


def get_lesson_prerequisites(
    db: Session,
    user: User,
    lesson_id: UUID,
) -> dict:
    """
    Get all prerequisites for a lesson with completion status.

    Args:
        db: Database session
        user: User object
        lesson_id: ID of the lesson

    Returns:
        Dictionary with prerequisite information
    """
    # Get prerequisites
    prerequisites = db.execute(
        select(LessonPrerequisite)
        .options(
            selectinload(LessonPrerequisite.prerequisite_lesson)
            .selectinload(LessonContent.motif)
        )
        .where(LessonPrerequisite.lesson_id == lesson_id)
    ).scalars().all()

    # Get user's completed lessons
    completed_progress = db.execute(
        select(UserProgress.motif_id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status == UnlockStatus.mastered
        )
    ).scalars().all()

    completed_motif_ids = set(completed_progress)

    prerequisite_info = []
    all_met = True

    for prereq in prerequisites:
        lesson = prereq.prerequisite_lesson
        is_completed = lesson.motif_id in completed_motif_ids

        if prereq.is_strict and not is_completed:
            all_met = False

        prerequisite_info.append({
            "id": lesson.id,
            "motif_id": lesson.motif_id,
            "motif_name": lesson.motif.name,
            "motif_slug": lesson.motif.slug,
            "difficulty_level": lesson.difficulty_level,
            "estimated_time_minutes": lesson.estimated_time_minutes,
            "is_strict": prereq.is_strict,
            "is_completed": is_completed,
        })

    return {
        "lesson_id": lesson_id,
        "prerequisites": prerequisite_info,
        "all_prerequisites_met": all_met,
    }


def get_lesson_sequence(
    db: Session,
    user: User,
    urn_id: Optional[UUID] = None,
) -> dict:
    """
    Get the full learning sequence for a user.

    Args:
        db: Database session
        user: User object
        urn_id: Optional urn to filter lessons

    Returns:
        Dictionary with sequence information
    """
    query = (
        select(LessonContent)
        .join(Motif, LessonContent.motif_id == Motif.id)
        .join(Urn, Motif.urn_id == Urn.id)
        .options(
            selectinload(LessonContent.motif).selectinload(Motif.urn)
        )
        .where(LessonContent.is_published.is_(True))
    )

    if urn_id:
        query = query.where(Motif.urn_id == urn_id)

    query = query.order_by(
        LessonContent.difficulty_level.asc().nullslast(),
        LessonContent.created_at.asc()
    )

    lessons = db.execute(query).scalars().all()

    # Get user progress
    user_progress = db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user.id)
    ).scalars().all()

    progress_by_motif = {p.motif_id: p for p in user_progress}

    sequence = []
    completed_count = 0
    current_position = 0

    for idx, lesson in enumerate(lessons):
        progress = progress_by_motif.get(lesson.motif_id)
        is_completed = progress and progress.status == UnlockStatus.mastered
        is_unlocked, _, _ = check_lesson_unlocked(db, user, lesson.id)

        if is_completed:
            completed_count += 1
            current_position = idx + 1

        sequence.append({
            "lesson_id": lesson.id,
            "motif_id": lesson.motif_id,
            "motif_name": lesson.motif.name,
            "motif_slug": lesson.motif.slug,
            "urn_id": lesson.motif.urn_id,
            "urn_name": lesson.motif.urn.name if lesson.motif.urn else None,
            "difficulty_level": lesson.difficulty_level,
            "estimated_time_minutes": lesson.estimated_time_minutes,
            "is_unlocked": is_unlocked,
            "is_completed": is_completed,
            "progress_status": progress.status.value if progress else None,
            "position": idx + 1,
        })

    urn_name = None
    if urn_id and lessons:
        urn_name = lessons[0].motif.urn.name if lessons[0].motif.urn else None

    return {
        "urn_id": urn_id,
        "urn_name": urn_name,
        "total_lessons": len(lessons),
        "completed_lessons": completed_count,
        "current_position": current_position,
        "sequence": sequence,
    }

