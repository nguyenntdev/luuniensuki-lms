"""Automated test suite for LN-03 Dual-Mode Spaced Learning Policy.

Validates:
- All 5 decision rules (RULE-LN-03-01 through RULE-LN-03-05)
- Invariants (INV-LN-03-01 to INV-LN-03-05)
- Mode semantics: baseline vs intervention vs ablations
- Observables: generative_assigned, review_burden, task_type_coverage
- Error handling & edge cases
- Conformance with LN-03 concrete fixture scenarios
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from backend.domain.review_task_types import (
    CognitiveTaskType,
    ReviewDecision,
    ReviewCard,
    GenerativeTaskDescriptor,
)
from research.spaced_learning.dual_mode_policy import (
    is_valid_finite_number,
    is_item_due,
    schedule_dual_mode_intervention,
    schedule_baseline,
    schedule_ablation,
    POLICY_VERSION,
)
from research.integrations.ln03 import run_policy


@pytest.fixture
def base_scenario_input():
    return {
        "case_id": "TEST-LN-03-001",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "fact_prerequisite_mastered": True,
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.5, "S2": 0.5},
            "event_condition": "regular",
            "is_new": False,
            "profile_id": "SYN-TEST",
            "synthetic": True,
        },
        "now_utc": "2026-11-05T08:00:00Z",
        "review_card": {
            "difficulty": 5.0,
            "due_utc": "2026-11-01T08:00:00Z",
            "id": "fact-ngo-mon",
            "last_review_utc": "2026-10-25T08:00:00Z",
            "source_verified": True,
            "stability_days": 5.0,
            "state": "review",
            "target_retention": 0.9,
        },
        "scheduler_weight": 1.0,
        "seed": 20261105,
        "task_type": "historical_explanation",
    }


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_is_valid_finite_number():
    assert is_valid_finite_number(1.0) is True
    assert is_valid_finite_number(0) is True
    assert is_valid_finite_number(-2.5) is True
    assert is_valid_finite_number("1.5") is True
    assert is_valid_finite_number("NaN") is False
    assert is_valid_finite_number("Inf") is False
    assert is_valid_finite_number("-Inf") is False
    assert is_valid_finite_number(float("nan")) is False
    assert is_valid_finite_number(float("inf")) is False
    assert is_valid_finite_number(None) is False
    assert is_valid_finite_number("invalid") is False


def test_is_item_due():
    now = "2026-11-05T08:00:00Z"
    past = "2026-11-01T08:00:00Z"
    future = "2026-11-10T08:00:00Z"
    assert is_item_due(past, now) is True
    assert is_item_due(now, now) is True
    assert is_item_due(future, now) is False
    assert is_item_due("invalid-date", now) is False


# ---------------------------------------------------------------------------
# Decision rules verification (RULE-LN-03-01 to 05)
# ---------------------------------------------------------------------------

def test_rule_01_nominal_eligible(base_scenario_input):
    """RULE-LN-03-01: When nominal -> schedule_eligible."""
    res = schedule_dual_mode_intervention(base_scenario_input)
    assert res["decision"] == "schedule_eligible"
    assert "schedule_eligible" in res["reason_codes"]
    assert res["generative_assigned"] is True
    assert res["review_burden"] == 2.0
    assert res["task_type_coverage"] == 1.0


def test_rule_02_missing_fact_base(base_scenario_input):
    """RULE-LN-03-02: When missing_fact_base -> assign_fact_retrieval."""
    scenario = dict(base_scenario_input)
    scenario["fact_prerequisite_mastered"] = False
    res = schedule_dual_mode_intervention(scenario)
    assert res["decision"] == "assign_fact_retrieval"
    assert "missing_fact_base" in res["reason_codes"]
    assert res["generative_assigned"] is False
    assert res["review_burden"] == 1.0
    assert res["task_type_coverage"] == 0.5


def test_rule_03_not_due(base_scenario_input):
    """RULE-LN-03-03: When not_due -> postpone."""
    scenario = dict(base_scenario_input)
    card = dict(scenario["review_card"])
    card["due_utc"] = "2026-12-01T08:00:00Z"
    scenario["review_card"] = card
    res = schedule_dual_mode_intervention(scenario)
    assert res["decision"] == "postpone"
    assert "not_due" in res["reason_codes"]
    assert res["generative_assigned"] is False
    assert res["review_burden"] == 0.0


def test_rule_04_nonfinite_weight(base_scenario_input):
    """RULE-LN-03-04: When nonfinite_weight -> reject_invalid_scheduler."""
    scenario = dict(base_scenario_input)
    scenario["scheduler_weight"] = "NaN"
    res = schedule_dual_mode_intervention(scenario)
    assert res["decision"] == "reject_invalid_scheduler"
    assert "nonfinite_weight" in res["reason_codes"]
    assert res["generative_assigned"] is False


def test_rule_05_absent_source(base_scenario_input):
    """RULE-LN-03-05: When absent_source -> block_explanation."""
    scenario = dict(base_scenario_input)
    card = dict(scenario["review_card"])
    card["source_verified"] = False
    scenario["review_card"] = card
    res = schedule_dual_mode_intervention(scenario)
    assert res["decision"] == "block_explanation"
    assert "absent_source" in res["reason_codes"]
    assert res["generative_assigned"] is False


# ---------------------------------------------------------------------------
# Baseline vs Intervention comparison
# ---------------------------------------------------------------------------

def test_baseline_behavior_on_missing_fact_base(base_scenario_input):
    """Baseline unconditionally schedules even if prerequisites are missing."""
    scenario = dict(base_scenario_input)
    scenario["fact_prerequisite_mastered"] = False

    res_base = run_policy(scenario, mode="baseline", config={})
    res_inter = run_policy(scenario, mode="intervention", config={})

    # Baseline schedules generative task regardless of missing prerequisites
    assert res_base["decision"] == "schedule_eligible"
    assert res_base["generative_assigned"] is True

    # Intervention blocks generative task and assigns fact retrieval instead
    assert res_inter["decision"] == "assign_fact_retrieval"
    assert res_inter["generative_assigned"] is False


def test_baseline_behavior_on_absent_source(base_scenario_input):
    """Baseline unconditionally schedules even if source is unverified."""
    scenario = dict(base_scenario_input)
    card = dict(scenario["review_card"])
    card["source_verified"] = False
    scenario["review_card"] = card

    res_base = run_policy(scenario, mode="baseline", config={})
    res_inter = run_policy(scenario, mode="intervention", config={})

    assert res_base["decision"] == "schedule_eligible"
    assert res_base["generative_assigned"] is True

    assert res_inter["decision"] == "block_explanation"
    assert res_inter["generative_assigned"] is False


# ---------------------------------------------------------------------------
# Ablation modes
# ---------------------------------------------------------------------------

def test_ablation_modes(base_scenario_input):
    # Ablation 1: generic_fsrs
    scenario_missing = dict(base_scenario_input)
    scenario_missing["fact_prerequisite_mastered"] = False
    res_a1 = run_policy(scenario_missing, mode="ablation", config={"ablation_type": "generic_fsrs"})
    assert res_a1["decision"] == "schedule_eligible"
    assert res_a1["generative_assigned"] is True

    # Ablation 2: omit_source_check
    scenario_unverified = dict(base_scenario_input)
    card = dict(scenario_unverified["review_card"])
    card["source_verified"] = False
    scenario_unverified["review_card"] = card
    res_a2 = run_policy(scenario_unverified, mode="ablation", config={"ablation_type": "omit_source_check"})
    assert res_a2["decision"] == "schedule_eligible"
    assert res_a2["generative_assigned"] is True

    # Ablation 3: omit_workload_limit
    res_a3 = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "omit_workload_limit"})
    assert res_a3["decision"] == "schedule_eligible"
    assert res_a3["review_burden"] == 5.0

    # Ablation: no_burden_cap (alias for omit_workload_limit)
    res_burden = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "no_burden_cap"})
    assert res_burden["decision"] == "schedule_eligible"
    assert res_burden["review_burden"] == 5.0

    # Ablation: retrieval_only
    res_retrieval = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "retrieval_only"})
    assert res_retrieval["decision"] == "assign_fact_retrieval"
    assert res_retrieval["generative_assigned"] is False
    assert res_retrieval["review_burden"] == 1.0


def test_five_study_conditions_configs_experiments(base_scenario_input):
    """Verify all 5 conditions specified in configs/experiments.json and aliases:
    - B0: baseline (mode='baseline', config={})
    - I1: intervention (mode='intervention', config={})
    - A1: generic_fsrs / retrieval_only
    - A2: omit_source_check / no_burden_cap
    - A3: omit_workload_limit / generic_fsrs
    """
    # 1. B0: Baseline
    res_b0 = run_policy(base_scenario_input, mode="baseline", config={})
    assert res_b0["decision"] == "schedule_eligible"
    assert res_b0["policy_version"] == "baseline-v1"
    assert res_b0["generative_assigned"] is True

    # 2. I1: Intervention
    res_i1 = run_policy(base_scenario_input, mode="intervention", config={})
    assert res_i1["decision"] == "schedule_eligible"
    assert res_i1["policy_version"] == POLICY_VERSION
    assert res_i1["generative_assigned"] is True

    # 3. A1: generic_fsrs (from configs/experiments.json) & retrieval_only alias
    res_a1_fsrs = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "generic_fsrs"})
    assert res_a1_fsrs["decision"] == "schedule_eligible"
    assert res_a1_fsrs["policy_version"] == "baseline-v1"

    res_a1_retrieval = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "retrieval_only"})
    assert res_a1_retrieval["decision"] == "assign_fact_retrieval"
    assert res_a1_retrieval["generative_assigned"] is False

    # 4. A2: omit_source_check (from configs/experiments.json) & no_burden_cap alias
    unverified = dict(base_scenario_input)
    card_unv = dict(unverified["review_card"])
    card_unv["source_verified"] = False
    unverified["review_card"] = card_unv
    res_a2_source = run_policy(unverified, mode="ablation", config={"ablation_type": "omit_source_check"})
    assert res_a2_source["decision"] == "schedule_eligible"
    assert res_a2_source["generative_assigned"] is True

    res_a2_burden = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "no_burden_cap"})
    assert res_a2_burden["decision"] == "schedule_eligible"
    assert res_a2_burden["review_burden"] == 5.0

    # 5. A3: omit_workload_limit (from configs/experiments.json)
    res_a3_workload = run_policy(base_scenario_input, mode="ablation", config={"ablation_type": "omit_workload_limit"})
    assert res_a3_workload["decision"] == "schedule_eligible"
    assert res_a3_workload["review_burden"] == 5.0


def test_edge_cases_empty_and_malformed():
    """Verify robust handling of empty, malformed, or missing input fields."""
    # Completely empty scenario
    res_empty = run_policy({}, mode="intervention", config={})
    assert res_empty["decision"] == "reject_invalid_scheduler"
    assert res_empty["generative_assigned"] is False

    # Missing review_card but valid weight
    res_no_card = run_policy({"scheduler_weight": 1.0, "now_utc": "2026-11-05T08:00:00Z"}, mode="intervention", config={})
    assert res_no_card["decision"] == "postpone"
    assert res_no_card["generative_assigned"] is False

    # Factual recall task (not historical_explanation) with unmastered prerequisite
    fact_task_scenario = {
        "scheduler_weight": 1.0,
        "now_utc": "2026-11-05T08:00:00Z",
        "task_type": "factual_recall",
        "fact_prerequisite_mastered": False,
        "review_card": {
            "due_utc": "2026-11-01T08:00:00Z",
            "source_verified": True,
        },
    }
    res_fact = run_policy(fact_task_scenario, mode="intervention", config={})
    assert res_fact["decision"] == "schedule_eligible"
    assert res_fact["generative_assigned"] is False
    assert res_fact["review_burden"] == 1.0


def test_invalid_adapter_mode(base_scenario_input):
    with pytest.raises(ValueError, match="Unknown mode"):
        run_policy(base_scenario_input, mode="unknown_mode", config={})


# ---------------------------------------------------------------------------
# Concrete Fixture Evaluation
# ---------------------------------------------------------------------------

def _resolve_fixture_path() -> Path:
    if os.environ.get("RESEARCH_FIXTURE_DIR"):
        p = Path(os.environ["RESEARCH_FIXTURE_DIR"]) / "LN-03_concrete.jsonl"
        if p.exists():
            return p
    if os.environ.get("SPEC"):
        p = Path(os.environ["SPEC"]) / "04_FIXTURES" / "CONCRETE" / "LN-03_concrete.jsonl"
        if p.exists():
            return p
    return (
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-03_concrete.jsonl"
    )


FIXTURE_PATH = _resolve_fixture_path()


def test_concrete_fixture_100_percent_intervention():
    fixture_path = FIXTURE_PATH
    assert fixture_path.exists(), f"Mandatory fixture missing (fail-closed): {fixture_path}"

    matches = 0
    total = 0
    with fixture_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            res = run_policy(row["input"], mode="intervention", config={})
            expected = row["oracle"]["expected_decision"]
            assert res["decision"] == expected, f"Mismatch in {row['case_id']}: {res['decision']} != {expected}"
            assert isinstance(res["generative_assigned"], bool)
            total += 1
            matches += 1

    assert total == 720
    assert matches == 720


# ---------------------------------------------------------------------------
# Holdout Fixture and B1 Leitner Baseline Tests
# ---------------------------------------------------------------------------

def test_b1_leitner_baseline_behavior(base_scenario_input):
    """Test B1 (Leitner Box without source grounding).

    1. Checks prerequisite: blocks generative task if missing fact base.
    2. Crucial flaw: ignores source verification, allowing ungrounded explanations.
    """
    # Case 1: Missing prerequisite -> Leitner demotes to fact retrieval
    scen_missing_pre = dict(base_scenario_input)
    scen_missing_pre["fact_prerequisite_mastered"] = False
    res_b1_pre = run_policy(scen_missing_pre, mode="leitner", config={})
    assert res_b1_pre["decision"] == "assign_fact_retrieval"
    assert res_b1_pre["generative_assigned"] is False
    assert res_b1_pre["policy_version"] == "leitner-v1"

    # Case 2: Unverified source -> Leitner lacks source check, assigns generative task!
    scen_unverified = dict(base_scenario_input)
    card_unv = dict(scen_unverified["review_card"])
    card_unv["source_verified"] = False
    scen_unverified["review_card"] = card_unv
    res_b1_src = run_policy(scen_unverified, mode="leitner", config={})
    assert res_b1_src["decision"] == "schedule_eligible"
    assert res_b1_src["generative_assigned"] is True


def test_independent_holdout_dataset_integrity_and_evaluation():
    """Verify holdout dataset structure and exact policy benchmarks across 120 cases."""
    holdout_path = Path(__file__).resolve().parents[2] / "research" / "fixtures" / "holdout" / "LN-03_holdout.jsonl"
    assert holdout_path.exists(), f"Holdout fixture missing: {holdout_path}"

    cases = []
    with holdout_path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) == 120, f"Expected 120 holdout cases, got {len(cases)}"

    fault_counts = {}
    for c in cases:
        fid = c["fault_id"]
        fault_counts[fid] = fault_counts.get(fid, 0) + 1

    expected_faults = {
        "nominal": 24,
        "missing_fact_base": 24,
        "not_due_for_review": 24,
        "non_finite_stability_weight": 24,
        "unverified_source_claim": 24,
    }
    assert fault_counts == expected_faults, f"Fault counts mismatch: {fault_counts} vs {expected_faults}"

    # Evaluate I1 intervention on all holdout cases: must achieve 100% oracle match
    oracle_matches = 0
    invalid_generative_i1 = 0
    invalid_generative_b0 = 0
    invalid_generative_b1 = 0
    eligible_count = 0

    for c in cases:
        inp = c["input"]
        exp_decision = c["oracle"]["expected_decision"]

        res_i1 = run_policy(inp, mode="intervention", config={})
        res_b0 = run_policy(inp, mode="baseline", config={})
        res_b1 = run_policy(inp, mode="leitner", config={})

        if res_i1["decision"] == exp_decision:
            oracle_matches += 1

        if c["fault_id"] in ("missing_fact_base", "unverified_source_claim"):
            eligible_count += 1
            if res_i1["generative_assigned"] is True:
                invalid_generative_i1 += 1
            if res_b0["generative_assigned"] is True:
                invalid_generative_b0 += 1
            if res_b1["generative_assigned"] is True:
                invalid_generative_b1 += 1

    assert oracle_matches == 120, f"I1 intervention failed oracle matches: {oracle_matches}/120"
    assert eligible_count == 48, f"Expected 48 eligible fault cases, got {eligible_count}"
    assert invalid_generative_i1 == 0, f"I1 had {invalid_generative_i1} invalid generative assignments"
    assert invalid_generative_b0 == 48, f"B0 expected 48 invalid assignments, got {invalid_generative_b0}"
    assert invalid_generative_b1 == 24, f"B1 expected 24 invalid assignments, got {invalid_generative_b1}"

