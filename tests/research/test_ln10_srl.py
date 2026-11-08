# -*- coding: utf-8 -*-
"""Automated tests for Study LN-10 (Self-Regulated Learning & Hue Heritage Projects)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from backend.domain.reflection_cycle import (
    DecisionCode,
    LearnerProject,
    ProjectGoal,
    ProjectPlan,
    ProjectStage,
    ProjectTransition,
    ReasonCode,
    ReflectionRecord,
    SRLPhase,
    TeacherSignoff,
    TransitionAction,
    evaluate_srl_cycle,
)
from research.integrations.ln10 import run_policy
from research.srl.project_state_machine import SRLProjectStateMachine


def get_fixture_path() -> Path:
    candidates = [
        Path(os.environ.get("LN10_FIXTURE_PATH", "")),
        Path(os.environ.get("RESEARCH_FIXTURE_DIR", "")) / "LN-10_concrete.jsonl",
        Path(__file__).resolve().parents[2] / "research" / "fixtures" / "LN-10_concrete.jsonl",
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-10_concrete.jsonl",
        Path("LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026/LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026/04_FIXTURES/CONCRETE/LN-10_concrete.jsonl"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[2]


def get_experiments_config_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[2] / "research" / "configs" / "experiments.json",
        Path("research/configs/experiments.json"),
        Path("configs/experiments.json"),
        Path("LUU_NIEN_RESEARCH_MASTER_EXECUTION_2026_11_07/configs/experiments.json"),
        Path(__file__).resolve().parents[2] / "configs" / "experiments.json",
        Path(__file__).resolve().parents[2] / "LUU_NIEN_RESEARCH_MASTER_EXECUTION_2026_11_07" / "configs" / "experiments.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


FIXTURE_PATH = get_fixture_path()


# --------------------------------------------------------------------------- #
# Domain Model Tests
# --------------------------------------------------------------------------- #
def test_domain_dataclasses_immutability():
    """Verify domain dataclasses are immutable and correctly typed."""
    goal = ProjectGoal(
        id="goal-01",
        goal_statement="Preserve Ngọ Môn historical motifs",
        content_scope="ngo-mon",
        created_at="2026-11-05T00:00:00Z",
    )
    assert goal.version == 1
    with pytest.raises(Exception):
        goal.version = 2  # type: ignore

    refl = ReflectionRecord(
        what_worked="Analyzed archival images",
        difficulties="Accessing 3D scans",
        planned_change="Substitute 2D rubbings",
        is_complete=True,
    )
    assert refl.is_complete is True


# --------------------------------------------------------------------------- #
# Rule Verification Tests (RULE-LN-10-01 to RULE-LN-10-05)
# --------------------------------------------------------------------------- #
def test_rule_ln10_01_nominal():
    """RULE-LN-10-01: nominal input -> allow_authorized_transition."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nguồn mới làm thay đổi phạm vi đề xuất",
        },
    }
    result = run_policy(scenario_input, mode="intervention", config={})
    assert result["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert result["transition_applied"] is True
    assert result["conflict_detected"] is False
    assert result["reflection_completed"] is True
    assert result["ownership_verified"] is True


def test_rule_ln10_02_missing_rationale():
    """RULE-LN-10-02: missing rationale -> request_reflection."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "   ",  # Blank/whitespace rationale
        },
    }
    result = run_policy(scenario_input, mode="intervention", config={})
    assert result["decision"] == DecisionCode.REQUEST_REFLECTION.value
    assert result["transition_applied"] is False
    assert ReasonCode.MISSING_RATIONALE.value in result["reason_codes"]


def test_rule_ln10_03_unauthorized_actor():
    """RULE-LN-10-03: unauthorized actor -> deny_transition."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": False},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nguồn mới làm thay đổi phạm vi đề xuất",
        },
    }
    result = run_policy(scenario_input, mode="intervention", config={})
    assert result["decision"] == DecisionCode.DENY_TRANSITION.value
    assert result["transition_applied"] is False
    assert result["ownership_verified"] is False
    assert ReasonCode.UNAUTHORIZED_ACTOR.value in result["reason_codes"]


def test_rule_ln10_04_offline_conflict():
    """RULE-LN-10-04: offline conflict / version mismatch -> resolve_revision_conflict."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 2,  # Stale version
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nguồn mới làm thay đổi phạm vi đề xuất",
        },
    }
    result = run_policy(scenario_input, mode="intervention", config={})
    assert result["decision"] == DecisionCode.RESOLVE_REVISION_CONFLICT.value
    assert result["transition_applied"] is False
    assert result["conflict_detected"] is True
    assert ReasonCode.OFFLINE_CONFLICT.value in result["reason_codes"]


def test_rule_ln10_05_skipped_reflection():
    """RULE-LN-10-05: premature submit without reflection -> reject_premature_submit."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": False,  # Reflection omitted
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "submit",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nộp bài",
        },
    }
    result = run_policy(scenario_input, mode="intervention", config={})
    assert result["decision"] == DecisionCode.REJECT_PREMATURE_SUBMIT.value
    assert result["transition_applied"] is False
    assert result["reflection_completed"] is False
    assert ReasonCode.SKIPPED_REFLECTION.value in result["reason_codes"]


# --------------------------------------------------------------------------- #
# Baseline vs Intervention vs Ablation Tests
# --------------------------------------------------------------------------- #
def test_baseline_mode_always_applies_transition():
    """Baseline naive checklist applies transition regardless of flaws."""
    # Even on offline conflict, baseline advances
    conflict_input = {
        "actor": {"role": "student", "owns_project": False},
        "project": {"reflection_completed": False, "version": 5},
        "transition": {"action": "submit", "expected_version": 1, "rationale": ""},
    }
    result = run_policy(conflict_input, mode="baseline", config={})
    assert result["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert result["transition_applied"] is True
    assert result["policy_version"] == "ln10-baseline-v1"


def test_ablation_disable_reflection():
    """Ablation disabling reflection allows missing rationale and skipped reflection."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"reflection_completed": False, "version": 3},
        "transition": {"action": "submit", "expected_version": 3, "rationale": ""},
    }
    result = run_policy(
        scenario_input, mode="ablation", config={"disable_reflection": True}
    )
    assert result["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert result["transition_applied"] is True


def test_ablation_disable_concurrency():
    """Ablation disabling concurrency allows stale version."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"reflection_completed": True, "version": 3},
        "transition": {
            "action": "revise_plan",
            "expected_version": 1,
            "rationale": "Valid reason",
        },
    }
    result = run_policy(
        scenario_input, mode="ablation", config={"disable_concurrency": True}
    )
    assert result["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert result["transition_applied"] is True


def test_ablation_disable_ownership():
    """Ablation disabling ownership allows non-owners."""
    scenario_input = {
        "actor": {"role": "student", "owns_project": False},
        "project": {"reflection_completed": True, "version": 3},
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "rationale": "Valid reason",
        },
    }
    result = run_policy(
        scenario_input, mode="ablation", config={"disable_ownership": True}
    )
    assert result["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert result["transition_applied"] is True


# --------------------------------------------------------------------------- #
# Fixture Conformance Tests
# --------------------------------------------------------------------------- #
def test_concrete_fixture_sample_conformance():
    """Test intervention agreement with oracle over a sample of concrete fixtures."""
    assert FIXTURE_PATH.exists(), f"Mandatory fixture missing (fail-closed): {FIXTURE_PATH}"

    with open(FIXTURE_PATH, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]

    # Test at least 50 sample lines across diverse fault IDs
    samples = lines[:50]
    for case in samples:
        inp = case["input"]
        expected = case["oracle"]["expected_decision"]
        res = run_policy(inp, mode="intervention", config={})
        assert res["decision"] == expected, f"Failed case {case['case_id']} ({case['fault_id']})"
        if case["fault_id"] == "nominal":
            assert res["transition_applied"] is True
        else:
            assert res["transition_applied"] is False


def test_metamorphic_insensitivity_to_irrelevant_fields():
    """Verify policy decisions are invariant to extraneous learner profile fields."""
    base_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nguồn mới làm thay đổi phạm vi đề xuất",
        },
    }

    # Add extraneous fields
    input_with_extras = dict(base_input)
    input_with_extras["learner"] = {
        "access": "standard",
        "competencies": {"S1": 0.99, "S2": 0.01},
        "xp": 99999,
    }
    input_with_extras["ui_theme"] = "dark_imperial"

    res_base = run_policy(base_input, mode="intervention", config={})
    res_extras = run_policy(input_with_extras, mode="intervention", config={})

    assert res_base["decision"] == res_extras["decision"]
    assert res_base["transition_applied"] == res_extras["transition_applied"]
    assert res_base["conflict_detected"] == res_extras["conflict_detected"]


def test_all_720_concrete_fixture_conformance():
    """Verify 100% agreement (720/720) on concrete test fixtures in intervention mode."""
    assert FIXTURE_PATH.is_file(), f"Mandatory fixture missing (fail-closed): {FIXTURE_PATH}"

    with open(FIXTURE_PATH, encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    assert len(cases) == 720, f"Expected 720 cases in fixture, found {len(cases)}"
    matches = 0
    for case in cases:
        inp = case["input"]
        expected = case["oracle"]["expected_decision"]
        res = run_policy(inp, mode="intervention", config={})
        assert res["decision"] == expected, f"Mismatch on {case['case_id']} ({case['fault_id']})"
        assert isinstance(res["transition_applied"], bool)
        assert isinstance(res["conflict_detected"], bool)
        assert isinstance(res["reflection_completed"], bool)
        assert isinstance(res["ownership_verified"], bool)
        if case["fault_id"] == "nominal":
            assert res["transition_applied"] is True
        else:
            assert res["transition_applied"] is False
        matches += 1

    assert matches == 720


def test_five_study_conditions_configs_experiments():
    """Verify all 5 conditions specified in configs/experiments.json:
    - B0: baseline (linear checklist auto-advance)
    - I1: intervention (SRL cyclical reflection state machine)
    - A1: ablation disable_reflection (and alias free_navigation)
    - A2: ablation disable_concurrency (and alias no_reflection_gate)
    - A3: ablation disable_ownership (and alias skip_forethought)
    """
    cfg_file = get_experiments_config_path()
    assert cfg_file.is_file(), f"experiments.json not found at {cfg_file}"
    matrix = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert "LN-10" in matrix["studies"], "LN-10 study missing from experiments.json"
    ln10_entry = matrix["studies"]["LN-10"]
    assert ln10_entry["adapter"] == "research.integrations.ln10:run_policy"

    runs = {r["id"]: r for r in ln10_entry["runs"]}
    assert set(runs.keys()) == {"B0", "I1", "A1", "A2", "A3"}

    # Base nominal scenario
    nominal_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {
            "goal": "evidence_based_conservation_proposal",
            "reflection_completed": True,
            "state": "monitoring",
            "version": 3,
        },
        "transition": {
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "Nguồn mới làm thay đổi phạm vi đề xuất",
        },
    }

    # 1. B0: Baseline (mode="baseline", config={})
    b0_run = runs["B0"]
    assert b0_run["mode"] == "baseline"
    res_b0 = run_policy(nominal_input, mode=b0_run["mode"], config=b0_run["config"])
    assert res_b0["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_b0["transition_applied"] is True
    assert res_b0["policy_version"] == "ln10-baseline-v1"

    # 2. I1: Intervention (mode="intervention", config={})
    i1_run = runs["I1"]
    assert i1_run["mode"] == "intervention"
    res_i1 = run_policy(nominal_input, mode=i1_run["mode"], config=i1_run["config"])
    assert res_i1["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_i1["transition_applied"] is True
    assert res_i1["policy_version"] == "ln10-intervention-srl-v1"

    # 3. A1: Ablation disable_reflection (config={"disable_reflection": true}) & alias free_navigation
    a1_run = runs["A1"]
    assert a1_run["mode"] == "ablation"
    assert a1_run["config"].get("disable_reflection") is True
    no_rationale_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"reflection_completed": True, "version": 3},
        "transition": {"action": "revise_plan", "expected_version": 3, "rationale": ""},
    }
    res_a1_spec = run_policy(no_rationale_input, mode="ablation", config=a1_run["config"])
    assert res_a1_spec["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a1_spec["transition_applied"] is True
    # Test alias free_navigation
    res_a1_alias = run_policy(no_rationale_input, mode="ablation", config={"free_navigation": True})
    assert res_a1_alias["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a1_alias["transition_applied"] is True

    # 4. A2: Ablation disable_concurrency (config={"disable_concurrency": true}) & alias no_reflection_gate
    a2_run = runs["A2"]
    assert a2_run["mode"] == "ablation"
    assert a2_run["config"].get("disable_concurrency") is True
    stale_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"reflection_completed": True, "version": 3},
        "transition": {"action": "revise_plan", "expected_version": 1, "rationale": "Valid"},
    }
    res_a2_spec = run_policy(stale_input, mode="ablation", config=a2_run["config"])
    assert res_a2_spec["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a2_spec["transition_applied"] is True
    # Test alias no_reflection_gate
    unreflected_input = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"reflection_completed": False, "version": 3},
        "transition": {"action": "submit", "expected_version": 3, "rationale": "Valid"},
    }
    res_a2_alias = run_policy(unreflected_input, mode="ablation", config={"no_reflection_gate": True})
    assert res_a2_alias["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a2_alias["transition_applied"] is True

    # 5. A3: Ablation disable_ownership (config={"disable_ownership": true}) & alias skip_forethought
    a3_run = runs["A3"]
    assert a3_run["mode"] == "ablation"
    assert a3_run["config"].get("disable_ownership") is True
    nonowner_input = {
        "actor": {"role": "student", "owns_project": False},
        "project": {"reflection_completed": True, "version": 3},
        "transition": {"action": "revise_plan", "expected_version": 3, "rationale": "Valid"},
    }
    res_a3_spec = run_policy(nonowner_input, mode="ablation", config=a3_run["config"])
    assert res_a3_spec["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a3_spec["transition_applied"] is True
    # Test alias skip_forethought
    res_a3_alias = run_policy(no_rationale_input, mode="ablation", config={"skip_forethought": True})
    assert res_a3_alias["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_a3_alias["transition_applied"] is True


def test_edge_cases_empty_and_malformed_inputs():
    """Verify policy handles empty/missing/malformed inputs safely without uncaught exceptions."""
    # 1. Completely empty dict
    res_empty = run_policy({}, mode="intervention", config={})
    assert res_empty["decision"] == DecisionCode.DENY_TRANSITION.value
    assert res_empty["transition_applied"] is False

    # 2. None input (gracefully coerced)
    res_none = run_policy(None, mode="intervention", config={})  # type: ignore
    assert res_none["decision"] == DecisionCode.DENY_TRANSITION.value
    assert res_none["transition_applied"] is False

    # 3. Baseline mode with empty input
    res_b0_empty = run_policy({}, mode="baseline", config={})
    assert res_b0_empty["decision"] == DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value
    assert res_b0_empty["transition_applied"] is True

    # 4. Unknown mode raises ValueError
    with pytest.raises(ValueError, match="Unknown mode"):
        run_policy({}, mode="unsupported_mode", config={})
