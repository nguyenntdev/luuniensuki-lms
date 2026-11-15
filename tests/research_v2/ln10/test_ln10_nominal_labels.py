"""Nominal happy path + native/contract label mapping diagnostics."""
from __future__ import annotations

from research_v2.contracts.types import StudyPrediction
from research_v2.methods.ln10.labels import (
    CONTRACT_DECISIONS,
    Decision,
    NATIVE_DECISIONS,
    to_contract_decision,
    validate_contract_decision,
)
from research_v2.methods.ln10.proposed import predict_batch
from tests.research_v2.ln10.ln10_helpers import make_features, make_input


def test_nominal_scenario_produces_valid_structured_result():
    pred = predict_batch([make_input(make_features(), case_id="happy-1")], {"seed": 11})[0]
    assert isinstance(pred, StudyPrediction)
    assert pred.study_id == "LN-10"
    assert pred.decision == "allow_authorized_transition"
    assert pred.score == 1.0
    assert "nominal_authorized" in pred.reason_codes
    assert pred.reason_codes and pred.evidence_ids


def test_batch_preserves_order_and_case_ids():
    inputs = [make_input(make_features(), case_id=f"order-{i}") for i in range(5)]
    preds = predict_batch(inputs, {"seed": 11})
    assert [p.case_id for p in preds] == [i.case_id for i in inputs]
    assert all(isinstance(p, StudyPrediction) for p in preds)


def test_native_to_contract_projection_is_total():
    for native in NATIVE_DECISIONS:
        projected = to_contract_decision(native)
        assert projected in CONTRACT_DECISIONS
        validate_contract_decision(projected)


def test_projection_keeps_families_distinct():
    assert to_contract_decision("resolve_revision_conflict") == "reject_conflict"
    assert to_contract_decision("deny_transition") == "reject_unauthorized"
    assert to_contract_decision("reject_premature_submit") == "require_reflection"
    assert to_contract_decision("request_reflection") == "require_reflection"
    assert to_contract_decision("postpone") == "postpone"


def test_decision_enum_covers_native_space():
    assert {d.value for d in Decision} == set(NATIVE_DECISIONS)
