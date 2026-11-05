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
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from ..models import Classroom, ClassMember, School, SchoolMember, User, UserRole


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
    school_id: Optional[UUID] = None,
    term: Optional[str] = None,
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
        school_id: Optional UUID of the associated school
        term: Optional term/academic period (e.g. '2025-2026-HK1')
        
    Returns:
        Created Classroom instance
    """
    if school_id:
        school = db.get(School, school_id)
        if not school:
            raise ValueError("School not found")

    class_code = generate_unique_class_code(db)
    
    classroom = Classroom(
        name=name,
        description=description,
        teacher_id=teacher.id,
        school_id=school_id or teacher.school_id,
        term=term,
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
    school_id: Optional[UUID] = None,
    term: Optional[str] = None,
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
        school_id: New school UUID
        term: New term string
        
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
    if school_id is not None:
        school = db.get(School, school_id)
        if not school:
            raise ValueError("School not found")
        classroom.school_id = school_id
    if term is not None:
        classroom.term = term
    
    classroom.updated_at = datetime.now(timezone.utc)
    
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
    guardian_email: Optional[str] = None,
    guardian_consent: Optional[bool] = None,
    guardian_user_id: Optional[UUID] = None,
) -> tuple[Classroom, ClassMember]:
    """
    Join a classroom using a class code.

    Args:
        db: Database session
        user: User joining the classroom
        class_code: Classroom code
        guardian_email: Optional guardian email for adult guardian consent flow
        guardian_consent: Optional boolean indicating guardian consent
        guardian_user_id: Optional UUID of guardian User account

    Returns:
        Tuple of (Classroom, ClassMember)

    Raises:
        ValueError: If code invalid, classroom not found, archived, or full
    """
    if not class_code or not class_code.strip():
        raise ValueError("Class code must not be empty")

    normalized_code = class_code.strip().upper()

    # Find classroom by code
    classroom = db.execute(
        select(Classroom).where(Classroom.class_code == normalized_code)
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
        if guardian_email and not existing_member.guardian_email:
            existing_member.guardian_email = guardian_email
        if guardian_consent is not None:
            existing_member.guardian_consent = bool(guardian_consent)
        if guardian_user_id and not existing_member.guardian_user_id:
            existing_member.guardian_user_id = guardian_user_id
        db.commit()
        db.refresh(existing_member)
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
        guardian_email=guardian_email,
        guardian_consent=bool(guardian_consent) if guardian_consent is not None else False,
        guardian_user_id=guardian_user_id,
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


# =============================================================================
# School Service Functions
# =============================================================================


def create_school(
    db: Session,
    name: str,
    code: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    settings: Optional[dict] = None,
) -> School:
    """Create a new school entity."""
    if not name or not name.strip():
        raise ValueError("School name must not be empty")

    normalized_code = code.strip().upper() if code else None
    if normalized_code:
        existing = db.execute(
            select(School).where(School.code == normalized_code)
        ).scalar_one_or_none()
        if existing:
            raise ValueError(f"School with code '{normalized_code}' already exists")

    school = School(
        name=name.strip(),
        code=normalized_code,
        address=address.strip() if address else None,
        city=city.strip() if city else None,
        region=region.strip() if region else None,
        is_active=True,
        settings=settings or {},
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def get_school(db: Session, school_id: UUID) -> Optional[School]:
    """Retrieve school by ID."""
    return db.get(School, school_id)


def list_schools(
    db: Session,
    city: Optional[str] = None,
    is_active: Optional[bool] = True,
    limit: int = 50,
    offset: int = 0,
) -> list[School]:
    """List schools with optional filters."""
    query = select(School)
    if is_active is not None:
        query = query.where(School.is_active == is_active)
    if city:
        query = query.where(School.city.ilike(f"%{city}%"))
    query = query.order_by(School.name.asc()).offset(offset).limit(limit)
    return list(db.execute(query).scalars().all())


def update_school(
    db: Session,
    school: School,
    name: Optional[str] = None,
    code: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    is_active: Optional[bool] = None,
    settings: Optional[dict] = None,
) -> School:
    """Update school attributes."""
    if name is not None:
        if not name.strip():
            raise ValueError("School name cannot be empty")
        school.name = name.strip()
    if code is not None:
        normalized_code = code.strip().upper() if code else None
        if normalized_code:
            existing = db.execute(
                select(School).where(
                    and_(School.code == normalized_code, School.id != school.id)
                )
            ).scalar_one_or_none()
            if existing:
                raise ValueError(f"School with code '{normalized_code}' already exists")
        school.code = normalized_code
    if address is not None:
        school.address = address.strip() if address else None
    if city is not None:
        school.city = city.strip() if city else None
    if region is not None:
        school.region = region.strip() if region else None
    if is_active is not None:
        school.is_active = is_active
    if settings is not None:
        school.settings = settings

    school.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(school)
    return school


def add_school_member(
    db: Session,
    school_id: UUID,
    user_id: UUID,
    role: str = "teacher",
) -> SchoolMember:
    """Add or update a teacher or member in a school."""
    school = db.get(School, school_id)
    if not school:
        raise ValueError("School not found")
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    existing = db.execute(
        select(SchoolMember).where(
            and_(SchoolMember.school_id == school_id, SchoolMember.user_id == user_id)
        )
    ).scalar_one_or_none()

    if existing:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    member = SchoolMember(
        school_id=school_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    if not user.school_id:
        user.school_id = school_id
    db.commit()
    db.refresh(member)
    return member


def get_school_classrooms(
    db: Session,
    school_id: UUID,
    include_archived: bool = False,
) -> list[Classroom]:
    """Get all classrooms belonging to a school."""
    query = select(Classroom).where(Classroom.school_id == school_id)
    if not include_archived:
        query = query.where(Classroom.is_archived == False)
    return list(db.execute(query.order_by(Classroom.created_at.desc())).scalars().all())


def get_classroom_roster(
    db: Session,
    classroom: Classroom,
    viewer: User,
) -> list[dict]:
    """
    Get the student roster for a classroom with strict authorization checks.
    
    Authorization:
    - Admin or super_admin: full details
    - Classroom teacher: full details
    - Enrolled student: peer list with PII redacted
    - External student or non-associated user: PermissionError
    """
    role_str = getattr(viewer.role, "value", str(viewer.role))
    if role_str == "guest":
        raise PermissionError("UNVERIFIED_TEACHER_ACCESS_DENIED: Guest teachers cannot access real student PII or live class records.")

    is_admin = viewer.role in (UserRole.admin, UserRole.super_admin)
    is_teacher = (viewer.role == UserRole.teacher and classroom.teacher_id == viewer.id)

    if is_teacher:
        is_verified = bool(getattr(viewer, "is_school_verified", True))
        if classroom.school_id:
            sm = db.execute(
                select(SchoolMember).where(
                    and_(
                        SchoolMember.school_id == classroom.school_id,
                        SchoolMember.user_id == viewer.id,
                    )
                )
            ).scalar_one_or_none()
            if sm and (
                getattr(sm, "is_verified", True) is False
                or getattr(sm, "verification_status", "verified") in ("unverified", "pending", "rejected")
            ):
                is_verified = False
        if not is_verified:
            raise PermissionError(
                "UNVERIFIED_TEACHER_ACCESS_DENIED: Unverified school users cannot access real student PII or live class records."
            )

    enrolled = db.execute(
        select(ClassMember).where(
            and_(ClassMember.class_id == classroom.id, ClassMember.user_id == viewer.id)
        )
    ).scalar_one_or_none()

    if not (is_admin or is_teacher or enrolled):
        raise PermissionError("Not authorized to access classroom roster")

    members = db.execute(
        select(ClassMember)
        .options(selectinload(ClassMember.user))
        .where(ClassMember.class_id == classroom.id)
        .order_by(ClassMember.joined_at.asc())
    ).scalars().all()

    can_view_pii = is_admin or is_teacher
    roster = []
    for m in members:
        user = m.user
        roster.append({
            "id": m.id,
            "user_id": m.user_id,
            "display_name": user.display_name if user else "Unknown",
            "email": user.email if (can_view_pii or m.user_id == viewer.id) else None,
            "role": m.role,
            "joined_at": m.joined_at,
            "guardian_email": m.guardian_email if (can_view_pii or m.user_id == viewer.id) else None,
            "guardian_consent": m.guardian_consent if (can_view_pii or m.user_id == viewer.id) else None,
        })
    return roster

