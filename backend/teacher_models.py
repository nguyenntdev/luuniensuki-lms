# -*- coding: utf-8 -*-
"""SQLAlchemy models for Teacher Onboarding and Support Center (Ticket V5-T099 / W09-A09)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .models import School, User


class TeacherSupportTicket(Base):
    """Teacher support ticket for technical, pedagogical, curriculum or verification help."""

    __tablename__ = "teacher_support_tickets"
    __table_args__ = (
        Index("idx_teacher_tickets_teacher", "teacher_id"),
        Index("idx_teacher_tickets_status", "status"),
        Index("idx_teacher_tickets_category", "category"),
        Index("idx_teacher_tickets_code", "ticket_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
    )
    ticket_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'normal'")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'open'")
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    admin_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responses: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
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

    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    school: Mapped[Optional["School"]] = relationship(foreign_keys=[school_id])


class TeacherOnboardingProfile(Base):
    """Tracks teacher interactive onboarding tour progress, school verification, and demo status."""

    __tablename__ = "teacher_onboarding_profiles"
    __table_args__ = (
        Index("idx_teacher_onboarding_teacher", "teacher_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_school_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    current_step: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'welcome'")
    )
    completed_steps: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    tour_dismissed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
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

    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    school: Mapped[Optional["School"]] = relationship(foreign_keys=[school_id])
