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
    candidates = [
        Path(os.environ.get("RESEARCH_FIXTURE_DIR", "")) / "LN-03_concrete.jsonl",
        Path(__file__).resolve().parents[2] / "research" / "fixtures" / "LN-03_concrete.jsonl",
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-03_concrete.jsonl",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[1]


FIXTURE_PATH = _resolve_fixture_path()
