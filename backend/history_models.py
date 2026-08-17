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
)
from sqlalchemy.dialects.postgresql import BIGINT, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import Base


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


class HistoricalConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"
    disputed = "disputed"


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
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("historical_entities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


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
