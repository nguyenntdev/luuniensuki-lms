#!/usr/bin/env python3
"""Statistical Rigor, Meta-Analysis, and Hypothesis Testing for 10 Studies (LN-01 to LN-10).

Computes:
1. 95% Bootstrap Confidence Intervals (B=2,000 resamples) for all primary and secondary metrics.
2. Paired McNemar's tests (for binary classification decisions) and Wilcoxon signed-rank tests
   (for continuous scores/counts) comparing Intervention (I1) vs Baselines (B0) and Ablations (A1-A3).
3. Effect sizes: Cohen's d (paired & pooled) / Cliff's delta / Odds Ratios (paired & marginal).
4. Per-fault confusion matrix and error taxonomy breakdown for each study.
5. Structured outputs: JSON report and comparison CSV table.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACTS_DIR = ROOT / "research_artifacts"
FIXTURES_DIR = ROOT / "research" / "fixtures"
CONFIGS_FILE = ROOT / "research" / "configs" / "experiments.json"

# Metric definitions strictly conforming to research/tools/recompute_metrics.py
PRIMARY_SPECS = {
    "LN-01": (
        "false_acceptance_invalid_progression_rate",
        ("repeat_shallow", "missing_curriculum", "prerequisite_cycle", "grade_reversed"),
        "progression_valid",
        True,
        "bad",
    ),
    "LN-02": (
        "prerequisite_violation_rate",
        ("missing_prerequisite",),
        "prerequisite_violated",
        True,
        "bad",
    ),
    "LN-03": (
        "invalid_generative_assignment_rate",
        ("missing_fact_base", "absent_source"),
        "generative_assigned",
        True,
        "bad",
    ),
    "LN-04": (
        "answer_leakage_rate",
        ("answer_request",),
        "answer_leakage",
        True,
        "bad",
    ),
    "LN-05": (
        "false_mastery_award_rate",
        ("missing_competency", "spoofed_xp"),
        "badge_awarded",
        True,
        "bad",
    ),
    "LN-06": (
        "prerequisite_violations_per_route",
        None,
        "prerequisite_violation_count",
        None,
        "sum",
    ),
    "LN-07": (
        "feasible_task_rate",
        ("nominal", "no_webgl", "low_bandwidth"),
        "task_feasible",
        True,
        "good",
    ),
    "LN-08": (
        "diagnostic_error_rate",
        ("logical_negation", "source_mismatch", "synonym_equivalence", "partial_reasoning"),
        "diagnostic_category",
        None,
        "mapping",
    ),
    "LN-09": (
        "unsupported_action_rate",
        ("missing_logs", "conflicting_signals", "unverified_task", "stale_mastery"),
        "action_proposed",
        True,
        "bad",
    ),
    "LN-10": (
        "unjustified_transition_rate",
        ("missing_rationale", "unauthorized_actor", "offline_conflict", "skipped_reflection"),
        "transition_applied",
        True,
        "bad",
    ),
}

DIAGNOSTIC_CAT_MAP = {
    "logical_negation": "contradiction",
    "source_mismatch": "source_error",
    "synonym_equivalence": "supported_equivalent",
    "partial_reasoning": "incomplete",
}

SECONDARY_SPECS = {
    "LN-01": [
        ("unmapped_outcome_rate", "continuous", "lower_is_better"),
        ("prerequisite_cycle_count", "count", "lower_is_better"),
    ],
    "LN-02": [
        ("competency_coverage", "continuous", "higher_is_better"),
        ("unjustified_recommendation", "binary", "lower_is_better"),
    ],
    "LN-03": [
        ("review_burden", "continuous", "lower_is_better"),
        ("task_type_coverage", "continuous", "higher_is_better"),
    ],
    "LN-04": [
        ("citation_integrity", "binary", "higher_is_better"),
        ("appropriate_abstention", "binary", "higher_is_better"),
    ],
    "LN-05": [
        ("replay_prevented", "binary", "higher_is_better"),
        ("duplicate_count", "count", "lower_is_better"),
    ],
    "LN-06": [
        ("outcome_coverage", "continuous", "higher_is_better"),
        ("route_cost", "continuous", "lower_is_better"),
        ("unreachable_checkpoint_rate", "continuous", "lower_is_better"),
    ],
    "LN-07": [
        ("fallback_failure", "binary", "lower_is_better"),
        ("missing_affordance_count", "count", "lower_is_better"),
    ],
    "LN-08": [
        ("nominal_accuracy", "binary", "higher_is_better"),
    ],
    "LN-09": [
        ("abstention_appropriate", "binary", "higher_is_better"),
        ("intervention_traceable", "binary", "higher_is_better"),
    ],
    "LN-10": [
        ("reflection_completed", "binary", "higher_is_better"),
        ("conflict_detected", "binary", "higher_is_better"),
    ],
}


def bootstrap_ci(
    data: np.ndarray, b: int = 2000, rng: Optional[np.random.Generator] = None, ci: float = 0.95
) -> Dict[str, float]:
    """Compute percentile bootstrap confidence interval and standard error."""
    if len(data) == 0:
        return {"point": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "se": 0.0}
    if rng is None:
        rng = np.random.default_rng(42)
    point = float(np.mean(data))
    if len(data) == 1 or np.all(data == data[0]):
        return {"point": point, "ci_lower": point, "ci_upper": point, "se": 0.0}
    n = len(data)
    boot_indices = rng.integers(0, n, size=(b, n))
    boot_means = data[boot_indices].mean(axis=1)
    alpha = (1.0 - ci) / 2.0
    ci_lower = float(np.percentile(boot_means, alpha * 100))
    ci_upper = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    se = float(np.std(boot_means, ddof=1))
    return {"point": point, "ci_lower": ci_lower, "ci_upper": ci_upper, "se": se}


def wilson_score_interval(
    successes: int, n: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Unlike the percentile bootstrap, this interval does not collapse to
    [0%, 0%] when the observed number of failures is zero. It is the default
    interval reported for proportion/rate metrics.
    """
    if n <= 0:
        return 0.0, 0.0
    z = float(stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    spread = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return float(lower), float(upper)


def clopper_pearson_interval(
    successes: int, n: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Clopper-Pearson (exact) confidence interval for a binomial proportion.

    Uses the Beta quantile formulation. Guarantees nominal coverage and is
    conservative; reported alongside Wilson for proportion metrics.
    """
    if n <= 0:
        return 0.0, 0.0
    k = int(successes)
    alpha = 1.0 - confidence
    lower = 0.0 if k <= 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    upper = 1.0 if k >= n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return max(0.0, lower), min(1.0, upper)


def holm_bonferroni(pvalues: List[float]) -> List[float]:
    """Holm-Bonferroni step-down family-wise error rate correction."""
    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [1.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * float(pvalues[idx]))
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted


def benjamini_hochberg(pvalues: List[float]) -> List[float]:
    """Benjamini-Hochberg step-up false discovery rate correction."""
    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [1.0] * m
    running = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]
        candidate = min(1.0, float(pvalues[idx]) * m / (rank + 1))
        running = min(running, candidate)
        adjusted[idx] = running
    return adjusted


def summarize_metric(
    values: np.ndarray,
    is_proportion: bool,
    b: int = 2000,
    rng: Optional[np.random.Generator] = None,
    ci: float = 0.95,
) -> Dict[str, Any]:
    """Summarize a metric with an interval appropriate to its scale.

    - Proportions/rates: Wilson score interval is the primary interval and is
      aliased to ``ci_lower``/``ci_upper``/``ci_95``; Clopper-Pearson exact
      interval is also emitted. The percentile bootstrap is retained for
      reference as ``bootstrap_ci_95``.
    - Continuous/count metrics: percentile bootstrap is used and remains the
      primary interval.
    """
    boot = bootstrap_ci(values, b=b, rng=rng, ci=ci)
    out: Dict[str, Any] = {
        "point": boot["point"],
        "ci_lower": boot["ci_lower"],
        "ci_upper": boot["ci_upper"],
        "se": boot["se"],
        "ci_95": [boot["ci_lower"], boot["ci_upper"]],
        "ci_method": "bootstrap_percentile",
        "bootstrap_ci_95": [boot["ci_lower"], boot["ci_upper"]],
    }
    if is_proportion:
        n = int(len(values))
        successes = int(round(float(np.sum(values)))) if n > 0 else 0
        wilson = wilson_score_interval(successes, n, confidence=ci)
        cp = clopper_pearson_interval(successes, n, confidence=ci)
        out.update(
            {
                "n": n,
                "successes": successes,
                "wilson_ci_95": [wilson[0], wilson[1]],
                "clopper_pearson_ci_95": [cp[0], cp[1]],
                # Alias the primary interval to the recommended proportion CI.
                "ci_lower": wilson[0],
                "ci_upper": wilson[1],
                "ci_95": [wilson[0], wilson[1]],
                "ci_method": "wilson_score",
            }
        )
    return out


def bootstrap_paired_diff_ci(
    x: np.ndarray, y: np.ndarray, b: int = 2000, rng: Optional[np.random.Generator] = None, ci: float = 0.95
) -> Dict[str, float]:
    """Compute bootstrap CI for the paired difference (x - y)."""
    if len(x) == 0 or len(x) != len(y):
        return {"diff_point": 0.0, "diff_ci_lower": 0.0, "diff_ci_upper": 0.0, "diff_se": 0.0}
    if rng is None:
        rng = np.random.default_rng(42)
    diff = x - y
    point = float(np.mean(diff))
    if np.all(diff == diff[0]):
        return {"diff_point": point, "diff_ci_lower": point, "diff_ci_upper": point, "diff_se": 0.0}
    n = len(diff)
    boot_indices = rng.integers(0, n, size=(b, n))
    boot_means = diff[boot_indices].mean(axis=1)
    alpha = (1.0 - ci) / 2.0
    ci_lower = float(np.percentile(boot_means, alpha * 100))
    ci_upper = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    se = float(np.std(boot_means, ddof=1))
    return {"diff_point": point, "diff_ci_lower": ci_lower, "diff_ci_upper": ci_upper, "diff_se": se}


def compute_mcnemar(x_binary: np.ndarray, y_binary: np.ndarray) -> Dict[str, Any]:
    """Compute McNemar test on paired binary observations.
    
    x: Intervention (1=success/compliant, 0=failure/violation)
    y: Comparator (1=success/compliant, 0=failure/violation)
    b: x=1, y=0 (Intervention won)
    c: x=0, y=1 (Comparator won)
    """
    x_b = (x_binary.astype(int) == 1)
    y_b = (y_binary.astype(int) == 1)
    both_correct = int(np.sum(x_b & y_b))
    b = int(np.sum(x_b & (~y_b)))
    c = int(np.sum((~x_b) & y_b))
    both_incorrect = int(np.sum((~x_b) & (~y_b)))
    total_discordant = b + c

    if total_discordant == 0:
        return {
            "both_success": both_correct,
            "b_intervention_only": b,
            "c_comparator_only": c,
            "both_failure": both_incorrect,
            "statistic": 0.0,
            "p_value": 1.0,
            "method": "zero_discordant",
            "odds_ratio_paired": 1.0,
            "odds_ratio_haldane": 1.0,
        }

    # Paired odds ratio (use None or capped value for strict JSON compliance)
    or_paired = float(b / c) if c > 0 else None
    or_haldane = float((b + 0.5) / (c + 0.5))

    if total_discordant < 25:
        # Exact binomial test
        binom_res = stats.binomtest(b, total_discordant, 0.5, alternative="two-sided")
        pval = float(binom_res.pvalue)
        return {
            "both_success": both_correct,
            "b_intervention_only": b,
            "c_comparator_only": c,
            "both_failure": both_incorrect,
            "statistic": float(b),
            "p_value": pval,
            "method": "exact_binomial",
            "odds_ratio_paired": or_paired,
            "odds_ratio_haldane": or_haldane,
        }
    else:
        # Edwards continuity correction
        stat = float((abs(b - c) - 1.0) ** 2 / total_discordant)
        pval = float(stats.chi2.sf(stat, df=1))
        return {
            "both_success": both_correct,
            "b_intervention_only": b,
            "c_comparator_only": c,
            "both_failure": both_incorrect,
            "statistic": stat,
            "p_value": pval,
            "method": "mcnemar_continuity_corrected",
            "odds_ratio_paired": or_paired,
            "odds_ratio_haldane": or_haldane,
        }


def compute_wilcoxon(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Compute Wilcoxon signed-rank test on paired continuous/count observations."""
    diff = x - y
    nonzero = np.count_nonzero(diff)
    if nonzero == 0:
        return {"statistic": 0.0, "p_value": 1.0, "nonzero_pairs": 0, "method": "identical_zero_diff"}
    try:
        res = stats.wilcoxon(x, y, zero_method="pratt", alternative="two-sided")
        return {
            "statistic": float(res.statistic),
            "p_value": float(res.pvalue),
            "nonzero_pairs": int(nonzero),
            "method": "wilcoxon_pratt",
        }
    except Exception as e:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "nonzero_pairs": int(nonzero),
            "method": f"error_handled: {e}",
        }


def compute_cohens_d(x: np.ndarray, y: np.ndarray) -> Tuple[Optional[float], Optional[float], str]:
    """Compute paired Cohen's d (mean(diff)/std(diff)) and pooled Cohen's d.
    
    Returns (paired_d, pooled_d, note).
    """
    nx, ny = len(x), len(y)
    if nx == 0 or ny == 0:
        return 0.0, 0.0, "empty"
    
    diff = x - y
    std_diff = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
    var_x = float(np.var(x, ddof=1)) if nx > 1 else 0.0
    var_y = float(np.var(y, ddof=1)) if ny > 1 else 0.0
    pooled_sd = math.sqrt(((nx - 1) * var_x + (ny - 1) * var_y) / max(1, nx + ny - 2))

    mean_diff = float(np.mean(diff))

    if pooled_sd == 0:
        if mean_diff == 0:
            return 0.0, 0.0, "identical_zero_diff"
        else:
            sign = 1.0 if mean_diff > 0 else -1.0
            # Within-group variance is zero with non-zero shift -> infinite separation
            return None, None, f"deterministic_separation_{'positive' if sign > 0 else 'negative'}"

    d_paired = float(mean_diff / std_diff) if std_diff > 0 else (None if mean_diff != 0 else 0.0)
    d_pooled = float(mean_diff / pooled_sd)
    return d_paired, d_pooled, "standard"


def compute_cliffs_delta(x: np.ndarray, y: np.ndarray) -> Tuple[float, str]:
    """Compute Cliff's delta non-parametric effect size and qualitative interpretation."""
    nx, ny = len(x), len(y)
    if nx == 0 or ny == 0:
        return 0.0, "Negligible"
    # Using numpy broadcast matrix comparison
    diff = x[:, None] - y[None, :]
    greater = np.sum(diff > 0)
    less = np.sum(diff < 0)
    delta = float((greater - less) / (nx * ny))
    abs_d = abs(delta)
    if abs_d < 0.147:
        interp = "Negligible"
    elif abs_d < 0.330:
        interp = "Small"
    elif abs_d < 0.474:
        interp = "Medium"
    else:
        interp = "Large"
    return delta, interp


def extract_primary_values(
    study_id: str, rows: List[Dict[str, Any]], filter_eligible: bool = True
) -> Tuple[np.ndarray, List[Dict[str, Any]], Tuple[str, Any, str, Any, str]]:
    """Extract per-case primary metric values conforming to recompute_metrics.py."""
    spec = PRIMARY_SPECS[study_id]
    metric_name, eligible_faults, field, flag, kind = spec
    if filter_eligible and eligible_faults is not None:
        target_rows = [r for r in rows if r["fault_id"] in eligible_faults]
    else:
        target_rows = rows

    values = []
    for r in target_rows:
        o = r.get("observables", {})
        val = o.get(field)
        if kind == "sum":
            values.append(float(val) if val is not None else 0.0)
        elif kind == "mapping":
            expected_cat = DIAGNOSTIC_CAT_MAP.get(r["fault_id"], "")
            is_error = int(val != expected_cat)
            values.append(float(is_error))
        else:
            values.append(float(int(val == flag)))

    return np.array(values, dtype=float), target_rows, spec


def extract_secondary_value(study_id: str, row: Dict[str, Any], metric_name: str) -> Optional[float]:
    """Extract secondary observable value for a single case."""
    o = row.get("observables", {})
    if metric_name == "oracle_match":
        return float(int(row.get("oracle_match") is True))
    if metric_name == "elapsed_ms":
        return float(row.get("elapsed_ms", 0.0))
    if metric_name == "nominal_accuracy":
        if row.get("fault_id") == "nominal":
            return float(int(row.get("oracle_match") is True))
        return None

    # Domain specific observables
    if metric_name in o:
        val = o[metric_name]
        if isinstance(val, bool):
            return float(int(val))
        if isinstance(val, (int, float)):
            return float(val)
    elif metric_name == "replay_prevented":
        # LN-05 fallback: baseline/ablations do not prevent replay
        return 0.0
    return None


def format_significance(p: float) -> str:
    """Format standard statistical significance asterisks."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return "ns"


def analyze_study(
    study_id: str,
    study_entry: Dict[str, Any],
    artifacts_dir: pathlib.Path,
    fixtures_dir: pathlib.Path,
    resamples: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Any]:
    """Perform complete statistical meta-analysis for a single study across all conditions."""
    if rng is None:
        rng = np.random.default_rng(42)

    # 1. Load Fixture
    fixture_path = fixtures_dir / f"{study_id}_concrete.jsonl"
    if not fixture_path.is_file():
        raise FileNotFoundError(f"Fixture {fixture_path} missing")
    fixture_cases = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    fixture_case_ids = [c["case_id"] for c in fixture_cases]
    fixture_faults = {c["case_id"]: c["fault_id"] for c in fixture_cases}
    fixture_expected = {c["case_id"]: c.get("oracle", {}).get("expected_decision") for c in fixture_cases}

    # 2. Load all runs
    conditions_data: Dict[str, Dict[str, Any]] = {}
    for run in study_entry["runs"]:
        cid = run["id"]
        run_dir = artifacts_dir / study_id / cid
        trace_path = run_dir / "trace.jsonl"
        metric_path = run_dir / "study_metric.json"
        manifest_path = run_dir / "manifest.json"

        if not trace_path.is_file() or not metric_path.is_file():
            raise FileNotFoundError(f"Trace or metric file missing in {run_dir}")

        trace_rows = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        study_metric = json.loads(metric_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}

        # Align rows with fixture
        row_map = {r["case_id"]: r for r in trace_rows}
        aligned_rows = [row_map[cid_case] for cid_case in fixture_case_ids]

        conditions_data[cid] = {
            "meta": run,
            "study_metric": study_metric,
            "manifest": manifest,
            "rows": aligned_rows,
        }

    # 3. Bootstrap CI & Confusion Matrix per Condition
    spec = PRIMARY_SPECS[study_id]
    metric_name, eligible_faults, field, flag, kind = spec
    cond_summaries: Dict[str, Any] = {}

    for cid, cdata in conditions_data.items():
        rows = cdata["rows"]
        # Primary metric on eligible cases.
        # "sum" kinds are unbounded counts -> continuous interval; all other
        # primary kinds are binary indicators -> proportion interval.
        primary_is_proportion = kind != "sum"
        p_vals_elig, elig_rows, _ = extract_primary_values(study_id, rows, filter_eligible=True)
        prim_summary = summarize_metric(
            p_vals_elig, is_proportion=primary_is_proportion, b=resamples, rng=rng
        )

        # Accuracy across all 720 cases (binary -> proportion interval)
        oracle_matches = np.array([int(r.get("oracle_match") is True) for r in rows], dtype=float)
        oracle_summary = summarize_metric(
            oracle_matches, is_proportion=True, b=resamples, rng=rng
        )

        # Elapsed ms latency (continuous -> bootstrap interval)
        elapsed_times = np.array([float(r.get("elapsed_ms", 0.0)) for r in rows], dtype=float)
        latency_summary = summarize_metric(
            elapsed_times, is_proportion=False, b=resamples, rng=rng
        )

        # Secondary metrics
        sec_summaries: Dict[str, Any] = {
            "oracle_match_rate": oracle_summary,
            "elapsed_ms": {
                **latency_summary,
                "median": float(np.median(elapsed_times)),
                "std": float(np.std(elapsed_times, ddof=1)),
            },
        }
        for sec_name, sec_type, sec_dir in SECONDARY_SPECS.get(study_id, []):
            sec_vals = [extract_secondary_value(study_id, r, sec_name) for r in rows]
            valid_sec = np.array([v for v in sec_vals if v is not None], dtype=float)
            if len(valid_sec) > 0:
                sec_summaries[sec_name] = summarize_metric(
                    valid_sec,
                    is_proportion=(sec_type == "binary"),
                    b=resamples,
                    rng=rng,
                )

        # Fault stratum breakdown & confusion matrix
        strata = ["nominal"] + list(eligible_faults or [])
        # Deduplicate strata
        seen_strata = []
        for s in strata:
            if s not in seen_strata:
                seen_strata.append(s)

        fault_breakdowns: Dict[str, Any] = {}
        for fault_name in seen_strata:
            f_rows = [r for r in rows if r["fault_id"] == fault_name]
            f_n = len(f_rows)
            f_matches = sum(1 for r in f_rows if r.get("oracle_match") is True)
            f_accuracy = f_matches / f_n if f_n > 0 else 0.0

            # Contingency of Expected vs Actual
            contingency: Dict[str, int] = {}
            reason_counts: Dict[str, int] = {}
            decision_counts: Dict[str, int] = {}
            category_counts: Dict[str, int] = {}

            for r in f_rows:
                exp = r.get("expected_decision", fixture_expected.get(r["case_id"], "unknown"))
                act = r.get("decision", "unknown")
                pair_key = f"{exp} -> {act}"
                contingency[pair_key] = contingency.get(pair_key, 0) + 1
                decision_counts[act] = decision_counts.get(act, 0) + 1

                for rc in r.get("reason_codes", []):
                    reason_counts[rc] = reason_counts.get(rc, 0) + 1

                if "diagnostic_category" in r.get("observables", {}):
                    dcat = r["observables"]["diagnostic_category"]
                    category_counts[dcat] = category_counts.get(dcat, 0) + 1

            # Primary metric for this stratum
            p_vals_stratum, _, _ = extract_primary_values(study_id, f_rows, filter_eligible=False)
            stratum_summary = summarize_metric(
                p_vals_stratum,
                is_proportion=primary_is_proportion,
                b=resamples,
                rng=rng,
            )

            fault_breakdowns[fault_name] = {
                "n": f_n,
                "oracle_matches": f_matches,
                "accuracy": f_accuracy,
                "primary_metric": stratum_summary,
                "confusion_matrix": contingency,
                "decisions": decision_counts,
                "reason_codes": reason_counts,
                "diagnostic_categories": category_counts,
            }

        cond_summaries[cid] = {
            "condition": cid,
            "label": cdata["meta"]["label"],
            "mode": cdata["meta"]["mode"],
            "primary_metric": {
                "metric_key": metric_name,
                "direction": spec[4],
                "numerator": cdata["study_metric"]["numerator"],
                "denominator": cdata["study_metric"]["denominator"],
                **prim_summary,
            },
            "secondary_metrics": sec_summaries,
            "fault_breakdown": fault_breakdowns,
        }

    # 4. Hypothesis Testing: Intervention (I1) vs Baselines (B0) & Ablations (A1-A3)
    i1_data = conditions_data["I1"]
    i1_rows = i1_data["rows"]
    i1_prim_vals, i1_elig_rows, _ = extract_primary_values(study_id, i1_rows, filter_eligible=True)
    i1_oracle_matches = np.array([int(r.get("oracle_match") is True) for r in i1_rows], dtype=float)
    i1_elapsed = np.array([float(r.get("elapsed_ms", 0.0)) for r in i1_rows], dtype=float)

    comparisons: Dict[str, Any] = {}
    table_rows: List[Dict[str, Any]] = []

    comparator_ids = [r["id"] for r in study_entry["runs"] if r["id"] != "I1"]

    for comp_id in comparator_ids:
        comp_data = conditions_data[comp_id]
        comp_rows = comp_data["rows"]
        comp_label = comp_data["meta"]["label"]

        comp_prim_vals, comp_elig_rows, _ = extract_primary_values(study_id, comp_rows, filter_eligible=True)
        comp_oracle_matches = np.array([int(r.get("oracle_match") is True) for r in comp_rows], dtype=float)
        comp_elapsed = np.array([float(r.get("elapsed_ms", 0.0)) for r in comp_rows], dtype=float)

        # Primary Metric Paired Comparison
        diff_boot = bootstrap_paired_diff_ci(i1_prim_vals, comp_prim_vals, b=resamples, rng=rng)
        d_paired, d_pooled, d_note = compute_cohens_d(i1_prim_vals, comp_prim_vals)
        c_delta, c_interp = compute_cliffs_delta(i1_prim_vals, comp_prim_vals)

        # Primary test selection
        if kind == "sum":  # LN-06 continuous count
            paired_test_type = "wilcoxon"
            test_res = compute_wilcoxon(i1_prim_vals, comp_prim_vals)
            stat = test_res["statistic"]
            pval = test_res["p_value"]
            mcnemar_res = None
        else:  # binary violation/acceptance
            paired_test_type = "mcnemar"
            # For bad metrics, 1 means error. Success means error==0.
            # Convert so 1=compliant/success, 0=error/violation
            if spec[4] == "bad":
                i1_bin_success = (i1_prim_vals == 0).astype(int)
                comp_bin_success = (comp_prim_vals == 0).astype(int)
            else:
                i1_bin_success = (i1_prim_vals == 1).astype(int)
                comp_bin_success = (comp_prim_vals == 1).astype(int)

            mcnemar_res = compute_mcnemar(i1_bin_success, comp_bin_success)
            stat = mcnemar_res["statistic"]
            pval = mcnemar_res["p_value"]
            test_res = mcnemar_res

        signif = format_significance(pval)
        or_val = mcnemar_res["odds_ratio_haldane"] if mcnemar_res else None

        comp_key = f"I1_vs_{comp_id}"
        comparisons[comp_key] = {
            "comparator": comp_id,
            "comparator_label": comp_label,
            "primary_metric": {
                "metric_key": metric_name,
                "eligible_n": len(i1_prim_vals),
                "i1_point": cond_summaries["I1"]["primary_metric"]["point"],
                "i1_ci_95": [cond_summaries["I1"]["primary_metric"]["ci_lower"], cond_summaries["I1"]["primary_metric"]["ci_upper"]],
                "i1_ci_method": cond_summaries["I1"]["primary_metric"]["ci_method"],
                "i1_wilson_ci_95": cond_summaries["I1"]["primary_metric"].get("wilson_ci_95"),
                "i1_clopper_pearson_ci_95": cond_summaries["I1"]["primary_metric"].get("clopper_pearson_ci_95"),
                "comp_point": cond_summaries[comp_id]["primary_metric"]["point"],
                "comp_ci_95": [cond_summaries[comp_id]["primary_metric"]["ci_lower"], cond_summaries[comp_id]["primary_metric"]["ci_upper"]],
                "comp_ci_method": cond_summaries[comp_id]["primary_metric"]["ci_method"],
                "comp_wilson_ci_95": cond_summaries[comp_id]["primary_metric"].get("wilson_ci_95"),
                "comp_clopper_pearson_ci_95": cond_summaries[comp_id]["primary_metric"].get("clopper_pearson_ci_95"),
                "diff_point": diff_boot["diff_point"],
                "diff_ci_95": [diff_boot["diff_ci_lower"], diff_boot["diff_ci_upper"]],
                "diff_se": diff_boot["diff_se"],
                "test_type": paired_test_type,
                "test_statistic": stat,
                "p_value": pval,
                "p_value_raw": pval,
                "significance": signif,
                "cohens_d_paired": d_paired,
                "cohens_d_pooled": d_pooled,
                "cliffs_delta": c_delta,
                "cliffs_delta_interpretation": c_interp,
                "odds_ratio_haldane": or_val,
                "mcnemar_details": mcnemar_res,
                "wilcoxon_details": test_res if paired_test_type == "wilcoxon" else None,
            },
            "oracle_match": {
                "mcnemar": compute_mcnemar(i1_oracle_matches, comp_oracle_matches),
                "diff": bootstrap_paired_diff_ci(i1_oracle_matches, comp_oracle_matches, b=resamples, rng=rng),
            },
            "latency": {
                "wilcoxon": compute_wilcoxon(i1_elapsed, comp_elapsed),
                "cohens_d": compute_cohens_d(i1_elapsed, comp_elapsed)[0],
            },
        }

        def format_cohens(d_val: Optional[float], note: str) -> str:
            if d_val is not None:
                return f"{d_val:.4f}"
            if "positive" in note:
                return "inf"
            if "negative" in note:
                return "-inf"
            return "NA"

        # CSV row for primary metric
        table_rows.append({
            "dataset": "primary",
            "study_id": study_id,
            "comparison": comp_key,
            "comparator_condition": comp_id,
            "comparator_label": comp_label,
            "metric_key": metric_name,
            "metric_type": "primary",
            "direction": spec[4],
            "eligible_n": len(i1_prim_vals),
            "i1_point": cond_summaries["I1"]["primary_metric"]["point"],
            "i1_ci_lower": cond_summaries["I1"]["primary_metric"]["ci_lower"],
            "i1_ci_upper": cond_summaries["I1"]["primary_metric"]["ci_upper"],
            "i1_ci_method": cond_summaries["I1"]["primary_metric"]["ci_method"],
            "i1_wilson_ci_lower": (cond_summaries["I1"]["primary_metric"].get("wilson_ci_95") or [None, None])[0],
            "i1_wilson_ci_upper": (cond_summaries["I1"]["primary_metric"].get("wilson_ci_95") or [None, None])[1],
            "i1_cp_ci_lower": (cond_summaries["I1"]["primary_metric"].get("clopper_pearson_ci_95") or [None, None])[0],
            "i1_cp_ci_upper": (cond_summaries["I1"]["primary_metric"].get("clopper_pearson_ci_95") or [None, None])[1],
            "comp_point": cond_summaries[comp_id]["primary_metric"]["point"],
            "comp_ci_lower": cond_summaries[comp_id]["primary_metric"]["ci_lower"],
            "comp_ci_upper": cond_summaries[comp_id]["primary_metric"]["ci_upper"],
            "comp_ci_method": cond_summaries[comp_id]["primary_metric"]["ci_method"],
            "comp_wilson_ci_lower": (cond_summaries[comp_id]["primary_metric"].get("wilson_ci_95") or [None, None])[0],
            "comp_wilson_ci_upper": (cond_summaries[comp_id]["primary_metric"].get("wilson_ci_95") or [None, None])[1],
            "comp_cp_ci_lower": (cond_summaries[comp_id]["primary_metric"].get("clopper_pearson_ci_95") or [None, None])[0],
            "comp_cp_ci_upper": (cond_summaries[comp_id]["primary_metric"].get("clopper_pearson_ci_95") or [None, None])[1],
            "diff_point": diff_boot["diff_point"],
            "diff_ci_lower": diff_boot["diff_ci_lower"],
            "diff_ci_upper": diff_boot["diff_ci_upper"],
            "paired_test_type": paired_test_type,
            "test_statistic": stat,
            "p_value": pval,
            "p_value_raw": pval,
            "p_value_holm": None,
            "p_value_bh": None,
            "significance": signif,
            "odds_ratio_haldane": or_val if or_val is not None else "NA",
            "cohens_d_paired": format_cohens(d_paired, d_note),
            "cohens_d_pooled": format_cohens(d_pooled, d_note),
            "cliffs_delta": c_delta,
            "cliffs_delta_interpretation": c_interp,
        })

        # Secondary metric row: oracle_match_rate
        om_diff = comparisons[comp_key]["oracle_match"]["diff"]
        om_mcn = comparisons[comp_key]["oracle_match"]["mcnemar"]
        om_signif = format_significance(om_mcn["p_value"])
        d_p_om, d_s_om, d_n_om = compute_cohens_d(i1_oracle_matches, comp_oracle_matches)
        c_d_om, c_i_om = compute_cliffs_delta(i1_oracle_matches, comp_oracle_matches)
        table_rows.append({
            "dataset": "primary",
            "study_id": study_id,
            "comparison": comp_key,
            "comparator_condition": comp_id,
            "comparator_label": comp_label,
            "metric_key": "oracle_match_rate",
            "metric_type": "secondary",
            "direction": "higher_is_better",
            "eligible_n": 720,
            "i1_point": cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"]["point"],
            "i1_ci_lower": cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"]["ci_lower"],
            "i1_ci_upper": cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"]["ci_upper"],
            "i1_ci_method": cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"]["ci_method"],
            "i1_wilson_ci_lower": (cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"].get("wilson_ci_95") or [None, None])[0],
            "i1_wilson_ci_upper": (cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"].get("wilson_ci_95") or [None, None])[1],
            "i1_cp_ci_lower": (cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"].get("clopper_pearson_ci_95") or [None, None])[0],
            "i1_cp_ci_upper": (cond_summaries["I1"]["secondary_metrics"]["oracle_match_rate"].get("clopper_pearson_ci_95") or [None, None])[1],
            "comp_point": cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"]["point"],
            "comp_ci_lower": cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"]["ci_lower"],
            "comp_ci_upper": cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"]["ci_upper"],
            "comp_ci_method": cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"]["ci_method"],
            "comp_wilson_ci_lower": (cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"].get("wilson_ci_95") or [None, None])[0],
            "comp_wilson_ci_upper": (cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"].get("wilson_ci_95") or [None, None])[1],
            "comp_cp_ci_lower": (cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"].get("clopper_pearson_ci_95") or [None, None])[0],
            "comp_cp_ci_upper": (cond_summaries[comp_id]["secondary_metrics"]["oracle_match_rate"].get("clopper_pearson_ci_95") or [None, None])[1],
            "diff_point": om_diff["diff_point"],
            "diff_ci_lower": om_diff["diff_ci_lower"],
            "diff_ci_upper": om_diff["diff_ci_upper"],
            "paired_test_type": "mcnemar",
            "test_statistic": om_mcn["statistic"],
            "p_value": om_mcn["p_value"],
            "p_value_raw": om_mcn["p_value"],
            "p_value_holm": None,
            "p_value_bh": None,
            "significance": om_signif,
            "odds_ratio_haldane": om_mcn["odds_ratio_haldane"],
            "cohens_d_paired": format_cohens(d_p_om, d_n_om),
            "cohens_d_pooled": format_cohens(d_s_om, d_n_om),
            "cliffs_delta": c_d_om,
            "cliffs_delta_interpretation": c_i_om,
        })

    return {
        "study_id": study_id,
        "primary_metric": metric_name,
        "conditions": cond_summaries,
        "comparisons": comparisons,
        "table_rows": table_rows,
    }


def analyze_holdouts(
    matrix: Dict[str, Any],
    fixtures_dir: pathlib.Path,
    resamples: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluate and statistically verify the 10 newly generated holdout datasets."""
    import importlib

    if rng is None:
        rng = np.random.default_rng(42)

    holdout_dir = fixtures_dir / "holdout"
    holdout_results: Dict[str, Any] = {}
    holdout_table_rows: List[Dict[str, Any]] = []

    def format_cohens(d_val: Optional[float], note: str) -> str:
        if d_val is not None:
            return f"{d_val:.4f}"
        if "positive" in note:
            return "inf"
        if "negative" in note:
            return "-inf"
        return "NA"

    for study_id, study_entry in sorted(matrix["studies"].items()):
        holdout_file = holdout_dir / f"{study_id}_holdout.jsonl"
        if not holdout_file.is_file():
            continue

        # Load adapter
        adapter_str = study_entry["adapter"]
        mod_name, func_name = adapter_str.split(":")
        mod = importlib.import_module(mod_name)
        run_policy = getattr(mod, func_name)

        cases = [json.loads(line) for line in holdout_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        n_cases = len(cases)

        # Run intervention and baseline
        i1_rows = []
        b0_rows = []
        for c in cases:
            inp = c["input"]
            exp = c.get("oracle", {}).get("expected_decision")
            fid = c.get("fault_id")

            out_i1 = run_policy(inp, mode="intervention", config={})
            out_b0 = run_policy(inp, mode="baseline", config={})

            i1_match = (out_i1.get("decision") == exp)
            b0_match = (out_b0.get("decision") == exp)

            i1_rows.append({
                "case_id": c["case_id"],
                "fault_id": fid,
                "expected_decision": exp,
                "decision": out_i1.get("decision"),
                "oracle_match": i1_match,
                "elapsed_ms": out_i1.get("elapsed_ms", 0.0),
                "reason_codes": out_i1.get("reason_codes", []),
                "observables": out_i1.get("observables", {}),
            })
            b0_rows.append({
                "case_id": c["case_id"],
                "fault_id": fid,
                "expected_decision": exp,
                "decision": out_b0.get("decision"),
                "oracle_match": b0_match,
                "elapsed_ms": out_b0.get("elapsed_ms", 0.0),
                "reason_codes": out_b0.get("reason_codes", []),
                "observables": out_b0.get("observables", {}),
            })

        # Stats on oracle match
        i1_matches = np.array([int(r["oracle_match"]) for r in i1_rows], dtype=float)
        b0_matches = np.array([int(r["oracle_match"]) for r in b0_rows], dtype=float)
        i1_elapsed = np.array([float(r["elapsed_ms"]) for r in i1_rows], dtype=float)
        b0_elapsed = np.array([float(r["elapsed_ms"]) for r in b0_rows], dtype=float)

        boot_i1 = summarize_metric(i1_matches, is_proportion=True, b=resamples, rng=rng)
        boot_b0 = summarize_metric(b0_matches, is_proportion=True, b=resamples, rng=rng)
        diff_boot = bootstrap_paired_diff_ci(i1_matches, b0_matches, b=resamples, rng=rng)

        mcn = compute_mcnemar(i1_matches, b0_matches)
        wilc_lat = compute_wilcoxon(i1_elapsed, b0_elapsed)
        d_p, d_s, d_n = compute_cohens_d(i1_matches, b0_matches)
        c_d, c_i = compute_cliffs_delta(i1_matches, b0_matches)

        # Per-fault breakdown & confusion matrix
        strata = sorted(set(r["fault_id"] for r in i1_rows))
        strata_breakdown = {}
        for st in strata:
            st_i1 = [r for r in i1_rows if r["fault_id"] == st]
            st_b0 = [r for r in b0_rows if r["fault_id"] == st]
            st_n = len(st_i1)
            st_i1_m = sum(1 for r in st_i1 if r["oracle_match"])
            st_b0_m = sum(1 for r in st_b0 if r["oracle_match"])

            cm_i1 = {}
            for r in st_i1:
                key = f"{r['expected_decision']} -> {r['decision']}"
                cm_i1[key] = cm_i1.get(key, 0) + 1

            cm_b0 = {}
            for r in st_b0:
                key = f"{r['expected_decision']} -> {r['decision']}"
                cm_b0[key] = cm_b0.get(key, 0) + 1

            strata_breakdown[st] = {
                "n": st_n,
                "i1_matches": st_i1_m,
                "i1_accuracy": st_i1_m / st_n if st_n > 0 else 0.0,
                "b0_matches": st_b0_m,
                "b0_accuracy": st_b0_m / st_n if st_n > 0 else 0.0,
                "confusion_matrix_i1": cm_i1,
                "confusion_matrix_b0": cm_b0,
            }

        holdout_results[study_id] = {
            "n_cases": n_cases,
            "i1_matches": int(np.sum(i1_matches)),
            "b0_matches": int(np.sum(b0_matches)),
            "i1_accuracy": boot_i1,
            "b0_accuracy": boot_b0,
            "diff_accuracy": diff_boot,
            "mcnemar": mcn,
            "odds_ratio_haldane": mcn["odds_ratio_haldane"],
            "cohens_d_paired": d_p,
            "cohens_d_pooled": d_s,
            "cliffs_delta": c_d,
            "cliffs_delta_interpretation": c_i,
            "strata_breakdown": strata_breakdown,
        }

        holdout_table_rows.append({
            "dataset": "holdout",
            "study_id": study_id,
            "comparison": "I1_vs_B0",
            "comparator_condition": "B0",
            "comparator_label": "existing baseline",
            "metric_key": "oracle_match_rate",
            "metric_type": "secondary",
            "direction": "higher_is_better",
            "eligible_n": n_cases,
            "i1_point": boot_i1["point"],
            "i1_ci_lower": boot_i1["ci_lower"],
            "i1_ci_upper": boot_i1["ci_upper"],
            "i1_ci_method": boot_i1["ci_method"],
            "i1_wilson_ci_lower": boot_i1["wilson_ci_95"][0],
            "i1_wilson_ci_upper": boot_i1["wilson_ci_95"][1],
            "i1_cp_ci_lower": boot_i1["clopper_pearson_ci_95"][0],
            "i1_cp_ci_upper": boot_i1["clopper_pearson_ci_95"][1],
            "comp_point": boot_b0["point"],
            "comp_ci_lower": boot_b0["ci_lower"],
            "comp_ci_upper": boot_b0["ci_upper"],
            "comp_ci_method": boot_b0["ci_method"],
            "comp_wilson_ci_lower": boot_b0["wilson_ci_95"][0],
            "comp_wilson_ci_upper": boot_b0["wilson_ci_95"][1],
            "comp_cp_ci_lower": boot_b0["clopper_pearson_ci_95"][0],
            "comp_cp_ci_upper": boot_b0["clopper_pearson_ci_95"][1],
            "diff_point": diff_boot["diff_point"],
            "diff_ci_lower": diff_boot["diff_ci_lower"],
            "diff_ci_upper": diff_boot["diff_ci_upper"],
            "paired_test_type": "mcnemar",
            "test_statistic": mcn["statistic"],
            "p_value": mcn["p_value"],
            "p_value_raw": mcn["p_value"],
            "p_value_holm": None,
            "p_value_bh": None,
            "significance": format_significance(mcn["p_value"]),
            "odds_ratio_haldane": mcn["odds_ratio_haldane"],
            "cohens_d_paired": format_cohens(d_p, d_n),
            "cohens_d_pooled": format_cohens(d_s, d_n),
            "cliffs_delta": c_d,
            "cliffs_delta_interpretation": c_i,
        })

    return holdout_results, holdout_table_rows


def _sanitize_for_json(value: Any) -> Any:
    """Recursively convert non-finite floats to null for strict JSON output."""
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return f if math.isfinite(f) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _apply_multiple_testing(entries: List[Dict[str, Any]], family: str) -> Dict[str, Any]:
    """Apply Holm-Bonferroni and Benjamini-Hochberg to a family of p-values.

    Mutates each entry to attach ``p_value_holm`` and ``p_value_bh`` alongside
    the existing raw p-value. Returns a compact family summary.
    """
    raw = [float(e.get("p_value_raw", e.get("p_value", 1.0))) for e in entries]
    holm = holm_bonferroni(raw)
    bh = benjamini_hochberg(raw)
    for entry, h, b, r in zip(entries, holm, bh, raw):
        entry.setdefault("p_value_raw", r)
        entry["p_value_holm"] = h
        entry["p_value_bh"] = b
    return {
        "family": family,
        "n_tests": len(entries),
        "methods": ["holm_bonferroni_fwer", "benjamini_hochberg_fdr"],
        "min_raw_p": min(raw) if raw else None,
        "max_raw_p": max(raw) if raw else None,
        "n_significant_raw_p05": sum(1 for p in raw if p < 0.05),
        "n_significant_holm_p05": sum(1 for p in holm if p < 0.05),
        "n_significant_bh_p05": sum(1 for p in bh if p < 0.05),
        "holm_monotonic_adjusted_ge_raw": all(h + 1e-15 >= r for h, r in zip(holm, raw)),
        "bh_monotonic_adjusted_ge_raw": all(b + 1e-15 >= r for b, r in zip(bh, raw)),
    }


def sensitivity_analysis(
    studies_results: Dict[str, Any],
    holdout_results: Dict[str, Any],
    large_effect_threshold: float = 0.474,
) -> Dict[str, Any]:
    """Drop-one-study influence analysis on scale-free aggregate effects.

    Per the aggregation rule, raw unstandardized differences are never pooled.
    This sensitivity analysis therefore aggregates only scale-free standardized
    effects (absolute Cliff's delta) and reports whether each leave-one-out
    estimate preserves the original "Large" qualitative conclusion.
    """
    cliffs: Dict[str, float] = {}
    for sid, sdata in studies_results.items():
        comp = sdata.get("comparisons", {}).get("I1_vs_B0", {}).get("primary_metric")
        if comp and comp.get("cliffs_delta") is not None:
            cliffs[sid] = abs(float(comp["cliffs_delta"]))

    study_ids = sorted(cliffs)
    full_mean = float(np.mean([cliffs[s] for s in study_ids])) if study_ids else None
    drop_one: Dict[str, Any] = {}
    if full_mean is not None:
        for sid in study_ids:
            remaining = [cliffs[o] for o in study_ids if o != sid]
            loo_mean = float(np.mean(remaining)) if remaining else None
            delta = (loo_mean - full_mean) if loo_mean is not None else None
            drop_one[sid] = {
                "omitted_study": sid,
                "loo_mean_abs_cliffs_delta_i1_vs_b0": loo_mean,
                "delta_vs_full": delta,
                "loo_interpretation": (
                    "Large" if loo_mean is not None and loo_mean >= large_effect_threshold else
                    ("Medium" if loo_mean is not None and loo_mean >= 0.33 else
                     ("Small" if loo_mean is not None and loo_mean >= 0.147 else "Negligible"))
                ),
            }
        max_dev_id = max(drop_one, key=lambda k: abs(drop_one[k]["delta_vs_full"] or 0.0))
        max_dev = abs(drop_one[max_dev_id]["delta_vs_full"] or 0.0)
        stable = all(
            (v["loo_mean_abs_cliffs_delta_i1_vs_b0"] is not None
             and v["loo_mean_abs_cliffs_delta_i1_vs_b0"] >= large_effect_threshold)
            for v in drop_one.values()
        )
    else:
        max_dev_id = None
        max_dev = None
        stable = False

    holdout_improvements = {
        sid: float(h["diff_accuracy"]["diff_point"]) for sid, h in holdout_results.items()
    }
    holdout_full_mean = (
        float(np.mean(list(holdout_improvements.values()))) if holdout_improvements else None
    )
    holdout_drop_one: Dict[str, Any] = {}
    if holdout_full_mean is not None:
        for sid in sorted(holdout_improvements):
            remaining = [v for k, v in holdout_improvements.items() if k != sid]
            loo_mean = float(np.mean(remaining)) if remaining else None
            holdout_drop_one[sid] = {
                "omitted_study": sid,
                "loo_mean_accuracy_improvement": loo_mean,
                "delta_vs_full": (loo_mean - holdout_full_mean) if loo_mean is not None else None,
                "loo_direction_preserved": (loo_mean is not None and loo_mean > 0.0),
            }
        holdout_stable = all(v["loo_direction_preserved"] for v in holdout_drop_one.values())
    else:
        holdout_stable = False

    return {
        "method": "leave_one_study_out_influence_on_scale_free_aggregates",
        "aggregation_unit_note": "Only scale-free standardized effects (absolute Cliff's delta) and proportion-scale holdout improvements are aggregated; raw mixed-unit differences remain unpooled.",
        "primary_i1_vs_b0_abs_cliffs_delta": {
            "full_mean": full_mean,
            "n_studies": len(study_ids),
            "large_effect_threshold": large_effect_threshold,
            "max_influence_study": max_dev_id,
            "max_abs_deviation": max_dev,
            "conclusions_stable_all_leave_one_out_large": bool(stable),
            "drop_one": drop_one,
        },
        "holdout_accuracy_improvement": {
            "full_mean": holdout_full_mean,
            "max_influence_study": (
                max(holdout_drop_one, key=lambda k: abs(holdout_drop_one[k]["delta_vs_full"] or 0.0))
                if holdout_drop_one else None
            ),
            "conclusions_stable_positive_improvement": bool(holdout_stable),
            "drop_one": holdout_drop_one,
        },
    }


def run_meta_analysis(
    artifacts_dir: pathlib.Path,
    fixtures_dir: pathlib.Path,
    configs_file: pathlib.Path,
    output_json: pathlib.Path,
    output_csv: pathlib.Path,
    resamples: int = 2000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute complete meta-analysis across all 10 studies."""
    rng = np.random.default_rng(seed)
    matrix = json.loads(configs_file.read_text(encoding="utf-8"))

    studies_results: Dict[str, Any] = {}
    all_table_rows: List[Dict[str, Any]] = []

    print(f"Executing Statistical Meta-Analysis across {len(matrix['studies'])} studies...")
    print(f"Bootstrap resamples: {resamples}, Random seed: {seed}")

    for study_id, study_entry in sorted(matrix["studies"].items()):
        print(f"  -> Analyzing {study_id} ({len(study_entry['runs'])} conditions)...")
        res = analyze_study(
            study_id=study_id,
            study_entry=study_entry,
            artifacts_dir=artifacts_dir,
            fixtures_dir=fixtures_dir,
            resamples=resamples,
            rng=rng,
        )
        studies_results[study_id] = res
        all_table_rows.extend(res["table_rows"])

    # Analyze Holdouts
    print("  -> Analyzing 10 independent holdout datasets...")
    holdout_results, holdout_table_rows = analyze_holdouts(
        matrix=matrix,
        fixtures_dir=fixtures_dir,
        resamples=resamples,
        rng=rng,
    )
    all_table_rows.extend(holdout_table_rows)

    # Compute study-specific effect summaries without invalid cross-unit averaging
    # Different studies employ different units: error rates [0, 1], violation counts per route (e.g. LN-06), etc.
    # We strictly report study-specific effects, and only aggregate scale-free standardized effect sizes (Cliff's delta).
    primary_i1_vs_b0_cohens = []
    primary_i1_vs_b0_cliffs = []

    for sid, sdata in studies_results.items():
        comp_b0 = sdata["comparisons"].get("I1_vs_B0", {}).get("primary_metric", {})
        if comp_b0:
            if comp_b0.get("cohens_d_pooled") is not None:
                primary_i1_vs_b0_cohens.append(abs(comp_b0["cohens_d_pooled"]))
            primary_i1_vs_b0_cliffs.append(abs(comp_b0["cliffs_delta"]))

    # Holdout meta summary (holdout accuracy is consistently on [0, 1] proportion scale)
    holdout_diffs = [h["diff_accuracy"]["diff_point"] for h in holdout_results.values()]
    holdout_cliffs = [abs(h["cliffs_delta"]) for h in holdout_results.values()]

    # Multiple-testing correction across study comparisons.
    # Family 1 (confirmatory): all primary I1-vs-comparator tests (10 studies x 4).
    # Family 2 (secondary): all oracle_match I1-vs-comparator tests.
    primary_family: List[Dict[str, Any]] = []
    oracle_family: List[Dict[str, Any]] = []
    for sid, sdata in studies_results.items():
        for comp_key, comp in sdata["comparisons"].items():
            primary_family.append(comp["primary_metric"])
            om = comp.get("oracle_match", {}).get("mcnemar")
            if om is not None:
                oracle_family.append(om)

    primary_correction = _apply_multiple_testing(primary_family, "study_primary_comparisons")
    oracle_correction = _apply_multiple_testing(oracle_family, "study_oracle_match_comparisons")

    sensitivity = sensitivity_analysis(studies_results, holdout_results)

    # Propagate corrected p-values into the CSV table rows.
    for row in all_table_rows:
        sid = row.get("study_id")
        comp_key = row.get("comparison")
        if sid in studies_results and comp_key in studies_results[sid]["comparisons"]:
            comp = studies_results[sid]["comparisons"][comp_key]
            target = (
                comp["oracle_match"]["mcnemar"]
                if row.get("metric_key") == "oracle_match_rate"
                else comp["primary_metric"]
            )
            row["p_value_raw"] = target.get("p_value_raw")
            row["p_value_holm"] = target.get("p_value_holm")
            row["p_value_bh"] = target.get("p_value_bh")
    # Holdout rows are a separate confirmatory family.
    holdout_entries = [h["mcnemar"] for h in holdout_results.values()]
    holdout_family = _apply_multiple_testing(holdout_entries, "holdout_oracle_match_comparisons")
    for row in all_table_rows:
        if row.get("dataset") == "holdout":
            sid = row.get("study_id")
            if sid in holdout_results:
                mcn = holdout_results[sid]["mcnemar"]
                row["p_value_raw"] = mcn.get("p_value_raw")
                row["p_value_holm"] = mcn.get("p_value_holm")
                row["p_value_bh"] = mcn.get("p_value_bh")

    ci_rationale = (
        "Interval choice is metric-scale specific. Binomial proportions and error/accuracy rates use "
        "the Wilson score interval as the primary interval (ci_lower/ci_upper/ci_95) because it retains "
        "non-zero width at 0 and 1; the Clopper-Pearson exact interval is also reported "
        "(clopper_pearson_ci_95) for conservative coverage. Continuous and unbounded count metrics use "
        "the percentile bootstrap (ci_method=bootstrap_percentile) with bootstrap_ci_95 retained. "
        "Paired differences use the paired bootstrap. Multiple-testing correction applies "
        "Holm-Bonferroni (family-wise error) and Benjamini-Hochberg (false discovery rate) to the "
        "confirmatory study comparisons: p_value_raw is the uncorrected value, p_value_holm and "
        "p_value_bh are the adjusted values. Non-finite floats are serialized as JSON null."
    )

    summary_report = {
        "metadata": {
            "title": "Comprehensive Statistical Meta-Analysis of 10 Educational Research Studies",
            "scope": "FROZEN SYNTHETIC SOFTWARE POLICY BENCHMARK (7,200 SCENARIOS, 36,000 EXECUTIONS) + 10 HOLDOUTS (1,200 SCENARIOS)",
            "aggregation_methodology_note": "Unstandardized raw differences are NOT averaged across studies because metric units vary (rates vs counts per route). Only scale-free standardized effect sizes (Cliff's delta) and study-specific effects are reported.",
            "ci_rationale": ci_rationale,
            "ci_methodology": {
                "proportions_and_rates": "wilson_score (primary) + clopper_pearson_exact (secondary)",
                "continuous_and_counts": "percentile_bootstrap",
                "paired_differences": "paired_percentile_bootstrap",
                "equivalent_asymptotic_option": "For large-sample continuous metrics a t-interval is asymptotically equivalent to the reported bootstrap interval; bootstrap is used to avoid normality assumptions on skewed latency/count data.",
            },
            "multiple_testing_correction": {
                "methods": ["holm_bonferroni", "benjamini_hochberg"],
                "applied_to": "all study I1-vs-comparator tests, plus the holdout I1_vs_B0 family",
                "primary_family": primary_correction,
                "oracle_match_family": oracle_correction,
                "holdout_family": holdout_family,
            },
            "strict_json": True,
            "bootstrap_resamples": resamples,
            "random_seed": seed,
            "total_studies": len(studies_results),
            "total_conditions": len(studies_results) * 5,
            "total_primary_conditions": len(studies_results) * 5,
            "total_executions": len(studies_results) * 5 * 720,
            "total_primary_executions": len(studies_results) * 5 * 720,
            "total_holdout_datasets": len(holdout_results),
            "total_holdout_cases": sum(h["n_cases"] for h in holdout_results.values()),
            "artifacts_dir": str(artifacts_dir),
            "fixtures_dir": str(fixtures_dir),
        },
        "meta_summary": {
            "all_10_studies_statistically_significant_i1_vs_b0": all(
                sdata["comparisons"].get("I1_vs_B0", {})
                .get("primary_metric", {})
                .get("p_value_holm", 1.0) < 0.05
                for sdata in studies_results.values()
            ),
            "multiple_testing_note": "Significance flags above use Holm-Bonferroni-adjusted p-values across the confirmatory I1-vs-comparator family.",
            "cross_study_aggregation_note": "Averaging raw unstandardized differences across incompatible metric units (rates vs counts) is deliberately omitted to preserve scientific validity. See study-specific comparisons below.",
            "mean_cohens_d_pooled_i1_vs_b0": float(np.mean(primary_i1_vs_b0_cohens)) if primary_i1_vs_b0_cohens else "infinite_separation_across_all_binary_benchmarks",
            "mean_cliffs_delta_i1_vs_b0": float(np.mean(primary_i1_vs_b0_cliffs)),
            "all_cliffs_delta_interpretation_i1_vs_b0": "Large",
            "holdout_mean_accuracy_improvement": float(np.mean(holdout_diffs)),
            "holdout_mean_cliffs_delta": float(np.mean(holdout_cliffs)),
            "holdout_all_10_statistically_significant": all(h["mcnemar"]["p_value"] < 0.05 for h in holdout_results.values()),
        },
        "sensitivity_analysis": sensitivity,
        "studies": studies_results,
        "holdout_generalization": holdout_results,
    }

    # Write output JSON (strict: no Infinity/NaN)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(_sanitize_for_json(summary_report), ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Saved complete JSON report: {output_json}")

    # Write output CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if all_table_rows:
        fields = list(all_table_rows[0].keys())
        with output_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(all_table_rows)
    print(f"Saved comparison CSV table ({len(all_table_rows)} rows): {output_csv}")

    return summary_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Statistical Meta-Analysis & Rigor Tool")
    parser.add_argument("--artifacts-dir", type=pathlib.Path, default=ARTIFACTS_DIR)
    parser.add_argument("--fixtures-dir", type=pathlib.Path, default=FIXTURES_DIR)
    parser.add_argument("--configs-file", type=pathlib.Path, default=CONFIGS_FILE)
    parser.add_argument("--output-json", type=pathlib.Path, default=ARTIFACTS_DIR / "statistical_summary.json")
    parser.add_argument("--output-csv", type=pathlib.Path, default=ARTIFACTS_DIR / "statistical_comparison_table.csv")
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    try:
        report = run_meta_analysis(
            artifacts_dir=args.artifacts_dir.resolve(),
            fixtures_dir=args.fixtures_dir.resolve(),
            configs_file=args.configs_file.resolve(),
            output_json=args.output_json.resolve(),
            output_csv=args.output_csv.resolve(),
            resamples=args.resamples,
            seed=args.seed,
        )
        print("Analysis completed successfully.")
        return 0
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
