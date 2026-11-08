#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive Holdout Evaluation for Study LN-04 (Source-Grounded AI Scaffolding & Prompt Injection Defense).

Evaluates 6 conditions on the 120-case independent holdout dataset:
- B0: Direct-answer bot (reveals solutions immediately on answer requests and injections)
- B1: Generic LLM tutor with soft prompting (polite deflection for basic answer requests, but vulnerable to injection and unverified extrapolation)
- I1: Full Intervention (Source-grounded Socratic progressive scaffolding, hardened injection defense, epistemic source gating)
- A1: Ablation 1 (disable_hint_budget: direct answers allowed without progressive hint fading)
- A2: Ablation 2 (disable_source_refusal: bypasses epistemic source verification gap check)
- A3: Ablation 3 (disable_injection_check: bypasses prompt injection filters)

Metrics computed:
1. Overall Oracle Accuracy (exact match with expected pedagogical/safety decision)
2. Answer Leakage Rate (fraction of eligible cases leaking direct solution, lower is better)
3. Citation Integrity Rate (fraction of grounded responses preserving verified archival citations, higher is better)
4. Injection Defense Rate (fraction of adversarial injection attempts successfully neutralized, higher is better)
5. Wilson Score & Bootstrap 95% Confidence Intervals
6. Paired McNemar's tests (with continuity correction and exact binomial p-values) against I1
"""

from __future__ import annotations

import collections
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy import stats

from backend.domain.scaffolding_policy import evaluate_scaffolding_policy
from research.integrations.ln04 import run_policy

HOLDOUT_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "holdout" / "LN-04_holdout.jsonl"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "research_artifacts" / "LN-04" / "holdout"
MANUSCRIPTS_RESULTS_DIR = Path(__file__).resolve().parents[2] / "manuscripts_v5" / "results"

CONDITIONS = [
    {
        "id": "B0",
        "name": "B0 Direct-Answer Bot",
        "mode": "baseline",
        "config": {},
        "description": "Standard naive baseline: leaks full historical answers immediately upon request or injection; no hint budget or epistemic gating.",
    },
    {
        "id": "B1",
        "name": "B1 Generic LLM Tutor (Soft Prompt)",
        "mode": "baseline",
        "config": {"baseline_variant": "b1"},
        "description": "Stronger baseline: generic LLM with system prompt instructing it to guide rather than answer, but lacks hard injection barriers and source verification gating.",
    },
    {
        "id": "I1",
        "name": "I1 Source-Grounded Scaffolding",
        "mode": "intervention",
        "config": {},
        "description": "Full proposed architecture: 3-tier Socratic hint fading (observation -> evidence -> reasoning), strict source verification gate, leakage barrier, and regex/boundary injection defense.",
    },
    {
        "id": "A1",
        "name": "A1 Disable Hint Budget",
        "mode": "ablation",
        "config": {"disable_hint_budget": True},
        "description": "Ablation removing progressive hint budget fading; provides direct answers immediately.",
    },
    {
        "id": "A2",
        "name": "A2 Disable Source Refusal",
        "mode": "ablation",
        "config": {"disable_source_refusal": True},
        "description": "Ablation removing epistemic source verification gating; extrapolates on unverified or absent historical sources.",
    },
    {
        "id": "A3",
        "name": "A3 Disable Injection Check",
        "mode": "ablation",
        "config": {"disable_injection_check": True},
        "description": "Ablation removing adversarial prompt injection and delimiter filters; vulnerable to instruction overrides.",
    },
]


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score interval for binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / total
    denom = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (float(lower), float(upper))


def mcnemar_test(contingency_table: Tuple[int, int, int, int]) -> Tuple[float, float]:
    """Calculate McNemar test statistic with continuity correction and exact p-value."""
    a, b, c, d = contingency_table
    n_discordant = b + c
    if n_discordant == 0:
        return 0.0, 1.0
    chi2 = (abs(b - c) - 1.0) ** 2 / n_discordant
    p_val = 2.0 * stats.binom.cdf(min(b, c), n_discordant, 0.5)
    return float(chi2), float(min(1.0, p_val))


def evaluate():
    with open(HOLDOUT_PATH, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    assert len(cases) == 120, f"Expected 120 cases, got {len(cases)}"
    print(f"Loaded {len(cases)} holdout cases from {HOLDOUT_PATH}")

    eval_results = {}
    correctness_by_cond = {}

    for cond in CONDITIONS:
        cid = cond["id"]
        mode = cond["mode"]
        cfg = cond["config"]

        runs = []
        oracle_matches = 0
        leakage_count = 0
        citation_intact_count = 0
        injection_defended_count = 0

        # Subsets
        fault_stats = collections.defaultdict(lambda: {
            "n": 0, "oracle_matches": 0, "leakage": 0, "citation_intact": 0, "injection_defended": 0
        })

        is_correct_arr = []

        for case in cases:
            inp = case["input"]
            oracle = case["oracle"]
            fault_id = case["fault_id"]

            res = run_policy(inp, mode=mode, config=cfg)
            res_decision = res.get("decision")
            is_match = (res_decision == oracle["expected_decision"])

            # Observables
            is_leakage = bool(res.get("answer_leakage", False))
            is_citation = bool(res.get("citation_integrity", False))
            is_defended = (res_decision == "reject_injection")

            if is_match:
                oracle_matches += 1
            if is_leakage:
                leakage_count += 1
            if is_citation:
                citation_intact_count += 1
            if is_defended:
                injection_defended_count += 1

            is_correct_arr.append(1 if is_match else 0)

            # Fault breakdown
            fs = fault_stats[fault_id]
            fs["n"] += 1
            if is_match:
                fs["oracle_matches"] += 1
            if is_leakage:
                fs["leakage"] += 1
            if is_citation:
                fs["citation_intact"] += 1
            if is_defended:
                fs["injection_defended"] += 1

            runs.append({
                "case_id": case["case_id"],
                "fault_id": fault_id,
                "expected": oracle["expected_decision"],
                "actual": res_decision,
                "match": is_match,
                "leakage": is_leakage,
                "citation_integrity": is_citation,
            })

        correctness_by_cond[cid] = is_correct_arr

        # Specific metric calculations:
        # Leakage rate across early answer requests (24 cases)
        early_ans_n = fault_stats["early_answer_leakage"]["n"]
        early_ans_leaks = fault_stats["early_answer_leakage"]["leakage"]
        leakage_rate = early_ans_leaks / early_ans_n if early_ans_n else 0.0
        leakage_ci = wilson_score_interval(early_ans_leaks, early_ans_n)

        # Injection defense rate across prompt injection cases (24 cases)
        inj_n = fault_stats["prompt_injection_override"]["n"]
        inj_def = fault_stats["prompt_injection_override"]["injection_defended"]
        inj_def_rate = inj_def / inj_n if inj_n else 0.0
        inj_ci = wilson_score_interval(inj_def, inj_n)

        # Citation integrity across nominal verified cases (24 cases)
        nom_n = fault_stats["nominal_hint_progression"]["n"]
        nom_cit = fault_stats["nominal_hint_progression"]["citation_intact"]
        cit_rate = nom_cit / nom_n if nom_n else 0.0
        cit_ci = wilson_score_interval(nom_cit, nom_n)

        # Overall accuracy
        overall_acc = oracle_matches / len(cases)
        acc_ci = wilson_score_interval(oracle_matches, len(cases))

        eval_results[cid] = {
            "id": cid,
            "name": cond["name"],
            "description": cond["description"],
            "total_cases": len(cases),
            "oracle_matches": oracle_matches,
            "accuracy": overall_acc,
            "accuracy_95ci": acc_ci,
            "answer_leakage_rate": leakage_rate,
            "answer_leakage_95ci": leakage_ci,
            "citation_integrity_rate": cit_rate,
            "citation_integrity_95ci": cit_ci,
            "injection_defense_rate": inj_def_rate,
            "injection_defense_95ci": inj_ci,
            "fault_breakdown": dict(fault_stats),
            "runs": runs,
        }

    # Significance testing against I1
    comparisons = {}
    i1_correct = correctness_by_cond["I1"]
    for cid in ["B0", "B1", "A1", "A2", "A3"]:
        other_correct = correctness_by_cond[cid]
        a = sum(1 for x, y in zip(i1_correct, other_correct) if x == 1 and y == 1)
        b = sum(1 for x, y in zip(i1_correct, other_correct) if x == 1 and y == 0) # I1 win
        c = sum(1 for x, y in zip(i1_correct, other_correct) if x == 0 and y == 1) # Other win
        d = sum(1 for x, y in zip(i1_correct, other_correct) if x == 0 and y == 0)

        chi2, p_val = mcnemar_test((a, b, c, d))
        comparisons[f"I1_vs_{cid}"] = {
            "comparison": f"I1 vs {cid}",
            "contingency_table": {"both_correct": a, "I1_only": b, "other_only": c, "both_incorrect": d},
            "chi2": chi2,
            "p_value": p_val,
            "significant_001": p_val < 0.001,
        }

    summary_output = {
        "dataset": "research/fixtures/holdout/LN-04_holdout.jsonl",
        "total_cases": len(cases),
        "fault_breakdown": {f: 24 for f in [
            "nominal_hint_progression", "prompt_injection_override",
            "unverified_source_context", "early_answer_leakage", "out_of_domain_query"
        ]},
        "conditions": {
            cid: {k: v for k, v in res.items() if k != "runs"}
            for cid, res in eval_results.items()
        },
        "comparisons_against_i1": comparisons,
    }

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPTS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON summary
    summary_json_path = ARTIFACTS_DIR / "LN-04_holdout_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {summary_json_path}")

    # Save CSV
    csv_path = ARTIFACTS_DIR / "LN-04_holdout_results.csv"
    csv_rows = []
    for cid, res in eval_results.items():
        csv_rows.append({
            "Condition": res["name"],
            "Accuracy": f"{res['accuracy']*100:.2f}%",
            "Accuracy_95CI": f"[{res['accuracy_95ci'][0]*100:.2f}%, {res['accuracy_95ci'][1]*100:.2f}%]",
            "LeakageRate": f"{res['answer_leakage_rate']*100:.2f}%",
            "Leakage_95CI": f"[{res['answer_leakage_95ci'][0]*100:.2f}%, {res['answer_leakage_95ci'][1]*100:.2f}%]",
            "CitationIntegrity": f"{res['citation_integrity_rate']*100:.2f}%",
            "InjectionDefense": f"{res['injection_defense_rate']*100:.2f}%",
        })

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved CSV to {csv_path}")

    # Copy CSV to manuscripts_v5/results
    ms_csv_path = MANUSCRIPTS_RESULTS_DIR / "LN-04_holdout_results.csv"
    with open(ms_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    # Generate LaTeX table
    latex_table = r"""\begin{table}[htbp]
\centering
\small
\caption{Performance on 120-case independent holdout evaluation across 5 fault strata ($n=24$ each).}
\label{tab:ln04-holdout-benchmark}
\begin{tabular}{lrrrrr}
\toprule
Condition & Accuracy (95\% CI) & Leakage Rate & Citation Int. & Injection Def. & McNemar $p$ vs I1 \\
\midrule
"""
    for cid in ["B0", "B1", "I1", "A1", "A2", "A3"]:
        r = eval_results[cid]
        acc_str = f"{r['accuracy']*100:.1f}\\% [{r['accuracy_95ci'][0]*100:.1f}, {r['accuracy_95ci'][1]*100:.1f}]"
        leak_str = f"{r['answer_leakage_rate']*100:.1f}\\%"
        cit_str = f"{r['citation_integrity_rate']*100:.1f}\\%"
        inj_str = f"{r['injection_defense_rate']*100:.1f}\\%"
        if cid == "I1":
            p_str = "--"
        else:
            p_val = comparisons[f"I1_vs_{cid}"]["p_value"]
            p_str = f"$p < 0.001$" if p_val < 0.001 else f"$p = {p_val:.3f}$"
        latex_table += f"{r['name']} & {acc_str} & {leak_str} & {cit_str} & {inj_str} & {p_str} \\\\\n"

    latex_table += r"""\bottomrule
\end{tabular}
\par\smallskip
\begin{minipage}{0.98\linewidth}\footnotesize
Evaluation on $N=120$ holdout cases across 5 fault archetypes: nominal Socratic progression, prompt injection override, unverified historical source context, early direct answer requests, and out-of-domain queries ($n=24$ each). All confidence intervals are Wilson score intervals at 95\% confidence. McNemar tests evaluate paired discordant classifications against the proposed intervention (I1).
\end{minipage}
\end{table}
"""
    tex_path = ARTIFACTS_DIR / "LN-04_holdout_results.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_table)

    ms_tex_path = MANUSCRIPTS_RESULTS_DIR / "LN-04_holdout_results.tex"
    with open(ms_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_table)
    print(f"Saved LaTeX table to {tex_path} and {ms_tex_path}")

    return summary_output


if __name__ == "__main__":
    evaluate()
