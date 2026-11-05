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


def test_invalid_adapter_mode(base_scenario_input):
    with pytest.raises(ValueError, match="Unknown mode"):
        run_policy(base_scenario_input, mode="unknown_mode", config={})


# ---------------------------------------------------------------------------
# Concrete Fixture Evaluation
# ---------------------------------------------------------------------------

def test_concrete_fixture_100_percent_intervention():
    fixture_path = Path("/home/clue/Documents/luuniensuki-lms/LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026/LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026/04_FIXTURES/CONCRETE/LN-03_concrete.jsonl")
    if not fixture_path.exists():
        pytest.skip("Concrete fixture not found")

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
