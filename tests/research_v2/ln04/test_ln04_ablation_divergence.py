"""Ablation divergence tests (LN-04).

Each ablation must flip exactly one mechanism and measurably diverge from the
proposed policy on cases that exercise that mechanism (spec 15_ABLATIONS C2/C3).
"""
from __future__ import annotations

from methods_helpers import (
    injection_question,
    load_gold,
    load_inputs,
    malicious_note,
    to_study_input,
    verified_nominal_features,
)
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln04 import ablations_a1, ablations_a2, ablations_a3, proposed


def _case(features: dict, case_id: str) -> StudyInput:
    return StudyInput(
        study_id="LN-04", case_id=case_id, split_id="test", group_id="grp-abl", features=features
    )


def _gold_by_case():
    return load_gold()


def test_a1_diverges_on_early_answer_requests():
    leak_rows = [
        row
        for row in load_inputs()
        if _gold_by_case()[row["case_id"]]["expected_decision"] == "restrict_leakage"
    ]
    inputs = [to_study_input(r) for r in leak_rows]
    proposed_preds = proposed.predict_batch(inputs)
    a1_preds = ablations_a1.predict_batch(inputs)
    divergent = sum(1 for p, a in zip(proposed_preds, a1_preds) if p.decision != a.decision)
    assert divergent > 0, "A1 must diverge from proposed on leakage-pressure cases"


def test_a2_diverges_on_unverified_source_cases():
    gap_rows = [
        row
        for row in load_inputs()
        if _gold_by_case()[row["case_id"]]["expected_decision"] == "abstain_source_gap"
    ]
    inputs = [to_study_input(r) for r in gap_rows]
    proposed_preds = proposed.predict_batch(inputs)
    a2_preds = ablations_a2.predict_batch(inputs)
    divergent = sum(1 for p, a in zip(proposed_preds, a2_preds) if p.decision != a.decision)
    assert divergent == len(gap_rows), "A2 must collapse every source-gap abstention"


def test_a3_diverges_on_injection_cases():
    inj_rows = [
        row
        for row in load_inputs()
        if _gold_by_case()[row["case_id"]]["expected_decision"] == "reject_injection"
    ]
    inputs = [to_study_input(r) for r in inj_rows]
    proposed_preds = proposed.predict_batch(inputs)
    a3_preds = ablations_a3.predict_batch(inputs)
    divergent = sum(1 for p, a in zip(proposed_preds, a3_preds) if p.decision != a.decision)
    assert divergent == len(inj_rows), "A3 must unblock every injection case"


def test_ablations_match_proposed_on_nominal_verified_cases():
    """Mechanism isolation: on nominal verified cases no ablated mechanism is
    exercised, so a1/a2/a3 must agree with proposed there."""
    nominal_rows = [
        row
        for row in load_inputs()
        if _gold_by_case()[row["case_id"]]["expected_decision"] == "hint_then_fade"
    ]
    inputs = [to_study_input(r) for r in nominal_rows]
    proposed_preds = proposed.predict_batch(inputs)
    for name, fn in (
        ("a1", ablations_a1),
        ("a2", ablations_a2),
        ("a3", ablations_a3),
    ):
        preds = fn.predict_batch(inputs)
        assert [p.decision for p in preds] == [p.decision for p in proposed_preds], name


def test_a2_on_malicious_note_only_channel_diverges():
    features = verified_nominal_features(
        question="Em cần tìm hiểu căn cứ sử liệu nào để giải thích vai trò của Thế Tổ Miếu?",
        retrieval={"source_ids": [], "source_status": "unverified"},
        retrieved_notes=malicious_note(),
    )
    p = proposed.predict_one(_case(features, "LN-04-TEST-ABL-NOTE-P"))
    a = ablations_a2.predict_one(_case(features, "LN-04-TEST-ABL-NOTE-A"))
    assert p.decision == "abstain_insufficient_source"
    assert a.decision != "abstain_insufficient_source"


def test_a3_on_malicious_note_injection_diverges():
    features = verified_nominal_features(
        question=injection_question(),
        retrieved_notes=malicious_note(),
    )
    p = proposed.predict_one(_case(features, "LN-04-TEST-ABL-INJ-P"))
    a = ablations_a3.predict_one(_case(features, "LN-04-TEST-ABL-INJ-A"))
    assert p.decision == "reject_injection"
    assert a.decision == "socratic_question"


def test_every_ablation_is_a_distinct_code_path_not_a_config_flag_of_proposed():
    """Spec N: baseline/ablation outputs must come from independent
    implementations, not the same predict function with different flags."""
    import research_v2.methods.ln04.ablations as abl
    import research_v2.methods.ln04.proposed as prop

    assert abl.predict_one_a1.__code__ is not prop.predict_one.__code__
    assert abl.predict_one_a2.__code__ is not prop.predict_one.__code__
    assert abl.predict_one_a3.__code__ is not prop.predict_one.__code__
