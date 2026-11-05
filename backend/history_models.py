# -*- coding: utf-8 -*-
"""Historical domain models — History-First Phase 1.

Entity / claim / source / relation / geography / asset / audit tables described
in docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part III. Imported by
``backend.models`` so ``Base.metadata`` (used by conftest create_all and Alembic
autogenerate) includes these tables.

DB types are stored as TEXT with Python enums for the controlled vocabularies
(registry-friendly evolution per HP-07 / section 6.2).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


# --------------------------------------------------------------------------- #
# Controlled vocabularies
# --------------------------------------------------------------------------- #
class HistoricalEntityType(str, Enum):
    urn = "urn"
    relief = "relief"
    person = "person"
    place = "place"
    event = "event"
    period = "period"
    dynasty = "dynasty"
    reign = "reign"
    object = "object"
    species = "species"
    concept = "concept"
    institution = "institution"
    document = "document"
    artwork = "artwork"
    technique = "technique"
    water_body = "water_body"
    mountain = "mountain"
    island = "island"
    settlement = "settlement"
    region = "region"


class HistoricalPublicationStatus(str, Enum):
    draft = "draft"
    internal_review = "internal_review"
    public_unverified = "public_unverified"
    verified = "verified"
    published = "published"
    disputed = "disputed"
    archived = "archived"


class HistoricalClaimType(str, Enum):
    factual = "factual"
    chronology = "chronology"
    geographic = "geographic"
    identification = "identification"
    attribution = "attribution"
    material = "material"
    measurement = "measurement"
    production = "production"
    symbolism = "symbolism"
    interpretation = "interpretation"
    traditional_account = "traditional_account"
    modern_interpretation = "modern_interpretation"
    disputed = "disputed"
    classification = "classification"
    relationship = "relationship"
    translation = "translation"
    etymology = "etymology"


class HistoricalVerificationStatus(str, Enum):
    unreviewed = "unreviewed"
    needs_source = "needs_source"
    source_attached = "source_attached"
    editor_reviewed = "editor_reviewed"
    expert_verified = "expert_verified"
    rejected = "rejected"
    disputed = "disputed"
    superseded = "superseded"
    draft = "draft"
    internal_review = "internal_review"
    verified = "verified"
    published = "published"
    archived = "archived"


class HistoricalConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"
    disputed = "disputed"
    contested = "contested"
    insufficient_sources = "insufficient_sources"


class HistoricalEpistemicCertainty(str, Enum):
    high = "high"
    medium = "medium"
    contested = "contested"
    insufficient_sources = "insufficient_sources"


class HistoricalClaimOrigin(str, Enum):
    legacy_import = "legacy_import"
    editorial = "editorial"
    authoritative_import = "authoritative_import"
    ai_generated = "ai_generated"
    community = "community"
    teacher = "teacher"
    student = "student"
    system_inferred = "system_inferred"


class HistoricalRiskLevel(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class HistoricalSourceType(str, Enum):
    primary_source = "primary_source"
    royal_record = "royal_record"
    archival_record = "archival_record"
    inscription = "inscription"
    museum_catalog = "museum_catalog"
    heritage_authority = "heritage_authority"
    government_publication = "government_publication"
    scholarly_book = "scholarly_book"
    peer_reviewed_article = "peer_reviewed_article"
    dissertation = "dissertation"
    conference_paper = "conference_paper"
    critical_edition = "critical_edition"
    reference_work = "reference_work"
    trusted_website = "trusted_website"
    newspaper = "newspaper"
    oral_history = "oral_history"
    community_source = "community_source"
    other = "other"


class HistoricalSourceVerificationStatus(str, Enum):
    unreviewed = "unreviewed"
    metadata_verified = "metadata_verified"
    accessible = "accessible"
    inaccessible = "inaccessible"
    rights_restricted = "rights_restricted"
    rejected = "rejected"


class HistoricalSupportType(str, Enum):
    supports = "supports"
    partially_supports = "partially_supports"
    contextualizes = "contextualizes"
    contradicts = "contradicts"
    mentions = "mentions"
    primary_evidence_for = "primary_evidence_for"
    secondary_interpretation_of = "secondary_interpretation_of"


class HistoricalRelationPredicate(str, Enum):
    located_on = "located_on"
    depicts = "depicts"
    associated_with = "associated_with"
    commissioned_by = "commissioned_by"
    cast_during = "cast_during"
    cast_at = "cast_at"
    created_during = "created_during"
    predecessor_of = "predecessor_of"
    successor_of = "successor_of"
    represents = "represents"
    located_in = "located_in"
    flows_through = "flows_through"
    part_of = "part_of"
    member_of = "member_of"
    mentioned_in = "mentioned_in"
    contemporaneous_with = "contemporaneous_with"
    commemorates = "commemorates"
    identified_as = "identified_as"
    related_to = "related_to"
    source_for = "source_for"
    influenced_by = "influenced_by"
    near = "near"
    maps_to_modern_place = "maps_to_modern_place"


class HistoricalGeoPrecision(str, Enum):
    exact = "exact"
    approximate = "approximate"
    settlement = "settlement"
    region = "region"
    water_body = "water_body"
    historical_boundary = "historical_boundary"
    modern_correspondence = "modern_correspondence"
    unknown = "unknown"


class HistoricalMappingStatus(str, Enum):
    verified = "verified"
    probable = "probable"
    disputed = "disputed"
    unknown = "unknown"


class HistoricalAssetType(str, Enum):
    photo = "photo"
    relief_crop = "relief_crop"
    model_3d = "3d_model"
    texture_3d = "3d_texture"
    map = "map"
    scan = "scan"
    illustration = "illustration"
    audio = "audio"
    video = "video"
    document_thumbnail = "document_thumbnail"


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class HistoricalEntity(Base):
    __tablename__ = "historical_entities"
    __table_args__ = (
        UniqueConstraint("slug"),
        Index("uq_historical_entities_slug", "slug"),
        Index("idx_historical_entities_type", "entity_type"),
        Index("idx_historical_entities_pub", "publication_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    name_han_nom: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alternative_names: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_precision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geo_precision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    publication_status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    claims: Mapped[list["HistoricalClaim"]] = relationship(
        "HistoricalClaim", back_populates="entity", cascade="all, delete-orphan"
    )
    geographies: Mapped[list["HistoricalGeography"]] = relationship(
        "HistoricalGeography", back_populates="entity", cascade="all, delete-orphan"
    )


class HistoricalSource(Base):
    __tablename__ = "historical_sources"
    __table_args__ = (
        Index("idx_historical_sources_type", "source_type"),
        Index("idx_historical_sources_year", "publication_year"),
        Index("idx_historical_sources_scope", "content_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editor_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    volume: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archive_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repository_identifier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rights_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attribution_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_display_allowed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    derivative_allowed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    content_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    checksum: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @property
    def is_approved(self) -> bool:
        """Indicate whether this source is verified and cleared for retrieval."""
        return self.verification_status in ("metadata_verified", "accessible")



class HistoricalClaim(Base):
    __tablename__ = "historical_claims"
    __table_args__ = (
        Index("idx_historical_claims_entity", "entity_id"),
        Index("idx_historical_claims_entity_ver", "entity_id", "verification_status"),
        Index("idx_historical_claims_type", "claim_type"),
        Index("idx_historical_claims_current", "entity_id", "is_current"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="CASCADE"), nullable=False
    )
    claim_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False)
    statement_vi: Mapped[str] = mapped_column(Text, nullable=False)
    statement_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_precision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False, default="normal")
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    supersedes_claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_claims.id"), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    content_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    @property
    def epistemic_certainty(self) -> str:
        if self.confidence in ("contested", "disputed") or self.verification_status == "disputed":
            return HistoricalEpistemicCertainty.contested.value
        if self.confidence == "insufficient_sources" or self.verification_status in ("needs_source", "unreviewed"):
            return HistoricalEpistemicCertainty.insufficient_sources.value
        if self.confidence == "high" and self.verification_status in ("expert_verified", "editor_reviewed"):
            return HistoricalEpistemicCertainty.high.value
        if self.confidence in ("high", "medium") or self.verification_status in ("editor_reviewed", "source_attached"):
            return HistoricalEpistemicCertainty.medium.value
        return HistoricalEpistemicCertainty.insufficient_sources.value

    @epistemic_certainty.setter
    def epistemic_certainty(self, val: str) -> None:
        if val in ("contested", "disputed"):
            self.confidence = HistoricalConfidence.contested.value
        elif val == "insufficient_sources":
            self.confidence = HistoricalConfidence.insufficient_sources.value
        elif val in ("high", "medium"):
            self.confidence = val
        else:
            self.confidence = str(val)

    @property
    def is_approved(self) -> bool:
        """Indicate whether this claim is officially approved/verified and current."""
        if not getattr(self, "is_current", True):
            return False
        if self.verification_status not in ("expert_verified", "editor_reviewed", "verified", "published"):
            return False
        if self.confidence in ("disputed", "contested", "unknown"):
            return False
        if self.claim_type == "disputed":
            return False
        return True

    @property
    def is_published(self) -> bool:
        """Indicate whether this claim is officially in published status."""
        return self.is_approved and self.verification_status == "published"

    @property
    def is_draft(self) -> bool:
        """Indicate whether this claim is in draft or internal review status."""
        return self.verification_status in ("draft", "internal_review")

    @property
    def is_unreviewed(self) -> bool:
        """Indicate whether this claim is unreviewed or pending sources."""
        return self.verification_status in ("unreviewed", "needs_source", "source_attached")

    @property
    def is_disputed(self) -> bool:
        """Indicate whether this claim is disputed, rejected, or contested."""
        return (
            self.verification_status in ("disputed", "rejected", "superseded", "archived")
            or self.confidence in ("disputed", "contested")
            or self.claim_type == "disputed"
        )

    entity: Mapped["HistoricalEntity"] = relationship("HistoricalEntity", back_populates="claims")
    source_bindings: Mapped[list["HistoricalClaimSource"]] = relationship(
        "HistoricalClaimSource", back_populates="claim", cascade="all, delete-orphan"
    )


class HistoricalClaimSource(Base):
    __tablename__ = "historical_claim_sources"
    __table_args__ = (
        Index("idx_historical_claim_sources_source", "source_id"),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_claims.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_sources.id", ondelete="CASCADE"), primary_key=True
    )
    support_type: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    locator_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_start: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_end: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    figure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    folio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inscription_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quotation_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quotation_language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editor_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    claim: Mapped["HistoricalClaim"] = relationship("HistoricalClaim", back_populates="source_bindings")
    source: Mapped["HistoricalSource"] = relationship("HistoricalSource")


class HistoricalEntityRelation(Base):
    __tablename__ = "historical_entity_relations"
    __table_args__ = (
        UniqueConstraint("subject_entity_id", "predicate", "object_entity_id"),
        Index("idx_historical_relations_subject", "subject_entity_id"),
        Index("idx_historical_relations_object", "object_entity_id"),
        Index("idx_historical_relations_predicate", "predicate"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="CASCADE"), nullable=False
    )
    predicate: Mapped[str] = mapped_column(Text, nullable=False)
    object_entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("historical_claims.id"), nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("historical_sources.id"), nullable=True)
    confidence: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HistoricalGeography(Base):
    __tablename__ = "historical_geographies"
    __table_args__ = (
        Index("idx_historical_geographies_mapping", "mapping_status"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="CASCADE"), primary_key=True
    )
    historical_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    modern_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_geometry: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    modern_geometry: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    geo_precision: Mapped[str] = mapped_column(Text, nullable=False)
    mapping_status: Mapped[str] = mapped_column(Text, nullable=False)
    source_claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("historical_claims.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    entity: Mapped["HistoricalEntity"] = relationship("HistoricalEntity", back_populates="geographies")


class HistoricalAsset(Base):
    __tablename__ = "historical_assets"
    __table_args__ = (
        Index("idx_historical_assets_entity", "entity_id"),
        Index("idx_historical_assets_type", "asset_type"),
        Index("idx_historical_assets_private", "is_private"),
        Index("idx_historical_assets_offline", "offline_licensing_allowed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type: Mapped[str] = mapped_column(Text, nullable=False)
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    byte_size: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rights_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_origin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_display_allowed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    derivative_allowed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    offline_licensing_allowed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default=text("true"))
    cache_control_policy: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, server_default=text("'public, max-age=31536000, immutable'")
    )
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="SET NULL"), nullable=True
    )
    media_cms_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("media_cms_items.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AssetCacheRevocation(Base):
    __tablename__ = "asset_cache_revocations"
    __table_args__ = (
        Index("idx_asset_revocations_asset", "asset_id"),
        Index("idx_asset_revocations_revoked_at", "revoked_at"),
        Index("idx_asset_revocations_cdn_purged", "cdn_purged"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    revocation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    revoked_by: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("'system'"))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cdn_purged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    purge_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class HistoricalContentAuditLog(Base):
    __tablename__ = "historical_content_audit_log"
    __table_args__ = (
        Index("idx_history_audit_resource", "resource_type", "resource_id"),
        Index("idx_history_audit_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    before_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HistoryStory(Base):
    """Block-based story engine table (Spec section 30).

    A story is an ordered list of typed blocks stored in ``blocks`` JSONB
    (30.1) — never one giant HTML field. Blocks reference entities/sources by
    UUID (30.2) so the frontend can deep-link into the atlas/urns/map/timeline
    surfaces.
    """

    __tablename__ = "history_stories"
    __table_args__ = (
        UniqueConstraint("slug"),
        Index("idx_history_stories_status", "status"),
        Index("idx_history_stories_featured", "featured"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title_vi: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hero_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocks: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    publication_status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def citations(self) -> list[dict]:
        return getattr(self, "_cached_citations", [])


class HistoryCollection(Base):
    """Teacher/editorial historical collection (Spec section 47).

    References canonical entity/source/story/question ids so a collection is a
    curated selection over the knowledge graph, not copied prose.
    """

    __tablename__ = "history_collections"
    __table_args__ = (
        UniqueConstraint("slug"),
        Index("idx_history_collections_owner", "owner_id"),
        Index("idx_history_collections_visibility", "visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title_vi: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    visibility: Mapped[str] = mapped_column(Text, nullable=False, default="private")
    entity_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    story_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    question_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class HistoryLessonAssignment(Base):
    """Teacher classroom lesson assignment with source-locked assessment basis (Spec V5-T033).

    Freezes the lesson content, rubric, and source set at assignment creation time.
    Future edits to the master lesson DO NOT alter this assignment's assessment basis.
    Enforces publication gate rejecting assignments with unverified/disputed claims.
    """

    __tablename__ = "history_lesson_assignments"
    __table_args__ = (
        Index("idx_hist_assignments_class", "classroom_id"),
        Index("idx_hist_assignments_lesson", "lesson_id"),
        Index("idx_hist_assignments_teacher", "assigned_by_id"),
        Index("idx_hist_assignments_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Pinned / source-locked fields
    pinned_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pinned_lesson_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    rubric: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pinned_source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    pinned_sources_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    pinned_claim_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    classroom: Mapped["Classroom"] = relationship(foreign_keys=[classroom_id])
    lesson: Mapped["LessonContent"] = relationship(foreign_keys=[lesson_id])
    assigned_by: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_by_id])
    submissions: Mapped[list["HistoryAssignmentSubmission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )

    def get_assessment_basis(self) -> dict[str, Any]:
        """Return the immutable assessment basis for this assignment."""
        return {
            "assignment_id": str(self.id),
            "classroom_id": str(self.classroom_id),
            "lesson_id": str(self.lesson_id),
            "pinned_version": self.pinned_version,
            "lesson_snapshot": dict(self.pinned_lesson_snapshot or {}),
            "rubric": dict(self.rubric or {}),
            "pinned_source_ids": [str(s) for s in (self.pinned_source_ids or [])],
            "pinned_sources": list(self.pinned_sources_snapshot or []),
            "pinned_claim_ids": [str(c) for c in (self.pinned_claim_ids or [])],
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class HistoryAssignmentSubmission(Base):
    """Student submission against a source-locked history lesson assignment (Spec V5-T033).

    Locks the assignment's assessment basis into `assessment_basis_snapshot` at submission time.
    """

    __tablename__ = "history_assignment_submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_hist_assignment_student"),
        Index("idx_hist_submissions_assignment", "assignment_id"),
        Index("idx_hist_submissions_student", "student_id"),
        Index("idx_hist_submissions_status", "status"),
        Index("idx_hist_submissions_idempotency", "idempotency_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("history_lesson_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="submitted"
    )  # "draft", "submitted", "graded", "returned"
    submission_content: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    assessment_basis_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rubric_evaluation: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    graded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    graded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assignment: Mapped["HistoryLessonAssignment"] = relationship(
        back_populates="submissions"
    )
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    graded_by: Mapped[Optional["User"]] = relationship(foreign_keys=[graded_by_id])


# --------------------------------------------------------------------------- #
# Learning Outcome Measurement Models (V5-T039 / Wave W03 / Slot A09)
# --------------------------------------------------------------------------- #
class HistoryEthicsProtocol(Base):
    """Ethics / IRB protocol registry for learning outcome research (Spec 63.2)."""

    __tablename__ = "history_ethics_protocols"
    __table_args__ = (
        UniqueConstraint("protocol_code"),
        Index("idx_history_ethics_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_code: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    irb_institution: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="submitted")
    approved_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    participant_consent_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HistoryLearningOutcomeAssessment(Base):
    """Source-based historical inquiry assessment task (pre/post/delayed)."""

    __tablename__ = "history_learning_outcome_assessments"
    __table_args__ = (
        UniqueConstraint("slug"),
        Index("idx_hist_lo_assess_phase", "assessment_phase"),
        Index("idx_hist_lo_assess_protocol", "ethics_protocol_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ethics_protocol_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_ethics_protocols.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_phase: Mapped[str] = mapped_column(Text, nullable=False, default="pre_test")
    instrument_type: Mapped[str] = mapped_column(Text, nullable=False, default="source_inquiry_rubric")
    target_urn_slug: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_motif_slug: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    claim_keys: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    rubric_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HistoryLearningOutcomeSubmission(Base):
    """Student submission to an objective source-based inquiry assessment."""

    __tablename__ = "history_learning_outcome_submissions"
    __table_args__ = (
        Index("idx_hist_lo_sub_student_phase", "student_id", "assessment_phase"),
        Index("idx_hist_lo_sub_assess", "assessment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_assessments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assessment_phase: Mapped[str] = mapped_column(Text, nullable=False, default="pre_test")
    instrument_type: Mapped[str] = mapped_column(Text, nullable=False, default="source_inquiry_rubric")
    responses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    citations_provided: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="submitted")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HistoryLearningOutcomeEvaluation(Base):
    """Independent assessor rubric evaluation for an inquiry submission."""

    __tablename__ = "history_learning_outcome_evaluations"
    __table_args__ = (
        UniqueConstraint("submission_id", "assessor_id"),
        Index("idx_hist_lo_eval_sub", "submission_id"),
        Index("idx_hist_lo_eval_assessor", "assessor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_submissions.id", ondelete="CASCADE"), nullable=False
    )
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_independent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rubric_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HistorySubjectiveSurvey(Base):
    """Subjective self-report surveys (e.g. Likert satisfaction/feelings).
    
    Strictly isolated: Cannot produce causal learning mastery metrics.
    """

    __tablename__ = "history_subjective_surveys"
    __table_args__ = (
        Index("idx_hist_subj_survey_student", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    survey_name: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_type: Mapped[str] = mapped_column(Text, nullable=False, default="self_report_survey")
    is_subjective_self_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    likert_responses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    perceived_learning_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    satisfaction_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HistoryCausalLearningMetric(Base):
    """Authoritative causal learning outcome metric derived from pre/post rubric scores."""

    __tablename__ = "history_causal_learning_metrics"
    __table_args__ = (
        Index("idx_hist_causal_metric_student", "student_id"),
        Index("idx_hist_causal_metric_protocol", "ethics_protocol_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ethics_protocol_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_ethics_protocols.id", ondelete="CASCADE"), nullable=False
    )
    pre_submission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_submissions.id"), nullable=False
    )
    post_submission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_submissions.id"), nullable=False
    )
    delayed_submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_submissions.id"), nullable=True
    )
    pre_score: Mapped[float] = mapped_column(Float, nullable=False)
    post_score: Mapped[float] = mapped_column(Float, nullable=False)
    delayed_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    normalized_gain: Mapped[float] = mapped_column(Float, nullable=False)
    absolute_gain: Mapped[float] = mapped_column(Float, nullable=False)
    inter_rater_agreement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competency_gains: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    instrument_type: Mapped[str] = mapped_column(Text, nullable=False, default="source_inquiry_rubric")
    is_valid_causal_claim: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


# --------------------------------------------------------------------------- #
# Teacher 45-Minute Lesson Wizard Models (V5-T091 / Wave W09 / Slot A01)
# --------------------------------------------------------------------------- #
class HistoryLessonPlan(Base):
    """Teacher 45-minute structured lesson wizard plan (Spec V5-T091 / W09-A01).

    Maintains 5-phase structured wizard flow:
    1. Objectives: Historical competencies (S1-S4), grade level, 45-min duration, qualities.
    2. Sources & Historical claims: Linked objects (Urn/Motif/Entity), sources, verified claims.
    3. Media: 2D Rubbing variant vs 3D Mesh variant, 2D fallback assets, preview links.
    4. Inquiry: 4 sequential activities (5m Warmup, 15m Exploration, 15m Deep Inquiry, 10m Exit ticket).
    5. Assessment: Rubric criteria (S1-S4 0-3 scale), exit ticket prompt & expected evidence.
    6. Precomputed/generated printable handout (student worksheet & teacher guide).

    Negative abuse invariant:
    Lesson CANNOT publish without approved historical object/source (rejects unreviewed,
    needs_source, or disputed claims).
    """

    __tablename__ = "history_lesson_plans"
    __table_args__ = (
        Index("idx_hist_lesson_plans_teacher", "teacher_id"),
        Index("idx_hist_lesson_plans_status", "status"),
        Index("idx_hist_lesson_plans_entity", "entity_id"),
        Index("idx_hist_lesson_plans_motif", "motif_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    target_grade: Mapped[str] = mapped_column(Text, nullable=False, default="Lớp 10 THPT")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    curriculum_framework: Mapped[str] = mapped_column(Text, nullable=False, default="CV 5512/BGDĐT")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    content_validation_status: Mapped[str] = mapped_column(Text, nullable=False, default="valid")

    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    urn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="SET NULL"),
        nullable=True,
    )
    motif_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="SET NULL"),
        nullable=True,
    )

    media_variant: Mapped[str] = mapped_column(Text, nullable=False, default="2d_rubbing")
    media_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    objectives: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    claim_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sources_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    claims_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    inquiry_activities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    assessment_rubric: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    printable_handout: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )



# --------------------------------------------------------------------------- #
# School Pilot Measurement & Ethics Models (V5-T100 / Wave W09 / Slot A10)
# --------------------------------------------------------------------------- #
class HistoryPilotGuardianConsent(Base):
    """Informed guardian consent verification for school pilot research (Spec 63.2 / V5-T100)."""

    __tablename__ = "history_pilot_guardian_consents"
    __table_args__ = (
        UniqueConstraint("ethics_protocol_id", "student_id", name="uq_pilot_consent_protocol_student"),
        Index("idx_pilot_consent_protocol", "ethics_protocol_id"),
        Index("idx_pilot_consent_student", "student_id"),
        Index("idx_pilot_consent_status", "consent_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ethics_protocol_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_ethics_protocols.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    guardian_name: Mapped[str] = mapped_column(Text, nullable=False)
    guardian_email: Mapped[str] = mapped_column(Text, nullable=False)
    guardian_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False, default="parent")
    consent_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")  # pending, verified, withdrawn
    verification_method: Mapped[str] = mapped_column(Text, nullable=False, default="school_roster")  # sms_otp, digital_signature, paper_signed, school_roster
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    protocol: Mapped["HistoryEthicsProtocol"] = relationship(foreign_keys=[ethics_protocol_id])
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    verified_by: Mapped[Optional["User"]] = relationship(foreign_keys=[verified_by_id])


class HistoryTeacherWorkloadLog(Base):
    """Teacher workload tracking and burnout prevention during school pilots (V5-T100)."""

    __tablename__ = "history_teacher_workload_logs"
    __table_args__ = (
        Index("idx_hist_tw_teacher", "teacher_id"),
        Index("idx_hist_tw_protocol", "ethics_protocol_id"),
        Index("idx_hist_tw_activity", "activity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True
    )
    ethics_protocol_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_ethics_protocols.id", ondelete="SET NULL"), nullable=True
    )
    activity_type: Mapped[str] = mapped_column(Text, nullable=False, default="rubric_grading")
    minutes_spent: Mapped[float] = mapped_column(Float, nullable=False)
    submissions_evaluated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cognitive_load_rating: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)  # NASA-TLX 0-100
    workload_category: Mapped[str] = mapped_column(Text, nullable=False, default="acceptable")  # optimal, acceptable, excessive
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])


# --------------------------------------------------------------------------- #
# Multilingual Learning Supports & Pedagogical Glossary (V5-T098 / W09-A08)
# --------------------------------------------------------------------------- #
from .domain.multilingual_glossary import (  # noqa: E402
    CANONICAL_PEDAGOGICAL_GLOSSARY,
    DISQUALIFIED_TRANSLATION_MARKERS,
    GlossaryCategory,
    GlossaryReviewStatus,
    GlossaryValidationError,
    MismatchedTranslationError,
    TranslationOrigin,
    UNREVIEWED_GLOSSARY_STATUSES,
    UnreviewedTranslationPromotionError,
    VERIFIED_GLOSSARY_STATUSES,
    build_translation_provenance,
    detect_translation_mismatch,
    is_placeholder_text,
    validate_glossary_term_invariants,
)


class HistoricalGlossaryTerm(Base):
    """Bilingual Vietnamese/English pedagogical glossary with epigraphic readings & provenance (V5-T098)."""

    __tablename__ = "historical_glossary_terms"
    __table_args__ = (
        Index("idx_hist_glossary_category", "category"),
        Index("idx_hist_glossary_review_status", "review_status"),
        Index("idx_hist_glossary_source_id", "source_id"),
        Index("idx_hist_glossary_origin", "origin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    term_vi: Mapped[str] = mapped_column(Text, nullable=False)
    term_en: Mapped[str] = mapped_column(Text, nullable=False)
    term_han_nom: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reading_quoc_ngu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    definition_vi: Mapped[str] = mapped_column(Text, nullable=False)
    definition_en: Mapped[str] = mapped_column(Text, nullable=False)
    contextual_usage_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contextual_usage_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_sources.id", ondelete="SET NULL"), nullable=True
    )
    citation_locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bilingual_citation: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, default="provisional")
    origin: Mapped[str] = mapped_column(String(64), nullable=False, default="ai_generated")
    is_machine_translated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uncertainty_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    epigrapher_signoff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translation_provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    related_entity_slugs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[Optional["HistoricalSource"]] = relationship(foreign_keys=[source_id])


class HistoryRubricCalibration(Base):
    """Dual-assessor rubric calibration and inter-rater agreement audit (V5-T100)."""

    __tablename__ = "history_rubric_calibrations"
    __table_args__ = (
        Index("idx_hist_rc_submission", "submission_id"),
        Index("idx_hist_rc_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_submissions.id", ondelete="CASCADE"), nullable=False
    )
    assessor_a_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assessor_b_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    evaluation_a_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_evaluations.id", ondelete="SET NULL"), nullable=True
    )
    evaluation_b_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("history_learning_outcome_evaluations.id", ondelete="SET NULL"), nullable=True
    )
    score_a: Mapped[float] = mapped_column(Float, nullable=False)
    score_b: Mapped[float] = mapped_column(Float, nullable=False)
    score_difference: Mapped[float] = mapped_column(Float, nullable=False)
    divergence_pct: Mapped[float] = mapped_column(Float, nullable=False)
    inter_rater_agreement: Mapped[float] = mapped_column(Float, nullable=False)
    tolerance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.15)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="calibrated")  # calibrated, divergent_requires_review
    consensus_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    criteria_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    submission: Mapped["HistoryLearningOutcomeSubmission"] = relationship(foreign_keys=[submission_id])
    assessor_a: Mapped["User"] = relationship(foreign_keys=[assessor_a_id])
    assessor_b: Mapped["User"] = relationship(foreign_keys=[assessor_b_id])


# --------------------------------------------------------------------------- #
# Curriculum Competency Catalog Models (V5-T095 / Wave W09 / Slot A05)
# Vietnam 2018 General Education Program (GDPT 2018)
# --------------------------------------------------------------------------- #
class StandardCompetencyDomain(str, Enum):
    historical_literacy = "historical_literacy"
    source_criticism = "source_criticism"
    historical_empathy = "historical_empathy"
    historical_communication = "historical_communication"


class CompetencyGradeBand(str, Enum):
    grade_6_7 = "GRADE_6_7"
    grade_8_9 = "GRADE_8_9"
    grade_10_12 = "GRADE_10_12"
    all_grades = "ALL"


class CompetencyMappingStatus(str, Enum):
    unreviewed = "unreviewed"
    verified = "verified"
    flagged = "flagged"
    deprecated = "deprecated"


class CompetencyFlagReason(str, Enum):
    inaccurate_grade_level = "inaccurate_grade_level"
    misaligned_competency = "misaligned_competency"
    historical_inaccuracy = "historical_inaccuracy"
    pedagogical_concern = "pedagogical_concern"
    other = "other"


class CurriculumCompetency(Base):
    """Standard historical competency descriptor under Vietnam 2018 General Education Program."""

    __tablename__ = "curriculum_competencies"
    __table_args__ = (
        UniqueConstraint("code", name="uq_curriculum_competencies_code"),
        Index("idx_curriculum_competency_domain", "domain"),
        Index("idx_curriculum_competency_framework", "standard_framework"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    standard_framework: Mapped[str] = mapped_column(Text, nullable=False, default="VN_GDPT_2018")
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    description_vi: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    grade_band_descriptors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    relic_mappings: Mapped[list["CurriculumCompetencyRelicMapping"]] = relationship(
        back_populates="competency", cascade="all, delete-orphan"
    )


class CurriculumCompetencyRelicMapping(Base):
    """Mapping between standard historical competencies, grade bands (Grades 6-12), and real relics."""

    __tablename__ = "curriculum_competency_relic_mappings"
    __table_args__ = (
        Index("idx_comp_mapping_competency", "competency_id"),
        Index("idx_comp_mapping_relic_urn", "relic_urn_slug"),
        Index("idx_comp_mapping_relic_motif", "relic_motif_id"),
        Index("idx_comp_mapping_status", "status"),
        Index("idx_comp_mapping_grade_band", "grade_band"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("curriculum_competencies.id", ondelete="CASCADE"), nullable=False
    )
    relic_urn_slug: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relic_motif_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_slug: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    grade_band: Mapped[str] = mapped_column(Text, nullable=False, default="GRADE_10_12")
    min_grade: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    max_grade: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    learning_activity_vi: Mapped[str] = mapped_column(Text, nullable=False)
    learning_activity_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_requirement_vi: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_requirement_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="unreviewed")
    is_reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_warning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán",
    )
    flag_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    competency: Mapped["CurriculumCompetency"] = relationship(back_populates="relic_mappings")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    updated_by: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_id])
    flags: Mapped[list["CurriculumCompetencyFlag"]] = relationship(
        back_populates="mapping", cascade="all, delete-orphan"
    )


class CurriculumCompetencyFlag(Base):
    """Teacher feedback and inaccuracy flagging on curriculum competency mappings."""

    __tablename__ = "curriculum_competency_flags"
    __table_args__ = (
        Index("idx_comp_flag_mapping", "mapping_id"),
        Index("idx_comp_flag_teacher", "flagged_by_id"),
        Index("idx_comp_flag_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mapping_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("curriculum_competency_relic_mappings.id", ondelete="CASCADE"), nullable=False
    )
    flagged_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    commentary: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_correction: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")  # pending, reviewed, resolved, dismissed
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    mapping: Mapped["CurriculumCompetencyRelicMapping"] = relationship(back_populates="flags")
    flagged_by: Mapped["User"] = relationship(foreign_keys=[flagged_by_id])
    resolved_by: Mapped[Optional["User"]] = relationship(foreign_keys=[resolved_by_id])


# --------------------------------------------------------------------------- #
# Canonical Urn & Motif Domain Mapping (Cửu Đỉnh 9x18 = 162)
# --------------------------------------------------------------------------- #
from .domain.canonical_urn_mapping import (  # noqa: E402
    AmbiguousAliasError,
    CANONICAL_RELIEFS,
    CANONICAL_RELIEF_SLUGS,
    CANONICAL_URNS,
    CANONICAL_URN_SLUGS,
    CanonicalReliefInfo,
    CanonicalUrnInfo,
    CrossUrnMisassignmentError,
    InvalidMotifCountError,
    MOTIFS_PER_URN,
    STABLE_MOTIF_IDS,
    TOTAL_MOTIFS,
    TOTAL_URNS,
    URN_ALIAS_INDEX,
    URN_ORDER,
    extract_urn_slug,
    resolve_canonical_motif_id,
    resolve_canonical_relief_slug,
    resolve_canonical_urn_slug,
    resolve_legacy_identifier,
    validate_dataset_uniqueness,
    validate_no_cross_urn_misassignment,
    validate_urn_motif_count,
)

# --------------------------------------------------------------------------- #
# Hán–Nôm Script, Reading, & Translation Review Domain (V5-T026)
# --------------------------------------------------------------------------- #
from .domain.han_nom_review import (  # noqa: E402
    KNOWN_MISSING_HAN_NOM_MOTIF_IDS,
    UNREVIEWED_REVIEW_STATUSES,
    VERIFIED_REVIEW_STATUSES,
    HanNomMotifReviewRecord,
    HanNomProvenanceOrigin,
    HanNomReviewError,
    HanNomReviewInput,
    HanNomReviewStatus,
    HanNomTranslationReview,
    UnverifiedPromotionForbiddenError,
    audit_162_han_nom_dataset,
    is_valid_source_citation,
    validate_han_nom_promotion,
)

# --------------------------------------------------------------------------- #
# Image & 3D Mesh Attribution Linkage with Rights Enforcement (V5-T027 / W02-A07)
# --------------------------------------------------------------------------- #
from .services.asset_rights import (  # noqa: E402
    APPROVED_LICENSES,
    APPROVED_RIGHTS_STATUSES,
    DEFAULT_CREATOR,
    DEFAULT_LEGAL_BASIS,
    DEFAULT_LICENSE,
    DEFAULT_RIGHTS_OWNER,
    EXPECTED_CAO_DINH_CHECKSUMS,
    GLB_MAGIC,
    JPEG_MAGIC,
    PNG_MAGIC,
    RESTRICTED_RIGHTS_STATUSES,
    URN_FALLBACK_2D_REGISTRY,
    URN_SLUGS,
    AssetDistributionBlockedError,
    AssetIntegrityError,
    AssetRightsError,
    AssetRightsMissingLicenseError,
    AssetRightsRevokedError,
    audit_all_relic_assets,
    audit_all_urn_manifests,
    can_distribute_on_cdn,
    enforce_cdn_distribution_policy,
    get_motif_fallback,
    get_motif_registry_162,
    get_viewer_fallback,
    resolve_asset_fallback,
    revoke_manifest_rights,
    sha256_of_file,
    sync_manifest_to_historical_asset,
    validate_historical_asset_distribution,
    validate_manifest_attribution,
    validate_manifest_checksum_integrity,
)

# --------------------------------------------------------------------------- #
# Peer / Group Historical Inquiry Models (V5-T038 / W03-A08)
# --------------------------------------------------------------------------- #
from .history_inquiry_models import (  # noqa: E402
    HistoricalInquiryActivity,
    HistoricalInquiryGroup,
    HistoricalInquiryGroupMember,
    HistoricalInquirySubmission,
    InquiryMemberRole,
    InquiryPrivacyMode,
    InquirySubmissionStatus,
)

# --------------------------------------------------------------------------- #
# Learning Outcome Measurement Domain (V5-T039 / Wave W03 / Slot A09)
# --------------------------------------------------------------------------- #
from .domain.learning_outcome import (  # noqa: E402
    DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
    AssessmentInstrumentType,
    AssessmentPhase,
    EthicsProtocolRequiredError,
    EthicsProtocolStatus,
    IndependentAssessorRequiredError,
    InvalidRubricScoreError,
    LearningOutcomeError,
    SubjectiveSurveyCannotProduceCausalMetricsError,
    UnpairedAssessmentError,
    calculate_effect_size_cohens_d,
    calculate_inter_rater_reliability,
    calculate_normalized_learning_gain,
    validate_assessor_independence,
    validate_ethics_protocol_active,
    validate_rubric_scores,
    verify_causal_learning_eligibility,
)

# --------------------------------------------------------------------------- #
# 3D Asset Manifest Validation Domain (V5-T041 / Wave W04 / Slot A01)
# --------------------------------------------------------------------------- #
from .services.manifest_validation import (  # noqa: E402
    ManifestChecksumError,
    ManifestLicenseError,
    ManifestMeshJoinError,
    ManifestMissingFallbackError,
    ManifestPhantomModelError,
    ManifestSizeError,
    ManifestValidationError,
    ManifestVersionError,
    WebGLHealthError,
    audit_all_3d_manifests,
    load_manifest,
    validate_2d_fallback_for_missing_meshes,
    validate_3d_asset_checksum_and_size,
    validate_3d_asset_license,
    validate_3d_asset_version,
    validate_3d_mesh_id_joins,
    validate_webgl_health_contract,
)

# --------------------------------------------------------------------------- #
# Mobile Route Audit & Replacement Domain (V5-T051 / Wave W05 / Slot A01)
# --------------------------------------------------------------------------- #
from .services.mobile_route_audit import (  # noqa: E402
    ForbiddenDummyTextError,
    PlaceholderRouteError,
    RouteAuditError,
    UnbackedRouteError,
    audit_mobile_routes,
    get_all_declared_route_paths,
    parse_app_router_routes,
    scan_for_forbidden_dummy_tokens,
    validate_no_placeholder_leakage,
    validate_route_auth_redirects,
    verify_screen_data_contracts,
)

# --------------------------------------------------------------------------- #
# P04–P06 Source/Claim Cross-Check & Corroboration Domain (V5-T076 / W07-A06)
# --------------------------------------------------------------------------- #
from .services.research_factory.citations import (  # noqa: E402
    CitationValidationResult,
    InvalidLocatorFormatError,
    MismatchedPageCitationError,
    ResearchFactoryCitationError,
    UncorroboratedClaimCitationError,
    validate_citation_locator,
    verify_claim_corroboration_policy,
)
from .services.research_factory.corroboration import (  # noqa: E402
    CANONICAL_WORKS,
    AnachronisticGeographyError,
    CanonicalWork,
    ContradictionRecord,
    ContradictionStatus,
    DisputeCategory,
    DisputedClaimCannotAutoVerifyError,
    MirrorDetectionResult,
    NormalizedEdition,
    OverpreciseChronologyError,
    ScholarlyDispute,
    ScholarlyDisputeLedger,
    detect_duplicate_or_mirror_sources,
    dispute_ledger,
    normalize_edition,
    resolve_date_chronology,
    resolve_place_geography,
)
from .services.research_factory.cross_check import (  # noqa: E402
    CrossCheckReport,
    bind_claim_source_verified,
    cross_check_entity_claims,
)



