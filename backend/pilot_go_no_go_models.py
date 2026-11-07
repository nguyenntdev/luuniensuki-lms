# -*- coding: utf-8 -*-
"""SQLAlchemy models for Pilot Go/No-Go Board (Ticket V5-T129 / Wave W12 Slot A09).

Features:
- Pilot go/no-go board evaluating production readiness for RBPC 2026.
- Signed owner decisions across 5 critical domains (Integrator, Historian, Business, Frontend, DevOps).
- Blocking issue register tracking P0, P1, P2, P3 issues and resolution statuses.
- Feature flag rollout plan with granular kill switch capabilities.
- Quantified rollback triggers and automated remediation runbooks.
- 24/7 on-call support contacts and escalation matrices.
- Negative abuse invariant: Launch is strictly BLOCKED if any P0 issue remains unresolved.
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from .base_model import Base


class RbpcGoNoGoVerdict(str, Enum):
    GO = "GO"
    BLOCKED = "BLOCKED"
    NO_GO = "NO_GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"


class RbpcIssueSeverity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class RbpcIssueStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    MITIGATED = "MITIGATED"
    ACCEPTED_RISK = "ACCEPTED_RISK"


def _validate_enum_val(enum_cls: type[Enum], key: str, val: Any) -> str:
    if isinstance(val, enum_cls):
        return str(val.value)
    if isinstance(val, str):
        allowed = {e.value for e in enum_cls}
        if val in allowed:
            return val
        raise ValueError(f"Invalid {key}: '{val}'. Must be one of {sorted(allowed)}")
    raise ValueError(f"Invalid {key}: expected {enum_cls.__name__} or str, got {type(val).__name__}")


class RbpcPilotGoNoGoEvaluation(Base):
    """Immutable audit records for Pilot Go/No-Go Board evaluations."""

    __tablename__ = "rbpc_pilot_go_no_go_evaluations"
    __table_args__ = (
        UniqueConstraint("board_ref", name="uq_rbpc_go_no_go_board_ref"),
        CheckConstraint(
            "verdict IN ('GO','BLOCKED','NO_GO','CONDITIONAL_GO')",
            name="ck_rbpc_go_no_go_verdict",
        ),
        Index("idx_rbpc_go_no_go_ref", "board_ref"),
        Index("idx_rbpc_go_no_go_verdict", "verdict"),
        Index("idx_rbpc_go_no_go_env", "target_environment"),
        Index("idx_rbpc_go_no_go_eval_at", "evaluated_at"),
        Index("idx_rbpc_go_no_go_blocked", "is_launch_blocked"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    board_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    release_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v2026.1.0-rbpc")
    target_environment: Mapped[str] = mapped_column(String(64), nullable=False, default="staging")
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, default=RbpcGoNoGoVerdict.BLOCKED.value)
    open_p0_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_p1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_p2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signed_owners_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_launch_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    blocking_reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    owner_decisions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    blocking_issues: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    feature_flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    rollback_triggers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    support_contacts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    evaluated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @validates("verdict")
    def validate_verdict(self, key: str, value: Any) -> str:
        return _validate_enum_val(RbpcGoNoGoVerdict, key, value)
