# -*- coding: utf-8 -*-
"""SQLAlchemy models for Pilot Onboarding Portal (Ticket V5-T116 / Wave W11 Slot A06).

Implements:
- Invitation-gated pilot access for verified teachers/schools and artisan partners
- Invitation tokens with expiration, max usage, target role, tenant binding, and revocation
- Pilot participant activations with guided onboarding checklist and compliance acknowledgment
- Pilot usage health telemetry tracking active engagement, health score, and risk indicators
- Pilot dedicated support tickets / feedback requests with SLA tracking
- Negative abuse invariant: Users without valid invitations/tokens CANNOT join private school/partner trials.
"""
from __future__ import annotations

import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


class PilotInvitation(Base):
    """Secure invitation token granting access to private school or partner pilots."""

    __tablename__ = "pilot_invitations"
    __table_args__ = (
        Index("idx_pilot_invitations_token", "token_hash"),
        Index("idx_pilot_invitations_code", "invitation_code"),
        Index("idx_pilot_invitations_status", "status"),
        Index("idx_pilot_invitations_tenant", "target_role", "organization_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invitation_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    pilot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "school_teacher" or "artisan_partner"
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="SET NULL"),
        nullable=True,
    )
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'active'")
    )  # active, exhausted, expired, revoked
    invited_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PilotParticipantActivation(Base):
    """Record of an authenticated user redeeming a pilot invitation and completing guided activation."""

    __tablename__ = "pilot_participant_activations"
    __table_args__ = (
        Index("idx_pilot_activations_user", "user_id"),
        Index("idx_pilot_activations_invitation", "invitation_id"),
        Index("idx_pilot_activations_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pilot_invitations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "school_teacher" or "artisan_partner"
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'activated'")
    )  # activated, onboarding, completed, suspended
    current_step: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'welcome'")
    )
    completed_steps: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    compliance_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    compliance_accepted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PilotUsageHealth(Base):
    """Tracks pilot usage health, activity signals, and churn risk for a participant."""

    __tablename__ = "pilot_usage_health"
    __table_args__ = (
        Index("idx_pilot_health_user", "user_id"),
        Index("idx_pilot_health_status", "health_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    activation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pilot_participant_activations.id", ondelete="CASCADE"),
        nullable=False,
    )
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    actions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_action_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_active_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    health_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0
    )  # 0 to 100
    health_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'healthy'")
    )  # healthy, attention_needed, at_risk, inactive
    telemetry_summary: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PilotSupportRequest(Base):
    """Dedicated pilot feedback and support requests with SLA and resolution tracking."""

    __tablename__ = "pilot_support_requests"
    __table_args__ = (
        Index("idx_pilot_support_user", "user_id"),
        Index("idx_pilot_support_status", "status"),
        Index("idx_pilot_support_category", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pilot_participant_activations.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # activation, onboarding_help, feature_feedback, data_privacy, bug_report
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'normal'")
    )  # low, normal, high, urgent
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'open'")
    )  # open, in_progress, resolved, closed
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    responses: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
