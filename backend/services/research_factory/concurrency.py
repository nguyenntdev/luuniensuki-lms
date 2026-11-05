# -*- coding: utf-8 -*-
"""Concurrency measurement and orchestration for AI Research Factory — V5 Wave W07.

Spec reference: V4.3.2 / V3.C3 / W07-A03.
Provides:
- Exact sweep-line measurement of overlapping parallel tasks.
- Real-time database metrics on active leases, queue depth, and provider usage.
- Multi-worker concurrency verification utilities.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.research_factory_models import (
    ProviderSemaphoreLease,
    ResearchJob,
    ResearchJobStatus,
    ResearchPhase,
)


@dataclass
class TaskExecutionRecord:
    task_id: str
    worker_id: str
    start_time: float
    end_time: float

    @property
    def duration_ms(self) -> float:
        return max(0.0, (self.end_time - self.start_time) * 1000.0)


def measure_overlapping_tasks(intervals: list[tuple[float, float]]) -> int:
    """Calculates peak overlapping concurrency using the sweep-line algorithm.

    Each interval `(start, end)` produces two discrete events:
    - `(start, +1)`
    - `(end, -1)`
    Events are sorted chronologically. In case of exact timestamp ties,
    decrements (-1) take precedence so point-boundaries are not double-counted.
    """
    if not intervals:
        return 0

    events: list[tuple[float, int]] = []
    for start, end in intervals:
        if end >= start:
            events.append((start, 1))
            events.append((end, -1))

    # Sort primarily by timestamp ascending; secondary by delta ascending (-1 before +1)
    events.sort(key=lambda x: (x[0], x[1]))

    peak = 0
    current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current

    return peak


class ConcurrencyMeasurementError(Exception):
    """Raised when concurrency invariant is violated or unmeasured."""
    pass


def validate_concurrency_invariant(observed_peak: int, expected: int = 10) -> bool:
    """Enforces that 10-concurrent label is strictly allowed ONLY when measured observed_peak >= expected.

    Negative abuse invariant (V5-T080):
    Observed_peak exact; 10 concurrent label only when measured.
    If observed_peak < expected, raises ConcurrencyMeasurementError.
    """
    if observed_peak < expected:
        raise ConcurrencyMeasurementError(
            f"Observed peak concurrency is {observed_peak}, which is below required {expected}. "
            f"Cannot claim or label as {expected} concurrent without actual measurement."
        )
    return True


def label_concurrency_level(observed_peak: int) -> str:
    """Returns verified concurrency label based strictly on measured observed_peak."""
    if observed_peak >= 10:
        return "10_CONCURRENT_VERIFIED"
    elif observed_peak >= 5:
        return f"PARTIAL_CONCURRENCY_{observed_peak}"
    else:
        return f"LOW_CONCURRENCY_{observed_peak}"


class ConcurrencyTracker:
    """Thread-safe recorder for multi-worker parallel execution metrics."""

    def __init__(self) -> None:
        self._records: list[TaskExecutionRecord] = []

    def record_task(
        self,
        task_id: str,
        worker_id: str,
        start_time: float,
        end_time: float,
    ) -> None:
        """Record the start and completion monotonic timestamp of an executed task."""
        self._records.append(
            TaskExecutionRecord(
                task_id=task_id,
                worker_id=worker_id,
                start_time=start_time,
                end_time=end_time,
            )
        )

    def get_peak_concurrency(self) -> int:
        """Returns the maximum observed number of simultaneously overlapping tasks."""
        intervals = [(r.start_time, r.end_time) for r in self._records]
        return measure_overlapping_tasks(intervals)

    def get_mean_duration_ms(self) -> float:
        """Returns the mean duration of recorded executions in milliseconds."""
        if not self._records:
            return 0.0
        total_ms = sum(r.duration_ms for r in self._records)
        return total_ms / len(self._records)

    def get_unique_workers_count(self) -> int:
        """Returns the number of unique worker identifiers participating in the run."""
        return len({r.worker_id for r in self._records})

    def get_tasks_count(self) -> int:
        """Total number of tasks recorded."""
        return len(self._records)

    def clear(self) -> None:
        """Clear recorded executions."""
        self._records.clear()


def measure_active_concurrency(
    db: Session,
    run_id: uuid.UUID | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Inspect current database concurrency, queue depth and semaphore usage."""
    now_utc = datetime.now(timezone.utc)

    # 1. Active leases
    lease_query = select(func.count(ResearchJob.id)).where(
        ResearchJob.state.in_(
            [ResearchJobStatus.LEASED.value, ResearchJobStatus.RUNNING.value]
        ),
        ResearchJob.lease_until > now_utc,
    )
    if run_id:
        lease_query = lease_query.join(
            ResearchPhase, ResearchJob.phase_id == ResearchPhase.id
        ).where(ResearchPhase.run_id == run_id)
    if provider:
        lease_query = lease_query.where(ResearchJob.provider == provider)

    active_leases_count = db.execute(lease_query).scalar() or 0

    # 2. Queued tasks
    queue_query = select(func.count(ResearchJob.id)).where(
        ResearchJob.state == ResearchJobStatus.QUEUED.value
    )
    if run_id:
        queue_query = queue_query.join(
            ResearchPhase, ResearchJob.phase_id == ResearchPhase.id
        ).where(ResearchPhase.run_id == run_id)
    if provider:
        queue_query = queue_query.where(ResearchJob.provider == provider)

    queued_count = db.execute(queue_query).scalar() or 0

    # 3. Completed tasks
    completed_query = select(func.count(ResearchJob.id)).where(
        ResearchJob.state == ResearchJobStatus.SUCCEEDED.value
    )
    if run_id:
        completed_query = completed_query.join(
            ResearchPhase, ResearchJob.phase_id == ResearchPhase.id
        ).where(ResearchPhase.run_id == run_id)
    if provider:
        completed_query = completed_query.where(ResearchJob.provider == provider)

    completed_count = db.execute(completed_query).scalar() or 0

    # 4. Failed tasks
    failed_query = select(func.count(ResearchJob.id)).where(
        ResearchJob.state == ResearchJobStatus.FAILED.value
    )
    if run_id:
        failed_query = failed_query.join(
            ResearchPhase, ResearchJob.phase_id == ResearchPhase.id
        ).where(ResearchPhase.run_id == run_id)
    if provider:
        failed_query = failed_query.where(ResearchJob.provider == provider)

    failed_count = db.execute(failed_query).scalar() or 0

    # 5. Active provider semaphore allocations
    semaphore_query = select(
        func.coalesce(func.sum(ProviderSemaphoreLease.weight), 0)
    ).where(ProviderSemaphoreLease.expires_at > now_utc)
    if provider:
        semaphore_query = semaphore_query.where(
            ProviderSemaphoreLease.provider == provider
        )

    active_semaphore_permits = db.execute(semaphore_query).scalar() or 0

    return {
        "active_leases_count": active_leases_count,
        "queued_jobs_count": queued_count,
        "completed_jobs_count": completed_count,
        "failed_jobs_count": failed_count,
        "active_semaphore_permits": active_semaphore_permits,
        "timestamp_utc": now_utc.isoformat(),
    }
