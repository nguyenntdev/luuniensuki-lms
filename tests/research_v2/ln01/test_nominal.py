"""Nominal scenario: structured, valid decisions from every method entry point."""
from __future__ import annotations

from research_v2.contracts.types import StudyPrediction
from research_v2.methods.ln01.proposed import predict_batch as proposed_batch
from research_v2.methods.ln01.baselines import predict_batch_b0, predict_batch_c1

from ln01_helpers import make_input, make_features


def test_nominal_accepts_and_returns_typed_predictions():
    preds = proposed_batch([make_input()], {})
    assert len(preds) == 1
    pred = preds[0]
    assert isinstance(pred, StudyPrediction)
    assert pred.decision == "accept"
    assert pred.reason_codes and all(isinstance(rc, str) for rc in pred.reason_codes)
    assert pred.case_id == "case-nominal"


def test_all_methods_emit_one_prediction_per_input_with_matching_case_ids():
    inputs = [make_input("c1"), make_input("c2", make_features())]
    for fn in (proposed_batch, predict_batch_b0, predict_batch_c1):
        preds = fn(inputs, {})
        assert len(preds) == len(inputs)
        assert [p.case_id for p in preds] == ["c1", "c2"]


def test_negative_case_cycle_is_rejected_by_proposed():
    feats = make_features(prerequisites=[[0, 1], [1, 2], [2, 0]])
    preds = proposed_batch([make_input("cyc", feats)], {})
    assert preds[0].decision == "reject_cycle"


def test_always_reject_and_always_accept_controls_are_distinguishable():
    """Golden-case QA: a healthy method must separate positive from negative cases."""
    good = proposed_batch([make_input("good")], {})[0]
    bad_feats = make_features(
        prerequisites=[[0, 1], [1, 2], [2, 0]],
        curriculum_anchor={"grade10": ""},
    )
    bad = proposed_batch([make_input("bad", bad_feats)], {})[0]
    assert good.decision == "accept"
    assert bad.decision != "accept"
