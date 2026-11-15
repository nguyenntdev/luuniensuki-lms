"""Run the frozen experiment matrix for one study or all studies."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.evaluation.runner import RunnerError, run_experiment

STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]

# V3-G21: --tier/--seed are now APPLIED, not merely parsed. Selection rules:
# - --tier accepts a comma-separated list (e.g. "T1,T2,T3"); a cell is selected
#   only when its tier is in that list.
# - --seed selects only cells whose declared seeds include the given seed.
# - An empty selection is an ERROR (exit 2) unless --allow-empty-selection is
#   given, so `--all --tier T1` cannot silently run nothing and claim success.


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


def select_cells(
    cells: list[dict],
    *,
    tiers: set[str] | None,
    seed: int | None,
) -> list[dict]:
    """Filter matrix cells by tier set and seed. Pure; used by tests too."""
    selected = []
    for cell in cells:
        if tiers is not None and str(cell.get("tier", "T3")) not in tiers:
            continue
        if seed is not None:
            seeds = cell.get("seeds")
            # no declared seeds -> cannot prove the seed is honored: reject
            if not isinstance(seeds, list) or seed not in seeds:
                continue
            cell = {**cell, "seeds": [seed]}
        selected.append(cell)
    return selected


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run Research V2 experiment matrix")
    ap.add_argument("--study", default=None, help="e.g. LN-06")
    ap.add_argument("--all", action="store_true")
    ap.add_argument(
        "--tier",
        default=None,
        help="Comma-separated tier filter, e.g. T3 or T1,T2,T3 (applied to cell selection)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Run only cells declaring this seed; the run uses exactly this seed",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument(
        "--allow-empty-selection",
        action="store_true",
        help="Permit a tier/seed filter that selects zero cells (otherwise exit 2)",
    )
    ap.add_argument("--output-root", type=Path, default=None)
    a = ap.parse_args(argv)

    studies = [a.study] if a.study else (STUDY_IDS if a.all else [])
    if not studies:
        print("ERROR: pass --study LN-XX or --all", file=sys.stderr)
        return 2

    tiers: set[str] | None = None
    if a.tier is not None:
        parts = a.tier.split(",")
        if any(not t.strip() for t in parts):
            print(f"ERROR: invalid --tier value {a.tier!r}", file=sys.stderr)
            return 2
        tiers = {t.strip().upper() for t in parts}
        if not tiers:
            print(f"ERROR: invalid --tier value {a.tier!r}", file=sys.stderr)
            return 2

    root = _repo_root()
    out_root = a.output_root or (root / "research_artifacts_v2" / "runs")
    failures = 0
    total_selected = 0
    for study in studies:
        matrix = _matrix_paths(study)[0]
        if not matrix.is_file():
            print(f"SKIP {study}: matrix missing at {matrix}", file=sys.stderr)
            failures += 1 if a.strict else 0
            continue

        import yaml

        try:
            raw = yaml.safe_load(matrix.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            print(f"FAIL {study}: matrix unreadable: {exc}", file=sys.stderr)
            failures += 1
            continue
        cells = raw.get("cells") or []

        selected = select_cells(cells, tiers=tiers, seed=a.seed)
        if not selected:
            if a.dry_run:
                print(
                    f"DRY-RUN {study}: matrix {matrix} exists; 0/{len(cells)} cells match "
                    f"tier={a.tier or 'ALL'} seed={a.seed if a.seed is not None else 'ALL'}"
                )
                continue
            print(
                f"ERROR {study}: tier/seed filter selects 0 of {len(cells)} cells "
                f"(tier={a.tier or 'ALL'} seed={a.seed if a.seed is not None else 'ALL'})",
                file=sys.stderr,
            )
            failures += 1
            continue
        total_selected += len(selected)

        if a.dry_run:
            for cell in selected:
                print(
                    f"DRY-RUN {study}: tier={cell.get('tier')} methods={len(cell.get('methods', []))} "
                    f"seeds={cell.get('seeds')} dataset={cell.get('dataset')}"
                )
            continue

        # run only the selected cells
        filtered_matrix = {**raw, "cells": selected}
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            yaml.safe_dump(filtered_matrix, tmp)
            tmp_path = Path(tmp.name)
        try:
            out = run_experiment(tmp_path, out_root, strict=a.strict)
            print(f"OK {study}: {out} (cells={len(selected)})")
        except RunnerError as exc:
            print(f"FAIL {study}: {exc}", file=sys.stderr)
            failures += 1
        finally:
            tmp_path.unlink(missing_ok=True)

    if not a.dry_run and total_selected == 0 and not a.allow_empty_selection:
        print("ERROR: tier/seed selection matched 0 cells overall", file=sys.stderr)
        return 2
    if a.dry_run and total_selected == 0 and not a.allow_empty_selection:
        print("ERROR: tier/seed selection matched 0 cells overall", file=sys.stderr)
        return 2

    if a.strict and failures:
        return 1
    if failures and not a.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

