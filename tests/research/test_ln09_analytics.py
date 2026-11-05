# -*- coding: utf-8 -*-
"""Automated tests for Study LN-09 (Learning Analytics & Teacher Intervention).

Verifies domain models, intervention rules, baseline comparisons, ablations,
and pedagogical invariants (INV-LN-09-01 to INV-LN-09-05).
"""
import json
from pathlib import Path
import pytest


from backend.domain.instructional_recommendations import (
    CompetencyArea,
    DecisionCode,
    DecisionSupportCard,
    INSTRUCTIONAL_ACTION_CATALOG,
    LearningSignal,
    PedagogicalNeed,
    ReasonCode,
    TeacherOverride,
    TeacherOverrideStatus,
    TeachingAction,
    check_data_freshness,
    check_evidence_verification,
    check_k_anonymity,
    check_signal_consistency,
    evaluate_instructional_recommendation,
)
from research.integrations.ln09 import run_policy
from research.teacher_analytics.intervention_rules import (
    POLICY_VERSION_ABLATION,
    POLICY_VERSION_BASELINE,
    POLICY_VERSION_INTERVENTION,
    evaluate_ablation_rules,
    evaluate_baseline_rules,
    evaluate_intervention_rules,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def nominal_input():
    return {
        "case_id": "TEST-TC-001",
        "candidate_intervention": "additional_source_comparison_activity",
        "class_context": {"grade": 12, "subject": "GDĐP", "synthetic": True},
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.2, "S2": 0.3, "S3": 0.1, "S4": 0.2},
            "is_new": False,
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "learning_evidence": [
            {"outcome": "spatial", "score": 0.2, "type": "quiz", "verified": True},
            {"outcome": "evidence_use", "score": 0.3, "type": "source_task", "verified": True},
        ],
        "observation_age_days": 1,
        "required_signal_types": ["quiz", "source_task"],
        "signals_conflict": False,
    }


@pytest.fixture
def missing_logs_input(nominal_input):
    inp = dict(nominal_input)
    inp["learning_evidence"] = []
    return inp


@pytest.fixture
def conflicting_signals_input(nominal_input):
    inp = dict(nominal_input)
    inp["signals_conflict"] = True
    return inp


@pytest.fixture
def unverified_task_input(nominal_input):
    inp = dict(nominal_input)
    inp["learning_evidence"] = [
        {"outcome": "spatial", "score": 0.2, "type": "quiz", "verified": True},
        {"outcome": "evidence_use", "score": 0.3, "type": "source_task", "verified": False},
    ]
    return inp


@pytest.fixture
def stale_mastery_input(nominal_input):
    inp = dict(nominal_input)
    inp["observation_age_days"] = 120
    return inp


# --------------------------------------------------------------------------- #
# Unit Tests: Intervention Policy Rules
# --------------------------------------------------------------------------- #
def test_intervention_nominal(nominal_input):
    """TEST-CORE-LN-09-01: nominal input -> propose_explained_action."""
    res = evaluate_intervention_rules(nominal_input)
    assert res.decision == DecisionCode.propose_explained_action.value
    assert ReasonCode.nominal.value in res.reason_codes
    assert res.action_proposed is True
    assert res.abstention_appropriate is False
    assert res.intervention_traceable is True
    assert res.policy_version == POLICY_VERSION_INTERVENTION
    assert res.candidate_intervention == "additional_source_comparison_activity"
    assert "Châu bản" in (res.rationale or "")


def test_intervention_missing_logs(missing_logs_input):
    """TEST-CORE-LN-09-02: missing logs -> abstain_missing_evidence (INV-LN-09-01)."""
    res = evaluate_intervention_rules(missing_logs_input)
    assert res.decision == DecisionCode.abstain_missing_evidence.value
    assert ReasonCode.missing_logs.value in res.reason_codes
    assert res.action_proposed is False
    assert res.abstention_appropriate is True


def test_intervention_conflicting_signals(conflicting_signals_input):
    """TEST-CORE-LN-09-03: conflicting signals -> abstain_conflict (INV-LN-09-05)."""
    res = evaluate_intervention_rules(conflicting_signals_input)
    assert res.decision == DecisionCode.abstain_conflict.value
    assert ReasonCode.conflicting_signals.value in res.reason_codes
    assert res.action_proposed is False
    assert res.abstention_appropriate is True


def test_intervention_unverified_task(unverified_task_input):
    """TEST-CORE-LN-09-04: unverified task -> abstain_unverified_source (INV-LN-09-02)."""
    res = evaluate_intervention_rules(unverified_task_input)
    assert res.decision == DecisionCode.abstain_unverified_source.value
    assert ReasonCode.unverified_task.value in res.reason_codes
    assert res.action_proposed is False
    assert res.abstention_appropriate is True


def test_intervention_stale_mastery(stale_mastery_input):
    """TEST-CORE-LN-09-05: stale observations (>30d) -> request_refresh."""
    res = evaluate_intervention_rules(stale_mastery_input)
    assert res.decision == DecisionCode.request_refresh.value
    assert ReasonCode.stale_mastery.value in res.reason_codes
    assert res.action_proposed is False
    assert res.abstention_appropriate is True


# --------------------------------------------------------------------------- #
# Unit Tests: Baseline Policy
# --------------------------------------------------------------------------- #
def test_baseline_proposes_unsupported_actions_on_faults(
    missing_logs_input, conflicting_signals_input, unverified_task_input, stale_mastery_input
):
    """Baseline blindly proposes action on missing, conflicting, unverified, and stale data."""
    for faulty_input in [missing_logs_input, conflicting_signals_input, unverified_task_input, stale_mastery_input]:
        res = evaluate_baseline_rules(faulty_input)
        assert res.action_proposed is True
        assert res.intervention_traceable is False
        assert res.decision == DecisionCode.propose_explained_action.value
        assert res.policy_version == POLICY_VERSION_BASELINE


def test_baseline_descriptive_only_mode(nominal_input):
    """Baseline with descriptive_only flag returns summary without action."""
    res = evaluate_baseline_rules(nominal_input, config={"descriptive_only": True})
    assert res.action_proposed is False
    assert res.decision == DecisionCode.descriptive_summary_only.value


# --------------------------------------------------------------------------- #
# Unit Tests: Ablations
# --------------------------------------------------------------------------- #
def test_ablation_descriptive_only(nominal_input):
    """Ablation 1: Dashboard with no suggestions."""
    res = evaluate_ablation_rules(nominal_input, config={"ablation_type": "descriptive_only"})
    assert res.decision == DecisionCode.descriptive_summary_only.value
    assert res.action_proposed is False
    assert res.policy_version == POLICY_VERSION_ABLATION


def test_ablation_no_freshness_source(unverified_task_input, stale_mastery_input):
    """Ablation 2: Removes freshness and source verification constraints."""
    config = {"ablation_type": "no_freshness_source"}
    res_unverified = evaluate_ablation_rules(unverified_task_input, config=config)
    assert res_unverified.decision == DecisionCode.propose_explained_action.value
    assert res_unverified.action_proposed is True

    res_stale = evaluate_ablation_rules(stale_mastery_input, config=config)
    assert res_stale.decision == DecisionCode.propose_explained_action.value
    assert res_stale.action_proposed is True


def test_ablation_no_rationale(nominal_input):
    """Ablation 3: Removes rationale explanation and curriculum traceability."""
    res = evaluate_ablation_rules(nominal_input, config={"ablation_type": "no_rationale"})
    assert res.decision == DecisionCode.propose_explained_action.value
    assert res.action_proposed is True
    assert res.intervention_traceable is False
    assert res.rationale == ""


# --------------------------------------------------------------------------- #
# Unit Tests: Invariants & Ethics (INV-LN-09-01 to INV-LN-09-05)
# --------------------------------------------------------------------------- #
def test_inv_ln_09_01_no_deficit_inference_from_missing_logs():
    """INV-LN-09-01: Zero submissions must not label student as low competency."""
    empty_input = {
        "learning_evidence": [],
        "observation_age_days": 1,
        "signals_conflict": False,
    }
    card = evaluate_instructional_recommendation(empty_input)
    assert card.decision == DecisionCode.abstain_missing_evidence.value
    assert "từ chối kết luận người học yếu kém" in card.rationale


def test_inv_ln_09_02_source_traceability():
    """INV-LN-09-02: Every proposed recommendation must trace back to curriculum anchor."""
    nominal = {
        "learning_evidence": [
            {"outcome": "spatial", "score": 0.2, "type": "quiz", "verified": True}
        ],
        "observation_age_days": 1,
        "signals_conflict": False,
        "candidate_intervention": "additional_spatial_orientation_activity",
    }
    card = evaluate_instructional_recommendation(nominal)
    assert card.action is not None
    assert card.action.curriculum_anchor_id == "GDDP12-HUE-HERITAGE-SPATIAL-S1"
    assert card.action.action_type == "additional_spatial_orientation_activity"
    assert card.intervention_traceable is True


def test_inv_ln_09_03_teacher_override():
    """INV-LN-09-03: Teacher can accept, reject, or modify any recommendation."""
    nominal = {
        "learning_evidence": [
            {"outcome": "evidence_use", "score": 0.2, "type": "source_task", "verified": True}
        ],
        "observation_age_days": 1,
        "signals_conflict": False,
        "candidate_intervention": "additional_source_comparison_activity",
    }
    card = evaluate_instructional_recommendation(nominal)
    assert card.action_proposed is True

    # 1. Teacher rejects
    reject_override = TeacherOverride(
        recommendation_id="REC-001",
        teacher_id="TEACHER-HUE-01",
        status=TeacherOverrideStatus.rejected,
        override_reason="Học sinh đã hoàn thành hoạt động tương tự tuần trước",
    )
    rejected_card = reject_override.apply(card)
    assert rejected_card.action_proposed is False
    assert rejected_card.decision == DecisionCode.descriptive_summary_only.value
    assert ReasonCode.teacher_rejected.value in rejected_card.reason_codes

    # 2. Teacher accepts
    accept_override = TeacherOverride(
        recommendation_id="REC-001",
        teacher_id="TEACHER-HUE-01",
        status=TeacherOverrideStatus.accepted,
        override_reason="Phù hợp với tiến độ tuần 14",
    )
    accepted_card = accept_override.apply(card)
    assert accepted_card.action_proposed is True
    assert ReasonCode.teacher_accepted.value in accepted_card.reason_codes

    # 3. Teacher modifies
    modify_override = TeacherOverride(
        recommendation_id="REC-001",
        teacher_id="TEACHER-HUE-01",
        status=TeacherOverrideStatus.modified,
        override_reason="Thay bằng bài đọc tư liệu mở rộng về Điện Kiến Trung",
        modified_action={
            "id": "ACT-CUSTOM-01",
            "action_type": "dien_kien_trung_reading",
            "objective": "Đọc tư liệu phục dựng Điện Kiến Trung",
            "curriculum_anchor_id": "GDDP12-HUE-KIEN-TRUNG",
        },
    )
    modified_card = modify_override.apply(card)
    assert modified_card.action is not None
    assert modified_card.action.id == "ACT-CUSTOM-01"
    assert ReasonCode.teacher_modified.value in modified_card.reason_codes


def test_inv_ln_09_04_k_anonymity_privacy_suppression():
    """INV-LN-09-04: If cohort size is below threshold (n < 5), suppress recommendations."""
    small_cohort_input = {
        "cohort_size": 3,
        "learning_evidence": [
            {"outcome": "spatial", "score": 0.2, "type": "quiz", "verified": True}
        ],
        "observation_age_days": 1,
        "signals_conflict": False,
    }
    card = evaluate_instructional_recommendation(small_cohort_input, k_threshold=5)
    assert card.k_anonymity_satisfied is False
    assert card.action_proposed is False
    assert card.decision == DecisionCode.abstain_missing_evidence.value
    assert ReasonCode.k_anonymity_violation.value in card.reason_codes


def test_inv_ln_09_05_conflict_visibility():
    """INV-LN-09-05: Conflicting signals are explicitly shown, not concealed."""
    conflict_input = {
        "learning_evidence": [
            {"outcome": "spatial", "score": 0.2, "type": "quiz", "verified": True},
            {"outcome": "spatial", "score": 0.9, "type": "field_work", "verified": True},
        ],
        "observation_age_days": 1,
        "signals_conflict": True,
    }
    card = evaluate_instructional_recommendation(conflict_input)
    assert card.decision == DecisionCode.abstain_conflict.value
    assert ReasonCode.conflicting_signals.value in card.reason_codes
    assert "mâu thuẫn" in card.rationale


# --------------------------------------------------------------------------- #
# Runner Adapter Contract Tests
# --------------------------------------------------------------------------- #
def test_run_policy_adapter_contract(nominal_input):
    """Adapter returns strictly compliant dict structure for run_benchmark.py."""
    res_inter = run_policy(nominal_input, mode="intervention", config={})
    assert isinstance(res_inter, dict)
    assert res_inter["decision"] == DecisionCode.propose_explained_action.value
    assert isinstance(res_inter["reason_codes"], list)
    assert isinstance(res_inter["policy_version"], str)
    assert isinstance(res_inter["action_proposed"], bool)
    assert res_inter["action_proposed"] is True

    res_base = run_policy(nominal_input, mode="baseline", config={})
    assert isinstance(res_base, dict)
    assert res_base["decision"] == DecisionCode.propose_explained_action.value
    assert res_base["action_proposed"] is True

    res_ablation = run_policy(nominal_input, mode="ablation", config={"ablation_type": "descriptive_only"})
    assert isinstance(res_ablation, dict)
    assert res_ablation["decision"] == DecisionCode.descriptive_summary_only.value
    assert res_ablation["action_proposed"] is False

    with pytest.raises(ValueError):
        run_policy(nominal_input, mode="invalid_mode", config={})


def test_concrete_fixture_sample_conformance():
    """Test against actual concrete fixtures from 04_FIXTURES/CONCRETE/LN-09_concrete.jsonl."""
    fixture_path = (
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-09_concrete.jsonl"
    )
    if not fixture_path.exists():
        pytest.skip("Concrete fixtures file not found")

    with fixture_path.open(encoding="utf-8") as f:
        # Test first 20 records
        for i, line in enumerate(f):
            if i >= 20:
                break
            record = json.loads(line)
            scenario_input = record["input"]
            expected = record["oracle"]["expected_decision"]

            result = run_policy(scenario_input, mode="intervention", config={})
            assert (
                result["decision"] == expected
            ), f"Mismatch in {record['case_id']} ({record['fault_id']}): expected {expected}, got {result['decision']}"
