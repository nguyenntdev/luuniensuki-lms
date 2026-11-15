"""Experiment matrix + prereg integrity (23_RUNBOOK_AND_MATRIX)."""
from __future__ import annotations

from pathlib import Path

import yaml

from ln08_helpers import DATA_DIR, load_t3_inputs, load_t3_gold

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = REPO_ROOT / "research_v2" / "experiments" / "ln08"
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
    assert cell["study"] == "LN-08"
    assert cell["tier"] == "T3"
    assert cell["dataset"] == "research_v2/data/ln08/t3_inputs.jsonl"
    assert cell["gold"] == "research_v2/data/ln08/t3_gold.jsonl"
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


def test_prereg_locks_primary_contrast_and_counterexamples():
    prereg = yaml.safe_load((EXPERIMENTS / "prereg.yaml").read_text())
    assert prereg["study_id"] == "LN-08"
    assert prereg["primary_contrast"]["intervention"] == "proposed"
    assert prereg["primary_contrast"]["comparator"] == "baselines_c1"
    assert prereg["oracle_basis"] == "DIAGNOSTIC_FEEDBACK_SPEC"
    ce_ids = {ce["id"] for ce in prereg["mandatory_counterexamples"]}
    assert "keyword_complete_but_reversed" in ce_ids
    assert "correct_paraphrase_no_exact_keywords" in ce_ids
    assert "fabricated_source_locator" in ce_ids
    assert set(prereg["ablation_hypotheses"]) == {
        "ablations_a1", "ablations_a2", "ablations_a3"
    }


def test_splits_declare_sealed_group_holdout():
    splits = yaml.safe_load((EXPERIMENTS / "splits.yaml").read_text())
    assert splits["group_key"] == "group_id"
    test_split = [s for s in splits["splits"] if s["split_id"] == "test"][0]
    assert test_split["n_cases"] == 120 and test_split["sealed"] is True
    rows = load_t3_inputs()
    groups = [r["group_id"] for r in rows]
    assert len(groups) == len(set(groups)) == 120


def test_dataset_decision_labels_are_within_declared_spaces():
    """Gold uses native legacy labels; every one must map into the frozen
    contract space via the documented deterministic mapping."""
    from research_v2.methods.ln08.labels import NATIVE_DECISIONS, NATIVE_TO_CONTRACT

    gold_rows = [
        line
        for line in (DATA_DIR / "t3_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(gold_rows) == 120
    for line in gold_rows:
        row = __import__("json").loads(line)
        assert row["study_id"] == "LN-08"
        assert row["expected_decision"] in NATIVE_DECISIONS
        assert NATIVE_TO_CONTRACT[row["expected_decision"]] in (
            __import__("research_v2.contracts.label_space", fromlist=["LN08_DECISIONS"]).LN08_DECISIONS
        )
        assert row["oracle_basis"] == "DIAGNOSTIC_FEEDBACK_SPEC"
    inputs = load_t3_inputs()
    assert [r["case_id"] for r in inputs] == [
        __import__("json").loads(l)["case_id"] for l in gold_rows
    ]


def test_gold_balanced_strata():
    gold = load_t3_gold()
    strata: dict[str, int] = {}
    for label in gold.values():
        strata[label] = strata.get(label, 0) + 1
    assert set(strata.values()) == {24}
