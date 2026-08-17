# -*- coding: utf-8 -*-
"""History Story Engine API schemas (Phase 10).

Request/response models for block-based history stories per
docs/specs/HISTORY_FIRST_MASTER_SPEC.md section 30. A story is an ordered list
of typed blocks (30.1); every block shape follows the example in 30.2
(``type`` + optional ``title``/``body`` + referenced ``entity_ids`` /
``source_claim_ids``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HistoryStoryCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=200)
    title_vi: str = Field(..., min_length=1, max_length=500)
    title_en: Optional[str] = None
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    hero_image_url: Optional[str] = None
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"
    publication_status: str = "unreviewed"
    featured: bool = False


class HistoryStoryUpdate(BaseModel):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title_vi: Optional[str] = Field(default=None, min_length=1, max_length=500)
    title_en: Optional[str] = None
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    hero_image_url: Optional[str] = None
    blocks: Optional[list[dict[str, Any]]] = None
    status: Optional[str] = None
    publication_status: Optional[str] = None
    featured: Optional[bool] = None


class HistoryStoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title_vi: str
    title_en: Optional[str] = None
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    hero_image_url: Optional[str] = None
    blocks: list[Any] = Field(default_factory=list)
    status: str
    publication_status: str
    featured: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class HistoryStoryListOut(BaseModel):
    items: list[HistoryStoryOut]
    total: int
    offset: int = 0
    limit: int = 50