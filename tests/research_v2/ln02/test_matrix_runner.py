"""Runner integration: matrix cell executes end-to-end through the real
runner path (resolving methods by module alias) and evaluates via metrics."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from research_v2.evaluation.runner import run_experiment  # noqa: E402
from research_v2.contracts.types import StudyPrediction  # noqa: E402
from research_v2.methods.ln02 import metrics as ln02_metrics  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX = REPO_ROOT / "research_v2" / "experiments" / "ln02" / "matrix.yaml"
EXPECTED_METHODS = [
    "proposed",
    "baselines_b0",
    "baselines_c1",
    "ablations_a1",
    "ablations_a2",
    "ablations_a3",
]


def test_matrix_yaml_declares_expected_cell():
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    assert matrix["repo_root"] == "."
    cells = matrix["cells"]
    assert len(cells) == 1
    cell = cells[0]
    assert cell["study"] == "LN-02"
    assert cell["tier"] == "T3"
    assert cell["dataset"] == "research_v2/data/ln02/t3_inputs.jsonl"
    assert cell["gold"] == "research_v2/data/ln02/t3_gold.jsonl"
    assert cell["methods"] == EXPECTED_METHODS
    assert cell["seeds"] == [11, 23, 37]
    assert cell["split_id"] == "test"
    assert cell["group_key"] == "group_id"


def test_prereg_and_splits_yaml_are_valid():
    prereg = yaml.safe_load(
        (REPO_ROOT / "research_v2" / "experiments" / "ln02" / "prereg.yaml").read_text(encoding="utf-8")
    )
    assert prereg["study_id"] == "LN-02"
    assert prereg["seeds"] == [11, 23, 37]
    assert prereg["primary_endpoint"]["name"] == "decision_accuracy"
    splits = yaml.safe_load(
        (REPO_ROOT / "research_v2" / "experiments" / "ln02" / "splits.yaml").read_text(encoding="utf-8")
    )
    assert splits["split_policy"] == "grouped_holdout"
    assert splits["splits"][0]["split_id"] == "test"


def test_runner_executes_all_matrix_cells(tmp_path):
    out_root = tmp_path / "runs"
    result = run_experiment(MATRIX, out_root, strict=True)
    index = json.loads((result / "run_index.json").read_text(encoding="utf-8"))
    assert index["n_cells"] == len(EXPECTED_METHODS) * 3  # methods x seeds
    assert index["n_failed"] == 0
    for entry in index["cells"]:
        assert entry["status"] == "PASS", entry


def test_runner_predictions_are_wellformed_and_evaluable(tmp_path):
    out_root = tmp_path / "runs"
    result = run_experiment(MATRIX, out_root, strict=True)
    cell_dir = result / "LN-02" / "T3" / "proposed" / "seed11"
    pred_rows = [
        json.loads(line)
        for line in (cell_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(pred_rows) == 120
    for row in pred_rows:
        assert row["study_id"] == "LN-02"
        assert isinstance(row["decision"], str)
        for forbidden in ("oracle", "expected_decision", "gold_label", "fault_id"):
            assert forbidden not in row
    metrics_path = cell_dir / "metrics.json"
    assert metrics_path.is_file()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["n_total"] == 120


def test_runner_method_aliases_resolve_predict_batch():
    from research_v2.evaluation.runner import _resolve_method

    for method_id in EXPECTED_METHODS:
        fn = _resolve_method("LN-02", method_id)
        assert callable(fn)
        assert fn.__name__ == "predict_batch"


def test_study_diagnostics_summarize_runner_predictions(tmp_path):
    out_root = tmp_path / "runs"
    result = run_experiment(MATRIX, out_root, strict=True)
    pred_path = result / "LN-02" / "T3" / "proposed" / "seed11" / "predictions.jsonl"
    preds = [
        json.loads(line)
        for line in pred_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    # Study-local diagnostics operate on prediction labels; gold stays sealed.
    labels = [row["decision"] for row in preds]
    histogram = ln02_metrics.label_histogram(labels)
    assert set(histogram) <= {
        "recommend_eligible",
        "remediate_first",
        "abstain_insufficient_data",
        "reject_cycle",
        "reject_invalid_score",
    }
    assert sum(histogram.values()) == 120


def test_all_predictions_are_studyprediction_instances():
    from research_v2.methods.ln02.baselines_b0 import predict_batch as b0

    from ln02_helpers import make_input

    preds = b0([make_input()], {})
    assert isinstance(preds[0], StudyPrediction)
