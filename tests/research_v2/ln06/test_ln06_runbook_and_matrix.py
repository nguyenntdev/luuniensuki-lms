"""Experiment matrix + prereg integrity (23_RUNBOOK_AND_MATRIX)."""
from __future__ import annotations

from pathlib import Path

import yaml

from research_v2.methods.ln06.dataset import load_jsonl, DATASET_PATH, GOLD_PATH
from research_v2.methods.ln06.labels import DECISION_VALUES

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = REPO_ROOT / "research_v2" / "experiments" / "ln06"
MATRIX_METHODS = [
    "proposed",
    "baselines_b0",
    "baselines_c1",
    "ablations_a1",
    "ablations_a2",
    "ablations_a3",
]


def test_matrix_schema_and_cell():
    matrix = yaml.safe_load((EXPERIMENTS / "matrix.yaml").read_text())
    assert matrix["repo_root"] == "."
    cells = matrix["cells"]
    assert len(cells) == 1
    cell = cells[0]
    assert cell["study"] == "LN-06"
    assert cell["tier"] == "T3"
    assert cell["dataset"] == "research_v2/data/ln06/t3_inputs.jsonl"
    assert cell["gold"] == "research_v2/data/ln06/t3_gold.jsonl"
    assert cell["methods"] == MATRIX_METHODS
    assert cell["seeds"] == [11, 23, 37]
    assert cell["split_id"] == "test"
    assert cell["group_key"] == "group_id"
    # 1 cell x 6 methods x 3 seeds = 18 experiment cells.
    assert len(cell["methods"]) * len(cell["seeds"]) == 18


def test_matrix_resolves_to_real_files():
    matrix = yaml.safe_load((EXPERIMENTS / "matrix.yaml").read_text())
    for cell in matrix["cells"]:
        assert (REPO_ROOT / cell["dataset"]).is_file()
        assert (REPO_ROOT / cell["gold"]).is_file()


def test_prereg_locks_primary_contrast_and_counterexample():
    prereg = yaml.safe_load((EXPERIMENTS / "prereg.yaml").read_text())
    assert prereg["study_id"] == "LN-06"
    assert prereg["primary_contrast"]["intervention"] == "proposed"
    assert prereg["primary_contrast"]["comparator"] == "baselines_c1"
    assert prereg["oracle_basis"] == "PEDAGOGICAL_DAG_CONSTRAINTS"
    ce_ids = {ce["id"] for ce in prereg["mandatory_counterexamples"]}
    assert "AB_same_outcome_choose_one" in ce_ids
    assert "asymmetric_travel_closed_checkpoint" in ce_ids
    assert set(prereg["ablation_hypotheses"]) == {
        "ablations_a1", "ablations_a2", "ablations_a3"
    }


def test_splits_declare_sealed_group_holdout():
    splits = yaml.safe_load((EXPERIMENTS / "splits.yaml").read_text())
    assert splits["group_key"] == "group_id"
    test_split = [s for s in splits["splits"] if s["split_id"] == "test"][0]
    assert test_split["n_cases"] == 120 and test_split["sealed"] is True
    rows = load_jsonl(DATASET_PATH)
    groups = [r["group_id"] for r in rows]
    assert len(groups) == len(set(groups)) == 120


def test_dataset_decision_labels_are_within_ln06_space(t3_dataset_paths):
    _, gold_path = t3_dataset_paths
    gold_rows = load_jsonl(gold_path)
    assert len(gold_rows) == 120
    for row in gold_rows:
        assert row["study_id"] == "LN-06"
        assert row["expected_decision"] in DECISION_VALUES
        assert row["oracle_basis"] == "PEDAGOGICAL_DAG_CONSTRAINTS"
    inputs = load_jsonl(DATASET_PATH)
    assert [r["case_id"] for r in inputs] == [r["case_id"] for r in gold_rows]
