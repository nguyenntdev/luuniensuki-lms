"""Adversarial tests for the anti-distortion gate.

Each test starts from a REAL experiment cell, copies it to a temp dir, and makes
exactly one dishonest edit. The auditor MUST catch every one. If any of these
passes silently, a reported number could be faked, so the gate itself would be
worthless.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from research_v3.eval.result_integrity import (
    audit_manifest_consistency,
    audit_run_cell,
    audit_tree,
)

REPO = Path(__file__).resolve().parents[3]
V2_RUNS = REPO / "research_artifacts_v2" / "runs"
CELL = V2_RUNS / "LN-06" / "T3" / "proposed" / "seed11"


def _copy_cell(tmp_path: Path) -> Path:
    if not CELL.is_dir():
        pytest.skip("reference experiment cell not present")
    dest = tmp_path / "cell"
    shutil.copytree(CELL, dest)
    # audit_run_cell locates gold relative to a repo root, so give the copy one.
    (tmp_path / "research_v2").mkdir(exist_ok=True)
    (tmp_path / "research_v2" / "data" / "ln06").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "research_v2" / "data" / "ln06" / "t3_gold.jsonl",
                tmp_path / "research_v2" / "data" / "ln06" / "t3_gold.jsonl")
    return dest


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_jsonl(p: Path, rows: list[dict]) -> None:
    p.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                 encoding="utf-8")


def test_clean_cell_passes(tmp_path):
    cell = _copy_cell(tmp_path)
    assert audit_run_cell(cell)["status"] == "PASS"


def test_inflated_accuracy_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    metrics["accuracy"] = 0.999999  # a number nobody could have measured here
    (cell / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R3: accuracy" in f for f in report["findings"])


def test_inflated_n_correct_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    # Make the claim strictly impossible: more correct than cases evaluated.
    metrics["n_correct"] = metrics["n_total"] + 1
    metrics["accuracy"] = 1.5
    (cell / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any(f.startswith("R3") for f in report["findings"])


def test_dropped_hard_cases_is_caught(tmp_path):
    """Removing the incorrect cases from predictions must not produce a clean PASS."""
    cell = _copy_cell(tmp_path)
    preds = _read_jsonl(cell / "predictions.jsonl")
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    wrong = {c["case_id"] for c in metrics["cases"] if not c["correct"]}
    if not wrong:
        pytest.skip("reference cell has no errors to drop")
    _write_jsonl(cell / "predictions.jsonl", [p for p in preds if p["case_id"] not in wrong])
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R2: case coverage mismatch" in f for f in report["findings"])


def test_edited_cases_correct_is_caught(tmp_path):
    """R11: flipping a single cases[i].correct without touching predictions.jsonl
    or the aggregates must fail the per-case recompute."""
    cell = _copy_cell(tmp_path)
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    target_idx = next(
        (i for i, c in enumerate(metrics["cases"]) if c["correct"]),
        None,
    )
    if target_idx is None:
        pytest.skip("reference cell has no correct cases to flip")
    target_id = metrics["cases"][target_idx]["case_id"]
    metrics["cases"][target_idx]["correct"] = False
    (cell / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any(
        f"R11" in f and target_id in f for f in report["findings"]
    ), report["findings"]


def test_edited_cases_gold_is_caught(tmp_path):
    """R11: rewriting the recorded gold of one case row must also fail."""
    cell = _copy_cell(tmp_path)
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    metrics["cases"][0]["gold"] = "__forged_gold__"
    (cell / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R11" in f for f in report["findings"])


def test_inflated_n_total_is_caught(tmp_path):
    """R3 explicit: an n_total larger than the gold row count is impossible."""
    cell = _copy_cell(tmp_path)
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    n_gold = len(_read_jsonl(tmp_path / "research_v2" / "data" / "ln06" / "t3_gold.jsonl"))
    metrics["n_total"] = n_gold + 1  # claims more cases than the sealed gold has
    (cell / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R3: n_total" in f for f in report["findings"])


def test_flipped_prediction_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    preds = _read_jsonl(cell / "predictions.jsonl")
    metrics = json.loads((cell / "metrics.json").read_text(encoding="utf-8"))
    wrong = {c["case_id"] for c in metrics["cases"] if not c["correct"]}
    if not wrong:
        pytest.skip("reference cell has no errors to flip")
    target = sorted(wrong)[0]
    for row in preds:
        if row["case_id"] == target:
            row["decision"] = "__fake_correct__"
    _write_jsonl(cell / "predictions.jsonl", preds)
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    # Either accuracy/confusion drift or the hash guard must fire.
    assert any(f.startswith(("R3", "R4", "R7")) for f in report["findings"])


def test_gold_tampering_after_run_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    gold = tmp_path / "research_v2" / "data" / "ln06" / "t3_gold.jsonl"
    rows = _read_jsonl(gold)
    rows[0]["expected_decision"] = "__edited_after_run__"
    _write_jsonl(gold, rows)
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R6: gold file changed" in f for f in report["findings"])


def test_duplicate_prediction_case_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    preds = _read_jsonl(cell / "predictions.jsonl")
    preds.append(dict(preds[0]))
    _write_jsonl(cell / "predictions.jsonl", preds)
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R8: duplicate prediction case ids" in f for f in report["findings"])


def test_gold_leak_in_prediction_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    preds = _read_jsonl(cell / "predictions.jsonl")
    preds[0]["expected_decision"] = "find_valid_route"
    _write_jsonl(cell / "predictions.jsonl", preds)
    report = audit_run_cell(cell)
    assert report["status"] == "FAIL"
    assert any("R1" in f for f in report["findings"])


def test_dataset_drift_after_pass_is_caught(tmp_path):
    cell = _copy_cell(tmp_path)
    root = tmp_path
    (root / "research_v2" / "data" / "ln06").mkdir(parents=True, exist_ok=True)
    src = REPO / "research_v2" / "data" / "ln06" / "t3_inputs.jsonl"
    dst = root / "research_v2" / "data" / "ln06" / "t3_inputs.jsonl"
    shutil.copy(src, dst)
    manifest_path = cell / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib
    manifest["dataset_path"] = "research_v2/data/ln06/t3_inputs.jsonl"
    manifest["dataset_sha256"] = hashlib.sha256(dst.read_bytes()).hexdigest()
    manifest["status"] = "PASS"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    # now edit the dataset
    dst.write_text(dst.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    report = audit_manifest_consistency(cell)
    assert report["status"] == "FAIL"
    assert any("R10" in f for f in report["findings"])


def test_tree_audit_end_to_end(tmp_path):
    cell = _copy_cell(tmp_path)
    # audit_tree expects <root>/<study>/<tier>/<method>/seedN; mirror that layout.
    shaped = tmp_path / "tree" / "LN-06" / "T3" / "proposed" / "seed11"
    shaped.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(cell, shaped)
    report = audit_tree(tmp_path / "tree")
    assert report["n_cells"] >= 1
    assert report["status"] == "PASS"


def test_tree_audit_min_cells_enforced(tmp_path):
    """Fewer cells than the required minimum must flip the tree audit to FAIL."""
    cell = _copy_cell(tmp_path)
    shaped = tmp_path / "tree" / "LN-06" / "T3" / "proposed" / "seed11"
    shaped.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(cell, shaped)
    report = audit_tree(tmp_path / "tree", min_cells=5)
    assert report["n_cells"] < 5
    assert report["status"] == "FAIL"
    assert any("min-cells" in f for f in report["findings"])
