# -*- coding: utf-8 -*-
"""Unit & Integration Tests for LN-02: Prerequisite-Aware Adaptive Learning.

Verifies:
- Cycle detection on competency dependency graphs (ALG-LN-02-01).
- Score validation and detection of score spoofing / out-of-range inputs (INV-LN-02-04).
- Abstention behavior for missing/unknown mastery without treating null as 0 (INV-LN-02-01).
- Hard prerequisite enforcement and remediation paths (INV-LN-02-02).
- Pure policy evaluation across baseline, intervention, and ablation modes.
- Callable research adapter interface research.integrations.ln02:run_policy.
"""
from __future__ import annotations

import math
import pytest

from backend.domain.competency_prerequisites import (
    CompetencyDimension,
    RecommendationDecision,
    ReasonCode,
    POLICY_VERSION,
    detect_dependency_cycle,
    validate_score_value,
    validate_all_scenario_scores,
    calculate_competency_coverage,
    evaluate_intervention,
    evaluate_baseline,
    evaluate_ablation,
)
from research.adaptive.prerequisite_policy import PrerequisitePolicy, evaluate_policy
from research.integrations.ln02 import run_policy


# --------------------------------------------------------------------------- #
# Fixture Helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def nominal_scenario() -> dict:
    return {
        "case_id": "TEST-NOMINAL-01",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "graph_edges": [["identify", "interpret"]],
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "mastery": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
        "score_observed": 0.7,
        "seed": 20261105,
        "target_task": {
            "id": "interpret-ngo-mon",
            "prerequisites": {"S1": 0.4},
            "target_competency": "S3",
        },
    }


@pytest.fixture
def missing_prereq_scenario() -> dict:
    return {
        "case_id": "TEST-MISSING-PREREQ-01",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "graph_edges": [["identify", "interpret"]],
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.1, "S2": 0.6, "S3": 0.2, "S4": 0.2},
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "mastery": {"S1": 0.1, "S2": 0.6, "S3": 0.2, "S4": 0.2},
        "score_observed": 0.7,
        "seed": 20261105,
        "target_task": {
            "id": "interpret-ngo-mon",
            "prerequisites": {"S1": 0.4},
            "target_competency": "S3",
        },
    }


@pytest.fixture
def missing_mastery_scenario() -> dict:
    return {
        "case_id": "TEST-MISSING-MASTERY-01",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "graph_edges": [["identify", "interpret"]],
        "learner": {
            "access": "standard",
            "competencies": {"S2": 0.6, "S3": 0.2, "S4": 0.2},  # S1 missing
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "mastery": {"S2": 0.6, "S3": 0.2, "S4": 0.2},  # S1 missing
        "score_observed": 0.7,
        "seed": 20261105,
        "target_task": {
            "id": "interpret-ngo-mon",
            "prerequisites": {"S1": 0.4},
            "target_competency": "S3",
        },
    }


@pytest.fixture
def invalid_score_scenario() -> dict:
    return {
        "case_id": "TEST-INVALID-SCORE-01",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "graph_edges": [["identify", "interpret"]],
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "mastery": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
        "score_observed": 1.8,  # > 1.0 invalid
        "seed": 20261105,
        "target_task": {
            "id": "interpret-ngo-mon",
            "prerequisites": {"S1": 0.4},
            "target_competency": "S3",
        },
    }


@pytest.fixture
def cyclic_graph_scenario() -> dict:
    return {
        "case_id": "TEST-CYCLIC-GRAPH-01",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "graph_edges": [["identify", "interpret"], ["interpret", "identify"]],
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
            "profile_id": "SYN-NOVICE",
            "synthetic": True,
        },
        "mastery": {"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2},
        "score_observed": 0.7,
        "seed": 20261105,
        "target_task": {
            "id": "interpret-ngo-mon",
            "prerequisites": {"S1": 0.4},
            "target_competency": "S3",
        },
    }


# --------------------------------------------------------------------------- #
# Unit Tests: Graph Cycles & Score Range Validation
# --------------------------------------------------------------------------- #
class TestGraphAndScoreValidation:
    def test_detect_cycle_acyclic(self):
        edges = [["a", "b"], ["b", "c"], ["c", "d"]]
        assert detect_dependency_cycle(edges) is False

    def test_detect_cycle_direct_2_node(self):
        edges = [["a", "b"], ["b", "a"]]
        assert detect_dependency_cycle(edges) is True

    def test_detect_cycle_3_node(self):
        edges = [["a", "b"], ["b", "c"], ["c", "a"]]
        assert detect_dependency_cycle(edges) is True

    def test_detect_cycle_self_loop(self):
        edges = [["a", "a"]]
        assert detect_dependency_cycle(edges) is True

    def test_detect_cycle_empty(self):
        assert detect_dependency_cycle([]) is False

    def test_validate_score_value_valid(self):
        for score in [0.0, 0.5, 1.0, 0.85, 0]:
            assert validate_score_value(score) is True

    def test_validate_score_value_out_of_bounds(self):
        for score in [-0.01, -1.0, 1.01, 1.8, 100.0]:
            assert validate_score_value(score) is False

    def test_validate_score_value_non_numeric(self):
        for score in [None, "0.5", math.nan, math.inf, True, False, []]:
            assert validate_score_value(score) is False

    def test_competency_coverage_calculation(self):
        assert calculate_competency_coverage({"S1": 0.8, "S2": 0.6, "S3": 0.2, "S4": 0.2}) == 1.0
        assert calculate_competency_coverage({"S1": 0.8, "S2": 0.6, "S3": 0.2}) == 0.75
        assert calculate_competency_coverage({"S1": 0.8}) == 0.25
        assert calculate_competency_coverage({}) == 0.0


# --------------------------------------------------------------------------- #
# Core Intervention Rules (TEST-CORE-LN-02-01 to 05)
# --------------------------------------------------------------------------- #
class TestInterventionRules:
    def test_nominal_recommends_eligible(self, nominal_scenario):
        result = evaluate_intervention(nominal_scenario)
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        assert ReasonCode.ELIGIBLE_RECOMMENDATION.value in result["reason_codes"]
        assert result["prerequisite_violated"] is False
        assert result["competency_coverage"] == 1.0
        assert result["unjustified_recommendation"] is False

    def test_missing_prerequisite_triggers_remediation(self, missing_prereq_scenario):
        result = evaluate_intervention(missing_prereq_scenario)
        assert result["decision"] == RecommendationDecision.remediate_first.value
        assert ReasonCode.PREREQUISITE_NOT_MET.value in result["reason_codes"]
        assert result["prerequisite_violated"] is False
        assert "S1" in result.get("unmet_prerequisites", [])

    def test_missing_mastery_abstains(self, missing_mastery_scenario):
        result = evaluate_intervention(missing_mastery_scenario)
        assert result["decision"] == RecommendationDecision.abstain_insufficient_data.value
        assert ReasonCode.INSUFFICIENT_COMPETENCY_DATA.value in result["reason_codes"]
        assert result["prerequisite_violated"] is False
        assert result["competency_coverage"] == 0.75

    def test_invalid_score_rejected(self, invalid_score_scenario):
        result = evaluate_intervention(invalid_score_scenario)
        assert result["decision"] == RecommendationDecision.reject_invalid_score.value
        assert ReasonCode.INVALID_SCORE_RANGE.value in result["reason_codes"]
        assert result["prerequisite_violated"] is False

    def test_cyclic_graph_rejected(self, cyclic_graph_scenario):
        result = evaluate_intervention(cyclic_graph_scenario)
        assert result["decision"] == RecommendationDecision.reject_cycle.value
        assert ReasonCode.CYCLE_DETECTED.value in result["reason_codes"]
        assert result["prerequisite_violated"] is False


# --------------------------------------------------------------------------- #
# Baseline vs Intervention Comparisons & Invariant Enforcement
# --------------------------------------------------------------------------- #
class TestBaselineVsIntervention:
    def test_baseline_violates_unmet_prerequisite(self, missing_prereq_scenario):
        # Baseline greedily recommends based on aggregate score 0.7 >= 0.5
        result = evaluate_baseline(missing_prereq_scenario)
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        # Because it recommended without prerequisites, prerequisite_violated is True!
        assert result["prerequisite_violated"] is True
        assert result["unjustified_recommendation"] is True

    def test_baseline_nominal_passes(self, nominal_scenario):
        result = evaluate_baseline(nominal_scenario)
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        assert result["prerequisite_violated"] is False
        assert result["unjustified_recommendation"] is False

    def test_intervention_blocks_violation(self, missing_prereq_scenario):
        result = evaluate_intervention(missing_prereq_scenario)
        assert result["decision"] == RecommendationDecision.remediate_first.value
        assert result["prerequisite_violated"] is False


# --------------------------------------------------------------------------- #
# Ablation Variants
# --------------------------------------------------------------------------- #
class TestAblationVariants:
    def test_ablation_no_prerequisites(self, missing_prereq_scenario):
        result = evaluate_ablation(missing_prereq_scenario, config={"variant": "no_prerequisites"})
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        assert ReasonCode.ABLATION_NO_PREREQUISITES.value in result["reason_codes"]
        assert result["prerequisite_violated"] is True

    def test_ablation_no_abstention(self, missing_mastery_scenario):
        # Without abstention, missing S1 is imputed as 0.0 -> fails threshold 0.4 -> remediate_first
        result = evaluate_ablation(missing_mastery_scenario, config={"variant": "no_abstention"})
        assert result["decision"] == RecommendationDecision.remediate_first.value
        assert ReasonCode.ABLATION_NO_ABSTENTION.value in result["reason_codes"]

    def test_ablation_single_latent_skill(self, missing_prereq_scenario):
        # Single latent skill collapses S1=0.1, S2=0.6, S3=0.2, S4=0.2 (avg = 0.275)
        # Average threshold is 0.4. Avg < 0.4 -> remediate
        result = evaluate_ablation(missing_prereq_scenario, config={"variant": "single_latent_skill"})
        assert result["decision"] == RecommendationDecision.remediate_first.value
        assert ReasonCode.ABLATION_COLLAPSED_LATENT.value in result["reason_codes"]

    def test_ablation_ignore_prerequisites_alias(self, missing_prereq_scenario):
        result = evaluate_ablation(missing_prereq_scenario, config={"variant": "ignore_prerequisites"})
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        assert result["prerequisite_violated"] is True

    def test_ablation_fixed_target_s3(self, nominal_scenario, missing_prereq_scenario):
        # In nominal_scenario, S3 is 0.2, threshold defaults to 0.4 -> remediate_first
        res1 = evaluate_ablation(nominal_scenario, config={"variant": "fixed_target_s3"})
        assert res1["decision"] == RecommendationDecision.remediate_first.value
        # If S3 >= 0.4, recommends eligible
        scenario_s3_met = dict(nominal_scenario)
        scenario_s3_met["mastery"] = dict(nominal_scenario["mastery"])
        scenario_s3_met["mastery"]["S3"] = 0.6
        res2 = evaluate_ablation(scenario_s3_met, config={"variant": "fixed_target_s3"})
        assert res2["decision"] == RecommendationDecision.recommend_eligible.value

    def test_ablation_disable_remediation(self, missing_prereq_scenario):
        result = evaluate_ablation(missing_prereq_scenario, config={"variant": "disable_remediation"})
        assert result["decision"] == RecommendationDecision.recommend_eligible.value
        assert result["prerequisite_violated"] is True

    def test_none_score_observed_handled_gracefully(self, nominal_scenario):
        scenario = dict(nominal_scenario)
        scenario["score_observed"] = None
        # baseline should not crash on None score_observed
        res_base = evaluate_baseline(scenario)
        assert res_base["decision"] in [RecommendationDecision.recommend_eligible.value, RecommendationDecision.remediate_first.value]
        # ablation should not crash on None score_observed
        res_ab = evaluate_ablation(scenario, config={"variant": "no_prerequisites"})
        assert res_ab["decision"] in [RecommendationDecision.recommend_eligible.value, RecommendationDecision.remediate_first.value]


# --------------------------------------------------------------------------- #
# Adapter Interface Compliance (research.integrations.ln02:run_policy)
# --------------------------------------------------------------------------- #
class TestAdapterInterface:
    def test_run_policy_intervention(self, nominal_scenario):
        res = run_policy(nominal_scenario, mode="intervention", config={})
        assert isinstance(res, dict)
        assert res["decision"] == "recommend_eligible"
        assert isinstance(res["reason_codes"], list)
        assert isinstance(res["policy_version"], str)
        assert isinstance(res["prerequisite_violated"], bool)
        assert res["prerequisite_violated"] is False
        assert "competency_coverage" in res

    def test_run_policy_baseline(self, missing_prereq_scenario):
        res = run_policy(missing_prereq_scenario, mode="baseline", config={})
        assert isinstance(res, dict)
        assert res["decision"] == "recommend_eligible"
        assert res["prerequisite_violated"] is True

    def test_run_policy_invalid_mode(self, nominal_scenario):
        with pytest.raises(ValueError, match="Unknown policy evaluation mode"):
            run_policy(nominal_scenario, mode="unsupported_mode", config={})


# --------------------------------------------------------------------------- #
# Metamorphic Property Tests
# --------------------------------------------------------------------------- #
class TestMetamorphicProperties:
    def test_metamorphic_increasing_prerequisite_score(self, missing_prereq_scenario):
        # Initial: S1 is 0.1 (< 0.4) -> remediate_first
        initial_res = run_policy(missing_prereq_scenario, mode="intervention", config={})
        assert initial_res["decision"] == RecommendationDecision.remediate_first.value

        # Perturbation: Increase S1 mastery to 0.5 (>= 0.4), keeping all else constant
        transformed = dict(missing_prereq_scenario)
        transformed["mastery"] = dict(missing_prereq_scenario["mastery"])
        transformed["mastery"]["S1"] = 0.5

        pert_res = run_policy(transformed, mode="intervention", config={})
        assert pert_res["decision"] == RecommendationDecision.recommend_eligible.value
        assert pert_res["prerequisite_violated"] is False
