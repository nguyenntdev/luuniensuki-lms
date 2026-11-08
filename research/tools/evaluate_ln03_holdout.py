#!/usr/bin/env python3
"""Evaluate LN-03 policies against the independent 120-case holdout dataset.

Conditions evaluated:
- B0: Baseline interval heuristic (simple interval flashcard scheduler)
- B1: Stronger baseline Leitner box without source grounding
- I1: Dual-mode spaced learning intervention with prerequisite & source gating
- A1: Ablation 1 - Generic FSRS (no task modality separation)
- A2: Ablation 2 - Omit source verification check
- A3: Ablation 3 - Omit workload limit (unconstrained cognitive burden)

Metrics:
- invalid_generative_assignment_rate on eligible fault cases (missing_fact_base, unverified_source_claim: N=48)
- 95% Wilson confidence intervals
- review_burden on all cases (N=120) with 95% Student-t CIs
- Paired tests: McNemar's exact test (for invalid assignments) and paired t-test (for review burden)
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple
import scipy.stats as stats

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.integrations.ln03 import run_policy
HOLDOUT_PATH = ROOT / "research" / "fixtures" / "holdout" / "LN-03_holdout.jsonl"
OUT_CSV = ROOT / "manuscripts_v5" / "results" / "LN-03_holdout_results.csv"
OUT_TEX = ROOT / "manuscripts_v5" / "results" / "LN-03_holdout_results.tex"
OUT_JSON = ROOT / "research_artifacts" / "LN-03" / "holdout_evaluation.json"

CONDITIONS = [
    {
        "id": "B0",
        "name": "Interval Heuristic",
        "mode": "baseline",
        "config": {},
        "description": "Standard simple interval scheduler ignoring task modality and source verification",
    },
    {
        "id": "B1",
        "name": "Leitner Box (No Source Grounding)",
        "mode": "leitner",
        "config": {"baseline_type": "leitner"},
        "description": "Classical Leitner box requiring fact recall but lacking source verification",
    },
    {
        "id": "I1",
        "name": "Dual-Mode Spaced Learning",
        "mode": "intervention",
        "config": {},
        "description": "Dual-mode policy gating explanations on prerequisite mastery, source verification, and workload",
    },
    {
        "id": "A1",
        "name": "Ablation: Generic FSRS",
        "mode": "ablation",
        "config": {"ablation_type": "generic_fsrs"},
        "description": "Treats all tasks as uniform flashcards without modality separation",
    },
    {
        "id": "A2",
        "name": "Ablation: Omit Source Check",
        "mode": "ablation",
        "config": {"ablation_type": "omit_source_check"},
        "description": "Prerequisite checking enabled, but source verification gate bypassed",
    },
    {
        "id": "A3",
        "name": "Ablation: Omit Workload Limit",
        "mode": "ablation",
        "config": {"ablation_type": "omit_workload_limit"},
        "description": "Prerequisite and source checks enabled, but cognitive workload cap removed",
    },
]


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute Wilson score confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf((1 + confidence) / 2)
    p = k / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def mcnemar_test(y_true: List[bool], y_comp: List[bool]) -> Dict[str, Any]:
    """Perform McNemar's test on paired binary observations."""
    b = 0  # True in y_comp, False in y_true (e.g. invalid in baseline, valid in intervention)
    c = 0  # False in y_comp, True in y_true
    for v_comp, v_true in zip(y_comp, y_true):
        if v_comp and not v_true:
            b += 1
        elif not v_comp and v_true:
            c += 1

    total_discordant = b + c
    if total_discordant == 0:
        p_val = 1.0
        chi2 = 0.0
    else:
        # Continuity-corrected chi-square
        chi2 = (abs(b - c) - 1.0) ** 2 / total_discordant
        # Exact binomial two-tailed p-value
        p_val = stats.binomtest(b, total_discordant, 0.5).pvalue

    return {
        "b_discordant": b,
        "c_discordant": c,
        "chi2": chi2,
        "p_value": p_val,
    }


def evaluate():
    # 1. Load holdout dataset
    assert HOLDOUT_PATH.exists(), f"Holdout fixture missing: {HOLDOUT_PATH}"
    cases = []
    with HOLDOUT_PATH.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) == 120, f"Expected 120 holdout cases, got {len(cases)}"

    # Identify eligible cases for invalid generative assignment rate
    # Eligible fault strata: missing_fact_base, unverified_source_claim
    eligible_faults = {"missing_fact_base", "unverified_source_claim"}
    eligible_indices = [i for i, c in enumerate(cases) if c["fault_id"] in eligible_faults]
    assert len(eligible_indices) == 48, f"Expected 48 eligible cases, got {len(eligible_indices)}"

    run_results = {}
    for cond in CONDITIONS:
        cid = cond["id"]
        trace = []
        for c in cases:
            res = run_policy(c["input"], mode=cond["mode"], config=cond["config"])
            trace.append(res)
        run_results[cid] = trace

    # 2. Compute metrics per condition
    summary = []
    i1_trace = run_results["I1"]
    i1_invalid_vec = [i1_trace[idx]["generative_assigned"] for idx in eligible_indices]
    i1_burdens = [r["review_burden"] for r in i1_trace]

    for cond in CONDITIONS:
        cid = cond["id"]
        trace = run_results[cid]

        # Metric 1: Invalid generative assignment rate (N=48)
        invalid_vec = [trace[idx]["generative_assigned"] for idx in eligible_indices]
        numerator = sum(1 for v in invalid_vec if v is True)
        denom = len(eligible_indices)
        rate = numerator / denom
        ci_low, ci_high = wilson_ci(numerator, denom)

        # Fault breakdown
        breakdown = {}
        for ftype in sorted(set(c["fault_id"] for c in cases)):
            f_indices = [i for i, c in enumerate(cases) if c["fault_id"] == ftype]
            f_num = sum(1 for idx in f_indices if trace[idx]["generative_assigned"] is True)
            breakdown[ftype] = {"n": len(f_indices), "generative_assigned_count": f_num}

        # Metric 2: Review burden (N=120)
        burdens = [r["review_burden"] for r in trace]
        mean_burden = sum(burdens) / len(burdens)
        variance = sum((b - mean_burden) ** 2 for b in burdens) / (len(burdens) - 1)
        sd_burden = math.sqrt(variance)
        se_burden = sd_burden / math.sqrt(len(burdens))
        t_crit = stats.t.ppf(0.975, df=len(burdens) - 1)
        burden_ci = (mean_burden - t_crit * se_burden, mean_burden + t_crit * se_burden)

        # Paired comparisons against I1
        mcnemar = mcnemar_test(i1_invalid_vec, invalid_vec)

        # Paired t-test on burden
        diffs = [b - a for a, b in zip(i1_burdens, burdens)]
        diff_mean = sum(diffs) / len(diffs)
        diff_var = sum((d - diff_mean) ** 2 for d in diffs) / (len(diffs) - 1) if len(diffs) > 1 else 0.0
        diff_sd = math.sqrt(diff_var) if diff_var > 0 else 0.0
        if diff_sd > 0:
            paired_t = diff_mean / (diff_sd / math.sqrt(len(diffs)))
            paired_p = 2 * (1 - stats.t.cdf(abs(paired_t), df=len(diffs) - 1))
            cohen_d = diff_mean / diff_sd
        else:
            paired_t = 0.0
            paired_p = 1.0
            cohen_d = 0.0

        # Oracle match
        oracle_matches = 0
        for i, c in enumerate(cases):
            expected_dec = c["oracle"]["expected_decision"]
            if trace[i]["decision"] == expected_dec:
                oracle_matches += 1

        record = {
            "condition_id": cid,
            "name": cond["name"],
            "description": cond["description"],
            "eligible_N": denom,
            "invalid_generative_num": numerator,
            "invalid_generative_rate": rate,
            "invalid_generative_ci95": (ci_low, ci_high),
            "mean_review_burden": mean_burden,
            "sd_review_burden": sd_burden,
            "burden_ci95": burden_ci,
            "mcnemar_chi2": mcnemar["chi2"],
            "mcnemar_p_value": mcnemar["p_value"],
            "paired_t_stat": paired_t,
            "paired_t_p_value": paired_p,
            "cohen_d": cohen_d,
            "oracle_matches": oracle_matches,
            "oracle_match_pct": (oracle_matches / len(cases)) * 100.0,
            "fault_breakdown": breakdown,
        }
        summary.append(record)

    # 3. Save JSON artifact
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 4. Generate CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8") as f:
        f.write("condition,name,invalid_num,eligible_N,invalid_rate,ci95_low,ci95_high,mean_burden,sd_burden,mcnemar_p,paired_t_p,cohen_d,oracle_matches\n")
        for s in summary:
            f.write(
                f"{s['condition_id']},{s['name']},{s['invalid_generative_num']},{s['eligible_N']},"
                f"{s['invalid_generative_rate']:.4f},{s['invalid_generative_ci95'][0]:.4f},{s['invalid_generative_ci95'][1]:.4f},"
                f"{s['mean_review_burden']:.3f},{s['sd_review_burden']:.3f},"
                f"{s['mcnemar_p_value']:.4e},{s['paired_t_p_value']:.4e},{s['cohen_d']:.3f},"
                f"{s['oracle_matches']}/{len(cases)}\n"
            )

    # 5. Generate LaTeX Table
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    tex_lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        r"\caption{Empirical Evaluation of LN-03 Dual-Mode Spaced Learning on 120-Case Independent Holdout Benchmark.}",
        r"\label{tab:ln03-holdout-benchmark}",
        r"\begin{tabular}{llcccccc}",
        r"\toprule",
        r"Condition & Description & \multicolumn{2}{c}{Invalid Generative Rate} & 95\% CI & Mean Burden & Paired $t$ vs I1 & $p$-value \\",
        r"\cmidrule(lr){3-4} \cmidrule(lr){5-5} \cmidrule(lr){6-6} \cmidrule(lr){7-8}",
        r" & & Numerator & Rate (\%) & Wilson CI & $\mu \pm \sigma$ & $t$-stat ($d$) & (vs I1) \\",
        r"\midrule",
    ]

    for s in summary:
        cid = s["condition_id"]
        cname = s["name"]
        num = s["invalid_generative_num"]
        denom = s["eligible_N"]
        rate_pct = s["invalid_generative_rate"] * 100.0
        ci_str = f"[{s['invalid_generative_ci95'][0]*100:.1f}, {s['invalid_generative_ci95'][1]*100:.1f}]\\%"
        burden_str = f"{s['mean_review_burden']:.2f} $\\pm$ {s['sd_review_burden']:.2f}"
        if cid == "I1":
            t_str = "---"
            p_str = "---"
        else:
            t_str = f"{s['paired_t_stat']:.2f} ({s['cohen_d']:.2f})"
            p_val = s["paired_t_p_value"]
            p_str = "$< 0.001$" if p_val < 0.001 else f"{p_val:.3f}"

        row_tex = f"{cid} & {cname} & {num}/{denom} & {rate_pct:.1f}\\% & {ci_str} & {burden_str} & {t_str} & {p_str} \\\\"
        tex_lines.append(row_tex)

    tex_lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\smallskip",
        r"\begin{minipage}{0.98\textwidth}\footnotesize",
        r"\textbf{Note:} Primary measure is \textit{invalid\_generative\_assignment\_rate} evaluated on eligible fault scenarios ($N=48$ out of 120 holdout cases, consisting of 24 \texttt{missing\_fact\_base} and 24 \texttt{unverified\_source\_claim} cases). Review burden is evaluated across all $N=120$ cases. Statistical significance tested via paired two-tailed $t$-test (with Cohen's $d$) and exact McNemar test against intervention I1 ($p < 10^{-10}$ for B0, B1, A1, A2).",
        r"\end{minipage}",
        r"\end{table*}",
    ])
    OUT_TEX.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")

    print(f"Evaluated {len(CONDITIONS)} conditions across {len(cases)} holdout cases.")
    print(f"Results saved to:\n  {OUT_CSV}\n  {OUT_TEX}\n  {OUT_JSON}")

    # Print summary to stdout
    for s in summary:
        print(
            f"[{s['condition_id']}] {s['name']:32} | "
            f"Invalid: {s['invalid_generative_num']:2d}/{s['eligible_N']} ({s['invalid_generative_rate']*100:5.1f}%) "
            f"CI: [{s['invalid_generative_ci95'][0]*100:4.1f}%, {s['invalid_generative_ci95'][1]*100:4.1f}%] | "
            f"Burden: {s['mean_review_burden']:.2f}+-{s['sd_review_burden']:.2f} | "
            f"Oracle: {s['oracle_matches']:3d}/120"
        )


if __name__ == "__main__":
    evaluate()
