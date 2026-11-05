# -*- coding: utf-8 -*-
"""Pydantic schemas for FSRS Spaced Repetition and Adaptive Evidence Practice."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DueEvidenceTaskOut(BaseModel):
    card_id: UUID
    source_id: UUID
    source_title: str
    author_text: Optional[str] = None
    citation_text: Optional[str] = None
    excerpt: Optional[str] = None
    prompt: Optional[str] = None
    task_type: str = "source_evaluation"
    fsrs_state: str
    fsrs_difficulty: float
    fsrs_stability: float
    fsrs_due_date: datetime
    retrievability: float
    is_mastered: bool
    mastery_badge_awarded: bool


class DueEvidenceTaskListOut(BaseModel):
    tasks: list[DueEvidenceTaskOut]
    total_due: int


class EvidenceEvaluationIn(BaseModel):
    card_id: UUID
    score: float = Field(ge=0.0, le=1.0)
    rating: Optional[str] = None
    dwell_time_seconds: float = Field(ge=0.0)
    client_claimed_badge: Optional[str] = None
    client_claimed_xp: Optional[int] = None


class AlgorithmicTransparencyOut(BaseModel):
    algorithm: str
    formula: str
    prior_stability: float
    new_stability: float
    prior_difficulty: float
    new_difficulty: float
    elapsed_days: float
    retrievability: float
    target_retention: float
    adaptive_applied: bool
    explanation: str


class EvidenceEvaluationOut(BaseModel):
    success: bool
    card_id: UUID
    source_id: UUID
    score: float
    rating: str
    fsrs_state: str
    fsrs_stability: float
    fsrs_difficulty: float
    interval_days: float
    fsrs_due_date: datetime
    retrievability: float
    xp_awarded: int
    user_total_xp: int
    is_mastered: bool
    mastery_badge: Optional[str] = None
    denied_badges: list[str] = Field(default_factory=list)
    abuse_detected: bool
    abuse_reason: Optional[str] = None
    algorithmic_transparency: AlgorithmicTransparencyOut


class FsrsSettingsOut(BaseModel):
    fsrs_enabled: bool
    optimal_retention: float
    recommended_range: list[float]
    review_count: int
    using_personal_params: bool
    cohort: str


class FsrsSettingsUpdateIn(BaseModel):
    fsrs_enabled: Optional[bool] = None
    optimal_retention: Optional[float] = Field(default=None, ge=0.70, le=0.97)


class FsrsModelTransparencyOut(BaseModel):
    algorithm_name: str
    parameters: list[float]
    retention_formula: str
    stability_recall_formula: str
    stability_forgetting_formula: str
    difficulty_formula: str
    default_optimal_retention: float
    retention_range: list[float]
    separation_guarantee: str
    anti_abuse_safeguards: list[str]


class RateCardRequestIn(BaseModel):
    rating: str


class RateCardResponseOut(BaseModel):
    card_id: UUID
    fsrs_due_date: datetime
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_state: str
    interval_days: float
    cohort: str
