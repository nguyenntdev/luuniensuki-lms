"""
Classroom Service for managing teacher classrooms and student enrollment.

This service handles:
- Generating unique class codes
- Managing student enrollment
- Archiving/unarchiving classrooms
- Classroom CRUD operations
"""

from __future__ import annotations

import random
import string
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..models import Classroom, ClassMember, User, UserRole


def generate_unique_class_code(db: Session, length: int = 8) -> str:
    """
    Generate a unique class code for joining classrooms.
    
    Args:
        db: Database session
        length: Length of the code (default: 8)
        
    Returns:
        Unique class code
    """
    # Use uppercase letters and numbers, excluding similar-looking characters
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    
    max_attempts = 100
    for _ in range(max_attempts):
        code = ''.join(random.choice(chars) for _ in range(length))
        
        # Check if code already exists
        existing = db.execute(
            select(Classroom).where(Classroom.class_code == code)
        ).scalar_one_or_none()
        
        if existing is None:
            return code
    
    raise ValueError("Failed to generate unique class code after multiple attempts")


def create_classroom(
    db: Session,
    teacher: User,
    name: str,
    description: Optional[str] = None,
    max_students: Optional[int] = None,
    settings: Optional[dict] = None,
) -> Classroom:
    """
    Create a new classroom.
    
    Args:
        db: Database session
        teacher: The teacher creating the classroom
        name: Classroom name
        description: Classroom description
        max_students: Maximum number of students allowed
        settings: Additional classroom settings
        
    Returns:
        Created Classroom instance
    """
    class_code = generate_unique_class_code(db)
    
    classroom = Classroom(
        name=name,
        description=description,
        teacher_id=teacher.id,
        class_code=class_code,
        max_students=max_students,
        is_archived=False,
        settings=settings or {},
    )
    
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return classroom


def update_classroom(
    db: Session,
    classroom: Classroom,
    name: Optional[str] = None,
    description: Optional[str] = None,
    max_students: Optional[int] = None,
    settings: Optional[dict] = None,
) -> Classroom:
    """
    Update classroom details.
    
    Args:
        db: Database session
        classroom: Classroom to update
        name: New classroom name
        description: New description
        max_students: New max students limit
        settings: New settings
        
    Returns:
        Updated Classroom instance
    """
    if name is not None:
        classroom.name = name
    if description is not None:
        classroom.description = description
    if max_students is not None:
        classroom.max_students = max_students
    if settings is not None:
        classroom.settings = settings
    
    classroom.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(classroom)
    
    return classroom


def archive_classroom(db: Session, classroom: Classroom) -> Classroom:
    """
    Archive a classroom.
    
    Args:
        db: Database session
        classroom: Classroom to archive
        
    Returns:
        Archived Classroom instance
    """
    classroom.is_archived = True
    classroom.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(classroom)
    
    return classroom


def unarchive_classroom(db: Session, classroom: Classroom) -> Classroom:
    """
    Unarchive a classroom.

    Args:
        db: Database session
        classroom: Classroom to unarchive

    Returns:
        Unarchived Classroom instance
    """
    classroom.is_archived = False
    classroom.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(classroom)

    return classroom


def join_classroom_by_code(
    db: Session,
    user: User,
    class_code: str,
) -> tuple[Classroom, ClassMember]:
    """
    Join a classroom using a class code.

    Args:
        db: Database session
        user: User joining the classroom
        class_code: Classroom code

    Returns:
        Tuple of (Classroom, ClassMember)

    Raises:
        ValueError: If classroom not found, archived, or full
    """
    # Find classroom by code
    classroom = db.execute(
        select(Classroom).where(Classroom.class_code == class_code.upper())
    ).scalar_one_or_none()

    if classroom is None:
        raise ValueError("Classroom not found with this code")

    if classroom.is_archived:
        raise ValueError("This classroom is archived and cannot accept new students")

    # Check if already a member
    existing_member = db.execute(
        select(ClassMember).where(
            and_(
                ClassMember.class_id == classroom.id,
                ClassMember.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if existing_member:
        return classroom, existing_member

    # Check max students limit
    if classroom.max_students is not None:
        current_count = db.execute(
            select(func.count(ClassMember.id)).where(
                ClassMember.class_id == classroom.id
            )
        ).scalar_one()

        if current_count >= classroom.max_students:
            raise ValueError("This classroom has reached its maximum student capacity")

    # Create new membership
    member = ClassMember(
        class_id=classroom.id,
        user_id=user.id,
        role="learner",
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return classroom, member


def remove_class_member(
    db: Session,
    classroom: Classroom,
    member_id: UUID,
) -> None:
    """
    Remove a member from a classroom.

    Args:
        db: Database session
        classroom: Classroom to remove member from
        member_id: ID of the ClassMember to remove

    Raises:
        ValueError: If member not found
    """
    member = db.execute(
        select(ClassMember).where(
            and_(
                ClassMember.id == member_id,
                ClassMember.class_id == classroom.id,
            )
        )
    ).scalar_one_or_none()

    if member is None:
        raise ValueError("Member not found in this classroom")

    db.delete(member)
    db.commit()


def get_enrolled_classrooms(db: Session, user: User) -> list[Classroom]:
    """
    Get all classrooms where the user is enrolled as a student.

    Args:
        db: Database session
        user: User to get enrollments for

    Returns:
        List of Classroom instances
    """
    classrooms = db.execute(
        select(Classroom)
        .join(ClassMember, ClassMember.class_id == Classroom.id)
        .where(
            and_(
                ClassMember.user_id == user.id,
                ClassMember.role == "learner",
            )
        )
        .order_by(Classroom.created_at.desc())
    ).scalars().all()

    return list(classrooms)


def get_classroom_member_count(db: Session, classroom_id: UUID) -> int:
    """
    Get the number of members in a classroom.

    Args:
        db: Database session
        classroom_id: Classroom ID

    Returns:
        Number of members
    """
    count = db.execute(
        select(func.count(ClassMember.id)).where(
            ClassMember.class_id == classroom_id
        )
    ).scalar_one()

    return count

