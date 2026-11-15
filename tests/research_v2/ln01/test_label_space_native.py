"""LN-01 native label-space enforcement (reviewer finding: drift guard).

The LN-01 engine must emit only labels from the frozen T3 gold vocabulary
(``LN01_NATIVE_DECISIONS``), and any unknown label must raise
``LabelSpaceError`` (fail-closed) instead of silently scoring as an error
class. Mirrors the label-space gating LN-02/04/05/06/08 already have.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v2.contracts.input_masking import mask_case_input
from research_v2.contracts.label_space import (
    LN01_DECISIONS,
    LN01_NATIVE_DECISIONS,
    DECISIONS_BY_STUDY,
    LabelSpaceError,
    NATIVE_DECISIONS_BY_STUDY,
    validate_decision,
    validate_native_decision,
)
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln01 import ablations, ablations_a2, ablations_a3
from research_v2.methods.ln01.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln01.engine import STUDY_ID as ENGINE_STUDY_ID
from research_v2.methods.ln01.engine import evaluate_case
from research_v2.methods.ln01.proposed import predict_batch as proposed_batch

from ln01_helpers import make_features, make_input

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln01" / "t3_gold.jsonl"


def _gold_decisions() -> list[str]:
    with GOLD_PATH.open(encoding="utf-8") as fh:
        return [json.loads(line)["expected_decision"] for line in fh if line.strip()]


def _t3_inputs() -> list[StudyInput]:
    inputs_path = REPO_ROOT / "research_v2" / "data" / "ln01" / "t3_inputs.jsonl"
    with inputs_path.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return [
        StudyInput("LN-01", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in rows
    ]


def test_all_120_t3_predictions_are_in_native_label_space():
    """Every predicted decision over all 120 T3 cases is in LN01_NATIVE_DECISIONS."""
    inputs = _t3_inputs()
    assert len(inputs) == 120
    for fn in (
        proposed_batch,
        predict_batch_b0,
        predict_batch_c1,
        ablations.predict_batch,
        ablations_a2.predict_batch,
        ablations_a3.predict_batch,
    ):
        preds = fn(inputs, {"seed": 11})
        assert len(preds) == 120
        for pred in preds:
            assert pred.decision in LN01_NATIVE_DECISIONS, (
                f"{fn.__name__}: {pred.case_id} emitted unknown label {pred.decision!r}"
            )


def test_native_decisions_exactly_equal_frozen_gold_labels():
    """LN01_NATIVE_DECISIONS == set(expected_decision) in t3_gold.jsonl."""
    gold = set(_gold_decisions())
    assert len(_gold_decisions()) == 120
    assert LN01_NATIVE_DECISIONS == gold


def test_engine_emits_every_native_label_and_gold_covers_them():
    """Engine vocabulary and frozen gold stay in both directions of agreement:
    each engine label is reachable on the T3 set and each gold label is native.
    """
    preds = proposed_batch(_t3_inputs(), {"seed": 11})
    assert {p.decision for p in preds} == set(_gold_decisions())
    assert set(_gold_decisions()) == LN01_NATIVE_DECISIONS
    assert ENGINE_STUDY_ID == "LN-01"


def test_validate_native_decision_accepts_each_native_label():
    for label in sorted(LN01_NATIVE_DECISIONS):
        assert validate_native_decision("LN-01", label) is None


def test_injected_unknown_decision_raises_label_space_error():
    """Unknown labels must fail closed at the validator (emit boundary)."""
    assert "reject_cylce" not in LN01_NATIVE_DECISIONS
    # Direct validator contract: unknown label raises, including near-misses
    # and the contract-space path-planning labels that LN-01 never emits.
    for bad in ("reject_cylce", "find_valid_route", "no_feasible_route", "cost_exceeded", ""):
        with pytest.raises(LabelSpaceError):
            validate_native_decision("LN-01", bad)


def test_monkeypatched_builder_with_unknown_label_raises(monkeypatch):
    """Artificially corrupt the engine's decision constants (drift simulation)
    and confirm the emit boundary raises LabelSpaceError, never returns a
    prediction outside the frozen gold space.
    """
    import research_v2.methods.ln01.engine as engine_mod

    monkeypatch.setattr(engine_mod, "DECISION_ACCEPT", "totally_unknown_label")
    inputs = [make_input("drift-2", make_features())]
    with pytest.raises(LabelSpaceError, match="totally_unknown_label"):
        engine_mod.evaluate_case(inputs[0], {})


def test_contract_space_untouched_and_native_registry_shape():
    """Existing contract sets stay intact; native registry holds LN-01 only."""
    # LN01_DECISIONS / DECISIONS_BY_STUDY unchanged (path-planning vocabulary).
    assert LN01_DECISIONS == frozenset(
        {"find_valid_route", "reject_cycle", "no_feasible_route", "cost_exceeded"}
    )
    assert DECISIONS_BY_STUDY["LN-01"] is LN01_DECISIONS
    assert "accept" not in LN01_DECISIONS
    # Native registry contains exactly the frozen gold vocabulary for LN-01.
    assert NATIVE_DECISIONS_BY_STUDY["LN-01"] is LN01_NATIVE_DECISIONS
    assert "find_valid_route" not in LN01_NATIVE_DECISIONS
    # Contract validator still accepts its own space (other studies unbroken).
    assert validate_decision("LN-01", "find_valid_route") is None


def test_native_validator_rejects_unknown_study_id():
    with pytest.raises(LabelSpaceError, match="unknown study_id"):
        validate_native_decision("LN-99", "accept")
    with pytest.raises(LabelSpaceError, match="unknown study_id"):
        validate_native_decision("LN-02", "recommend_eligible")
