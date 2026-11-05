# -*- coding: utf-8 -*-
"""V5-T073: Distributed Leasing and Concurrency in AI Research Factory.

Validates the production contract for distributed task leasing and provider concurrency:
1. SELECT ... FOR UPDATE SKIP LOCKED:
   Worker pods atomically lease queued tasks without lock contention or duplicate execution.
2. Negative abuse test:
   Two worker pods cannot lease the exact same task simultaneously.
3. TTL expiry and recovery:
   Abandoned or crashed worker leases are safely recovered and re-queued.
4. Split-brain defense:
   Stale workers with expired lease tokens are rejected from renewing or completing tasks.
5. Distributed Provider Semaphore:
   Cross-pod rate and concurrency limiting for third-party APIs (Gemini, OCR) preventing quota storms.
6. Measured overlapping tasks:
   Multi-worker execution with sweep-line mathematical verification of peak overlapping concurrency.
"""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.models import User, UserRole
from backend.research_factory_models import (
    ProviderConcurrencyConfig,
    ProviderSemaphoreLease,
    ResearchAttempt,
    ResearchJob,
    ResearchJobStatus,
    ResearchLease,
    ResearchLeaseStatus,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
    ResearchRunStatus,
)
from backend.security import hash_password
from backend.services.research_factory import (
    ConcurrencyTracker,
    DistributedProviderSemaphore,
    JobNotFoundError,
    LeaseLostError,
    SemaphoreCapacityError,
    SemaphoreTimeoutError,
    acquire_provider_slot,
    complete_job,
    lease_next_job,
    mark_job_running,
    measure_active_concurrency,
    measure_overlapping_tasks,
    recover_expired_leases,
    release_lease,
    release_provider_slot,
    renew_lease,
    renew_provider_slot,
)


# --------------------------------------------------------------------------- #
# Test Setup Helpers
# --------------------------------------------------------------------------- #
def _create_user(db_session, email: str = "lease_admin@histolab.icu") -> User:
    user = User(
        email=email,
        password_hash=hash_password("SecureAdminPassword123!"),
        display_name="Lease Admin",
        username=f"admin_{uuid.uuid4().hex[:8]}",
        role=UserRole.admin,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _setup_run_and_phase(
    db_session,
    phase_code: str = "P01",
    wave: int = 1,
) -> tuple[ResearchRun, ResearchPhase]:
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:8]}@histolab.icu")
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_cao_dinh_01"],
        status=ResearchRunStatus.RUNNING.value,
        cost_budget=50.0,
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code=phase_code,
        wave=wave,
        state=ResearchPhaseStatus.DISPATCHED.value,
        input_sha256="test_input_sha256",
    )
    db_session.add(phase)
    db_session.commit()
    return run, phase


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_job_leasing_for_update_skip_locked_basic(db_session):
    """Test basic lease acquisition using SELECT ... FOR UPDATE SKIP LOCKED."""
    run, phase = _setup_run_and_phase(db_session)

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="archival_extractor",
        idempotency_key=f"lease_basic_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
        priority=10,
        provider="gemini",
    )
    db_session.add(job)
    db_session.commit()

    worker_id = "pod-worker-01"
    leased_job = lease_next_job(
        db=db_session,
        worker_id=worker_id,
        ttl_seconds=120,
        run_id=run.id,
    )

    assert leased_job is not None
    assert leased_job.id == job.id
    assert leased_job.state == ResearchJobStatus.LEASED.value
    assert leased_job.lease_owner == worker_id
    assert leased_job.lease_token is not None
    assert leased_job.lease_until is not None
    assert leased_job.attempt == 1

    # Verify audit ledger
    active_lease = db_session.execute(
        select(ResearchLease).where(
            ResearchLease.job_id == job.id,
            ResearchLease.lease_token == leased_job.lease_token,
        )
    ).scalar_one()
    assert active_lease.worker_id == worker_id
    assert active_lease.status == ResearchLeaseStatus.ACTIVE.value

    attempt_rec = db_session.execute(
        select(ResearchAttempt).where(
            ResearchAttempt.job_id == job.id,
            ResearchAttempt.attempt_number == 1,
        )
    ).scalar_one()
    assert attempt_rec.worker_id == worker_id


def test_negative_abuse_two_worker_pods_cannot_lease_same_task(engine):
    """NEGATIVE ABUSE TEST: Two worker pods cannot lease the exact same task simultaneously.

    Simulates two separate worker pods running on distinct database connections
    attempting to acquire the same queued job at the exact same instant.
    PostgreSQL's SELECT ... FOR UPDATE SKIP LOCKED guarantees that exactly ONE
    pod wins the lease, while the competing pod skips the row and receives None.
    """
    SessionLocal = sessionmaker(bind=engine)
    init_session = SessionLocal()

    admin = _create_user(init_session, f"admin_abuse_{uuid.uuid4().hex[:8]}@histolab.icu")
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_nhan_dinh_05"],
        status=ResearchRunStatus.RUNNING.value,
        created_by=admin.id,
    )
    init_session.add(run)
    init_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code="P03",
        wave=1,
        state=ResearchPhaseStatus.DISPATCHED.value,
        input_sha256="contest_phase_input",
    )
    init_session.add(phase)
    init_session.commit()

    # Single contestable job
    job = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="critical_han_nom_transcriber",
        idempotency_key=f"contested_slot_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
        priority=100,
    )
    init_session.add(job)
    init_session.commit()
    target_job_id = job.id
    init_session.close()

    barrier = threading.Barrier(2)
    results = {}

    def worker_attempt(worker_id: str):
        worker_session = SessionLocal()
        try:
            # Synchronize both threads right before query execution
            barrier.wait(timeout=5.0)
            leased = lease_next_job(
                db=worker_session,
                worker_id=worker_id,
                ttl_seconds=300,
                job_id=target_job_id,
            )
            results[worker_id] = leased.id if leased else None
        finally:
            worker_session.close()

    t1 = threading.Thread(target=worker_attempt, args=("pod-alpha",))
    t2 = threading.Thread(target=worker_attempt, args=("pod-beta",))

    t1.start()
    t2.start()
    t1.join(timeout=10.0)
    t2.join(timeout=10.0)

    # Invariant Verification:
    # Exactly ONE worker pod acquired the job ID; the other got None
    leased_values = list(results.values())
    assert (
        leased_values.count(target_job_id) == 1
    ), f"Expected exactly 1 pod to acquire task {target_job_id}, got: {results}"
    assert (
        leased_values.count(None) == 1
    ), f"Expected exactly 1 pod to receive None, got: {results}"

    # Verify database state reflects the single winner
    verify_session = SessionLocal()
    winner_job = verify_session.execute(
        select(ResearchJob).where(ResearchJob.id == target_job_id)
    ).scalar_one()

    winning_worker = "pod-alpha" if results["pod-alpha"] == target_job_id else "pod-beta"
    assert winner_job.lease_owner == winning_worker
    assert winner_job.state == ResearchJobStatus.LEASED.value
    assert winner_job.attempt == 1

    verify_session.close()


def test_lease_renewal_and_heartbeat(db_session):
    """Test extending an active lease via renew_lease."""
    run, phase = _setup_run_and_phase(db_session)
    job = ResearchJob(
        phase_id=phase.id,
        slot_number=2,
        role_key="entity_matcher",
        idempotency_key=f"renew_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
    )
    db_session.add(job)
    db_session.commit()

    leased = lease_next_job(db_session, "pod-worker-02", ttl_seconds=60)
    initial_expiry = leased.lease_until

    # Renew lease with +180s extension
    time.sleep(0.01)
    renewed = renew_lease(
        db=db_session,
        job_id=leased.id,
        worker_id="pod-worker-02",
        lease_token=leased.lease_token,
        extension_seconds=180,
    )

    assert renewed.lease_until > initial_expiry
    assert renewed.last_heartbeat_at >= leased.last_heartbeat_at


def test_negative_stale_worker_split_brain_rejected(db_session):
    """NEGATIVE TEST: Stale worker with expired lease cannot renew or complete task.

    When Worker A's lease expires and Worker B re-leases the task with a new token,
    Worker A's subsequent completion or renewal attempts must be rejected with LeaseLostError.
    """
    run, phase = _setup_run_and_phase(db_session)
    job = ResearchJob(
        phase_id=phase.id,
        slot_number=3,
        role_key="split_brain_test",
        idempotency_key=f"split_brain_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
    )
    db_session.add(job)
    db_session.commit()

    # Worker A leases with 0-second TTL (immediately expired)
    now_past = datetime.now(timezone.utc) - timedelta(seconds=10)
    leased_a = lease_next_job(db_session, "pod-worker-A", ttl_seconds=1)
    old_token_a = leased_a.lease_token
    target_job_id = job.id

    # Force expiration in DB
    job.lease_until = now_past
    db_session.commit()

    # Worker B leases the expired task
    leased_b = lease_next_job(db_session, "pod-worker-B", ttl_seconds=300)
    assert leased_b is not None
    assert leased_b.lease_owner == "pod-worker-B"
    assert leased_b.lease_token != old_token_a
    token_b = leased_b.lease_token

    # Worker A attempts to renew -> REJECTED
    with pytest.raises(LeaseLostError):
        renew_lease(
            db=db_session,
            job_id=target_job_id,
            worker_id="pod-worker-A",
            lease_token=old_token_a,
            extension_seconds=60,
        )

    # Worker A attempts to complete -> REJECTED
    with pytest.raises(LeaseLostError):
        complete_job(
            db=db_session,
            job_id=target_job_id,
            worker_id="pod-worker-A",
            lease_token=old_token_a,
            output_sha256="abc_stale_output",
        )

    # Worker B successfully completes the task
    completed = complete_job(
        db=db_session,
        job_id=target_job_id,
        worker_id="pod-worker-B",
        lease_token=token_b,
        output_sha256="legitimate_sha256_output",
        result_envelope={"status": "SUCCEEDED", "records": 42},
    )
    assert completed.state == ResearchJobStatus.SUCCEEDED.value
    assert completed.output_sha256 == "legitimate_sha256_output"


def test_job_lifecycle_running_and_complete(db_session):
    """Test full happy-path lifecycle: QUEUED -> LEASED -> RUNNING -> SUCCEEDED."""
    run, phase = _setup_run_and_phase(db_session)
    job = ResearchJob(
        phase_id=phase.id,
        slot_number=4,
        role_key="narrative_synthesizer",
        idempotency_key=f"lifecycle_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
    )
    db_session.add(job)
    db_session.commit()

    # 1. Lease
    leased = lease_next_job(db_session, "worker-pod-4", ttl_seconds=120, job_id=job.id)
    assert leased.state == ResearchJobStatus.LEASED.value

    # 2. Mark Running
    running = mark_job_running(
        db_session,
        leased.id,
        "worker-pod-4",
        leased.lease_token,
    )
    assert running.state == ResearchJobStatus.RUNNING.value

    # 3. Complete
    completed = complete_job(
        db=db_session,
        job_id=leased.id,
        worker_id="worker-pod-4",
        lease_token=leased.lease_token,
        output_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        result_envelope={"narrative_id": "draft_01", "word_count": 850},
    )
    assert completed.state == ResearchJobStatus.SUCCEEDED.value
    assert completed.lease_owner is None
    assert completed.lease_token is None
    assert completed.completed_at is not None

    # Check lease ledger
    lease_rec = db_session.execute(
        select(ResearchLease).where(ResearchLease.job_id == leased.id).order_by(ResearchLease.granted_at.desc())
    ).scalars().first()
    assert lease_rec is not None
    assert lease_rec.status == ResearchLeaseStatus.COMPLETED.value
    assert lease_rec.released_at is not None


def test_job_release_and_retry_backoff(db_session):
    """Test job error release back into queue and terminal failure on max attempts."""
    run, phase = _setup_run_and_phase(db_session)
    job = ResearchJob(
        phase_id=phase.id,
        slot_number=5,
        role_key="ocr_processor",
        idempotency_key=f"retry_{uuid.uuid4().hex}",
        state=ResearchJobStatus.QUEUED.value,
        max_attempts=2,
    )
    db_session.add(job)
    db_session.commit()

    # First attempt: fails and releases back to queue with backoff
    leased_1 = lease_next_job(db_session, "worker-retry", ttl_seconds=60, job_id=job.id)
    assert leased_1.attempt == 1

    released = release_lease(
        db=db_session,
        job_id=leased_1.id,
        worker_id="worker-retry",
        lease_token=leased_1.lease_token,
        error_message="Network timeout to archive server",
        backoff_seconds=10,
    )
    assert released.state == ResearchJobStatus.QUEUED.value
    assert released.error_message == "Network timeout to archive server"
    assert released.lease_owner is None

    # Reset available_at to now for test
    released.available_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    # Second attempt: reaches max_attempts (2) -> FAILED
    leased_2 = lease_next_job(db_session, "worker-retry", ttl_seconds=60, job_id=job.id)
    assert leased_2.attempt == 2

    failed = release_lease(
        db=db_session,
        job_id=leased_2.id,
        worker_id="worker-retry",
        lease_token=leased_2.lease_token,
        error_message="Fatal unrecoverable format error",
    )
    assert failed.state == ResearchJobStatus.FAILED.value
    assert failed.error_message == "Fatal unrecoverable format error"


def test_recover_expired_leases_daemon(db_session):
    """Test background recovery of abandoned worker tasks."""
    run, phase = _setup_run_and_phase(db_session)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=6,
        role_key="unresponsive_task",
        idempotency_key=f"recover_{uuid.uuid4().hex}",
        state=ResearchJobStatus.RUNNING.value,
        lease_owner="crashed-pod-99",
        lease_token="crashed_token_123",
        lease_until=past_time,
        attempt=1,
        max_attempts=3,
    )
    db_session.add(job)
    db_session.commit()

    recovered_count = recover_expired_leases(db_session, grace_period_seconds=0)
    assert recovered_count >= 1

    db_session.refresh(job)
    assert job.state == ResearchJobStatus.QUEUED.value
    assert job.lease_owner is None
    assert job.lease_token is None


def test_distributed_provider_semaphore_capacity_limit(db_session):
    """Test distributed cross-pod provider semaphore with capacity enforcement."""
    provider = f"test_provider_{uuid.uuid4().hex[:6]}"
    max_cap = 2

    # Set provider config
    cfg = ProviderConcurrencyConfig(
        provider=provider,
        max_concurrency=max_cap,
        rate_limit_per_minute=60,
    )
    db_session.add(cfg)
    db_session.commit()

    # 1. Acquire permit 1
    p1 = acquire_provider_slot(
        db=db_session,
        provider=provider,
        holder_id="pod-01",
        max_concurrency=max_cap,
        ttl_seconds=60,
    )
    assert p1 is not None

    # 2. Acquire permit 2
    p2 = acquire_provider_slot(
        db=db_session,
        provider=provider,
        holder_id="pod-02",
        max_concurrency=max_cap,
        ttl_seconds=60,
    )
    assert p2 is not None

    # 3. Third acquire exceeds capacity -> returns None
    p3 = acquire_provider_slot(
        db=db_session,
        provider=provider,
        holder_id="pod-03",
        max_concurrency=max_cap,
        ttl_seconds=60,
    )
    assert p3 is None, "Should not exceed max_concurrency 2"

    # 4. Release permit 1 -> capacity freed
    released = release_provider_slot(db_session, p1.id, p1.lease_token)
    assert released is True

    # 5. Now permit 3 can be acquired
    p3_retry = acquire_provider_slot(
        db=db_session,
        provider=provider,
        holder_id="pod-03",
        max_concurrency=max_cap,
        ttl_seconds=60,
    )
    assert p3_retry is not None

    # Clean up
    release_provider_slot(db_session, p2.id, p2.lease_token)
    release_provider_slot(db_session, p3_retry.id, p3_retry.lease_token)


def test_distributed_provider_semaphore_context_manager_sync_and_async(engine):
    """Test DistributedProviderSemaphore context manager in sync and async modes."""
    SessionLocal = sessionmaker(bind=engine)
    provider = f"semaphore_ctx_{uuid.uuid4().hex[:6]}"

    # Synchronous context manager
    with DistributedProviderSemaphore(
        session_factory=SessionLocal,
        provider=provider,
        max_concurrency=2,
        ttl_seconds=30,
    ) as permit:
        assert permit is not None
        assert permit.provider == provider

    # Verify released after exit
    verify_session = SessionLocal()
    active_count = verify_session.execute(
        select(ProviderSemaphoreLease).where(
            ProviderSemaphoreLease.provider == provider
        )
    ).scalars().all()
    assert len(active_count) == 0
    verify_session.close()

    # Asynchronous context manager
    async def async_test():
        async with DistributedProviderSemaphore(
            session_factory=SessionLocal,
            provider=provider,
            max_concurrency=2,
            ttl_seconds=30,
        ) as async_permit:
            assert async_permit is not None
            assert async_permit.provider == provider

    asyncio.run(async_test())


def test_measured_overlapping_tasks_sweep_line():
    """Unit test for sweep-line algorithm measuring overlapping execution intervals.

    Simulates execution intervals of 5 tasks:
    Task 1: [1.0, 5.0]
    Task 2: [2.0, 6.0]
    Task 3: [3.0, 7.0]
    Task 4: [4.0, 8.0]
    Task 5: [10.0, 12.0]
    Interval [4.0, 5.0] has all 4 tasks (1, 2, 3, 4) overlapping simultaneously.
    """
    intervals = [
        (1.0, 5.0),
        (2.0, 6.0),
        (3.0, 7.0),
        (4.0, 8.0),
        (10.0, 12.0),
    ]
    peak = measure_overlapping_tasks(intervals)
    assert peak == 4

    tracker = ConcurrencyTracker()
    for idx, (s, e) in enumerate(intervals):
        tracker.record_task(f"task_{idx}", f"worker_{idx % 2}", s, e)

    assert tracker.get_peak_concurrency() == 4
    assert tracker.get_tasks_count() == 5
    assert tracker.get_unique_workers_count() == 2
    assert tracker.get_mean_duration_ms() > 0


def test_multi_worker_concurrent_job_execution_measured(engine):
    """END-TO-END MEASURED CONCURRENCY TEST:

    1. Seeds a full 10-slot research phase.
    2. Spawns 4 concurrent worker threads competing to lease and execute all 10 jobs.
    3. Each worker leases via lease_next_job (SELECT ... FOR UPDATE SKIP LOCKED).
    4. Tasks simulate processing (100ms) while holding the lease.
    5. Measures peak overlapping concurrency using ConcurrencyTracker.
    6. Asserts:
       - Every task executed exactly once (no duplicates).
       - Peak overlapping tasks >= 2 (measured real concurrency).
       - Database reflects 10 completed jobs, 0 queued.
    """
    SessionLocal = sessionmaker(bind=engine)
    setup_session = SessionLocal()

    admin = _create_user(setup_session, f"admin_e2e_{uuid.uuid4().hex[:8]}@histolab.icu")
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_cao_dinh_01"],
        status=ResearchRunStatus.RUNNING.value,
        created_by=admin.id,
    )
    setup_session.add(run)
    setup_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code=ResearchPhaseCode.P04.value,
        wave=1,
        state=ResearchPhaseStatus.DISPATCHED.value,
        input_sha256="multithread_phase_sha",
    )
    setup_session.add(phase)
    setup_session.commit()

    # Seed exactly 10 slots
    for slot_idx in range(1, 11):
        job = ResearchJob(
            phase_id=phase.id,
            slot_number=slot_idx,
            role_key=f"worker_slot_{slot_idx}",
            idempotency_key=f"e2e_slot_{run.id}_{slot_idx}",
            state=ResearchJobStatus.QUEUED.value,
            priority=slot_idx,
            provider="gemini",
        )
        setup_session.add(job)
    setup_session.commit()
    phase_id = phase.id
    run_id = run.id
    setup_session.close()

    tracker = ConcurrencyTracker()
    completed_jobs_list: list[str] = []
    lock = threading.Lock()

    def worker_loop(worker_name: str):
        session = SessionLocal()
        try:
            while True:
                # Atomically lease next eligible job
                job = lease_next_job(
                    db=session,
                    worker_id=worker_name,
                    ttl_seconds=60,
                    run_id=run_id,
                )
                if not job:
                    break

                job_id = job.id
                token = job.lease_token

                # Transition to RUNNING
                mark_job_running(session, job_id, worker_name, token)

                # Execute work and record concurrency interval
                start_t = time.monotonic()
                time.sleep(0.08)  # 80ms execution window
                end_t = time.monotonic()

                with lock:
                    tracker.record_task(str(job_id), worker_name, start_t, end_t)
                    completed_jobs_list.append(str(job_id))

                # Complete task
                complete_job(
                    db=session,
                    job_id=job_id,
                    worker_id=worker_name,
                    lease_token=token,
                    output_sha256=f"hash_{job_id}",
                    result_envelope={"status": "SUCCEEDED", "slot": job.slot_number},
                )
        finally:
            session.close()

    # Run 4 worker threads concurrently
    threads = [
        threading.Thread(target=worker_loop, args=(f"worker-pod-{i}",))
        for i in range(1, 5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15.0)

    # Invariants verification:
    # 1. All 10 jobs completed
    assert len(completed_jobs_list) == 10
    assert len(set(completed_jobs_list)) == 10, "Duplicate task execution detected!"

    # 2. Measured peak concurrency >= 2
    peak_concurrency = tracker.get_peak_concurrency()
    assert (
        peak_concurrency >= 2
    ), f"Expected overlapping concurrency >= 2, got {peak_concurrency}"

    # 3. Database metrics reflection
    inspect_session = SessionLocal()
    metrics = measure_active_concurrency(inspect_session, run_id=run_id)
    assert metrics["completed_jobs_count"] == 10
    assert metrics["queued_jobs_count"] == 0
    assert metrics["active_leases_count"] == 0

    inspect_session.close()
