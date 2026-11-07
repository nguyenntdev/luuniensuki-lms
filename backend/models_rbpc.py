# -*- coding: utf-8 -*-
"""SQLAlchemy 2.x declarative models for LƯU NIÊN — RBPC 2026.

Hue-wide Living Heritage Knowledge Catalogue & Commercial Vertical Slice:
- Heritage Knowledge Graph: places, relationships, source citations, media assets
- RBPC Commercial Slice: curated stories, claim evidence, consented creators,
  experiences, inquiries, allowlisted telemetry events, and append-only audit logs.

Content Scope: RBPC_HUE (isolated from legacy CUU_DINH).
Strict Additive Safety: All enum columns are stored as PostgreSQL TEXT with Python
Enum validation to prevent destructive DDL alterations.

Reference Specifications:
- Master Execution Goal V2 (§5.3, §V2-B.2)
- docs/rbpc/API_CONTRACTS.md
- docs/rbpc/DATABASE_CONTRACTS.md
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base_model import Base


# --------------------------------------------------------------------------- #
# Controlled Vocabularies & Enums (Python validation, stored as TEXT in DB)
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
    sketchfab_embed = "sketchfab_embed"
    glb = "glb"
    audio = "audio"
    video = "video"
    document = "document"


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


class HeritageAccuracyGrade(str, Enum):
    survey_grade = "survey_grade"
    measured_photogrammetry = "measured_photogrammetry"
    historian_reviewed = "historian_reviewed"
    illustrative_only = "illustrative_only"
    unreviewed = "unreviewed"
    rejected_accuracy = "rejected_accuracy"


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


class RbpcStoryStatus(str, Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    published = "published"
    archived = "archived"


class RbpcConsentStatus(str, Enum):
    consented = "consented"
    verified_written_consent = "verified_written_consent"
    pending_review = "pending_review"
    revoked = "revoked"


class RbpcAvailabilityMode(str, Enum):
    inquiry_only = "inquiry_only"
    disabled = "disabled"


class RbpcInquiryStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    confirmed = "confirmed"
    declined = "declined"
    closed = "closed"


class RbpcContactChannel(str, Enum):
    email = "email"
    phone = "phone"
    zalo = "zalo"


class RbpcSupportType(str, Enum):
    direct = "direct"
    contextual = "contextual"
    interpretation = "interpretation"
    unverified = "unverified"


class RbpcEpistemicCertainty(str, Enum):
    high = "high"
    medium = "medium"
    contested = "contested"
    insufficient_sources = "insufficient_sources"
    community_tradition = "community_tradition"


class RbpcNotificationStatus(str, Enum):
    queued = "queued"
    sending = "sending"
    sent = "sent"
    failed_retryable = "failed_retryable"
    failed = "failed"


class RbpcSettlementStatus(str, Enum):
    pending_compliance = "pending_compliance"
    approved = "approved"
    settled = "settled"
    refunded = "refunded"
    disputed = "disputed"


class RbpcPayoutStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    disbursed = "disbursed"
    withheld = "withheld"
    cancelled = "cancelled"


class RbpcReviewStatus(str, Enum):
    pending_moderation = "pending_moderation"
    published = "published"
    rejected = "rejected"
    disputed = "disputed"
    archived = "archived"


class RbpcDisputeStatus(str, Enum):
    opened = "opened"
    under_review = "under_review"
    resolved_upheld = "resolved_upheld"
    resolved_overturned = "resolved_overturned"
    dismissed = "dismissed"


class RbpcSlotStatus(str, Enum):
    open = "open"
    closed = "closed"
    cancelled = "cancelled"


class RbpcReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    expired = "expired"
    cancelled = "cancelled"


class RbpcAudioConsentScope(str, Enum):
    full_public = "full_public"
    educational_only = "educational_only"
    preview_only = "preview_only"
    revoked = "revoked"


class RbpcOralHistoryStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    consented = "consented"
    revoked = "revoked"
    erased = "erased"


class RbpcEvidenceDomain(str, Enum):
    product = "product"
    customer = "customer"
    market = "market"
    finances = "finances"
    impact = "impact"
    legal = "legal"
    team = "team"


class RbpcEvidencePointerStatus(str, Enum):
    active_verified = "active_verified"
    archived = "archived"
    needs_review = "needs_review"


class RbpcPitchClaimStatus(str, Enum):
    verified_observed = "VERIFIED_OBSERVED"
    verified_hypothesis = "VERIFIED_HYPOTHESIS"
    verified_projection = "VERIFIED_PROJECTION"
    ungrounded_flagged = "UNGROUNDED_FLAGGED"


class RbpcPitchReadiness(str, Enum):
    approved_for_pitch = "APPROVED_FOR_PITCH"
    flagged_unready = "FLAGGED_UNREADY"


class RbpcRevenueStream(str, Enum):
    visitor_commerce = "visitor_commerce"
    school_b2b = "school_b2b"


def _validate_enum(enum_cls: type[Enum], key: str, val: Any) -> str:
    """Validate that val matches an enum member or string value."""
    if isinstance(val, enum_cls):
        return str(val.value)
    if isinstance(val, str):
        allowed = {e.value for e in enum_cls}
        if val in allowed:
            return val
        raise ValueError(f"Invalid {key}: '{val}'. Must be one of {sorted(allowed)}")
    raise ValueError(f"Invalid {key}: expected {enum_cls.__name__} or str, got {type(val).__name__}")


# --------------------------------------------------------------------------- #
# Table 1: Heritage Places
# --------------------------------------------------------------------------- #
class HeritagePlace(Base):
    """Canonical heritage place or intangible cultural entry across Huế."""

    __tablename__ = "heritage_places"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_heritage_places_slug"),
        CheckConstraint(
            "location_lat IS NULL OR (location_lat >= -90.0 AND location_lat <= 90.0)",
            name="ck_heritage_places_lat_range",
        ),
        CheckConstraint(
            "location_lon IS NULL OR (location_lon >= -180.0 AND location_lon <= 180.0)",
            name="ck_heritage_places_lon_range",
        ),
        CheckConstraint(
            "entity_type IN ('site','monument','building','object','landscape','intangible','community','collection')",
            name="ck_heritage_places_entity_type",
        ),
        CheckConstraint(
            "editorial_status IN ('candidate','draft','source_backed','in_review','approved','published','withdrawn')",
            name="ck_heritage_places_editorial_status",
        ),
        Index("idx_heritage_places_category", "heritage_category"),
        Index("idx_heritage_places_type", "entity_type"),
        Index("idx_heritage_places_status", "editorial_status"),
        Index("idx_heritage_places_scope", "content_scope"),
        Index("idx_heritage_places_parent", "parent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    heritage_category: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="SET NULL"),
        nullable=True,
    )
    official_designation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    official_reference_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    period_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    location_lon: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    geo_precision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_access_status: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    access_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visitor_summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visitor_summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editorial_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageRecordStatus.candidate.value
    )
    content_scope: Mapped[str] = mapped_column(Text, nullable=False, default="RBPC_HUE")
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped[Optional[HeritagePlace]] = relationship(
        "HeritagePlace",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list[HeritagePlace]] = relationship(
        "HeritagePlace",
        back_populates="parent",
    )
    outgoing_relations: Mapped[list[HeritageHeritageRelation]] = relationship(
        "HeritageHeritageRelation",
        foreign_keys="[HeritageHeritageRelation.from_place_id]",
        back_populates="from_place",
        cascade="all, delete-orphan",
    )
    incoming_relations: Mapped[list[HeritageHeritageRelation]] = relationship(
        "HeritageHeritageRelation",
        foreign_keys="[HeritageHeritageRelation.to_place_id]",
        back_populates="to_place",
        cascade="all, delete-orphan",
    )
    sources: Mapped[list[HeritageSourceEvidence]] = relationship(
        "HeritageSourceEvidence",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    media_assets: Mapped[list[HeritageMediaAsset]] = relationship(
        "HeritageMediaAsset",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    stories: Mapped[list[RbpcStory]] = relationship(
        "RbpcStory",
        back_populates="place",
    )

    @validates("entity_type")
    def validate_entity_type(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageEntityType, key, value)

    @validates("editorial_status")
    def validate_editorial_status(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageRecordStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 2: Heritage Relationships
# --------------------------------------------------------------------------- #
class HeritageHeritageRelation(Base):
    """Bidirectional or hierarchical relationship between two heritage places."""

    __tablename__ = "heritage_heritage_relations"
    __table_args__ = (
        UniqueConstraint(
            "from_place_id",
            "to_place_id",
            "relationship_type",
            name="uq_heritage_relations_from_to_rel",
        ),
        Index("idx_heritage_relations_from", "from_place_id"),
        Index("idx_heritage_relations_to", "to_place_id"),
        Index("idx_heritage_relations_type", "relationship_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    from_place_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_place_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False)
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    from_place: Mapped[HeritagePlace] = relationship(
        "HeritagePlace",
        foreign_keys=[from_place_id],
        back_populates="outgoing_relations",
    )
    to_place: Mapped[HeritagePlace] = relationship(
        "HeritagePlace",
        foreign_keys=[to_place_id],
        back_populates="incoming_relations",
    )


# --------------------------------------------------------------------------- #
# Table 3: Heritage Source Evidence
# --------------------------------------------------------------------------- #
class HeritageSourceEvidence(Base):
    """Bibliographic source and evidentiary fact grounding a heritage place."""

    __tablename__ = "heritage_source_evidence"
    __table_args__ = (
        CheckConstraint(
            "evidence_status IN ('needs_review','verified','disputed','rejected')",
            name="ck_heritage_source_evidence_status",
        ),
        CheckConstraint(
            "reuse_rights IN ('public_domain','cc_by','cc_by_sa','cc_by_nc_sa','educational_fair_use','restricted','unknown')",
            name="ck_heritage_source_evidence_reuse",
        ),
        Index("idx_heritage_evidence_place", "place_id"),
        Index("idx_heritage_evidence_status", "evidence_status"),
        Index("idx_heritage_evidence_rights", "reuse_rights"),
        Index("idx_heritage_evidence_scope", "content_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    place_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_title: Mapped[str] = mapped_column(Text, nullable=False)
    source_author: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cited_section: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cited_page: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    interpretation_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageEvidenceStatus.needs_review.value
    )
    reuse_rights: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageReuseRights.unknown.value
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content_scope: Mapped[str] = mapped_column(Text, nullable=False, default="RBPC_HUE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    place: Mapped[HeritagePlace] = relationship("HeritagePlace", back_populates="sources")

    @validates("evidence_status")
    def validate_evidence_status(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageEvidenceStatus, key, value)

    @validates("reuse_rights")
    def validate_reuse_rights(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageReuseRights, key, value)


# --------------------------------------------------------------------------- #
# Table 4: Heritage Media Assets & 3D Governance
# --------------------------------------------------------------------------- #
class HeritageMediaAsset(Base):
    """Media asset with licensing governance, NoAI flag, and 3D viewer metadata."""

    __tablename__ = "heritage_media_assets"
    __table_args__ = (
        CheckConstraint(
            "media_type IN ('photo','sketchfab_embed','glb','audio','video','document')",
            name="ck_heritage_media_type",
        ),
        CheckConstraint(
            "commercial_use_status IN ('permitted','blocked_nc','unreviewed','requires_custom_grant')",
            name="ck_heritage_media_commercial_status",
        ),
        CheckConstraint(
            "embed_permission_status IN ('permitted','needs_rights_review','blocked','author_contacted')",
            name="ck_heritage_media_embed_status",
        ),
        CheckConstraint(
            "accuracy_grade IN ('survey_grade','measured_photogrammetry','historian_reviewed','illustrative_only','unreviewed','rejected_accuracy')",
            name="ck_heritage_media_accuracy_grade",
        ),
        Index("idx_heritage_media_place", "place_id"),
        Index("idx_heritage_media_type", "media_type"),
        Index("idx_heritage_media_model_uid", "model_uid"),
        Index("idx_heritage_media_noai", "noai"),
        Index("idx_heritage_media_status", "content_status"),
        Index("idx_heritage_media_scope", "content_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    place_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="CASCADE"),
        nullable=True,
    )
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_platform: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creator_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creator_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_uid: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    noai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    commercial_use_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageCommercialUseStatus.unreviewed.value
    )
    embed_permission_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageEmbedPermissionStatus.needs_rights_review.value
    )
    accuracy_grade: Mapped[str] = mapped_column(
        Text, nullable=False, default=HeritageAccuracyGrade.unreviewed.value
    )
    provenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attribution_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_status: Mapped[str] = mapped_column(Text, nullable=False, default="candidate")
    embed_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rights_reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rights_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content_scope: Mapped[str] = mapped_column(Text, nullable=False, default="RBPC_HUE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    place: Mapped[Optional[HeritagePlace]] = relationship(
        "HeritagePlace", back_populates="media_assets"
    )

    @validates("media_type")
    def validate_media_type(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageMediaType, key, value)

    @validates("commercial_use_status")
    def validate_commercial_use_status(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageCommercialUseStatus, key, value)

    @validates("embed_permission_status")
    def validate_embed_permission_status(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageEmbedPermissionStatus, key, value)

    @validates("accuracy_grade")
    def validate_accuracy_grade(self, key: str, value: Any) -> str:
        return _validate_enum(HeritageAccuracyGrade, key, value)


# --------------------------------------------------------------------------- #
# Table 5: RBPC Creators (Consented Artisans)
# --------------------------------------------------------------------------- #
class RbpcCreator(Base):
    """Living practitioner or craft master with written display consent."""

    __tablename__ = "rbpc_creators"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_rbpc_creators_slug"),
        CheckConstraint(
            "consent_status IN ('consented','verified_written_consent','pending_review','revoked')",
            name="ck_rbpc_creators_consent_status",
        ),
        Index("idx_rbpc_creators_consent", "consent_status"),
        Index("idx_rbpc_creators_verified", "is_verified"),
        Index("idx_rbpc_creators_place", "heritage_place_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    public_name: Mapped[str] = mapped_column(Text, nullable=False)
    craft_tradition: Mapped[str] = mapped_column(Text, nullable=False)
    craft_tradition_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_bio_vi: Mapped[str] = mapped_column(Text, nullable=False)
    approved_bio_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_portrait_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_region: Mapped[str] = mapped_column(Text, nullable=False, default="Huế")
    display_consent_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcConsentStatus.consented.value
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    years_of_practice: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_lineage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    heritage_place_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    identity_document_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rights_clearance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Aliases & properties for Pydantic schema compatibility
    @property
    def craft_tradition_vi(self) -> str:
        return self.craft_tradition

    @property
    def portrait_asset_url(self) -> Optional[str]:
        return self.approved_portrait_url

    @portrait_asset_url.setter
    def portrait_asset_url(self, value: Optional[str]) -> None:
        self.approved_portrait_url = value

    # Relationships
    heritage_place: Mapped[Optional[HeritagePlace]] = relationship("HeritagePlace")
    experiences: Mapped[list[RbpcExperience]] = relationship(
        "RbpcExperience",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    stories: Mapped[list[RbpcStory]] = relationship(
        "RbpcStory",
        back_populates="creator",
    )

    @validates("consent_status")
    def validate_consent_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcConsentStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 6: RBPC Experiences (Commercial Cultural Offerings)
# --------------------------------------------------------------------------- #
class RbpcExperience(Base):
    """Real-world cultural experience with honest inquiry-only booking mode."""

    __tablename__ = "rbpc_experiences"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_rbpc_experiences_slug"),
        CheckConstraint(
            "availability_mode IN ('inquiry_only','disabled')",
            name="ck_rbpc_experiences_avail_mode",
        ),
        Index("idx_rbpc_experiences_creator", "creator_id"),
        Index("idx_rbpc_experiences_avail", "availability_mode"),
        Index("idx_rbpc_experiences_pub", "publication_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    title_vi: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_vi: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    area_public: Mapped[str] = mapped_column(Text, nullable=False, default="Huế")
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pricing_display: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    indicative_price_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="VND")
    availability_mode: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcAvailabilityMode.inquiry_only.value
    )
    publication_state: Mapped[str] = mapped_column(Text, nullable=False, default="published")
    cancellation_policy_text_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancellation_policy_text_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_party_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=10)
    languages_supported: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=lambda: ["vi"]
    )
    notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rights_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator: Mapped[RbpcCreator] = relationship("RbpcCreator", back_populates="experiences")
    inquiries: Mapped[list[RbpcInquiry]] = relationship(
        "RbpcInquiry",
        back_populates="experience",
        cascade="all, delete-orphan",
    )
    stories: Mapped[list[RbpcStory]] = relationship(
        "RbpcStory",
        back_populates="experience",
    )
    workshop_slots: Mapped[list[RbpcWorkshopSlot]] = relationship(
        "RbpcWorkshopSlot",
        back_populates="experience",
        cascade="all, delete-orphan",
    )

    @validates("availability_mode")
    def validate_availability_mode(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcAvailabilityMode, key, value)


# --------------------------------------------------------------------------- #
# Table 7: RBPC Stories (Curated Story Journeys)
# --------------------------------------------------------------------------- #
class RbpcStory(Base):
    """Editorial narrative linking places, creators, and living craft traditions."""

    __tablename__ = "rbpc_stories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_rbpc_stories_slug"),
        CheckConstraint(
            "status IN ('draft','review','approved','published','archived')",
            name="ck_rbpc_stories_status",
        ),
        Index("idx_rbpc_stories_place", "place_id"),
        Index("idx_rbpc_stories_creator", "creator_id"),
        Index("idx_rbpc_stories_exp", "experience_id"),
        Index("idx_rbpc_stories_status", "status"),
        Index("idx_rbpc_stories_scope", "content_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title_vi: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intro_vi: Mapped[str] = mapped_column(Text, nullable=False)
    intro_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    place_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="SET NULL"),
        nullable=True,
    )
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="SET NULL"),
        nullable=True,
    )
    experience_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_experiences.id", ondelete="SET NULL"),
        nullable=True,
    )
    primary_asset_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_context_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    approved_summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcStoryStatus.draft.value
    )
    rights_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reading_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content_scope: Mapped[str] = mapped_column(Text, nullable=False, default="RBPC_HUE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    place: Mapped[Optional[HeritagePlace]] = relationship("HeritagePlace", back_populates="stories")
    creator: Mapped[Optional[RbpcCreator]] = relationship("RbpcCreator", back_populates="stories")
    experience: Mapped[Optional[RbpcExperience]] = relationship(
        "RbpcExperience", back_populates="stories"
    )
    claims: Mapped[list[RbpcClaimEvidence]] = relationship(
        "RbpcClaimEvidence",
        back_populates="story",
        cascade="all, delete-orphan",
    )

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcStoryStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 8: RBPC Claim Evidence (Story Grounding Claims)
# --------------------------------------------------------------------------- #
class RbpcClaimEvidence(Base):
    """Grounded factual assertion or craft technique citation supporting a story."""

    __tablename__ = "rbpc_claim_evidence"
    __table_args__ = (
        CheckConstraint(
            "support_type IN ('direct','contextual','interpretation','unverified')",
            name="ck_rbpc_claim_support_type",
        ),
        Index("idx_rbpc_claims_story", "story_id"),
        Index("idx_rbpc_claims_category", "claim_category"),
        Index("idx_rbpc_claims_status", "review_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_stories.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(Text, nullable=False, default="vi")
    claim_category: Mapped[str] = mapped_column(Text, nullable=False, default="historical_fact")
    source_ref_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    source_title: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    support_type: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcSupportType.direct.value
    )
    citation_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_excerpt_private: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    story: Mapped[RbpcStory] = relationship("RbpcStory", back_populates="claims")

    @property
    def notes(self) -> Optional[str]:
        """Alias for evidence_excerpt_private (reviewer/editorial notes)."""
        return self.evidence_excerpt_private

    @notes.setter
    def notes(self, value: Optional[str]) -> None:
        self.evidence_excerpt_private = value

    @validates("support_type")
    def validate_support_type(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcSupportType, key, value)


# --------------------------------------------------------------------------- #
# Table 9: RBPC Inquiries (Availability Requests, Zero PII Leaks)
# --------------------------------------------------------------------------- #
class RbpcInquiry(Base):
    """Inquiry-only booking request with opaque tracking and explicit consent."""

    __tablename__ = "rbpc_inquiries"
    __table_args__ = (
        UniqueConstraint("public_ref", name="uq_rbpc_inquiries_ref"),
        UniqueConstraint("idempotency_key", name="uq_rbpc_inquiries_idempotency"),
        UniqueConstraint("opaque_token", name="uq_rbpc_inquiries_token"),
        CheckConstraint(
            "contact_channel IN ('email','phone','zalo')",
            name="ck_rbpc_inquiries_contact_channel",
        ),
        CheckConstraint(
            "state IN ('new','contacted','confirmed','declined','closed')",
            name="ck_rbpc_inquiries_state",
        ),
        CheckConstraint(
            "party_size >= 1 AND party_size <= 50",
            name="ck_rbpc_inquiries_party_size",
        ),
        Index("idx_rbpc_inquiries_exp", "experience_id"),
        Index("idx_rbpc_inquiries_state", "state"),
        Index("idx_rbpc_inquiries_provider", "provider_id"),
        Index("idx_rbpc_inquiries_retention", "retention_due_at"),
        Index("idx_rbpc_inquiries_sla", "sla_due_at"),
        Index("idx_rbpc_inquiries_escalated", "escalated_at"),
        Index("idx_rbpc_inquiries_optin", "email_opt_in", "sms_opt_in"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    public_ref: Mapped[str] = mapped_column(Text, nullable=False)
    experience_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_experiences.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    contact_channel: Mapped[str] = mapped_column(Text, nullable=False)
    contact_value: Mapped[str] = mapped_column(Text, nullable=False)
    desired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_version: Mapped[str] = mapped_column(Text, nullable=False, default="rbpc-inquiry-v1")
    consent_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    privacy_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    state: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcInquiryStatus.new.value
    )
    internal_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    opaque_token: Mapped[str] = mapped_column(Text, nullable=False)
    retention_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    email_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notification_preferences: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    slot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_workshop_slots.id", ondelete="SET NULL"),
        nullable=True,
    )
    reservation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_seat_reservations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Aliases for Pydantic schema consistency
    @property
    def reference(self) -> str:
        return self.public_ref

    @property
    def status(self) -> str:
        return self.state

    @property
    def status_token(self) -> str:
        return self.opaque_token

    # Relationships
    experience: Mapped[RbpcExperience] = relationship("RbpcExperience", back_populates="inquiries")
    notifications: Mapped[list[RbpcNotificationOutbox]] = relationship(
        "RbpcNotificationOutbox",
        back_populates="inquiry",
        cascade="all, delete-orphan",
    )
    settlements: Mapped[list[RbpcSettlementLedger]] = relationship(
        "RbpcSettlementLedger",
        back_populates="inquiry",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[RbpcCustomerReview]] = relationship(
        "RbpcCustomerReview",
        back_populates="inquiry",
        cascade="all, delete-orphan",
    )
    workshop_slot: Mapped[Optional[RbpcWorkshopSlot]] = relationship(
        "RbpcWorkshopSlot",
        foreign_keys=[slot_id],
    )
    reservation: Mapped[Optional[RbpcSeatReservation]] = relationship(
        "RbpcSeatReservation",
        foreign_keys=[reservation_id],
    )

    @validates("contact_channel")
    def validate_contact_channel(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcContactChannel, key, value)

    @validates("state")
    def validate_state(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcInquiryStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 10: RBPC Events (Allowlisted Telemetry, Zero PII)
# --------------------------------------------------------------------------- #
class RbpcEvent(Base):
    """Anonymous telemetry events for cultural exploration and inquiry conversion."""

    __tablename__ = "rbpc_events"
    __table_args__ = (
        Index("idx_rbpc_events_name", "event_name"),
        Index("idx_rbpc_events_occurred", "occurred_at"),
        Index("idx_rbpc_events_session", "anonymous_session_id"),
        Index("idx_rbpc_events_story", "story_id"),
        Index("idx_rbpc_events_experience", "experience_id"),
        Index("idx_rbpc_events_place", "heritage_place_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    anonymous_session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_stories.id", ondelete="SET NULL"),
        nullable=True,
    )
    experience_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_experiences.id", ondelete="SET NULL"),
        nullable=True,
    )
    heritage_place_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("heritage_places.id", ondelete="SET NULL"),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    consent_scope: Mapped[str] = mapped_column(
        Text, nullable=False, default="telemetry_anonymous"
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# --------------------------------------------------------------------------- #
# Table 11: RBPC Content Audit (Append-Only Governance Log)
# --------------------------------------------------------------------------- #
class RbpcContentAudit(Base):
    """Append-only audit trail recording editorial transitions and cryptographic hashes."""

    __tablename__ = "rbpc_content_audit"
    __table_args__ = (
        Index("idx_rbpc_audit_entity", "entity_type", "entity_id"),
        Index("idx_rbpc_audit_action", "action"),
        Index("idx_rbpc_audit_created", "created_at"),
        Index("idx_rbpc_audit_actor", "actor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diff_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    approved_scope: Mapped[str] = mapped_column(Text, nullable=False, default="RBPC_HUE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# --------------------------------------------------------------------------- #
# Table 12: RBPC Notification Outbox (Partner Outbox Queue & SLA Tracking)
# --------------------------------------------------------------------------- #
class RbpcNotificationOutbox(Base):
    """Durable notification outbox queue for partner alerts with zero fake confirmations."""

    __tablename__ = "rbpc_notification_outbox"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','sending','sent','failed_retryable','failed')",
            name="ck_rbpc_notification_outbox_status",
        ),
        Index("idx_rbpc_notif_outbox_inquiry", "inquiry_id"),
        Index("idx_rbpc_notif_outbox_status", "status"),
        Index("idx_rbpc_notif_outbox_created", "created_at"),
        Index("idx_rbpc_notif_outbox_retry", "status", "next_retry_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inquiry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_inquiries.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False, default="inquiry_created")
    channel: Mapped[str] = mapped_column(Text, nullable=False, default="email")
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_masked: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_clean: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcNotificationStatus.queued.value
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    inquiry: Mapped[RbpcInquiry] = relationship("RbpcInquiry", back_populates="notifications")

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcNotificationStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 13: RBPC Fee & Revenue Settlement Ledger (Verified Transactions)
# --------------------------------------------------------------------------- #
class RbpcSettlementLedger(Base):
    """Immutable financial ledger for commercial settlements, contracted take rates,
    taxes, refunds, and artisan payouts after compliance approval.

    Negative abuse invariant (V5-T108):
    Merely transitioning an inquiry to 'confirmed' produces ZERO revenue in this
    ledger. A verified settlement record with positive amounts requires explicit
    settlement recording and compliance approval.
    """

    __tablename__ = "rbpc_settlement_ledger"
    __table_args__ = (
        UniqueConstraint("settlement_ref", name="uq_rbpc_settlement_ref"),
        CheckConstraint(
            "gross_amount_vnd >= 0.0",
            name="ck_rbpc_settlement_gross_nonneg",
        ),
        CheckConstraint(
            "take_rate >= 0.0 AND take_rate <= 1.0",
            name="ck_rbpc_settlement_take_rate_range",
        ),
        CheckConstraint(
            "status IN ('pending_compliance','approved','settled','refunded','disputed')",
            name="ck_rbpc_settlement_status",
        ),
        CheckConstraint(
            "payout_status IN ('pending','approved','disbursed','withheld','cancelled')",
            name="ck_rbpc_settlement_payout_status",
        ),
        CheckConstraint(
            "revenue_stream IN ('visitor_commerce', 'school_b2b')",
            name="ck_rbpc_settlement_revenue_stream",
        ),
        Index("idx_rbpc_settlement_inquiry", "inquiry_id"),
        Index("idx_rbpc_settlement_provider", "provider_id"),
        Index("idx_rbpc_settlement_creator", "creator_id"),
        Index("idx_rbpc_settlement_status", "status"),
        Index("idx_rbpc_settlement_payout", "payout_status"),
        Index("idx_rbpc_settlement_stream", "revenue_stream"),
        Index("idx_rbpc_settlement_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    settlement_ref: Mapped[str] = mapped_column(Text, nullable=False)
    inquiry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_inquiries.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Financial Breakdowns (in VND)
    gross_amount_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0
    )
    revenue_stream: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcRevenueStream.visitor_commerce.value, server_default=text("'visitor_commerce'")
    )
    take_rate: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.1500  # Default 15% platform contracted take rate
    )
    platform_fee_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0
    )
    tax_vat_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0  # VAT / applicable local taxes
    )
    artisan_payout_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0  # Net payout owed to artisan/provider
    )
    refund_amount_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0  # Deducted upon refund
    )

    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcSettlementStatus.pending_compliance.value
    )
    payout_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcPayoutStatus.pending.value
    )

    # Compliance & Verification metadata
    compliance_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    compliance_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    compliance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Settlement transaction proof
    transaction_proof_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="VND")
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    inquiry: Mapped[RbpcInquiry] = relationship("RbpcInquiry", back_populates="settlements")
    creator: Mapped[Optional[RbpcCreator]] = relationship("RbpcCreator")

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcSettlementStatus, key, value)

    @validates("payout_status")
    def validate_payout_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcPayoutStatus, key, value)

    @validates("revenue_stream")
    def validate_revenue_stream(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcRevenueStream, key, value)


# --------------------------------------------------------------------------- #
# Table 14: RBPC Verified Customer Reviews (Completed Inquiries Only)
# --------------------------------------------------------------------------- #
class RbpcCustomerReview(Base):
    """Verified customer reviews for cultural experiences.

    Negative abuse invariant (V5-T107):
    Only customers with verified completed experience inquiries (state == 'closed'
    and completion verified) can submit reviews. Uncompleted, fake, or cancelled
    inquiries cannot post ratings or reviews. Reviews pass through automated
    anti-fraud heuristics and moderation queue.
    """

    __tablename__ = "rbpc_customer_reviews"
    __table_args__ = (
        UniqueConstraint("inquiry_id", name="uq_rbpc_review_inquiry"),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_rbpc_review_rating_range",
        ),
        CheckConstraint(
            "status IN ('pending_moderation','published','rejected','disputed','archived')",
            name="ck_rbpc_review_status",
        ),
        Index("idx_rbpc_review_exp", "experience_id"),
        Index("idx_rbpc_review_status", "status"),
        Index("idx_rbpc_review_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inquiry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_inquiries.id", ondelete="CASCADE"),
        nullable=False,
    )
    experience_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_experiences.id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_display_name: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    verified_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcReviewStatus.pending_moderation.value
    )
    fraud_flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    moderated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    inquiry: Mapped[RbpcInquiry] = relationship("RbpcInquiry", back_populates="reviews")
    experience: Mapped[RbpcExperience] = relationship("RbpcExperience")
    disputes: Mapped[list[RbpcReviewDispute]] = relationship(
        "RbpcReviewDispute",
        back_populates="review",
        cascade="all, delete-orphan",
    )

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcReviewStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 15: RBPC Review Disputes (Partner / Customer Contestation Queue)
# --------------------------------------------------------------------------- #
class RbpcReviewDispute(Base):
    """Disputes filed against reviews by partners or customers for moderation review."""

    __tablename__ = "rbpc_review_disputes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('opened','under_review','resolved_upheld','resolved_overturned','dismissed')",
            name="ck_rbpc_dispute_status",
        ),
        Index("idx_rbpc_dispute_review", "review_id"),
        Index("idx_rbpc_dispute_status", "status"),
        Index("idx_rbpc_dispute_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_customer_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    disputant_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcDisputeStatus.opened.value
    )
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    review: Mapped[RbpcCustomerReview] = relationship("RbpcCustomerReview", back_populates="disputes")

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcDisputeStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 16: RBPC Workshop Availability Slots (Finite Seat Capacity & Schedules)
# --------------------------------------------------------------------------- #
class RbpcWorkshopSlot(Base):
    """Calendar time slot for a workshop offering with finite seat capacity.

    Negative abuse invariant (V5-T102):
    Concurrency race condition prevented: reserved_seats + confirmed_seats <= capacity
    is enforced at both application layer (with row-level pessimistic locks)
    and database storage engine layer (CheckConstraint ck_rbpc_slots_capacity_bound).
    Two concurrent requests cannot book or confirm the last remaining seat twice.
    """

    __tablename__ = "rbpc_workshop_slots"
    __table_args__ = (
        CheckConstraint(
            "capacity >= 1 AND capacity <= 100",
            name="ck_rbpc_slots_capacity_range",
        ),
        CheckConstraint(
            "reserved_seats >= 0",
            name="ck_rbpc_slots_reserved_nonneg",
        ),
        CheckConstraint(
            "confirmed_seats >= 0",
            name="ck_rbpc_slots_confirmed_nonneg",
        ),
        CheckConstraint(
            "reserved_seats + confirmed_seats <= capacity",
            name="ck_rbpc_slots_capacity_bound",
        ),
        CheckConstraint(
            "end_time > start_time",
            name="ck_rbpc_slots_time_valid",
        ),
        CheckConstraint(
            "status IN ('open','closed','cancelled')",
            name="ck_rbpc_slots_status",
        ),
        Index("idx_rbpc_slots_exp", "experience_id"),
        Index("idx_rbpc_slots_time", "start_time", "end_time"),
        Index("idx_rbpc_slots_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experience_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_experiences.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reserved_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcSlotStatus.open.value
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    experience: Mapped[RbpcExperience] = relationship(
        "RbpcExperience", back_populates="workshop_slots"
    )
    reservations: Mapped[list[RbpcSeatReservation]] = relationship(
        "RbpcSeatReservation",
        back_populates="slot",
        cascade="all, delete-orphan",
    )

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcSlotStatus, key, value)

    @property
    def available_seats(self) -> int:
        return max(0, self.capacity - self.confirmed_seats - self.reserved_seats)


# --------------------------------------------------------------------------- #
# Table 17: RBPC Workshop Seat Reservations (Hold Timeouts & Confirmations)
# --------------------------------------------------------------------------- #
class RbpcSeatReservation(Base):
    """Temporary hold or confirmed booking on seats in a workshop slot.

    Holds are subject to reserve timeouts (expires_at). Stale holds release
    seats automatically back to available inventory. Provider confirmation locks
    seats permanently.
    """

    __tablename__ = "rbpc_seat_reservations"
    __table_args__ = (
        UniqueConstraint("public_ref", name="uq_rbpc_reservations_public_ref"),
        UniqueConstraint("idempotency_key", name="uq_rbpc_reservations_idempotency"),
        CheckConstraint(
            "seats >= 1 AND seats <= 20",
            name="ck_rbpc_reservations_seats_range",
        ),
        CheckConstraint(
            "status IN ('pending','confirmed','expired','cancelled')",
            name="ck_rbpc_reservations_status",
        ),
        Index("idx_rbpc_reservations_slot", "slot_id"),
        Index("idx_rbpc_reservations_status", "status"),
        Index("idx_rbpc_reservations_expires", "expires_at"),
        Index("idx_rbpc_reservations_inquiry", "inquiry_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_workshop_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    inquiry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_inquiries.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    public_ref: Mapped[str] = mapped_column(Text, nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcReservationStatus.pending.value
    )
    hold_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=900)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    customer_contact: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    slot: Mapped[RbpcWorkshopSlot] = relationship(
        "RbpcWorkshopSlot", back_populates="reservations"
    )
    inquiry: Mapped[Optional[RbpcInquiry]] = relationship(
        "RbpcInquiry", foreign_keys=[inquiry_id]
    )

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcReservationStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 18: RBPC Oral History Recordings & Consent Studio (Living Memory & Right to Erasure)
# --------------------------------------------------------------------------- #
class RbpcOralHistoryRecording(Base):
    """Living practitioner oral history recording, cultural context, per-use consent,
    and right-to-erasure lifecycle.

    Negative abuse invariant (V5-T109):
    When consent is revoked or erased:
    1. Status transitions to 'revoked' or 'erased' with immutable timestamp and reason.
    2. Public endpoint immediately refuses to serve the audio and transcript with HTTP 403 / 410.
    3. Associated audio URL and content hashes are immediately purged and invalidated
       in both local memory and persistent CDN invalidation ledger (AssetCacheRevocation).
    """

    __tablename__ = "rbpc_oral_history_recordings"
    __table_args__ = (
        UniqueConstraint("creator_id", "recording_code", name="uq_rbpc_oral_history_code"),
        CheckConstraint(
            "consent_scope IN ('full_public','educational_only','preview_only','revoked')",
            name="ck_rbpc_oral_history_consent_scope",
        ),
        CheckConstraint(
            "status IN ('draft','submitted','consented','revoked','erased')",
            name="ck_rbpc_oral_history_status",
        ),
        Index("idx_rbpc_oral_history_creator", "creator_id"),
        Index("idx_rbpc_oral_history_status", "status"),
        Index("idx_rbpc_oral_history_scope", "consent_scope"),
        Index("idx_rbpc_oral_history_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="CASCADE"),
        nullable=False,
    )
    recording_code: Mapped[str] = mapped_column(Text, nullable=False)
    title_vi: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_sha256: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False, default="audio/webm")

    # Cultural context preservation
    cultural_context_vi: Mapped[str] = mapped_column(Text, nullable=False)
    cultural_context_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recording_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recording_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interviewer_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    epistemic_certainty: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcEpistemicCertainty.community_tradition.value
    )

    # Granular Per-Use Media Consent & Lifecycle
    consent_scope: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcAudioConsentScope.preview_only.value
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcOralHistoryStatus.draft.value
    )
    consent_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_agreement_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Right to Erasure / Revocation
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revoked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    erased_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Version tracking pointer (current active version)
    current_version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator: Mapped[RbpcCreator] = relationship("RbpcCreator")
    transcript_versions: Mapped[list[RbpcAudioTranscriptVersion]] = relationship(
        "RbpcAudioTranscriptVersion",
        back_populates="recording",
        cascade="all, delete-orphan",
        order_by="desc(RbpcAudioTranscriptVersion.version_number)",
    )

    @validates("consent_scope")
    def validate_consent_scope(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcAudioConsentScope, key, value)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcOralHistoryStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 19: RBPC Audio Transcript Versions (Timecoded Cues & Version History)
# --------------------------------------------------------------------------- #
class RbpcAudioTranscriptVersion(Base):
    """Versioned audio transcript with timecoded cues, bilingual text,
    and human artisan verification status.
    """

    __tablename__ = "rbpc_audio_transcript_versions"
    __table_args__ = (
        UniqueConstraint("recording_id", "version_number", name="uq_rbpc_audio_version"),
        Index("idx_rbpc_audio_ver_rec", "recording_id"),
        Index("idx_rbpc_audio_ver_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_oral_history_recordings.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    transcript_text_vi: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_text_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timed_cues: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_verified_by_artisan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artisan_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    recording: Mapped[RbpcOralHistoryRecording] = relationship(
        "RbpcOralHistoryRecording", back_populates="transcript_versions"
    )


# --------------------------------------------------------------------------- #
# Table 20: RBPC Startup Evidence Room Pointers (V5-T120 / W11-A10)
# --------------------------------------------------------------------------- #
class RbpcEvidencePointer(Base):
    """Versioned evidence pointer across product, customer, market, finances, impact, legal, and team."""

    __tablename__ = "rbpc_evidence_room_pointers"
    __table_args__ = (
        UniqueConstraint("pointer_id", name="uq_rbpc_evidence_pointer_id"),
        Index("idx_rbpc_evid_domain", "domain"),
        Index("idx_rbpc_evid_status", "status"),
        Index("idx_rbpc_evid_verified", "verified_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pointer_id: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    doc_ref: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcEvidencePointerStatus.active_verified.value
    )
    hash_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @validates("domain")
    def validate_domain(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcEvidenceDomain, key, value)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcEvidencePointerStatus, key, value)


# --------------------------------------------------------------------------- #
# Table 21: RBPC Pitch Review Audit Records (V5-T120 / W11-A10)
# --------------------------------------------------------------------------- #
class RbpcPitchReview(Base):
    """Immutable audit records for pitch review evaluations against evidence room."""

    __tablename__ = "rbpc_pitch_reviews"
    __table_args__ = (
        UniqueConstraint("audit_ref", name="uq_rbpc_pitch_audit_ref"),
        Index("idx_rbpc_pitch_readiness", "pitch_readiness"),
        Index("idx_rbpc_pitch_reviewed_at", "reviewed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_ref: Mapped[str] = mapped_column(Text, nullable=False)
    pitch_deck_title: Mapped[str] = mapped_column(Text, nullable=False)
    deck_version: Mapped[str] = mapped_column(Text, nullable=False)
    total_claims_audited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_claims_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ungrounded_claims_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pitch_readiness: Mapped[str] = mapped_column(
        Text, nullable=False, default=RbpcPitchReadiness.flagged_unready.value
    )
    claims_payload: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    audit_findings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @validates("pitch_readiness")
    def validate_pitch_readiness(self, key: str, value: Any) -> str:
        return _validate_enum(RbpcPitchReadiness, key, value)


# --------------------------------------------------------------------------- #
# Table 22: RBPC Partner Discovery & LOI Vault (V5-T113 / W11-A03)
# --------------------------------------------------------------------------- #
from .partner_loi_models import (  # noqa: E402, F401
    RbpcLoiConsentType,
    RbpcPartnerCategory,
    RbpcPartnerLoiStatus,
    RbpcPartnerLoiVault,
)


# --------------------------------------------------------------------------- #
# Table 23: RBPC Pilot Go/No-Go Board (V5-T129 / W12-A09)
# --------------------------------------------------------------------------- #
from .pilot_go_no_go_models import (  # noqa: E402, F401
    RbpcGoNoGoVerdict,
    RbpcIssueSeverity,
    RbpcIssueStatus,
    RbpcPilotGoNoGoEvaluation,
)







