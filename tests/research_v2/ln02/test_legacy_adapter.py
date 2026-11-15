"""Legacy engine adapter: read-only bridge, decision parity, no mutation."""
from __future__ import annotations

import pytest

from research_v2.methods.ln02 import proposed
from research_v2.methods.ln02.legacy_adapter import (
    LegacyEngineBlockedError,
    predict_batch as legacy_batch,
    predict_one_legacy,
)
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
from ln02_helpers import (
    cyclic_graph_features,
    invalid_score_features,
    load_t3_inputs,
    make_input,
    nominal_features,
    unobserved_dimension_features,
)


@pytest.mark.parametrize(
    "features_fn",
    [
        nominal_features,
        high_aggregate := lambda: {
            "content": {"id": "motif-gap", "type": "imperial-urn-motif"},
            "graph_edges": [["foundation_orientation", "chronological_sequence"]],
            "learner": {
                "competencies": {"S1": 0.22, "S2": 0.82, "S3": 0.75, "S4": 0.85},
                "profile_id": "LEARNER-GAP",
            },
            "mastery": {"S1": 0.22, "S2": 0.82, "S3": 0.75, "S4": 0.85},
            "score_observed": 0.74,
            "target_task": {
                "id": "task-gap",
                "prerequisites": {"S1": 0.6, "S2": 0.4},
                "target_competency": "S3",
            },
        },
        unobserved_dimension_features,
        cyclic_graph_features,
        invalid_score_features,
    ],
)
def test_legacy_parity_with_proposed_on_golden_cases(features_fn):
    inp = make_input(features=features_fn())
    legacy_pred = predict_one_legacy(inp, {})
    proposed_pred = proposed.predict_batch([inp], {})[0]
    assert legacy_pred.decision == proposed_pred.decision


def test_legacy_adapter_does_not_mutate_input_features():
    features = {
        "content": {"id": "motif-mut", "type": "imperial-urn-motif"},
        "graph_edges": [["a", "b"]],
        "learner": {"competencies": {"S1": 0.8, "S2": 0.7, "S3": 0.9, "S4": 0.6}},
        "mastery": {"S1": 0.8, "S2": 0.7, "S3": 0.9, "S4": 0.6},
        "score_observed": 0.7,
        "target_task": {"id": "task-mut", "prerequisites": {"S1": 0.5}, "target_competency": "S3"},
    }
    snapshot = repr(features)
    inp = make_input(features=features)
    predict_one_legacy(inp, {})
    assert repr(features) == snapshot


def test_legacy_dataset_parity_full():
    """On the frozen T3 dataset the legacy engine and the proposed policy
    agree case-by-case (independent checker, evaluator-side only here)."""
    inputs = load_t3_inputs()
    legacy_decisions = tuple(p.decision for p in legacy_batch(inputs, {}))
    proposed_decisions = tuple(p.decision for p in proposed.predict_batch(inputs, {}))
    assert legacy_decisions == proposed_decisions


def test_baseline_b0_fails_dataset_majority():
    """Sanity: the naive control is not competitive on the full dataset."""
    inputs = load_t3_inputs()
    b0_decisions = tuple(p.decision for p in b0(inputs, {}))
    legacy_decisions = tuple(p.decision for p in legacy_batch(inputs, {}))
    agreement = sum(1 for a, b in zip(b0_decisions, legacy_decisions) if a == b)
    assert agreement < len(inputs)


def test_unknown_decision_from_legacy_raises_typed_error(monkeypatch):
    import research.adaptive.prerequisite_policy as legacy_policy

    def bogus(scenario_input, *, mode="intervention", config=None):
        return {"decision": "fabricated_label", "reason_codes": []}

    monkeypatch.setattr(legacy_policy, "evaluate_policy", bogus)
    inp = make_input()
    with pytest.raises(LegacyEngineBlockedError):
        predict_one_legacy(inp, {})
