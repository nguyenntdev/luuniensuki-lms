# -*- coding: utf-8 -*-
"""Automated tests for Study LN-10 (Self-Regulated Learning & Hue Heritage Projects)."""
from __future__ import annotations

import json
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

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
    / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
    / "04_FIXTURES"
    / "CONCRETE"
    / "LN-10_concrete.jsonl"
)


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
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture file {FIXTURE_PATH} not found")

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
