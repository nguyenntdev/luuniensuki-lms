# -*- coding: utf-8 -*-
"""Admin / content-management / RAG / embedding / classroom / leaderboard models.

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
Field sets, validators and defaults are preserved exactly. ``backend.main``
imports these by their original bare names.

NOTE on ``AIJobOut``: this module owns the *admin-facing* shape (with
``user_id``/``user_email``/``prompt``/``response``). A second, leaner ``AIJobOut``
lives in ``backend.apischemas.ai`` and was the last inline definition in
``main.py``, so it (not this admin shape) is what ``main``'s endpoints and
``main.AIJobOut`` resolved to. This admin shape is relocated here verbatim for
completeness even though ``backend.main`` does not import it.

These models are intentionally distinct from any same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ClassMemberAddRequest(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def _validate_identifier(self) -> "ClassMemberAddRequest":
        if not self.user_id and not self.email:
            raise ValueError("Either user_id or email is required.")
        return self


class AssignmentCreateRequest(BaseModel):
    quest_id: UUID
    due_at: Optional[datetime] = None


class ClassMemberOut_Legacy(BaseModel):
    user_id: UUID
    display_name: str
    email: str
    role: str
    joined_at: datetime


class AssignmentSummaryOut(BaseModel):
    id: UUID
    quest_id: UUID
    quest_slug: str
    quest_name: str
    due_at: Optional[datetime] = None
    assigned_at: datetime
    completion_percent: float


class ClassSummaryOut_Legacy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    member_count: int
    assignment_count: int


class ClassDetailOut_Legacy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    members: list[ClassMemberOut_Legacy]
    assignments: list[AssignmentSummaryOut]


class AdminLessonOut(BaseModel):
    id: UUID
    motif_id: UUID
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: bool
    is_ai_generated: bool
    version: int = 1
    last_editor_id: Optional[UUID] = None
    published_at: Optional[datetime] = None
    publish_note: Optional[str] = None
    # Review workflow fields
    status: str = "draft"
    submitted_for_review_at: Optional[datetime] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminLessonCreateRequest(BaseModel):
    motif_id: UUID
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_ai_generated: Optional[bool] = None


class AdminLessonUpdateRequest(BaseModel):
    intro_text: Optional[str] = None
    description: Optional[str] = None
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_ai_generated: Optional[bool] = None
    publish_note: Optional[str] = None  # Note for publishing this version


class AdminQuizQuestionOut(BaseModel):
    id: UUID
    motif_id: UUID
    urn_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[Any] = None
    correct_answer: str
    target_mesh_name: Optional[str] = None
    difficulty: int
    explanation: Optional[str] = None
    is_published: bool
    is_active: bool
    # Review workflow fields
    status: str = "draft"
    submitted_for_review_at: Optional[datetime] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime


class AdminQuizQuestionCreateRequest(BaseModel):
    motif_id: UUID
    urn_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[Any] = None
    correct_answer: str
    target_mesh_name: Optional[str] = None
    difficulty: Optional[int] = 1
    explanation: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class AdminQuizQuestionUpdateRequest(BaseModel):
    question_type: Optional[str] = None
    question_text: Optional[str] = None
    options: Optional[Any] = None
    correct_answer: Optional[str] = None
    target_mesh_name: Optional[str] = None
    difficulty: Optional[int] = None
    explanation: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class RagEmbeddingRebuildOut(BaseModel):
    total: int
    updated: int
    skipped: int


class RagHealthOut(BaseModel):
    total_documents: int
    active_documents: int
    documents_with_embeddings: int
    documents_without_embeddings: int
    coverage_percent: float
    last_embedding_updated_at: Optional[datetime] = None
    oldest_embedding_at: Optional[datetime] = None
    embedding_model: str
    settings_status: dict[str, Any]
    status: str
    issues: list[str]


class EmbeddingJobOut(BaseModel):
    id: UUID
    status: str
    total_documents: int
    processed_documents: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by_id: UUID
    created_at: datetime
    progress_percent: float = 0.0


class EmbeddingRebuildRequest(BaseModel):
    force: bool = False


class AIJobOut(BaseModel):
    id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    job_type: str
    status: str
    provider: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    title: str


class ContentFlagCreateRequest(BaseModel):
    content_type: str
    content_id: UUID
    reason: str = Field(min_length=3, max_length=255)


class ContentFlagOut(BaseModel):
    id: UUID
    user_id: UUID
    content_type: str
    content_id: UUID
    reason: str
    created_at: datetime


class ContentVersionListOut(BaseModel):
    id: UUID
    version: int
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class ContentVersionOut(BaseModel):
    id: UUID
    content_type: str
    content_id: UUID
    version: int
    data: dict
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class RevertContentIn(BaseModel):
    change_note: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
