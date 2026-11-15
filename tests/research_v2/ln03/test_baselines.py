"""Baselines: B0 sanity behaviour and C1 Leitner classical policy tests."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03.baselines_b0 import predict_batch as b0
from research_v2.methods.ln03.baselines_c1 import predict_batch as c1
from research_v2.methods.ln03.errors import PolicyConfigError

from ln03_helpers import make_features


def _inp(case_id: str, **overrides) -> StudyInput:
    return StudyInput("LN-03", case_id, "test", "grp-base", make_features(**overrides))


def test_b0_schedules_everything_including_invalid_states():
    cases = [
        _inp("LN-03-B0-1", fact_prerequisite_mastered=False),
        _inp("LN-03-B0-2", review_card={"source_verified": False}),
        _inp("LN-03-B0-3", scheduler_weight=float("nan")),
        _inp("LN-03-B0-4", review_card={"due_utc": "2026-11-20T12:00:00Z"}),
    ]
    assert all(p.decision == "schedule_eligible" for p in b0(cases))


def test_b0_negative_control_earns_imperfect_score_on_oracle():
    """Golden-case QA: an always-accept system must never earn perfect utility."""
    from research_v2.contracts.input_masking import mask_case_input

    from ln03_helpers import load_t3_gold, load_t3_inputs

    inputs = [
        StudyInput("LN-03", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    gold = load_t3_gold()
    correct = sum(1 for p in b0(inputs) if gold[p.case_id] == p.decision)
    assert correct < len(gold)  # must fail the 96 non-eligible oracle cases


def test_c1_schedules_classical_boxes():
    features = make_features()
    features["review_card"]["repetitions"] = 9  # box 5
    pred = c1([_inp("LN-03-C1-1", **{"review_card": {"repetitions": 9}})])[0]
    assert pred.decision == "schedule_eligible"
    assert "leitner_box_5" in pred.reason_codes


def test_c1_box_progression_monotonic():
    p1 = c1([_inp("LN-03-C1-2", **{"review_card": {"repetitions": 0}})])[0]
    p5 = c1([_inp("LN-03-C1-3", **{"review_card": {"repetitions": 8}})])[0]
    assert "leitner_box_1" in p1.reason_codes
    assert "leitner_box_5" in p5.reason_codes


def test_c1_ignores_source_verification_by_design():
    pred = c1([_inp("LN-03-C1-4", review_card={"source_verified": False})])[0]
    assert pred.decision == "schedule_eligible"  # classical scheduler has no epistemic gate


def test_c1_invalid_gradations_fail_closed():
    with pytest.raises(PolicyConfigError, match="5-element"):
        c1([_inp("LN-03-C1-5")], {"leitner_gradations": [1, 2, 3]})
    with pytest.raises(PolicyConfigError, match="positive"):
        c1([_inp("LN-03-C1-6")], {"leitner_gradations": [1, 2, 3, 4, -5]})


def test_c1_optional_due_check_when_configured():
    case = _inp("LN-03-C1-7", review_card={"due_utc": "2026-11-20T12:00:00Z"})
    assert c1([case])[0].decision == "schedule_eligible"  # default: due-agnostic
    assert c1([case], {"postpone_if_not_due": True})[0].decision == "postpone"
