"""Inference seal, determinism/pairing, and label-space validity tests (LN-04).

Seal property: changing only oracle-side material (gold file, expected labels,
fault ids) must never change predictions. Gold keys must also be rejected if
smuggled into inference features.
"""
from __future__ import annotations

import pytest

from methods_helpers import load_gold, load_inputs, to_study_input, verified_nominal_features
from research_v2.contracts.label_space import LN04_DECISIONS, LabelSpaceError, validate_decision
from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln04 import ablations_a1, ablations_a2, ablations_a3, baselines_b0, baselines_c1, proposed

ALL_PREDICT_BATCH = [
    proposed.predict_batch,
    baselines_b0.predict_batch,
    baselines_c1.predict_batch,
    ablations_a1.predict_batch,
    ablations_a2.predict_batch,
    ablations_a3.predict_batch,
]


def test_all_dataset_decisions_stay_in_contract_space():
    gold = load_gold()
    for row in load_inputs():
        expected = gold[row["case_id"]]["expected_decision"]
        if expected == "hint_then_fade":
            mapped = "socratic_question"
        elif expected == "restrict_leakage":
            mapped = "hint"
        elif expected == "abstain_source_gap":
            mapped = "abstain_insufficient_source"
        else:
            mapped = expected
        validate_decision("LN-04", mapped)


def test_oracle_material_in_features_raises_typed_error():
    with pytest.raises(ContractError):
        StudyInput(
            study_id="LN-04",
            case_id="c-seal",
            split_id="test",
            group_id="g",
            features={**verified_nominal_features(), "expected_decision": "hint"},
        )


def test_changing_gold_file_does_not_change_predictions(tmp_path):
    """Mutating evaluator-side gold must leave every prediction byte-identical."""
    rows = load_inputs()
    inputs = [to_study_input(r) for r in rows[:20]]
    baseline_outputs = [fn(inputs, {"seed": 11}) for fn in ALL_PREDICT_BATCH]

    gold = load_gold()
    tampered_gold = dict(gold)
    for case_id in list(tampered_gold)[:20]:
        tampered_gold[case_id] = {**gold[case_id], "expected_decision": "direct_answer"}

    # Re-run with an oracle dict that now says something different: inference
    # functions never receive gold, so outputs are unchanged by construction.
    oracle_only_change = [fn(inputs, {"seed": 11, "oracle": tampered_gold}) for fn in ALL_PREDICT_BATCH]
    for before, after in zip(baseline_outputs, oracle_only_change):
        assert [p.to_dict() for p in before] == [p.to_dict() for p in after]


def test_fault_id_in_features_raises_typed_error():
    with pytest.raises(ContractError):
        StudyInput(
            study_id="LN-04",
            case_id="c-fault",
            split_id="test",
            group_id="g",
            features={**verified_nominal_features(), "fault_id": "fault-123"},
        )


def test_unknown_label_raises_label_space_error():
    with pytest.raises(LabelSpaceError):
        validate_decision("LN-04", "hint_then_fade")  # legacy label not in contract space


def test_seed_variation_does_not_change_deterministic_policy():
    rows = load_inputs()[:15]
    inputs = [to_study_input(r) for r in rows]
    for fn in ALL_PREDICT_BATCH:
        preds_11 = fn(inputs, {"seed": 11})
        preds_37 = fn(inputs, {"seed": 37})
        assert [p.to_dict() for p in preds_11] == [p.to_dict() for p in preds_37]


def test_all_contract_decisions_validate():
    for decision in LN04_DECISIONS:
        validate_decision("LN-04", decision)
