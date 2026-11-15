"""Determinism: reordering inputs must not change decisions, costs or routes."""
from __future__ import annotations

import json
import random

from research_v2.contracts.input_masking import mask_case_input
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln06.dataset import load_jsonl, DATASET_PATH
from research_v2.methods.ln06.proposed import predict_batch

ALL_METHODS = [
    "proposed",
    "baselines_b0",
    "baselines_c1",
    "ablations_a1",
    "ablations_a2",
    "ablations_a3",
]


def _predict_all(inputs, seed=11):
    from importlib import import_module

    return {
        m: import_module(f"research_v2.methods.ln06.{m}").predict_batch(inputs, {"seed": seed})
        for m in ALL_METHODS
    }


def test_matrix_dataset_predictions_stable_under_case_reordering(t3_dataset_paths):
    inputs_path, _ = t3_dataset_paths
    rows = load_jsonl(inputs_path)
    forward = [
        StudyInput("LN-06", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]
    shuffled_rows = rows[:]
    random.Random(123).shuffle(shuffled_rows)
    shuffled = [
        StudyInput("LN-06", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in shuffled_rows
    ]
    forward_preds = _predict_all(forward)
    shuffled_preds = _predict_all(shuffled)
    by_case = {}
    for method, preds in shuffled_preds.items():
        by_case[method] = {p.case_id: p for p in preds}
    for method, preds in forward_preds.items():
        for pred in preds:
            twin = by_case[method][pred.case_id]
            assert pred.decision == twin.decision
            assert pred.score == twin.score
            assert pred.evidence_ids == twin.evidence_ids


def test_feature_key_order_does_not_matter(t3_dataset_paths):
    inputs_path, _ = t3_dataset_paths
    row = load_jsonl(inputs_path)[0]
    feats = mask_case_input(row)
    reversed_feats = {
        k: (list(reversed(v)) if isinstance(v, list) and k == "stops" else v)
        for k, v in reversed(list(feats.items()))
    }
    a = predict_batch(
        [StudyInput("LN-06", row["case_id"], "test", row["group_id"], feats)], {}
    )[0]
    b = predict_batch(
        [StudyInput("LN-06", row["case_id"], "test", row["group_id"], reversed_feats)], {}
    )[0]
    assert a.decision == b.decision
    assert a.score == b.score
    assert a.evidence_ids == b.evidence_ids


def test_repeated_calls_deterministic(t3_dataset_paths):
    inputs_path, _ = t3_dataset_paths
    rows = load_jsonl(inputs_path)[:20]
    inputs = [
        StudyInput("LN-06", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]
    first = _predict_all(inputs)
    second = _predict_all(inputs)
    for method in ALL_METHODS:
        assert [p.to_dict() for p in first[method]] == [p.to_dict() for p in second[method]]


def test_input_hash_independent_of_gold(t3_dataset_paths):
    """Masking yields byte-identical features whether or not gold fields sit nearby."""
    inputs_path, _ = t3_dataset_paths
    row = load_jsonl(inputs_path)[0]
    with_gold = dict(row)
    with_gold["oracle"] = {"expected_decision": "find_valid_route"}
    with_gold["fault_id"] = "synthetic"
    assert mask_case_input(with_gold) == mask_case_input(row)
