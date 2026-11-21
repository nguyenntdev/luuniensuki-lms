"""Gate 5: Statistical Claims and Recomputation Validator (statistical_claims.py).

Recomputes performance metrics directly from raw predictions and ground truth,
calculates cluster-resampled bootstrap confidence intervals, enforces multiplicity
corrections (Holm-Bonferroni), and verifies sample size and power constraints.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence

from research_v4_2.contracts.types import GateResult
from research_v4_2.eval.metrics import (
    accuracy,
    roc_auc,
    nll,
    f1_score,
    mae,
    rmse,
    percentile_latency,
    geometric_mean,
)
from research_v4_2.eval.statistics import (
    paired_cluster_bootstrap_delta,
    paired_permutation_test,
    holm_bonferroni,
    power_feasibility_check,
)


def _get_metric_evaluator(metric_name: str) -> tuple[Callable[[Sequence[Dict[str, Any]]], float], bool]:
    """Return metric function over records, and a boolean indicating if larger is better."""
    name = metric_name.lower().replace("-", "_").strip()

    if "acc" in name:
        return lambda recs: accuracy([r["y_true"] for r in recs], [r["y_pred"] for r in recs]), True
    elif "auc" in name:
        return lambda recs: roc_auc([r["y_true"] for r in recs], [r.get("y_prob", r.get("y_pred")) for r in recs]), True
    elif "f1" in name:
        return lambda recs: f1_score([r["y_true"] for r in recs], [r["y_pred"] for r in recs]), True
    elif "nll" in name or "cross_entropy" in name:
        return lambda recs: nll([r["y_true"] for r in recs], [r.get("y_prob", r.get("y_pred")) for r in recs]), False
    elif "mae" in name:
        return lambda recs: mae([r["y_true"] for r in recs], [r["y_pred"] for r in recs]), False
    elif "rmse" in name:
        return lambda recs: rmse([r["y_true"] for r in recs], [r["y_pred"] for r in recs]), False
    elif "latency" in name:
        return lambda recs: percentile_latency([r.get("latency_ms", r.get("y_pred")) for r in recs], 95.0), False
    elif "geomean" in name:
        return lambda recs: geometric_mean([r.get("runtime_ms", r.get("y_pred")) for r in recs]), False
    else:
        # Default fallback to accuracy
        return lambda recs: accuracy([r["y_true"] for r in recs], [r["y_pred"] for r in recs]), True


def validate_statistical_claims(
    win_card_data: Dict[str, Any],
    cand_preds: Sequence[Dict[str, Any]],
    base_preds: Sequence[Dict[str, Any]],
    gold_records: Sequence[Dict[str, Any]],
    cluster_key: str = "cluster_id",
    all_hypotheses_p_raw: Optional[List[float]] = None,
    tolerance: float = 0.01,
) -> GateResult:
    """Validate and recompute statistical superiority claims from raw predictions."""
    messages = []
    details = {}

    n_samples = len(gold_records)
    metric_name = win_card_data.get("primary_metric", "accuracy")
    delta_min = float(win_card_data.get("delta_min", 0.01))
    reported_effect = float(win_card_data.get("effect", 0.0))
    reported_ci = win_card_data.get("ci95", [0.0, 0.0])
    reported_p_adj = float(win_card_data.get("p_adjusted", 1.0))

    # Build aligned records
    merged_cand = []
    merged_base = []
    cluster_set = set()

    for idx, (c, b, g) in enumerate(zip(cand_preds, base_preds, gold_records)):
        cid = g.get(cluster_key) or c.get(cluster_key) or b.get(cluster_key) or f"c_{idx // 10}"
        cluster_set.add(cid)

        yt = g.get("y_true", g.get("label", g.get("gold", 0)))
        cp = c.get("y_pred", c.get("prediction", 0))
        cprob = c.get("y_prob", cp)
        bp = b.get("y_pred", b.get("prediction", 0))
        bprob = b.get("y_prob", bp)

        merged_cand.append({
            "case_id": g.get("case_id", idx),
            cluster_key: cid,
            "y_true": yt,
            "y_pred": cp,
            "y_prob": cprob,
            "latency_ms": c.get("latency_ms", cp),
            "runtime_ms": c.get("runtime_ms", cp),
        })
        merged_base.append({
            "case_id": g.get("case_id", idx),
            cluster_key: cid,
            "y_true": yt,
            "y_pred": bp,
            "y_prob": bprob,
            "latency_ms": b.get("latency_ms", bp),
            "runtime_ms": b.get("runtime_ms", bp),
        })

    n_clusters = len(cluster_set)
    details["n_samples"] = n_samples
    details["n_clusters"] = n_clusters

    # 1. Power & sample size feasibility check
    pwr_check = power_feasibility_check(n_samples=n_samples, n_clusters=n_clusters, delta_min=delta_min)
    if not pwr_check["adequate"]:
        for issue in pwr_check["issues"]:
            messages.append(f"UNDERPOWERED_CLAIM: {issue}")

    # 2. Metric evaluation & delta orientation
    eval_fn, larger_is_better = _get_metric_evaluator(metric_name)
    m_cand = eval_fn(merged_cand)
    m_base = eval_fn(merged_base)

    if larger_is_better:
        recomputed_delta = m_cand - m_base
    else:
        # For loss/latency, improvement is lower
        recomputed_delta = m_base - m_cand

    details["recomputed_m_cand"] = m_cand
    details["recomputed_m_base"] = m_base
    details["recomputed_delta"] = recomputed_delta
    details["reported_effect"] = reported_effect

    # Check match with reported effect in WinCard
    if abs(recomputed_delta - reported_effect) > tolerance:
        messages.append(
            f"EFFECT_MISMATCH: WinCard reports effect={reported_effect:.4f}, but recomputation from raw "
            f"predictions yielded {recomputed_delta:.4f} (tolerance={tolerance})."
        )

    # 3. Meaningful minimum delta constraint (delta >= delta_min)
    if recomputed_delta < delta_min:
        messages.append(
            f"DELTA_BELOW_MINIMUM: Recomputed delta ({recomputed_delta:.4f}) is lower than the "
            f"preregistered minimum meaningful difference delta_min ({delta_min:.4f}). Claim is null."
        )

    # 4. Cluster-resampled bootstrap CI (95%)
    # Form record pair for bootstrap
    paired_records = []
    for c_rec, b_rec in zip(merged_cand, merged_base):
        paired_records.append({
            cluster_key: c_rec[cluster_key],
            "cand": c_rec,
            "base": b_rec,
        })

    def cand_wrap(sub_recs):
        return eval_fn([r["cand"] for r in sub_recs])

    def base_wrap(sub_recs):
        return eval_fn([r["base"] for r in sub_recs])

    if larger_is_better:
        _, ci_lower, ci_upper = paired_cluster_bootstrap_delta(
            records=paired_records,
            cluster_key=cluster_key,
            cand_metric_fn=cand_wrap,
            base_metric_fn=base_wrap,
            n_bootstraps=500,
            seed=42,
        )
    else:
        _, ci_lower, ci_upper = paired_cluster_bootstrap_delta(
            records=paired_records,
            cluster_key=cluster_key,
            cand_metric_fn=base_wrap,
            base_metric_fn=cand_wrap,
            n_bootstraps=500,
            seed=42,
        )

    details["recomputed_ci95"] = [ci_lower, ci_upper]
    details["reported_ci95"] = reported_ci

    # Superiority requirement: CI lower bound must be > 0
    if ci_lower <= 0.0:
        messages.append(
            f"CONFIDENCE_INTERVAL_SPANS_ZERO: Recomputed 95% cluster CI [{ci_lower:.4f}, {ci_upper:.4f}] "
            f"lower bound is <= 0. Difference is not statistically distinguishable from zero."
        )

    # 5. Significance test & Holm multiplicity adjustment
    # Difference per instance
    if larger_is_better:
        diffs = [
            (1.0 if c["y_pred"] == c["y_true"] else 0.0) - (1.0 if b["y_pred"] == b["y_true"] else 0.0)
            for c, b in zip(merged_cand, merged_base)
        ]
    else:
        diffs = [b["latency_ms"] - c["latency_ms"] for c, b in zip(merged_cand, merged_base)]

    p_raw = paired_permutation_test(diffs, n_permutations=1000, seed=42)
    details["recomputed_p_raw"] = p_raw

    # Multiplicity correction
    if all_hypotheses_p_raw:
        hypotheses = list(all_hypotheses_p_raw)
        if p_raw not in hypotheses:
            hypotheses.append(p_raw)
        adj_p_list = holm_bonferroni(hypotheses)
        p_adj = adj_p_list[hypotheses.index(p_raw)]
    else:
        # Single hypothesis or pre-adjusted
        p_adj = p_raw

    details["recomputed_p_adjusted"] = p_adj

    if p_adj >= 0.05:
        messages.append(
            f"MULTIPLICITY_REJECTION: Adjusted p-value ({p_adj:.4f}) does not pass alpha=0.05 threshold."
        )

    passed = len(messages) == 0
    if passed:
        messages.append(
            f"Statistical claims verified: delta={recomputed_delta:.4f} >= {delta_min}, "
            f"CI=[{ci_lower:.4f}, {ci_upper:.4f}] > 0, p_adj={p_adj:.4f} < 0.05."
        )

    return GateResult(
        gate_name="statistical_claims",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Recompute and validate statistical superiority claims.")
    parser.add_argument("--win-card", type=str, required=True, help="Path to WinCard JSON.")
    parser.add_argument("--cand", type=str, required=True, help="Path to candidate predictions JSON.")
    parser.add_argument("--base", type=str, required=True, help="Path to baseline predictions JSON.")
    parser.add_argument("--gold", type=str, required=True, help="Path to ground truth JSON.")
    parser.add_argument("--cluster-key", type=str, default="cluster_id", help="Cluster key name.")

    args = parser.parse_args()

    try:
        with open(args.win_card, "r", encoding="utf-8") as f:
            win_card = json.load(f)
        with open(args.cand, "r", encoding="utf-8") as f:
            cand = json.load(f)
        with open(args.base, "r", encoding="utf-8") as f:
            base = json.load(f)
        with open(args.gold, "r", encoding="utf-8") as f:
            gold = json.load(f)
    except Exception as e:
        print(f"[STATISTICAL_CLAIMS] File load error: {e}")
        sys.exit(1)

    result = validate_statistical_claims(win_card, cand, base, gold, cluster_key=args.cluster_key)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
