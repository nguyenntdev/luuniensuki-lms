"""Runner failure-mode tests: metrics errors and missing gold must never
masquerade as a successful strict run.

Every scenario builds a tiny temporary matrix + dataset (+ gold) under
``tmp_path``; no repository data under ``research_v2/data`` is modified. The
LN-06 ``proposed`` method is reused as a real, cheap ``predict_batch`` (2
synthetic cases) so the runner exercises its genuine module-resolution path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes  # noqa: E402
from research_v2.contracts.types import StudyInput  # noqa: E402
from research_v2.evaluation.runner import RunnerError, run_experiment  # noqa: E402
from research_v2.methods.ln06.dataset import TrailCase  # noqa: E402
from research_v2.methods.ln06.proposed import predict_batch as ln06_predict_batch  # noqa: E402

# A minimal feasible LN-06 trail: s1 -> s2 covers o1 -> o2 within budget.
TINY_INPUT: dict = {
    "stops": [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "imperial-site"},
        {"id": "s2", "cost": 10, "provides": ["o2"], "requires": ["o1"], "type": "imperial-site"},
    ],
    "available_stops": ["s1", "s2"],
    "target_outcomes": ["o1", "o2"],
    "time_budget_minutes": 100,
    "checkpoint_claim_verified": True,
}


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )


def _dataset_rows(tmp_path: Path, n_cases: int = 2) -> list[dict]:
    """Build tiny LN-06 fixture rows ({case_id, group_id, input})."""
    rows = [
        {"case_id": f"LT-{i:02d}", "group_id": f"grp-{i:02d}", "input": TINY_INPUT}
        for i in range(1, n_cases + 1)
    ]
    _write_jsonl(tmp_path / "ds" / "inputs.jsonl", rows)
    return rows


def _gold_rows(case_ids: list[str]) -> list[dict]:
    return [
        {"case_id": cid, "expected_decision": "find_valid_route"} for cid in case_ids
    ]


def _write_matrix(tmp_path: Path, cell: dict) -> Path:
    matrix = {"repo_root": str(tmp_path), "cells": [cell]}
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix), encoding="utf-8")
    return matrix_path


def _cell(dataset: str = "ds/inputs.jsonl", gold: str | None = "ds/gold.jsonl") -> dict:
    return {
        "study": "LN-06",
        "tier": "T3",
        "dataset": dataset,
        "gold": gold,
        "methods": ["proposed"],
        "seeds": [11],
        "split_id": "test",
        "group_key": "group_id",
    }


def _cell_dir(out_root: Path) -> Path:
    return out_root / "LN-06" / "T3" / "proposed" / "seed11"


def test_tiny_ln06_input_is_schema_valid_and_feasible() -> None:
    """Guard: the shared tiny fixture is a legal, feasible LN-06 case."""
    case = TrailCase.from_features(TINY_INPUT, case_id="LT-01")
    preds = ln06_predict_batch(
        [
            StudyInput(
                study_id="LN-06",
                case_id="LT-01",
                split_id="test",
                group_id="grp-01",
                features=dict(TINY_INPUT),
            )
        ],
        {"seed": 11},
    )
    assert case.target_outcomes == frozenset({"o1", "o2"})
    assert preds[0].decision == "find_valid_route"


def test_metrics_failure_marks_cell_fail_and_strict_raises(tmp_path: Path) -> None:
    """Gold with an EXTRA case -> compute_metrics raises -> cell FAIL,
    metrics_error.txt written, and a strict run raises RunnerError."""
    rows = _dataset_rows(tmp_path)
    case_ids = [r["case_id"] for r in rows]
    # Intentionally include an extra gold case not present in the dataset.
    _write_jsonl(tmp_path / "ds" / "gold.jsonl", _gold_rows(case_ids + ["LT-EXTRA"]))

    matrix_path = _write_matrix(tmp_path, _cell())
    out_root = tmp_path / "out"

    with pytest.raises(RunnerError) as excinfo:
        run_experiment(matrix_path, out_root, strict=True)
    assert "1 experiment cell(s) failed" in str(excinfo.value)

    index = json.loads((out_root / "run_index.json").read_text(encoding="utf-8"))
    assert index["n_cells"] == 1
    assert index["n_failed"] == 1
    entry = index["cells"][0]
    assert entry["status"] == "FAIL"
    assert entry["error_code"] == "EvaluationError"
    assert entry["metrics_status"] == "error"

    cell_dir = _cell_dir(out_root)
    # Predictions were persisted BEFORE gold was read (no fake success).
    assert (cell_dir / "predictions.jsonl").is_file()
    assert (cell_dir / "metrics_error.txt").is_file()
    assert not (cell_dir / "metrics.json").is_file()

    manifest = json.loads((cell_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAIL"
    assert manifest["error_code"] == "EvaluationError"
    assert manifest["metrics_status"] == "error"


def test_missing_declared_gold_fails_strict_run(tmp_path: Path) -> None:
    """A cell declaring a gold path that does not exist must fail (strict)."""
    _dataset_rows(tmp_path)
    cell = _cell(gold="ds/gold_missing.jsonl")
    matrix_path = _write_matrix(tmp_path, cell)
    out_root = tmp_path / "out"

    with pytest.raises(RunnerError) as excinfo:
        run_experiment(matrix_path, out_root, strict=True)
    assert "1 experiment cell(s) failed" in str(excinfo.value)

    index = json.loads((out_root / "run_index.json").read_text(encoding="utf-8"))
    assert index["n_failed"] == 1
    entry = index["cells"][0]
    assert entry["status"] == "FAIL"
    assert entry["error_code"] == "MISSING_GOLD"


def test_method_module_failure_marks_cell_fail_and_strict_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A method module whose predict_batch raises must FAIL its cell; strict raises."""
    _dataset_rows(tmp_path)
    _write_jsonl(tmp_path / "ds" / "gold.jsonl", _gold_rows(["LT-01", "LT-02"]))

    # Deterministically break the resolved LN-06 method: the runner imports
    # research_v2.methods.ln06.proposed and calls its predict_batch.
    def broken_predict_batch(inputs, config=None):
        raise RuntimeError("synthetic method crash")

    import research_v2.methods.ln06.proposed as ln06_proposed

    monkeypatch.setattr(ln06_proposed, "predict_batch", broken_predict_batch)

    matrix_path = _write_matrix(tmp_path, _cell())
    out_root = tmp_path / "out"

    with pytest.raises(RunnerError) as excinfo:
        run_experiment(matrix_path, out_root, strict=True)
    assert "1 experiment cell(s) failed" in str(excinfo.value)

    index = json.loads((out_root / "run_index.json").read_text(encoding="utf-8"))
    entry = index["cells"][0]
    assert entry["study_id"] == "LN-06"
    assert entry["status"] in {"FAIL", "ERROR"}
    assert entry["metrics_status"] == "not_computed"

    cell_dir = _cell_dir(out_root)
    assert (cell_dir / "error.txt").is_file() or (cell_dir / "traceback.txt").is_file()
    assert not (cell_dir / "metrics.json").is_file()


def test_clean_matrix_strict_run_passes_with_metrics(tmp_path: Path) -> None:
    """Clean tiny matrix: strict run returns the output root with metrics.json."""
    rows = _dataset_rows(tmp_path)
    _write_jsonl(
        tmp_path / "ds" / "gold.jsonl",
        _gold_rows([r["case_id"] for r in rows]),
    )
    matrix_path = _write_matrix(tmp_path, _cell())
    out_root = tmp_path / "out"

    result = run_experiment(matrix_path, out_root, strict=True)
    assert result == out_root
    assert result.is_dir()

    index = json.loads((result / "run_index.json").read_text(encoding="utf-8"))
    assert index["n_cells"] == 1
    assert index["n_failed"] == 0
    entry = index["cells"][0]
    assert entry["status"] == "PASS"
    assert entry["metrics_status"] == "ok"

    cell_dir = _cell_dir(result)
    metrics = json.loads((cell_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["n_total"] == 2
    assert metrics["n_correct"] == 2
    assert metrics["accuracy"] == 1.0

    manifest = json.loads((cell_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert manifest["metrics_status"] == "ok"
    # Predictions follow the canonical hashing standard for masked inputs.
    preds = [
        json.loads(line)
        for line in (cell_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {p["case_id"] for p in preds} == {r["case_id"] for r in rows}
    # input_sha256 must equal the canonical digest of the masked features.
    for p, r in zip(preds, rows):
        assert p["input_sha256"] == sha256_bytes(canonical_json(r["input"]))


def test_metrics_failure_isolated_across_cells_non_strict(tmp_path: Path) -> None:
    """Non-strict: one cell's metrics failure must not abort sibling cells."""
    rows = _dataset_rows(tmp_path)
    case_ids = [r["case_id"] for r in rows]
    _write_jsonl(tmp_path / "ds" / "gold.jsonl", _gold_rows(case_ids))
    _write_jsonl(
        tmp_path / "ds" / "gold_extra.jsonl", _gold_rows(case_ids + ["LT-EXTRA"])
    )

    good = _cell(gold="ds/gold.jsonl")
    bad = {**_cell(gold="ds/gold_extra.jsonl"), "study": "LN-02"}
    matrix = {"repo_root": str(tmp_path), "cells": [good, bad]}
    matrix_path = tmp_path / "matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix), encoding="utf-8")
    out_root = tmp_path / "out"

    result = run_experiment(matrix_path, out_root, strict=False)
    index = json.loads((result / "run_index.json").read_text(encoding="utf-8"))
    by_study = {c["study_id"]: c for c in index["cells"]}
    assert by_study["LN-06"]["status"] == "PASS"
    assert by_study["LN-06"]["metrics_status"] == "ok"
    assert by_study["LN-02"]["status"] == "FAIL"
    assert by_study["LN-02"]["metrics_status"] == "error"
    assert index["n_failed"] == 1
