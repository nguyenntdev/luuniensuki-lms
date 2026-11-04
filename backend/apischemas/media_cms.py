# -*- coding: utf-8 -*-
"""Pydantic schemas for Museum Operator Media CMS (V5-T050 / W04-A10)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaCmsItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: str = Field(default="image")
    rights_owner: str = Field(..., min_length=1, max_length=255)
    license_type: str = Field(..., min_length=1, max_length=100)
    attribution: str = Field(..., min_length=1)
    public_display_allowed: bool = True
    derivative_allowed: bool = True
    historical_entity_id: Optional[UUID] = None
    relic_slug: Optional[str] = None


class MediaCmsItemCreate(MediaCmsItemBase):
    pass


class MediaCmsItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[str] = None
    rights_owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    license_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    attribution: Optional[str] = Field(default=None, min_length=1)
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    historical_entity_id: Optional[UUID] = None
    relic_slug: Optional[str] = None


class MediaCmsReviewAction(BaseModel):
    reason: Optional[str] = None
    notes: Optional[str] = None


class MediaCmsItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: Optional[str] = None
    asset_type: str
    file_format: str
    mime_type: str
    storage_url: str
    thumbnail_url: Optional[str] = None
    file_size_bytes: int
    sha256: str
    rights_owner: str
    license_type: str
    attribution: str
    public_display_allowed: bool
    derivative_allowed: bool
    historical_entity_id: Optional[UUID] = None
    relic_slug: Optional[str] = None
    publication_status: str
    version: int
    review_notes: Optional[str] = None
    uploaded_by_id: Optional[UUID] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MediaCmsItemListOut(BaseModel):
    items: list[MediaCmsItemOut]
    total: int
    limit: int
    offset: int


class MediaCmsPreviewOut(BaseModel):
    item: MediaCmsItemOut
    viewer_type: str
    viewer_config: dict[str, Any]
    rights_summary: dict[str, Any]
    staged_review_summary: dict[str, Any]
