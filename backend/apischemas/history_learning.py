# -*- coding: utf-8 -*-
"""Historical Learning Engine V2 API schemas (Phase 8).

Request/response models for the question-model V2 endpoints and mastery
dimensions per docs/specs/HISTORY_FIRST_MASTER_SPEC.md sections 32-34.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HistoryQuestionCreate(BaseModel):
    motif_id: UUID
    question_type: str
    question_text: str = Field(..., min_length=1, max_length=2000)
    options: Optional[list[Any]] = None
    correct_answer: Optional[str] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)
    skill_type: Optional[str] = None
    explanation: Optional[str] = None
    is_published: bool = True
    is_active: bool = True
    # V2 common fields (Spec 32.1)
    skill_dimensions: Optional[list[str]] = None
    entity_id: Optional[UUID] = None
    claim_ids: Optional[list[UUID]] = None
    source_ids: Optional[list[UUID]] = None
    answer_contract: Optional[dict[str, Any]] = None


class HistoryQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int
    skill_type: Optional[str] = None
    explanation: Optional[str] = None
    is_published: bool
    is_active: bool
    content_validation_status: str
    skill_dimensions: Optional[list[Any]] = None
    entity_id: Optional[UUID] = None
    claim_ids: Optional[list[Any]] = None
    source_ids: Optional[list[Any]] = None
    answer_contract: Optional[dict] = None
    status: Optional[str] = None
    created_at: datetime


class HistoryQuestionListOut(BaseModel):
    items: list[HistoryQuestionOut]
    total: int
    offset: int
    limit: int


class HistoryQuestionGradeIn(BaseModel):
    """Client submits ONLY the raw answer. Correctness is never accepted from
    the client — the server derives it from the answer contract (Spec 33.4)."""

    answer: dict[str, Any]


class HistoryQuestionGradeOut(BaseModel):
    correct: bool
    score: float
    feedback_vi: str
    skill_dimensions: list[str]


class MasteryDimensionOut(BaseModel):
    dimension: str
    value: Optional[float] = None
    total_questions: int = 0
    correct_answers: int = 0
    last_score: Optional[float] = None


class HistorySkillsOut(BaseModel):
    user_id: UUID
    dimensions: list[MasteryDimensionOut]
    overall: Optional[float] = None