"""Mandatory counterexample: keyword-complete-but-reversed relation.

Spec 03.F Case 1 / spec 14.F: an answer that contains ALL canonical keywords
yet REVERSES the historical relation ("Ngọ Môn is NOT on the ritual axis")
MUST be classified as a contradiction - never feedback_supported. A pure
keyword matcher (B0/A1) accepts it; the proposed negation parser must not.
"""
from __future__ import annotations

from ln08_helpers import (
    KEYWORD_COMPLETE_REVERSED_EN,
    KEYWORD_COMPLETE_REVERSED_VI,
    make_features,
    make_input,
    policy_solve,
)


def test_vi_negated_answer_with_all_keywords_is_contradiction():
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)
    assert "trục nghi lễ" in features["answer"]  # sanity: keyword present
    assert policy_solve("proposed", features) == "classify_contradiction"


def test_en_negated_answer_with_all_keywords_is_contradiction():
    features = make_features(
        answer=KEYWORD_COMPLETE_REVERSED_EN,
        evidence_source=None,  # unused key ignored by make_features
    )
    assert "ritual axis" in features["answer"]
    assert policy_solve("proposed", features) == "classify_contradiction"


def test_negated_answer_is_never_feedback_supported():
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)
    assert policy_solve("proposed", features) != "feedback_supported"


def test_negated_answer_with_fabricated_source_reports_source_error_first():
    # Source verification precedes negation analysis in the decision chain.
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI, source_id="SOURCE-FABRICATED")
    assert policy_solve("proposed", features) == "classify_source_error"


def test_b0_and_a1_are_fooled_by_the_reversed_answer():
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)
    assert policy_solve("baselines_b0", features) == "feedback_supported"
    assert policy_solve("ablations_a1", features) == "feedback_supported"


def test_a2_no_negation_ablation_is_fooled_by_the_reversed_answer():
    features = make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)
    assert policy_solve("ablations_a2", features) == "feedback_supported"


def test_prediction_contract_carries_contradiction_with_negation_reason():
    from research_v2.methods.ln08.proposed import predict_one

    pred = predict_one(make_input("t-neg", make_features(answer=KEYWORD_COMPLETE_REVERSED_VI)))
    assert pred.decision == "classify_contradiction"
    assert any("logical_negation" in rc for rc in pred.reason_codes)
