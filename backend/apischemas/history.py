# -*- coding: utf-8 -*-
"""History-First domain API schemas (Phase 1).

Request/response models for the historical governance layer:
entities, claims, sources, claim-source bindings, relations, geographies,
assets, and the audit trail. Maps to the tables defined in
``backend/history_models`` per docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part III.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #
class HistoricalEntityCreate(BaseModel):
    entity_type: str
    slug: str = Field(..., min_length=1, max_length=200)
    name_vi: str = Field(..., min_length=1, max_length=300)
    name_en: Optional[str] = None
    name_han_nom: Optional[str] = None
    alternative_names: list[str] = Field(default_factory=list)
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_precision: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    geo_precision: Optional[str] = None
    publication_status: str = "draft"
    content_version: int = 1


class HistoricalEntityUpdate(BaseModel):
    entity_type: Optional[str] = None
    slug: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name_vi: Optional[str] = Field(default=None, min_length=1, max_length=300)
    name_en: Optional[str] = None
    name_han_nom: Optional[str] = None
    alternative_names: Optional[list[str]] = None
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_precision: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    geo_precision: Optional[str] = None
    publication_status: Optional[str] = None


class HistoricalEntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    slug: str
    name_vi: str
    name_en: Optional[str] = None
    name_han_nom: Optional[str] = None
    alternative_names: list[Any] = Field(default_factory=list)
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_precision: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_precision: Optional[str] = None
    publication_status: str
    content_version: int
    created_at: datetime
    updated_at: datetime


class HistoricalEntityListOut(BaseModel):
    items: list[HistoricalEntityOut]
    total: int
    offset: int
    limit: int


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
class HistoricalSourceCreate(BaseModel):
    source_type: str
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: Optional[str] = None
    author_text: Optional[str] = None
    editor_text: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=0, le=9999)
    publication_date: Optional[date] = None
    edition: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    archive_url: Optional[str] = None
    repository_identifier: Optional[str] = None
    language: Optional[str] = None
    citation_text: Optional[str] = None
    rights_status: Optional[str] = None
    license: Optional[str] = None
    attribution_text: Optional[str] = None
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    verification_status: str = "unreviewed"


class HistoricalSourceUpdate(BaseModel):
    source_type: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    subtitle: Optional[str] = None
    author_text: Optional[str] = None
    editor_text: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=0, le=9999)
    publication_date: Optional[date] = None
    edition: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    archive_url: Optional[str] = None
    repository_identifier: Optional[str] = None
    language: Optional[str] = None
    citation_text: Optional[str] = None
    rights_status: Optional[str] = None
    license: Optional[str] = None
    attribution_text: Optional[str] = None
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    verification_status: Optional[str] = None


class HistoricalSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    title: str
    subtitle: Optional[str] = None
    author_text: Optional[str] = None
    editor_text: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[date] = None
    edition: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    archive_url: Optional[str] = None
    repository_identifier: Optional[str] = None
    language: Optional[str] = None
    citation_text: Optional[str] = None
    rights_status: Optional[str] = None
    license: Optional[str] = None
    attribution_text: Optional[str] = None
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    verification_status: str
    created_at: datetime
    updated_at: datetime


class HistoricalSourceListOut(BaseModel):
    items: list[HistoricalSourceOut]
    total: int
    offset: int
    limit: int


# --------------------------------------------------------------------------- #
# Claims
# --------------------------------------------------------------------------- #
class HistoricalClaimCreate(BaseModel):
    entity_id: UUID
    claim_key: Optional[str] = None
    claim_type: str
    statement_vi: str = Field(..., min_length=1)
    statement_en: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    date_precision: Optional[str] = None
    confidence: str = "unknown"
    verification_status: str = "unreviewed"
    origin: str
    risk_level: str = "normal"
    review_notes: Optional[str] = None


class HistoricalClaimUpdate(BaseModel):
    claim_key: Optional[str] = None
    claim_type: Optional[str] = None
    statement_vi: Optional[str] = Field(default=None, min_length=1)
    statement_en: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    date_precision: Optional[str] = None
    confidence: Optional[str] = None
    verification_status: Optional[str] = None
    origin: Optional[str] = None
    risk_level: Optional[str] = None
    review_notes: Optional[str] = None


class HistoricalClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_id: UUID
    claim_key: Optional[str] = None
    claim_type: str
    statement_vi: str
    statement_en: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    date_precision: Optional[str] = None
    confidence: str
    verification_status: str
    origin: str
    risk_level: str
    review_notes: Optional[str] = None
    created_by: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    supersedes_claim_id: Optional[UUID] = None
    is_current: bool


class HistoricalClaimListOut(BaseModel):
    items: list[HistoricalClaimOut]
    total: int
    offset: int
    limit: int


# --------------------------------------------------------------------------- #
# Claim–Source bindings
# --------------------------------------------------------------------------- #
class HistoricalClaimSourceCreate(BaseModel):
    source_id: UUID
    support_type: str
    locator_type: Optional[str] = None
    page_start: Optional[str] = None
    page_end: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    figure: Optional[str] = None
    folio: Optional[str] = None
    inscription_location: Optional[str] = None
    quotation_excerpt: Optional[str] = None
    quotation_language: Optional[str] = None
    editor_note: Optional[str] = None


class HistoricalClaimSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: UUID
    source_id: UUID
    support_type: str
    locator_type: Optional[str] = None
    page_start: Optional[str] = None
    page_end: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    figure: Optional[str] = None
    folio: Optional[str] = None
    inscription_location: Optional[str] = None
    quotation_excerpt: Optional[str] = None
    quotation_language: Optional[str] = None
    editor_note: Optional[str] = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Relations
# --------------------------------------------------------------------------- #
class HistoricalRelationCreate(BaseModel):
    subject_entity_id: UUID
    predicate: str
    object_entity_id: UUID
    claim_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    confidence: str = "unknown"
    verification_status: str = "unreviewed"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class HistoricalRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_entity_id: UUID
    predicate: str
    object_entity_id: UUID
    claim_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    confidence: str
    verification_status: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Geographies
# --------------------------------------------------------------------------- #
class HistoricalGeographyUpsert(BaseModel):
    historical_name: Optional[str] = None
    modern_name: Optional[str] = None
    historical_geometry: Optional[dict] = None
    modern_geometry: Optional[dict] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    geo_precision: str
    mapping_status: str
    source_claim_id: Optional[UUID] = None
    notes: Optional[str] = None


class HistoricalGeographyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: UUID
    historical_name: Optional[str] = None
    modern_name: Optional[str] = None
    historical_geometry: Optional[dict] = None
    modern_geometry: Optional[dict] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    geo_precision: str
    mapping_status: str
    source_claim_id: Optional[UUID] = None
    notes: Optional[str] = None


# --------------------------------------------------------------------------- #
# Assets
# --------------------------------------------------------------------------- #
class HistoricalAssetCreate(BaseModel):
    asset_type: str
    storage_url: str = Field(..., min_length=1)
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    byte_size: Optional[int] = None
    sha256: Optional[str] = None
    rights_status: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    source_origin: Optional[str] = None
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    entity_id: Optional[UUID] = None


class HistoricalAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_type: str
    storage_url: str
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    byte_size: Optional[int] = None
    sha256: Optional[str] = None
    rights_status: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    source_origin: Optional[str] = None
    public_display_allowed: Optional[bool] = None
    derivative_allowed: Optional[bool] = None
    entity_id: Optional[UUID] = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------------- #
class HistoricalSearchItem(BaseModel):
    id: UUID
    entity_type: str
    slug: str
    name_vi: str
    name_en: Optional[str] = None
    summary_vi: Optional[str] = None
    publication_status: str
    matched_on: Optional[str] = None


class HistoricalSearchOut(BaseModel):
    query: str
    items: list[HistoricalSearchItem]
    total: int
