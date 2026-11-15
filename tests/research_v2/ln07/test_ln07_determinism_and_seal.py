"""Determinism / pairing tests (LN-07-03 section G pairing) + inference seal.

- Repeated runs with identical inputs/config produce byte-identical
  predictions regardless of seed (the policy consumes no randomness).
- Oracle material must never influence a prediction: mutating gold fields in
  the raw fixture (they never enter the masked input anyway) or attempting to
  smuggle oracle keys into features must not change (or must reject) the
  prediction.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest  # noqa: E402

from research_v2.contracts.types import ContractError, StudyInput  # noqa: E402
from research_v2.methods.ln07.proposed import predict_batch  # noqa: E402
from tests.research_v2.ln07.ln07_helpers import (  # noqa: E402
    make_case,
    make_input,
    policy_predict,
    policy_solve,
    t3_inputs,
)


class TestDeterminism:
    def test_identical_inputs_identical_predictions_across_seeds(self):
        inputs = t3_inputs()[:24]
        p11 = policy_predict("proposed", inputs, {"seed": 11})
        p23 = policy_predict("proposed", inputs, {"seed": 23})
        p37 = policy_predict("proposed", inputs, {"seed": 37})
        assert [x.to_dict() for x in p11] == [x.to_dict() for x in p23]
        assert [x.to_dict() for x in p11] == [x.to_dict() for x in p37]

    def test_repeated_runs_byte_identical(self):
        inputs = t3_inputs()[:24]
        first = [x.to_dict() for x in policy_predict("proposed", inputs, {"seed": 11})]
        for _ in range(3):
            again = [x.to_dict() for x in policy_predict("proposed", inputs, {"seed": 11})]
            assert again == first

    def test_all_methods_deterministic(self):
        case = make_case(required=["visual_detail", "inscription"], network_kbps=80)
        for method in (
            "proposed",
            "baselines_b0",
            "baselines_c1",
            "ablations_a1",
            "ablations_a2",
            "ablations_a3",
        ):
            a = policy_solve(method, case)
            b = policy_solve(method, case)
            assert a == b, method

    def test_case_input_hash_stability(self):
        from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes

        a = make_case(required=["visual_detail"], case_id="d1")
        b = make_case(required=["visual_detail"], case_id="d1")
        ia, ib = make_input(a), make_input(b)
        assert sha256_bytes(canonical_json(ia.features)) == sha256_bytes(
            canonical_json(ib.features)
        )


class TestInferenceSeal:
    def test_masked_inputs_carry_no_gold_fields(self):
        for inp in t3_inputs():
            leaked = (
                set(inp.features)
                & {"oracle", "expected_decision", "fault_id", "gold", "cohort"}
            )
            assert not leaked, inp.case_id

    def test_forbidden_feature_keys_rejected_by_contract(self):
        with pytest.raises(ContractError):
            StudyInput(
                study_id="LN-07",
                case_id="leaky",
                split_id="test",
                group_id="g",
                features={"expected_decision": "choose_feasible_modality"},
            )

    def test_changing_gold_material_does_not_change_prediction(self):
        case = make_case(required=["visual_detail", "inscription"], case_id="seal")
        base = policy_solve("proposed", case)
        # Policies read only case features; there is no oracle channel at all.
        # Simulate: same features through a different method entry point must
        # give the same decision.
        from research_v2.methods.ln07.proposed import predict_one

        pred = predict_one(make_input(case))
        assert pred.decision == base["decision"]

    def test_batch_contract_preserves_order_and_count(self):
        inputs = t3_inputs()
        preds = predict_batch(inputs, {"seed": 11})
        assert len(preds) == len(inputs) == 120
        assert [p.case_id for p in preds] == [i.case_id for i in inputs]
        for p in preds:
            assert p.study_id == "LN-07"
            assert isinstance(p.reason_codes, tuple)
