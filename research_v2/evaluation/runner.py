"""Experiment matrix runner.

Reads a YAML matrix describing studies, datasets, methods and seeds; invokes the
method's ``predict_batch``; writes oracle-free predictions, a run manifest and
environment capture; and evaluates against sealed gold via the metrics module.
"""
from __future__ import annotations

import json
import platform
import time
import traceback
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

from ..contracts.canonical_hash import canonical_json, sha256_bytes, sha256_file
from ..contracts.input_masking import mask_case_input
from ..contracts.types import ContractError, StudyInput, StudyPrediction
from .metrics import compute_metrics

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required for the experiment runner") from exc


class RunnerError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for lineno, line in enumerate(Path(path).open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RunnerError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _git_sha(repo_root: Path) -> str:
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), text=True
        ).strip()
    except Exception:
        return "unknown"


def _resolve_method(study_id: str, method_id: str):
    """Import ``research_v2.methods.<lnXX>.<module>.predict_batch``."""
    ln = study_id.lower().replace("-", "")
    module = import_module(f"research_v2.methods.{ln}.{method_id}")
    fn = getattr(module, "predict_batch", None)
    if fn is None:
        raise RunnerError(f"method {method_id!r} for {study_id} has no predict_batch")
    return fn


def run_experiment(matrix_path: Path, output_root: Path, strict: bool = True) -> Path:
    """Execute every (study, dataset, method, seed) cell declared in the matrix."""
    matrix = _load_yaml(Path(matrix_path))
    repo_root = Path(matrix.get("repo_root", matrix_path.parent.parent.parent)).resolve()
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    cells = matrix.get("cells", [])
    if not cells:
        raise RunnerError(f"matrix {matrix_path} declares no cells")
    commit = _git_sha(repo_root)
    summary: list[dict[str, Any]] = []
    failed = 0

    for cell in cells:
        study_id = cell["study"]
        tier = cell.get("tier", "T3")
        dataset_path = (repo_root / cell["dataset"]).resolve()
        gold_path = (repo_root / cell["gold"]).resolve() if cell.get("gold") else None
        methods = cell.get("methods", [])
        seeds = cell.get("seeds", [11])
        split_id = cell.get("split_id", "test")
        group_key = cell.get("group_key", "group_id")
        label_map = cell.get("label_map") or {}

        if not dataset_path.is_file():
            _record_missing_matrix(cell, summary, "MISSING_DATASET")
            if strict:
                failed += 1
            continue

        rows = _load_jsonl(dataset_path)
        dataset_sha = sha256_file(dataset_path)

        for method_id in methods:
            for seed in seeds:
                cell_dir = output_root / study_id / f"{tier}" / method_id / f"seed{seed}"
                cell_dir.mkdir(parents=True, exist_ok=True)
                started = time.time()
                status = "PASS"
                error_code = None
                pred_rows: list[dict[str, Any]] = []
                try:
                    predict_batch = _resolve_method(study_id, method_id)
                    inputs = [
                        StudyInput(
                            study_id=study_id,
                            case_id=row["case_id"],
                            split_id=split_id,
                            group_id=str(row.get(group_key) or row.get("group_id") or row["case_id"]),
                            features=mask_case_input(row),
                        )
                        for row in rows
                    ]
                    preds = predict_batch(inputs, {"seed": seed})
                    if len(preds) != len(inputs):
                        raise RunnerError(
                            f"{method_id}: returned {len(preds)} predictions for {len(inputs)} inputs"
                        )
                    for inp, pred in zip(inputs, preds):
                        if not isinstance(pred, StudyPrediction):
                            raise RunnerError(f"{method_id}: predict_batch must return StudyPrediction")
                        if pred.case_id != inp.case_id:
                            raise RunnerError(f"{method_id}: case_id mismatch {pred.case_id} != {inp.case_id}")
                        pred_rows.append(
                            {
                                **pred.to_dict(),
                                "group_id": inp.group_id,
                                "split_id": inp.split_id,
                                "input_sha256": sha256_bytes(canonical_json(inp.features)),
                            }
                        )
                    _write_jsonl(cell_dir / "predictions.jsonl", pred_rows)
                except (ContractError, RunnerError) as exc:
                    status = "FAIL"
                    error_code = type(exc).__name__
                    (cell_dir / "error.txt").write_text(str(exc) + "\n", encoding="utf-8")
                    failed += 1
                except Exception:  # pragma: no cover - captured with full trace
                    status = "ERROR"
                    error_code = "UnhandledException"
                    (cell_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
                    failed += 1

                wall_ms = (time.time() - started) * 1000.0
                manifest = {
                    "study_id": study_id,
                    "tier": tier,
                    "dataset_path": str(dataset_path.relative_to(repo_root)),
                    "dataset_sha256": dataset_sha,
                    "gold_path": str(gold_path.relative_to(repo_root)) if gold_path else None,
                    "method_id": method_id,
                    "seed": seed,
                    "split_id": split_id,
                    "source_commit": commit,
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "wall_ms": round(wall_ms, 3),
                    "status": status,
                    "error_code": error_code,
                    "n_inputs": len(rows),
                }
                (cell_dir / "run_manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )

                if status == "PASS" and gold_path and gold_path.is_file():
                    try:
                        metrics = compute_metrics(
                            cell_dir / "predictions.jsonl", gold_path, label_map=label_map
                        )
                        (cell_dir / "metrics.json").write_text(
                            json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                        )
                    except Exception as exc:  # pragma: no cover
                        (cell_dir / "metrics_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
                summary.append(manifest)

    index = {
        "matrix": str(matrix_path),
        "source_commit": commit,
        "cells": summary,
        "n_cells": len(summary),
        "n_failed": failed,
    }
    (output_root / "run_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if strict and failed:
        raise RunnerError(f"{failed} experiment cell(s) failed; see {output_root / 'run_index.json'}")
    return output_root


def _record_missing_matrix(cell: Mapping[str, Any], summary: list[dict[str, Any]], code: str) -> None:
    summary.append({"study_id": cell.get("study"), "tier": cell.get("tier"), "status": code})
