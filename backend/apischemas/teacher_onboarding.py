# -*- coding: utf-8 -*-
"""Pydantic schemas for Teacher Onboarding and Support Center (Ticket V5-T099 / W09-A09)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeacherOnboardingProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    school_id: Optional[UUID] = None
    school_name: Optional[str] = None
    is_school_verified: bool = True
    mode: str = Field("verified", description="'demo' or 'verified'")
    current_step: str = "welcome"
    completed_steps: list[str] = Field(default_factory=list)
    is_completed: bool = False
    tour_dismissed: bool = False
    completed_at: Optional[datetime] = None
    verification_warning: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TeacherOnboardingStepIn(BaseModel):
    step: str = Field(..., description="Onboarding step key, e.g. welcome, sample_templates, etc.")
    completed: bool = True


class TeacherOnboardingDismissIn(BaseModel):
    dismiss: bool = True


class SampleLessonTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    topic: str
    target_grade: str
    duration_minutes: int
    curriculum_framework: str
    is_sample_template: bool = True
    template_badge: str = "SAMPLE TEMPLATE"
    disclaimer: str
    media_variant: str = "2d_rubbing"
    objectives: dict[str, Any] = Field(default_factory=dict)
    inquiry_activities: list[dict[str, Any]] = Field(default_factory=list)
    assessment_rubric: dict[str, Any] = Field(default_factory=dict)


class SampleLessonTemplateCloneOut(BaseModel):
    cloned_plan_id: UUID
    title: str
    topic: str
    status: str = "draft"
    message: str


class TeacherSupportTicketCreateIn(BaseModel):
    subject: str = Field(..., min_length=5, max_length=255)
    category: str = Field(
        ...,
        description="Category: pedagogical_guidance, curriculum_alignment, technical_issue, account_verification, rubric_scoring, student_privacy, other",
    )
    priority: str = Field("normal", description="Priority: low, normal, high, urgent")
    message: str = Field(..., min_length=10)
    school_id: Optional[UUID] = None


class TeacherSupportTicketReplyIn(BaseModel):
    message: str = Field(..., min_length=3)


class TeacherSupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_code: str
    teacher_id: UUID
    teacher_name: str
    school_id: Optional[UUID] = None
    school_name: Optional[str] = None
    subject: str
    category: str
    priority: str
    status: str
    message: str
    admin_response: Optional[str] = None
    responses: list[dict[str, Any]] = Field(default_factory=list)
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TeacherTrainingResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    duration_minutes: int
    format: str
    category: str
    is_mandatory_for_verification: bool
    summary: str
    resource_url: str
