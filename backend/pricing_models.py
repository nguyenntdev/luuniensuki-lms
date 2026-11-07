# -*- coding: utf-8 -*-
"""SQLAlchemy models for Pricing Experiment Instrumentation (Ticket V5-T117 / W11-A07).

Implements:
- A/B pricing interest tracking with user consent
- Strict anti-abuse: pricing tier or calculator clicks do NOT count as paying customers or revenue
- Real contract acceptance logging
- Zero dark patterns / explicit consent lifecycle
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .models import School, User


class PricingTierKey(str, Enum):
    pilot = "pilot"
    standard_school = "standard_school"
    district_enterprise = "district_enterprise"
    artisan_pro = "artisan_pro"


class PricingEventType(str, Enum):
    tier_view = "tier_view"
    calculator_interaction = "calculator_interaction"
    quote_inquiry = "quote_inquiry"
    contract_sign_attempt = "contract_sign_attempt"
    contract_accepted = "contract_accepted"


class ContractStatus(str, Enum):
    draft = "draft"
    pending_signature = "pending_signature"
    signed_and_executed = "signed_and_executed"
    cancelled = "cancelled"


class PricingExperimentEvent(Base):
    """Tracks pricing interest events with explicit telemetry consent and zero dark patterns.

    Negative abuse invariant (V5-T117):
    Events with event_type in ('tier_view', 'calculator_interaction', 'quote_inquiry')
    produce EXACTLY is_paying_customer=False and revenue_impact_vnd=0.0.
    Merely clicking or calculating does NOT count as a paying customer or recognized revenue.
    """

    __tablename__ = "pricing_experiment_events"
    __table_args__ = (
        Index("idx_pricing_exp_user", "user_id"),
        Index("idx_pricing_exp_experiment", "experiment_key"),
        Index("idx_pricing_exp_type", "event_type"),
        Index("idx_pricing_exp_tier", "tier_key"),
        Index("idx_pricing_exp_created", "created_at"),
        CheckConstraint(
            "event_type IN ('tier_view', 'calculator_interaction', 'quote_inquiry', 'contract_sign_attempt', 'contract_accepted')",
            name="ck_pricing_exp_event_type",
        ),
        CheckConstraint(
            "revenue_impact_vnd >= 0.0",
            name="ck_pricing_exp_revenue_nonneg",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    anonymous_session_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    experiment_key: Mapped[str] = mapped_column(
        String(100), nullable=False, default="school_pricing_v1"
    )
    variant_key: Mapped[str] = mapped_column(
        String(50), nullable=False, default="control"
    )  # e.g., "annual_flat", "per_student_metered", "curriculum_bundle"
    tier_key: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # pilot, standard_school, district_enterprise, artisan_pro
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    
    # Explicit Consent & Anti-Dark-Pattern Auditing
    has_experiment_consent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    consent_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="2026.1-pricing"
    )

    # Strictly enforced anti-abuse flags
    is_paying_customer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    revenue_impact_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0
    )

    calculator_params: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    client_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class PricingContract(Base):
    """Institutional / School B2B real contract acceptance.

    Represents verified commercial intent and legally bound commitment.
    Only contracts transitioning to 'signed_and_executed' with dual-party signatures
    represent paying customers and agreed contract value.
    """

    __tablename__ = "pricing_contracts"
    __table_args__ = (
        UniqueConstraint("contract_number", name="uq_pricing_contract_number"),
        Index("idx_pricing_contract_school", "school_id"),
        Index("idx_pricing_contract_status", "status"),
        Index("idx_pricing_contract_signer", "signer_user_id"),
        CheckConstraint(
            "status IN ('draft', 'pending_signature', 'signed_and_executed', 'cancelled')",
            name="ck_pricing_contract_status",
        ),
        CheckConstraint(
            "contract_value_vnd >= 0.0",
            name="ck_pricing_contract_value_nonneg",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contract_number: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    signer_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tier_key: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    variant_key: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    contract_value_vnd: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0.0
    )
    student_seat_capacity: Mapped[int] = mapped_column(
        Numeric(8, 0), nullable=False, default=100
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ContractStatus.draft.value
    )
    terms_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v2026.1-edu"
    )
    signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signature_ip_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    verification_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
