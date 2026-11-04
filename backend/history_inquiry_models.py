# -*- coding: utf-8 -*-
"""Peer / Group Historical Inquiry models (V5-T038 / Wave W03, Slot A08).

Supports collaborative source evidence synthesis, teacher moderation, and
privacy isolation for historical inquiry activities.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


class InquirySubmissionStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    revision_requested = "revision_requested"


class InquiryPrivacyMode(str, Enum):
    private_group = "private_group"
    class_visible = "class_visible"


class InquiryMemberRole(str, Enum):
    leader = "leader"
    contributor = "contributor"


class HistoricalInquiryActivity(Base):
    """Pedagogical historical inquiry activity / research question assigned to a class."""

    __tablename__ = "historical_inquiry_activities"
    __table_args__ = (
        Index("idx_inquiry_activities_class", "classroom_id"),
        Index("idx_inquiry_activities_creator", "created_by_id"),
        Index("idx_inquiry_activities_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    guiding_questions: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    suggested_source_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    suggested_claim_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    rubric_criteria: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
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
    groups: Mapped[list["HistoricalInquiryGroup"]] = relationship(
        "HistoricalInquiryGroup",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class HistoricalInquiryGroup(Base):
    """Peer collaboration group formed to address a historical inquiry activity."""

    __tablename__ = "historical_inquiry_groups"
    __table_args__ = (
        Index("idx_inquiry_groups_activity", "activity_id"),
        Index("idx_inquiry_groups_classroom", "classroom_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_inquiry_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    activity: Mapped["HistoricalInquiryActivity"] = relationship(
        "HistoricalInquiryActivity", back_populates="groups"
    )
    members: Mapped[list["HistoricalInquiryGroupMember"]] = relationship(
        "HistoricalInquiryGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    submission: Mapped[Optional["HistoricalInquirySubmission"]] = relationship(
        "HistoricalInquirySubmission",
        back_populates="group",
        uselist=False,
        cascade="all, delete-orphan",
    )


class HistoricalInquiryGroupMember(Base):
    """Membership of students within a peer historical inquiry group."""

    __tablename__ = "historical_inquiry_group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_inquiry_group_members"),
        Index("idx_inquiry_group_members_group", "group_id"),
        Index("idx_inquiry_group_members_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_inquiry_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=InquiryMemberRole.contributor.value
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    group: Mapped["HistoricalInquiryGroup"] = relationship(
        "HistoricalInquiryGroup", back_populates="members"
    )
    user: Mapped[Any] = relationship("User")


class HistoricalInquirySubmission(Base):
    """Collaborative evidence synthesis and historical argument submitted by a group."""

    __tablename__ = "historical_inquiry_submissions"
    __table_args__ = (
        UniqueConstraint("group_id", name="uq_inquiry_submissions_group"),
        Index("idx_inquiry_submissions_activity", "activity_id"),
        Index("idx_inquiry_submissions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_inquiry_groups.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_inquiry_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    synthesis_argument: Mapped[str] = mapped_column(Text, nullable=False, default="")
    epistemic_rating: Mapped[str] = mapped_column(
        String(50), nullable=False, default="dang_khao_cuu"
    )
    evidence_items: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=InquirySubmissionStatus.draft.value
    )
    privacy_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default=InquiryPrivacyMode.private_group.value
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rubric_evaluation: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )
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

    # Relationships
    group: Mapped["HistoricalInquiryGroup"] = relationship(
        "HistoricalInquiryGroup", back_populates="submission"
    )
    activity: Mapped["HistoricalInquiryActivity"] = relationship(
        "HistoricalInquiryActivity"
    )
    submitted_by: Mapped[Any] = relationship("User", foreign_keys=[submitted_by_id])
    moderated_by: Mapped[Any] = relationship("User", foreign_keys=[moderated_by_id])
