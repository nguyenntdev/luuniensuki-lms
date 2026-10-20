# -*- coding: utf-8 -*-
"""Imperial domain models — STTTNNĐ (Lưu Niên — Đại Nội Huế).

Architectural domain entities for Đại Nội Huế (Imperial City of Hue):
- Zones, Sites, Historical Media
- Aerial Map Assets, Annotations (with normalized UV coordinates), Annotation Links, Audit
- Learning Lenses & Site bindings
- Learning Paths & Path Steps
- Pedagogical Activities & Student Submissions

Enforces:
1. Strict content_scope = 'STTT_IMPERIAL_CITY' on all tables via CHECK constraints.
2. Normalized UV coordinate bounds (0.0 <= u <= 1.0, 0.0 <= v <= 1.0) on map annotations.
3. Optimistic concurrency control via `row_version`.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


# --------------------------------------------------------------------------- #
# Controlled Vocabularies / Enums
# --------------------------------------------------------------------------- #
class ImperialReviewStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    published = "published"
    archived = "archived"


class ImperialLicenseStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ImperialShapeType(str, Enum):
    point = "point"
    polygon = "polygon"
    bbox = "bbox"


class ImperialPositionConfidence(str, Enum):
    verified = "verified"
    approximate = "approximate"
    uncertain = "uncertain"


class ImperialLinkTargetType(str, Enum):
    story = "story"
    lesson = "lesson"
    source = "source"
    quiz = "quiz"
    activity = "activity"
    trail = "trail"


class ImperialSubmissionStatus(str, Enum):
    submitted = "submitted"
    graded = "graded"
    resubmit_requested = "resubmit_requested"


class ImperialSiteCondition(str, Enum):
    extant = "extant"
    reconstructed = "reconstructed"
    ruined = "ruined"
    lost = "lost"


class ImperialLearningLevel(str, Enum):
    L1_DOCUMENTED = "L1_DOCUMENTED"
    L2_VERIFIED = "L2_VERIFIED"
    L3_EXTENDED = "L3_EXTENDED"


class ImperialMediaKind(str, Enum):
    photo = "photo"
    drawing = "drawing"
    historical_photo = "historical_photo"
    schematic = "schematic"
    audio = "audio"
    video = "video"


CONTENT_SCOPE_IMPERIAL = "STTT_IMPERIAL_CITY"


# --------------------------------------------------------------------------- #
# 1. ImperialZone
# --------------------------------------------------------------------------- #
class ImperialZone(Base):
    """Zonal grouping of monuments within the Imperial City of Hue."""

    __tablename__ = "imperial_zones"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_zones_scope"),
        UniqueConstraint("slug", name="uq_imperial_zones_slug"),
        Index("idx_imperial_zones_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    sites: Mapped[list["ImperialSite"]] = relationship(
        "ImperialSite", back_populates="zone", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 2. ImperialSite
# --------------------------------------------------------------------------- #
class ImperialSite(Base):
    """Architectural site / monument in the Imperial City."""

    __tablename__ = "imperial_sites"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_sites_scope"),
        UniqueConstraint("slug", name="uq_imperial_sites_slug"),
        Index("idx_imperial_sites_zone", "zone_id"),
        Index("idx_imperial_sites_published", "is_published"),
        Index("idx_imperial_sites_level", "learning_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_zones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_han_nom: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    alternative_names: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    site_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'palace'")
    )
    condition: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'extant'")
    )
    learning_level: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'L1_DOCUMENTED'")
    )
    summary_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    architectural_features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    construction_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    zone: Mapped["ImperialZone"] = relationship("ImperialZone", back_populates="sites")
    annotations: Mapped[list["ImperialMapAnnotation"]] = relationship(
        "ImperialMapAnnotation", back_populates="site"
    )
    media: Mapped[list["ImperialMedia"]] = relationship(
        "ImperialMedia", back_populates="site", cascade="all, delete-orphan"
    )
    lens_associations: Mapped[list["ImperialLensSite"]] = relationship(
        "ImperialLensSite", back_populates="site", cascade="all, delete-orphan"
    )
    path_steps: Mapped[list["ImperialPathStep"]] = relationship(
        "ImperialPathStep", back_populates="site"
    )
    activities: Mapped[list["ImperialActivity"]] = relationship(
        "ImperialActivity", back_populates="site"
    )


# --------------------------------------------------------------------------- #
# 3. ImperialMapAsset
# --------------------------------------------------------------------------- #
class ImperialMapAsset(Base):
    """High-resolution aerial photographic or reconstructed map asset."""

    __tablename__ = "imperial_map_assets"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_map_assets_scope"),
        CheckConstraint("version > 0", name="ck_imperial_map_assets_version"),
        CheckConstraint(
            "mime_type IN ('image/jpeg','image/png','image/webp')",
            name="ck_imperial_map_assets_mime",
        ),
        CheckConstraint("width_px BETWEEN 1 AND 100000", name="ck_imperial_map_assets_width"),
        CheckConstraint("height_px BETWEEN 1 AND 100000", name="ck_imperial_map_assets_height"),
        CheckConstraint(
            "license_status IN ('pending','approved','rejected')",
            name="ck_imperial_map_assets_license_status",
        ),
        CheckConstraint(
            "review_status IN ('draft','in_review','approved','published','archived')",
            name="ck_imperial_map_assets_review_status",
        ),
        UniqueConstraint("content_scope", "slug", "version", name="uq_imperial_map_assets_scope_slug_version"),
        Index(
            "idx_imperial_active_map",
            "content_scope",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
        Index("idx_imperial_map_assets_review", "review_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    title_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    image_storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_locator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    copyright_holder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credit_text: Mapped[str] = mapped_column(Text, nullable=False)
    license_kind: Mapped[str] = mapped_column(String(100), nullable=False)
    license_evidence_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    license_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'draft'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    annotations: Mapped[list["ImperialMapAnnotation"]] = relationship(
        "ImperialMapAnnotation", back_populates="map_asset", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 4. ImperialMapAnnotation
# --------------------------------------------------------------------------- #
class ImperialMapAnnotation(Base):
    """Normalized UV marker or polygon annotation placed on an aerial map asset."""

    __tablename__ = "imperial_map_annotations"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_map_annotations_scope"),
        CheckConstraint(
            "shape_type IN ('point','polygon','bbox')",
            name="ck_imperial_map_annotations_shape",
        ),
        CheckConstraint("u >= 0.0 AND u <= 1.0", name="ck_imperial_map_annotations_u_range"),
        CheckConstraint("v >= 0.0 AND v <= 1.0", name="ck_imperial_map_annotations_v_range"),
        CheckConstraint(
            "review_status IN ('draft','in_review','approved','published','archived')",
            name="ck_imperial_map_annotations_review_status",
        ),
        CheckConstraint(
            "position_confidence IN ('verified','approximate','uncertain')",
            name="ck_imperial_map_annotations_confidence",
        ),
        UniqueConstraint("map_asset_id", "site_id", name="uq_imperial_map_annotations_asset_site"),
        Index("idx_imperial_map_annotations_asset", "map_asset_id", "review_status"),
        Index("idx_imperial_map_annotations_site", "site_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    map_asset_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_map_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_sites.id", ondelete="RESTRICT"),
        nullable=False,
    )
    shape_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'point'")
    )
    u: Mapped[float] = mapped_column(Numeric(9, 7), nullable=False)
    v: Mapped[float] = mapped_column(Numeric(9, 7), nullable=False)
    polygon_uv: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marker_style: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'monument'")
    )
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'draft'")
    )
    position_confidence: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'approximate'")
    )
    position_source_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editorial_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    map_asset: Mapped["ImperialMapAsset"] = relationship(
        "ImperialMapAsset", back_populates="annotations"
    )
    site: Mapped["ImperialSite"] = relationship("ImperialSite", back_populates="annotations")
    links: Mapped[list["ImperialAnnotationLink"]] = relationship(
        "ImperialAnnotationLink", back_populates="annotation", cascade="all, delete-orphan"
    )
    audits: Mapped[list["ImperialAnnotationAudit"]] = relationship(
        "ImperialAnnotationAudit", back_populates="annotation", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 5. ImperialAnnotationLink
# --------------------------------------------------------------------------- #
class ImperialAnnotationLink(Base):
    """Link from an annotation to pedagogical target (story, lesson, quiz, trail, etc.)."""

    __tablename__ = "imperial_annotation_links"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_annotation_links_scope"),
        CheckConstraint(
            "target_type IN ('story','lesson','source','quiz','activity','trail')",
            name="ck_imperial_annotation_links_target_type",
        ),
        UniqueConstraint("annotation_id", "target_type", "target_id", name="uq_imperial_annotation_links_target"),
        Index("idx_imperial_annotation_links_target", "target_type", "target_id"),
        Index("idx_imperial_annotation_links_annotation", "annotation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_map_annotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    # Relationships
    annotation: Mapped["ImperialMapAnnotation"] = relationship(
        "ImperialMapAnnotation", back_populates="links"
    )


# --------------------------------------------------------------------------- #
# 6. ImperialAnnotationAudit
# --------------------------------------------------------------------------- #
class ImperialAnnotationAudit(Base):
    """Append-only audit trail for map annotation curation and editorial changes."""

    __tablename__ = "imperial_annotation_audit"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_annotation_audit_scope"),
        Index("idx_imperial_annotation_audit_annotation", "annotation_id"),
        Index("idx_imperial_annotation_audit_created", "created_at"),
        Index("idx_imperial_annotation_audit_actor", "actor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_map_annotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    before_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    annotation: Mapped["ImperialMapAnnotation"] = relationship(
        "ImperialMapAnnotation", back_populates="audits"
    )


# --------------------------------------------------------------------------- #
# 7. ImperialLens
# --------------------------------------------------------------------------- #
class ImperialLens(Base):
    """Thematic pedagogical lens for filtering and contextualizing sites."""

    __tablename__ = "imperial_lenses"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_lenses_scope"),
        UniqueConstraint("code", name="uq_imperial_lenses_code"),
        Index("idx_imperial_lenses_active", "is_active"),
        Index("idx_imperial_lenses_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    lens_sites: Mapped[list["ImperialLensSite"]] = relationship(
        "ImperialLensSite", back_populates="lens", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 8. ImperialLensSite
# --------------------------------------------------------------------------- #
class ImperialLensSite(Base):
    """Association linking an ImperialLens with a monument site."""

    __tablename__ = "imperial_lens_sites"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_lens_sites_scope"),
        UniqueConstraint("lens_id", "site_id", name="uq_imperial_lens_sites_lens_site"),
        Index("idx_imperial_lens_sites_lens", "lens_id"),
        Index("idx_imperial_lens_sites_site", "site_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    lens_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_lenses.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("1.0"))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    curatorial_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lens: Mapped["ImperialLens"] = relationship("ImperialLens", back_populates="lens_sites")
    site: Mapped["ImperialSite"] = relationship("ImperialSite", back_populates="lens_associations")


# --------------------------------------------------------------------------- #
# 9. ImperialLearningPath
# --------------------------------------------------------------------------- #
class ImperialLearningPath(Base):
    """Curated thematic trail / learning path through Imperial City sites."""

    __tablename__ = "imperial_learning_paths"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_learning_paths_scope"),
        CheckConstraint(
            "review_status IN ('draft','published','archived')",
            name="ck_imperial_learning_paths_review",
        ),
        UniqueConstraint("slug", name="uq_imperial_learning_paths_slug"),
        Index("idx_imperial_learning_paths_published", "is_published"),
        Index("idx_imperial_learning_paths_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'standard'")
    )
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("45"))
    age_group: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'all'")
    )
    learning_objectives: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'draft'")
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    steps: Mapped[list["ImperialPathStep"]] = relationship(
        "ImperialPathStep",
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="ImperialPathStep.step_order",
    )
    activities: Mapped[list["ImperialActivity"]] = relationship(
        "ImperialActivity", back_populates="path"
    )


# --------------------------------------------------------------------------- #
# 10. ImperialPathStep
# --------------------------------------------------------------------------- #
class ImperialPathStep(Base):
    """Step in an Imperial City learning path."""

    __tablename__ = "imperial_path_steps"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_path_steps_scope"),
        UniqueConstraint("path_id", "step_order", name="uq_imperial_path_steps_order"),
        Index("idx_imperial_path_steps_path", "path_id"),
        Index("idx_imperial_path_steps_site", "site_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    path_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_learning_paths.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_sites.id", ondelete="RESTRICT"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    source_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rubrics: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))

    # Relationships
    path: Mapped["ImperialLearningPath"] = relationship(
        "ImperialLearningPath", back_populates="steps"
    )
    site: Mapped["ImperialSite"] = relationship("ImperialSite", back_populates="path_steps")


# --------------------------------------------------------------------------- #
# 11. ImperialActivity
# --------------------------------------------------------------------------- #
class ImperialActivity(Base):
    """Pedagogical inquiry activity or assignment tied to site or learning path."""

    __tablename__ = "imperial_activities"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_activities_scope"),
        Index("idx_imperial_activities_site", "site_id"),
        Index("idx_imperial_activities_path", "path_id"),
        Index("idx_imperial_activities_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_sites.id", ondelete="SET NULL"),
        nullable=True,
    )
    path_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_learning_paths.id", ondelete="SET NULL"),
        nullable=True,
    )
    activity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'evidence_reflection'")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    rubric_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("100"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    site: Mapped[Optional["ImperialSite"]] = relationship(
        "ImperialSite", back_populates="activities"
    )
    path: Mapped[Optional["ImperialLearningPath"]] = relationship(
        "ImperialLearningPath", back_populates="activities"
    )
    submissions: Mapped[list["ImperialSubmission"]] = relationship(
        "ImperialSubmission", back_populates="activity", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 12. ImperialSubmission
# --------------------------------------------------------------------------- #
class ImperialSubmission(Base):
    """Student submission for an Imperial City learning activity."""

    __tablename__ = "imperial_submissions"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_submissions_scope"),
        CheckConstraint(
            "status IN ('submitted','graded','resubmit_requested')",
            name="ck_imperial_submissions_status",
        ),
        Index("idx_imperial_submissions_student", "student_id"),
        Index("idx_imperial_submissions_activity", "activity_id"),
        Index("idx_imperial_submissions_classroom", "classroom_id"),
        Index("idx_imperial_submissions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'submitted'")
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rubric_scores: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    activity: Mapped["ImperialActivity"] = relationship(
        "ImperialActivity", back_populates="submissions"
    )


# --------------------------------------------------------------------------- #
# 13. ImperialMedia
# --------------------------------------------------------------------------- #
class ImperialMedia(Base):
    """Verified historical media, photographs, and drawings tied to monuments."""

    __tablename__ = "imperial_media"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_media_scope"),
        Index("idx_imperial_media_site", "site_id"),
        Index("idx_imperial_media_published", "is_published"),
        Index("idx_imperial_media_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    media_kind: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'photo'")
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credit: Mapped[str] = mapped_column(Text, nullable=False)
    historical_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    site: Mapped["ImperialSite"] = relationship("ImperialSite", back_populates="media")
