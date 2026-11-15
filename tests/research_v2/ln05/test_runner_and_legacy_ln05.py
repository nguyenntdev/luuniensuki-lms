"""Runner-integration and legacy-adapter tests for LN-05.

Covers: matrix schema, prereg invariants, runner-compatible aliases, the
legacy engine adapter (read-only, translated labels), and study metrics.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

from research_v2.methods.ln05.legacy_adapter import LegacyLn05Adapter
from tests.research_v2.ln05.conftest import (
    DATASET_SHA256,
    REPO,
    load_gold,
    load_rows,
    make_inputs,
    run_config,
)

MATRIX_PATH = REPO / "research_v2" / "experiments" / "ln05" / "matrix.yaml"
PREREG_PATH = REPO / "research_v2" / "experiments" / "ln05" / "prereg.yaml"
SPLITS_PATH = REPO / "research_v2" / "experiments" / "ln05" / "splits.yaml"


def test_matrix_schema_and_cell_count():
    matrix = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    assert matrix["repo_root"] == "."
    assert len(matrix["cells"]) == 1
    cell = matrix["cells"][0]
    assert cell["study"] == "LN-05"
    assert cell["tier"] == "T3"
    assert cell["dataset"] == "research_v2/data/ln05/t3_inputs.jsonl"
    assert cell["gold"] == "research_v2/data/ln05/t3_gold.jsonl"
    assert cell["methods"] == [
        "proposed",
        "baselines_b0",
        "baselines_c1",
        "ablations_a1",
        "ablations_a2",
        "ablations_a3",
    ]
    assert cell["seeds"] == [11, 23, 37]
    assert cell["split_id"] == "test"
    assert cell["group_key"] == "group_id"


def test_prereg_pins_dataset_hashes_and_counterexamples():
    prereg = yaml.safe_load(PREREG_PATH.read_text(encoding="utf-8"))
    assert prereg["study_id"] == "LN-05"
    ds = prereg["datasets"][0]
    assert ds["inputs_sha256"] == DATASET_SHA256
    ce_ids = {ce["id"] for ce in prereg["mandatory_counterexamples"]}
    assert "LN05-CE-1" in ce_ids  # the 100x duplicate case
    assert prereg["primary_endpoint"]["name"] == "security_utility_frontier"


def test_prereg_marks_b0_sanity_only():
    prereg = yaml.safe_load(PREREG_PATH.read_text(encoding="utf-8"))
    b0 = next(m for m in prereg["methods_registered"] if m["id"] == "baselines_b0")
    assert "SANITY_ONLY" in b0["note"]


def test_splits_declare_group_disjoint_holdout():
    splits = yaml.safe_load(SPLITS_PATH.read_text(encoding="utf-8"))
    assert splits["split_id"] == "test"
    assert splits["splits"]["test"]["n_cases"] == 120
    # group_key uniqueness: one replay family per case, no straddling.
    rows = load_rows()
    group_ids = [r["group_id"] for r in rows]
    assert len(set(group_ids)) == len(group_ids)


def test_runner_alias_modules_expose_predict_batch():
    from importlib import import_module

    for method_id in (
        "proposed",
        "baselines_b0",
        "baselines_c1",
        "ablations_a1",
        "ablations_a2",
        "ablations_a3",
    ):
        module = import_module(f"research_v2.methods.ln05.{method_id}")
        assert callable(module.predict_batch), method_id
        assert module.METHOD_ID == method_id, (method_id, module.METHOD_ID)


def test_runner_can_execute_ln05_matrix(tmp_path):
    """Full runner pass over the LN-05 matrix: 6 methods x 3 seeds = 18 cells."""
    from research_v2.evaluation.runner import run_experiment

    out = run_experiment(MATRIX_PATH, tmp_path, strict=True)
    index = json.loads((out / "run_index.json").read_text(encoding="utf-8"))
    assert index["n_cells"] == 18
    assert index["n_failed"] == 0
    statuses = Counter(c["status"] for c in index["cells"])
    assert statuses == Counter({"PASS": 18})


def test_runner_predictions_match_gold_for_proposed(tmp_path):
    from research_v2.evaluation.runner import run_experiment

    out = run_experiment(MATRIX_PATH, tmp_path, strict=True)
    preds_path = out / "LN-05" / "T3" / "proposed" / "seed11" / "predictions.jsonl"
    preds = [json.loads(line) for line in preds_path.open(encoding="utf-8")]
    golds = load_gold()
    assert len(preds) == 120
    assert all(p["decision"] == golds[p["case_id"]] for p in preds)
    # oracle-free predictions
    for p in preds:
        assert "oracle" not in p and "expected_decision" not in p


def test_legacy_adapter_matches_legacy_engine_with_translated_labels():
    from research.gamification.mastery_reward_policy import evaluate_mastery_reward_intervention
    from research_v2.methods.ln05.labels import to_v2_decision

    adapter = LegacyLn05Adapter()
    assert adapter.available
    for row in load_rows()[:25]:
        legacy_raw = evaluate_mastery_reward_intervention(row["input"], {})
        inputs = make_inputs([row])
        adapted = adapter.predict_one(inputs[0], mode="intervention")
        # The adapter projects onto the V2 label space; the raw engine emits
        # the legacy vocabulary. They must agree under the bijection.
        assert adapted.decision == to_v2_decision(legacy_raw.decision)
        assert adapted.reason_codes == tuple(legacy_raw.reason_codes)


def test_legacy_adapter_translates_all_five_families_correctly():
    from tests.research_v2.ln05.conftest import gold_v2

    adapter = LegacyLn05Adapter()
    golds_v2 = gold_v2()
    inputs = make_inputs(load_rows())
    matched = 0
    for inp in inputs:
        adapted = adapter.predict_one(inp, mode="intervention")
        if adapted.decision == golds_v2[inp.case_id]:
            matched += 1
    assert matched == 120, f"legacy adapter must reproduce gold under V2 mapping: {matched}/120"


def test_legacy_adapter_does_not_mutate_input_features():
    import copy

    adapter = LegacyLn05Adapter()
    rows = load_rows()
    before = copy.deepcopy(rows[0]["input"])
    inputs = make_inputs([rows[0]])
    adapter.predict_one(inputs[0], mode="intervention")
    assert rows[0]["input"] == before


def test_security_utility_metrics_frontier():
    from research_v2.methods.ln05.metrics import security_utility_metrics

    m = security_utility_metrics(
        decisions={"r1": "grant_if_eligible", "r2": "deduplicate_events", "l1": "grant_if_eligible"},
        replay_case_ids=["r1", "r2"],
        legit_eligible_case_ids=["l1"],
    )
    assert m["false_award_rate"] == 0.5
    assert m["legitimate_award_recall"] == 1.0


def test_confusion_rejects_population_mismatch():
    from research_v2.methods.ln05.metrics import confusion

    with __import__("pytest").raises(ValueError, match="population"):
        confusion({"a": "grant_if_eligible"}, {"a": "grant_if_eligible", "b": "revalidate_badge"})
