# -*- coding: utf-8 -*-
"""Museum Operator Media CMS domain models (Wave W04 / Slot A10 / V5-T050).

Provides models for museum operator media asset management:
- Secure asset uploads (GLB, PNG, JPEG, WEBP)
- Licensing & rights metadata (rights owner, license type, attribution, display permissions)
- Staged publication lifecycle (draft -> in_review -> approved -> published / rejected / archived)
- Revision/version tracking
- Integration with historical assets and audit trail
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BIGINT,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


class MediaCmsStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    published = "published"
    rejected = "rejected"
    archived = "archived"


class MediaCmsAssetType(str, enum.Enum):
    image = "image"
    model3d = "model3d"
    mesh = "mesh"
    drawing = "drawing"
    rubbing2d = "rubbing2d"


class MediaCmsFileFormat(str, enum.Enum):
    glb = "glb"
    png = "png"
    jpeg = "jpeg"
    webp = "webp"


class MediaCmsItem(Base):
    """Museum operator media CMS asset with staged publication approval."""

    __tablename__ = "media_cms_items"
    __table_args__ = (
        CheckConstraint(
            "publication_status IN ('draft', 'in_review', 'approved', 'published', 'rejected', 'archived')",
            name="ck_media_cms_status",
        ),
        CheckConstraint(
            "file_format IN ('glb', 'png', 'jpeg', 'webp')",
            name="ck_media_cms_format",
        ),
        Index("idx_media_cms_status", "publication_status"),
        Index("idx_media_cms_relic", "relic_slug"),
        Index("idx_media_cms_entity", "historical_entity_id"),
        Index("idx_media_cms_type", "asset_type"),
        Index("idx_media_cms_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="image", server_default=text("'image'")
    )
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BIGINT, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Licensing and Rights Metadata (strictly verified)
    rights_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    license_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attribution: Mapped[str] = mapped_column(Text, nullable=False)
    public_display_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    derivative_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    # Historical relic / entity link
    historical_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    relic_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Staged approval & versioning
    publication_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft", server_default=text("'draft'")
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attribution & Timestamps
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    historical_entity = relationship("HistoricalEntity", foreign_keys=[historical_entity_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
