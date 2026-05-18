"""
Quest Assignment Service
Handles quest assignment to students and classrooms.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from backend.models import (
    QuestAssignment,
    AssignmentProgress,
    Quest,
    Classroom,
    ClassMember,
    User,
    QuestProgress,
)


def assign_quest_to_classroom(
    db: Session,
    classroom: Classroom,
    quest_id: UUID,
    teacher: User,
    due_at: Optional[datetime] = None,
    points_override: Optional[int] = None,
    notes: Optional[str] = None,
) -> QuestAssignment:
    """
    Assign a quest to an entire classroom.
    All current members will get assignment progress entries.
    
    Args:
        db: Database session
        classroom: Classroom to assign to
        quest_id: Quest ID to assign
        teacher: Teacher assigning the quest
        due_at: Optional due date
        points_override: Optional custom points for this assignment
        notes: Optional teacher notes
        
    Returns:
        Created QuestAssignment instance
    """
    # Verify quest exists
    quest = db.get(Quest, quest_id)
    if not quest:
        raise ValueError("Quest not found")
    
    if not quest.is_active:
        raise ValueError("Cannot assign inactive quest")
    
    # Check if quest is already assigned to this classroom
    existing = db.execute(
        select(QuestAssignment).where(
            QuestAssignment.class_id == classroom.id,
            QuestAssignment.quest_id == quest_id
        )
    ).scalar_one_or_none()
    
    if existing:
        raise ValueError("Quest is already assigned to this classroom")
    
    # Create assignment
    assignment = QuestAssignment(
        class_id=classroom.id,
        quest_id=quest_id,
        assigned_by_id=teacher.id,
        due_at=due_at,
        points_override=points_override,
        notes=notes,
    )
    
    db.add(assignment)
    db.flush()
    
    # Create progress entries for all current classroom members
    members = db.execute(
        select(ClassMember).where(ClassMember.class_id == classroom.id)
    ).scalars().all()
    
    for member in members:
        # Skip if already has progress for this assignment
        existing_progress = db.execute(
            select(AssignmentProgress).where(
                AssignmentProgress.assignment_id == assignment.id,
                AssignmentProgress.user_id == member.user_id
            )
        ).scalar_one_or_none()
        
        if not existing_progress:
            progress = AssignmentProgress(
                assignment_id=assignment.id,
                user_id=member.user_id,
                status="assigned",
            )
            db.add(progress)
    
    db.commit()
    db.refresh(assignment)
    
    return assignment


def assign_quest_to_student(
    db: Session,
    classroom: Classroom,
    quest_id: UUID,
    student_id: UUID,
    teacher: User,
    due_at: Optional[datetime] = None,
    points_override: Optional[int] = None,
    notes: Optional[str] = None,
) -> QuestAssignment:
    """
    Assign a quest to an individual student in a classroom.
    
    Args:
        db: Database session
        classroom: Classroom context
        quest_id: Quest ID to assign
        student_id: Student user ID
        teacher: Teacher assigning the quest
        due_at: Optional due date
        points_override: Optional custom points
        notes: Optional teacher notes
        
    Returns:
        Created QuestAssignment instance
    """
    # Verify student is in classroom
    member = db.execute(
        select(ClassMember).where(
            ClassMember.class_id == classroom.id,
            ClassMember.user_id == student_id
        )
    ).scalar_one_or_none()
    
    if not member:
        raise ValueError("Student is not a member of this classroom")
    
    # Verify quest exists
    quest = db.get(Quest, quest_id)
    if not quest:
        raise ValueError("Quest not found")
    
    if not quest.is_active:
        raise ValueError("Cannot assign inactive quest")
    
    # Create or get assignment
    assignment = db.execute(
        select(QuestAssignment).where(
            QuestAssignment.class_id == classroom.id,
            QuestAssignment.quest_id == quest_id
        )
    ).scalar_one_or_none()

    # If assignment doesn't exist for this classroom, create it
    if not assignment:
        assignment = QuestAssignment(
            class_id=classroom.id,
            quest_id=quest_id,
            assigned_by_id=teacher.id,
            due_at=due_at,
            points_override=points_override,
            notes=notes,
        )
        db.add(assignment)
        db.flush()

    # Create progress entry for the specific student
    existing_progress = db.execute(
        select(AssignmentProgress).where(
            AssignmentProgress.assignment_id == assignment.id,
            AssignmentProgress.user_id == student_id
        )
    ).scalar_one_or_none()

    if existing_progress:
        raise ValueError("Student already has this assignment")

    progress = AssignmentProgress(
        assignment_id=assignment.id,
        user_id=student_id,
        status="assigned",
    )
    db.add(progress)

    db.commit()
    db.refresh(assignment)

    return assignment


def get_classroom_assignments(
    db: Session,
    classroom_id: UUID,
    include_completed: bool = True,
) -> list[QuestAssignment]:
    """
    Get all quest assignments for a classroom.

    Args:
        db: Database session
        classroom_id: Classroom ID
        include_completed: Whether to include completed assignments

    Returns:
        List of QuestAssignment instances
    """
    query = select(QuestAssignment).where(
        QuestAssignment.class_id == classroom_id
    ).options(
        selectinload(QuestAssignment.quest),
        selectinload(QuestAssignment.assigned_by),
        selectinload(QuestAssignment.progress_entries),
    )

    assignments = db.execute(query.order_by(QuestAssignment.assigned_at.desc())).scalars().all()

    return list(assignments)


def get_student_assignments(
    db: Session,
    user_id: UUID,
    classroom_id: Optional[UUID] = None,
) -> list[dict]:
    """
    Get all quest assignments for a student.

    Args:
        db: Database session
        user_id: Student user ID
        classroom_id: Optional classroom filter

    Returns:
        List of assignment dictionaries with progress
    """
    query = select(AssignmentProgress).where(
        AssignmentProgress.user_id == user_id
    ).options(
        selectinload(AssignmentProgress.assignment).selectinload(QuestAssignment.quest),
        selectinload(AssignmentProgress.assignment).selectinload(QuestAssignment.classroom),
    )

    if classroom_id:
        query = query.join(QuestAssignment).where(
            QuestAssignment.class_id == classroom_id
        )

    progress_entries = db.execute(query).scalars().all()

    results = []
    for progress in progress_entries:
        assignment = progress.assignment
        results.append({
            "assignment_id": str(assignment.id),
            "quest_id": str(assignment.quest_id),
            "quest_name": assignment.quest.name,
            "quest_description": assignment.quest.description,
            "classroom_id": str(assignment.class_id),
            "classroom_name": assignment.classroom.name,
            "due_at": assignment.due_at,
            "assigned_at": assignment.assigned_at,
            "points_override": assignment.points_override,
            "notes": assignment.notes,
            "status": progress.status,
            "completed_at": progress.completed_at,
        })

    return results


def get_classroom_assignment_progress(
    db: Session,
    assignment_id: UUID,
) -> dict:
    """
    Get progress statistics for a classroom assignment.

    Args:
        db: Database session
        assignment_id: Assignment ID

    Returns:
        Dictionary with progress statistics
    """
    assignment = db.execute(
        select(QuestAssignment).where(QuestAssignment.id == assignment_id)
        .options(
            selectinload(QuestAssignment.quest),
            selectinload(QuestAssignment.progress_entries),
        )
    ).scalar_one_or_none()

    if not assignment:
        raise ValueError("Assignment not found")

    total_students = len(assignment.progress_entries)
    assigned_count = sum(1 for p in assignment.progress_entries if p.status == "assigned")
    in_progress_count = sum(1 for p in assignment.progress_entries if p.status == "in_progress")
    completed_count = sum(1 for p in assignment.progress_entries if p.status == "completed")

    return {
        "assignment_id": str(assignment.id),
        "quest_name": assignment.quest.name,
        "total_students": total_students,
        "assigned": assigned_count,
        "in_progress": in_progress_count,
        "completed": completed_count,
        "completion_rate": (completed_count / total_students * 100) if total_students > 0 else 0,
        "due_at": assignment.due_at,
        "assigned_at": assignment.assigned_at,
    }


def update_assignment(
    db: Session,
    assignment_id: UUID,
    due_at: Optional[datetime] = None,
    points_override: Optional[int] = None,
    notes: Optional[str] = None,
) -> QuestAssignment:
    """
    Update an assignment.

    Args:
        db: Database session
        assignment_id: Assignment ID
        due_at: Optional due date
        points_override: Optional custom points
        notes: Optional teacher notes

    Returns:
        Updated QuestAssignment instance
    """
    assignment = db.get(QuestAssignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")

    if due_at is not None:
        assignment.due_at = due_at
    if points_override is not None:
        assignment.points_override = points_override
    if notes is not None:
        assignment.notes = notes

    db.commit()
    db.refresh(assignment)

    return assignment


def delete_assignment(
    db: Session,
    assignment_id: UUID,
) -> None:
    """
    Delete an assignment.
    This will cascade delete all progress entries.

    Args:
        db: Database session
        assignment_id: Assignment ID
    """
    assignment = db.get(QuestAssignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")

    db.delete(assignment)
    db.commit()


def submit_assignment(
    db: Session,
    assignment_id: UUID,
    user_id: UUID,
) -> AssignmentProgress:
    """
    Submit an assignment as completed.

    Args:
        db: Database session
        assignment_id: Assignment ID
        user_id: Student user ID

    Returns:
        Updated AssignmentProgress instance
    """
    progress = db.execute(
        select(AssignmentProgress).where(
            AssignmentProgress.assignment_id == assignment_id,
            AssignmentProgress.user_id == user_id
        )
    ).scalar_one_or_none()

    if not progress:
        raise ValueError("Assignment progress not found")

    if progress.status == "completed":
        raise ValueError("Assignment already completed")

    # Check if quest is actually completed
    assignment = db.get(QuestAssignment, assignment_id)
    quest_progress = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == user_id,
            QuestProgress.quest_id == assignment.quest_id
        )
    ).scalar_one_or_none()

    if not quest_progress or quest_progress.status != "completed":
        # Update status to in_progress
        progress.status = "in_progress"
    else:
        # Mark as completed
        progress.status = "completed"
        progress.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)

    return progress


