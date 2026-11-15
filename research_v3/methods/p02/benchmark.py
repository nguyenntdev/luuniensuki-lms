"""P02 benchmark CLI: runs the full preregistered matrix and writes artifacts.

Usage (from repo root):
    python -m research_v3.methods.p02.benchmark \
        --instances-per-cell 6 --seed 20261115 \
        --out research_artifacts_v3/runs/p02

Produces under ``<out>/``:
- ``instances.jsonl``     : every generated instance + certified oracle verdict
- ``predictions.jsonl``   : one row per (solver, instance) with status/cost
- ``study_metric.json``   : aggregated cells, per-regime, per-family, stats
- ``manifest.json``       : sha256 of every artifact + config + environment

Honesty rules enforced here:
- every solver row carries its status; aggregates never relabel timeouts;
- paired statistics vs C0/C1 use shared.solvable instances only and are
  reported alongside instance counts;
- negative results (proposed losing optimality on tight budgets) are
  reported verbatim, never smoothed.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

from research_v2.contracts.canonical_hash import sha256_bytes, sha256_input

from .eval_stats import paired_report, proportion_ci
from .generator import BUDGET_REGIMES, TOPOLOGY_FAMILIES, generate_matrix
from .metrics import (
    evaluate_cell,
    paired_cost_differences,
    per_family_breakdown,
    per_regime_breakdown,
)
from .problems import PlanningProblem, parse_problem
from .solvers import EXACT_SOLVERS, SOLVER_DESCRIPTIONS, run_solver, validate_route

ALL_SOLVERS = ("c0_greedy", "c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed", "a3_alternative_blind")
CONFIRMATORY_FAMILY = ("p02_proposed_vs_c1_branch_and_bound", "p02_proposed_vs_c0_greedy")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n"
    path.write_text(payload, encoding="utf-8")
    return sha256_bytes(payload.encode("utf-8"))


def run_matrix(
    *,
    instances_per_cell: int,
    seed: int,
    solvers: tuple[str, ...] = ALL_SOLVERS,
) -> dict[str, Any]:
    """Generate, solve and score the full matrix; returns the study payload."""
    t0 = time.perf_counter()
    cases = generate_matrix(seed=seed, instances_per_cell=instances_per_cell)
    problems: list[PlanningProblem] = [c.problem for c in cases]

    per_solver_rows: dict[str, list[dict[str, Any]]] = {}
    per_solver_results = {}
    cells: dict[str, Any] = {}
    for solver_id in solvers:
        results = []
        rows: list[dict[str, Any]] = []
        for problem in problems:
            res = run_solver(solver_id, problem)
            violations = validate_route(problem, res.route) if res.route else []
            results.append(res)
            rows.append(
                {
                    "solver_id": solver_id,
                    "problem_id": problem.problem_id,
                    "family_id": problem.family_id,
                    "regime": None,  # filled below from the case map
                    "decision": res.decision,
                    "status": res.status,
                    "route": list(res.route),
                    "total_cost": res.total_cost,
                    "reason_codes": list(res.reason_codes),
                    "route_violations": violations,
                    "wall_ms": round(res.wall_ms, 4),
                    "nodes_expanded": res.nodes_expanded,
                }
            )
        per_solver_results[solver_id] = results
        per_solver_rows[solver_id] = rows
        cells[solver_id] = evaluate_cell(solver_id, cases, results).to_dict()

    regime_of = {c.problem.problem_id: c.regime for c in cases}
    for rows in per_solver_rows.values():
        for row in rows:
            row["regime"] = regime_of[row["problem_id"]]

    # Honest route validation: any returned route must satisfy every constraint.
    invalid_routes = {
        s: [r["problem_id"] for r in rows if r["route_violations"]]
        for s, rows in per_solver_rows.items()
    }

    per_regime = {
        s: per_regime_breakdown(s, cases, per_solver_results[s]) for s in solvers
    }
    per_family = {
        s: per_family_breakdown(s, cases, per_solver_results[s]) for s in solvers
    }

    # Paired statistics: proposed vs C1 (confirmatory) and vs C0.
    stats: dict[str, Any] = {}
    for contrast in ("p02_proposed_vs_c1_branch_and_bound", "p02_proposed_vs_c0_greedy"):
        _, other = contrast.split("_vs_")
        diffs, groups, _flags = paired_cost_differences(
            cases, per_solver_results["p02_proposed"], per_solver_results[other]
        )
        stats[contrast] = paired_report(diffs, groups, label_a="p02_proposed", label_b=other)

    # Multiplicity: Holm within the declared confirmatory family.
    from research_v3.eval.statistics import family_control

    fam_p = []
    for contrast in CONFIRMATORY_FAMILY:
        p = stats[contrast].get("wilcoxon") or {}
        fam_p.append(p.get("p_value"))
    stats["holm_adjusted_p_confirmatory"] = dict(
        zip(CONFIRMATORY_FAMILY, family_control([p if p is not None else 1.0 for p in fam_p]))
    )

    return {
        "paper_id": "P02",
        "study": "Constraint-Aware Learning Path Planning with Alternative Activities",
        "seed": seed,
        "instances_per_cell": instances_per_cell,
        "n_instances": len(cases),
        "regimes": list(BUDGET_REGIMES),
        "families": list(TOPOLOGY_FAMILIES),
        "solvers": list(solvers),
        "solver_descriptions": {s: SOLVER_DESCRIPTIONS[s] for s in solvers},
        "c2_label": "independent exact search (reimplementation); not a published library",
        "cells": cells,
        "per_regime": per_regime,
        "per_family": per_family,
        "paired_statistics": stats,
        "confirmatory_family": list(CONFIRMATORY_FAMILY),
        "invalid_routes": invalid_routes,
        "exact_solver_false_infeasibility_must_be_zero": {
            s: cells[s]["false_infeasibility"] for s in solvers if s in EXACT_SOLVERS
        },
        "wall_seconds": round(time.perf_counter() - t0, 3),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="P02 solver benchmark")
    ap.add_argument("--instances-per-cell", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261115)
    ap.add_argument("--out", type=Path, default=Path("research_artifacts_v3/runs/p02"))
    ap.add_argument(
        "--solvers", nargs="*", default=list(ALL_SOLVERS),
        help="subset of solver ids (default: all five)",
    )
    args = ap.parse_args(argv)

    solvers = tuple(args.solvers)
    for s in solvers:
        if s not in ALL_SOLVERS:
            ap.error(f"unknown solver {s!r}; known: {ALL_SOLVERS}")

    study = run_matrix(instances_per_cell=args.instances_per_cell, seed=args.seed, solvers=solvers)

    # Re-materialize the instances for the artifact trail (deterministic).
    cases = generate_matrix(seed=args.seed, instances_per_cell=args.instances_per_cell)
    instance_rows = [
        {
            "problem_id": c.problem.problem_id,
            "family_id": c.problem.family_id,
            "regime": c.regime,
            "alt_density": c.alt_density,
            "n_activities": c.n_activities,
            "n_targets": c.n_targets,
            "alt_outcomes": c.alt_outcomes,
            "problem": c.problem.to_dict(),
            "oracle_decision": c.oracle.decision,
            "oracle_optimum_cost": c.oracle.optimum_cost,
            "oracle_optimal_route": list(c.oracle.optimal_route) if c.oracle.optimal_route else None,
        }
        for c in cases
    ]
    prediction_rows = []
    for solver_id in solvers:
        study_rows = study  # noqa: F841 (kept for clarity)
        preds = _collect_predictions(cases, solver_id, args)
        prediction_rows.extend(preds)

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "instances.jsonl": _write_jsonl(out / "instances.jsonl", instance_rows),
        "predictions.jsonl": _write_jsonl(out / "predictions.jsonl", prediction_rows),
    }
    study["artifacts_sha256"] = artifacts
    study["environment"] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ortools_available": _ortools_available(),
        "c2_note": "ortools/pulp unavailable in this environment; C2 is an independent exact reimplementation (Dijkstra-with-state), labelled as such.",
    }
    (out / "study_metric.json").write_text(
        json.dumps(study, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    study_sha = sha256_bytes((out / "study_metric.json").read_bytes())
    manifest = {
        "paper_id": "P02",
        "run": "benchmark_matrix",
        "seed": args.seed,
        "instances_per_cell": args.instances_per_cell,
        "artifacts": {**artifacts, "study_metric.json": study_sha},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    cells = study["cells"]
    print(f"instances: {study['n_instances']}  seed={args.seed}")
    for s in solvers:
        c = cells[s]
        print(
            f"{s:22s} exact_match={c['exact_match_rate']:.3f} "
            f"feas={c['feasibility_rate']:.3f} false_infeas={c['false_infeasibility']} "
            f"gap={c['mean_relative_gap'] if c['mean_relative_gap'] is not None else 'n/a'} "
            f"p95ms={c['wall_ms_p95']}"
        )
    for contrast, rep in study["paired_statistics"].items():
        if isinstance(rep, dict) and "mean_diff" in rep:
            print(f"{contrast}: mean_cost_diff={rep['mean_diff']} n={rep['n']}")
    print(f"artifacts -> {out}")
    return 0


def _collect_predictions(cases, solver_id: str, args) -> list[dict[str, Any]]:
    """One row per (solver, instance) — re-run is deterministic and cheap."""
    from .solvers import run_solver as _rs

    rows = []
    for c in cases:
        res = _rs(solver_id, c.problem)
        rows.append(
            {
                "solver_id": solver_id,
                "problem_id": c.problem.problem_id,
                "family_id": c.problem.family_id,
                "regime": c.regime,
                "decision": res.decision,
                "status": res.status,
                "route": list(res.route),
                "total_cost": res.total_cost,
                "dwell_cost": res.dwell_cost,
                "travel_cost": res.travel_cost,
                "reason_codes": list(res.reason_codes),
                "wall_ms": round(res.wall_ms, 4),
                "oracle_decision": c.oracle.decision,
                "oracle_optimum_cost": c.oracle.optimum_cost,
            }
        )
    return rows


def _ortools_available() -> bool:
    try:
        import ortools  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
