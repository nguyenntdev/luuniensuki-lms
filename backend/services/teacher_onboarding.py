# -*- coding: utf-8 -*-
"""Service implementation for Teacher Onboarding and Support Center (Ticket V5-T099 / W09-A09)."""
from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any, Optional
from uuid import UUID
import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..domain.teacher_onboarding import (
    OnboardingStep,
    SAMPLE_LESSON_TEMPLATES,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
    TEACHER_TRAINING_RESOURCES,
    UnverifiedTeacherAccessDeniedError,
    verify_teacher_school_access,
)
from ..history_models import HistoryLessonPlan
from ..models import School, SchoolMember, User, UserRole
from ..teacher_models import TeacherOnboardingProfile, TeacherSupportTicket


def get_or_create_teacher_onboarding_profile(
    db: Session, teacher: User
) -> TeacherOnboardingProfile:
    """Retrieve or initialize the teacher onboarding profile."""
    profile = db.execute(
        select(TeacherOnboardingProfile).where(
            TeacherOnboardingProfile.teacher_id == teacher.id
        )
    ).scalar_one_or_none()

    if profile is None:
        is_verified = getattr(teacher, "is_school_verified", True)
        profile = TeacherOnboardingProfile(
            id=uuid.uuid4(),
            teacher_id=teacher.id,
            school_id=teacher.school_id,
            is_school_verified=is_verified,
            current_step=OnboardingStep.welcome.value,
            completed_steps=[],
            is_completed=False,
            tour_dismissed=False,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        # Keep verified status in sync with user
        is_verified = getattr(teacher, "is_school_verified", True)
        if profile.is_school_verified != is_verified:
            profile.is_school_verified = is_verified
            db.commit()
            db.refresh(profile)

    return profile


def record_onboarding_step(
    db: Session, teacher: User, step: str, completed: bool = True
) -> TeacherOnboardingProfile:
    """Record an onboarding tour step as completed."""
    profile = get_or_create_teacher_onboarding_profile(db, teacher)

    steps = list(profile.completed_steps or [])
    if completed and step not in steps:
        steps.append(step)
    profile.completed_steps = steps
    profile.current_step = step

    if step == OnboardingStep.completed.value or len(steps) >= 5:
        profile.is_completed = True
        profile.completed_at = datetime.now(timezone.utc)
        teacher.teacher_onboarding_completed = True

    teacher.teacher_onboarding_step = step
    db.commit()
    db.refresh(profile)
    return profile


def complete_teacher_onboarding(
    db: Session, teacher: User
) -> TeacherOnboardingProfile:
    """Explicitly mark teacher onboarding tour as completed."""
    profile = get_or_create_teacher_onboarding_profile(db, teacher)
    profile.is_completed = True
    profile.completed_at = datetime.now(timezone.utc)
    profile.current_step = OnboardingStep.completed.value

    steps = list(profile.completed_steps or [])
    if OnboardingStep.completed.value not in steps:
        steps.append(OnboardingStep.completed.value)
    profile.completed_steps = steps

    teacher.teacher_onboarding_completed = True
    teacher.teacher_onboarding_step = OnboardingStep.completed.value
    db.commit()
    db.refresh(profile)
    return profile


def reset_teacher_onboarding(
    db: Session, teacher: User
) -> TeacherOnboardingProfile:
    """Reset onboarding state for re-training or demo restart."""
    profile = get_or_create_teacher_onboarding_profile(db, teacher)
    profile.is_completed = False
    profile.completed_at = None
    profile.completed_steps = []
    profile.current_step = OnboardingStep.welcome.value
    profile.tour_dismissed = False

    teacher.teacher_onboarding_completed = False
    teacher.teacher_onboarding_step = OnboardingStep.welcome.value
    db.commit()
    db.refresh(profile)
    return profile


def dismiss_teacher_tour(
    db: Session, teacher: User, dismiss: bool = True
) -> TeacherOnboardingProfile:
    """Dismiss or re-enable the interactive onboarding tour banner."""
    profile = get_or_create_teacher_onboarding_profile(db, teacher)
    profile.tour_dismissed = dismiss
    db.commit()
    db.refresh(profile)
    return profile


# --------------------------------------------------------------------------- #
# Sample Templates Service
# --------------------------------------------------------------------------- #

def get_sample_templates() -> list[dict[str, Any]]:
    """Return all verified sample lesson templates."""
    return SAMPLE_LESSON_TEMPLATES


def get_sample_template_by_id(template_id: str) -> Optional[dict[str, Any]]:
    """Find a specific sample template by ID."""
    for tmpl in SAMPLE_LESSON_TEMPLATES:
        if tmpl["id"] == template_id:
            return tmpl
    return None


def clone_sample_template_to_lesson_plan(
    db: Session, teacher: User, template_id: str
) -> HistoryLessonPlan:
    """Clone a verified sample template into an active draft lesson plan for the teacher."""
    tmpl = get_sample_template_by_id(template_id)
    if not tmpl:
        raise ValueError(f"Sample lesson template '{template_id}' not found.")

    plan_id = uuid.uuid4()
    plan = HistoryLessonPlan(
        id=plan_id,
        teacher_id=teacher.id,
        title=f"[Bản sao mẫu] {tmpl['title']}",
        topic=tmpl["topic"],
        target_grade=tmpl["target_grade"],
        duration_minutes=tmpl.get("duration_minutes", 45),
        curriculum_framework=tmpl.get("curriculum_framework", "CV 5512/BGDĐT"),
        status="draft",
        media_variant=tmpl.get("media_variant", "2d_rubbing"),
        objectives=tmpl["objectives"],
        inquiry_activities=tmpl["inquiry_activities"],
        assessment_rubric=tmpl["assessment_rubric"],
        media_config={"is_cloned_from_sample": True, "sample_template_id": template_id},
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# --------------------------------------------------------------------------- #
# Support Tickets Service
# --------------------------------------------------------------------------- #

def create_support_ticket(
    db: Session,
    teacher: User,
    subject: str,
    category: str,
    message: str,
    priority: str = "normal",
    school_id: Optional[UUID] = None,
) -> TeacherSupportTicket:
    """Create a new teacher support ticket with a generated unique ticket code."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m")
    suffix = secrets.token_hex(3).upper()
    ticket_code = f"TKT-{now_str}-{suffix}"

    ticket = TeacherSupportTicket(
        id=uuid.uuid4(),
        teacher_id=teacher.id,
        school_id=school_id or teacher.school_id,
        ticket_code=ticket_code,
        subject=subject,
        category=category,
        priority=priority,
        status=SupportTicketStatus.open.value,
        message=message,
        responses=[],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_support_tickets(
    db: Session,
    user: User,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> list[TeacherSupportTicket]:
    """List support tickets for the current teacher (or all for admin)."""
    query = select(TeacherSupportTicket)

    role_str = getattr(user.role, "value", str(user.role))
    if role_str not in ("admin", "super_admin"):
        query = query.where(TeacherSupportTicket.teacher_id == user.id)

    if status_filter:
        query = query.where(TeacherSupportTicket.status == status_filter)
    if category_filter:
        query = query.where(TeacherSupportTicket.category == category_filter)

    query = query.order_by(TeacherSupportTicket.created_at.desc())
    return list(db.execute(query).scalars().all())


def get_support_ticket(
    db: Session, user: User, ticket_id: UUID
) -> TeacherSupportTicket:
    """Retrieve ticket details with permission check."""
    ticket = db.get(TeacherSupportTicket, ticket_id)
    if not ticket:
        raise ValueError("Support ticket not found.")

    role_str = getattr(user.role, "value", str(user.role))
    if role_str not in ("admin", "super_admin") and ticket.teacher_id != user.id:
        raise PermissionError("Not authorized to view this support ticket.")

    return ticket


def add_support_ticket_reply(
    db: Session, user: User, ticket_id: UUID, message: str
) -> TeacherSupportTicket:
    """Add a reply to an existing support ticket."""
    ticket = get_support_ticket(db, user, ticket_id)

    role_str = getattr(user.role, "value", str(user.role))
    reply_entry = {
        "id": str(uuid.uuid4()),
        "author_id": str(user.id),
        "author_name": user.display_name,
        "author_role": role_str,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    current_responses = list(ticket.responses or [])
    current_responses.append(reply_entry)
    ticket.responses = current_responses

    if role_str in ("admin", "super_admin"):
        ticket.admin_response = message
        ticket.status = SupportTicketStatus.in_progress.value
    elif ticket.status == SupportTicketStatus.resolved.value:
        ticket.status = SupportTicketStatus.in_progress.value

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket


# --------------------------------------------------------------------------- #
# Teacher Training Resources Service
# --------------------------------------------------------------------------- #

def get_training_resources(category: Optional[str] = None) -> list[dict[str, Any]]:
    """List curated professional development and pedagogical training resources."""
    if not category:
        return TEACHER_TRAINING_RESOURCES
    return [r for r in TEACHER_TRAINING_RESOURCES if r.get("category") == category]


def get_training_resource_by_id(resource_id: str) -> Optional[dict[str, Any]]:
    """Find a specific training resource by ID."""
    for res in TEACHER_TRAINING_RESOURCES:
        if res["id"] == resource_id:
            return res
    return None
