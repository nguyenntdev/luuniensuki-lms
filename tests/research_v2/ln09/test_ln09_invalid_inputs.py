"""Malformed inputs must raise typed failures (ContractError), never silent
guessed fallbacks — for every method entry point."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln09 import ablations, ablations_a2, ablations_a3
from research_v2.methods.ln09.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln09.proposed import predict_batch as proposed_batch

from ln09_helpers import make_features, make_input

ALL_METHODS = (
    proposed_batch,
    predict_batch_b0,
    predict_batch_c1,
    ablations.predict_batch,
    ablations_a2.predict_batch,
    ablations_a3.predict_batch,
)


def test_features_not_a_mapping_raises():
    """The engine's own guard: a StudyInput whose features were swapped to a
    non-mapping after construction must raise a typed ContractError (the
    contract layer catches the common case upstream with its own error)."""
    inp = StudyInput("LN-09", "bad", "test", "g", {})
    object.__setattr__(inp, "features", ["nope"])
    with pytest.raises(ContractError, match="features must be a mapping"):
        proposed_batch([inp], {})


@pytest.mark.parametrize("fn", ALL_METHODS)
def test_missing_learning_evidence_key_is_treated_as_empty_not_error(fn):
    """learning_evidence absent (None) is legitimate missingness handled by the
    abstention branch, not a crash — but evidence present in wrong type raises."""
    feats = make_features()
    feats["learning_evidence"] = "not-a-list"
    with pytest.raises(ContractError, match="learning_evidence"):
        fn([make_input("bad-ev", feats)], {})


@pytest.mark.parametrize("fn", ALL_METHODS)
def test_evidence_row_not_mapping_raises(fn):
    feats = make_features(learning_evidence=["quiz 0.2"])
    with pytest.raises(ContractError, match="learning_evidence"):
        fn([make_input("bad-ev-row", feats)], {})


@pytest.mark.parametrize("fn", ALL_METHODS)
def test_evidence_missing_score_raises(fn):
    feats = make_features(learning_evidence=[{"type": "quiz", "verified": True}])
    with pytest.raises(ContractError, match="score"):
        fn([make_input("bad-score", feats)], {})


@pytest.mark.parametrize("fn", [proposed_batch, predict_batch_c1])
def test_evidence_score_out_of_range_raises(fn):
    feats = make_features(learning_evidence=[{"outcome": "spatial", "score": 1.5, "type": "quiz", "verified": True}])
    with pytest.raises(ContractError, match=r"score out of \[0,1\]"):
        fn([make_input("range", feats)], {})


@pytest.mark.parametrize("fn", ALL_METHODS)
def test_evidence_missing_type_raises(fn):
    feats = make_features(learning_evidence=[{"score": 0.2, "verified": True}])
    with pytest.raises(ContractError, match="type"):
        fn([make_input("bad-type", feats)], {})


@pytest.mark.parametrize("fn", ALL_METHODS)
def test_non_boolean_verified_raises(fn):
    feats = make_features(learning_evidence=[{"score": 0.2, "type": "quiz", "verified": "yes"}])
    with pytest.raises(ContractError, match="verified must be boolean"):
        fn([make_input("bad-verified", feats)], {})


def test_negative_age_raises():
    feats = make_features(observation_age_days=-3)
    with pytest.raises(ContractError, match="observation_age_days"):
        proposed_batch([make_input("neg-age", feats)], {})


def test_non_integer_age_raises():
    feats = make_features(observation_age_days="recent")
    with pytest.raises(ContractError, match="observation_age_days"):
        proposed_batch([make_input("str-age", feats)], {})


def test_bad_required_signal_types_raises():
    feats = make_features(required_signal_types="source_task")
    with pytest.raises(ContractError, match="required_signal_types"):
        proposed_batch([make_input("bad-req", feats)], {})


def test_bad_override_status_raises():
    feats = make_features(teacher_override={"status": "maybe"})
    with pytest.raises(ContractError, match="teacher_override"):
        proposed_batch([make_input("bad-override", feats)], {})


def test_non_string_candidate_raises():
    feats = make_features(candidate_intervention=42)
    with pytest.raises(ContractError, match="candidate_intervention"):
        proposed_batch([make_input("bad-cand", feats)], {})


def test_unanchored_candidate_abstains_not_fabricates():
    """A verified-evidence case whose candidate action has no curriculum anchor
    cannot be traced (INV-LN-09-02): explicit abstention, never fabrication."""
    feats = make_features(candidate_intervention="totally_made_up_activity")
    pred = proposed_batch([make_input("unanchored", feats)], {})[0]
    assert pred.decision == "abstain_unverified_source"
    assert "unsupported_intervention" in pred.reason_codes
