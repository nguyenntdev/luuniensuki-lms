# -*- coding: utf-8 -*-
"""Holdout evaluation runner and statistical analysis for LN-02.
Evaluates B0, B1, I1, A1, A2, A3 across the 120 holdout scenarios.
Computes metrics, 95% CIs, McNemar tests, and outputs structured results.
"""
from __future__ import annotations

import json
import math
import pathlib
from typing import Any, Optional
import scipy.stats as stats

from backend.domain.competency_prerequisites import (
    RecommendationDecision,
    ReasonCode,
    POLICY_VERSION,
    detect_dependency_cycle,
    validate_score_value,
    validate_all_scenario_scores,
    calculate_competency_coverage,
    evaluate_intervention,
    evaluate_baseline,
    evaluate_ablation,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOLDOUT_FILE = ROOT / "research" / "fixtures" / "holdout" / "LN-02_holdout.jsonl"


def evaluate_b1_irt(scenario_input: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """B1: Stronger baseline - Item Response Theory (1PL / Rasch proxy) without prerequisite graph.

    Models learner as a 1D scalar ability theta, estimated from available responses/mastery.
    Target task difficulty beta is the average prerequisite threshold.
    Item response logistic probability:
        P(correct | theta, beta) = 1 / (1 + exp(-1.7 * (theta - beta)))
    Task is recommended if expected success probability P >= 0.50 (i.e. theta >= beta).

    Critically, B1:
    1. Ignores the prerequisite dependency graph (does not detect cycles).
    2. Does not validate domain ranges [0, 1] on scores or mastery.
    3. Collapses multidimensional competencies S1-S4 into 1D scalar theta, allowing
       compensatory trade-offs (e.g. high S2 compensates for deficient S1).
    4. Does not abstain when critical prerequisite dimensions are unobserved.
    """
    mastery = scenario_input.get("mastery", {})
    score_observed = scenario_input.get("score_observed")
    target_task = scenario_input.get("target_task", {})
    prerequisites = target_task.get("prerequisites", {})

    # Estimate scalar theta from available numeric mastery values or score_observed
    valid_scores = [v for v in mastery.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if valid_scores:
        theta = sum(valid_scores) / len(valid_scores)
    elif validate_score_value(score_observed):
        theta = float(score_observed)
    else:
        theta = 0.5  # default prior

    # Target task difficulty beta is the mean required prerequisite threshold
    if prerequisites:
        beta = sum(prerequisites.values()) / len(prerequisites)
    else:
        beta = 0.5

    # 1PL logistic probability with D=1.7
    z = 1.7 * (theta - beta)
    z_clamped = max(min(z, 50.0), -50.0)
    p_success = 1.0 / (1.0 + math.exp(-z_clamped))

    recommended = bool(p_success >= 0.50)
    decision = RecommendationDecision.recommend_eligible.value if recommended else RecommendationDecision.remediate_first.value

    # Check for actual prerequisite violation
    has_unmet_prereq = False
    for req_dim, req_val in prerequisites.items():
        if req_dim not in mastery or mastery[req_dim] is None or mastery[req_dim] < req_val:
            has_unmet_prereq = True
            break

    prerequisite_violated = bool(recommended and has_unmet_prereq)
    unjustified = bool(
        recommended
        and (
            has_unmet_prereq
            or not validate_all_scenario_scores(scenario_input)
            or detect_dependency_cycle(scenario_input.get("graph_edges", []))
        )
    )

    return {
        "decision": decision,
        "reason_codes": ["IRT_1PL_UNIDIMENSIONAL_SCORE"],
        "policy_version": "ln02-b1-irt-v1.0",
        "prerequisite_violated": prerequisite_violated,
        "competency_coverage": calculate_competency_coverage(mastery),
        "unjustified_recommendation": unjustified,
        "research_only": True,
        "irt_theta": round(theta, 4),
        "irt_beta": round(beta, 4),
        "p_success": round(p_success, 4),
    }


def wilson_score_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = successes / n
    denominator = 1 + z**2 / n
    centre_adjusted_probability = p + z**2 / (2 * n)
    adjusted_limits = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    lower = max(0.0, (centre_adjusted_probability - adjusted_limits) / denominator)
    upper = min(1.0, (centre_adjusted_probability + adjusted_limits) / denominator)
    return round(lower, 4), round(upper, 4)


def mcnemar_test(y_true: list[bool], pred_a: list[bool], pred_b: list[bool]) -> dict[str, Any]:
    """Perform McNemar test for paired nominal data (comparing accuracy of model A vs model B)."""
    # b: A correct, B wrong
    # c: A wrong, B correct
    b = sum(1 for yt, pa, pb in zip(y_true, pred_a, pred_b) if pa == yt and pb != yt)
    c = sum(1 for yt, pa, pb in zip(y_true, pred_a, pred_b) if pa != yt and pb == yt)

    # Edwards continuity correction
    if (b + c) == 0:
        chi2 = 0.0
        p_val = 1.0
    else:
        chi2 = ((abs(b - c) - 1.0) ** 2) / (b + c)
        p_val = stats.chi2.sf(chi2, df=1)

    return {
        "b_modelA_correct_modelB_wrong": b,
        "c_modelA_wrong_modelB_correct": c,
        "chi2": round(chi2, 4),
        "p_value": p_val,
        "significant_p001": bool(p_val < 0.001),
        "significant_p05": bool(p_val < 0.05),
    }


def main():
    with open(HOLDOUT_FILE, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(cases)} holdout cases from {HOLDOUT_FILE}")

    # Conditions to evaluate
    conditions = {
        "B0": lambda inp: evaluate_baseline(inp),
        "B1": lambda inp: evaluate_b1_irt(inp),
        "I1": lambda inp: evaluate_intervention(inp),
        "A1": lambda inp: evaluate_ablation(inp, config={"variant": "no_prerequisites"}),
        "A2": lambda inp: evaluate_ablation(inp, config={"variant": "single_latent_skill"}),
        "A3": lambda inp: evaluate_ablation(inp, config={"variant": "no_abstention"}),
    }

    results: dict[str, list[dict[str, Any]]] = {cond: [] for cond in conditions}

    for case in cases:
        inp = case["input"]
        exp_dec = case["oracle"]["expected_decision"]
        fid = case["fault_id"]

        for cond_name, fn in conditions.items():
            res = fn(inp)
            res["case_id"] = case["case_id"]
            res["fault_id"] = fid
            res["oracle_expected"] = exp_dec
            res["oracle_match"] = (res["decision"] == exp_dec)
            results[cond_name].append(res)

    # Compute metrics per condition
    summary: dict[str, Any] = {}
    for cond_name, rows in results.items():
        total_n = len(rows)
        oracle_matches = sum(1 for r in rows if r["oracle_match"])
        accuracy = oracle_matches / total_n
        acc_ci = wilson_score_interval(oracle_matches, total_n)

        # Prerequisite violation rate on missing_prerequisite stratum (N=24)
        missing_prereq_rows = [r for r in rows if r["fault_id"] == "missing_prerequisite"]
        mp_n = len(missing_prereq_rows)
        mp_viol = sum(1 for r in missing_prereq_rows if r["prerequisite_violated"])
        mp_viol_rate = mp_viol / mp_n if mp_n > 0 else 0.0
        mp_viol_ci = wilson_score_interval(mp_viol, mp_n)

        # Overall prerequisite violation count across all 120 cases
        overall_viol = sum(1 for r in rows if r["prerequisite_violated"])
        overall_viol_rate = overall_viol / total_n
        overall_viol_ci = wilson_score_interval(overall_viol, total_n)

        # Unjustified recommendations
        overall_unjustified = sum(1 for r in rows if r["unjustified_recommendation"])

        # Competency coverage mean
        covs = [r["competency_coverage"] for r in rows]
        cov_mean = sum(covs) / len(covs)
        cov_std = math.sqrt(sum((c - cov_mean) ** 2 for c in covs) / (len(covs) - 1))

        # Breakdown by fault_id
        fault_breakdown = {}
        for fid in ["nominal", "missing_prerequisite", "latent_dimension_unobserved", "cyclic_prerequisite", "out_of_range_score"]:
            f_rows = [r for r in rows if r["fault_id"] == fid]
            f_matches = sum(1 for r in f_rows if r["oracle_match"])
            f_viol = sum(1 for r in f_rows if r["prerequisite_violated"])
            fault_breakdown[fid] = {
                "n": len(f_rows),
                "oracle_matches": f_matches,
                "oracle_accuracy": round(f_matches / len(f_rows), 4),
                "violations": f_viol,
            }

        summary[cond_name] = {
            "condition": cond_name,
            "total_cases": total_n,
            "oracle_matches": oracle_matches,
            "accuracy": round(accuracy, 4),
            "accuracy_95ci": acc_ci,
            "prereq_violations_on_missing_stratum": mp_viol,
            "prereq_violation_rate_missing_stratum": round(mp_viol_rate, 4),
            "prereq_violation_rate_missing_stratum_95ci": mp_viol_ci,
            "overall_violations": overall_viol,
            "overall_violation_rate": round(overall_viol_rate, 4),
            "overall_violation_rate_95ci": overall_viol_ci,
            "overall_unjustified_recommendations": overall_unjustified,
            "mean_competency_coverage": round(cov_mean, 4),
            "std_competency_coverage": round(cov_std, 4),
            "fault_breakdown": fault_breakdown,
        }

    # Paired McNemar tests comparing I1 against other conditions
    mcnemar_comparisons = {}
    y_true = [True] * len(cases)
    i1_matches = [r["oracle_match"] for r in results["I1"]]

    for other in ["B0", "B1", "A1", "A2", "A3"]:
        other_matches = [r["oracle_match"] for r in results[other]]
        mcnemar_comparisons[f"I1_vs_{other}"] = mcnemar_test(y_true, i1_matches, other_matches)

    # Also compare violation rate on missing_prerequisite stratum
    # For missing_prereq cases: I1 has 0 violations, others have violations
    mp_indices = [idx for idx, c in enumerate(cases) if c["fault_id"] == "missing_prerequisite"]
    violation_comparisons = {}
    for other in ["B0", "B1", "A1", "A2", "A3"]:
        i1_viol = [results["I1"][idx]["prerequisite_violated"] for idx in mp_indices]
        other_viol = [results[other][idx]["prerequisite_violated"] for idx in mp_indices]
        # In terms of safe decisions (not violated): True = safe (not violated)
        i1_safe = [not v for v in i1_viol]
        other_safe = [not v for v in other_viol]
        violation_comparisons[f"I1_vs_{other}_safety"] = mcnemar_test([True] * len(mp_indices), i1_safe, other_safe)

    full_output = {
        "summary": summary,
        "mcnemar_accuracy_comparisons": mcnemar_comparisons,
        "mcnemar_prereq_safety_comparisons": violation_comparisons,
    }

    out_json = ROOT / "research" / "fixtures" / "holdout" / "LN-02_holdout_evaluation.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved evaluation results to {out_json}")
    print("\n" + "=" * 80)
    print("HOLDOUT EVALUATION SUMMARY:")
    print("=" * 80)
    print(f"{'Condition':<10} | {'Acc (%)':<10} | {'95% CI':<18} | {'Prereq Viol (N=24)':<20} | {'Overall Viol':<14} | {'Unjustified':<12}")
    print("-" * 80)
    for c, s in summary.items():
        acc_str = f"{s['accuracy']*100:.1f}%"
        ci_str = f"[{s['accuracy_95ci'][0]*100:.1f}%, {s['accuracy_95ci'][1]*100:.1f}%]"
        pv_str = f"{s['prereq_violations_on_missing_stratum']}/24 ({s['prereq_violation_rate_missing_stratum']*100:.1f}%)"
        print(f"{c:<10} | {acc_str:<10} | {ci_str:<18} | {pv_str:<20} | {s['overall_violations']:<14} | {s['overall_unjustified_recommendations']:<12}")

    print("\n" + "=" * 80)
    print("PAIRED MCNEMAR TESTS (I1 vs Baselines & Ablations on Oracle Agreement):")
    print("=" * 80)
    for comp, res in mcnemar_comparisons.items():
        print(f"{comp:<15}: b={res['b_modelA_correct_modelB_wrong']}, c={res['c_modelA_wrong_modelB_correct']}, chi2={res['chi2']:.4f}, p={res['p_value']:.4e} (sig p<0.001: {res['significant_p001']})")

    print("\n" + "=" * 80)
    print("PAIRED MCNEMAR TESTS ON PREREQUISITE SAFETY (missing_prerequisite stratum N=24):")
    print("=" * 80)
    for comp, res in violation_comparisons.items():
        print(f"{comp:<22}: b={res['b_modelA_correct_modelB_wrong']}, c={res['c_modelA_wrong_modelB_correct']}, chi2={res['chi2']:.4f}, p={res['p_value']:.4e}")

if __name__ == "__main__":
    main()
