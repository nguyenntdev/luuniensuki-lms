# -*- coding: utf-8 -*-
"""V5-T072: 10-slot WaveDispatcher for AI Research Factory.

Validates the implementation contract for Wave W07 Slot A02:
1. Single transaction creates exactly 10 unique slots per phase wave.
2. Slot uniqueness and numbering strictly 1..10.
3. Payload snapshot hash (SHA-256) is computed and stored on the phase and jobs.
4. Durable queue: jobs enqueued with QUEUED status and execution parameters.
5. Idempotent replay: re-dispatching same run/phase/wave returns existing jobs without duplicate enqueueing.
6. Phase coverage: all phases P00 to P11 have strictly 10 unique roles mapped.
7. Negative abuse test: One role absent -> wave does not falsely count ten.
   When fewer than 10 roles or missing slots are passed, dispatch raises RoleIncompleteError
   and nothing is committed to the database.
8. Status summary returns complete 10-slot health breakdown.
"""
from __future__ import annotations

import hashlib
import json
import uuid
import pytest
from sqlalchemy import select

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
from backend.services.research_factory import (
    PHASE_ROLES_REGISTRY,
    RoleIncompleteError,
    SubagentRoleSpec,
    WaveDispatchError,
    WaveDispatchResult,
    WaveDispatcher,
    compute_payload_snapshot_hash,
    get_roles_for_phase,
)
from backend.security import hash_password


def _create_user(db_session, email: str = "dispatcher_admin@histolab.icu") -> User:
    user = User(
        email=email,
        password_hash=hash_password("SecureAdminPassword123!"),
        display_name="Wave Dispatcher Administrator",
        username=f"admin_{uuid.uuid4().hex[:8]}",
        role=UserRole.admin,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_registry_contains_all_12_phases_with_exactly_10_roles():
    """Validates that phases P00..P11 each have exactly 10 distinct roles registered."""
    expected_phases = [f"P{i:02d}" for i in range(12)]
    assert sorted(list(PHASE_ROLES_REGISTRY.keys())) == expected_phases

    for phase in expected_phases:
        roles = get_roles_for_phase(phase)
        assert len(roles) == 10, f"Phase {phase} has {len(roles)} roles instead of 10"
        slots = [r.slot for r in roles]
        assert slots == list(range(1, 11)), f"Phase {phase} slots are not 1..10: {slots}"
        codes = [r.code for r in roles]
        assert len(set(codes)) == 10, f"Duplicate codes in phase {phase}: {codes}"


def test_payload_snapshot_hash_computation():
    """Verifies deterministic SHA-256 digest computation over payload dictionaries."""
    payload1 = {"entity_slug": "urn_cao_dinh_05", "mode": "strict"}
    payload2 = {"mode": "strict", "entity_slug": "urn_cao_dinh_05"}
    # Key ordering must not affect hash
    hash1 = compute_payload_snapshot_hash(payload1)
    hash2 = compute_payload_snapshot_hash(payload2)
    assert hash1 == hash2
    assert len(hash1) == 64
    assert int(hash1, 16) > 0


def test_single_transaction_creates_exactly_10_unique_slots(db_session):
    """Core positive invariant: Single transaction creates exactly 10 unique slots per phase."""
    admin = _create_user(db_session)
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_nhan_dinh_01"],
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    dispatcher = WaveDispatcher(db_session)
    payload = {"urn": "nhan_dinh", "motif": "cop", "task": "source_discovery"}

    result = dispatcher.dispatch_phase_wave(
        run_id=run.id,
        phase_code="P01",
        wave=1,
        input_payload=payload,
        priority=5,
    )

    assert isinstance(result, WaveDispatchResult)
    assert result.run_id == run.id
    assert result.phase_code == "P01"
    assert result.wave == 1
    assert result.slot_count == 10
    assert len(result.job_ids) == 10
    assert result.is_idempotent_replay is False

    # Check persistence in database
    phase = db_session.execute(
        select(ResearchPhase).where(ResearchPhase.id == result.phase_id)
    ).scalar_one()
    assert phase.state == ResearchPhaseStatus.DISPATCHED.value
    assert phase.input_sha256 == compute_payload_snapshot_hash(payload)

    jobs = sorted(list(phase.jobs), key=lambda j: j.slot_number)
    assert len(jobs) == 10
    assert [j.slot_number for j in jobs] == list(range(1, 11))
    for j in jobs:
        assert j.state == ResearchJobStatus.QUEUED.value
        assert j.priority == 5
        assert j.payload == payload
        assert j.idempotency_key.startswith(f"{run.id}:P01:1:{j.slot_number}:")


def test_negative_abuse_one_role_absent_does_not_falsely_count_ten(db_session):
    """Required negative/abuse invariant: One role absent -> wave does not falsely count ten.

    If an incomplete list of roles (e.g. 9 roles instead of 10) is provided,
    the dispatcher MUST reject the dispatch with RoleIncompleteError,
    MUST NOT create a partial wave, and MUST NOT claim slot_count=10.
    """
    admin = _create_user(db_session, "abuse_tester@histolab.icu")
    run = ResearchRun(
        scope_id="cuu_dinh_162_motifs",
        subject_ids=["urn_tuyen_dinh_03"],
        created_by=admin.id,
    )
    db_session.add(run)
    db_session.commit()

    dispatcher = WaveDispatcher(db_session)
    full_roles = get_roles_for_phase("P00")
    # Simulate missing role #7 (legal source planner absent)
    incomplete_9_roles = [r for r in full_roles if r.slot != 7]
    assert len(incomplete_9_roles) == 9

    with pytest.raises(RoleIncompleteError) as exc_info:
        dispatcher.dispatch_phase_wave(
            run_id=run.id,
            phase_code="P00",
            wave=1,
            role_overrides=incomplete_9_roles,
        )

    assert "requires exactly 10 roles, got 9" in str(exc_info.value)

    # Invariant: Phase was NOT created or has zero jobs
    phase = db_session.execute(
        select(ResearchPhase).where(
            ResearchPhase.run_id == run.id,
            ResearchPhase.phase_code == "P00",
        )
    ).scalar_one_or_none()
    assert phase is None, "Incomplete phase was erroneously committed to database!"


def test_negative_abuse_slot_index_gap_rejected(db_session):
    """Negative invariant: 10 roles with non-consecutive slots (gap) must be rejected."""
    admin = _create_user(db_session, "gap_tester@histolab.icu")
    run = ResearchRun(subject_ids=["urn_du_dinh_04"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    dispatcher = WaveDispatcher(db_session)
    # 10 roles, but slots are 1..9, 11 (missing slot 10)
    gap_roles = [
        SubagentRoleSpec(1, "P00-A01", "R1"),
        SubagentRoleSpec(2, "P00-A02", "R2"),
        SubagentRoleSpec(3, "P00-A03", "R3"),
        SubagentRoleSpec(4, "P00-A04", "R4"),
        SubagentRoleSpec(5, "P00-A05", "R5"),
        SubagentRoleSpec(6, "P00-A06", "R6"),
        SubagentRoleSpec(7, "P00-A07", "R7"),
        SubagentRoleSpec(8, "P00-A08", "R8"),
        SubagentRoleSpec(9, "P00-A09", "R9"),
        SubagentRoleSpec(11, "P00-A11", "R11"),  # Invalid slot index!
    ]

    with pytest.raises(RoleIncompleteError) as exc_info:
        dispatcher.dispatch_phase_wave(
            run_id=run.id,
            phase_code="P00",
            wave=1,
            role_overrides=gap_roles,
        )

    assert "Role slots must be consecutive 1..10" in str(exc_info.value)


def test_idempotent_redispatch_returns_existing_wave(db_session):
    """Verifies that re-dispatching the exact same phase wave does not recreate or duplicate jobs."""
    admin = _create_user(db_session, "idempotent_tester@histolab.icu")
    run = ResearchRun(subject_ids=["urn_chuong_dinh_02"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    dispatcher = WaveDispatcher(db_session)
    payload = {"entity_slug": "urn_chuong_dinh_02"}

    # First dispatch
    result1 = dispatcher.dispatch_phase_wave(run.id, "P02", wave=1, input_payload=payload)
    assert result1.is_idempotent_replay is False
    assert result1.slot_count == 10

    # Second dispatch with identical arguments
    result2 = dispatcher.dispatch_phase_wave(run.id, "P02", wave=1, input_payload=payload)
    assert result2.is_idempotent_replay is True
    assert result2.slot_count == 10
    assert result2.job_ids == result1.job_ids
    assert result2.phase_id == result1.phase_id

    # Total jobs in database for this phase must still be exactly 10
    phase = db_session.execute(
        select(ResearchPhase).where(ResearchPhase.id == result1.phase_id)
    ).scalar_one()
    assert len(phase.jobs) == 10


def test_phase_status_summary(db_session):
    """Verifies detailed 10-slot health summary extraction."""
    admin = _create_user(db_session, "summary_tester@histolab.icu")
    run = ResearchRun(subject_ids=["urn_anh_dinh_01"], created_by=admin.id)
    db_session.add(run)
    db_session.commit()

    dispatcher = WaveDispatcher(db_session)
    dispatch = dispatcher.dispatch_phase_wave(run.id, "P05", wave=1)

    summary = dispatcher.get_phase_status_summary(dispatch.phase_id)
    assert summary["phase_code"] == "P05"
    assert summary["slot_count"] == 10
    assert summary["is_complete_ten"] is True
    assert len(summary["slots"]) == 10
    for s in summary["slots"]:
        assert s["state"] == ResearchJobStatus.QUEUED.value
        assert 1 <= s["slot_number"] <= 10
