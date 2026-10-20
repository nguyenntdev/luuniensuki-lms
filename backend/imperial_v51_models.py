# -*- coding: utf-8 -*-
"""Imperial domain models V5.1 extensions — STTTNNĐ (Lưu Niên — Đại Nội Huế).

Architectural domain entities for V5.1 modules:
- Learning Media & Media Hotspots (image, panorama360, model3d, UV coordinates)
- Art Details, Claim Sources, and Art Detail Questions
- Heritage Detective Clues & Clue Attempts
- Interactive Questions & Game Submissions
- Teacher Assignment Releases

Enforces:
1. Strict content_scope = 'STTT_IMPERIAL_CITY' on all tables via CHECK constraints.
2. Normalized UV coordinate bounds (0.0 <= u <= 1.0, 0.0 <= v <= 1.0) on media hotspots.
3. Optimistic concurrency control via `row_version` where applicable.
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
from .imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialReviewStatus,
    ImperialSite,
)


# --------------------------------------------------------------------------- #
# Controlled Vocabularies / Enums for V5.1
# --------------------------------------------------------------------------- #
class ImperialLearningMediaKind(str, Enum):
    image = "image"
    panorama360 = "panorama360"
    model3d = "model3d"


class ImperialMediaAssetContext(str, Enum):
    extant = "extant"
    historical_photo = "historical_photo"
    restoration_drawing = "restoration_drawing"


class ImperialPointKind(str, Enum):
    point = "point"
    rect = "rect"
    polygon = "polygon"


class ImperialArtDetailKind(str, Enum):
    carving = "carving"
    pattern = "pattern"
    painting = "painting"
    mosaic = "mosaic"
    relief = "relief"


class ImperialStoryType(str, Enum):
    documented_event = "documented_event"
    legend = "legend"
    oral_account = "oral_account"
    interpretation = "interpretation"


class ImperialEvidenceStrength(str, Enum):
    verified = "verified"
    probable = "probable"
    traditional = "traditional"


class ImperialClueTargetType(str, Enum):
    site = "site"
    art_detail = "art_detail"


class ImperialQuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    matching = "matching"
    hotspot_identify = "hotspot_identify"


# --------------------------------------------------------------------------- #
# 1. ImperialLearningMedia
# --------------------------------------------------------------------------- #
class ImperialLearningMedia(Base):
    """Learning media assets (photos, 360 panoramas, 3D models) for architectural sites."""

    __tablename__ = "imperial_learning_media"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_learning_media_scope"),
        CheckConstraint("kind IN ('image', 'panorama360', 'model3d')", name="ck_imperial_learning_media_kind"),
        CheckConstraint(
            "license_status IN ('pending', 'approved', 'rejected')",
            name="ck_imperial_learning_media_license",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
            name="ck_imperial_learning_media_review",
        ),
        CheckConstraint(
            "asset_context IN ('extant', 'historical_photo', 'restoration_drawing')",
            name="ck_imperial_learning_media_context",
        ),
        Index("idx_imperial_learning_media_site", "site_id"),
        Index("idx_imperial_learning_media_review", "review_status"),
        Index("idx_imperial_learning_media_kind", "kind"),
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
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'image'")
    )
    media_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    asset_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    width_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_px: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    license_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'pending'")
    )
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    alt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credit_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_context: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'extant'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    site: Mapped["ImperialSite"] = relationship("ImperialSite")
    hotspots: Mapped[list["ImperialMediaHotspot"]] = relationship(
        "ImperialMediaHotspot", back_populates="media", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 2. ImperialArtDetail
# --------------------------------------------------------------------------- #
class ImperialArtDetail(Base):
    """Art detail, carving, pattern, mosaic or decorative element on a monument."""

    __tablename__ = "imperial_art_details"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_art_details_scope"),
        CheckConstraint(
            "kind IN ('carving', 'pattern', 'painting', 'mosaic', 'relief')",
            name="ck_imperial_art_details_kind",
        ),
        CheckConstraint(
            "story_type IN ('documented_event', 'legend', 'oral_account', 'interpretation')",
            name="ck_imperial_art_details_story_type",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
            name="ck_imperial_art_details_review",
        ),
        UniqueConstraint("slug", name="uq_imperial_art_details_slug"),
        Index("idx_imperial_art_details_site", "site_id"),
        Index("idx_imperial_art_details_slug", "slug"),
        Index("idx_imperial_art_details_kind", "kind"),
        Index("idx_imperial_art_details_review", "review_status"),
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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'carving'")
    )
    motif: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technique: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description_observation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'documented_event'")
    )
    meaning_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_value_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cultural_value_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    art_value_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    content_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    site: Mapped["ImperialSite"] = relationship("ImperialSite")
    claim_sources: Mapped[list["ImperialArtDetailClaimSource"]] = relationship(
        "ImperialArtDetailClaimSource",
        back_populates="art_detail",
        cascade="all, delete-orphan",
    )
    questions: Mapped[list["ImperialArtDetailQuestion"]] = relationship(
        "ImperialArtDetailQuestion",
        back_populates="art_detail",
        cascade="all, delete-orphan",
    )
    hotspots: Mapped[list["ImperialMediaHotspot"]] = relationship(
        "ImperialMediaHotspot",
        back_populates="art_detail",
    )


# --------------------------------------------------------------------------- #
# 3. ImperialMediaHotspot
# --------------------------------------------------------------------------- #
class ImperialMediaHotspot(Base):
    """Normalized UV hotspot marker or region overlaid on learning media."""

    __tablename__ = "imperial_media_hotspots"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_media_hotspots_scope"),
        CheckConstraint("point_kind IN ('point', 'rect', 'polygon')", name="ck_imperial_media_hotspots_point_kind"),
        CheckConstraint("u >= 0.0 AND u <= 1.0", name="ck_imperial_media_hotspots_u_range"),
        CheckConstraint("v >= 0.0 AND v <= 1.0", name="ck_imperial_media_hotspots_v_range"),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
            name="ck_imperial_media_hotspots_review",
        ),
        Index("idx_imperial_media_hotspots_media", "media_id"),
        Index("idx_imperial_media_hotspots_detail", "detail_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_learning_media.id", ondelete="CASCADE"),
        nullable=False,
    )
    point_kind: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'point'")
    )
    u: Mapped[float] = mapped_column(Numeric(9, 7), nullable=False)
    v: Mapped[float] = mapped_column(Numeric(9, 7), nullable=False)
    position_payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_art_details.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    media: Mapped["ImperialLearningMedia"] = relationship(
        "ImperialLearningMedia", back_populates="hotspots"
    )
    art_detail: Mapped[Optional["ImperialArtDetail"]] = relationship(
        "ImperialArtDetail", back_populates="hotspots"
    )


# --------------------------------------------------------------------------- #
# 4. ImperialArtDetailClaimSource
# --------------------------------------------------------------------------- #
class ImperialArtDetailClaimSource(Base):
    """Historical claim attribution and primary source citation for an art detail."""

    __tablename__ = "imperial_art_detail_claim_sources"
    __table_args__ = (
        CheckConstraint(
            "content_scope = 'STTT_IMPERIAL_CITY'",
            name="ck_imperial_art_detail_claim_sources_scope",
        ),
        CheckConstraint(
            "evidence_strength IN ('verified', 'probable', 'traditional')",
            name="ck_imperial_art_detail_claim_sources_strength",
        ),
        Index("idx_imperial_art_detail_claim_sources_detail", "detail_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    detail_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_art_details.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_locator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_strength: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'verified'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    art_detail: Mapped["ImperialArtDetail"] = relationship(
        "ImperialArtDetail", back_populates="claim_sources"
    )


# --------------------------------------------------------------------------- #
# 5. ImperialArtDetailQuestion
# --------------------------------------------------------------------------- #
class ImperialArtDetailQuestion(Base):
    """Formative inquiry question bound to an art detail."""

    __tablename__ = "imperial_art_detail_questions"
    __table_args__ = (
        CheckConstraint(
            "content_scope = 'STTT_IMPERIAL_CITY'",
            name="ck_imperial_art_detail_questions_scope",
        ),
        Index("idx_imperial_art_detail_questions_detail", "detail_id"),
        Index("idx_imperial_art_detail_questions_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    detail_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_art_details.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'multiple_choice'")
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    answer_key: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    art_detail: Mapped["ImperialArtDetail"] = relationship(
        "ImperialArtDetail", back_populates="questions"
    )


# --------------------------------------------------------------------------- #
# 6. ImperialClue
# --------------------------------------------------------------------------- #
class ImperialClue(Base):
    """Heritage detective riddle / clue pointing to a site or art detail."""

    __tablename__ = "imperial_clues"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_clues_scope"),
        CheckConstraint("target_type IN ('site', 'art_detail')", name="ck_imperial_clues_target_type"),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
            name="ck_imperial_clues_review",
        ),
        Index("idx_imperial_clues_target", "target_type", "target_id"),
        Index("idx_imperial_clues_review", "review_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    clue_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    hint_steps: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    grade_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    attempts: Mapped[list["ImperialClueAttempt"]] = relationship(
        "ImperialClueAttempt", back_populates="clue", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# 7. ImperialClueAttempt
# --------------------------------------------------------------------------- #
class ImperialClueAttempt(Base):
    """Student/user attempt on a detective clue."""

    __tablename__ = "imperial_clue_attempts"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_clue_attempts_scope"),
        Index("idx_imperial_clue_attempts_clue", "clue_id"),
        Index("idx_imperial_clue_attempts_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    clue_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_clues.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_target_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempt_number: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    clue: Mapped["ImperialClue"] = relationship("ImperialClue", back_populates="attempts")
    user: Mapped[Optional[Any]] = relationship("User")


# --------------------------------------------------------------------------- #
# 8. ImperialQuestion
# --------------------------------------------------------------------------- #
class ImperialQuestion(Base):
    """Gamified quiz question (multiple choice, matching, hotspot) grounded in evidence."""

    __tablename__ = "imperial_questions"
    __table_args__ = (
        CheckConstraint("content_scope = 'STTT_IMPERIAL_CITY'", name="ck_imperial_questions_scope"),
        CheckConstraint(
            "question_type IN ('multiple_choice', 'matching', 'hotspot_identify')",
            name="ck_imperial_questions_type",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
            name="ck_imperial_questions_review",
        ),
        Index("idx_imperial_questions_site", "site_id"),
        Index("idx_imperial_questions_detail", "detail_id"),
        Index("idx_imperial_questions_review", "review_status"),
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
    detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("imperial_art_details.id", ondelete="SET NULL"),
        nullable=True,
    )
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'multiple_choice'")
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    answer_key: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_why: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    site: Mapped[Optional["ImperialSite"]] = relationship("ImperialSite")
    art_detail: Mapped[Optional["ImperialArtDetail"]] = relationship("ImperialArtDetail")


# --------------------------------------------------------------------------- #
# 9. ImperialAssignmentRelease
# --------------------------------------------------------------------------- #
class ImperialAssignmentRelease(Base):
    """Teacher released assignment / quest / journey for a specific classroom."""

    __tablename__ = "imperial_assignment_releases"
    __table_args__ = (
        CheckConstraint(
            "content_scope = 'STTT_IMPERIAL_CITY'",
            name="ck_imperial_assignment_releases_scope",
        ),
        Index("idx_imperial_assignment_releases_teacher", "teacher_id"),
        Index("idx_imperial_assignment_releases_journey", "journey_slug"),
        Index("idx_imperial_assignment_releases_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text(f"'{CONTENT_SCOPE_IMPERIAL}'")
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_name: Mapped[str] = mapped_column(String(255), nullable=False)
    journey_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rubric_weights: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # Relationships
    teacher: Mapped[Any] = relationship("User")
