"""Legacy adapter provenance parity and dataset agreement tests."""
from __future__ import annotations

import pytest

from research_v2.contracts.input_masking import mask_case_input
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.errors import ScenarioError
from research_v2.methods.ln03.legacy_adapter import legacy_decide, predict_batch as legacy

from ln03_helpers import load_t3_gold, load_t3_inputs, make_features


def test_legacy_adapter_matches_proposed_on_full_t3_dataset():
    """The V2 proposed method must reproduce the observed legacy engine
    (PEDAGOGICAL_SPEC_DUAL_MODE oracle basis) decision-for-decision."""
    inputs = [
        StudyInput("LN-03", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    ours = proposed.predict_batch(inputs, {"seed": 11})
    theirs = legacy(inputs, {"seed": 11})
    assert [p.decision for p in ours] == [p.decision for p in theirs]


def test_proposed_matches_gold_oracle_on_full_t3_dataset():
    gold = load_t3_gold()
    inputs = [
        StudyInput("LN-03", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    preds = proposed.predict_batch(inputs, {"seed": 11})
    correct = sum(1 for p in preds if gold[p.case_id] == p.decision)
    assert correct == len(gold) == 120


def test_legacy_decide_mode_guard_and_unknown_label_rejection():
    # Legacy integration adapter rejects unknown modes with ValueError.
    from research.integrations.ln03 import run_policy

    with pytest.raises(ValueError, match="Unknown mode"):
        run_policy(make_features(), mode="bogus_mode", config={})
    # The V2 adapter fail-closes when the legacy engine emits an unknown label.
    import research.integrations.ln03 as legacy_mod

    original = legacy_mod.run_policy

    def _bogus(features, *, mode, config):
        return {"decision": "mystery_label", "reason_codes": []}

    try:
        legacy_mod.run_policy = _bogus
        with pytest.raises(ScenarioError, match="unknown decision"):
            legacy_decide(make_features(), mode="intervention")
    finally:
        legacy_mod.run_policy = original


def test_dataset_shape_invariants():
    rows = load_t3_inputs()
    gold = load_t3_gold()
    assert len(rows) == len(gold) == 120
    for row in rows:
        assert row["study_id"] == "LN-03"
        assert row["case_id"] in gold
        feats = row["input"]
        assert feats["task_type"] == "historical_explanation"
        assert isinstance(feats["fact_prerequisite_mastered"], bool)
        assert isinstance(feats["review_card"]["source_verified"], bool)
        assert "expected_decision" not in feats


def test_metrics_diagnostic_counts_invalid_assignments():
    from research_v2.methods.ln03.metrics import summarize

    rows = [
        {
            "decision": "schedule_eligible",
            "input": {
                "task_type": "historical_explanation",
                "fact_prerequisite_mastered": False,
                "review_card": {"source_verified": True},
            },
        },
        {
            "decision": "assign_fact_retrieval",
            "input": {
                "task_type": "historical_explanation",
                "fact_prerequisite_mastered": False,
                "review_card": {"source_verified": True},
            },
        },
    ]
    summary = summarize(rows)
    assert summary["invalid_generative_assignment"]["numerator"] == 1
    assert summary["invalid_generative_assignment"]["denominator"] == 1
    assert summary["invalid_generative_assignment"]["rate"] == 1.0
