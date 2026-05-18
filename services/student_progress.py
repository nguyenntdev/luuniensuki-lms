"""
Student Progress Service for classroom progress tracking.

This service handles:
- Calculating overall completion percentage for students
- Getting lesson completion stats
- Getting quiz performance stats
- Getting streak and engagement stats
- Getting motif discovery progress
- Comparing individual progress with class average
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import Session

from ..models import (
    User,
    Classroom,
    ClassMember,
    UserProgress,
    QuizAttempt,
    Motif,
    UnlockStatus,
    UserSession,
)


def get_student_progress(db: Session, student_id: UUID, classroom_id: UUID) -> dict:
    """
    Get comprehensive progress data for a student in a classroom.
    
    Args:
        db: Database session
        student_id: Student user ID
        classroom_id: Classroom ID
        
    Returns:
        Dictionary with progress metrics
        
    Raises:
        ValueError: If student is not a member of the classroom
    """
    # Verify student is in classroom
    member = db.execute(
        select(ClassMember).where(
            and_(
                ClassMember.class_id == classroom_id,
                ClassMember.user_id == student_id,
            )
        )
    ).scalar_one_or_none()
    
    if member is None:
        raise ValueError("Student is not a member of this classroom")
    
    student = db.get(User, student_id)
    if student is None:
        raise ValueError("Student not found")
    
    # Get lesson/motif completion stats
    total_motifs = db.execute(select(func.count(Motif.id))).scalar_one()
    
    discovered_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == student_id,
                UserProgress.status.in_([
                    UnlockStatus.discovered,
                    UnlockStatus.learned,
                    UnlockStatus.mastered,
                ])
            )
        )
    ).scalar_one()
    
    learned_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == student_id,
                UserProgress.status.in_([
                    UnlockStatus.learned,
                    UnlockStatus.mastered,
                ])
            )
        )
    ).scalar_one()
    
    mastered_motifs = db.execute(
        select(func.count(UserProgress.id)).where(
            and_(
                UserProgress.user_id == student_id,
                UserProgress.status == UnlockStatus.mastered,
            )
        )
    ).scalar_one()
    
    # Get quiz stats
    quiz_attempts_count = db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.user_id == student_id
        )
    ).scalar_one()
    
    quizzes_passed = db.execute(
        select(func.count(QuizAttempt.id)).where(
            and_(
                QuizAttempt.user_id == student_id,
                QuizAttempt.passed == True,
            )
        )
    ).scalar_one()
    
    avg_quiz_score = db.execute(
        select(func.avg(QuizAttempt.score)).where(
            QuizAttempt.user_id == student_id
        )
    ).scalar_one() or 0.0
    
    # Get time spent (from sessions)
    total_time_spent = calculate_time_spent(db, student_id)
    
    # Calculate overall completion percentage
    overall_completion = (discovered_motifs / total_motifs * 100) if total_motifs > 0 else 0.0
    
    return {
        "student_id": student_id,
        "classroom_id": classroom_id,
        "joined_at": member.joined_at,
        "overall_completion_percent": round(overall_completion, 1),
        "lessons": {
            "total_motifs": total_motifs,
            "discovered": discovered_motifs,
            "learned": learned_motifs,
            "mastered": mastered_motifs,
        },
        "quizzes": {
            "total_attempts": quiz_attempts_count,
            "passed": quizzes_passed,
            "average_score": round(avg_quiz_score, 1),
        },
        "engagement": {
            "current_streak": student.current_streak,
            "longest_streak": student.longest_streak,
            "total_xp": student.total_xp,
            "time_spent_minutes": total_time_spent,
        },
    }


def get_class_progress_summary(db: Session, classroom_id: UUID) -> dict:
    """
    Get class-wide progress summary with averages.

    Args:
        db: Database session
        classroom_id: Classroom ID

    Returns:
        Dictionary with class-wide metrics
    """
    # Get all student members
    student_ids = db.execute(
        select(ClassMember.user_id).where(
            and_(
                ClassMember.class_id == classroom_id,
                ClassMember.role == "learner",
            )
        )
    ).scalars().all()

    if not student_ids:
        return {
            "classroom_id": classroom_id,
            "student_count": 0,
            "averages": {
                "completion_percent": 0.0,
                "discovered_motifs": 0.0,
                "learned_motifs": 0.0,
                "mastered_motifs": 0.0,
                "quiz_attempts": 0.0,
                "quizzes_passed": 0.0,
                "average_quiz_score": 0.0,
                "current_streak": 0.0,
                "total_xp": 0.0,
            },
        }

    total_motifs = db.execute(select(func.count(Motif.id))).scalar_one()

    # Get average progress metrics
    progress_data = []
    for student_id in student_ids:
        discovered = db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == student_id,
                    UserProgress.status.in_([
                        UnlockStatus.discovered,
                        UnlockStatus.learned,
                        UnlockStatus.mastered,
                    ])
                )
            )
        ).scalar_one()

        learned = db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == student_id,
                    UserProgress.status.in_([
                        UnlockStatus.learned,
                        UnlockStatus.mastered,
                    ])
                )
            )
        ).scalar_one()

        mastered = db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == student_id,
                    UserProgress.status == UnlockStatus.mastered,
                )
            )
        ).scalar_one()

        progress_data.append({
            "discovered": discovered,
            "learned": learned,
            "mastered": mastered,
        })

    # Calculate averages
    avg_discovered = sum(p["discovered"] for p in progress_data) / len(progress_data)
    avg_learned = sum(p["learned"] for p in progress_data) / len(progress_data)
    avg_mastered = sum(p["mastered"] for p in progress_data) / len(progress_data)
    avg_completion = (avg_discovered / total_motifs * 100) if total_motifs > 0 else 0.0

    # Get quiz averages
    quiz_stats = db.execute(
        select(
            func.avg(func.count(QuizAttempt.id)).label("avg_attempts"),
            func.avg(func.count(QuizAttempt.id).filter(QuizAttempt.passed == True)).label("avg_passed"),
        )
        .where(QuizAttempt.user_id.in_(student_ids))
        .group_by(QuizAttempt.user_id)
    ).first()

    avg_score = db.execute(
        select(func.avg(QuizAttempt.score)).where(
            QuizAttempt.user_id.in_(student_ids)
        )
    ).scalar_one() or 0.0

    # Get user stats averages
    user_stats = db.execute(
        select(
            func.avg(User.current_streak).label("avg_streak"),
            func.avg(User.total_xp).label("avg_xp"),
        )
        .where(User.id.in_(student_ids))
    ).first()

    return {
        "classroom_id": classroom_id,
        "student_count": len(student_ids),
        "averages": {
            "completion_percent": round(avg_completion, 1),
            "discovered_motifs": round(avg_discovered, 1),
            "learned_motifs": round(avg_learned, 1),
            "mastered_motifs": round(avg_mastered, 1),
            "quiz_attempts": round(quiz_stats.avg_attempts if quiz_stats else 0.0, 1),
            "quizzes_passed": round(quiz_stats.avg_passed if quiz_stats else 0.0, 1),
            "average_quiz_score": round(avg_score, 1),
            "current_streak": round(user_stats.avg_streak if user_stats else 0.0, 1),
            "total_xp": round(user_stats.avg_xp if user_stats else 0.0, 1),
        },
    }


def get_class_leaderboard(
    db: Session,
    classroom_id: UUID,
    limit: int = 50,
    order_by: str = "xp",
) -> list[dict]:
    """
    Get class leaderboard sorted by various metrics.

    Args:
        db: Database session
        classroom_id: Classroom ID
        limit: Maximum number of students to return
        order_by: Metric to sort by ('xp', 'streak', 'motifs', 'quizzes')

    Returns:
        List of student rankings with their metrics
    """
    # Get all student members
    members = db.execute(
        select(ClassMember)
        .where(
            and_(
                ClassMember.class_id == classroom_id,
                ClassMember.role == "learner",
            )
        )
    ).scalars().all()

    if not members:
        return []

    student_ids = [m.user_id for m in members]

    # Get students with their progress
    students = db.execute(
        select(User).where(User.id.in_(student_ids))
    ).scalars().all()

    leaderboard = []
    for student in students:
        # Get motif stats
        discovered_count = db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == student.id,
                    UserProgress.status.in_([
                        UnlockStatus.discovered,
                        UnlockStatus.learned,
                        UnlockStatus.mastered,
                    ])
                )
            )
        ).scalar_one()

        mastered_count = db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == student.id,
                    UserProgress.status == UnlockStatus.mastered,
                )
            )
        ).scalar_one()

        # Get quiz stats
        quizzes_passed = db.execute(
            select(func.count(QuizAttempt.id)).where(
                and_(
                    QuizAttempt.user_id == student.id,
                    QuizAttempt.passed == True,
                )
            )
        ).scalar_one()

        leaderboard.append({
            "student_id": student.id,
            "display_name": student.display_name,
            "total_xp": student.total_xp,
            "current_streak": student.current_streak,
            "discovered_motifs": discovered_count,
            "mastered_motifs": mastered_count,
            "quizzes_passed": quizzes_passed,
        })

    # Sort by the requested metric
    sort_key_map = {
        "xp": lambda x: x["total_xp"],
        "streak": lambda x: x["current_streak"],
        "motifs": lambda x: x["discovered_motifs"],
        "quizzes": lambda x: x["quizzes_passed"],
    }

    sort_key = sort_key_map.get(order_by, sort_key_map["xp"])
    leaderboard.sort(key=sort_key, reverse=True)

    # Add rank
    for i, entry in enumerate(leaderboard[:limit], start=1):
        entry["rank"] = i

    return leaderboard[:limit]


def calculate_time_spent(db: Session, user_id: UUID) -> int:
    """
    Calculate total time spent in minutes from user sessions.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Total time spent in minutes
    """
    sessions = db.execute(
        select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.ended_at.isnot(None),
            )
        )
    ).scalars().all()

    total_minutes = 0
    for session in sessions:
        if session.ended_at and session.started_at:
            duration = session.ended_at - session.started_at
            total_minutes += int(duration.total_seconds() / 60)

    return total_minutes


