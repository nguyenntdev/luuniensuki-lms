"""Same-seed digest determinism: identical inputs -> identical predictions,
and the canonical input digest is stable across runs."""
from __future__ import annotations

import json

from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes, sha256_input
from research_v2.methods.ln01.proposed import predict_batch as proposed_batch
from research_v2.methods.ln01.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln01 import ablations

from ln01_helpers import make_features, make_input


def test_same_seed_same_digest_deterministic_proposed():
    inp_a = make_input("det-1", make_features(seed=11))
    inp_b = make_input("det-1", make_features(seed=11))
    digest_a = sha256_bytes(canonical_json(inp_a.features))
    digest_b = sha256_bytes(canonical_json(inp_b.features))
    assert digest_a == digest_b
    preds_a = proposed_batch([inp_a], {"seed": 11})
    preds_b = proposed_batch([inp_b], {"seed": 11})
    assert preds_a[0].to_dict() == preds_b[0].to_dict()


def test_different_seed_value_does_not_change_pure_decision():
    """The decision is a pure function of features; seed is provenance metadata
    and must not alter the emitted decision for identical features."""
    feats = make_features()
    preds = [proposed_batch([make_input("s", feats)], {"seed": s})[0].decision for s in (11, 23, 37)]
    assert preds == ["accept", "accept", "accept"]


def test_digest_changes_when_features_change():
    a = sha256_input(make_features())
    b = sha256_input(make_features(prerequisites=[[0, 1], [1, 2], [2, 3], [0, 3]]))
    assert a != b


def test_batch_predictions_stable_and_serializable():
    inputs = [make_input("p1"), make_input("p2", make_features(prerequisites=[[0, 1], [1, 0]]))]
    run1 = [p.to_dict() for p in proposed_batch(inputs, {})]
    run2 = [p.to_dict() for p in proposed_batch(inputs, {})]
    assert run1 == run2
    for row in run1:
        json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)
    for fn in (predict_batch_b0, predict_batch_c1, ablations.predict_batch):
        assert [p.to_dict() for p in fn(inputs, {})] == [p.to_dict() for p in fn(inputs, {})]
