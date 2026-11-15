"""Run the frozen experiment matrix for one study or all studies."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.evaluation.runner import RunnerError, run_experiment

STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _matrix_paths(study: str | None) -> list[Path]:
    root = _repo_root()
    if study:
        return [root / "research_v2" / "experiments" / study.lower().replace("-", "") / "matrix.yaml"]
    return [
        root / "research_v2" / "experiments" / s.lower().replace("-", "") / "matrix.yaml"
        for s in STUDY_IDS
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run Research V2 experiment matrix")
    ap.add_argument("--study", default=None, help="e.g. LN-06")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tier", default=None, help="T1,T2,T3 filter (informational)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--output-root", type=Path, default=None)
    a = ap.parse_args(argv)

    studies = [a.study] if a.study else (STUDY_IDS if a.all else [])
    if not studies:
        print("ERROR: pass --study LN-XX or --all", file=sys.stderr)
        return 2

    root = _repo_root()
    out_root = a.output_root or (root / "research_artifacts_v2" / "runs")
    failures = 0
    for study in studies:
        matrix = _matrix_paths(study)[0]
        if not matrix.is_file():
            print(f"SKIP {study}: matrix missing at {matrix}", file=sys.stderr)
            failures += 1 if a.strict else 0
            continue
        if a.dry_run:
            print(f"DRY-RUN {study}: matrix {matrix} exists")
            continue
        try:
            out = run_experiment(matrix, out_root, strict=a.strict)
            print(f"OK {study}: {out}")
        except RunnerError as exc:
            print(f"FAIL {study}: {exc}", file=sys.stderr)
            failures += 1

    if a.strict and failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
