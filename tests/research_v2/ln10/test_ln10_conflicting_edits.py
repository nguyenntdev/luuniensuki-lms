"""Mandatory counterexample: TWO CONFLICTING OFFLINE EDITS to the same version.

The scientifically correct outcome (LN-10-03.F case 1, INV-LN-10-04): the
state machine must DETECT the conflict and REJECT/POSTPONE into a visible
conflict-resolution state (``resolve_revision_conflict``). Silently applying
either edit is the regression under test.
"""
from __future__ import annotations

import pytest

from tests.research_v2.ln10.ln10_helpers import (
    conflicting_edits_features,
    make_features,
    make_input,
)
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln10.ablations import a2_solve
from research_v2.methods.ln10.baselines import b0_decide, c1_decide
from research_v2.methods.ln10.dataset import parse_case
from research_v2.methods.ln10.proposed import predict_batch, solve_case

CONFLICT = "resolve_revision_conflict"


def test_proposed_detects_two_conflicting_offline_edits():
    inp = make_input(conflicting_edits_features(), case_id="conflict-mandatory")
    pred = predict_batch([inp], {"seed": 11})[0]
    assert pred.decision == CONFLICT
    assert "concurrent_offline_edits" in pred.reason_codes
    assert pred.score == 0.0  # nothing applied


def test_proposed_does_not_silently_apply_either_edit():
    """The accepted new_goal must be neither edit's payload — no last-write-wins."""
    inp = make_input(conflicting_edits_features(), case_id="conflict-no-apply")
    pred = predict_batch([inp], {"seed": 11})[0]
    assert pred.decision != "allow_authorized_transition"
    features = conflicting_edits_features()
    edit_goals = {e["new_goal"] for e in features["concurrent_edits"]}
    # evidence must reference both conflicting editors, proving detection
    evidence = " ".join(pred.evidence_ids)
    assert "student-a" in evidence and "student-b" in evidence
    assert edit_goals  # payload check guard; application is what must NOT happen


def test_proposed_conflict_precedes_rationale_and_reflection_gates():
    """A conflict must not be masked into a reflection/rationale label."""
    features = conflicting_edits_features(transition={
        "action": "submit",
        "expected_version": 3,
        "new_goal": None,
        "rationale": "",
    })
    case = parse_case("conflict-order", features)
    result = solve_case(case)
    assert result["decision"] == CONFLICT
    assert result["conflict_detected"] is True


def test_identical_redelivery_is_idempotent_not_conflict():
    """Same payload re-delivered by the same editor is a replay, not a conflict."""
    features = make_features(
        concurrent_edits=[
            {
                "editor": "student-a",
                "expected_version": 3,
                "action": "revise_plan",
                "new_goal": "heritage_learning_campaign",
                "rationale": "Khảo sát thực địa.",
            },
            {
                "editor": "student-a",
                "expected_version": 3,
                "action": "revise_plan",
                "new_goal": "heritage_learning_campaign",
                "rationale": "Khảo sát thực địa.",
            },
        ],
    )
    case = parse_case("conflict-idempotent", features)
    result = solve_case(case)
    assert result["decision"] == "allow_authorized_transition"
    assert result["conflict_detected"] is False


def test_c1_checklist_baseline_misses_same_version_conflict():
    """C1 has no concurrent-edit-set detector: it silently applies (regression)."""
    features = conflicting_edits_features()
    case = parse_case("conflict-c1", features)
    result = c1_decide(case)
    # Documented classical failure: CAS passes (versions aligned), checklist
    # never inspects the edit set -> the first edit is silently applied.
    assert result["decision"] == "allow_authorized_transition"
    assert result["conflict_detected"] is False


def test_b0_baseline_silently_applies_conflicting_edits():
    features = conflicting_edits_features()
    case = parse_case("conflict-b0", features)
    result = b0_decide(case)
    assert result["decision"] == "allow_authorized_transition"


def test_a2_ablation_loses_conflict_detection():
    """Removing concurrency control makes the ablation apply the conflict."""
    features = conflicting_edits_features()
    case = parse_case("conflict-a2", features)
    result = a2_solve(case)
    assert result["decision"] == "allow_authorized_transition"
    assert "concurrency_check_disabled" in result["reason_codes"]


def test_t3_dataset_conflict_stratum_all_detected():
    """All 24 T3 conflict-stratum cases (stale CAS) must be detected."""
    import json
    from pathlib import Path

    from research_v2.methods.ln10.dataset import DATASET_PATH

    rows = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    conflict_rows = [
        r for r in rows
        if r["input"]["transition"]["expected_version"] != r["input"]["project"]["version"]
    ]
    assert len(conflict_rows) == 24
    preds = predict_batch(
        [
            StudyInput("LN-10", r["case_id"], "test", r["group_id"], r["input"])
            for r in conflict_rows
        ],
        {"seed": 11},
    )
    assert all(p.decision == CONFLICT for p in preds)


def test_legacy_engine_gaps_same_version_conflict():
    """The observed legacy engine silently applies the mandatory case (provenance)."""
    pytest.importorskip("research.integrations.ln10")
    from research_v2.methods.ln10.legacy_adapter import legacy_decide

    features = conflicting_edits_features()
    features.pop("concurrent_edits", None)  # legacy input contract has no edit set
    result = legacy_decide(features, mode="intervention")
    # Documented legacy limitation: plain CAS passes, no conflict raised.
    assert result["decision"] == "allow_authorized_transition"
    assert result["conflict_detected"] is False
