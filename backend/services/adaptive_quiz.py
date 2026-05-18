"""
Adaptive Quiz Service
Implements ELO-like rating system for adaptive difficulty adjustment.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models import (
    QuizQuestion,
    UserSkillLevel,
    QuizAttempt,
    SkillType,
    User,
)


# Constants for ELO-like rating system
K_FACTOR = 0.1  # Learning rate for skill level updates
MIN_SKILL_LEVEL = 0.0
MAX_SKILL_LEVEL = 1.0
DEFAULT_SKILL_LEVEL = 0.5
DIFFICULTY_TOLERANCE = 0.15  # +/- tolerance for question selection


def normalize_difficulty(difficulty: int) -> float:
    """
    Normalize integer difficulty (1-5) to float (0.0-1.0).
    
    Args:
        difficulty: Integer difficulty (1-5)
        
    Returns:
        Normalized difficulty as float (0.0-1.0)
    """
    # Map 1-5 to 0.0-1.0
    # 1 -> 0.0, 2 -> 0.25, 3 -> 0.5, 4 -> 0.75, 5 -> 1.0
    return (difficulty - 1) / 4.0


def get_user_skill_level(
    db: Session,
    user_id: UUID,
    skill_type: str
) -> UserSkillLevel:
    """
    Get or create user skill level for a specific skill type.
    
    Args:
        db: Database session
        user_id: User ID
        skill_type: Skill type (from SkillType enum)
        
    Returns:
        UserSkillLevel instance
    """
    stmt = select(UserSkillLevel).where(
        UserSkillLevel.user_id == user_id,
        UserSkillLevel.skill_type == skill_type
    )
    skill = db.execute(stmt).scalar_one_or_none()
    
    if skill is None:
        # Create new skill level starting at 0.5
        skill = UserSkillLevel(
            user_id=user_id,
            skill_type=skill_type,
            skill_level=DEFAULT_SKILL_LEVEL,
            total_questions=0,
            correct_answers=0
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
    
    return skill


def update_skill_level(
    db: Session,
    user_id: UUID,
    skill_type: str,
    question_difficulty: int,
    is_correct: bool
) -> UserSkillLevel:
    """
    Update user's skill level based on quiz answer using ELO-like algorithm.
    
    Args:
        db: Database session
        user_id: User ID
        skill_type: Skill type
        question_difficulty: Question difficulty (1-5)
        is_correct: Whether the answer was correct
        
    Returns:
        Updated UserSkillLevel
    """
    skill = get_user_skill_level(db, user_id, skill_type)
    
    # Normalize question difficulty to 0.0-1.0
    normalized_difficulty = normalize_difficulty(question_difficulty)
    
    # Calculate expected performance (higher skill should perform better on easier questions)
    expected = 1.0 - abs(skill.skill_level - normalized_difficulty)
    
    # Actual performance (1 if correct, 0 if wrong)
    actual = 1.0 if is_correct else 0.0
    
    # Update skill level using ELO-like formula
    delta = K_FACTOR * (actual - expected)
    new_skill_level = skill.skill_level + delta
    
    # Clamp to valid range
    new_skill_level = max(MIN_SKILL_LEVEL, min(MAX_SKILL_LEVEL, new_skill_level))
    
    # Update statistics
    skill.skill_level = new_skill_level
    skill.total_questions += 1
    if is_correct:
        skill.correct_answers += 1
    skill.last_updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(skill)
    
    return skill


def get_recommended_difficulty(
    db: Session,
    user_id: UUID,
    skill_type: str
) -> float:
    """
    Get recommended difficulty level for a user based on their skill level.

    Args:
        db: Database session
        user_id: User ID
        skill_type: Skill type

    Returns:
        Recommended difficulty as float (0.0-1.0)
    """
    skill = get_user_skill_level(db, user_id, skill_type)
    return skill.skill_level


def get_adaptive_questions(
    db: Session,
    user_id: UUID,
    motif_id: Optional[UUID] = None,
    skill_type: Optional[str] = None,
    limit: int = 10
) -> list[QuizQuestion]:
    """
    Get adaptive quiz questions based on user's skill level.

    Args:
        db: Database session
        user_id: User ID
        motif_id: Optional motif ID to filter by
        skill_type: Optional skill type to filter by
        limit: Maximum number of questions to return

    Returns:
        List of QuizQuestion instances matched to user's skill level
    """
    # Get user's skill level for the specified skill type
    if skill_type:
        recommended_difficulty = get_recommended_difficulty(db, user_id, skill_type)
    else:
        # Use average of all skills if no specific skill type
        stmt = select(func.avg(UserSkillLevel.skill_level)).where(
            UserSkillLevel.user_id == user_id
        )
        avg_skill = db.execute(stmt).scalar()
        recommended_difficulty = avg_skill if avg_skill is not None else DEFAULT_SKILL_LEVEL

    # Calculate difficulty range (recommended +/- tolerance)
    min_difficulty = max(0.0, recommended_difficulty - DIFFICULTY_TOLERANCE)
    max_difficulty = min(1.0, recommended_difficulty + DIFFICULTY_TOLERANCE)

    # Convert normalized difficulty back to integer range (1-5)
    # 0.0-1.0 -> 1-5
    min_int_difficulty = max(1, int(min_difficulty * 4) + 1)
    max_int_difficulty = min(5, int(max_difficulty * 4) + 1)

    # Build query
    query = select(QuizQuestion).where(
        QuizQuestion.is_active.is_(True),
        QuizQuestion.is_published.is_(True),
        QuizQuestion.difficulty >= min_int_difficulty,
        QuizQuestion.difficulty <= max_int_difficulty
    )

    if motif_id:
        query = query.where(QuizQuestion.motif_id == motif_id)

    if skill_type:
        query = query.where(QuizQuestion.skill_type == skill_type)

    # Randomize and limit
    query = query.order_by(func.random()).limit(limit)

    questions = db.execute(query).scalars().all()

    return list(questions)


def recalculate_user_skills(
    db: Session,
    user_id: UUID
) -> list[UserSkillLevel]:
    """
    Recalculate user's skill levels from their quiz attempt history.
    This is useful for backfilling or recalibrating skill levels.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of recalculated UserSkillLevel instances
    """
    # Get all quiz attempts for the user
    stmt = select(QuizAttempt).where(
        QuizAttempt.user_id == user_id
    ).order_by(QuizAttempt.completed_at)

    attempts = db.execute(stmt).scalars().all()

    # Reset or create skill levels
    for skill_type_value in [st.value for st in SkillType]:
        stmt = select(UserSkillLevel).where(
            UserSkillLevel.user_id == user_id,
            UserSkillLevel.skill_type == skill_type_value
        )
        skill = db.execute(stmt).scalar_one_or_none()

        if skill:
            skill.skill_level = DEFAULT_SKILL_LEVEL
            skill.total_questions = 0
            skill.correct_answers = 0
        else:
            skill = UserSkillLevel(
                user_id=user_id,
                skill_type=skill_type_value,
                skill_level=DEFAULT_SKILL_LEVEL,
                total_questions=0,
                correct_answers=0
            )
            db.add(skill)

    db.commit()

    # Replay all quiz attempts to recalculate
    for attempt in attempts:
        # Parse answers from JSONB
        answers = attempt.answers
        if not isinstance(answers, list):
            continue

        for answer in answers:
            question_id = answer.get("question_id")
            is_correct = answer.get("is_correct", False)

            if not question_id:
                continue

            # Get the question
            question = db.get(QuizQuestion, UUID(question_id))
            if not question or not question.skill_type:
                continue

            # Update skill level
            update_skill_level(
                db,
                user_id,
                question.skill_type,
                question.difficulty,
                is_correct
            )

    # Return all updated skill levels
    stmt = select(UserSkillLevel).where(UserSkillLevel.user_id == user_id)
    skills = db.execute(stmt).scalars().all()

    return list(skills)


