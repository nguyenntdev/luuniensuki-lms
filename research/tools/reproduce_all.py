#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive CLI reproduction runner for 10 Educational Research Studies (LN-01 to LN-10).

Supports:
  1. Automated clean environment check.
  2. Running the full 50-condition benchmark matrix (--benchmark).
  3. Running the 10 independent holdout evaluations (--holdout).
  4. Computing all statistical significance metrics (--statistics).
  5. Generating publication tables and validating release readiness (--verify).

Usage:
  python3 research/tools/reproduce_all.py --all
  python3 research/tools/reproduce_all.py --benchmark --output /tmp/reproduction_output
  python3 research/tools/reproduce_all.py --holdout
  python3 research/tools/reproduce_all.py --statistics
  python3 research/tools/reproduce_all.py --verify
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import math
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from check_sources import verify_spec
from recompute_metrics import PRIMARY, CAT, compute
from run_all import run_benchmark_suite
from verify_release import check as verify_release_check

MATRIX = json.loads((ROOT / "configs" / "experiments.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Math & Statistical Helpers (Self-contained, standard library only)
# --------------------------------------------------------------------------- #
def chi2_sf_1df(chi2: float) -> float:
    """Survival function (p-value) for Chi-Square distribution with 1 degree of freedom."""
    if chi2 <= 0.0:
        return 1.0
    # For df=1, chi2 = Z^2, so P(chi2 >= x) = 2 * (1 - Phi(sqrt(x))) = erfc(sqrt(x/2))
    return math.erfc(math.sqrt(chi2 / 2.0))


def mcnemar_test(b: int, c: int) -> Tuple[float, float]:
    """Compute McNemar's test with Edwards continuity correction.

    b: cases where Condition 1 is wrong and Condition 2 is right
    c: cases where Condition 1 is right and Condition 2 is wrong
    """
    total = b + c
    if total == 0:
        return 0.0, 1.0
    chi2 = (abs(b - c) - 1.0) ** 2 / total if abs(b - c) > 1.0 else 0.0
    p_value = chi2_sf_1df(chi2)
    return chi2, p_value


def paired_proportion_ci95(p1: float, p2: float, b: int, c: int, n: int) -> Tuple[float, float]:
    """95% Confidence Interval for difference in paired proportions (p1 - p2)."""
    diff = p1 - p2
    if n == 0:
        return 0.0, 0.0
    # Variance of difference in paired proportions: Var(p1 - p2) = (b + c - (b - c)^2 / n) / n^2
    var = (b + c - ((b - c) ** 2) / n) / (n * n)
    se = math.sqrt(max(0.0, var))
    margin = 1.95996 * se
    return diff - margin, diff + margin


# --------------------------------------------------------------------------- #
# Phase 1: Automated Clean Environment Check
# --------------------------------------------------------------------------- #
def check_clean_environment(repo: pathlib.Path, allow_uncommitted: bool = False) -> Dict[str, Any]:
    """Verify repository clean state, Python runtime, baseline commit ancestry, and fixtures."""
    repo = repo.resolve()
    problems: List[str] = []

    # 1. Python version check
    py_ver = sys.version_info
    if py_ver < (3, 10):
        problems.append(f"Python 3.10+ required, current is {platform.python_version()}")

    # 2. Git checks
    if not (repo / ".git").is_dir():
        problems.append(f"Not a git repository: {repo}")
        head_sha = "unknown"
        dirty = True
    else:
        try:
            head_sha = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except Exception as e:
            problems.append(f"Failed to resolve git HEAD: {e}")
            head_sha = "unknown"

        try:
            porcelain = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            dirty = bool(porcelain)
            if dirty and not allow_uncommitted:
                problems.append("Working tree has uncommitted modifications. Commit changes or pass --allow-uncommitted.")
        except Exception as e:
            problems.append(f"Failed to check git status: {e}")
            dirty = True

        # Ancestor check
        base_commit = MATRIX["old_spec_ancestral_commit"]
        try:
            subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", base_commit, head_sha],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            problems.append(f"Current commit {head_sha} is not an ancestor/descendant of baseline commit {base_commit}")

    # 3. Fixtures integrity check
    fixture_audit = verify_spec(ROOT / "fixtures")
    if fixture_audit["issues"]:
        problems.extend([f"Fixture issue: {iss}" for iss in fixture_audit["issues"][:5]])

    # 4. Adapter import check
    imported_adapters = 0
    for s_id, s_info in MATRIX["studies"].items():
        adapter_spec = s_info["adapter"]
        mod_name, _, fn_name = adapter_spec.partition(":")
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            func = getattr(mod, fn_name)
            if not callable(func):
                problems.append(f"Adapter {adapter_spec} is not callable")
            else:
                imported_adapters += 1
        except Exception as e:
            problems.append(f"Cannot import adapter {adapter_spec}: {e}")

    # 5. Holdout files check
    holdout_dir = ROOT / "fixtures" / "holdout"
    holdout_files_present = 0
    for i in range(1, 11):
        hf = holdout_dir / f"LN-{i:02d}_holdout.jsonl"
        if hf.is_file():
            holdout_files_present += 1
        else:
            problems.append(f"Missing holdout fixture {hf.name}")

    status = "PASS" if not problems else "FAIL"
    return {
        "status": status,
        "python_version": platform.python_version(),
        "repo_path": str(repo),
        "head_sha": head_sha,
        "dirty": dirty,
        "ancestral_baseline": MATRIX["old_spec_ancestral_commit"],
        "fixtures_validated": len(fixture_audit["stats"].get("fixtures", {})),
        "holdout_files_present": holdout_files_present,
        "adapters_imported": imported_adapters,
        "problems": problems,
    }


# --------------------------------------------------------------------------- #
# Phase 2: 50-Condition Benchmark Matrix
# --------------------------------------------------------------------------- #
def run_benchmark_matrix(
    repo: pathlib.Path,
    benchmark_dir: pathlib.Path,
    workers: int = 10,
    studies: str = "all",
    allow_uncommitted: bool = False,
    max_cases: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute full 50-condition benchmark matrix via self-contained run_all module."""
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    report = run_benchmark_suite(
        repo=repo,
        output=benchmark_dir,
        spec=ROOT / "fixtures",
        workers=workers,
        studies_filter=studies,
        allow_uncommitted=allow_uncommitted,
        max_cases=max_cases,
    )
    return report


# --------------------------------------------------------------------------- #
# Phase 3: 10 Independent Holdout Evaluations
# --------------------------------------------------------------------------- #
def evaluate_one_holdout(
    study: str,
    holdout_file: pathlib.Path,
    adapter_fn: Any,
) -> Dict[str, Any]:
    """Evaluate holdout dataset against intervention (I1) and baseline (B0)."""
    cases = [json.loads(line) for line in holdout_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise ValueError(f"Empty holdout file: {holdout_file}")

    total = len(cases)
    i1_matches = 0
    b0_matches = 0
    fault_breakdown: Dict[str, Dict[str, Any]] = collections.defaultdict(lambda: {"n": 0, "i1_pass": 0, "b0_pass": 0})
    rows_evaluated = []

    for c in cases:
        fid = c.get("fault_id", "unknown")
        inp = c["input"]
        exp_dec = c.get("oracle", {}).get("expected_decision")

        # Run intervention
        res_i1 = adapter_fn(inp, mode="intervention", config={})
        ok_i1 = (res_i1.get("decision") == exp_dec)
        i1_matches += int(ok_i1)

        # Run baseline
        res_b0 = adapter_fn(inp, mode="baseline", config={})
        ok_b0 = (res_b0.get("decision") == exp_dec)
        b0_matches += int(ok_b0)

        fault_breakdown[fid]["n"] += 1
        fault_breakdown[fid]["i1_pass"] += int(ok_i1)
        fault_breakdown[fid]["b0_pass"] += int(ok_b0)

        rows_evaluated.append({
            "case_id": c.get("case_id"),
            "fault_id": fid,
            "expected_decision": exp_dec,
            "i1_decision": res_i1.get("decision"),
            "b0_decision": res_b0.get("decision"),
            "i1_pass": ok_i1,
            "b0_pass": ok_b0,
        })

    return {
        "study": study,
        "cases_evaluated": total,
        "intervention_accuracy": round(i1_matches / total, 4),
        "baseline_accuracy": round(b0_matches / total, 4),
        "intervention_matches": i1_matches,
        "baseline_matches": b0_matches,
        "accuracy_gain": round((i1_matches - b0_matches) / total, 4),
        "fault_breakdown": dict(fault_breakdown),
    }


def run_holdout_evaluations(
    holdout_out_dir: pathlib.Path,
    studies_filter: str = "all",
) -> Dict[str, Any]:
    """Execute evaluation on all 10 independent holdout datasets."""
    holdout_out_dir.mkdir(parents=True, exist_ok=True)
    holdout_dir = ROOT / "fixtures" / "holdout"

    studies = sorted(MATRIX["studies"]) if studies_filter == "all" else [x.strip() for x in studies_filter.split(",")]
    results: List[Dict[str, Any]] = []

    for study in studies:
        hf = holdout_dir / f"{study}_holdout.jsonl"
        if not hf.is_file():
            results.append({"study": study, "status": "FAIL", "error": f"Missing {hf.name}"})
            continue

        adapter_spec = MATRIX["studies"][study]["adapter"]
        mod_name, _, fn_name = adapter_spec.partition(":")
        mod = __import__(mod_name, fromlist=[fn_name])
        adapter_fn = getattr(mod, fn_name)

        try:
            eval_res = evaluate_one_holdout(study, hf, adapter_fn)
            eval_res["status"] = "PASS"
            results.append(eval_res)
        except Exception as e:
            results.append({"study": study, "status": "FAIL", "error": str(e)})

    # Summary
    csv_rows = []
    for r in results:
        if r.get("status") == "PASS":
            csv_rows.append({
                "study": r["study"],
                "cases": r["cases_evaluated"],
                "intervention_accuracy": r["intervention_accuracy"],
                "baseline_accuracy": r["baseline_accuracy"],
                "accuracy_gain": r["accuracy_gain"],
            })

    if csv_rows:
        with (holdout_out_dir / "holdout_summary.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["study", "cases", "intervention_accuracy", "baseline_accuracy", "accuracy_gain"])
            w.writeheader()
            w.writerows(csv_rows)

    report = {
        "status": "PASS" if all(x.get("status") == "PASS" for x in results) else "FAIL",
        "cohort": "INDEPENDENT_HOLDOUT",
        "studies_evaluated": len(results),
        "total_cases": sum(x.get("cases_evaluated", 0) for x in results),
        "results": results,
    }
    (holdout_out_dir / "holdout_evaluation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


# --------------------------------------------------------------------------- #
# Phase 4: Statistical Significance Metrics
# --------------------------------------------------------------------------- #
def compute_statistical_significance(
    benchmark_dir: pathlib.Path,
    stats_out_dir: pathlib.Path,
    studies_filter: str = "all",
) -> Dict[str, Any]:
    """Compute paired statistical significance metrics (McNemar, Risk Reduction, 95% CI) between Baseline (B0) and Intervention (I1)."""
    stats_out_dir.mkdir(parents=True, exist_ok=True)
    studies = sorted(MATRIX["studies"]) if studies_filter == "all" else [x.strip() for x in studies_filter.split(",")]
    study_stats: List[Dict[str, Any]] = []

    for study in studies:
        b0_trace_path = benchmark_dir / study / "B0" / "trace.jsonl"
        i1_trace_path = benchmark_dir / study / "I1" / "trace.jsonl"
        if not b0_trace_path.is_file() or not i1_trace_path.is_file():
            continue

        b0_rows = [json.loads(x) for x in b0_trace_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        i1_rows = [json.loads(x) for x in i1_trace_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        b0_by_id = {r["case_id"]: r for r in b0_rows}
        i1_by_id = {r["case_id"]: r for r in i1_rows}

        metric_name, faults, field, flag, kind = PRIMARY[study]
        eligible_cases = [
            cid for cid, r in b0_by_id.items()
            if faults is None or r.get("fault_id") in faults
        ]

        n = len(eligible_cases)
        if n == 0:
            continue

        b0_failures = 0
        i1_failures = 0
        b_count = 0  # B0 fails, I1 passes
        c_count = 0  # B0 passes, I1 fails
        a_count = 0  # Both pass
        d_count = 0  # Both fail

        for cid in eligible_cases:
            r_b0 = b0_by_id[cid]
            r_i1 = i1_by_id[cid]
            v_b0 = r_b0.get("observables", {}).get(field)
            v_i1 = r_i1.get("observables", {}).get(field)

            if kind == "mapping":
                b0_fail = (v_b0 != CAT.get(r_b0.get("fault_id", ""), ""))
                i1_fail = (v_i1 != CAT.get(r_i1.get("fault_id", ""), ""))
            elif kind == "good":
                b0_fail = (v_b0 != flag)
                i1_fail = (v_i1 != flag)
            elif kind == "sum":
                b0_fail = (v_b0 > 0)
                i1_fail = (v_i1 > 0)
            else:
                b0_fail = (v_b0 == flag)
                i1_fail = (v_i1 == flag)

            b0_failures += int(b0_fail)
            i1_failures += int(i1_fail)

            if b0_fail and not i1_fail:
                b_count += 1
            elif not b0_fail and i1_fail:
                c_count += 1
            elif not b0_fail and not i1_fail:
                a_count += 1
            else:
                d_count += 1

        b0_rate = b0_failures / n
        i1_rate = i1_failures / n
        arr = b0_rate - i1_rate
        rrr = (arr / b0_rate) if b0_rate > 0 else 0.0
        chi2, p_val = mcnemar_test(b_count, c_count)
        ci_low, ci_high = paired_proportion_ci95(b0_rate, i1_rate, b_count, c_count, n)

        entry = {
            "study": study,
            "metric_key": metric_name,
            "eligible_n": n,
            "baseline_failures": b0_failures,
            "baseline_rate": round(b0_rate, 4),
            "intervention_failures": i1_failures,
            "intervention_rate": round(i1_rate, 4),
            "absolute_risk_reduction": round(arr, 4),
            "relative_risk_reduction": round(rrr, 4),
            "ci95_arr": [round(ci_low, 4), round(ci_high, 4)],
            "contingency_table": {
                "both_pass": a_count,
                "baseline_fail_intervention_pass": b_count,
                "baseline_pass_intervention_fail": c_count,
                "both_fail": d_count,
            },
            "mcnemar_chi2": round(chi2, 4),
            "mcnemar_p_value": p_val,
            "statistically_significant_p001": bool(p_val < 0.001),
        }
        study_stats.append(entry)

    # Output CSV summary
    csv_fields = [
        "study", "metric_key", "eligible_n", "baseline_rate", "intervention_rate",
        "absolute_risk_reduction", "relative_risk_reduction", "mcnemar_chi2", "mcnemar_p_value", "statistically_significant_p001"
    ]
    with (stats_out_dir / "statistical_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        for s in study_stats:
            w.writerow({k: s[k] for k in csv_fields})

    report = {
        "scientific_notice": "SYNTHETIC_SOFTWARE_POLICY_COMPARISON: Evaluates automated policy invariants, not human learner retention.",
        "studies_analyzed": len(study_stats),
        "results": study_stats,
    }
    (stats_out_dir / "statistical_significance_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


# --------------------------------------------------------------------------- #
# Phase 5: Publication Tables & Technical Release Gate
# --------------------------------------------------------------------------- #
def verify_and_generate_tables(benchmark_dir: pathlib.Path, tables_dir: pathlib.Path) -> Dict[str, Any]:
    """Validate release integrity and generate manuscript LaTeX / CSV table fragments."""
    tables_dir.mkdir(parents=True, exist_ok=True)
    report, registry = verify_release_check(benchmark_dir)

    def esc(x: Any) -> str:
        return str(x).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")

    for study, entry in MATRIX["studies"].items():
        study_runs = benchmark_dir / study
        if not study_runs.is_dir():
            continue
        rows = []
        for cond in entry["runs"]:
            cid = cond["id"]
            m_path = study_runs / cid / "study_metric.json"
            mf_path = study_runs / cid / "manifest.json"
            if not m_path.is_file() or not mf_path.is_file():
                continue
            metric = json.loads(m_path.read_text(encoding="utf-8"))
            manifest = json.loads(mf_path.read_text(encoding="utf-8"))
            rows.append({
                "condition": cid,
                "variant": cond["label"],
                "numerator": metric["numerator"],
                "denominator": metric["denominator"],
                "value": metric["value"],
                "metric": metric["metric_key"],
                "unit": metric["unit"],
                "run_id": manifest["run_id"],
                "source_sha": manifest["source_commit_at_runtime"],
                "trace_sha256": manifest["trace_sha256"],
            })

        if not rows:
            continue

        with (tables_dir / f"{study}_results.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        name = rows[0]["metric"]
        unit = rows[0]["unit"]
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\small",
            r"\caption{Comparison on frozen synthetic software-policy scenarios (not student outcomes).}",
            r"\label{tab:" + study.lower() + "-policy-benchmark}",
            r"\begin{tabular}{lrrr}",
            r"\toprule",
            r"Condition & Numerator & Eligible $N$ & Metric \\",
            r"\midrule",
        ]
        for row in rows:
            if unit == "violations_per_synthetic_route":
                show = f"{row['value']:.4f} / route"
            else:
                show = f"{row['value']*100:.2f}\\%"
            lines.append(f"{esc(row['condition'] + ' ' + row['variant'])} & {row['numerator']} & {row['denominator']} & {show} \\\\")

        lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\par\smallskip",
            r"\begin{minipage}{0.98\linewidth}\footnotesize",
            "Primary measure: " + esc(name) + ". All conditions are executed on the same frozen synthetic policy inputs; the eligible denominator depends on the declared fault strata. These are software-policy decisions, not measured changes in learning. Read exact run IDs and SHA-256 fingerprints in the accompanying evidence registry. Source commit: " + r"\texttt{" + rows[0]["source_sha"][:12] + "}.",
            r"\end{minipage}",
            r"\end{table}",
        ])
        (tables_dir / f"{study}_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "release_validation": report,
        "tables_generated_dir": str(tables_dir),
    }


# --------------------------------------------------------------------------- #
# Main CLI Orchestration
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive CLI reproduction for 10 Educational Research Studies"
    )
    parser.add_argument("--all", action="store_true", help="Execute all phases (clean check, benchmark, holdout, statistics, verify)")
    parser.add_argument("--benchmark", action="store_true", help="Run 50-condition benchmark matrix")
    parser.add_argument("--holdout", action="store_true", help="Run 10 independent holdout evaluations")
    parser.add_argument("--statistics", action="store_true", help="Compute statistical significance metrics")
    parser.add_argument("--verify", action="store_true", help="Validate release readiness and generate publication tables")
    parser.add_argument("--output", type=pathlib.Path, default=None, help="Root directory for reproduction outputs")
    parser.add_argument("--repo", type=pathlib.Path, default=None, help="Path to repo root (defaults to parent repo)")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads (default: 4, 1..10)")
    parser.add_argument("--studies", default="all", help="Studies filter: 'all' or comma-separated list")
    parser.add_argument("--allow-uncommitted", action="store_true", help="Allow uncommitted git working tree (development/test mode)")
    parser.add_argument("--max-cases", type=int, default=None, help="Limit cases per run for fast smoke execution")
    parser.add_argument("--json", action="store_true", help="Print summary report as JSON")
    args = parser.parse_args()

    # Determine actions: if none specified, default to --all
    run_all_phases = args.all or not (args.benchmark or args.holdout or args.statistics or args.verify)
    do_benchmark = run_all_phases or args.benchmark
    do_holdout = run_all_phases or args.holdout
    do_statistics = run_all_phases or args.statistics
    do_verify = run_all_phases or args.verify

    repo = (args.repo or REPO_ROOT).resolve()

    # Default output dir in /tmp if not specified
    if args.output:
        out_root = args.output.resolve()
    else:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_root = pathlib.Path(f"/tmp/reproduce_luunien_{timestamp}").resolve()

    out_root.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "reproduction_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "output_directory": str(out_root),
        "phases": {},
    }

    # Step 1: Clean environment check
    env_check = check_clean_environment(repo, allow_uncommitted=args.allow_uncommitted)
    summary["phases"]["environment_check"] = env_check
    if env_check["status"] != "PASS" and not args.allow_uncommitted:
        print(json.dumps({"status": "BLOCKED", "reason": "Environment check failed", "details": env_check}, indent=2))
        return 1

    benchmark_dir = out_root / "benchmark"
    holdout_dir = out_root / "holdout"
    stats_dir = out_root / "statistics"
    tables_dir = out_root / "manuscript_tables"

    # Step 2: Benchmark matrix
    if do_benchmark:
        bm_res = run_benchmark_matrix(
            repo=repo,
            benchmark_dir=benchmark_dir,
            workers=args.workers,
            studies=args.studies,
            allow_uncommitted=args.allow_uncommitted,
            max_cases=args.max_cases,
        )
        summary["phases"]["benchmark"] = bm_res
        if bm_res.get("status") != "PASS":
            print(json.dumps({"status": "FAILED", "phase": "benchmark", "details": bm_res}, indent=2))
            return 1

    # Step 3: Holdout evaluations
    if do_holdout:
        ho_res = run_holdout_evaluations(
            holdout_out_dir=holdout_dir,
            studies_filter=args.studies,
        )
        summary["phases"]["holdout"] = ho_res

    # Step 4: Statistical significance
    if do_statistics:
        target_bm = benchmark_dir if benchmark_dir.exists() else (REPO_ROOT / "research_artifacts")
        stats_res = compute_statistical_significance(
            benchmark_dir=target_bm,
            stats_out_dir=stats_dir,
            studies_filter=args.studies,
        )
        summary["phases"]["statistics"] = stats_res

    # Step 5: Verify release & generate tables
    if do_verify:
        target_bm = benchmark_dir if benchmark_dir.exists() else (REPO_ROOT / "research_artifacts")
        verify_res = verify_and_generate_tables(
            benchmark_dir=target_bm,
            tables_dir=tables_dir,
        )
        summary["phases"]["verification"] = verify_res

    # Summary json
    summary_file = out_root / "reproduction_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    all_pass = all(
        p.get("status") in ("PASS", "SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE")
        for p in summary["phases"].values()
        if isinstance(p, dict) and "status" in p
    )
    summary["overall_status"] = "PASS" if all_pass else "FAIL"

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("\n=======================================================")
        print(f" Reproduction Complete: {summary['overall_status']}")
        print(f" Artifacts Root: {out_root}")
        print(" Phases Executed:")
        for k, v in summary["phases"].items():
            st = v.get("status", "COMPLETE") if isinstance(v, dict) else "COMPLETE"
            print(f"  - {k}: {st}")
        print("=======================================================\n")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
