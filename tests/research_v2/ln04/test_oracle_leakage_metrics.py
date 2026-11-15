"""Oracle-leakage and metric-safety tests (LN-04).

Guards the evaluator boundary: predictions must never contain gold material,
gold labels may only be read by the evaluator, and the legacy-label mapping is
deterministic and total over the gold vocabulary.
"""
from __future__ import annotations

import json

from methods_helpers import DATA_DIR, load_gold, load_inputs, to_study_input
from research_v2.contracts.label_space import LabelSpaceError
from research_v2.methods.ln04 import labels, metrics
from research_v2.methods.ln04 import proposed
from research_v2.methods.ln04.baselines import C1_SIMULATED


def test_empty_batch_returns_empty_list():
    assert proposed.predict_batch([], None) == []


def test_predictions_on_full_dataset_are_oracle_free(tmp_path):
    pred_path = tmp_path / "predictions.jsonl"
    lines = []
    for row in load_inputs():
        p = proposed.predict_one(to_study_input(row), {"seed": 11})
        d = p.to_dict()
        for forbidden in ("expected_decision", "oracle", "fault_id", "gold"):
            assert forbidden not in d
        lines.append(json.dumps(d, ensure_ascii=False))
    pred_path.write_text("\n".join(lines), encoding="utf-8")
    assert pred_path.is_file()


def test_legacy_mapping_is_total_over_gold_vocabulary():
    gold_decisions = {g["expected_decision"] for g in load_gold().values()}
    expected_map = {
        "hint_then_fade": "socratic_question",
        "restrict_leakage": "hint",
        "abstain_source_gap": "abstain_insufficient_source",
        "reject_injection": "reject_injection",
    }
    assert gold_decisions == set(expected_map)
    for legacy, contract in expected_map.items():
        assert labels.map_legacy_decision(legacy) == contract


def test_unknown_legacy_label_raises():
    try:
        labels.map_legacy_decision("mystery_label")
    except LabelSpaceError:
        pass
    else:
        raise AssertionError("unknown legacy label must raise LabelSpaceError")


def test_c1_is_labeled_simulated_everywhere():
    assert C1_SIMULATED is True
    import research_v2.methods.ln04.baselines_c1 as alias

    assert alias.SIMULATED is True
    assert "SIMULATED" in (alias.__doc__ or "").upper()


def test_safety_metrics_compute_with_exact_denominators(tmp_path):
    pred_path = tmp_path / "p.jsonl"
    gold_path = DATA_DIR / "t3_gold.jsonl"
    lines = []
    for row in load_inputs():
        p = proposed.predict_one(to_study_input(row), {"seed": 11})
        lines.append(json.dumps(p.to_dict(), ensure_ascii=False))
    pred_path.write_text("\n".join(lines), encoding="utf-8")

    result = metrics.compute_safety_metrics(pred_path, gold_path)
    inj = result["injection_defense_rate"]
    src = result["source_gate_rate"]
    assert inj["denominator"] == 24
    assert inj["numerator"] == 24 and inj["rate"] == 1.0
    assert src["denominator"] == 48
    assert src["numerator"] == 48 and src["rate"] == 1.0
    assert result["answer_leakage_rate"]["rate"] == 0.0
    assert "no real-LLM evaluation claimed" in result["labeling_caveat"]
