# -*- coding: utf-8 -*-
"""Quests and collection request/response models.

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
Field sets, defaults and inheritance are preserved exactly. ``backend.main``
imports these by their original bare names.

These models are intentionally distinct from any same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class CollectionItemOut(BaseModel):
    motif_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    status: str


class QuestProgressOut(BaseModel):
    quest_name: str
    total: int
    discovered: int
    progress_percent: float


class CollectionStatsOut(BaseModel):
    total: int
    discovered: int
    learned: int
    mastered: int
    quest: QuestProgressOut


class UserCollectionResponse(BaseModel):
    items: list[CollectionItemOut]
    stats: CollectionStatsOut


class QuestRewardOut(BaseModel):
    reward_type: str
    amount: Optional[int] = None
    badge_slug: Optional[str] = None
    metadata: Optional[Any] = None


class QuestObjectiveOut(BaseModel):
    id: UUID
    objective_type: str
    target_value: int
    current_value: int
    is_complete: bool
    params: Optional[dict[str, Any]] = None


class QuestStepOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    display_order: int
    completion_percent: float
    objectives: list[QuestObjectiveOut]


class QuestPrerequisiteOut(BaseModel):
    id: UUID
    slug: str
    name: str


class QuestListItemOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    display_order: int
    status: str
    progress_percent: float
    is_locked: bool
    lock_reason: Optional[str] = None
    prerequisite: Optional[QuestPrerequisiteOut] = None
    rewards: list[QuestRewardOut]


class QuestCertificateOut(BaseModel):
    code: str
    issued_at: datetime
    issuer_name: str


class QuestDetailOut(QuestListItemOut):
    steps: list[QuestStepOut]
    certificate: Optional[QuestCertificateOut] = None


class QuestSummaryObjectiveOut(BaseModel):
    objective_type: str
    current_value: int
    target_value: int


class QuestSummaryOut(BaseModel):
    quest_id: UUID
    quest_slug: str
    quest_name: str
    status: str
    progress_percent: float
    next_step_title: Optional[str] = None
    next_objective: Optional[QuestSummaryObjectiveOut] = None
