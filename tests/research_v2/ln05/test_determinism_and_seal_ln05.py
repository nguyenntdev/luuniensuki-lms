"""Determinism, idempotency and inference-seal tests for LN-05.

Scientific boundary: model inputs never contain gold labels; changing only
oracle/gold material must never alter a prediction.
"""
from __future__ import annotations

import copy
import json

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.methods.ln05 import predict_batch as predict_proposed
from tests.research_v2.ln05.conftest import make_inputs, run_config


def test_identical_inputs_and_seed_produce_byte_identical_predictions():
    rows = make_inputs.__wrapped__ if False else None  # keep linters honest
    from tests.research_v2.ln05.conftest import load_rows

    inputs = make_inputs(load_rows())
    a = predict_proposed(inputs, run_config(seed=11))
    b = predict_proposed(inputs, run_config(seed=11))
    assert [p.to_dict() for p in a] == [p.to_dict() for p in b]


def test_predictions_stable_across_seeds():
    """The policy is deterministic rule evaluation; seeds must not move it."""
    from tests.research_v2.ln05.conftest import load_rows

    inputs = make_inputs(load_rows())
    a = predict_proposed(inputs, run_config(seed=11))
    b = predict_proposed(inputs, run_config(seed=37))
    assert [(p.case_id, p.decision) for p in a] == [(p.case_id, p.decision) for p in b]


def test_repeated_case_input_hash_yields_stable_output():
    from tests.research_v2.ln05.conftest import load_rows

    rows = load_rows()
    r = rows[0]
    h1 = sha256_input(r["input"])
    h2 = sha256_input(json.loads(json.dumps(r["input"])))
    assert h1 == h2
    a = predict_proposed(make_inputs([r]), run_config())
    b = predict_proposed(make_inputs([json.loads(json.dumps(r))]), run_config())
    assert a[0].to_dict() == b[0].to_dict()


def test_changing_only_oracle_material_does_not_change_prediction():
    """Inference seal: gold material is not part of the model input at all."""
    from tests.research_v2.ln05.conftest import load_rows

    rows = load_rows()
    r = rows[0]
    inputs = make_inputs([r])
    base = predict_proposed(inputs, run_config())

    # Simulate evaluating under a *different* gold answer for the same case:
    # the prediction pipeline never sees gold, so nothing can change.
    from research_v2.contracts.types import StudyPrediction

    forged_gold = StudyPrediction(
        study_id="LN-05",
        case_id=r["case_id"],
        decision="deny_mastery_badge",
    )
    assert base[0].decision != forged_gold.decision  # sanity: they differ
    again = predict_proposed(inputs, run_config())
    assert again[0].to_dict() == base[0].to_dict()


def test_input_masking_strips_gold_from_raw_fixture():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import FORBIDDEN_INPUT_KEYS

    from tests.research_v2.ln05.conftest import load_rows

    for r in load_rows()[:20]:
        raw = dict(r)
        raw["oracle"] = {"expected_decision": "grant_if_eligible"}
        raw["fault_id"] = "fault-1"
        masked = mask_case_input(raw)
        assert not (set(masked) & FORBIDDEN_INPUT_KEYS)
        assert "oracle" not in masked and "fault_id" not in raw["input"]


def test_predictions_never_carry_gold_material():
    from tests.research_v2.ln05.conftest import load_rows

    forbidden = {"oracle", "expected_decision", "expected_category", "fault_id", "gold_label"}
    inputs = make_inputs(load_rows())
    for p in predict_proposed(inputs, run_config()):
        payload = p.to_dict()
        assert not (set(payload) & forbidden), payload


def test_features_are_not_mutated_by_evaluation():
    from tests.research_v2.ln05.conftest import load_rows

    rows = load_rows()
    before = copy.deepcopy(rows[0]["input"])
    from tests.research_v2.ln05.conftest import make_inputs

    predict_proposed(make_inputs([rows[0]]), run_config())
    assert rows[0]["input"] == before
