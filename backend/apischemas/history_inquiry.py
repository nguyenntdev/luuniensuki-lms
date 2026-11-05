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
    comparative_links: list[ComparativeLinkOut] = Field(default_factory=list)
    inline_feedback: list[TeacherInlineFeedbackOut] = Field(default_factory=list)
    revision_cycle: int = 1
    revision_history: list[dict[str, Any]] = Field(default_factory=list)
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


class ComparativeLinkCreate(BaseModel):
    source_id_a: UUID
    source_id_b: Optional[UUID] = None
    claim_id: Optional[UUID] = None
    relation_type: str = Field(
        ...,
        pattern="^(supports|refutes|corroborates|contrasts|qualifies)$",
        description="Comparative relationship type between sources or claim",
    )
    rationale: str = Field(..., min_length=1, max_length=2000)


class ComparativeLinkOut(BaseModel):
    id: str
    source_id_a: str
    source_title_a: str
    source_id_b: Optional[str] = None
    source_title_b: Optional[str] = None
    claim_id: Optional[str] = None
    claim_title: Optional[str] = None
    relation_type: str
    rationale: str
    created_by_user_id: str
    created_by_name: str
    created_at: str


class TeacherInlineFeedbackCreate(BaseModel):
    target_type: str = Field(
        default="card",
        pattern="^(card|comparison|hypothesis|synthesis|board)$",
    )
    target_id: Optional[str] = None
    comment: str = Field(..., min_length=1, max_length=3000)


class TeacherInlineFeedbackOut(BaseModel):
    id: str
    target_type: str
    target_id: Optional[str] = None
    teacher_id: str
    teacher_name: str
    comment: str
    created_at: str
    resolved: bool = False


class InquiryBoardCardCreate(BaseModel):
    source_id: UUID
    locator: str = Field(..., min_length=1, max_length=255)
    excerpt: str = Field(..., min_length=1, max_length=5000)
    claim_id: Optional[UUID] = None
    support_type: str = Field(
        default="supports",
        pattern="^(supports|refutes|inconclusive|disputed)$",
    )
    board_column: Optional[str] = Field(
        default=None,
        pattern="^(supporting|refuting|synthesis|unresolved)$",
    )
    position: Optional[int] = 0
    linked_evidence_id: Optional[str] = None
    comparison_notes: Optional[str] = None
    interpretation_note: str = Field(..., min_length=1, max_length=2000)


class InquiryBoardCardUpdate(BaseModel):
    support_type: Optional[str] = Field(
        default=None,
        pattern="^(supports|refutes|inconclusive|disputed)$",
    )
    board_column: Optional[str] = Field(
        default=None,
        pattern="^(supporting|refuting|synthesis|unresolved)$",
    )
    position: Optional[int] = None
    linked_evidence_id: Optional[str] = None
    comparison_notes: Optional[str] = None
    interpretation_note: Optional[str] = None
    locator: Optional[str] = None
    excerpt: Optional[str] = None


class InquiryBoardCardOut(BaseModel):
    id: str
    source_id: str
    source_title: str
    author: Optional[str] = None
    locator: str
    excerpt: str
    claim_id: Optional[str] = None
    claim_title: Optional[str] = None
    support_type: str
    board_column: str
    position: int
    linked_evidence_id: Optional[str] = None
    comparison_notes: Optional[str] = None
    inline_feedback: list[TeacherInlineFeedbackOut] = Field(default_factory=list)
    interpretation_note: str
    contributed_by_user_id: str
    contributed_by_name: str
    contributed_at: str


class InquiryBoardOut(BaseModel):
    group_id: UUID
    group_name: str
    activity_id: UUID
    activity_title: str
    hypothesis: str
    synthesis_argument: str
    epistemic_rating: str
    status: str
    privacy_mode: str
    revision_cycle: int
    version: int
    columns: list[str] = Field(
        default_factory=lambda: ["supporting", "refuting", "synthesis", "unresolved"]
    )
    cards: list[InquiryBoardCardOut] = Field(default_factory=list)
    comparative_links: list[ComparativeLinkOut] = Field(default_factory=list)
    inline_feedback: list[TeacherInlineFeedbackOut] = Field(default_factory=list)
    revision_history: list[dict[str, Any]] = Field(default_factory=list)
    teacher_feedback: Optional[str] = None
    score: Optional[float] = None
    rubric_evaluation: Optional[dict[str, Any]] = None
    updated_at: datetime


class BoardRequestRevisionIn(BaseModel):
    teacher_feedback: str = Field(..., min_length=1)
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    rubric_evaluation: Optional[dict[str, Any]] = None
    revision_notes: Optional[str] = None


class BoardResubmitIn(BaseModel):
    revision_notes: Optional[str] = Field(default="", max_length=2000)


class RevisionCycleOut(BaseModel):
    group_id: UUID
    revision_cycle: int
    status: str
    history: list[dict[str, Any]] = Field(default_factory=list)


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
