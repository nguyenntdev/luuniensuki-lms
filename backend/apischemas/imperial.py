# -*- coding: utf-8 -*-
"""Pydantic v2 schemas for STTTNNĐ (Lưu Niên — Đại Nội Huế).

Request, response, and export/import DTOs for:
- Imperial Zones & Architectural Sites (summary, detail, timeline, evidence)
- Aerial Map Assets (detail, list, upload, review, publish)
- Map Annotations (normalized UV bounds, optimistic locking, links, audit)
- Pedagogical Lenses, Learning Paths & Steps
- Inquiry Activities & Student Submissions
- Historical Monument Media
- Full Dataset JSON Export / Import with schema versioning and SHA-256 integrity hash
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --------------------------------------------------------------------------- #
# Base Schema Configuration
# --------------------------------------------------------------------------- #
class ImperialBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --------------------------------------------------------------------------- #
# Zones
# --------------------------------------------------------------------------- #
class ImperialZoneBase(ImperialBaseSchema):
    slug: str = Field(..., min_length=1, max_length=100)
    title_vi: str = Field(..., min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    display_order: int = Field(default=0, ge=0)


class ImperialZoneCreate(ImperialZoneBase):
    pass


class ImperialZoneUpdate(ImperialBaseSchema):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    title_vi: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialZoneSummary(ImperialBaseSchema):
    id: UUID
    slug: str
    title_vi: str
    title_en: Optional[str] = None
    display_order: int
    site_count: Optional[int] = 0


class ImperialZoneOut(ImperialZoneBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


# --------------------------------------------------------------------------- #
# Media
# --------------------------------------------------------------------------- #
class ImperialMediaBase(ImperialBaseSchema):
    media_kind: str = Field(default="photo", max_length=50)
    url: str = Field(..., min_length=1, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    alt_text: Optional[str] = Field(default=None, max_length=255)
    license: str = Field(..., min_length=1, max_length=100)
    owner: Optional[str] = Field(default=None, max_length=255)
    credit: str = Field(..., min_length=1)
    historical_year: Optional[int] = None
    is_published: bool = False
    display_order: int = Field(default=0, ge=0)


class ImperialMediaCreate(ImperialMediaBase):
    site_id: UUID


class ImperialMediaUpdate(ImperialBaseSchema):
    media_kind: Optional[str] = Field(default=None, max_length=50)
    url: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    alt_text: Optional[str] = Field(default=None, max_length=255)
    license: Optional[str] = Field(default=None, max_length=100)
    owner: Optional[str] = Field(default=None, max_length=255)
    credit: Optional[str] = None
    historical_year: Optional[int] = None
    is_published: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialMediaOut(ImperialMediaBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    site_id: UUID
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


# --------------------------------------------------------------------------- #
# Sites
# --------------------------------------------------------------------------- #
class ImperialSiteBase(ImperialBaseSchema):
    slug: str = Field(..., min_length=1, max_length=100)
    name_vi: str = Field(..., min_length=1, max_length=255)
    name_en: Optional[str] = Field(default=None, max_length=255)
    name_han_nom: Optional[str] = Field(default=None, max_length=255)
    alternative_names: list[str] = Field(default_factory=list)
    site_type: str = Field(default="palace", max_length=50)
    condition: str = Field(default="extant", max_length=50)
    learning_level: str = Field(default="L1_DOCUMENTED", max_length=50)
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    historical_context: Optional[str] = None
    architectural_features: Optional[str] = None
    construction_year: Optional[int] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    is_published: bool = False
    display_order: int = Field(default=0, ge=0)


class ImperialSiteCreate(ImperialSiteBase):
    zone_id: UUID


class ImperialSiteUpdate(ImperialBaseSchema):
    zone_id: Optional[UUID] = None
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name_vi: Optional[str] = Field(default=None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(default=None, max_length=255)
    name_han_nom: Optional[str] = Field(default=None, max_length=255)
    alternative_names: Optional[list[str]] = None
    site_type: Optional[str] = Field(default=None, max_length=50)
    condition: Optional[str] = Field(default=None, max_length=50)
    learning_level: Optional[str] = Field(default=None, max_length=50)
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    historical_context: Optional[str] = None
    architectural_features: Optional[str] = None
    construction_year: Optional[int] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    is_published: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialSiteSummary(ImperialBaseSchema):
    id: UUID
    zone_id: UUID
    slug: str
    name_vi: str
    name_en: Optional[str] = None
    site_type: str
    condition: str
    learning_level: str
    is_published: bool
    display_order: int


class ImperialSiteDetail(ImperialSiteBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    zone_id: UUID
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
    zone: Optional[ImperialZoneSummary] = None
    media: list[ImperialMediaOut] = Field(default_factory=list)


class ImperialSiteTimelineItem(ImperialBaseSchema):
    year: Optional[int] = None
    period_label: Optional[str] = None
    event_title: str
    description: Optional[str] = None
    source_ref: Optional[str] = None
    is_verified: bool = True


class ImperialSiteTimeline(ImperialBaseSchema):
    site_slug: str
    site_name_vi: str
    timeline: list[ImperialSiteTimelineItem] = Field(default_factory=list)


class ImperialSiteEvidenceItem(ImperialBaseSchema):
    claim_id: Optional[UUID] = None
    claim_type: str
    assertion_vi: str
    confidence_level: str
    source_title: str
    source_citation: Optional[str] = None
    verification_status: str


class ImperialSiteEvidence(ImperialBaseSchema):
    site_slug: str
    site_name_vi: str
    evidence: list[ImperialSiteEvidenceItem] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Map Assets
# --------------------------------------------------------------------------- #
class ImperialMapAssetBase(ImperialBaseSchema):
    title_vi: str = Field(..., min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    version: int = Field(default=1, ge=1)
    width_px: int = Field(..., ge=1, le=100000)
    height_px: int = Field(..., ge=1, le=100000)
    source_title: str = Field(..., min_length=1, max_length=255)
    source_locator: Optional[str] = Field(default=None, max_length=255)
    copyright_holder: Optional[str] = Field(default=None, max_length=255)
    credit_text: str = Field(..., min_length=1)
    license_kind: str = Field(..., min_length=1, max_length=100)
    license_evidence_key: Optional[str] = Field(default=None, max_length=500)


class ImperialMapAssetUpload(ImperialMapAssetBase):
    image_storage_key: str = Field(..., min_length=1, max_length=500)
    preview_storage_key: Optional[str] = Field(default=None, max_length=500)
    image_sha256: str = Field(..., min_length=64, max_length=64)
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]


class ImperialMapAssetSummary(ImperialBaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    title_vi: str
    title_en: Optional[str] = None
    slug: str
    version: int
    width_px: int
    height_px: int
    license_kind: str
    license_status: str
    review_status: str
    is_active: bool


class ImperialMapAssetDetail(ImperialMapAssetBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    image_storage_key: str
    preview_storage_key: Optional[str] = None
    image_sha256: str
    mime_type: str
    license_status: str
    review_status: str
    is_active: bool
    created_by: UUID
    approved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    row_version: int = 1


class ImperialMapAssetReview(ImperialBaseSchema):
    action: Literal["approve", "reject", "request_changes"]
    notes: Optional[str] = None


class ImperialMapAssetPublish(ImperialBaseSchema):
    is_active: bool = True
    row_version: int = Field(..., ge=1, description="Current row_version for optimistic lock check")


# --------------------------------------------------------------------------- #
# Map Annotations & Links
# --------------------------------------------------------------------------- #
class ImperialAnnotationBase(ImperialBaseSchema):
    shape_type: Literal["point", "polygon", "bbox"] = "point"
    u: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized horizontal coordinate on aerial map [0.0, 1.0]",
    )
    v: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized vertical coordinate on aerial map [0.0, 1.0]",
    )
    polygon_uv: Optional[list[list[float]]] = Field(
        default=None,
        description="Polygon vertices as list of [u, v] pairs, each coordinate between 0.0 and 1.0",
    )
    label: Optional[str] = Field(default=None, max_length=255)
    marker_style: str = Field(default="monument", max_length=50)
    z_index: int = Field(default=0)
    is_visible: bool = True
    position_confidence: Literal["verified", "approximate", "uncertain"] = "approximate"
    position_source_ref: Optional[str] = None
    editorial_notes: Optional[str] = None

    @field_validator("polygon_uv")
    @classmethod
    def validate_polygon_uv(
        cls, v: Optional[list[list[float]]]
    ) -> Optional[list[list[float]]]:
        if v is None:
            return None
        if len(v) < 3:
            raise ValueError("polygon_uv must contain at least 3 vertices")
        for i, pt in enumerate(v):
            if len(pt) != 2:
                raise ValueError(
                    f"polygon vertex at index {i} must have exactly 2 coordinates [u, v]"
                )
            pu, pv = pt[0], pt[1]
            if not (0.0 <= pu <= 1.0) or not (0.0 <= pv <= 1.0):
                raise ValueError(
                    f"polygon vertex at index {i} ({pu}, {pv}) is outside normalized bounds [0.0, 1.0]"
                )
        return v


class ImperialAnnotationCreate(ImperialAnnotationBase):
    map_asset_id: UUID
    site_id: UUID


class ImperialAnnotationUpdate(ImperialBaseSchema):
    u: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    v: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    shape_type: Optional[Literal["point", "polygon", "bbox"]] = None
    polygon_uv: Optional[list[list[float]]] = None
    label: Optional[str] = Field(default=None, max_length=255)
    marker_style: Optional[str] = Field(default=None, max_length=50)
    z_index: Optional[int] = None
    is_visible: Optional[bool] = None
    review_status: Optional[
        Literal["draft", "in_review", "approved", "published", "archived"]
    ] = None
    position_confidence: Optional[
        Literal["verified", "approximate", "uncertain"]
    ] = None
    position_source_ref: Optional[str] = None
    editorial_notes: Optional[str] = None
    row_version: int = Field(
        ..., ge=1, description="Required current row_version for optimistic concurrency check"
    )

    @field_validator("polygon_uv")
    @classmethod
    def validate_polygon_uv(
        cls, v: Optional[list[list[float]]]
    ) -> Optional[list[list[float]]]:
        if v is None:
            return None
        if len(v) < 3:
            raise ValueError("polygon_uv must contain at least 3 vertices")
        for i, pt in enumerate(v):
            if len(pt) != 2:
                raise ValueError(
                    f"polygon vertex at index {i} must have exactly 2 coordinates [u, v]"
                )
            pu, pv = pt[0], pt[1]
            if not (0.0 <= pu <= 1.0) or not (0.0 <= pv <= 1.0):
                raise ValueError(
                    f"polygon vertex at index {i} ({pu}, {pv}) is outside normalized bounds [0.0, 1.0]"
                )
        return v


class ImperialAnnotationLinkCreate(ImperialBaseSchema):
    target_type: Literal["story", "lesson", "source", "quiz", "activity", "trail"]
    target_id: UUID
    sort_order: int = Field(default=0, ge=0)


class ImperialAnnotationLinkOut(ImperialBaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    annotation_id: UUID
    target_type: str
    target_id: UUID
    sort_order: int


class ImperialAnnotationAuditOut(ImperialBaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    annotation_id: UUID
    actor_id: Optional[UUID] = None
    action: str
    before_json: Optional[Any] = None
    after_json: Optional[Any] = None
    created_at: datetime


class ImperialAnnotationOut(ImperialAnnotationBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    map_asset_id: UUID
    site_id: UUID
    review_status: str
    created_by: UUID
    updated_by: UUID
    approved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    row_version: int = 1
    site: Optional[ImperialSiteSummary] = None
    links: list[ImperialAnnotationLinkOut] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Lenses
# --------------------------------------------------------------------------- #
class ImperialLensBase(ImperialBaseSchema):
    code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    prompt: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=50)
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class ImperialLensCreate(ImperialLensBase):
    pass


class ImperialLensUpdate(ImperialBaseSchema):
    code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    prompt: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=50)
    display_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialLensOut(ImperialLensBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


class ImperialLensSiteCreate(ImperialBaseSchema):
    lens_id: UUID
    site_id: UUID
    relevance_score: float = Field(default=1.0, ge=0.0)
    sequence: int = Field(default=0, ge=0)
    curatorial_notes: Optional[str] = None


class ImperialLensSiteOut(ImperialBaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    lens_id: UUID
    site_id: UUID
    relevance_score: float
    sequence: int
    curatorial_notes: Optional[str] = None
    site: Optional[ImperialSiteSummary] = None


# --------------------------------------------------------------------------- #
# Learning Paths & Steps
# --------------------------------------------------------------------------- #
class ImperialPathStepBase(ImperialBaseSchema):
    site_id: UUID
    step_order: int = Field(default=0, ge=0)
    title: Optional[str] = Field(default=None, max_length=255)
    prompt: str = Field(..., min_length=1)
    source_requirement: Optional[str] = None
    rubrics: Optional[Any] = None
    estimated_minutes: int = Field(default=10, ge=1)


class ImperialPathStepCreate(ImperialPathStepBase):
    pass


class ImperialPathStepOut(ImperialPathStepBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    path_id: UUID
    site: Optional[ImperialSiteSummary] = None


class ImperialLearningPathBase(ImperialBaseSchema):
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    kind: str = Field(default="standard", max_length=50)
    duration_min: int = Field(default=45, ge=1)
    age_group: str = Field(default="all", max_length=50)
    learning_objectives: list[str] = Field(default_factory=list)
    prerequisites: Optional[str] = None
    review_status: Literal["draft", "published", "archived"] = "draft"
    is_published: bool = False
    display_order: int = Field(default=0, ge=0)


class ImperialLearningPathCreate(ImperialLearningPathBase):
    steps: list[ImperialPathStepCreate] = Field(default_factory=list)


class ImperialLearningPathUpdate(ImperialBaseSchema):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    kind: Optional[str] = Field(default=None, max_length=50)
    duration_min: Optional[int] = Field(default=None, ge=1)
    age_group: Optional[str] = Field(default=None, max_length=50)
    learning_objectives: Optional[list[str]] = None
    prerequisites: Optional[str] = None
    review_status: Optional[Literal["draft", "published", "archived"]] = None
    is_published: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialLearningPathSummary(ImperialBaseSchema):
    id: UUID
    slug: str
    title: str
    title_en: Optional[str] = None
    kind: str
    duration_min: int
    age_group: str
    is_published: bool
    display_order: int


class ImperialLearningPathDetail(ImperialLearningPathBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    row_version: int = 1
    steps: list[ImperialPathStepOut] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Activities & Student Submissions
# --------------------------------------------------------------------------- #
class ImperialActivityBase(ImperialBaseSchema):
    site_id: Optional[UUID] = None
    path_id: Optional[UUID] = None
    activity_type: str = Field(default="evidence_reflection", max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    instructions: str = Field(..., min_length=1)
    rubric_json: Optional[Any] = None
    max_points: int = Field(default=100, ge=1)
    is_active: bool = True


class ImperialActivityCreate(ImperialActivityBase):
    pass


class ImperialActivityUpdate(ImperialBaseSchema):
    site_id: Optional[UUID] = None
    path_id: Optional[UUID] = None
    activity_type: Optional[str] = Field(default=None, max_length=50)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    instructions: Optional[str] = None
    rubric_json: Optional[Any] = None
    max_points: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None
    row_version: Optional[int] = Field(default=None, ge=1)


class ImperialActivityOut(ImperialActivityBase):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    created_at: datetime
    updated_at: datetime
    row_version: int = 1


class ImperialSubmissionCreate(ImperialBaseSchema):
    activity_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    answer_text: str = Field(..., min_length=1)
    evidence_refs: list[Any] = Field(default_factory=list)


class ImperialSubmissionGrade(ImperialBaseSchema):
    score: Optional[float] = Field(default=None, ge=0.0)
    rubric_scores: Optional[dict[str, int]] = Field(
        default=None,
        description="Rubric scores S1-S4 (0-3 scale each: S1_spatial, S2_temporal, S3_evidence, S4_argument)",
    )
    feedback: Optional[str] = None
    status: Literal["graded", "resubmit_requested"] = "graded"


class ImperialSubmissionOut(ImperialBaseSchema):
    id: UUID
    content_scope: str = "STTT_IMPERIAL_CITY"
    activity_id: UUID
    student_id: UUID
    classroom_id: Optional[UUID] = None
    status: Literal["submitted", "graded", "resubmit_requested"]
    answer_text: str
    evidence_refs: list[Any] = Field(default_factory=list)
    score: Optional[float] = None
    rubric_scores: Optional[dict[str, Any]] = None
    feedback: Optional[str] = None
    graded_by: Optional[UUID] = None
    graded_at: Optional[datetime] = None
    submitted_at: datetime
    updated_at: datetime
    row_version: int = 1


# --------------------------------------------------------------------------- #
# AI Tutor (STTT Scope-Locked)
# --------------------------------------------------------------------------- #
class ImperialAIAskRequest(ImperialBaseSchema):
    query: str = Field(..., min_length=1, description="Historical inquiry question about Dai Noi")
    site_slug: Optional[str] = Field(default=None, description="Optional slug of site in focus (e.g. 'ngo-mon', 'dien-thai-hoa')")
    context: Optional[str] = Field(default=None, description="Optional student/classroom context")


class ImperialAISourceRef(ImperialBaseSchema):
    source_title: str
    citation: Optional[str] = None
    volume_or_chapter: Optional[str] = None
    archival_unit: Optional[str] = None
    reliability_level: Optional[str] = "verified_primary_source"


class ImperialAICertaintyUncertainty(ImperialBaseSchema):
    certainty: str = Field(default="", description="Điều chắc chắn (Certainty verified by primary sources)")
    uncertainty: str = Field(default="", description="Điều cần kiểm chứng thêm (Epistemic uncertainty)")


class ImperialAIAskResponse(ImperialBaseSchema):
    content_scope: Literal["STTT_IMPERIAL_CITY"] = "STTT_IMPERIAL_CITY"
    insufficient_evidence: bool = Field(default=False, description="True if question is outside Dai Noi or forbidden")
    message: Optional[str] = Field(default=None, description="Direct answer or polite refusal message")
    inquiry_answer: str = Field(default="", description="(1) Trả lời gợi mở tư duy")
    sources_cited: list[ImperialAISourceRef] = Field(default_factory=list, description="(2) Nguồn sử liệu đối chiếu")
    certainty_vs_uncertainty: ImperialAICertaintyUncertainty = Field(
        default_factory=ImperialAICertaintyUncertainty,
        description="(3) Điều chắc chắn vs Điều cần kiểm chứng thêm",
    )
    site_slug: Optional[str] = None


# --------------------------------------------------------------------------- #
# JSON Export / Import Payload Schemas
# --------------------------------------------------------------------------- #
class ImperialExportPayload(ImperialBaseSchema):
    """Full pedagogical dataset export payload for STTTNNĐ with verification hash."""

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    content_scope: Literal["STTT_IMPERIAL_CITY"] = "STTT_IMPERIAL_CITY"
    zones: list[ImperialZoneOut] = Field(default_factory=list)
    sites: list[ImperialSiteDetail] = Field(default_factory=list)
    map_assets: list[ImperialMapAssetDetail] = Field(default_factory=list)
    annotations: list[ImperialAnnotationOut] = Field(default_factory=list)
    lenses: list[ImperialLensOut] = Field(default_factory=list)
    learning_paths: list[ImperialLearningPathDetail] = Field(default_factory=list)
    activities: list[ImperialActivityOut] = Field(default_factory=list)
    verification_hash: str = Field(
        ...,
        description="SHA-256 integrity hash of canonical payload contents (excluding hash field itself)",
    )

    @classmethod
    def compute_hash(cls, payload_dict: dict[str, Any]) -> str:
        """Compute SHA-256 hash across canonical sorted representation of all payload fields except verification_hash."""
        filtered = {k: v for k, v in payload_dict.items() if k != "verification_hash"}
        canonical_json = json.dumps(filtered, sort_keys=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify verification_hash matches freshly computed hash of the contents."""
        data = self.model_dump(mode="json")
        expected_hash = self.compute_hash(data)
        return hmac.compare_digest(self.verification_hash, expected_hash)


class ImperialImportPayload(ImperialBaseSchema):
    """Import payload received from external/backup sources for verification before insertion."""

    schema_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    exported_at: Optional[datetime] = None
    content_scope: Literal["STTT_IMPERIAL_CITY"] = "STTT_IMPERIAL_CITY"
    zones: list[ImperialZoneCreate] = Field(default_factory=list)
    sites: list[ImperialSiteCreate] = Field(default_factory=list)
    map_assets: list[ImperialMapAssetUpload] = Field(default_factory=list)
    annotations: list[ImperialAnnotationCreate] = Field(default_factory=list)
    lenses: list[ImperialLensCreate] = Field(default_factory=list)
    learning_paths: list[ImperialLearningPathCreate] = Field(default_factory=list)
    activities: list[ImperialActivityCreate] = Field(default_factory=list)
    verification_hash: str

    @classmethod
    def compute_hash(cls, payload_dict: dict[str, Any]) -> str:
        """Compute SHA-256 hash across canonical sorted representation of all payload fields except verification_hash."""
        filtered = {k: v for k, v in payload_dict.items() if k != "verification_hash"}
        canonical_json = json.dumps(filtered, sort_keys=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify verification_hash against payload content."""
        data = self.model_dump(mode="json", exclude_unset=True)
        expected_hash = self.compute_hash(data)
        if hmac.compare_digest(self.verification_hash, expected_hash):
            return True
        data_all = self.model_dump(mode="json")
        expected_hash_all = self.compute_hash(data_all)
        return hmac.compare_digest(self.verification_hash, expected_hash_all)
