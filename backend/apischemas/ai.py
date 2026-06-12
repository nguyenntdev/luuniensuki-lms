# -*- coding: utf-8 -*-
"""AI tutor / generation / recommendation request/response models.

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
Field sets, validators and defaults are preserved exactly. ``backend.main``
imports these by their original bare names.

NOTE on ``AIJobOut``: ``main.py`` historically defined ``AIJobOut`` twice with
*different* field sets — an admin-facing shape (in ``backend.apischemas.admin``)
and this leaner AI-domain shape. The leaner shape was the *last* inline
definition, so it is the one every endpoint reference and ``main.AIJobOut``
resolved to (the admin shape was shadowed before any use). ``backend.main``
imports this leaner shape under the bare name ``AIJobOut``.

These models are intentionally distinct from any same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationItemOut(BaseModel):
    kind: str
    title: str
    description: Optional[str] = None
    href: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class RecommendationAIOut(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    job_id: Optional[UUID] = None
    status: Optional[str] = None


class RecommendationOut(BaseModel):
    id: UUID
    source: str
    created_at: datetime
    items: list[RecommendationItemOut]
    ai: Optional[RecommendationAIOut] = None
    opted_out: bool = False


class RecommendationRefreshRequest(BaseModel):
    use_llm: Optional[bool] = False


class AIJobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    provider: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class AIChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


class AIContextIn(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    quiz_question_id: Optional[UUID] = None


class AICitationOut(BaseModel):
    index: int
    source_type: str
    source_id: Optional[str] = None
    title: str
    snippet: Optional[str] = None


class AIAnswerOut(BaseModel):
    answer: str
    citations: list[AICitationOut] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class AITutorRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[AIChatMessage] = Field(default_factory=list)
    context: Optional[AIContextIn] = None
    level: Optional[str] = None


class AIQuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    context: Optional[AIContextIn] = None
    limit: int = Field(default=6, ge=1, le=12)


class LessonGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    motif_mesh_name: Optional[str] = None
    motif_name: Optional[str] = None
    urn_slug: Optional[str] = None
    level: Optional[str] = "beginner"
    language: Optional[str] = "vi"
    force: bool = False
    use_seed: bool = True
    generate_quiz: bool = False
    quiz_count: int = Field(default=4, ge=1, le=20)


class LessonGenerateOut(BaseModel):
    motif_id: UUID
    lesson_id: UUID
    summary: str
    ai_job_id: Optional[UUID] = None
    used_seed: bool = False


class QuizGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    motif_mesh_name: Optional[str] = None
    motif_name: Optional[str] = None
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    count: int = Field(default=5, ge=1, le=30)
    difficulty: int = Field(default=2, ge=1, le=5)
    replace_existing: bool = False
    use_seed: bool = True


class QuizGenerateOut(BaseModel):
    question_ids: list[UUID]
    ai_job_id: Optional[UUID] = None
    used_seed: bool = False


class SummaryGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    level: Optional[str] = None


class SummaryGenerateOut(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class FlashcardGenerateIn(BaseModel):
    topic: Optional[str] = None
    motif_id: Optional[UUID] = None
    count: int = Field(default=8, ge=2, le=30)
    level: Optional[str] = None


class FlashcardOut(BaseModel):
    front: str
    back: str


class FlashcardGenerateOut(BaseModel):
    cards: list[FlashcardOut]
    job_id: Optional[UUID] = None


class FeedbackGenerateIn(BaseModel):
    question: str = Field(min_length=1)
    correct_answer: str = Field(min_length=1)
    user_answer: str = Field(min_length=1)
    context: Optional[AIContextIn] = None


class FeedbackGenerateOut(BaseModel):
    is_correct: bool
    explanation: str
    next_step: Optional[str] = None
    job_id: Optional[UUID] = None


class CoachGenerateIn(BaseModel):
    goal: Optional[str] = None
    availability_minutes_per_day: Optional[int] = Field(default=15, ge=5, le=120)
    days_per_week: Optional[int] = Field(default=5, ge=2, le=7)


class CoachGenerateOut(BaseModel):
    message: str
    weekly_plan: list[str] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class ExplainGenerateIn(BaseModel):
    text: str = Field(min_length=1)
    level: str = Field(pattern="^(child|teen|expert)$")


class ExplainGenerateOut(BaseModel):
    explanation: str
    job_id: Optional[UUID] = None


class ReviewPlanItem(BaseModel):
    motif_id: UUID
    motif_name: str
    due_in_days: int
    status: str


class ReviewPlanOut(BaseModel):
    items: list[ReviewPlanItem]


class DiagnosticGenerateIn(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    count: int = Field(default=6, ge=2, le=20)
    level: Optional[str] = None


class DiagnosticQuestionOut(BaseModel):
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: Optional[str] = None


class DiagnosticGenerateOut(BaseModel):
    questions: list[DiagnosticQuestionOut]
    job_id: Optional[UUID] = None


class SeedUrnIn(BaseModel):
    force: bool = False
    generate_quiz: bool = True
    quiz_count: int = Field(default=4, ge=1, le=20)
    use_seed: bool = True


class SeedUrnResult(BaseModel):
    motif_id: UUID
    status: str
    lesson_id: Optional[UUID] = None
    quiz_count: int = 0
    used_seed: bool = False


class SeedUrnOut(BaseModel):
    urn_id: UUID
    urn_slug: str
    total: int
    created: int
    skipped: int
    results: list[SeedUrnResult]
