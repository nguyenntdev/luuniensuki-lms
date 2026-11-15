"""Experiment matrix + prereg integrity (LN-07-23 RUNBOOK_AND_MATRIX)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import yaml  # noqa: E402

from research_v2.methods.ln07.dataset import DATASET_PATH, GOLD_PATH, load_jsonl  # noqa: E402
from research_v2.methods.ln07.labels import NATIVE_DECISIONS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = REPO_ROOT / "research_v2" / "experiments" / "ln07"
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
    assert cell["study"] == "LN-07"
    assert cell["tier"] == "T3"
    assert cell["dataset"] == "research_v2/data/ln07/t3_inputs.jsonl"
    assert cell["gold"] == "research_v2/data/ln07/t3_gold.jsonl"
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
    assert prereg["study_id"] == "LN-07"
    assert prereg["primary_contrast"]["intervention"] == "proposed"
    assert prereg["primary_contrast"]["comparator"] == "baselines_c1"
    assert prereg["oracle_basis"] == "DESIGN_SPEC_EMPIRICAL_HOLDOUT"
    assert prereg["primary_endpoint"]["name"] == "task_feasibility_rate"
    ce_ids = {ce["id"] for ce in prereg["mandatory_counterexamples"]}
    assert {
        "raster_image_but_missing_inscription",
        "audio_spatial_shape_without_description",
        "webgl_ok_but_input_device_cannot_manipulate",
        "text_only_complete_task_semantics",
    } <= ce_ids
    assert set(prereg["ablation_hypotheses"]) == {
        "ablations_a1",
        "ablations_a2",
        "ablations_a3",
    }


def test_splits_declare_sealed_group_holdout():
    splits = yaml.safe_load((EXPERIMENTS / "splits.yaml").read_text())
    assert splits["group_key"] == "group_id"
    test_split = [s for s in splits["splits"] if s["split_id"] == "test"][0]
    assert test_split["n_cases"] == 120 and test_split["sealed"] is True
    rows = load_jsonl(DATASET_PATH)
    groups = [r["group_id"] for r in rows]
    assert len(groups) == len(set(groups)) == 120


def test_dataset_labels_within_native_ln07_space():
    gold_rows = load_jsonl(GOLD_PATH)
    assert len(gold_rows) == 120
    for row in gold_rows:
        assert row["study_id"] == "LN-07"
        assert row["expected_decision"] in NATIVE_DECISIONS
        assert row["oracle_basis"] == "DESIGN_SPEC_EMPIRICAL_HOLDOUT"
    inputs = load_jsonl(DATASET_PATH)
    assert [r["case_id"] for r in inputs] == [r["case_id"] for r in gold_rows]
    assert not any("oracle" in r["input"] or "expected_decision" in r["input"] for r in inputs)


def test_runner_discovers_all_matrix_methods():
    from research_v2.evaluation.runner import _resolve_method

    for method in MATRIX_METHODS:
        fn = _resolve_method("LN-07", method)
        assert callable(fn)


def test_matrix_end_to_end_dry_output_matches_gold():
    """Full pipeline: run one cell by hand and verify metrics wiring."""
    from research_v2.contracts.input_masking import mask_case_input
    from research_v2.contracts.types import StudyInput
    from research_v2.evaluation.metrics import compute_metrics
    from research_v2.methods.ln07.proposed import predict_batch
    import tempfile

    rows = load_jsonl(DATASET_PATH)
    inputs = [
        StudyInput(
            study_id="LN-07",
            case_id=r["case_id"],
            split_id="test",
            group_id=r["group_id"],
            features=mask_case_input(r),
        )
        for r in rows
    ]
    preds = predict_batch(inputs, {"seed": 11})
    with tempfile.TemporaryDirectory() as td:
        ppath = Path(td) / "predictions.jsonl"
        with ppath.open("w", encoding="utf-8") as fh:
            for p in preds:
                fh.write(
                    __import__("json").dumps(
                        {
                            **p.to_dict(),
                            "group_id": next(
                                r["group_id"] for r in rows if r["case_id"] == p.case_id
                            ),
                            "split_id": "test",
                            "input_sha256": "0" * 64,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        metrics = compute_metrics(ppath, GOLD_PATH)
        assert metrics["n_total"] == 120
        assert metrics["accuracy"] == 1.0
