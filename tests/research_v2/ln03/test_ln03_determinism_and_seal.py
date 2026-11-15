"""Determinism and oracle-leakage (inference seal) tests for LN-03."""
from __future__ import annotations

import json

from research_v2.contracts.input_masking import mask_case_input
from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.baselines_b0 import predict_batch as b0
from research_v2.methods.ln03.baselines_c1 import predict_batch as c1
from research_v2.methods.ln03.legacy_adapter import predict_batch as legacy

from ln03_helpers import load_t3_gold, load_t3_inputs, make_features


def _masked_inputs(rows, limit=None):
    out = []
    for row in rows[: limit or len(rows)]:
        out.append(
            StudyInput(
                study_id="LN-03",
                case_id=row["case_id"],
                split_id="test",
                group_id=row["group_id"],
                features=mask_case_input(row),
            )
        )
    return out


def test_repeat_run_identical_predictions():
    inputs = _masked_inputs(load_t3_inputs(), limit=40)
    run1 = proposed.predict_batch(inputs, {"seed": 23})
    run2 = proposed.predict_batch(inputs, {"seed": 23})
    assert run1 == run2
    assert [p.to_dict() for p in run1] == [p.to_dict() for p in run2]


def test_seed_change_does_not_alter_decisions():
    inputs = _masked_inputs(load_t3_inputs(), limit=40)
    a = proposed.predict_batch(inputs, {"seed": 11})
    b = proposed.predict_batch(inputs, {"seed": 37})
    assert [p.decision for p in a] == [p.decision for p in b]


def test_changing_only_oracle_does_not_alter_prediction():
    features = make_features()
    base = proposed.predict_batch(
        [StudyInput("LN-03", "LN-03-SEAL-1", "test", "grp", features)], {"seed": 11}
    )[0]
    # Inject oracle-shaped keys into a COPY of the features; contract must block.
    poisoned = dict(features)
    poisoned["expected_decision"] = "schedule_eligible"
    try:
        proposed.predict_batch([StudyInput("LN-03", "LN-03-SEAL-2", "test", "grp", poisoned)])
    except ContractError:
        pass  # frozen contract rejects leakage at construction: correct fail-closed
    else:
        raise AssertionError("oracle key in features must be rejected")
    # Original prediction unchanged (oracle lives evaluator-side only).
    again = proposed.predict_batch(
        [StudyInput("LN-03", "LN-03-SEAL-1", "test", "grp", features)], {"seed": 11}
    )[0]
    assert again == base


def test_predictions_serialize_without_gold_material():
    inputs = _masked_inputs(load_t3_inputs(), limit=20)
    for method in (proposed.predict_batch, b0, c1, legacy):
        for pred in method(inputs, {"seed": 11}):
            row = json.loads(json.dumps(pred.to_dict()))
            assert "expected_decision" not in row
            assert "oracle" not in row
            assert "fault_id" not in row
            assert "gold" not in row


def test_masked_dataset_inputs_never_contain_gold_fields():
    for row in load_t3_inputs():
        feats = mask_case_input(row)
        assert "expected_decision" not in feats
        assert "oracle" not in feats
        assert "fault_id" not in feats
        assert set(feats) & {"gold_label", "label", "cohort"} == set()


def test_gold_stays_evaluator_side():
    gold = load_t3_gold()
    assert len(gold) == 120
    assert all(set(v) == set() or isinstance(v, str) for v in gold.values())
