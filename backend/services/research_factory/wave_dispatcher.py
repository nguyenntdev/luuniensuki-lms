# -*- coding: utf-8 -*-
"""10-Slot WaveDispatcher for AI Research Factory (W07-A02 / V5-T072).

Core invariants enforced:
1. Single transactional boundary: creates/enqueues exactly 10 unique slots per phase wave.
2. Slot numbering strictly 1..10 with unique constraint per phase.
3. Strict 10-role specification: If any required role is absent or invalid, the dispatch
   aborts atomically and the wave does not falsely count ten.
4. Input and payload snapshot digest: cryptographic SHA-256 computed and bound to phase and jobs.
5. Idempotent dispatch: re-dispatching with the same run/phase/wave is idempotent and returns
   the existing jobs without double queueing.
6. Durable queue: jobs are enqueued with QUEUED state, priority, and available_at ready
   for worker leasing.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import User, UserRole
from ...research_factory_models import (
    ResearchJob,
    ResearchJobStatus,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
    ResearchRunStatus,
)
from .roles import SubagentRoleSpec, get_roles_for_phase


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_payload_snapshot_hash(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of a payload dictionary."""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# --------------------------------------------------------------------------- #
# Typed DTOs and Exceptions
# --------------------------------------------------------------------------- #
class WaveDispatchError(Exception):
    """Base error for WaveDispatcher operations."""
    code: str = "WAVE_DISPATCH_ERROR"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class RoleIncompleteError(WaveDispatchError):
    """Raised when role definitions or required 10 roles are absent or invalid."""
    code = "ROLE_INCOMPLETE"


class InvalidPhaseStateError(WaveDispatchError):
    """Raised when the phase cannot be dispatched due to invalid run/phase state."""
    code = "INVALID_PHASE_STATE"


class WaveDispatchResult(BaseModel):
    """Result summary of a 10-slot wave dispatch."""
    run_id: UUID
    phase_id: UUID
    phase_code: str
    wave: int
    slot_count: int = 10
    input_sha256: str
    job_ids: List[UUID]
    roles: List[str]
    is_idempotent_replay: bool = False
    dispatched_at: datetime = Field(default_factory=_utcnow)

    @property
    def total_slots(self) -> int:
        return self.slot_count

    @property
    def jobs(self) -> List[UUID]:
        return self.job_ids


# --------------------------------------------------------------------------- #
# WaveDispatcher Implementation
# --------------------------------------------------------------------------- #
class WaveDispatcher:
    """Dispatches exactly 10 unique subagent slots per phase wave in a single transaction."""

    REQUIRED_SLOT_COUNT: int = 10

    def __init__(self, db: Session):
        self.db = db

    def dispatch_phase_wave(
        self,
        run_id: UUID,
        phase_code: str,
        wave: int = 1,
        input_payload: Optional[Dict[str, Any]] = None,
        role_overrides: Optional[List[SubagentRoleSpec]] = None,
        priority: int = 0,
        payload: Optional[Dict[str, Any]] = None,
    ) -> WaveDispatchResult:
        """Enqueues exactly 10 slots for a phase wave in a single transaction.

        Invariants enforced:
        - If role_overrides is provided, it MUST contain exactly 10 valid unique roles.
        - If any role is missing or slot indices do not match 1..10, transaction is aborted.
        - Payload snapshot hash is computed and stored on the phase and jobs.
        - Replay deduplication: if phase wave already dispatched with 10 jobs, returns replay result.
        """
        if payload is not None and input_payload is None:
            input_payload = payload
        # 1. Fetch and validate ResearchRun
        run = self.db.execute(
            select(ResearchRun).where(ResearchRun.id == run_id)
        ).scalar_one_or_none()
        if not run:
            raise WaveDispatchError(f"ResearchRun {run_id} not found.", {"run_id": str(run_id)})

        if run.status in [ResearchRunStatus.CANCELLED.value, ResearchRunStatus.FAILED.value]:
            raise InvalidPhaseStateError(
                f"Cannot dispatch phase wave for ResearchRun {run_id} in terminal state '{run.status}'.",
                {"run_id": str(run_id), "status": run.status},
            )

        phase_code_norm = phase_code.upper()
        if phase_code_norm not in [c.value for c in ResearchPhaseCode]:
            raise WaveDispatchError(f"Invalid phase code: {phase_code}", {"phase_code": phase_code})

        # 2. Resolve roles to dispatch
        roles: List[SubagentRoleSpec]
        if role_overrides is not None:
            # Negative abuse defense: Verify exactly 10 roles
            if len(role_overrides) != self.REQUIRED_SLOT_COUNT:
                raise RoleIncompleteError(
                    f"Phase {phase_code_norm} requires exactly {self.REQUIRED_SLOT_COUNT} roles, got {len(role_overrides)}.",
                    {
                        "phase_code": phase_code_norm,
                        "expected_count": self.REQUIRED_SLOT_COUNT,
                        "provided_count": len(role_overrides),
                    },
                )
            # Verify slot numbers 1..10
            slots_seen = {r.slot for r in role_overrides}
            if slots_seen != set(range(1, self.REQUIRED_SLOT_COUNT + 1)):
                raise RoleIncompleteError(
                    f"Role slots must be consecutive 1..10, got {sorted(slots_seen)}.",
                    {"phase_code": phase_code_norm, "slots": sorted(slots_seen)},
                )
            roles = sorted(role_overrides, key=lambda r: r.slot)
        else:
            roles = get_roles_for_phase(phase_code_norm)

        if len(roles) != self.REQUIRED_SLOT_COUNT:
            raise RoleIncompleteError(
                f"Role registry for {phase_code_norm} does not contain {self.REQUIRED_SLOT_COUNT} roles.",
                {"phase_code": phase_code_norm, "count": len(roles)},
            )

        # 3. Payload snapshot hash
        payload_dict = input_payload or {}
        payload_sha256 = compute_payload_snapshot_hash(payload_dict)

        # 4. Check if phase already exists
        phase = self.db.execute(
            select(ResearchPhase).where(
                ResearchPhase.run_id == run_id,
                ResearchPhase.phase_code == phase_code_norm,
                ResearchPhase.wave == wave,
            )
        ).scalar_one_or_none()

        if phase:
            existing_jobs = sorted(list(phase.jobs), key=lambda j: j.slot_number)
            if len(existing_jobs) == self.REQUIRED_SLOT_COUNT:
                # Idempotent replay: wave was already dispatched cleanly
                return WaveDispatchResult(
                    run_id=run.id,
                    phase_id=phase.id,
                    phase_code=phase.phase_code,
                    wave=phase.wave,
                    slot_count=len(existing_jobs),
                    input_sha256=phase.input_sha256,
                    job_ids=[j.id for j in existing_jobs],
                    roles=[j.role_key for j in existing_jobs],
                    is_idempotent_replay=True,
                )
            elif len(existing_jobs) > 0 and len(existing_jobs) != self.REQUIRED_SLOT_COUNT:
                raise RoleIncompleteError(
                    f"Corrupt wave: Phase {phase.id} has {len(existing_jobs)} jobs instead of {self.REQUIRED_SLOT_COUNT}.",
                    {"phase_id": str(phase.id), "existing_count": len(existing_jobs)},
                )
        else:
            phase = ResearchPhase(
                run_id=run.id,
                phase_code=phase_code_norm,
                wave=wave,
                state=ResearchPhaseStatus.DISPATCHED.value,
                input_sha256=payload_sha256,
            )
            self.db.add(phase)
            self.db.flush()

        # 5. Atomic single-transaction enqueue of exactly 10 slots
        created_jobs: List[ResearchJob] = []
        for role_spec in roles:
            job_idempotency_key = f"{run.id}:{phase_code_norm}:{wave}:{role_spec.slot}:{payload_sha256}"
            job = ResearchJob(
                phase_id=phase.id,
                slot_number=role_spec.slot,
                role_key=role_spec.code,
                idempotency_key=job_idempotency_key,
                state=ResearchJobStatus.QUEUED.value,
                attempt=0,
                priority=priority,
                provider=role_spec.default_provider,
                estimated_tokens=role_spec.estimated_tokens,
                payload=payload_dict,
            )
            self.db.add(job)
            created_jobs.append(job)

        # Update run status if in initial state
        if run.status == ResearchRunStatus.QUEUED.value:
            run.status = ResearchRunStatus.RUNNING.value

        self.db.commit()

        # Validate post-commit invariants
        assert len(created_jobs) == self.REQUIRED_SLOT_COUNT
        assert {j.slot_number for j in created_jobs} == set(range(1, 11))

        return WaveDispatchResult(
            run_id=run.id,
            phase_id=phase.id,
            phase_code=phase.phase_code,
            wave=phase.wave,
            slot_count=len(created_jobs),
            input_sha256=phase.input_sha256,
            job_ids=[j.id for j in created_jobs],
            roles=[j.role_key for j in created_jobs],
            is_idempotent_replay=False,
        )

    def get_phase_status_summary(self, phase_id: UUID) -> Dict[str, Any]:
        """Queries the current status of all 10 slots in a phase."""
        phase = self.db.execute(
            select(ResearchPhase).where(ResearchPhase.id == phase_id)
        ).scalar_one_or_none()
        if not phase:
            raise WaveDispatchError(f"ResearchPhase {phase_id} not found.")

        jobs = sorted(list(phase.jobs), key=lambda j: j.slot_number)
        return {
            "phase_id": str(phase.id),
            "run_id": str(phase.run_id),
            "phase_code": phase.phase_code,
            "wave": phase.wave,
            "state": phase.state,
            "slot_count": len(jobs),
            "is_complete_ten": len(jobs) == self.REQUIRED_SLOT_COUNT,
            "slots": [
                {
                    "slot_number": j.slot_number,
                    "role_key": j.role_key,
                    "state": j.state,
                    "job_id": str(j.id),
                    "idempotency_key": j.idempotency_key,
                }
                for j in jobs
            ],
        }
