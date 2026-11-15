"""CLI: recompute and verify every reported metric from raw predictions.

Usage:
  python -m research_v3.scripts.result_integrity --runs-root research_artifacts_v2/runs
  python -m research_v3.scripts.result_integrity --cell research_artifacts_v2/runs/LN-06/T3/proposed/seed11
  python -m research_v3.scripts.result_integrity --runs-root <dir> --pattern '*/*/*/*/metrics.json' --json

Fail-closed by default:
  - zero matched cells fails unless ``--allow-empty`` is given explicitly
    (the ONLY escape hatch, for auditing a root that is legitimately empty);
  - ``--min-cells N`` (default 1) fails when fewer than N cells are audited,
    e.g. ``--min-cells 190`` guards against silently dropped run cells.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v3.eval.result_integrity import (
    IntegrityError,
    audit_manifest_consistency,
    audit_run_cell,
    audit_tree,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Recompute metrics from raw predictions and fail on any mismatch")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--runs-root", type=Path, help="audit every experiment cell under this root")
    group.add_argument("--cell", type=Path, help="audit a single experiment cell directory")
    ap.add_argument("--pattern", default="*/*/*/*/metrics.json")
    ap.add_argument(
        "--min-cells",
        type=int,
        default=1,
        metavar="N",
        help="fail when fewer than N experiment cells are audited (default: 1)",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--allow-empty",
        action="store_true",
        help=(
            "do not fail when no cells matched (default: fail closed). This is the "
            "ONLY escape hatch from the empty-root check; --min-cells still applies "
            "to any cells that do match."
        ),
    )
    a = ap.parse_args(argv)

    try:
        if a.cell is not None:
            report = audit_run_cell(a.cell)
            cons = audit_manifest_consistency(a.cell)
            failed = report["status"] == "FAIL" or cons["status"] == "FAIL"
            out = {"status": "FAIL" if failed else "PASS", "cells": [report, cons]}
        else:
            out = audit_tree(a.runs_root, pattern=a.pattern, min_cells=max(a.min_cells, 1))
            if out["n_cells"] == 0 and not a.allow_empty:
                out["status"] = "FAIL"
                out["findings"] = [f"no experiment cells matched {a.pattern} under {a.runs_root}"]
    except IntegrityError as exc:
        print(f"RESULT INTEGRITY ERROR: {exc}", file=sys.stderr)
        return 2

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        cells = out.get("n_cells", len(out.get("cells", [])))
        print(f"status={out['status']} cells={cells}")
        for finding in out.get("findings", [])[:20]:
            print(f"  - {finding}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
