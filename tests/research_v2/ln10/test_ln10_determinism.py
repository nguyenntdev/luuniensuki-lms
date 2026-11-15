"""Determinism / pairing: repeated identical input yields byte-identical output."""
from __future__ import annotations

from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes
from tests.research_v2.ln10.ln10_helpers import (
    conflicting_edits_features,
    make_features,
    make_input,
    premature_submit_features,
)
from research_v2.methods.ln10.proposed import predict_batch

CASES = [
    ("nominal", make_features()),
    ("conflict", conflicting_edits_features()),
    ("premature", premature_submit_features()),
]


def test_repeated_seed_same_input_hash_stable_output():
    inputs = [make_input(feats, case_id=cid) for cid, feats in CASES]
    base = [p.to_dict() for p in predict_batch(inputs, {"seed": 11})]
    for _ in range(3):
        repeat = [p.to_dict() for p in predict_batch(inputs, {"seed": 11})]
        assert repeat == base


def test_seed_change_does_not_change_decisions():
    """The policy is deterministic; the seed must not be a hidden random input."""
    inputs = [make_input(feats, case_id=cid) for cid, feats in CASES]
    base = [p.to_dict() for p in predict_batch(inputs, {"seed": 11})]
    for seed in (23, 37, 101, 211):
        assert [p.to_dict() for p in predict_batch(inputs, {"seed": seed})] == base


def test_feature_key_order_does_not_change_output():
    import copy

    inputs = [make_input(feats, case_id=cid) for cid, feats in CASES]
    base = [p.to_dict() for p in predict_batch(inputs, {"seed": 11})]
    reordered = []
    for inp in inputs:
        feats = copy.deepcopy(dict(inp.features))
        flipped = dict(reversed(list(feats.items())))
        reordered.append(make_input(flipped, case_id=inp.case_id))
    assert [p.to_dict() for p in predict_batch(reordered, {"seed": 11})] == base


def test_canonical_input_hash_matches_fixture_recipe(t3_inputs):
    """input_sha256 in the T3 fixtures equals sha256 of canonical features."""
    row = t3_inputs[0]
    assert sha256_bytes(canonical_json(row["input"])) == row["input_sha256"]
