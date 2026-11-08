#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluation runner for LN-06 holdout benchmark across B0, B1, I1, A1, A2, A3.

Conditions:
- B0: Naive spatial TSP / reverse spatial order (mode="b0")
- B1: Greedy topological search without time-budget bounds (mode="b1")
- I1: Cognitively constrained DAG trail planner with verified stops (mode="intervention")
- A1: Ablation 1 - disable prerequisite DAG constraints (mode="ablation", config={"enforce_prerequisites": False})
- A2: Ablation 2 - disable time budget constraints (mode="ablation", config={"enforce_budget": False})
- A3: Ablation 3 - disable source verification gate (mode="ablation", config={"enforce_sources": False})
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.integrations.ln06 import run_policy
HOLDOUT_PATH = ROOT / "research" / "fixtures" / "holdout" / "LN-06_holdout.jsonl"
OUT_DIR = ROOT / "research_artifacts" / "holdout" / "LN-06"


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score interval for binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.959963984540054  # 95%
    p = successes / total
    denom = 1 + (z ** 2) / total
    center = (p + (z ** 2) / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) + (z ** 2) / (4 * total)) / total)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def normal_mean_ci(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% confidence interval for mean of continuous metric."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    mean = sum(values) / n
    if n == 1:
        return (mean, mean)
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_err = math.sqrt(variance / n)
    z = 1.959963984540054
    return (max(0.0, mean - z * std_err), mean + z * std_err)


def paired_t_test(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute paired Student's t-test statistic and approximate two-tailed p-value."""
    n = len(x)
    if n != len(y) or n == 0:
        return 0.0, 1.0
    d = [x[i] - y[i] for i in range(n)]
    mean_d = sum(d) / n
    var_d = sum((diff - mean_d) ** 2 for diff in d) / (n - 1) if n > 1 else 0.0
    if var_d == 0.0:
        return 0.0, 1.0 if mean_d == 0.0 else 0.0
    se_d = math.sqrt(var_d / n)
    t_stat = mean_d / se_d
    # Approximation of p-value via Gaussian tail for large df (~120)
    p_val = math.erfc(abs(t_stat) / math.sqrt(2.0))
    return t_stat, p_val


def mcnemar_test(b: int, c: int) -> Tuple[float, float]:
    """Compute McNemar test statistic with continuity correction and p-value approximation.
    b: condition 1 correct, condition 2 incorrect
    c: condition 1 incorrect, condition 2 correct
    """
    total = b + c
    if total == 0:
        return 0.0, 1.0
    stat = ((abs(b - c) - 1.0) ** 2) / total
    p_val = math.erfc(math.sqrt(stat) / math.sqrt(2.0))
    return stat, p_val


def evaluate_condition(
    cases: List[Dict[str, Any]],
    mode: str,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    cfg = config or {}
    traces = []

    per_case_correct = []
    prereq_violations = []
    outcome_coverages = []
    route_costs = []
    fault_correct = {
        "nominal": 0,
        "unreachable_checkpoint": 0,
        "source_gap_in_monument": 0,
        "prerequisite_cycle": 0,
        "over_time_budget": 0,
    }

    for c in cases:
        c_input = c["input"]
        fault_id = c["fault_id"]
        oracle = c["oracle"]
        exp_decision = oracle["expected_decision"]

        t0 = time.perf_counter()
        res = run_policy(c_input, mode=mode, config=cfg)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        decision = res["decision"]
        oracle_match = (decision == exp_decision)

        is_correct = oracle_match
        per_case_correct.append(is_correct)
        if is_correct:
            fault_correct[fault_id] += 1

        prereq_v = res["prerequisite_violation_count"]
        prereq_violations.append(prereq_v)
        outcome_coverages.append(res["outcome_coverage"])
        route_costs.append(res["route_cost"])

        traces.append({
            "case_id": c["case_id"],
            "fault_id": fault_id,
            "decision": decision,
            "expected_decision": exp_decision,
            "oracle_match": oracle_match,
            "observables": {
                "prerequisite_violation_count": prereq_v,
                "outcome_coverage": res["outcome_coverage"],
                "route_cost": res["route_cost"],
                "unreachable_checkpoint_rate": res["unreachable_checkpoint_rate"],
                "stop_sequence": res["stop_sequence"],
            },
            "elapsed_ms": round(elapsed_ms, 3),
        })

    n_total = len(cases)
    n_correct = sum(per_case_correct)
    acc = n_correct / n_total
    acc_ci = wilson_score_interval(n_correct, n_total)

    mean_violations = sum(prereq_violations) / n_total
    viol_ci = normal_mean_ci([float(x) for x in prereq_violations])

    mean_coverage = sum(outcome_coverages) / n_total
    cov_ci = normal_mean_ci(outcome_coverages)

    mean_cost = sum(route_costs) / n_total
    cost_ci = normal_mean_ci([float(x) for x in route_costs])

    return {
        "mode": mode,
        "config": cfg,
        "n_total": n_total,
        "n_correct": n_correct,
        "accuracy": round(acc, 4),
        "accuracy_ci_95": [round(acc_ci[0], 4), round(acc_ci[1], 4)],
        "mean_prerequisite_violations": round(mean_violations, 4),
        "total_prerequisite_violations": sum(prereq_violations),
        "violations_ci_95": [round(viol_ci[0], 4), round(viol_ci[1], 4)],
        "mean_outcome_coverage": round(mean_coverage, 4),
        "coverage_ci_95": [round(cov_ci[0], 4), round(cov_ci[1], 4)],
        "mean_route_cost": round(mean_cost, 4),
        "cost_ci_95": [round(cost_ci[0], 4), round(cost_ci[1], 4)],
        "fault_breakdown": {
            f: {"n": 24, "correct": fault_correct[f], "accuracy": round(fault_correct[f] / 24, 4)}
            for f in fault_correct
        },
        "per_case_correct": per_case_correct,
        "prereq_violations": prereq_violations,
        "outcome_coverages": outcome_coverages,
        "route_costs": route_costs,
        "traces": traces,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with HOLDOUT_PATH.open("r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(cases)} holdout cases from {HOLDOUT_PATH}")

    conditions = {
        "B0": {"mode": "b0", "config": {}, "label": "Naive Spatial TSP"},
        "B1": {"mode": "b1", "config": {}, "label": "Greedy Topological (No Budget)"},
        "I1": {"mode": "intervention", "config": {}, "label": "Cognitively Constrained DAG Trail Planner"},
        "A1": {"mode": "ablation", "config": {"enforce_prerequisites": False}, "label": "Ablation: Disable Prerequisites"},
        "A2": {"mode": "ablation", "config": {"enforce_budget": False}, "label": "Ablation: Disable Budget"},
        "A3": {"mode": "ablation", "config": {"enforce_sources": False}, "label": "Ablation: Disable Sources"},
    }

    eval_results = {}
    for c_id, c_spec in conditions.items():
        print(f"Evaluating condition {c_id}: {c_spec['label']}...")
        res = evaluate_condition(cases, mode=c_spec["mode"], config=c_spec["config"])
        eval_results[c_id] = res

        # Write traces
        trace_file = OUT_DIR / f"trace_{c_id}.jsonl"
        with trace_file.open("w", encoding="utf-8") as tf:
            for tr in res["traces"]:
                tf.write(json.dumps(tr, ensure_ascii=False) + "\n")

    # Statistical significance comparisons against Intervention I1
    ref = eval_results["I1"]
    comparisons = {}
    for c_id in ["B0", "B1", "A1", "A2", "A3"]:
        comp = eval_results[c_id]
        
        # McNemar on correctness
        b = sum(1 for i in range(len(cases)) if ref["per_case_correct"][i] and not comp["per_case_correct"][i])
        c = sum(1 for i in range(len(cases)) if not ref["per_case_correct"][i] and comp["per_case_correct"][i])
        m_stat, m_pval = mcnemar_test(b, c)

        # Paired t-test on prerequisite violations
        t_stat, t_pval = paired_t_test(
            [float(x) for x in comp["prereq_violations"]],
            [float(x) for x in ref["prereq_violations"]]
        )

        comparisons[f"I1_vs_{c_id}"] = {
            "comparison": f"I1 vs {c_id}",
            "mcnemar_b": b,
            "mcnemar_c": c,
            "mcnemar_stat": round(m_stat, 4),
            "mcnemar_p_value": m_pval,
            "paired_t_violations_stat": round(t_stat, 4),
            "paired_t_violations_p_value": t_pval,
        }

    # Prepare summary report without per_case lists for clean JSON
    summary_report = {
        "study": "LN-06",
        "title": "Cognitively Constrained Heritage Trails & Route Optimization",
        "dataset": "research/fixtures/holdout/LN-06_holdout.jsonl",
        "n_cases": len(cases),
        "results": {
            c_id: {k: v for k, v in res.items() if k not in ("per_case_correct", "traces", "prereq_violations", "outcome_coverages", "route_costs")}
            for c_id, res in eval_results.items()
        },
        "statistical_comparisons": comparisons,
    }

    summary_file = OUT_DIR / "LN-06_holdout_summary.json"
    summary_file.write_text(json.dumps(summary_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved holdout summary to {summary_file}")

    print("\n================== LN-06 HOLDOUT BENCHMARK SUMMARY ==================")
    print(f"{'Condition':<6} | {'Label':<35} | {'Acc (%)':<9} | {'95% CI':<18} | {'Violations':<11} | {'Coverage':<9} | {'Cost':<7}")
    print("-" * 105)
    for c_id, c_spec in conditions.items():
        r = eval_results[c_id]
        ci_str = f"[{r['accuracy_ci_95'][0]:.3f}, {r['accuracy_ci_95'][1]:.3f}]"
        print(f"{c_id:<6} | {c_spec['label']:<35} | {r['accuracy']*100:>7.2f}% | {ci_str:<18} | {r['total_prerequisite_violations']:>11} | {r['mean_outcome_coverage']:>8.3f} | {r['mean_route_cost']:>6.1f}")

    print("\nStatistical Significance vs I1 (Cognitive DAG Trail Planner):")
    for comp_name, comp_data in comparisons.items():
        print(f"  {comp_name:<12}: McNemar chi2={comp_data['mcnemar_stat']:>7.2f} (p={comp_data['mcnemar_p_value']:.2e}), Paired t (viol)={comp_data['paired_t_violations_stat']:>7.2f} (p={comp_data['paired_t_violations_p_value']:.2e})")


if __name__ == "__main__":
    main()
