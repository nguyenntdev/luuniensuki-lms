"""Aggregate per-cell metrics into study summaries and an evidence matrix."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate(runs_root: Path, out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for metrics_path in sorted(runs_root.glob("*/*/*/*/metrics.json")):
        parts = metrics_path.relative_to(runs_root).parts
        study_id, tier, method_id, seed_dir = parts[0], parts[1], parts[2], parts[3]
        m = _load(metrics_path)
        rows.append(
            {
                "study_id": study_id,
                "tier": tier,
                "method_id": method_id,
                "seed": seed_dir.replace("seed", ""),
                "n_total": m.get("n_total"),
                "accuracy": m.get("accuracy"),
                "error_rate": m.get("error_rate"),
                "error_rate_wilson_low": (m.get("error_rate_wilson_ci_95") or [None, None])[0],
                "error_rate_wilson_high": (m.get("error_rate_wilson_ci_95") or [None, None])[1],
                "predictions_sha256": m.get("predictions_sha256"),
            }
        )

    by_study: dict[str, list[dict]] = {}
    for r in rows:
        by_study.setdefault(r["study_id"], []).append(r)

    summary = {"n_cells": len(rows), "studies": {}}
    for study, cells in by_study.items():
        summary["studies"][study] = {"n_cells": len(cells), "cells": cells}

    (out_root / "aggregate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if rows:
        with (out_root / "evidence_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate Research V2 results")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--preregistered-only", action="store_true")
    ap.add_argument("--runs-root", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    root = _repo_root()
    runs_root = a.runs_root or (root / "research_artifacts_v2" / "runs")
    out = a.out or (root / "research_artifacts_v2" / "release")
    if not runs_root.is_dir():
        print(f"ERROR: runs root missing: {runs_root}", file=sys.stderr)
        return 1
    summary = aggregate(runs_root, out)
    print(json.dumps({"n_cells": summary["n_cells"], "studies": sorted(summary["studies"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
