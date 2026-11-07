# -*- coding: utf-8 -*-
"""Comprehensive test suite for Study LN-08: Diagnostic Feedback Engine.

Covers:
- Taxonomy models and data contracts (P01)
- Pedagogical invariants INV-LN-08-01 through INV-LN-08-05 (P02)
- Negation detection and contradiction classification (ALG-LN-08-01 / ALG-LN-08-04)
- Source linkage and citation locator verification (ALG-LN-08-03)
- Synonym equivalence and semantic preservation (RULE-LN-08-04)
- Partial reasoning classification (RULE-LN-08-05)
- Baseline naive keyword matcher vulnerabilities (false positives on negation, false negatives on synonyms)
- Intervention vs Baseline contrast
- All 5 conditions: B0, I1, A1 (keyword_only), A2 (disable_negation), A3 (no_source_grounding / disable_source_link)
- Metamorphic pair transformations
- Edge cases and boundary robustness
- 720-scenario concrete fixture conformance
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.domain.history_error_taxonomy import (
    DiagnosticCategory,
    DiagnosticDecision,
    HistoricalErrorType,
)
from research.feedback.diagnostic_feedback import (
    has_negation,
    has_synonym_equivalence,
    is_partial_reasoning,
    normalize_text,
    verify_source_linkage,
)
from research.integrations.ln08 import run_policy


# --------------------------------------------------------------------------- #
# Fixtures & Sample Payloads
# --------------------------------------------------------------------------- #

@pytest.fixture
def base_scenario_input():
    return {
        "case_id": "LN-08-TC-SAMPLE",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "evidence": {
            "claim_id": "CLAIM-SYN-001",
            "source_id": "SOURCE-SYN-001",
            "verified": True,
        },
        "expected_conclusion": "spatial_ritual_relationship",
        "language": "vi",
        "learner": {
            "access": "standard",
            "competencies": {"S1": 0.5, "S2": 0.5, "S3": 0.5, "S4": 0.5},
            "profile_id": "SYN-TEST",
            "synthetic": True,
        },
        "prompt": "Dựa vào nguồn, hãy giải thích mối quan hệ kiến trúc và nghi lễ.",
    }


# --------------------------------------------------------------------------- #
# Unit Tests: Linguistic Analysis & Preprocessing
# --------------------------------------------------------------------------- #

def test_unicode_normalization_preserves_content():
    raw = "  Ngọ   Môn  thuộc   trục  nghi   lễ.  "
    norm = normalize_text(raw)
    assert norm == "Ngọ Môn thuộc trục nghi lễ."


def test_negation_detection_positive_cases():
    test_cases = [
        "Ngọ Môn không thuộc trục nghi lễ, trái với thông tin được cung cấp.",
        "Công trình này không nằm trên tuyến nghi thức.",
        "Điện Thái Hòa chẳng phải là trung tâm nghi lễ.",
        "Tư liệu phủ nhận quan hệ không gian này.",
        "Nhận định trên là sai lệch so với nguồn sử liệu.",
        "Ngược lại với tư liệu, công trình này xây năm khác.",
    ]
    for text in test_cases:
        negated, token = has_negation(text)
        assert negated, f"Expected negation detected in: '{text}'"
        assert token is not None


def test_negation_detection_negative_cases():
    test_cases = [
        "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn.",
        "Theo tư liệu, vị trí Ngọ Môn nằm trên tuyến không gian phục vụ nghi thức.",
        "Điện Thái Hòa là nơi cử hành các đại lễ triều đình.",
    ]
    for text in test_cases:
        negated, token = has_negation(text)
        assert not negated, f"Did not expect negation in: '{text}'"
        assert token is None


def test_synonym_equivalence_detection():
    synonym_text = "Theo tư liệu, vị trí Ngọ Môn nằm trên tuyến không gian phục vụ nghi thức."
    assert has_synonym_equivalence(synonym_text)

    canonical_text = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    assert not has_synonym_equivalence(canonical_text)


def test_partial_reasoning_detection():
    partial_text = "Ngọ Môn là một công trình kiến trúc."
    assert is_partial_reasoning(partial_text)

    complete_text = "Ngọ Môn là một công trình kiến trúc thuộc trục nghi lễ."
    assert not is_partial_reasoning(complete_text)


def test_source_linkage_verification():
    valid_evidence = {"source_id": "SOURCE-SYN-001", "verified": True}
    ok, err = verify_source_linkage(valid_evidence)
    assert ok
    assert err is None

    wrong_evidence = {"source_id": "SOURCE-SYN-WRONG", "verified": True}
    ok, err = verify_source_linkage(wrong_evidence)
    assert not ok
    assert err == "source_mismatch_untrusted"

    unverified_evidence = {"source_id": "SOURCE-SYN-001", "verified": False}
    ok, err = verify_source_linkage(unverified_evidence)
    assert not ok
    assert err == "source_unverified"

    empty_evidence = {}
    ok, err = verify_source_linkage(empty_evidence)
    assert not ok
    assert err == "missing_source_locator"


# --------------------------------------------------------------------------- #
# Integration Tests: Intervention Policy (All 5 Fault Archetypes)
# --------------------------------------------------------------------------- #

def test_intervention_nominal(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-001"
    base_scenario_input["evidence"]["verified"] = True

    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert result["diagnostic_category"] == DiagnosticCategory.SUPPORTED.value
    assert "Đáp án và nguồn phù hợp" in result["reason_codes"]


def test_intervention_logical_negation(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn không thuộc trục nghi lễ, trái với thông tin được cung cấp."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-001"

    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.CLASSIFY_CONTRADICTION.value
    assert result["diagnostic_category"] == DiagnosticCategory.CONTRADICTION.value
    assert "Phủ định biến câu đúng thành sai" in result["reason_codes"]


def test_intervention_source_mismatch(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-WRONG"

    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.CLASSIFY_SOURCE_ERROR.value
    assert result["diagnostic_category"] == DiagnosticCategory.SOURCE_ERROR.value
    assert "Nguồn không hỗ trợ nhận định" in result["reason_codes"]


def test_intervention_synonym_equivalence(base_scenario_input):
    base_scenario_input["answer"] = "Theo tư liệu, vị trí Ngọ Môn nằm trên tuyến không gian phục vụ nghi thức."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-001"

    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.PRESERVE_SEMANTICS.value
    assert result["diagnostic_category"] == DiagnosticCategory.SUPPORTED_EQUIVALENT.value
    assert "Diễn đạt khác nhưng cùng mệnh đề" in result["reason_codes"]


def test_intervention_partial_reasoning(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn là một công trình kiến trúc."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-001"

    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.FEEDBACK_INCOMPLETE.value
    assert result["diagnostic_category"] == DiagnosticCategory.INCOMPLETE.value
    assert "Câu trả lời đúng một phần" in result["reason_codes"]


# --------------------------------------------------------------------------- #
# Baseline Tests & Contrast (INV-LN-08-01 Invariant Enforcement)
# --------------------------------------------------------------------------- #

def test_baseline_fooled_by_negation(base_scenario_input):
    """INV-LN-08-01: Baseline naive keyword match accepts negated answer as correct."""
    base_scenario_input["answer"] = "Ngọ Môn không thuộc trục nghi lễ, trái với thông tin được cung cấp."

    result = run_policy(base_scenario_input, mode="baseline", config={})
    assert result["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert result["false_keyword_match"] is True
    assert result["diagnostic_category"] == DiagnosticCategory.KEYWORD_MATCH.value


def test_baseline_fooled_by_source_mismatch(base_scenario_input):
    """Baseline ignores source citation validity, accepting fabricated citation."""
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-WRONG"

    result = run_policy(base_scenario_input, mode="baseline", config={})
    assert result["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert result["diagnostic_category"] == DiagnosticCategory.KEYWORD_MATCH.value


def test_baseline_fails_synonym_equivalence(base_scenario_input):
    """Baseline penalizes students who express equivalent concepts using authentic synonyms."""
    base_scenario_input["answer"] = "Theo tư liệu, vị trí Ngọ Môn nằm trên tuyến không gian phục vụ nghi thức."

    result = run_policy(base_scenario_input, mode="baseline", config={})
    assert result["decision"] == DiagnosticDecision.FEEDBACK_INCOMPLETE.value
    assert result["diagnostic_category"] == DiagnosticCategory.KEYWORD_MISSING.value


# --------------------------------------------------------------------------- #
# Metamorphic Transformation Tests
# --------------------------------------------------------------------------- #

def test_metamorphic_pair_negation_inversion(base_scenario_input):
    """Pairwise test: inserting negation inverts decision from supported to contradiction."""
    aff_input = dict(base_scenario_input)
    aff_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    aff_res = run_policy(aff_input, mode="intervention", config={})

    neg_input = dict(base_scenario_input)
    neg_input["answer"] = "Ngọ Môn không thuộc trục nghi lễ, trái với thông tin được cung cấp."
    neg_res = run_policy(neg_input, mode="intervention", config={})

    assert aff_res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert neg_res["decision"] == DiagnosticDecision.CLASSIFY_CONTRADICTION.value


def test_metamorphic_pair_source_swap(base_scenario_input):
    """Pairwise test: swapping source to untrusted flips decision to classify_source_error."""
    valid_input = dict(base_scenario_input)
    valid_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    valid_input["evidence"] = {"source_id": "SOURCE-SYN-001", "verified": True}
    res_valid = run_policy(valid_input, mode="intervention", config={})

    invalid_input = dict(base_scenario_input)
    invalid_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    invalid_input["evidence"] = {"source_id": "SOURCE-SYN-WRONG", "verified": True}
    res_invalid = run_policy(invalid_input, mode="intervention", config={})

    assert res_valid["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert res_invalid["decision"] == DiagnosticDecision.CLASSIFY_SOURCE_ERROR.value


# --------------------------------------------------------------------------- #
# All 5 Conditions: B0, I1, A1, A2, A3
# --------------------------------------------------------------------------- #

def test_condition_b0_baseline(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    res = run_policy(base_scenario_input, mode="baseline", config={})
    assert "diagnostic_category" in res
    assert res["policy_version"].startswith("baseline")


def test_condition_i1_intervention(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    res = run_policy(base_scenario_input, mode="intervention", config={})
    assert res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value
    assert res["diagnostic_category"] == DiagnosticCategory.SUPPORTED.value


def test_condition_a1_keyword_only(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn không thuộc trục nghi lễ."
    res = run_policy(base_scenario_input, mode="ablation", config={"ablation": "keyword_only"})
    assert res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value


def test_condition_a2_disable_negation(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn không thuộc trục nghi lễ, trái với thông tin được cung cấp."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-001"
    res = run_policy(base_scenario_input, mode="ablation", config={"ablation": "disable_negation"})
    assert res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value


def test_condition_a3_disable_source_link(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-WRONG"
    res = run_policy(base_scenario_input, mode="ablation", config={"ablation": "disable_source_link"})
    assert res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value


def test_condition_a3_no_source_grounding_alias(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    base_scenario_input["evidence"]["source_id"] = "SOURCE-SYN-WRONG"
    res = run_policy(base_scenario_input, mode="ablation", config={"ablation": "no_source_grounding"})
    assert res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value


# --------------------------------------------------------------------------- #
# Robustness & Boundary Conditions
# --------------------------------------------------------------------------- #

def test_empty_answer_abstains(base_scenario_input):
    base_scenario_input["answer"] = ""
    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.ABSTAIN.value
    assert result["diagnostic_category"] == DiagnosticCategory.UNCLASSIFIED.value


def test_unknown_gibberish_abstains(base_scenario_input):
    base_scenario_input["answer"] = "Lorem ipsum dolor sit amet."
    result = run_policy(base_scenario_input, mode="intervention", config={})
    assert result["decision"] == DiagnosticDecision.ABSTAIN.value
    assert result["diagnostic_category"] == DiagnosticCategory.UNCLASSIFIED.value


def test_pure_function_determinism(base_scenario_input):
    base_scenario_input["answer"] = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn."
    res1 = run_policy(base_scenario_input, mode="intervention", config={})
    res2 = run_policy(base_scenario_input, mode="intervention", config={})
    assert res1 == res2


# --------------------------------------------------------------------------- #
# Concrete Fixture Batch Conformance (720 Synthetic Scenarios)
# --------------------------------------------------------------------------- #

def test_concrete_fixture_conformance():
    fixture_path = (
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-08_concrete.jsonl"
    )
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found at {fixture_path}")

    total = 0
    intervention_matches = 0
    baseline_negation_fooled = 0
    baseline_synonym_rejected = 0

    with fixture_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total += 1
            expected = row["oracle"]["expected_decision"]
            fault_id = row["fault_id"]

            int_res = run_policy(row["input"], mode="intervention", config={})
            if int_res["decision"] == expected:
                intervention_matches += 1

            base_res = run_policy(row["input"], mode="baseline", config={})
            if fault_id == "logical_negation" and base_res["decision"] == DiagnosticDecision.FEEDBACK_SUPPORTED.value:
                baseline_negation_fooled += 1
            if fault_id == "synonym_equivalence" and base_res["decision"] != expected:
                baseline_synonym_rejected += 1

    assert total == 720
    assert intervention_matches == 720, f"Expected 720/720 matches, got {intervention_matches}"
    assert baseline_negation_fooled == 144, "All 144 negation cases should fool baseline"
    assert baseline_synonym_rejected == 144, "All 144 synonym cases should fail in baseline"
