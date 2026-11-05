# -*- coding: utf-8 -*-
"""Distributed job leasing for AI Research Factory — V5 Wave W07.

Spec reference: V4.3.2 / V3.C3 / AIR-041–045.
Guarantees:
- Exactly-once active lease per slot using PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED`.
- Atomic TTL updates and heartbeats.
- Recovery of abandoned or crashed worker tasks.
- Cryptographic lease tokens preventing split-brain completions by expired workers.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from backend.research_factory_models import (
    ResearchAttempt,
    ResearchJob,
    ResearchJobStatus,
    ResearchLease,
    ResearchLeaseStatus,
    ResearchPhase,
)


class ResearchLeaseError(Exception):
    """Base exception for research leasing errors."""


class LeaseLostError(ResearchLeaseError):
    """Raised when an operation attempts to mutate a job whose lease was lost or expired."""


class JobNotFoundError(ResearchLeaseError):
    """Raised when the requested job does not exist."""


class MaxAttemptsExceededError(ResearchLeaseError):
    """Raised when job retry attempts exceed max_attempts."""


def lease_next_job(
    db: Session,
    worker_id: str,
    ttl_seconds: int = 300,
    phase_code: str | None = None,
    provider: str | None = None,
    run_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
) -> ResearchJob | None:
    """Atomically lease the next eligible queued or expired research job.

    Uses `SELECT ... FOR UPDATE SKIP LOCKED` inside a short database transaction.
    Commits immediately upon updating lease metadata so row locks are never held
    across network calls or LLM inferences.

    Eligible jobs:
    1) State is QUEUED and available_at <= now
    2) State is LEASED or RUNNING, but lease_until <= now (crashed worker recovery)
       and attempt < max_attempts
    """
    now_utc = datetime.now(timezone.utc)

    # Base query for eligible candidate
    query = select(ResearchJob)

    if phase_code is not None or run_id is not None:
        phase_subq = select(ResearchPhase.id)
        if phase_code is not None:
            phase_subq = phase_subq.where(ResearchPhase.phase_code == phase_code)
        if run_id is not None:
            phase_subq = phase_subq.where(ResearchPhase.run_id == run_id)
        query = query.where(ResearchJob.phase_id.in_(phase_subq))

    if provider is not None:
        query = query.where(ResearchJob.provider == provider)

    if job_id is not None:
        query = query.where(ResearchJob.id == job_id)

    # Eligible: either queued and available, or expired lease eligible for retry
    eligibility_cond = or_(
        and_(
            ResearchJob.state == ResearchJobStatus.QUEUED.value,
            ResearchJob.available_at <= now_utc,
        ),
        and_(
            ResearchJob.state.in_(
                [ResearchJobStatus.LEASED.value, ResearchJobStatus.RUNNING.value]
            ),
            ResearchJob.lease_until <= now_utc,
            ResearchJob.attempt < ResearchJob.max_attempts,
        ),
    )
    query = query.where(eligibility_cond)

    # Priority ordering: highest priority first, then oldest creation
    query = (
        query.order_by(ResearchJob.priority.desc(), ResearchJob.created_at.asc())
        .with_for_update(of=ResearchJob, skip_locked=True)
        .limit(1)
    )

    job = db.execute(query).scalars().first()
    if not job:
        db.commit()
        return None

    # Acquired row lock on candidate job. Atomically assign lease
    new_token = uuid.uuid4().hex
    expiry = now_utc + timedelta(seconds=ttl_seconds)

    # If previous lease was expired, mark old active lease as EXPIRED
    if job.lease_token:
        stale_leases = (
            db.execute(
                select(ResearchLease).where(
                    ResearchLease.job_id == job.id,
                    ResearchLease.status == ResearchLeaseStatus.ACTIVE.value,
                )
            )
            .scalars()
            .all()
        )
        for sl in stale_leases:
            sl.status = ResearchLeaseStatus.EXPIRED.value
            sl.released_at = now_utc

    job.state = ResearchJobStatus.LEASED.value
    job.lease_owner = worker_id
    job.lease_token = new_token
    job.lease_until = expiry
    job.last_heartbeat_at = now_utc
    job.attempt += 1

    # Record lease grant in historical audit table
    lease_record = ResearchLease(
        job_id=job.id,
        worker_id=worker_id,
        lease_token=new_token,
        status=ResearchLeaseStatus.ACTIVE.value,
        granted_at=now_utc,
        expires_at=expiry,
    )
    db.add(lease_record)

    # Record attempt
    attempt_record = ResearchAttempt(
        job_id=job.id,
        attempt_number=job.attempt,
        worker_id=worker_id,
        started_at=now_utc,
        status=ResearchJobStatus.LEASED.value,
    )
    db.add(attempt_record)

    db.commit()
    db.refresh(job)
    return job


def renew_lease(
    db: Session,
    job_id: uuid.UUID,
    worker_id: str,
    lease_token: str,
    extension_seconds: int = 300,
) -> ResearchJob:
    """Atomically extend an active lease TTL.

    Raises `LeaseLostError` if the lease was lost, expired, or reassigned.
    """
    now_utc = datetime.now(timezone.utc)

    query = (
        select(ResearchJob)
        .where(ResearchJob.id == job_id)
        .with_for_update()
    )
    job = db.execute(query).scalars().first()

    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if (
        job.lease_owner != worker_id
        or job.lease_token != lease_token
        or job.state not in [ResearchJobStatus.LEASED.value, ResearchJobStatus.RUNNING.value]
    ):
        raise LeaseLostError(
            f"Cannot renew lease: Job {job_id} is no longer leased to worker '{worker_id}' with given token."
        )

    # Verify not already past expiration by more than grace period
    if job.lease_until and job.lease_until < now_utc:
        raise LeaseLostError(
            f"Cannot renew lease: Lease for job {job_id} has already expired at {job.lease_until}."
        )

    new_expiry = now_utc + timedelta(seconds=extension_seconds)
    job.lease_until = new_expiry
    job.last_heartbeat_at = now_utc

    # Update active lease record
    active_lease = (
        db.execute(
            select(ResearchLease).where(
                ResearchLease.job_id == job.id,
                ResearchLease.lease_token == lease_token,
                ResearchLease.status == ResearchLeaseStatus.ACTIVE.value,
            )
        )
        .scalars()
        .first()
    )
    if active_lease:
        active_lease.expires_at = new_expiry

    db.commit()
    db.refresh(job)
    return job


def mark_job_running(
    db: Session,
    job_id: uuid.UUID,
    worker_id: str,
    lease_token: str,
) -> ResearchJob:
    """Transitions a leased job to RUNNING state."""
    now_utc = datetime.now(timezone.utc)

    query = select(ResearchJob).where(ResearchJob.id == job_id).with_for_update()
    job = db.execute(query).scalars().first()

    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if job.lease_owner != worker_id or job.lease_token != lease_token:
        raise LeaseLostError(f"Worker {worker_id} does not own active lease on job {job_id}")

    job.state = ResearchJobStatus.RUNNING.value
    job.last_heartbeat_at = now_utc

    db.commit()
    db.refresh(job)
    return job


def complete_job(
    db: Session,
    job_id: uuid.UUID,
    worker_id: str,
    lease_token: str,
    output_sha256: str,
    result_envelope: dict[str, Any] | None = None,
    status: ResearchJobStatus = ResearchJobStatus.SUCCEEDED,
) -> ResearchJob:
    """Atomically marks a job as complete (SUCCEEDED or NO_EVIDENCE).

    Rejects stale workers whose lease has expired and been revoked.
    """
    now_utc = datetime.now(timezone.utc)

    query = select(ResearchJob).where(ResearchJob.id == job_id).with_for_update()
    job = db.execute(query).scalars().first()

    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if job.lease_owner != worker_id or job.lease_token != lease_token:
        raise LeaseLostError(
            f"Stale completion rejected: Worker {worker_id} does not hold active lease on job {job_id}"
        )

    job.state = status.value
    job.output_sha256 = output_sha256
    job.result_envelope = result_envelope or {}
    job.completed_at = now_utc
    job.lease_owner = None
    job.lease_token = None
    job.lease_until = None

    # Close active lease
    active_lease = (
        db.execute(
            select(ResearchLease).where(
                ResearchLease.job_id == job.id,
                ResearchLease.lease_token == lease_token,
                ResearchLease.status == ResearchLeaseStatus.ACTIVE.value,
            )
        )
        .scalars()
        .first()
    )
    if active_lease:
        active_lease.status = ResearchLeaseStatus.COMPLETED.value
        active_lease.released_at = now_utc

    # Update attempt record
    latest_attempt = (
        db.execute(
            select(ResearchAttempt)
            .where(
                ResearchAttempt.job_id == job.id,
                ResearchAttempt.worker_id == worker_id,
            )
            .order_by(ResearchAttempt.attempt_number.desc())
        )
        .scalars()
        .first()
    )
    if latest_attempt:
        latest_attempt.status = status.value
        latest_attempt.ended_at = now_utc

    db.commit()
    db.refresh(job)
    return job


def release_lease(
    db: Session,
    job_id: uuid.UUID,
    worker_id: str,
    lease_token: str,
    error_message: str | None = None,
    backoff_seconds: int = 0,
) -> ResearchJob:
    """Release a lease back to the queue or mark as FAILED if max attempts exceeded."""
    now_utc = datetime.now(timezone.utc)

    query = select(ResearchJob).where(ResearchJob.id == job_id).with_for_update()
    job = db.execute(query).scalars().first()

    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if job.lease_owner != worker_id or job.lease_token != lease_token:
        raise LeaseLostError(
            f"Cannot release lease: Worker {worker_id} does not hold active lease on job {job_id}"
        )

    if job.attempt >= job.max_attempts:
        job.state = ResearchJobStatus.FAILED.value
        job.error_message = error_message or "Max retry attempts exceeded"
    else:
        job.state = ResearchJobStatus.QUEUED.value
        job.available_at = now_utc + timedelta(seconds=backoff_seconds)
        if error_message:
            job.error_message = error_message

    job.lease_owner = None
    job.lease_token = None
    job.lease_until = None

    # Close lease
    active_lease = (
        db.execute(
            select(ResearchLease).where(
                ResearchLease.job_id == job.id,
                ResearchLease.lease_token == lease_token,
                ResearchLease.status == ResearchLeaseStatus.ACTIVE.value,
            )
        )
        .scalars()
        .first()
    )
    if active_lease:
        active_lease.status = ResearchLeaseStatus.RELEASED.value
        active_lease.released_at = now_utc

    # Update attempt
    latest_attempt = (
        db.execute(
            select(ResearchAttempt)
            .where(
                ResearchAttempt.job_id == job.id,
                ResearchAttempt.worker_id == worker_id,
            )
            .order_by(ResearchAttempt.attempt_number.desc())
        )
        .scalars()
        .first()
    )
    if latest_attempt:
        latest_attempt.status = (
            ResearchJobStatus.FAILED.value
            if job.attempt >= job.max_attempts
            else ResearchJobStatus.QUEUED.value
        )
        latest_attempt.ended_at = now_utc
        latest_attempt.error_message = error_message

    db.commit()
    db.refresh(job)
    return job


def recover_expired_leases(db: Session, grace_period_seconds: int = 0) -> int:
    """Find and recover tasks whose worker pods crashed or abandoned them.

    Returns the number of recovered jobs.
    """
    now_utc = datetime.now(timezone.utc)
    threshold = now_utc - timedelta(seconds=grace_period_seconds)

    query = (
        select(ResearchJob)
        .where(
            ResearchJob.state.in_(
                [ResearchJobStatus.LEASED.value, ResearchJobStatus.RUNNING.value]
            ),
            ResearchJob.lease_until < threshold,
        )
        .with_for_update(skip_locked=True)
    )

    expired_jobs = db.execute(query).scalars().all()
    count = 0

    for job in expired_jobs:
        # Close associated active lease
        active_leases = (
            db.execute(
                select(ResearchLease).where(
                    ResearchLease.job_id == job.id,
                    ResearchLease.status == ResearchLeaseStatus.ACTIVE.value,
                )
            )
            .scalars()
            .all()
        )
        for al in active_leases:
            al.status = ResearchLeaseStatus.EXPIRED.value
            al.released_at = now_utc

        if job.attempt >= job.max_attempts:
            job.state = ResearchJobStatus.FAILED.value
            job.error_message = "Lease expired and max retry attempts exceeded"
        else:
            job.state = ResearchJobStatus.QUEUED.value
            job.available_at = now_utc

        job.lease_owner = None
        job.lease_token = None
        job.lease_until = None
        count += 1

    db.commit()
    return count
