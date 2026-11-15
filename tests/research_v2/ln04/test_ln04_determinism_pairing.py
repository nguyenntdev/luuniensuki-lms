"""Determinism / pairing stability tests (LN-04).

Repeated runs with the same input SHA, config, and seed must yield byte-stable
predictions; per-case pairing is preserved for paired analysis.
"""
from __future__ import annotations

from methods_helpers import load_inputs, to_study_input
from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes
from research_v2.methods.ln04 import ablations_a1, ablations_a2, ablations_a3, baselines_b0, baselines_c1, proposed

METHODS = [
    ("proposed", proposed.predict_batch),
    ("baselines_b0", baselines_b0.predict_batch),
    ("baselines_c1", baselines_c1.predict_batch),
    ("ablations_a1", ablations_a1.predict_batch),
    ("ablations_a2", ablations_a2.predict_batch),
    ("ablations_a3", ablations_a3.predict_batch),
]


def test_repeat_run_byte_identical():
    rows = load_inputs()[:25]
    inputs = [to_study_input(r) for r in rows]
    for name, fn in METHODS:
        first = fn(inputs, {"seed": 23})
        second = fn(inputs, {"seed": 23})
        h1 = sha256_bytes(canonical_json([p.to_dict() for p in first]))
        h2 = sha256_bytes(canonical_json([p.to_dict() for p in second]))
        assert h1 == h2, f"{name} not deterministic"


def test_full_dataset_pairing_preserved():
    rows = load_inputs()
    inputs = [to_study_input(r) for r in rows]
    for name, fn in METHODS:
        preds = fn(inputs, {"seed": 11})
        assert len(preds) == len(inputs)
        assert [p.case_id for p in preds] == [i.case_id for i in inputs], name


def test_predictions_carry_no_gold_fields():
    rows = load_inputs()
    inputs = [to_study_input(r) for r in rows]
    for name, fn in METHODS:
        for pred in fn(inputs, {"seed": 11}):
            d = pred.to_dict()
            for forbidden in ("expected_decision", "oracle", "gold", "fault_id", "label"):
                assert forbidden not in d, (name, forbidden)


def test_input_sha_stability_across_runs():
    rows = load_inputs()[:10]
    hashes_1 = [sha256_bytes(canonical_json(to_study_input(r).features)) for r in rows]
    hashes_2 = [sha256_bytes(canonical_json(to_study_input(r).features)) for r in rows]
    assert hashes_1 == hashes_2
