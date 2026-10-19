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
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="verified")
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
