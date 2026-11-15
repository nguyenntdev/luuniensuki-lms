"""Determinism & pairing: identical input + config + seed -> identical output."""
from __future__ import annotations

import json

from ln08_helpers import load_t3_inputs, make_features, make_input


def test_repeat_runs_produce_identical_predictions():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.proposed import predict_batch

    rows = load_t3_inputs()[:30]
    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]
    first = [p.to_dict() for p in predict_batch(inputs, {"seed": 11})]
    for seed in (11, 23, 37):
        again = [p.to_dict() for p in predict_batch(inputs, {"seed": seed})]
        assert again == first, f"predictions changed with seed {seed}"


def test_input_hash_pairing_is_stable():
    from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes
    from research_v2.contracts.input_masking import mask_case_input

    rows = load_t3_inputs()[:20]
    hashes_a = [sha256_bytes(canonical_json(mask_case_input(r))) for r in rows]
    hashes_b = [sha256_bytes(canonical_json(mask_case_input(r))) for r in rows]
    assert hashes_a == hashes_b
    # The fixture-declared hash must match the canonical recomputation.
    for row, digest in zip(rows, hashes_a):
        assert digest == row["input_sha256"]


def test_all_matrix_methods_are_deterministic():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput

    rows = load_t3_inputs()[:12]
    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]
    from research_v2.methods.ln08.proposed import predict_batch as proposed
    from research_v2.methods.ln08.baselines_b0 import predict_batch as b0
    from research_v2.methods.ln08.baselines_c1 import predict_batch as c1
    from research_v2.methods.ln08.ablations_a1 import predict_batch as a1
    from research_v2.methods.ln08.ablations_a2 import predict_batch as a2
    from research_v2.methods.ln08.ablations_a3 import predict_batch as a3

    for fn in (proposed, b0, c1, a1, a2, a3):
        first = [p.to_dict() for p in fn(inputs, {"seed": 37})]
        second = [p.to_dict() for p in fn(inputs, {"seed": 37})]
        assert first == second


def test_predictions_never_carry_gold_fields():
    from research_v2.evaluation.metrics import FORBIDDEN_GOLD_IN_PREDICTION
    from research_v2.methods.ln08.proposed import predict_batch
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput

    rows = load_t3_inputs()[:10]
    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]
    for pred in predict_batch(inputs, {"seed": 11}):
        row = pred.to_dict()
        assert not (set(row) & FORBIDDEN_GOLD_IN_PREDICTION)
        assert json.dumps(row).count("expected_decision") == 0
