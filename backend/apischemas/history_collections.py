# -*- coding: utf-8 -*-
"""History Collection API schemas (Phase 11, Spec section 47)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HistoryCollectionCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=200)
    title_vi: str = Field(..., min_length=1, max_length=300)
    title_en: Optional[str] = None
    description_vi: Optional[str] = None
    visibility: str = "private"
    entity_ids: list[Any] = Field(default_factory=list)
    source_ids: list[Any] = Field(default_factory=list)
    story_ids: list[Any] = Field(default_factory=list)
    question_ids: list[Any] = Field(default_factory=list)


class HistoryCollectionUpdate(BaseModel):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title_vi: Optional[str] = Field(default=None, min_length=1, max_length=300)
    title_en: Optional[str] = None
    description_vi: Optional[str] = None
    visibility: Optional[str] = None
    entity_ids: Optional[list[Any]] = None
    source_ids: Optional[list[Any]] = None
    story_ids: Optional[list[Any]] = None
    question_ids: Optional[list[Any]] = None


class HistoryCollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    slug: str
    title_vi: str
    title_en: Optional[str] = None
    description_vi: Optional[str] = None
    status: str
    visibility: str
    entity_ids: list[Any] = Field(default_factory=list)
    source_ids: list[Any] = Field(default_factory=list)
    story_ids: list[Any] = Field(default_factory=list)
    question_ids: list[Any] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class HistoryCollectionListOut(BaseModel):
    items: list[HistoryCollectionOut]
    total: int
    offset: int
    limit: int
