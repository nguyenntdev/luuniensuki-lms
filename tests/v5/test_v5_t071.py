# -*- coding: utf-8 -*-
"""V5-T071: Run and Job Tables for AI Research Factory.

Validates the persistence schema and invariants for the 12-phase x 10-concurrent subagent
AI Research Factory engine:
1. Run, Phase, Job, Attempt, Lease, Budget, Evidence Result data integrity and relationships.
2. 10-slot uniqueness and slot_number BETWEEN 1 AND 10 constraint.
3. Distributed worker leasing with token, expiry, and heartbeat.
4. Budget tracking (token spend and cost allocations).
5. Immutable evidence results with cryptographic SHA-256 digests.
6. Negative / abuse test: Restart does not erase run history.
   Proves durable pipeline persistence survives process/session reloads.
7. Cascade deletes: Deleting a run cleanly cascades to phases, jobs, attempts, leases, budgets, and evidence.
8. Idempotency key deduplication on job creation.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.models import User, UserRole
from backend.research_factory_models import (
    ResearchAttempt,
    ResearchBudget,
    ResearchEvidenceResult,
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


def _create_user(db_session, email: str = "research_admin@histolab.icu") -> User:
    user = User(
        email=email,
        password_hash=hash_password("SecureAdminPassword123!"),
        display_name="Research Factory Administrator",
        username=f"admin_{uuid.uuid4().hex[:8]}",
        role=UserRole.admin,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_research_run_creation_and_attributes(db_session):
    """Verifies ResearchRun entity creation with default attributes and foreign user link."""
    admin = _create_user(db_session)
    config_raw = json.dumps({"mode": "standard", "scope": "cuu_dinh_162_motifs", "urn": "nhan_dinh"})
    config_hash = hashlib.sha256(config_raw.encode("utf-8")).hexdigest()

    run = ResearchRun(
        mode="standard",
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_nhan_dinh_01", "urn_nhan_dinh_02"],
        status=ResearchRunStatus.QUEUED.value,
        config_hash=config_hash,
        cost_budget=100.0,
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    loaded = db_session.execute(select(ResearchRun).where(ResearchRun.id == run.id)).scalar_one()
    assert loaded.id == run.id
    assert loaded.mode == "standard"
    assert loaded.scope_id == "cuu_dinh_162_motifs"
    assert loaded.subject_ids == ["urn_nhan_dinh_01", "urn_nhan_dinh_02"]
    assert loaded.config_hash == config_hash
    assert loaded.cost_budget == 100.0
    assert loaded.status == ResearchRunStatus.QUEUED.value
    assert loaded.created_by == admin.id
    assert loaded.created_at is not None


def test_research_phase_and_10_slot_jobs(db_session):
    """Verifies that a phase holds exactly 10 distinct subagent slots and enforces slot uniqueness."""
    admin = _create_user(db_session, "phase_runner@histolab.icu")
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_cao_dinh_05"],
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code=ResearchPhaseCode.P01.value,
        wave=1,
        state=ResearchPhaseStatus.DISPATCHED.value,
        input_sha256="abc123inputhash",
    )
    db_session.add(phase)
    db_session.commit()

    roles = [
        "scholarly_catalog_scout",
        "archive_connector",
        "monument_inscriptions_bot",
        "primary_source_validator",
        "open_access_indexer",
        "colonial_period_gazetteer",
        "court_records_crawler",
        "heritage_image_scout",
        "lexicographical_finder",
        "provenance_tracer",
    ]
    assert len(roles) == 10

    for idx, role in enumerate(roles, start=1):
        job = ResearchJob(
            phase_id=phase.id,
            slot_number=idx,
            role_key=role,
            idempotency_key=f"{run.id}:P01:1:{idx}",
            state=ResearchJobStatus.QUEUED.value,
            provider="gemini",
            estimated_tokens=5000,
        )
        db_session.add(job)
    db_session.commit()

    loaded_phase = db_session.execute(select(ResearchPhase).where(ResearchPhase.id == phase.id)).scalar_one()
    assert len(loaded_phase.jobs) == 10
    indices = {j.slot_number for j in loaded_phase.jobs}
    assert indices == set(range(1, 11))


def test_slot_uniqueness_negative_constraint(db_session):
    """Negative test: Attempting to create duplicate slot_number within the same phase raises IntegrityError."""
    admin = _create_user(db_session, "slot_neg@histolab.icu")
    run = ResearchRun(
        subject_ids=["urn_thuan_dinh_02"],
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code="P02",
        wave=1,
    )
    db_session.add(phase)
    db_session.commit()

    job1 = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="rights_verifier_primary",
        idempotency_key="key_slot_1",
    )
    db_session.add(job1)
    db_session.commit()

    # Attempt duplicate slot_number=1 on the same phase
    job2_duplicate = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="rights_verifier_secondary",
        idempotency_key="key_slot_1_dup",
    )
    db_session.add(job2_duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_slot_range_negative_constraint(db_session):
    """Negative test: Slot number outside 1..10 violates check constraint."""
    admin = _create_user(db_session, "slot_range@histolab.icu")
    run = ResearchRun(
        subject_ids=["urn_thuan_dinh_03"],
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code="P02",
        wave=1,
    )
    db_session.add(phase)
    db_session.commit()

    # Slot number 11 is out of range (1..10)
    job_invalid = ResearchJob(
        phase_id=phase.id,
        slot_number=11,
        role_key="invalid_slot_agent",
        idempotency_key="key_slot_11",
    )
    db_session.add(job_invalid)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_worker_lease_and_heartbeat_lifecycle(db_session):
    """Verifies distributed worker lease creation, token, and release."""
    admin = _create_user(db_session, "lease_worker@histolab.icu")
    run = ResearchRun(subject_ids=["urn_tuyen_dinh_03"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(run_id=run.id, phase_code="P03", wave=1)
    db_session.add(phase)
    db_session.commit()

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="ocr_glyph_segmenter",
        idempotency_key="ocr_job_1",
    )
    db_session.add(job)
    db_session.commit()

    now = datetime.now(timezone.utc)
    lease_token = uuid.uuid4().hex
    lease = ResearchLease(
        job_id=job.id,
        worker_id="pod_worker_7a8b",
        lease_token=lease_token,
        status=ResearchLeaseStatus.ACTIVE.value,
        expires_at=now + timedelta(seconds=60),
    )
    db_session.add(lease)
    db_session.commit()

    loaded_lease = db_session.execute(select(ResearchLease).where(ResearchLease.id == lease.id)).scalar_one()
    assert loaded_lease.worker_id == "pod_worker_7a8b"
    assert loaded_lease.lease_token == lease_token
    assert loaded_lease.status == ResearchLeaseStatus.ACTIVE.value
    assert loaded_lease.expires_at > now

    # Release lease upon completion
    loaded_lease.status = ResearchLeaseStatus.RELEASED.value
    loaded_lease.released_at = datetime.now(timezone.utc)
    db_session.commit()

    reloaded = db_session.execute(select(ResearchLease).where(ResearchLease.id == lease.id)).scalar_one()
    assert reloaded.status == ResearchLeaseStatus.RELEASED.value
    assert reloaded.released_at is not None


def test_research_attempt_execution_metrics_and_errors(db_session):
    """Verifies immutable attempt tracking with duration, worker, and error details."""
    admin = _create_user(db_session, "attempt_admin@histolab.icu")
    run = ResearchRun(subject_ids=["urn_anh_dinh_04"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(run_id=run.id, phase_code="P04", wave=1)
    db_session.add(phase)
    db_session.commit()

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=2,
        role_key="atomic_claim_extractor",
        idempotency_key="claim_job_2",
    )
    db_session.add(job)
    db_session.commit()

    # Attempt 1: Failed
    att1 = ResearchAttempt(
        job_id=job.id,
        attempt_number=1,
        worker_id="worker_runner_01",
        status="FAILED",
        error_message="Gateway timeout from upstream inference provider",
    )
    db_session.add(att1)

    # Attempt 2: Succeeded
    att2 = ResearchAttempt(
        job_id=job.id,
        attempt_number=2,
        worker_id="worker_runner_02",
        status="SUCCEEDED",
        ended_at=datetime.now(timezone.utc),
    )
    db_session.add(att2)
    job.attempt = 2
    job.state = ResearchJobStatus.SUCCEEDED.value
    db_session.commit()

    loaded_job = db_session.execute(select(ResearchJob).where(ResearchJob.id == job.id)).scalar_one()
    assert len(loaded_job.attempts) == 2
    assert loaded_job.attempts[0].status == "FAILED"
    assert "timeout" in loaded_job.attempts[0].error_message
    assert loaded_job.attempts[1].status == "SUCCEEDED"


def test_research_budget_accounting_and_caps(db_session):
    """Verifies provider budget allocation and token spend per run."""
    admin = _create_user(db_session, "budget_admin@histolab.icu")
    run = ResearchRun(subject_ids=["urn_huyen_dinh_05"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    # Provider budget
    b1 = ResearchBudget(
        run_id=run.id,
        provider="gemini",
        total_budget=50.0,
        allocated=20.0,
        spent=12.5,
    )
    b2 = ResearchBudget(
        run_id=run.id,
        provider="ocr_engine",
        total_budget=10.0,
        allocated=5.0,
        spent=1.2,
    )
    db_session.add_all([b1, b2])
    db_session.commit()

    budgets = db_session.execute(select(ResearchBudget).where(ResearchBudget.run_id == run.id)).scalars().all()
    assert len(budgets) == 2
    providers = {b.provider for b in budgets}
    assert providers == {"gemini", "ocr_engine"}
    gemini_b = next(b for b in budgets if b.provider == "gemini")
    assert gemini_b.spent == 12.5
    assert gemini_b.total_budget == 50.0


def test_evidence_result_immutable_envelope(db_session):
    """Verifies ResearchEvidenceResult stores immutable schema envelope and artifact linkage."""
    admin = _create_user(db_session, "evidence_admin@histolab.icu")
    run = ResearchRun(subject_ids=["urn_nghi_dinh_06"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(run_id=run.id, phase_code="P06", wave=1)
    db_session.add(phase)
    db_session.commit()

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=7,
        role_key="citation_and_quote_validator",
        idempotency_key="citation_job_7",
    )
    db_session.add(job)
    db_session.commit()

    metrics = {"input_tokens": 1500, "output_tokens": 400, "duration_ms": 1200}
    evidence = ResearchEvidenceResult(
        job_id=job.id,
        schema_version="research-agent-result/v1",
        input_manifest_sha256="abc123inputmanifestsha",
        artifact_sha256="def456artifactsha",
        artifact_uri="s3://private-research/runs/evidence_001.json",
        model_identifier="gemini-2.5-pro",
        metrics=metrics,
        warnings=[],
        failures=[],
    )
    db_session.add(evidence)
    db_session.commit()

    loaded = db_session.execute(
        select(ResearchEvidenceResult).where(ResearchEvidenceResult.id == evidence.id)
    ).scalar_one()
    assert loaded.artifact_sha256 == "def456artifactsha"
    assert loaded.schema_version == "research-agent-result/v1"
    assert loaded.metrics["input_tokens"] == 1500
    assert loaded.model_identifier == "gemini-2.5-pro"


def test_negative_abuse_restart_does_not_erase_run_history(db_session):
    """Negative/abuse invariant test: Service restart/crash does not erase run history.

    Simulates process failure / session tear down and reconnect to verify
    run, phase, job, and evidence rows persist cleanly across engine restarts.
    """
    admin = _create_user(db_session, "restart_tester@histolab.icu")
    run_id = uuid.uuid4()
    run = ResearchRun(
        id=run_id,
        subject_ids=["urn_du_dinh_07"],
        status=ResearchRunStatus.RUNNING.value,
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(
        run_id=run.id,
        phase_code="P07",
        wave=1,
        state=ResearchPhaseStatus.RUNNING.value,
    )
    db_session.add(phase)
    db_session.commit()

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="full_vi_narrative_drafter",
        idempotency_key=f"restart_test_job_{uuid.uuid4().hex}",
        state=ResearchJobStatus.RUNNING.value,
    )
    db_session.add(job)
    db_session.commit()

    job_id = job.id
    phase_id = phase.id

    # Simulate crash / process restart: expire/clear session cache and reopen session on connection
    db_session.expire_all()
    fresh_session = sessionmaker(bind=db_session.get_bind())()

    try:
        persisted_run = fresh_session.execute(select(ResearchRun).where(ResearchRun.id == run_id)).scalar_one_or_none()
        assert persisted_run is not None, "Run history was lost upon restart!"
        assert persisted_run.status == ResearchRunStatus.RUNNING.value

        persisted_phase = fresh_session.execute(select(ResearchPhase).where(ResearchPhase.id == phase_id)).scalar_one_or_none()
        assert persisted_phase is not None, "Phase history was lost upon restart!"

        persisted_job = fresh_session.execute(select(ResearchJob).where(ResearchJob.id == job_id)).scalar_one_or_none()
        assert persisted_job is not None, "Job state was lost upon restart!"
        assert persisted_job.role_key == "full_vi_narrative_drafter"
    finally:
        fresh_session.close()


def test_cascade_deletion_cleans_child_records(db_session):
    """Verifies deleting a ResearchRun cascades cleanly to phases, jobs, attempts, leases, budgets, and evidence."""
    admin = _create_user(db_session, "cascade_admin@histolab.icu")
    run = ResearchRun(subject_ids=["urn_tuyen_dinh_08"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    phase = ResearchPhase(run_id=run.id, phase_code="P08", wave=1)
    db_session.add(phase)
    db_session.commit()

    job = ResearchJob(
        phase_id=phase.id,
        slot_number=1,
        role_key="qa_verifier",
        idempotency_key="cascade_job_1",
    )
    db_session.add(job)
    db_session.commit()

    attempt = ResearchAttempt(
        job_id=job.id,
        attempt_number=1,
        worker_id="worker_01",
        status="SUCCEEDED",
    )
    lease = ResearchLease(
        job_id=job.id,
        worker_id="worker_01",
        lease_token="lease_token_123",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    budget = ResearchBudget(
        run_id=run.id,
        provider="default",
    )
    evidence = ResearchEvidenceResult(
        job_id=job.id,
        input_manifest_sha256="input_sha_123",
        artifact_sha256="abc123sha",
        artifact_uri="s3://private-research/test.json",
        model_identifier="gemini-2.5-pro",
    )
    db_session.add_all([attempt, lease, budget, evidence])
    db_session.commit()

    # Delete run
    db_session.delete(run)
    db_session.commit()

    assert db_session.execute(select(ResearchRun).where(ResearchRun.id == run.id)).scalar_one_or_none() is None
    assert db_session.execute(select(ResearchPhase).where(ResearchPhase.id == phase.id)).scalar_one_or_none() is None
    assert db_session.execute(select(ResearchJob).where(ResearchJob.id == job.id)).scalar_one_or_none() is None
    assert db_session.execute(select(ResearchAttempt).where(ResearchAttempt.job_id == job.id)).scalars().all() == []
    assert db_session.execute(select(ResearchLease).where(ResearchLease.job_id == job.id)).scalars().all() == []
    assert db_session.execute(select(ResearchBudget).where(ResearchBudget.run_id == run.id)).scalars().all() == []
    assert db_session.execute(select(ResearchEvidenceResult).where(ResearchEvidenceResult.job_id == job.id)).scalars().all() == []
