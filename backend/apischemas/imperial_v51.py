# -*- coding: utf-8 -*-
"""Pydantic v2 schemas for STTTNNĐ (Lưu Niên — Đại Nội Huế) V5.1 modules.

DTOs for:
- Learning Media & Media Hotspots (image, panorama360, model3d, UV coordinates)
- Art Details, Claim Sources, Art Detail Questions with story types
- Heritage Detective Clues & Attempts
- Interactive Questions & Game Submissions (with answer_key hidden in public schemas)
- Teacher Assignment Releases
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImperialV51BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --------------------------------------------------------------------------- #
# 1. Media Hotspots & Learning Media
# --------------------------------------------------------------------------- #
class ImperialLearningMediaBase(ImperialV51BaseSchema):
    kind: Literal["image", "panorama360", "model3d"] = "image"
    media_url: str = Field(..., min_length=1, max_length=1000)
    thumbnail_url: Optional[str] = Field(default=None, max_length=1000)
    asset_revision: int = Field(default=1, ge=1)
    width_px: Optional[int] = Field(default=None, ge=1)
    height_px: Optional[int] = Field(default=None, ge=1)
    license_status: Literal["pending", "approved", "rejected"] = "pending"
    review_status: Literal["draft", "in_review", "approved", "published", "archived"] = "draft"
    alt_text: Optional[str] = None
    credit_text: Optional[str] = None
    asset_context: Literal["extant", "historical_photo", "restoration_drawing"] = "extant"


class ImperialLearningMediaCreate(ImperialLearningMediaBase):
    site_id: UUID


class ImperialLearningMediaUpdate(ImperialV51BaseSchema):
    kind: Optional[Literal["image", "panorama360", "model3d"]] = None
    media_url: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    thumbnail_url: Optional[str] = Field(default=None, max_length=1000)
    asset_revision: Optional[int] = Field(default=None, ge=1)
    width_px: Optional[int] = Field(default=None, ge=1)
    height_px: Optional[int] = Field(default=None, ge=1)
    license_status: Optional[Literal["pending", "approved", "rejected"]] = None
    review_status: Optional[Literal["draft", "in_review", "approved", "published", "archived"]] = None
    alt_text: Optional[str] = None
    credit_text: Optional[str] = None
    asset_context: Optional[Literal["extant", "historical_photo", "restoration_drawing"]] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialMediaHotspotBase(ImperialV51BaseSchema):
    point_kind: Literal["point", "rect", "polygon"] = "point"
    u: float = Field(..., ge=0.0, le=1.0)
    v: float = Field(..., ge=0.0, le=1.0)
    position_payload: Optional[dict[str, Any]] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    detail_id: Optional[UUID] = None
    review_status: Literal["draft", "in_review", "approved", "published", "archived"] = "draft"


class ImperialMediaHotspotCreate(ImperialMediaHotspotBase):
    media_id: Optional[UUID] = None


class ImperialMediaHotspotUpdate(ImperialV51BaseSchema):
    point_kind: Optional[Literal["point", "rect", "polygon"]] = None
    u: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    v: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    position_payload: Optional[dict[str, Any]] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    detail_id: Optional[UUID] = None
    review_status: Optional[Literal["draft", "in_review", "approved", "published", "archived"]] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialMediaHotspotOut(ImperialMediaHotspotBase):
    id: UUID
    media_id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
    art_detail: Optional[ImperialArtDetailSummary] = None


class ImperialLearningMediaOut(ImperialLearningMediaBase):
    id: UUID
    site_id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
    hotspots: list[ImperialMediaHotspotOut] = []


# --------------------------------------------------------------------------- #
# 2. Art Details, Claims & Detail Questions
# --------------------------------------------------------------------------- #
class ImperialArtDetailClaimSourceBase(ImperialV51BaseSchema):
    section: str = Field(..., min_length=1, max_length=100)
    claim_text: str = Field(..., min_length=1)
    source_title: str = Field(..., min_length=1, max_length=255)
    source_locator: Optional[str] = Field(default=None, max_length=255)
    evidence_strength: Literal["verified", "probable", "traditional"] = "verified"


class ImperialArtDetailClaimSourceCreate(ImperialArtDetailClaimSourceBase):
    detail_id: Optional[UUID] = None


class ImperialArtDetailClaimSourceOut(ImperialArtDetailClaimSourceBase):
    id: UUID
    detail_id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime


class ImperialArtDetailQuestionBase(ImperialV51BaseSchema):
    question_type: str = Field(default="multiple_choice", max_length=50)
    prompt: str = Field(..., min_length=1)
    options: list[Any] = []
    answer_key: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    display_order: int = Field(default=0, ge=0)


class ImperialArtDetailQuestionCreate(ImperialArtDetailQuestionBase):
    detail_id: Optional[UUID] = None


class ImperialArtDetailQuestionOut(ImperialV51BaseSchema):
    id: UUID
    detail_id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    question_type: str
    prompt: str
    options: list[Any]
    explanation: Optional[str] = None
    display_order: int
    created_at: datetime
    updated_at: datetime


class ImperialArtDetailBase(ImperialV51BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    kind: Literal["carving", "pattern", "painting", "mosaic", "relief"] = "carving"
    motif: Optional[str] = Field(default=None, max_length=255)
    material: Optional[str] = Field(default=None, max_length=255)
    technique: Optional[str] = Field(default=None, max_length=255)
    description_observation: Optional[str] = None
    story_body: Optional[str] = None
    story_type: Literal["documented_event", "legend", "oral_account", "interpretation"] = "documented_event"
    meaning_body: Optional[str] = None
    historical_value_body: Optional[str] = None
    cultural_value_body: Optional[str] = None
    art_value_body: Optional[str] = None
    review_status: Literal["draft", "in_review", "approved", "published", "archived"] = "draft"
    content_revision: int = Field(default=1, ge=1)


class ImperialArtDetailCreate(ImperialArtDetailBase):
    site_id: UUID
    claim_sources: list[ImperialArtDetailClaimSourceBase] = []
    questions: list[ImperialArtDetailQuestionBase] = []


class ImperialArtDetailUpdate(ImperialV51BaseSchema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    kind: Optional[Literal["carving", "pattern", "painting", "mosaic", "relief"]] = None
    motif: Optional[str] = Field(default=None, max_length=255)
    material: Optional[str] = Field(default=None, max_length=255)
    technique: Optional[str] = Field(default=None, max_length=255)
    description_observation: Optional[str] = None
    story_body: Optional[str] = None
    story_type: Optional[Literal["documented_event", "legend", "oral_account", "interpretation"]] = None
    meaning_body: Optional[str] = None
    historical_value_body: Optional[str] = None
    cultural_value_body: Optional[str] = None
    art_value_body: Optional[str] = None
    review_status: Optional[Literal["draft", "in_review", "approved", "published", "archived"]] = None
    content_revision: Optional[int] = Field(default=None, ge=1)
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialArtDetailSummary(ImperialV51BaseSchema):
    id: UUID
    site_id: UUID
    title: str
    slug: str
    kind: str
    motif: Optional[str] = None
    story_type: str
    review_status: str


class ImperialArtDetailDetail(ImperialArtDetailBase):
    id: UUID
    site_id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
    claim_sources: list[ImperialArtDetailClaimSourceOut] = []
    questions: list[ImperialArtDetailQuestionOut] = []


# Update forward reference on ImperialMediaHotspotOut
ImperialMediaHotspotOut.model_rebuild()


# --------------------------------------------------------------------------- #
# 3. Heritage Detective Clues & Attempts
# --------------------------------------------------------------------------- #
class ImperialClueBase(ImperialV51BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    clue_text: str = Field(..., min_length=1)
    target_type: Literal["site", "art_detail"]
    target_id: UUID
    hint_steps: list[Any] = []
    grade_level: Optional[str] = Field(default=None, max_length=50)
    difficulty: Optional[str] = Field(default=None, max_length=50)
    review_status: Literal["draft", "in_review", "approved", "published", "archived"] = "draft"


class ImperialClueCreate(ImperialClueBase):
    pass


class ImperialClueUpdate(ImperialV51BaseSchema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    clue_text: Optional[str] = Field(default=None, min_length=1)
    target_type: Optional[Literal["site", "art_detail"]] = None
    target_id: Optional[UUID] = None
    hint_steps: Optional[list[Any]] = None
    grade_level: Optional[str] = Field(default=None, max_length=50)
    difficulty: Optional[str] = Field(default=None, max_length=50)
    review_status: Optional[Literal["draft", "in_review", "approved", "published", "archived"]] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialClueOut(ImperialClueBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


class ImperialClueAttemptRequest(ImperialV51BaseSchema):
    selected_target_id: UUID
    attempt_number: int = Field(default=1, ge=1)


class ImperialClueAttemptResponse(ImperialV51BaseSchema):
    id: UUID
    clue_id: UUID
    is_correct: bool
    attempt_number: int
    hint_steps: list[Any] = []
    message: str


# --------------------------------------------------------------------------- #
# 4. Interactive Questions & Game Submissions
# --------------------------------------------------------------------------- #
class ImperialQuestionBase(ImperialV51BaseSchema):
    site_id: Optional[UUID] = None
    detail_id: Optional[UUID] = None
    question_type: Literal["multiple_choice", "matching", "hotspot_identify"] = "multiple_choice"
    prompt: str = Field(..., min_length=1)
    options: list[Any] = []
    explanation_why: Optional[str] = None
    source_citation: Optional[str] = None
    review_status: Literal["draft", "in_review", "approved", "published", "archived"] = "draft"


class ImperialQuestionCreate(ImperialQuestionBase):
    answer_key: str = Field(..., min_length=1)


class ImperialQuestionUpdate(ImperialV51BaseSchema):
    site_id: Optional[UUID] = None
    detail_id: Optional[UUID] = None
    question_type: Optional[Literal["multiple_choice", "matching", "hotspot_identify"]] = None
    prompt: Optional[str] = Field(default=None, min_length=1)
    options: Optional[list[Any]] = None
    answer_key: Optional[str] = Field(default=None, min_length=1)
    explanation_why: Optional[str] = None
    source_citation: Optional[str] = None
    review_status: Optional[Literal["draft", "in_review", "approved", "published", "archived"]] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialQuestionOut(ImperialV51BaseSchema):
    """Public inquiry question response.

    Note: answer_key and explanation_why are strictly hidden before submission.
    """
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    site_id: Optional[UUID] = None
    detail_id: Optional[UUID] = None
    question_type: str
    prompt: str
    options: list[Any] = []
    source_citation: Optional[str] = None
    review_status: str
    created_at: datetime


class ImperialQuestionAdminOut(ImperialQuestionBase):
    """Admin representation including answer key and explanations."""
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    answer_key: str
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


class ImperialGameSubmitRequest(ImperialV51BaseSchema):
    question_id: UUID
    user_answer: str = Field(..., min_length=1)


class ImperialGameSubmitResponse(ImperialV51BaseSchema):
    question_id: UUID
    is_correct: bool
    user_answer: str
    correct_answer: str
    explanation_why: Optional[str] = None
    source_citation: Optional[str] = None


# --------------------------------------------------------------------------- #
# 5. Teacher Assignment Releases
# --------------------------------------------------------------------------- #
class ImperialAssignmentReleaseCreate(ImperialV51BaseSchema):
    class_name: str = Field(..., min_length=1, max_length=255)
    journey_slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    due_date: Optional[datetime] = None
    rubric_weights: Optional[dict[str, Any]] = None
    is_active: bool = True


class ImperialAssignmentReleaseUpdate(ImperialV51BaseSchema):
    class_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    journey_slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    due_date: Optional[datetime] = None
    rubric_weights: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialAssignmentReleaseOut(ImperialV51BaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    teacher_id: UUID
    class_name: str
    journey_slug: str
    title: str
    due_date: Optional[datetime] = None
    rubric_weights: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
