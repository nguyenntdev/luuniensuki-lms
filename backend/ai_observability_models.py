# -*- coding: utf-8 -*-
"""AI Observability & Budgeting Domain Models (Wave W06 / Slot A09 / V5-T069).

Provides models for:
- Telemetry logging: token tracking (prompt/completion), latency, cost, model,
  citation validity, and error codes with STRICT ZERO PII (prompt SHA-256 only).
- Budget caps: user-level and classroom-level token ceilings and USD cost limits.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


class AITelemetryLog(Base):
    """Immutable telemetry event log for AI operations.

    STRICT INVARIANT: NEVER stores raw user prompts, user emails, names, or PII.
    Only stores cryptographic prompt hashes (SHA-256), token counts, latency,
    cost estimates, and citation validity statistics.
    """

    __tablename__ = "ai_telemetry_logs"
    __table_args__ = (
        Index("idx_ai_telemetry_user_created", "user_id", "created_at"),
        Index("idx_ai_telemetry_classroom_created", "classroom_id", "created_at"),
        Index("idx_ai_telemetry_operation", "operation"),
        Index("idx_ai_telemetry_created_at", "created_at"),
        Index("idx_ai_telemetry_status", "status"),
        Index("idx_ai_telemetry_model", "model"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    operation: Mapped[str] = mapped_column(
        String(100), nullable=False, default="tutor"
    )
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="gemini-3.8-flash-tiered"
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="clara"
    )

    # Token usage metrics
    prompt_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    # Performance & Financial metrics
    latency_ms: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default=text("0.0")
    )
    cost_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default=text("0.0")
    )

    # Citation validity metrics
    citation_valid_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    citation_invalid_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    citation_validity_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0, server_default=text("1.0")
    )

    # Status & Error handling
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="success", server_default=text("'success'")
    )  # success, budget_exhausted, provider_error, rate_limited, fallback_used
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Zero-PII Prompt Signature (SHA-256 digest of normalized prompt)
    prompt_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AIBudgetCap(Base):
    """Configurable AI token and cost budget ceilings for users and classrooms.

    When an entity exhausts its budget, queries receive HTTP 429/503 capacity limit
    responses with an explicit retry policy and deterministic fallbacks.
    """

    __tablename__ = "ai_budget_caps"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_ai_budget_caps_entity"),
        Index("idx_ai_budget_caps_entity", "entity_type", "entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # "user", "classroom"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    daily_token_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=500_000, server_default=text("500000")
    )
    daily_cost_limit_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0, server_default=text("5.0")
    )
    max_tokens_per_request: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4096, server_default=text("4096")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
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
