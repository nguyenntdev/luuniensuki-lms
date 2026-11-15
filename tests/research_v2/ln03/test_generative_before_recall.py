"""Mandatory LN-03 counterexample: generative task before any stable fact recall.

Expected (PEDAGOGICAL_SPEC_DUAL_MODE): proposed must NOT assign the generative
explanation; it must remediate with fact retrieval. B0 fails this gate by
design (negative control). Ablation A2 also fails it (mechanism isolated).
"""
from __future__ import annotations

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.baselines_b0 import predict_batch as b0
from research_v2.methods.ln03.baselines_c1 import predict_batch as c1
from research_v2.methods.ln03.scenario import parse_case

from ln03_helpers import make_features


def _inp(**overrides) -> StudyInput:
    return StudyInput(
        study_id="LN-03",
        case_id=overrides.pop("case_id", "LN-03-CE-0001"),
        split_id="test",
        group_id="grp-ce-1",
        features=make_features(**overrides),
    )


def test_proposed_never_assigns_generative_before_stable_fact_recall():
    pred = proposed.predict_batch([_inp(fact_prerequisite_mastered=False)])[0]
    assert pred.decision == "assign_fact_retrieval"
    assert "missing_fact_base" in pred.reason_codes
    assert "RULE-LN-03-02" in pred.reason_codes


def test_proposed_unstable_repetition_history_blocks_generative():
    # Prerequisite flag true but observed repetitions below stability threshold.
    features = make_features()
    features["review_card"]["repetitions"] = 0
    pred = proposed.predict_batch(
        [StudyInput("LN-03", "LN-03-CE-0002", "test", "grp-ce-2", features)],
        {"fact_stability_min_repetitions": 2},
    )[0]
    assert pred.decision == "assign_fact_retrieval"
    assert "unstable_repetition_history" in pred.reason_codes


def test_proposed_missing_fact_base_rejected_not_guessed():
    features = make_features()
    del features["fact_prerequisite_mastered"]
    features["review_card"]["due_utc"] = "2026-11-02T12:00:00Z"
    try:
        proposed.predict_batch([StudyInput("LN-03", "LN-03-CE-0003", "test", "grp-ce-3", features)])
    except Exception as exc:
        assert type(exc).__name__ == "ScenarioError"
    else:
        raise AssertionError("missing fact base must raise typed ScenarioError, not default")


def test_b0_negative_control_violates_the_gate():
    pred = b0([_inp(fact_prerequisite_mastered=False)])[0]
    assert pred.decision == "schedule_eligible"  # always schedules: documented failure


def test_c1_leitner_downtakes_to_fact_retrieval_without_source_gate():
    # C1 keeps the prerequisite demotion but ignores unverified sources.
    pred = c1([_inp(fact_prerequisite_mastered=False, review_card={"source_verified": False})])[0]
    assert pred.decision == "assign_fact_retrieval"


def test_ablation_a2_reproduces_the_counterexample_failure():
    from research_v2.methods.ln03.ablations_a2 import predict_batch as a2

    pred = a2([_inp(fact_prerequisite_mastered=False)])[0]
    assert pred.decision == "schedule_eligible"  # gate disabled -> invalid assignment


def test_parse_case_generative_flag_consistency():
    case = parse_case("c1", make_features(fact_prerequisite_mastered=False))
    assert case.is_generative is True
    assert case.fact_prerequisite_mastered is False
