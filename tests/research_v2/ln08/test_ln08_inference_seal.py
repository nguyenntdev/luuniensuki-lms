"""Inference seal: predictions depend only on legitimate features, never gold."""
from __future__ import annotations

import pytest

from ln08_helpers import make_features, make_input


def test_oracle_keys_are_forbidden_in_study_input():
    from research_v2.contracts.types import ContractError

    features = make_features(expected_decision="feedback_supported")
    with pytest.raises(ContractError, match="forbidden"):
        make_input("t-leak", features)


def test_nested_oracle_keys_are_rejected():
    from research_v2.contracts.types import ContractError

    features = make_features()
    features["input"] = {"gold_label": "classify_contradiction"}
    with pytest.raises(ContractError, match="forbidden"):
        make_input("t-nested", features)


def test_changing_only_gold_material_cannot_change_predictions():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.methods.ln08.proposed import predict_batch

    row = {
        "case_id": "t-seal",
        "group_id": "g",
        "input": make_features(),
    }
    base = predict_batch([_study_input(row)], {})

    mutated = dict(row)
    mutated["expected_decision"] = "classify_contradiction"
    mutated["fault_id"] = "FAULT-999"
    mutated["cohort"] = "ATTACK"
    mutated["oracle"] = {"expected_decision": "abstain"}
    after = predict_batch([_study_input(mutated)], {})
    assert [p.to_dict() for p in base] == [p.to_dict() for p in after]


def _study_input(row):
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput

    return StudyInput("LN-08", row["case_id"], "test", row["group_id"], mask_case_input(row))


def test_solver_ignores_non_schema_feature_keys():
    from research_v2.methods.ln08.dataset import DiagnosticCase
    from research_v2.methods.ln08.proposed import solve_case

    features = make_features(learner={"profile_id": "x"}, seed=1)
    a = solve_case(DiagnosticCase.from_features(features, case_id="x"))
    features["learner"] = {"profile_id": "totally-different"}
    b = solve_case(DiagnosticCase.from_features(features, case_id="x"))
    assert a["decision"] == b["decision"]


def test_gold_decision_flip_via_direct_features_is_blocked_by_dataset_layer():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    features = make_features(expected_decision="feedback_supported")
    import pytest

    with pytest.raises(DatasetError, match="forbidden gold fields"):
        DiagnosticCase.from_features(features, case_id="t-gold")
