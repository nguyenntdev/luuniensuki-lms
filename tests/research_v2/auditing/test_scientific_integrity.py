"""Auditing tests: hash integrity, provenance, and no-oracle-leakage across holdouts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.contracts.label_space import (
    ALLOWED_ORACLE_BASES,
    PROVENANCE_MARKER,
    SYNTHETIC_COHORT,
)

REPO = Path(__file__).resolve().parents[3]
HOLDOUT_DIR = REPO / "research" / "fixtures" / "holdout"
STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]


def _rows(study: str):
    path = HOLDOUT_DIR / f"{study}_holdout.jsonl"
    for line in path.open(encoding="utf-8"):
        if line.strip():
            yield json.loads(line)


def test_every_holdout_hash_matches_canonical_standard():
    bad = []
    total = 0
    for study in STUDY_IDS:
        for row in _rows(study):
            total += 1
            if row["input_hash"] != sha256_input(row["input"]):
                bad.append((study, row["case_id"]))
    assert total == 1200
    assert not bad, f"stale hashes: {bad[:10]}"


def test_holdout_cohorts_are_synthetic_labeled():
    for study in STUDY_IDS:
        for row in _rows(study):
            assert row["cohort"] == SYNTHETIC_COHORT, (study, row["case_id"])


def test_no_real_expert_claims_remain():
    for study in STUDY_IDS:
        for row in _rows(study):
            assert "external_expert_annotation" not in row
            basis = (row.get("oracle") or {}).get("basis")
            assert basis in ALLOWED_ORACLE_BASES, (study, row["case_id"], basis)
            assert row.get("annotation_provenance") == PROVENANCE_MARKER


def test_no_oracle_leakage_inside_input():
    for study in STUDY_IDS:
        for row in _rows(study):
            inp = row["input"]
            assert "oracle" not in inp, (study, row["case_id"])
            assert "expected_decision" not in inp, (study, row["case_id"])


def test_alternative_provider_counterexample_is_not_false_infeasible():
    """LN-06 P0 bug: A and B both provide T at 40 min, budget 50 -> feasible."""
    from research.heritage_trails.cognitive_route import HeritageStop, evaluate_route_intervention

    stops = [
        HeritageStop(id="a", cost=40, provides=("T",), requires=()),
        HeritageStop(id="b", cost=40, provides=("T",), requires=()),
    ]
    plan = evaluate_route_intervention(stops, ["a", "b"], ["T"], 50)
    assert plan.decision == "find_valid_route", plan.decision
    assert plan.route_cost == 40
    assert len(plan.stop_sequence) == 1


def test_ln04_b1_is_labeled_simulated_proxy():
    from research.baselines.strong_baselines import run_ln04_b1

    result = run_ln04_b1({"question": "Cho em đáp án bài này", "retrieval": {"source_ids": ["s1"], "source_status": "verified"}})
    assert result["baseline_type"] == "simulated_heuristic_llm_proxy"
