# -*- coding: utf-8 -*-
"""API router for Teacher Onboarding and Support Center (Ticket V5-T099 / W09-A09)."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..apischemas.teacher_onboarding import (
    SampleLessonTemplateCloneOut,
    SampleLessonTemplateOut,
    TeacherOnboardingDismissIn,
    TeacherOnboardingProfileOut,
    TeacherOnboardingStepIn,
    TeacherSupportTicketCreateIn,
    TeacherSupportTicketOut,
    TeacherSupportTicketReplyIn,
    TeacherTrainingResourceOut,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..models import School, User, UserRole
from ..services import teacher_onboarding as teacher_service

router = APIRouter(prefix="/api/v1/teacher", tags=["teacher_onboarding_support"])


def _build_profile_out(db: Session, teacher: User, profile: Any) -> TeacherOnboardingProfileOut:
    school_name = None
    if teacher.school_id:
        sch = db.get(School, teacher.school_id)
        if sch:
            school_name = sch.name

    is_verified = bool(getattr(teacher, "is_school_verified", True))
    mode = "verified" if is_verified else "demo"
    warning = (
        None
        if is_verified
        else "Tài khoản giáo viên chưa được nhà trường xác thực. Chế độ dùng thử (Demo Mode) đang kích hoạt: Không thể xem dữ liệu PII học sinh thật hoặc hồ sơ lớp học trực tiếp."
    )

    return TeacherOnboardingProfileOut(
        id=profile.id,
        teacher_id=profile.teacher_id,
        school_id=profile.school_id,
        school_name=school_name,
        is_school_verified=is_verified,
        mode=mode,
        current_step=profile.current_step,
        completed_steps=profile.completed_steps or [],
        is_completed=profile.is_completed,
        tour_dismissed=profile.tour_dismissed,
        completed_at=profile.completed_at,
        verification_warning=warning,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _build_ticket_out(db: Session, ticket: Any) -> TeacherSupportTicketOut:
    teacher = db.get(User, ticket.teacher_id)
    teacher_name = teacher.display_name if teacher else "Giáo viên"
    school_name = None
    if ticket.school_id:
        sch = db.get(School, ticket.school_id)
        if sch:
            school_name = sch.name

    return TeacherSupportTicketOut(
        id=ticket.id,
        ticket_code=ticket.ticket_code,
        teacher_id=ticket.teacher_id,
        teacher_name=teacher_name,
        school_id=ticket.school_id,
        school_name=school_name,
        subject=ticket.subject,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        message=ticket.message,
        admin_response=ticket.admin_response,
        responses=ticket.responses or [],
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


# --------------------------------------------------------------------------- #
# Onboarding Tour Endpoints
# --------------------------------------------------------------------------- #

@router.get("/onboarding/profile", response_model=TeacherOnboardingProfileOut)
def get_teacher_onboarding_profile(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Retrieve teacher onboarding profile, school verification status, and demo mode."""
    profile = teacher_service.get_or_create_teacher_onboarding_profile(db, current_user)
    return _build_profile_out(db, current_user, profile)


@router.post("/onboarding/step", response_model=TeacherOnboardingProfileOut)
def record_teacher_onboarding_step(
    payload: TeacherOnboardingStepIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Record an onboarding tour step completion."""
    profile = teacher_service.record_onboarding_step(
        db, current_user, payload.step, payload.completed
    )
    return _build_profile_out(db, current_user, profile)


@router.post("/onboarding/complete", response_model=TeacherOnboardingProfileOut)
def complete_teacher_onboarding(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Mark onboarding tour as completely finished."""
    profile = teacher_service.complete_teacher_onboarding(db, current_user)
    return _build_profile_out(db, current_user, profile)


@router.post("/onboarding/reset", response_model=TeacherOnboardingProfileOut)
def reset_teacher_onboarding(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Reset onboarding tour progress for re-training or demo restart."""
    profile = teacher_service.reset_teacher_onboarding(db, current_user)
    return _build_profile_out(db, current_user, profile)


@router.post("/onboarding/dismiss", response_model=TeacherOnboardingProfileOut)
def dismiss_teacher_tour(
    payload: TeacherOnboardingDismissIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Dismiss or re-enable the interactive onboarding tour banner."""
    profile = teacher_service.dismiss_teacher_tour(db, current_user, payload.dismiss)
    return _build_profile_out(db, current_user, profile)


# --------------------------------------------------------------------------- #
# Sample Lesson Templates Endpoints
# --------------------------------------------------------------------------- #

@router.get("/sample-templates", response_model=list[SampleLessonTemplateOut])
def list_sample_templates(
    current_user: User = Depends(get_current_user),
):
    """List verified sample lesson templates clearly marked as 'SAMPLE TEMPLATE'."""
    return teacher_service.get_sample_templates()


@router.get("/sample-templates/{template_id}", response_model=SampleLessonTemplateOut)
def get_sample_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a specific sample lesson template."""
    tmpl = teacher_service.get_sample_template_by_id(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample lesson template '{template_id}' not found.",
        )
    return tmpl


@router.post(
    "/sample-templates/{template_id}/clone",
    response_model=SampleLessonTemplateCloneOut,
    status_code=status.HTTP_201_CREATED,
)
def clone_sample_template(
    template_id: str,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Clone a verified sample template into an editable personal draft lesson plan."""
    try:
        plan = teacher_service.clone_sample_template_to_lesson_plan(
            db, current_user, template_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return SampleLessonTemplateCloneOut(
        cloned_plan_id=plan.id,
        title=plan.title,
        topic=plan.topic,
        status=plan.status,
        message="Sao chép giáo án mẫu thành công thành bản thảo cá nhân.",
    )


# --------------------------------------------------------------------------- #
# Teacher Training Resources Endpoints
# --------------------------------------------------------------------------- #

@router.get("/training/resources", response_model=list[TeacherTrainingResourceOut])
def list_training_resources(
    category: Optional[str] = Query(None, description="Filter by training category"),
    current_user: User = Depends(get_current_user),
):
    """List curated professional development and teacher training resources."""
    return teacher_service.get_training_resources(category=category)


@router.get("/training/resources/{resource_id}", response_model=TeacherTrainingResourceOut)
def get_training_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a specific teacher training resource."""
    res = teacher_service.get_training_resource_by_id(resource_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training resource '{resource_id}' not found.",
        )
    return res


# --------------------------------------------------------------------------- #
# Support Tickets Endpoints
# --------------------------------------------------------------------------- #

@router.post(
    "/support/tickets",
    response_model=TeacherSupportTicketOut,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    payload: TeacherSupportTicketCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Submit a teacher support ticket for pedagogical, technical, curriculum, or verification help."""
    ticket = teacher_service.create_support_ticket(
        db=db,
        teacher=current_user,
        subject=payload.subject,
        category=payload.category,
        message=payload.message,
        priority=payload.priority,
        school_id=payload.school_id,
    )
    return _build_ticket_out(db, ticket)


@router.get("/support/tickets", response_model=list[TeacherSupportTicketOut])
def list_support_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """List submitted support tickets."""
    tickets = teacher_service.list_support_tickets(
        db=db,
        user=current_user,
        status_filter=status_filter,
        category_filter=category_filter,
    )
    return [_build_ticket_out(db, t) for t in tickets]


@router.get("/support/tickets/{ticket_id}", response_model=TeacherSupportTicketOut)
def get_support_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific support ticket."""
    try:
        ticket = teacher_service.get_support_ticket(db, current_user, ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return _build_ticket_out(db, ticket)


@router.post("/support/tickets/{ticket_id}/reply", response_model=TeacherSupportTicketOut)
def reply_support_ticket(
    ticket_id: UUID,
    payload: TeacherSupportTicketReplyIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """Add a follow-up reply or teacher comment to an existing support ticket."""
    try:
        ticket = teacher_service.add_support_ticket_reply(
            db=db, user=current_user, ticket_id=ticket_id, message=payload.message
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return _build_ticket_out(db, ticket)
