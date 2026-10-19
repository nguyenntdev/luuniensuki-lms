# -*- coding: utf-8 -*-
"""Heritage Knowledge Catalogue API schemas (Phase 1).

Request and response models for the Hue-wide heritage knowledge catalogue:
places, relationships, source evidence, media assets (including Sketchfab 3D
metadata, NoAI restrictions, and licensing governance), and unified search.

Namespace: /api/v1/heritage/*
Content Scope: RBPC_HUE (isolated from legacy CUU_DINH)
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --------------------------------------------------------------------------- #
# Controlled Vocabularies & Enums
# --------------------------------------------------------------------------- #
class HeritageEntityType(str, Enum):
    site = "site"
    monument = "monument"
    building = "building"
    object = "object"
    landscape = "landscape"
    intangible = "intangible"
    community = "community"
    collection = "collection"


class HeritageRecordStatus(str, Enum):
    candidate = "candidate"
    draft = "draft"
    source_backed = "source_backed"
    in_review = "in_review"
    approved = "approved"
    published = "published"
    withdrawn = "withdrawn"


class HeritageMediaType(str, Enum):
    photo = "photo"
    audio = "audio"
    video = "video"
    sketchfab_embed = "sketchfab_embed"
    glb = "glb"
    document = "document"


class HeritageAccuracyGrade(str, Enum):
    survey_grade = "survey_grade"
    measured_photogrammetry = "measured_photogrammetry"
    historian_reviewed = "historian_reviewed"
    illustrative_only = "illustrative_only"
    unreviewed = "unreviewed"
    rejected_accuracy = "rejected_accuracy"


class HeritageCommercialUseStatus(str, Enum):
    permitted = "permitted"
    blocked_nc = "blocked_nc"
    unreviewed = "unreviewed"
    requires_custom_grant = "requires_custom_grant"


class HeritageEmbedPermissionStatus(str, Enum):
    permitted = "permitted"
    needs_rights_review = "needs_rights_review"
    blocked = "blocked"
    author_contacted = "author_contacted"


class HeritageEvidenceStatus(str, Enum):
    needs_review = "needs_review"
    verified = "verified"
    disputed = "disputed"
    rejected = "rejected"


class HeritageReuseRights(str, Enum):
    public_domain = "public_domain"
    cc_by = "cc_by"
    cc_by_sa = "cc_by_sa"
    cc_by_nc_sa = "cc_by_nc_sa"
    educational_fair_use = "educational_fair_use"
    restricted = "restricted"
    unknown = "unknown"


# --------------------------------------------------------------------------- #
# Query Parameters & Filtering
# --------------------------------------------------------------------------- #
class HeritagePlaceQuery(BaseModel):
    """Query parameters for browsing and filtering heritage places with cursor pagination."""

    category: Optional[str] = Field(
        default=None,
        description="Filter by heritage category (e.g. imperial_architecture, royal_tomb, craft_living_culture, music_performance).",
    )
    entity_type: Optional[HeritageEntityType] = Field(
        default=None,
        description="Filter by structural entity type.",
    )
    editorial_status: Optional[HeritageRecordStatus] = Field(
        default=HeritageRecordStatus.published,
        description="Filter by editorial publication state. Defaults to published for public queries.",
    )
    content_scope: str = Field(
        default="RBPC_HUE",
        description="Content domain scope isolation.",
    )
    has_3d: Optional[bool] = Field(
        default=None,
        description="Filter by availability of approved 3D models.",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Opaque cursor string for deterministic keyset pagination.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of items to return (1-100).",
    )
    q: Optional[str] = Field(
        default=None,
        description="Full-text / diacritic-tolerant keyword search string.",
    )


# --------------------------------------------------------------------------- #
# Media Assets & 3D Governance
# --------------------------------------------------------------------------- #
class HeritageMediaAssetOut(BaseModel):
    """Media asset with comprehensive rights, accuracy grade, and 3D embed metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    place_id: Optional[UUID] = None
    media_type: HeritageMediaType
    source_platform: Optional[str] = Field(
        default=None,
        description="Upstream platform name (e.g. sketchfab, wikimedia, openheritage3d, cyark).",
    )
    original_url: str = Field(..., description="Canonical source URL of the asset.")
    title: Optional[str] = None
    creator_name: Optional[str] = None
    creator_url: Optional[str] = None
    model_uid: Optional[str] = Field(
        default=None,
        description="Exact 32-character hexadecimal identifier for Sketchfab models.",
    )
    license_label: Optional[str] = Field(
        default=None,
        description="Licence name (e.g. CC BY 4.0, CC BY-NC-SA 4.0, Public Domain).",
    )
    license_url: Optional[str] = None
    noai: bool = Field(
        default=False,
        description="Strict NoAI flag: prohibit AI ingestion, CV training, or generative scraping.",
    )
    commercial_use_status: HeritageCommercialUseStatus = HeritageCommercialUseStatus.unreviewed
    embed_permission_status: HeritageEmbedPermissionStatus = (
        HeritageEmbedPermissionStatus.needs_rights_review
    )
    accuracy_grade: HeritageAccuracyGrade = HeritageAccuracyGrade.unreviewed
    provenance_notes: Optional[str] = Field(
        default=None,
        description="Historical or technical provenance explanation (e.g. photogrammetry dataset, survey).",
    )
    attribution_text: Optional[str] = Field(
        default=None,
        description="Mandatory legal attribution line for public display.",
    )
    content_status: str = Field(
        default="candidate",
        description="Publication readiness: candidate, cleared_for_this_use, blocked, withdrawn.",
    )
    embed_url: Optional[str] = Field(
        default=None,
        description="Sanitized direct embed iframe endpoint (only populated when rights are cleared).",
    )
    content_scope: str = "RBPC_HUE"
    created_at: datetime


# --------------------------------------------------------------------------- #
# Source Evidence
# --------------------------------------------------------------------------- #
class HeritageSourceEvidenceOut(BaseModel):
    """Authoritative source citation and claim verification for a heritage place."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    place_id: UUID
    source_url: Optional[str] = None
    source_title: str = Field(..., description="Bibliographic or archival source title.")
    source_author: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    cited_section: Optional[str] = Field(
        default=None,
        description="Specific chapter, decree, or gazetteer volume.",
    )
    cited_page: Optional[str] = Field(
        default=None,
        description="Exact page number or folio reference in the original publication.",
    )
    retrieved_at: Optional[datetime] = None
    statement: str = Field(
        ...,
        description="Verified factual statement or extracted claim supported by this source.",
    )
    interpretation_note: Optional[str] = Field(
        default=None,
        description="Contextual or historiographical note distinguishing fact from folklore/legend.",
    )
    evidence_status: HeritageEvidenceStatus = HeritageEvidenceStatus.needs_review
    reuse_rights: HeritageReuseRights = HeritageReuseRights.unknown
    reviewer_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    content_scope: str = "RBPC_HUE"


# --------------------------------------------------------------------------- #
# Heritage Relationships
# --------------------------------------------------------------------------- #
class HeritageRelationOut(BaseModel):
    """Bidirectional or hierarchical relationship between two heritage places."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_place_id: UUID
    to_place_id: UUID
    from_place_slug: Optional[str] = None
    from_place_name: Optional[str] = None
    to_place_slug: Optional[str] = None
    to_place_name: Optional[str] = None
    relationship_type: str = Field(
        ...,
        description="Relationship semantic: contains, contained_in, honors, architectural_twin, historical_successor, associated_craft, ceremonial_connection.",
    )
    claim_id: Optional[UUID] = None
    review_state: str = Field(
        default="draft",
        description="Verification state of relationship: draft, verified, disputed.",
    )
    created_at: datetime


# --------------------------------------------------------------------------- #
# Engagement CTA Metadata
# --------------------------------------------------------------------------- #
class HeritageEngagementOut(BaseModel):
    """Structured engagement CTA attached to a heritage place."""

    cta_kind: str = Field(
        default="none",
        description="Call to action kind: none, story_journey, experience_inquiry, maker_profile.",
    )
    target_slug: Optional[str] = Field(
        default=None,
        description="Slug of the target story, maker, or experience.",
    )
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    notice: Optional[str] = None


# --------------------------------------------------------------------------- #
# Heritage Places: List & Detail Out
# --------------------------------------------------------------------------- #
class HeritagePlaceOut(BaseModel):
    """Summary representation of a heritage place for catalogue grids and search cards."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str = Field(..., description="URL-safe unique identifier.")
    name_vi: str = Field(..., description="Canonical Vietnamese name with correct diacritics.")
    name_en: Optional[str] = Field(default=None, description="Official English designation.")
    entity_type: HeritageEntityType
    heritage_category: str = Field(
        ...,
        description="Domain category (e.g. imperial_architecture, royal_tomb, craft_living_culture, music_performance).",
    )
    parent_id: Optional[UUID] = None
    official_designation: Optional[str] = Field(
        default=None,
        description="Official legal or UNESCO designation (e.g. UNESCO World Heritage Component, Special National Monument).",
    )
    official_reference_id: Optional[str] = Field(
        default=None,
        description="Formal inventory ID (e.g. UNESCO 678-001, 678-007).",
    )
    period_label: Optional[str] = Field(
        default=None,
        description="Historical epoch or construction era (e.g. Thời Nguyễn (1802-1945), Triều Tự Đức (1864)).",
    )
    historical_state: Optional[str] = Field(
        default=None,
        description="Architectural state: standing, restored, partially_lost, ruins, vanished.",
    )
    location_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    location_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    geo_precision: Optional[str] = Field(
        default=None,
        description="Precision level: exact_gps, approximate_site, polygon_centroid, none_intangible.",
    )
    current_access_status: str = Field(
        default="unknown",
        description="Visitor access status: open, restricted, undergoing_restoration, closed, unknown.",
    )
    visitor_summary_vi: Optional[str] = None
    visitor_summary_en: Optional[str] = None
    editorial_status: HeritageRecordStatus = HeritageRecordStatus.candidate
    content_scope: str = "RBPC_HUE"
    has_3d: bool = Field(default=False, description="Whether rights-cleared 3D media is available.")
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Slug cannot be empty.")
        return v


class HeritagePlaceDetailOut(HeritagePlaceOut):
    """Deep representation of a heritage place including relational evidence and media."""

    access_notes: Optional[str] = None
    historical_summary_vi: Optional[str] = None
    historical_summary_en: Optional[str] = None
    parent_place: Optional[HeritagePlaceOut] = None
    child_places: list[HeritagePlaceOut] = Field(default_factory=list)
    relations: list[HeritageRelationOut] = Field(default_factory=list)
    sources: list[HeritageSourceEvidenceOut] = Field(default_factory=list)
    media: list[HeritageMediaAssetOut] = Field(default_factory=list)
    engagement: Optional[HeritageEngagementOut] = None


class HeritagePlaceListOut(BaseModel):
    """Paginated list of heritage places with cursor pagination indicators."""

    items: list[HeritagePlaceOut]
    next_cursor: Optional[str] = Field(
        default=None,
        description="Opaque token to pass in cursor query param for next page, or null if end of catalogue.",
    )
    has_more: bool = Field(default=False, description="True if more records exist beyond this page.")
    total_count: Optional[int] = Field(
        default=None,
        description="Total published records matching query filters, when computed.",
    )


# --------------------------------------------------------------------------- #
# Search Schemas
# --------------------------------------------------------------------------- #
class HeritageSearchItemOut(BaseModel):
    """Individual search hit with highlight metadata and relevance score."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name_vi: str
    name_en: Optional[str] = None
    entity_type: HeritageEntityType
    heritage_category: str
    summary: Optional[str] = None
    matched_on: Optional[str] = Field(
        default=None,
        description="Field where match was found: name_vi, name_en, official_reference_id, summary.",
    )
    score: Optional[float] = None
    has_3d: bool = False
    thumbnail_url: Optional[str] = None


class HeritageSearchOut(BaseModel):
    """Unified search response across the heritage knowledge catalogue."""

    items: list[HeritageSearchItemOut]
    total: int
    query: str
    scope: str = "RBPC_HUE"
