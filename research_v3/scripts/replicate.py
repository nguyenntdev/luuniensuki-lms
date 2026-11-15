"""V3-G13: deterministic-vs-stochastic replication guard.

Enforces the spec rule (04_METHODOLOGY / reliability rules):
- deterministic methods must be BYTE-IDENTICAL across repeated runs — any
  prediction-hash drift is a determinism violation;
- stochastic methods require >= 5 INDEPENDENT seeds, and the report must state
  explicitly that identical hashes across seeds are NOT independent replicates
  (seed pseudo-replication).

Input: a run directory containing seed*/predictions.jsonl (V2/V3 layout) or an
explicit method kind. Fail-closed: violations exit nonzero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from research_v3.scripts._paths import RESEARCH_V3_ROOT

DEFAULT_RUNS = RESEARCH_V3_ROOT.parent / "research_artifacts_v3" / "runs"
MIN_INDEPENDENT_SEEDS = 5

EXIT_OK = 0
EXIT_GUARD_FAILED = 15


class ReplicationError(ValueError):
    """Raised when the replication contract is violated."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_seed_hashes(run_dir: Path) -> dict[str, str]:
    """Map seed-name -> predictions sha256 from a run directory."""
    hashes: dict[str, str] = {}
    for seed_dir in sorted(p for p in run_dir.iterdir() if p.is_dir() and p.name.startswith("seed")):
        pred = seed_dir / "predictions.jsonl"
        if not pred.is_file():
            raise ReplicationError(f"{run_dir.name}/{seed_dir.name}: predictions.jsonl missing")
        hashes[seed_dir.name] = _sha256_file(pred)
    if not hashes:
        raise ReplicationError(f"{run_dir}: no seed*/predictions.jsonl found")
    return hashes


def guard(
    *,
    method_kind: str,
    seed_hashes: dict[str, str],
    min_seeds: int = MIN_INDEPENDENT_SEEDS,
) -> dict:
    """Pure guard. Raises ReplicationError on violation; returns the report."""
    if method_kind not in {"deterministic", "stochastic"}:
        raise ReplicationError(f"unknown method kind {method_kind!r}")
    unique = set(seed_hashes.values())
    n_seeds = len(seed_hashes)
    identical_across_seeds = len(unique) == 1 and n_seeds > 1

    report: dict = {
        "schema": "research_v3.replication_guard/v1",
        "task_id": "V3-G13",
        "method_kind": method_kind,
        "n_seeds": n_seeds,
        "n_unique_prediction_hashes": len(unique),
        "identical_across_seeds": identical_across_seeds,
        "seed_hashes": dict(sorted(seed_hashes.items())),
        "status": "PASS",
        "warnings": [],
    }

    if method_kind == "deterministic":
        if not identical_across_seeds and n_seeds > 1:
            report["status"] = "FAIL"
            raise ReplicationError(
                f"deterministic method produced {len(unique)} distinct prediction hashes "
                f"across {n_seeds} seeds — byte-identical reproduction required"
            )
        report["verdict"] = (
            "Byte-identical across runs: deterministic contract holds. Note: the "
            "repeated runs are the SAME replicate, not independent evidence."
        )
        return report

    # stochastic
    if n_seeds < min_seeds:
        report["status"] = "FAIL"
        raise ReplicationError(
            f"stochastic method has {n_seeds} seed(s); at least {min_seeds} INDEPENDENT "
            "seeds are required"
        )
    if identical_across_seeds:
        report["status"] = "FAIL"
        report["warnings"].append(
            "Identical prediction hashes across seeds: these are seed "
            "pseudo-replications, NOT independent replicates. Either the method is "
            "actually deterministic (redeclare it) or the seeds were not applied."
        )
        raise ReplicationError(
            "stochastic method shows identical hashes across seeds — NOT independent "
            "replicates (seed pseudo-replication)"
        )
    report["verdict"] = (
        f"{n_seeds} seeds with distinct prediction hashes: treated as independent "
        "replicates for variance estimation."
    )
    return report


def discover_run_dirs(runs_root: Path, *, study: str | None, method: str | None) -> list[Path]:
    if not runs_root.is_dir():
        raise ReplicationError(f"runs root not found: {runs_root}")
    if study and method:
        candidates = [runs_root / study / method]
    elif study:
        candidates = sorted(p for p in runs_root.glob(study) if p.is_dir())
    elif method:
        candidates = sorted(p for p in runs_root.glob(f"*/{method}") if p.is_dir())
    else:
        candidates = sorted(p for p in runs_root.glob("*/*") if p.is_dir())
    dirs = sorted(
        p for p in candidates if p.is_dir() and any(p.glob("seed*/predictions.jsonl"))
    )
    if not dirs:
        raise ReplicationError(
            f"no run directories under {runs_root} (study={study!r}, method={method!r}) "
            "with seed*/predictions.jsonl"
        )
    return dirs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.replicate",
        description=(
            "Replication guard: deterministic methods must be byte-identical "
            "across runs; stochastic methods need >=5 independent seeds and must "
            "report that identical hashes are NOT independent replicates (V3-G13)."
        ),
    )
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS, help="Root containing <study>/<method>/seed*/")
    parser.add_argument("--study", default=None, help="Limit to one study/dir (glob)")
    parser.add_argument("--method", default=None, help="Limit to one method/dir (glob)")
    parser.add_argument(
        "--kind",
        choices=["deterministic", "stochastic"],
        required=True,
        help="Declare the method kind honestly",
    )
    parser.add_argument("--min-seeds", type=int, default=MIN_INDEPENDENT_SEEDS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        run_dirs = discover_run_dirs(args.runs_root, study=args.study, method=args.method)
        reports = []
        for rd in run_dirs:
            hashes = collect_seed_hashes(rd)
            rep = guard(method_kind=args.kind, seed_hashes=hashes, min_seeds=args.min_seeds)
            rep["run_dir"] = str(rd)
            reports.append(rep)
            print(
                f"{rep['status']} replicate {rd}: {rep['n_seeds']} seeds, "
                f"{rep['n_unique_prediction_hashes']} unique hashes — {rep['verdict']}"
            )
        if args.json:
            print(json.dumps(reports, ensure_ascii=False, indent=2))
        print(f"OK replicate: {len(reports)} run(s) satisfy the {args.kind} replication contract.")
        return EXIT_OK
    except ReplicationError as exc:
        print(f"FAIL replicate: {exc}", file=sys.stderr)
        return EXIT_GUARD_FAILED


if __name__ == "__main__":
    sys.exit(main())
