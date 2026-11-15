"""Study-specific secondary metrics + legacy adapter parity (17/18 + 05)."""
from __future__ import annotations

from ln08_helpers import load_t3_gold, load_t3_inputs

#: Contract -> native inverse used only for legacy parity comparison
#: (evaluator-side, never at inference time).
from research_v2.methods.ln08.labels import NATIVE_TO_CONTRACT

CONTRACT_TO_NATIVE: dict[str, str] = {}
for _native, _contract in NATIVE_TO_CONTRACT.items():
    if _contract not in CONTRACT_TO_NATIVE:
        CONTRACT_TO_NATIVE[_contract] = _native

# "supported" folds both the canonical native label and the synonym split
# label; legacy parity compares at this folded granularity (the reason codes
# keep the synonym_equivalence distinction).
SYNONYM_SPLIT_CLASS = {"feedback_supported", "preserve_semantics"}


def _parity_key(label: str) -> str:
    return "supported" if label in SYNONYM_SPLIT_CLASS else label


def _preds_and_golds():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.labels import NATIVE_TO_CONTRACT
    from research_v2.methods.ln08.proposed import predict_batch

    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    preds = predict_batch(inputs, {"seed": 11})
    rows = [
        {"case_id": p.case_id, "decision": p.decision}
        for p in preds
    ]
    gold = load_t3_gold()
    contract_gold = {cid: NATIVE_TO_CONTRACT[label] for cid, label in gold.items()}
    return rows, contract_gold


def test_false_negation_acceptance_zero_for_proposed():
    from research_v2.methods.ln08.metrics import false_negation_acceptance_rate

    preds, golds = _preds_and_golds()
    metric = false_negation_acceptance_rate(preds, golds)
    assert metric["denominator"] == 24
    assert metric["numerator"] == 0
    assert metric["rate"] == 0.0


def test_false_source_error_acceptance_zero_for_proposed():
    from research_v2.methods.ln08.metrics import false_source_error_acceptance_rate

    preds, golds = _preds_and_golds()
    metric = false_source_error_acceptance_rate(preds, golds)
    assert metric["denominator"] == 24
    assert metric["numerator"] == 0


def test_synonym_false_rejection_zero_for_proposed():
    from research_v2.methods.ln08.metrics import synonym_false_rejection_rate

    preds, golds = _preds_and_golds()
    metric = synonym_false_rejection_rate(preds, golds)
    # Supported stratum = canonical (24) + synonym (24) folded under contract.
    assert metric["denominator"] == 48
    assert metric["numerator"] == 0


def test_error_axis_summary_shape():
    from research_v2.methods.ln08.metrics import error_axis_summary

    preds, golds = _preds_and_golds()
    summary = error_axis_summary(preds, golds)
    assert set(summary) == {
        "false_negation_acceptance",
        "false_source_error_acceptance",
        "synonym_false_rejection",
        "abstain",
    }
    assert summary["abstain"]["denominator"] == 120


def test_b0_fails_both_false_acceptance_axes():
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.baselines_b0 import predict_batch as b0
    from research_v2.methods.ln08.labels import NATIVE_TO_CONTRACT
    from research_v2.methods.ln08.metrics import (
        false_negation_acceptance_rate,
        false_source_error_acceptance_rate,
    )

    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    preds = [{"case_id": p.case_id, "decision": p.decision} for p in b0(inputs, {"seed": 11})]
    gold = load_t3_gold()
    contract_gold = {cid: NATIVE_TO_CONTRACT[label] for cid, label in gold.items()}
    neg = false_negation_acceptance_rate(preds, contract_gold)
    src = false_source_error_acceptance_rate(preds, contract_gold)
    assert neg["numerator"] == 24 and neg["rate"] == 1.0
    assert src["numerator"] == 24 and src["rate"] == 1.0


def test_legacy_adapter_matches_proposed_on_full_t3_dataset():
    """The V2 proposed method must reproduce the observed legacy engine
    (DIAGNOSTIC_FEEDBACK_SPEC oracle basis) decision-for-decision under the
    deterministic contract -> native mapping."""
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08 import proposed
    from research_v2.methods.ln08.legacy_adapter import predict_batch as legacy

    inputs = [
        StudyInput("LN-08", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    ours = proposed.predict_batch(inputs, {"seed": 11})
    theirs = legacy(inputs, {"seed": 11})
    ours_native = [CONTRACT_TO_NATIVE[p.decision] for p in ours]
    theirs_native = [p.decision for p in theirs]
    ours_parity = [_parity_key(CONTRACT_TO_NATIVE[p.decision]) for p in ours]
    theirs_parity = [_parity_key(p.decision) for p in theirs]
    assert ours_parity == theirs_parity


def test_legacy_adapter_fail_closed_on_unknown_label():
    import research.integrations.ln08 as legacy_mod
    import pytest

    from ln08_helpers import make_features
    from research_v2.methods.ln08.dataset import DatasetError
    from research_v2.methods.ln08.legacy_adapter import legacy_decide

    original = legacy_mod.run_policy

    def _bogus(features, *, mode, config):
        return {"decision": "mystery_label", "reason_codes": []}

    try:
        legacy_mod.run_policy = _bogus
        with pytest.raises(DatasetError, match="unknown decision"):
            legacy_decide(make_features(), mode="intervention")
    finally:
        legacy_mod.run_policy = original
