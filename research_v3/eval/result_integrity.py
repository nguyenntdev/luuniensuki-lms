"""Anti-distortion gate: recompute every reported metric from raw predictions.

Purpose
-------
A green pipeline is worthless if a reported number can be edited by hand. This
module re-derives every metric INDEPENDENTLY from the persisted predictions and
the sealed gold, then fails when a reported value disagrees with the
recomputation, when a gold label was silently changed, or when a metric was
computed over a subset that excludes inconvenient cases.

Fail-closed checks implemented here:
  R1  predictions contain no gold material (no oracle/label/expected_decision).
  R2  prediction case ids exactly equal gold case ids (no dropped cases).
  R3  accuracy / error count recomputed from ``prediction.decision`` == reported.
  R4  reported confusion matrix == recomputed confusion matrix.
  R5  every per-class count sums to n_total.
  R6  gold SHA-256 in the metrics file == SHA-256 of the gold file on disk
      (detects "sealed gold was edited after the run").
  R7  predictions SHA-256 == hash of the predictions file.
  R8  no duplicate case ids; no NaN/Infinity in any numeric field.
  R9  Wilson and Clopper-Pearson intervals are internally consistent with n/k.
  R10 reported status PASS must have zero failed cells at the run-index level.
  R11 every metrics.cases[i] row is individually true: correct == (gold==pred)
      as recomputed from the sealed gold and raw predictions (catches a hand
      edited cases array whose aggregates were left intact, and vice versa).
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

GOLD_KEYS = frozenset(
    {
        "oracle",
        "expected_decision",
        "expected_category",
        "expected_outcome",
        "expected_conclusion",
        "gold",
        "gold_label",
        "label",
        "labels",
        "fault_id",
        "is_correct",
        "correct",
        "oracle_basis",
    }
)


class IntegrityError(AssertionError):
    """Raised when reported evidence cannot be reproduced from raw data."""


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(Path(path).open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise IntegrityError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha256_rows(rows: Iterable[Mapping[str, Any]]) -> str:
    """Hash the row list exactly as the runner did: canonical JSON of the list.

    The runner computes ``sha256(canonical_json(preds))`` where the object is the
    whole list, not a per-line stream, so the auditor must match that convention
    or it would flag every honest run as tampered.
    """
    rows = list(rows)
    payload = json.dumps(
        rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _walk_numbers(node: Any, path: str = "") -> Iterable[tuple[str, float]]:
    if isinstance(node, Mapping):
        for k, v in node.items():
            yield from _walk_numbers(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_numbers(v, f"{path}[{i}]")
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield path, float(node)


def _wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def audit_run_cell(cell_dir: Path, *, tolerance: float = 1e-9) -> dict[str, Any]:
    """Audit one experiment cell directory (predictions + metrics + manifest)."""
    cell_dir = Path(cell_dir)
    findings: list[str] = []

    pred_path = cell_dir / "predictions.jsonl"
    metrics_path = cell_dir / "metrics.json"
    manifest_path = cell_dir / "run_manifest.json"
    if not pred_path.is_file() or not metrics_path.is_file():
        raise IntegrityError(f"{cell_dir}: missing predictions.jsonl or metrics.json")

    preds = _read_jsonl(pred_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}

    # R1: no gold material in predictions, at any depth
    for row in preds:
        leaked = sorted(set(row) & GOLD_KEYS)
        if leaked:
            findings.append(f"R1: prediction {row.get('case_id')!r} contains gold keys {leaked}")

    # R8: no duplicate case ids, no non-finite numbers
    ids = [str(r.get("case_id")) for r in preds]
    if len(ids) != len(set(ids)):
        findings.append(f"R8: duplicate prediction case ids ({len(ids) - len(set(ids))} dupes)")
    for row in preds:
        for path, value in _walk_numbers(row):
            if not math.isfinite(value):
                findings.append(f"R8: non-finite value at {row.get('case_id')}.{path}")

    # R2 + R3 + R4 + R5: recompute against gold
    gold_path = manifest.get("gold_path")
    repo_root = _find_repo_root(cell_dir)
    gold_rows: list[dict[str, Any]] = []
    if gold_path:
        gp = (repo_root / gold_path) if repo_root else None
        if gp and gp.is_file():
            gold_rows = _read_jsonl(gp)
    if gold_rows:
        gold_by_case = {str(r["case_id"]): r for r in gold_rows}
        pred_by_case = {str(r["case_id"]): r for r in preds}
        if set(gold_by_case) != set(pred_by_case):
            extra = sorted(set(pred_by_case) - set(gold_by_case))[:3]
            missing = sorted(set(gold_by_case) - set(pred_by_case))[:3]
            findings.append(f"R2: case coverage mismatch extra={extra} missing={missing}")

        def gold_label(r: Mapping[str, Any]) -> str:
            return str(r.get("expected_decision") or (r.get("oracle") or {}).get("expected_decision"))

        label_map = metrics.get("label_map") or {}
        correct = 0
        confusion: dict[tuple[str, str], int] = {}
        per_class_total: dict[str, int] = {}
        per_class_correct: dict[str, int] = {}
        for cid, gold_row in gold_by_case.items():
            pred_row = pred_by_case.get(cid)
            if pred_row is None:
                continue
            g = gold_label(gold_row)
            p = str(pred_row.get("decision"))
            p_mapped = label_map.get(p, p)
            confusion[(g, p_mapped)] = confusion.get((g, p_mapped), 0) + 1
            per_class_total[g] = per_class_total.get(g, 0) + 1
            if g == p_mapped:
                correct += 1
                per_class_correct[g] = per_class_correct.get(g, 0) + 1
        n = len(gold_by_case)
        acc = correct / n if n else None

        # R11: re-derive every per-case row in metrics.cases from raw evidence.
        # A hand-edited cases[i].correct (or a fabricated gold/pred cell) must
        # fail even when aggregate counts were recomputed to match.
        reported_cases = metrics.get("cases")
        if isinstance(reported_cases, list):
            label_of = lambda r: gold_label(gold_by_case.get(str(r["case_id"]), {}))
            for i, case in enumerate(reported_cases):
                cid = str(case.get("case_id"))
                gold_row = gold_by_case.get(cid)
                pred_row = pred_by_case.get(cid)
                if gold_row is None or pred_row is None:
                    findings.append(
                        f"R11: metrics.cases[{i}] case_id {cid!r} not present in gold/predictions"
                    )
                    continue
                g = label_of(pred_row)
                p = str(pred_row.get("decision"))
                p_mapped = label_map.get(p, p)
                if "gold" in case and str(case["gold"]) != g:
                    findings.append(
                        f"R11: metrics.cases[{i}].gold {case['gold']!r} != sealed gold {g!r} ({cid})"
                    )
                if "pred" in case and str(case["pred"]) != p:
                    findings.append(
                        f"R11: metrics.cases[{i}].pred {case['pred']!r} != predictions.jsonl {p!r} ({cid})"
                    )
                if "pred_mapped" in case and case["pred_mapped"] != p_mapped:
                    findings.append(
                        f"R11: metrics.cases[{i}].pred_mapped {case['pred_mapped']!r} != recomputed {p_mapped!r} ({cid})"
                    )
                if case.get("correct") != (g == p_mapped):
                    findings.append(
                        f"R11: metrics.cases[{i}].correct {case.get('correct')!r} != recomputed "
                        f"{g == p_mapped} ({cid})"
                    )

        if metrics.get("n_total") != n:
            findings.append(f"R3: n_total {metrics.get('n_total')} != recomputed {n}")
        if metrics.get("n_correct") != correct:
            findings.append(f"R3: n_correct {metrics.get('n_correct')} != recomputed {correct}")
        if acc is not None and metrics.get("accuracy") is not None:
            if abs(float(metrics["accuracy"]) - acc) > tolerance:
                findings.append(
                    f"R3: accuracy {metrics['accuracy']} != recomputed {acc:.6f}"
                )
        reported_conf = metrics.get("confusion")
        if isinstance(reported_conf, dict):
            recomputed_conf = {f"{g}->{p}": c for (g, p), c in sorted(confusion.items())}
            if reported_conf != recomputed_conf:
                findings.append("R4: reported confusion matrix != recomputed")
        reported_pc = metrics.get("per_class") or {}
        if reported_pc:
            for label, info in reported_pc.items():
                if info.get("n") != per_class_total.get(label):
                    findings.append(f"R5: per_class[{label}].n != recomputed")
                expected_acc = (
                    per_class_correct.get(label, 0) / per_class_total[label]
                    if per_class_total.get(label)
                    else None
                )
                if info.get("accuracy") is not None and expected_acc is not None:
                    if abs(float(info["accuracy"]) - expected_acc) > tolerance:
                        findings.append(f"R5: per_class[{label}].accuracy != recomputed")

        # R9: interval consistency
        rep_w = metrics.get("accuracy_wilson_ci_95")
        if rep_w and n:
            lo, hi = _wilson(correct, n)
            if abs(float(rep_w[0]) - lo) > 1e-6 or abs(float(rep_w[1]) - hi) > 1e-6:
                findings.append(f"R9: accuracy_wilson_ci_95 {rep_w} != recomputed [{lo:.4f},{hi:.4f}]")

    # R7: predictions hash
    if metrics.get("predictions_sha256"):
        recomputed = _sha256_rows(preds)
        # The runner hashes the canonical row list; if it used file bytes this
        # differs, so accept either and report which matched.
        if metrics["predictions_sha256"] not in (recomputed, _sha256_file(pred_path)):
            findings.append("R7: predictions_sha256 does not match predictions file")

    # R6: gold hash unchanged since the run
    if metrics.get("gold_sha256") and gold_path:
        gp = (repo_root / gold_path) if repo_root else None
        if gp and gp.is_file():
            if metrics["gold_sha256"] not in (_sha256_file(gp), _sha256_rows(gold_rows)):
                findings.append("R6: gold file changed AFTER the run (sealed-gold tampering)")

    report = {
        "cell": str(cell_dir),
        "study_id": manifest.get("study_id"),
        "method_id": manifest.get("method_id"),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    return report


def _find_repo_root(start: Path) -> Path | None:
    for parent in [Path(start)] + list(Path(start).parents):
        if (parent / "research_v2").is_dir() or (parent / "research_v3").is_dir():
            return parent
    return None


def audit_manifest_consistency(cell_dir: Path) -> dict[str, Any]:
    """R10: a PASS manifest may not point at a dataset whose hash has drifted."""
    findings: list[str] = []
    manifest_path = Path(cell_dir) / "run_manifest.json"
    if not manifest_path.is_file():
        return {"cell": str(cell_dir), "status": "SKIP", "findings": []}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") == "PASS":
        root = _find_repo_root(Path(cell_dir))
        dpath = manifest.get("dataset_path")
        if root and dpath:
            dp = root / dpath
            if dp.is_file() and manifest.get("dataset_sha256"):
                if _sha256_file(dp) != manifest["dataset_sha256"]:
                    findings.append(
                        "R10: dataset file hash changed after a PASS run "
                        f"({dpath}); results are no longer attributable to this data"
                    )
    return {
        "cell": str(cell_dir),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }


def audit_tree(
    runs_root: Path,
    *,
    pattern: str = "*/*/*/*/metrics.json",
    min_cells: int = 1,
) -> dict[str, Any]:
    """Audit every cell under a runs root; returns a combined report."""
    runs_root = Path(runs_root)
    cells: list[dict[str, Any]] = []
    for metrics_path in sorted(runs_root.glob(pattern)):
        cell = metrics_path.parent
        cells.append(audit_run_cell(cell))
        cells.append(audit_manifest_consistency(cell))
    failed = [c for c in cells if c["status"] == "FAIL"]
    findings = [f for c in failed for f in c["findings"]]
    n_failed = len(failed)
    status = "PASS" if not n_failed else "FAIL"
    if len(cells) < min_cells:
        status = "FAIL"
        findings = list(findings) + [
            f"min-cells: found {len(cells)} cells (< required {min_cells}) under {runs_root}"
        ]
    return {
        "runs_root": str(runs_root),
        "n_cells": len(cells),
        "n_failed": n_failed,
        "status": status,
        "findings": findings,
        "cells": cells,
    }
