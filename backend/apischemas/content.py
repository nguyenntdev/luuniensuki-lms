# -*- coding: utf-8 -*-
"""Content-domain request/response models (urns, motifs, lessons, quizzes,
exams, certificates, analytics, progress-unlock, tags, search).

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
Field sets, validators, defaults and docstrings are preserved exactly so the
generated OpenAPI schema is unchanged. ``backend.main`` imports these by their
original bare names.

These models are intentionally distinct from the same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UrnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    model_url: str


class AnalyticsEventIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    payload: Optional[dict[str, Any]] = None
    path: Optional[str] = None
    session_id: Optional[UUID] = None
    cohort: Optional[str] = Field(None, max_length=50)
    device_info: Optional[dict[str, Any]] = None


class AnalyticsEventsIn(BaseModel):
    events: list[AnalyticsEventIn]


class AnalyticsEventsOut(BaseModel):
    success: bool
    count: int


class MotifOut(BaseModel):
    id: UUID
    urn_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    pos_x: float
    pos_y: float
    pos_z: float
    bounding_radius: float
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    is_demo: bool
    display_order: Optional[int] = None
    lesson_intro: Optional[str] = None


class MotifsByUrnResponse(BaseModel):
    urn: UrnOut
    motifs: list[MotifOut]


class MotifProgressOut(BaseModel):
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    lesson_viewed_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    quiz_attempts: int
    quiz_best_score: int
    xp_earned: int


class UrnProgressResponse(BaseModel):
    urn_id: UUID
    urn_slug: str
    motifs: list[MotifProgressOut]


class UrnListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    model_url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    is_demo: bool
    motif_count: int = 0
    discovered_count: int = 0
    learned_count: int = 0
    mastered_count: int = 0


class UrnDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    name_han: Optional[str] = None
    represents: Optional[str] = None
    description: Optional[str] = None
    model_url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    is_demo: bool


class UrnDetailResponse(BaseModel):
    urn: UrnDetailOut
    motifs: list[MotifOut]


class LessonContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    is_ai_generated: bool = False
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None


class MotifQuizQuestionOut(BaseModel):
    # Pre-submission payload: the answer key (correct_answer) and per-question
    # explanation are intentionally excluded so the client never receives answers
    # before submitting. Grading is server-authoritative (Requirement 4.2).
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = 1
    image_url: Optional[str] = None


class UserProgressDetailOut(BaseModel):
    """User progress for a specific motif."""

    id: UUID
    user_id: UUID
    motif_id: UUID
    status: str  # hidden, discovered, learned, mastered
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    xp_earned: int = 0
    quiz_best_score: Optional[int] = None


class MotifDetailOut(BaseModel):
    id: UUID
    urn: UrnOut
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    image_url: Optional[str] = None
    is_demo: bool
    display_order: Optional[int] = None
    lesson: Optional[LessonContentOut] = None
    quiz_question_count: int = 0
    quiz_questions: list[MotifQuizQuestionOut] = Field(default_factory=list)
    progress: Optional[UserProgressDetailOut] = None  # User's progress for this motif


class LessonCompleteResponse(BaseModel):
    user_id: UUID
    motif_id: UUID
    status: str
    lesson_viewed_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    xp_awarded: int
    total_xp: int


class TapPosition(BaseModel):
    x: float
    y: float
    z: float


class ProgressUnlockRequest(BaseModel):
    motif_id: Optional[UUID] = None
    mesh_name: Optional[str] = None
    tap_position: Optional[TapPosition] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "ProgressUnlockRequest":
        if self.motif_id is None and not self.mesh_name:
            raise ValueError("Either motif_id or mesh_name is required.")
        return self


class ProgressResponseDto(BaseModel):
    """Progress DTO matching mobile UnlockResponseDto.progress structure."""

    id: UUID
    user_id: UUID
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    xp_earned: int = 0
    quiz_best_score: Optional[int] = None


class BadgeResponseDto(BaseModel):
    """Badge DTO for new badges earned."""

    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    xp_bonus: int = 0


class ProgressUnlockResponse(BaseModel):
    """Response matching mobile UnlockResponseDto structure."""

    progress: ProgressResponseDto
    xp_earned: int
    total_xp: int
    new_badges: list[BadgeResponseDto] = []
    streak_updated: bool = False
    current_streak: int = 0


class QuizQuestionOut(BaseModel):
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int
    image_url: Optional[str] = None


class MotifQuizResponse(BaseModel):
    motif_id: UUID
    questions: list[QuizQuestionOut]
    attempts: int
    best_score: int
    pass_percent: int


class QuizAnswerIn(BaseModel):
    question_id: UUID
    answer: str


class QuizSubmitRequest(BaseModel):
    motif_id: UUID
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = Field(default=None, ge=0, le=3600)


class QuizResultDetail(BaseModel):
    question_id: UUID
    correct: bool
    correct_answer: str
    user_answer: Optional[str] = None
    explanation: Optional[str] = None


class QuizSubmitResponse(BaseModel):
    motif_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    status: str
    attempts: int
    best_score: int
    xp_awarded: int
    total_xp: int
    results: list[QuizResultDetail]


class UrnExamResponse(BaseModel):
    urn_id: UUID
    questions: list[QuizQuestionOut]
    attempts: int
    best_score: int
    pass_percent: int


class UrnExamSubmitRequest(BaseModel):
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = None


class UrnExamResultDetail(BaseModel):
    question_id: UUID
    correct: bool
    correct_answer: str
    user_answer: Optional[str] = None
    explanation: Optional[str] = None


class CertificateSummaryOut(BaseModel):
    code: str
    issuer_name: str
    issued_at: datetime


class UrnExamSubmitResponse(BaseModel):
    urn_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_awarded: int
    total_xp: int
    results: list[UrnExamResultDetail]
    certificate: Optional[CertificateSummaryOut] = None


class UrnExamSnapshotOut(BaseModel):
    pass_percent: int
    questions: list[QuizQuestionOut]


class UrnExamAttemptResultOut(BaseModel):
    score: int
    max_score: int
    percentage: int
    passed: bool
    results: list[UrnExamResultDetail]
    certificate: Optional[CertificateSummaryOut] = None


class UrnExamAttemptPayloadOut(BaseModel):
    urn: UrnOut
    exam: UrnExamSnapshotOut
    answers: dict[str, str]
    time_taken_seconds: Optional[int] = None
    submitted_at: datetime
    result: UrnExamAttemptResultOut


class UrnExamAttemptOut(BaseModel):
    id: UUID
    urn_id: UUID
    urn_slug: str
    urn_name: str
    score: int
    passed: bool
    created_at: datetime


class CertificateVerifyOut(BaseModel):
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    user_id: UUID
    display_name: str
    reason_type: str
    reason_id: UUID


class CertificateOut(BaseModel):
    """Output schema for certificate details."""

    id: UUID
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    reason_type: str
    reason_id: UUID


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    tag_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


class TagCreateIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    tag_type: str = Field(..., pattern="^(topic|difficulty|audience|era|style)$")
    description: Optional[str] = None
    is_active: bool = True


class ContentTagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tag_id: UUID
    content_type: str
    content_id: UUID
    created_at: datetime
    tag: TagOut


class ContentTagCreateIn(BaseModel):
    tag_slugs: list[str] = Field(..., min_items=1)


class SearchRequest(BaseModel):
    q: Optional[str] = Field(None, description="Search query")
    tags: Optional[list[str]] = Field(
        None, description="List of tag slugs to filter by"
    )
    content_types: Optional[list[str]] = Field(
        None, description="List of content types to search (lesson, motif, quiz, quest)"
    )
    limit: int = Field(20, ge=1, le=100)


class SearchResultItem(BaseModel):
    content_type: str
    content_id: UUID
    title: str
    description: Optional[str] = None
    tags: list[TagOut]
    relevance_score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int
    query: Optional[str] = None
    applied_tags: list[str] = []
