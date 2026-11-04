# -*- coding: utf-8 -*-
"""Pydantic schemas for Peer / Group Historical Inquiry (V5-T038).

Covers collaborative source evidence synthesis, teacher moderation, and
privacy isolation for historical inquiry activities.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InquiryEvidenceItemIn(BaseModel):
    source_id: UUID
    locator: str = Field(..., min_length=1, max_length=255)
    excerpt: str = Field(..., min_length=1, max_length=5000)
    claim_id: Optional[UUID] = None
    support_type: str = Field(default="supports")
    interpretation_note: str = Field(..., min_length=1, max_length=2000)


class InquiryEvidenceItemOut(BaseModel):
    id: str
    source_id: str
    source_title: str
    author: Optional[str] = None
    locator: str
    excerpt: str
    claim_id: Optional[str] = None
    claim_title: Optional[str] = None
    support_type: str
    interpretation_note: str
    contributed_by_user_id: str
    contributed_by_name: str
    contributed_at: str


class HistoricalInquiryActivityCreate(BaseModel):
    classroom_id: Optional[UUID] = None
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    guiding_questions: list[str] = Field(default_factory=list)
    suggested_source_ids: list[UUID] = Field(default_factory=list)
    suggested_claim_ids: list[UUID] = Field(default_factory=list)
    rubric_criteria: Optional[dict[str, Any]] = None
    due_at: Optional[datetime] = None
    is_active: bool = True


class HistoricalInquiryActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    classroom_id: Optional[UUID] = None
    title: str
    description: str
    guiding_questions: list[str] = Field(default_factory=list)
    suggested_source_ids: list[UUID] = Field(default_factory=list)
    suggested_claim_ids: list[UUID] = Field(default_factory=list)
    rubric_criteria: Optional[dict[str, Any]] = None
    created_by_id: UUID
    due_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    groups_count: int = 0


class HistoricalInquiryGroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    member_ids: Optional[list[UUID]] = None


class HistoricalInquiryGroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    display_name: Optional[str] = None
    username: Optional[str] = None
    role: str
    joined_at: datetime


class HistoricalInquiryGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    classroom_id: Optional[UUID] = None
    name: str
    created_by_id: UUID
    members: list[HistoricalInquiryGroupMemberOut] = Field(default_factory=list)
    submission_status: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime


class HistoricalInquirySubmissionUpdate(BaseModel):
    hypothesis: Optional[str] = None
    synthesis_argument: Optional[str] = None
    epistemic_rating: Optional[str] = None
    privacy_mode: Optional[str] = None


class HistoricalInquirySubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    activity_id: UUID
    hypothesis: str
    synthesis_argument: str
    epistemic_rating: str
    evidence_items: list[InquiryEvidenceItemOut] = Field(default_factory=list)
    status: str
    privacy_mode: str
    submitted_at: Optional[datetime] = None
    submitted_by_id: Optional[UUID] = None
    moderated_by_id: Optional[UUID] = None
    moderated_at: Optional[datetime] = None
    teacher_feedback: Optional[str] = None
    score: Optional[float] = None
    rubric_evaluation: Optional[dict[str, Any]] = None
    version: int
    created_at: datetime
    updated_at: datetime


class HistoricalInquiryTeacherModerationIn(BaseModel):
    status: str = Field(..., pattern="^(approved|revision_requested)$")
    teacher_feedback: str = Field(..., min_length=1)
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    rubric_evaluation: Optional[dict[str, Any]] = None


class HistoricalInquiryTeacherModerationOut(BaseModel):
    submission_id: UUID
    status: str
    score: Optional[float]
    teacher_feedback: str
    rubric_evaluation: Optional[dict[str, Any]] = None
    moderated_at: datetime
    moderated_by_id: UUID


class AddGroupMemberIn(BaseModel):
    user_id: UUID
    role: str = Field(default="contributor", pattern="^(leader|contributor)$")
