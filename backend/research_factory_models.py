# -*- coding: utf-8 -*-
"""Research Factory domain models — V5 Wave W07.

Spec reference: V3.C3 / V4.3 / AIR-041–045.
Provides schema for:
- research_runs: Global run version, config hash, cost budget
- research_phases: Barrier state for P00..P11, input/gate SHA256
- research_agent_jobs: 10 unique slots per wave, leasing with TTL and worker pod IDs
- research_job_attempts: Historical trace of job attempts
- research_job_leases: Audit of lease grants, heartbeats and revocations
- research_budgets: Per-run / per-provider token and cost allocations
- research_evidence_results: Immutable envelope output per agent job
- provider_semaphore_leases: Distributed cross-pod rate/concurrency control for AI/OCR providers
- provider_concurrency_configs: Configurable provider concurrency and rate limits
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
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


# --------------------------------------------------------------------------- #
# Controlled Vocabularies
# --------------------------------------------------------------------------- #
class ResearchRunStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELED = "CANCELLED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    BLOCKED = "BLOCKED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    PUBLISHED = "PUBLISHED"
    ROLLED_BACK = "ROLLED_BACK"


class ResearchPhaseCode(str, Enum):
    P00 = "P00"  # Scope & Urn Relief Targeting
    P01 = "P01"  # Archival Discovery & Candidate Collection
    P02 = "P02"  # Ingestion & Legal Clearance
    P03 = "P03"  # Text Extraction & Hán-Nôm Transcription
    P04 = "P04"  # Historical Entity Linking & Disambiguation
    P05 = "P05"  # Atomic Historical Claim Extraction
    P06 = "P06"  # Scholarly Cross-Check & Contradiction Resolution
    P07 = "P07"  # Bilingual Narrative Synthesis
    P08 = "P08"  # Pedagogical Curriculum & Lesson Generation
    P09 = "P09"  # Peer Multi-Agent Red Teaming & Verification
    P10 = "P10"  # Human Editorial Sign-Off
    P11 = "P11"  # Immutable Publication & Release Manifest


class ResearchPhaseStatus(str, Enum):
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    FAN_IN = "FAN_IN"
    GATED = "GATED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELED = "CANCELLED"
    COMPLETED = "COMPLETED"


ResearchPhaseState = ResearchPhaseStatus


class ResearchJobStatus(str, Enum):
    QUEUED = "QUEUED"
    LEASED = "LEASED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    NO_EVIDENCE = "NO_EVIDENCE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    CANCELED = "CANCELLED"


ResearchJobState = ResearchJobStatus


class ResearchLeaseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    LOST = "LOST"
    COMPLETED = "COMPLETED"
    REVOKED = "REVOKED"


# --------------------------------------------------------------------------- #
# Table Models
# --------------------------------------------------------------------------- #
class ResearchRun(Base):
    """Execution run across historical entities/urns."""

    __tablename__ = "research_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scope_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="cuu_dinh_162_motifs"
    )
    content_scope: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default="NINE_URNS"
    )
    subject_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, default="RELIEF"
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    subject_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    source_release_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResearchRunStatus.QUEUED.value
    )
    current_phase: Mapped[str] = mapped_column(
        String(16), nullable=False, default="P00"
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    run_manifest_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    cost_budget: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    worker_slots_per_phase: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    max_active_phases_per_run: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    human_approval_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    metadata_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    phases: Mapped[list["ResearchPhase"]] = relationship(
        "ResearchPhase", back_populates="run", cascade="all, delete-orphan"
    )
    budgets: Mapped[list["ResearchBudget"]] = relationship(
        "ResearchBudget", back_populates="run", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        if "subject_id" in kwargs and "subject_ids" not in kwargs:
            kwargs["subject_ids"] = [kwargs["subject_id"]]
        elif "subject_ids" in kwargs and kwargs["subject_ids"] and "subject_id" not in kwargs:
            kwargs["subject_id"] = str(kwargs["subject_ids"][0])
        super().__init__(**kwargs)


class ResearchPhase(Base):
    """Barrier phase within a run. Exactly 10 slots per wave dispatched."""

    __tablename__ = "research_phases"
    __table_args__ = (
        UniqueConstraint("run_id", "phase_code", "wave", name="uq_research_phase_run_wave"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_code: Mapped[str] = mapped_column(String(10), nullable=False)
    phase_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wave: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResearchPhaseStatus.QUEUED.value
    )
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    input_manifest_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    gate_manifest_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    output_snapshot_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    barrier_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gate_checks: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="phases")
    jobs: Mapped[list["ResearchJob"]] = relationship(
        "ResearchJob", back_populates="phase", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        if "status" in kwargs and "state" not in kwargs:
            kwargs["state"] = kwargs["status"]
        elif "state" in kwargs and "status" not in kwargs:
            kwargs["status"] = kwargs["state"]
        if "input_manifest_sha256" in kwargs and "input_sha256" not in kwargs:
            kwargs["input_sha256"] = kwargs["input_manifest_sha256"]
        if "output_snapshot_sha256" in kwargs and "gate_manifest_sha256" not in kwargs:
            kwargs["gate_manifest_sha256"] = kwargs["output_snapshot_sha256"]
        super().__init__(**kwargs)


class ResearchJob(Base):
    """Individual agent task slot (1..10 per wave).

    Leased using SELECT ... FOR UPDATE SKIP LOCKED.
    """

    __tablename__ = "research_agent_jobs"
    __table_args__ = (
        UniqueConstraint("phase_id", "slot_number", name="uq_research_job_phase_slot"),
        CheckConstraint("slot_number BETWEEN 1 AND 10", name="chk_research_job_slot_range"),
        Index("research_job_leases_idx", "state", "lease_until"),
        Index("research_job_queue_idx", "state", "available_at", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    role_key: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResearchJobStatus.QUEUED.value, index=True
    )
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Distributed leasing attributes
    lease_owner: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # e.g. "pod-worker-01:pid-1234"
    lease_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # Cryptographic UUID / secret nonce to prevent stale heartbeats
    lease_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Workload & Provider details
    provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g. "openai", "gemini", "ocr"
    model_identifier: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    estimated_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    input_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    output_schema_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="v1"
    )

    # Result & Artifacts
    output_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    result_envelope: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    phase: Mapped["ResearchPhase"] = relationship("ResearchPhase", back_populates="jobs")
    attempts: Mapped[list["ResearchAttempt"]] = relationship(
        "ResearchAttempt", back_populates="job", cascade="all, delete-orphan"
    )
    leases: Mapped[list["ResearchLease"]] = relationship(
        "ResearchLease", back_populates="job", cascade="all, delete-orphan"
    )
    evidence_results: Mapped[list["ResearchEvidenceResult"]] = relationship(
        "ResearchEvidenceResult", back_populates="job", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        if "agent_index" in kwargs and "slot_number" not in kwargs:
            kwargs["slot_number"] = kwargs["agent_index"]
        elif "slot_number" in kwargs and "agent_index" not in kwargs:
            kwargs["agent_index"] = kwargs["slot_number"]
        if "agent_role" in kwargs and "role_key" not in kwargs:
            kwargs["role_key"] = kwargs["agent_role"]
        elif "role_key" in kwargs and "agent_role" not in kwargs:
            kwargs["agent_role"] = kwargs["role_key"]
        if "status" in kwargs and "state" not in kwargs:
            kwargs["state"] = kwargs["status"]
        elif "state" in kwargs and "status" not in kwargs:
            kwargs["status"] = kwargs["state"]
        if "attempts_count" in kwargs and "attempt" not in kwargs:
            kwargs["attempt"] = kwargs["attempts_count"]
        elif "attempt" in kwargs and "attempts_count" not in kwargs:
            kwargs["attempts_count"] = kwargs["attempt"]
        if "max_retries" in kwargs and "max_attempts" not in kwargs:
            kwargs["max_attempts"] = kwargs["max_retries"]
        elif "max_attempts" in kwargs and "max_retries" not in kwargs:
            kwargs["max_retries"] = kwargs["max_attempts"]
        if "input_payload" in kwargs and "payload" not in kwargs:
            kwargs["payload"] = kwargs["input_payload"]
        elif "payload" in kwargs and "input_payload" not in kwargs:
            kwargs["input_payload"] = kwargs["payload"]
        super().__init__(**kwargs)


# Alias for spec parity
ResearchAgentJob = ResearchJob


class ResearchAttempt(Base):
    """Execution attempt of a research job slot."""

    __tablename__ = "research_job_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_agent_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResearchJobStatus.RUNNING.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job: Mapped["ResearchJob"] = relationship("ResearchJob", back_populates="attempts")


class ResearchLease(Base):
    """Historical ledger of lease grants, renewals and releases."""

    __tablename__ = "research_job_leases"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_agent_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lease_token: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResearchLeaseStatus.ACTIVE.value
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    job: Mapped["ResearchJob"] = relationship("ResearchJob", back_populates="leases")


class ResearchBudget(Base):
    """Run-level provider budget allocation and token spend."""

    __tablename__ = "research_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    allocated: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    spent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="budgets")


class ResearchEvidenceResult(Base):
    """Immutable envelope output produced by an agent slot."""

    __tablename__ = "research_evidence_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_agent_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="research-agent-result/v1"
    )
    output_schema: Mapped[str] = mapped_column(
        String(64), nullable=False, default="default/v1"
    )
    input_manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    model_identifier: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="SUCCEEDED")
    source_ids: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    claim_ids: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    evidence_locator_ids: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    usage_metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    failures: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    raw_envelope: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    job: Mapped["ResearchJob"] = relationship(
        "ResearchJob", back_populates="evidence_results"
    )


class ProviderSemaphoreLease(Base):
    """Distributed cross-worker semaphore lease for third-party AI/OCR APIs."""

    __tablename__ = "provider_semaphore_leases"
    __table_args__ = (
        Index("idx_provider_semaphore_expires", "provider", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    holder_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lease_token: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProviderConcurrencyConfig(Base):
    """Per-provider rate & concurrency limits."""

    __tablename__ = "provider_concurrency_configs"

    provider: Mapped[str] = mapped_column(String(100), primary_key=True)
    max_concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


ResearchJob = ResearchAgentJob
ResearchJobStatus = ResearchJobState
ResearchPhaseStatus = ResearchPhaseState


# --------------------------------------------------------------------------- #
# P11 Publication Releases, Invalidation & Rollback Models (V5-T079 / W07-A09)
# --------------------------------------------------------------------------- #
class ResearchPublicationRelease(Base):
    """Immutable, cryptographically signed publication release manifest and snapshot."""

    __tablename__ = "research_publication_releases"
    __table_args__ = (
        Index("idx_research_pub_release_code", "release_code"),
        Index("idx_research_pub_release_status", "status"),
        Index("idx_research_pub_release_run", "run_id"),
        Index("idx_research_pub_release_manifest", "manifest_sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    release_code: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    scope: Mapped[str] = mapped_column(
        String(100), nullable=False, default="cuu_dinh_162_motifs"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PREPARED"
    )
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signed_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    signer_identity: Mapped[str] = mapped_column(String(255), nullable=False)
    signer_role: Mapped[str] = mapped_column(String(64), nullable=False, default="admin")
    snapshot_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    previous_release_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_publication_releases.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invalidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invalidation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cache_purge_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING"
    )
    purged_at: Mapped[Optional[datetime]] = mapped_column(
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

    correction_events: Mapped[list["ResearchCorrectionEvent"]] = relationship(
        "ResearchCorrectionEvent",
        back_populates="release",
        cascade="all, delete-orphan",
    )
    cache_purge_events: Mapped[list["ResearchCachePurgeEvent"]] = relationship(
        "ResearchCachePurgeEvent",
        back_populates="release",
        cascade="all, delete-orphan",
    )


class ResearchCorrectionEvent(Base):
    """P11 invalidation, errata, or retraction event."""

    __tablename__ = "research_correction_events"
    __table_args__ = (
        Index("idx_research_correction_release", "release_id"),
        Index("idx_research_correction_trigger", "trigger_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    release_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_publication_releases.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_claims.id", ondelete="SET NULL"),
        nullable=True,
    )
    story_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("history_stories.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    actor_identity: Mapped[str] = mapped_column(String(255), nullable=False)
    cache_purged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    release: Mapped["ResearchPublicationRelease"] = relationship(
        "ResearchPublicationRelease", back_populates="correction_events"
    )


class ResearchCachePurgeEvent(Base):
    """Purge event recorded for CDN / proxy / in-memory cache keys."""

    __tablename__ = "research_cache_purge_events"
    __table_args__ = (
        Index("idx_research_cache_purge_release", "release_id"),
        Index("idx_research_cache_purge_key", "cache_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    release_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_publication_releases.id", ondelete="CASCADE"),
        nullable=False,
    )
    cache_key: Mapped[str] = mapped_column(String(512), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    purge_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PURGED"
    )
    purged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    release: Mapped["ResearchPublicationRelease"] = relationship(
        "ResearchPublicationRelease", back_populates="cache_purge_events"
    )


# Spec aliases
AIPublicationRelease = ResearchPublicationRelease
AICorrectionEvent = ResearchCorrectionEvent


