# -*- coding: utf-8 -*-
"""V5-T126: AI 10-Subagent Concurrency Measured Test Suite.

Wave W12, Slot A06 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Canonical Registry:
   - 12 phases (P00..P11) x 10 unique agent slots = 120 unique agent slots.
   - Distinct role codes, names, default providers, and estimated token counts.
2. Token Cost & Budget Calculation:
   - Cumulative token cost computation across all 120 subagent slots.
   - Provider breakdown (Gemini, OCR) using standard rate models.
3. Cryptographic Trace Logs & Provenance:
   - Detailed execution traces citing worker ID, slot, role code, job ID,
     cryptographic lease token, timestamps, duration, tokens, and cost.
4. True 10-Subagent Concurrency Overlap (Live PostgreSQL):
   - Multi-threaded execution barrier coordinates exactly 10 workers leasing distinct slots.
   - Sweep-line interval analysis measures observed peak concurrency >= 10.
5. End-to-End 12-Phase Concurrency Audit:
   - Executes / audits all 12 phases P00 to P11 with 10 slots each.
   - Verifies all 12 phases achieve observed peak >= 10.
   - Confirms total of 120 completed jobs and accurate cumulative spend.
6. Negative Abuse Invariant:
   - Concurrency of 10 is claimed ONLY when measured with >= 10 overlapping leases via sweep-line analysis.
   - Serial execution (peak=1), sub-10 peak (e.g., 9), or disjoint tasks strictly fail with ConcurrencyMeasurementError.
7. Database Persistence & Restart Resilience:
   - ResearchRun, ResearchPhase, and ResearchJob records persist across session close and restart.
"""
from __future__ import annotations

import hashlib
import threading
import time
import uuid
from typing import Any, List

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.models import User, UserRole
from backend.research_factory_models import (
    ResearchJob,
    ResearchJobStatus,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
    ResearchRunStatus,
)
from backend.security import hash_password
from backend.services.research_factory import (
    DEFAULT_PROVIDER_PRICING,
    ConcurrencyMeasurementError,
    ConcurrencyTracker,
    MultiPhaseAuditReport,
    PhaseConcurrencySummary,
    ResearchFactoryConcurrencyAuditor,
    RoleIncompleteError,
    SubagentExecutionTrace,
    TokenCostCalculator,
    WaveDispatcher,
    assert_strictly_10_concurrent,
    complete_job,
    get_roles_for_phase,
    label_concurrency_level,
    lease_next_job,
    mark_job_running,
    measure_overlapping_tasks,
    validate_concurrency_invariant,
)


# --------------------------------------------------------------------------- #
# Helpers & Setup
# --------------------------------------------------------------------------- #
def _create_admin_user(db_session: Session) -> User:
    admin = User(
        email=f"concurrency_admin_{uuid.uuid4().hex[:6]}@histolab.icu",
        password_hash=hash_password("SuperSecretPassword123!"),
        display_name="Concurrency Admin",
        username=f"admin_{uuid.uuid4().hex[:8]}",
        role=UserRole.admin,
        is_profile_public=True,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


def _setup_research_run(
    db_session: Session,
    mode: str = "STRICT_PRODUCTION",
) -> ResearchRun:
    admin = _create_admin_user(db_session)
    run = ResearchRun(
        mode=mode,
        content_scope="NINE_URNS",
        subject_type="RELIEF",
        subject_id="urn_cao_dinh_01",
        subject_ids=["urn_cao_dinh_01", "urn_cao_dinh_02"],
        status=ResearchRunStatus.RUNNING.value,
        cost_budget=100.0,
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()
    return run


# --------------------------------------------------------------------------- #
# 1. Verification of 12 Phases x 10 Slots = 120 Roles
# --------------------------------------------------------------------------- #
def test_verify_12_phases_x_10_unique_agent_slots():
    """Requirement: Verify 12 phases x 10 unique agent slots = 120 unique agent slots."""
    report = ResearchFactoryConcurrencyAuditor.verify_registry_12x10_slots()
    assert report["verified"] is True
    assert report["total_phases"] == 12
    assert report["roles_per_phase"] == 10
    assert report["total_agent_slots"] == 120
    assert report["unique_role_codes_count"] == 120
    assert report["total_estimated_tokens"] == 618000

    expected_phases = [f"P{i:02d}" for i in range(12)]
    assert sorted(list(report["phase_details"].keys())) == expected_phases

    for phase_code in expected_phases:
        roles = get_roles_for_phase(phase_code)
        assert len(roles) == 10
        assert [r.slot for r in roles] == list(range(1, 11))
        assert len({r.code for r in roles}) == 10
        assert all(r.code.startswith(f"{phase_code}-A") for r in roles)
        assert all(r.estimated_tokens > 0 for r in roles)


# --------------------------------------------------------------------------- #
# 2. Token Cost & Budget Calculation
# --------------------------------------------------------------------------- #
def test_compute_token_cost_and_provider_breakdown():
    """Requirement: Compute token cost across subagent slots and providers."""
    budget = TokenCostCalculator.calculate_factory_12_phase_budget()
    assert budget["total_phases"] == 12
    assert budget["total_agent_slots"] == 120
    assert budget["cumulative_estimated_tokens"] == 618000
    assert budget["cumulative_cost_usd"] > 0.0

    # Provider breakdown verification
    prov_totals = budget["provider_totals"]
    assert "gemini" in prov_totals
    assert "ocr" in prov_totals
    assert prov_totals["gemini"]["slots"] == 114
    assert prov_totals["ocr"]["slots"] == 6  # P03 has 6 OCR slots
    assert prov_totals["gemini"]["tokens"] + prov_totals["ocr"]["tokens"] == 618000

    # Cost calculations
    # Gemini standard blended rate: $0.15 per 1M tokens
    gemini_tokens = prov_totals["gemini"]["tokens"]
    expected_gemini_cost = round((gemini_tokens / 1_000_000.0) * 0.15, 6)
    assert prov_totals["gemini"]["cost_usd"] == expected_gemini_cost

    # OCR rate: $1.50 per 1M tokens
    ocr_tokens = prov_totals["ocr"]["tokens"]
    expected_ocr_cost = round((ocr_tokens / 1_000_000.0) * 1.50, 6)
    assert prov_totals["ocr"]["cost_usd"] == expected_ocr_cost

    total_cost = round(expected_gemini_cost + expected_ocr_cost, 6)
    assert budget["cumulative_cost_usd"] == total_cost


# --------------------------------------------------------------------------- #
# 3. Negative Abuse: Concurrency 10 Claimed ONLY When Measured >= 10 Overlaps
# --------------------------------------------------------------------------- #
def test_negative_abuse_strict_10_concurrency_enforcement():
    """Requirement: Negative abuse - Concurrency of 10 is claimed ONLY when measured with >= 10 overlapping leases via sweep-line analysis."""
    # 1. Exact >= 10 passes
    assert assert_strictly_10_concurrent(10) is True
    assert assert_strictly_10_concurrent(15) is True
    assert validate_concurrency_invariant(10, expected=10) is True
    assert label_concurrency_level(10) == "10_CONCURRENT_VERIFIED"

    # 2. Peak of 9 is rejected
    with pytest.raises(ConcurrencyMeasurementError) as exc_info:
        assert_strictly_10_concurrent(9)
    assert "Negative abuse violation" in str(exc_info.value)
    assert "measured peak is 9" in str(exc_info.value)

    # 3. Serial execution (peak=1) is rejected
    with pytest.raises(ConcurrencyMeasurementError) as exc_info:
        assert_strictly_10_concurrent(1)
    assert "measured peak is 1" in str(exc_info.value)

    # 4. Sweep-line simulation with only 8 overlapping intervals raises error
    staggered_8 = [(1.0 + i * 0.1, 2.0) for i in range(8)]
    assert measure_overlapping_tasks(staggered_8) == 8
    with pytest.raises(ConcurrencyMeasurementError):
        ResearchFactoryConcurrencyAuditor.simulate_or_audit_phase(
            phase_code="P01",
            intervals=staggered_8,
            strict_10_check=True,
        )

    # 5. Serial intervals (zero overlap) produce peak=1 and fail strict check
    serial_intervals = [(float(i), float(i + 1)) for i in range(10)]
    assert measure_overlapping_tasks(serial_intervals) == 1
    with pytest.raises(ConcurrencyMeasurementError):
        ResearchFactoryConcurrencyAuditor.simulate_or_audit_phase(
            phase_code="P00",
            intervals=serial_intervals,
            strict_10_check=True,
        )


# --------------------------------------------------------------------------- #
# 4. Live PostgreSQL: True 10-Subagent Concurrency with Trace Logs & Provenance
# --------------------------------------------------------------------------- #
def test_live_postgres_phase_10_worker_concurrency_and_trace_provenance(db_session):
    """Executes a real 10-slot wave in PostgreSQL with 10 concurrent worker threads.

    Validates:
    - 10 distinct slots leased and completed.
    - Synchronized execution barrier guarantees simultaneous overlap.
    - Sweep-line measures observed_peak >= 10.
    - Cryptographic trace logs with worker ID, job ID, lease token, timestamps, and cost.
    """
    bind = db_session.get_bind()
    db_url = bind.engine.url if hasattr(bind, "engine") else bind.url
    worker_engine = create_engine(db_url, pool_size=15, max_overflow=5, pool_pre_ping=True)
    WorkerSession = sessionmaker(bind=worker_engine)

    setup_session = WorkerSession()
    run = _setup_research_run(setup_session)
    run_id = run.id
    setup_session.close()

    # Measure concurrency for P03 (which exercises both Gemini and OCR subagents)
    summary = ResearchFactoryConcurrencyAuditor.run_phase_concurrency_measurement(
        db_session_factory=WorkerSession,
        run_id=run_id,
        phase_code="P03",
        wave=1,
        hold_duration_ms=40.0,
        strict_10_check=True,
    )

    # Invariants verification:
    assert summary.phase_code == "P03"
    assert summary.wave == 1
    assert summary.total_slots == 10
    assert summary.is_verified_10_concurrent is True
    assert summary.concurrency_label == "10_CONCURRENT_VERIFIED"
    assert summary.observed_peak >= 10, f"Expected observed peak >= 10, got {summary.observed_peak}"
    assert summary.total_tokens == 55000
    assert summary.total_cost_usd > 0.0

    # Trace logs citation verification
    assert len(summary.trace_logs) == 10
    slots_seen = set()
    worker_ids = set()
    tokens_seen = set()

    for trace in summary.trace_logs:
        assert trace["phase_code"] == "P03"
        assert trace["status"] == "SUCCEEDED"
        assert trace["duration_ms"] >= 30.0
        assert trace["cost_usd"] > 0.0
        assert len(trace["lease_token"]) > 0
        assert trace["role_code"].startswith("P03-A")
        slots_seen.add(trace["slot_number"])
        worker_ids.add(trace["worker_id"])
        tokens_seen.add(trace["lease_token"])

    # All 10 distinct slots and 10 distinct workers
    assert slots_seen == set(range(1, 11))
    assert len(worker_ids) == 10
    assert len(tokens_seen) == 10

    # Provider breakdown includes OCR and Gemini
    assert "ocr" in summary.provider_breakdown
    assert "gemini" in summary.provider_breakdown
    assert summary.provider_breakdown["ocr"]["slots"] == 6
    assert summary.provider_breakdown["gemini"]["slots"] == 4

    worker_engine.dispose()


# --------------------------------------------------------------------------- #
# 5. Live PostgreSQL: Audit All 12 Phases x 10 Slots (120 Slots Total)
# --------------------------------------------------------------------------- #
def test_live_postgres_all_12_phases_concurrency_audit(db_session):
    """Executes all 12 phases P00 to P11 in PostgreSQL, measuring 10-subagent concurrency per phase.

    Validates:
    - 12 phases dispatched and executed sequentially.
    - Each phase runs 10 concurrent worker threads with synchronization barrier.
    - Sweep-line measures observed_peak >= 10 for every single phase.
    - Total of 120 completed agent jobs.
    - Full cumulative token cost computed.
    """
    bind = db_session.get_bind()
    db_url = bind.engine.url if hasattr(bind, "engine") else bind.url
    worker_engine = create_engine(db_url, pool_size=15, max_overflow=5, pool_pre_ping=True)
    WorkerSession = sessionmaker(bind=worker_engine)

    setup_session = WorkerSession()
    run = _setup_research_run(setup_session)
    run_id = run.id
    setup_session.close()

    # Audit all 12 phases
    audit_report = ResearchFactoryConcurrencyAuditor.audit_all_12_phases(
        db_session_factory=WorkerSession,
        run_id=run_id,
        hold_duration_ms=15.0,  # Fast holding duration for test throughput
    )

    # Invariants verification:
    assert isinstance(audit_report, MultiPhaseAuditReport)
    assert audit_report.total_phases == 12
    assert audit_report.total_slots == 120
    assert audit_report.all_phases_verified_10_concurrent is True
    assert len(audit_report.phase_results) == 12

    # Verify per-phase peaks
    for phase_code, peak in audit_report.observed_peaks.items():
        assert peak >= 10, f"Phase {phase_code} failed concurrency threshold: peak={peak}"

    # Verify token cost and budget
    assert audit_report.total_tokens == 618000
    assert audit_report.total_cost_usd > 0.0

    # Verify database persistence: 12 phases, 120 jobs with SUCCEEDED status
    verify_session = WorkerSession()
    phases_count = verify_session.execute(
        select(func.count(ResearchPhase.id)).where(ResearchPhase.run_id == run_id)
    ).scalar()
    assert phases_count == 12

    jobs_count = verify_session.execute(
        select(func.count(ResearchJob.id))
        .join(ResearchPhase, ResearchJob.phase_id == ResearchPhase.id)
        .where(
            ResearchPhase.run_id == run_id,
            ResearchJob.state == ResearchJobStatus.SUCCEEDED.value,
        )
    ).scalar()
    assert jobs_count == 120

    verify_session.close()
    worker_engine.dispose()


# --------------------------------------------------------------------------- #
# 6. Database Persistence & Restart Resilience
# --------------------------------------------------------------------------- #
def test_persistence_across_session_restart(db_session):
    """Verifies that research runs, phases, jobs, trace tokens, and results persist across session restart."""
    bind = db_session.get_bind()
    db_url = bind.engine.url if hasattr(bind, "engine") else bind.url
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionMaker = sessionmaker(bind=engine)

    # Session 1: Create run, phase, and execute wave
    s1 = SessionMaker()
    run = _setup_research_run(s1)
    run_id = run.id

    summary = ResearchFactoryConcurrencyAuditor.run_phase_concurrency_measurement(
        db_session_factory=SessionMaker,
        run_id=run_id,
        phase_code="P06",
        wave=1,
        hold_duration_ms=20.0,
        strict_10_check=True,
    )
    assert summary.observed_peak >= 10
    s1.close()

    # Session 2: Fresh session simulating restart
    s2 = SessionMaker()
    reloaded_run = s2.get(ResearchRun, run_id)
    assert reloaded_run is not None
    assert reloaded_run.status == ResearchRunStatus.RUNNING.value

    reloaded_phases = s2.scalars(
        select(ResearchPhase).where(ResearchPhase.run_id == run_id)
    ).all()
    assert len(reloaded_phases) == 1
    p06_phase = reloaded_phases[0]
    assert p06_phase.phase_code == "P06"

    reloaded_jobs = s2.scalars(
        select(ResearchJob).where(ResearchJob.phase_id == p06_phase.id)
    ).all()
    assert len(reloaded_jobs) == 10
    assert all(j.state == ResearchJobStatus.SUCCEEDED.value for j in reloaded_jobs)
    assert all(j.output_sha256 is not None for j in reloaded_jobs)
    assert all(j.result_envelope is not None for j in reloaded_jobs)

    s2.close()
    engine.dispose()
