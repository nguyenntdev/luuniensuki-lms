#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export holdout benchmark results to CSV and publication-ready LaTeX tables."""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "research_artifacts" / "LN-08" / "holdout_evaluation" / "holdout_results.json"
data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
metrics = data["summary_metrics"]
paired = data["paired_tests"]

cond_labels = {
    "B0": "Exact keyword matcher",
    "B1": "Embedding cosine similarity (no negation parser)",
    "I1": "LN-08 taxonomic diagnostic reasoner",
    "A1": "Ablation: keyword-only",
    "A2": "Ablation: disable negation parser",
    "A3": "Ablation: disable source linkage validator",
}

# CSV Export
csv_lines = [
    "condition,label,total_n,eligible_n,errors_all,error_rate_all,errors_eligible,error_rate_eligible,ci_95_low,ci_95_high,fp_neg_rate,mcnemar_p_vs_i1"
]

for cond, m in metrics.items():
    p_val = paired[f"I1_vs_{cond}"]["p_value"] if cond != "I1" else 0.0
    csv_lines.append(
        f"{cond},{cond_labels[cond]},{m['total_cases']},{m['eligible_fault_cases']},{m['total_errors']},{m['overall_error_rate']:.4f},{m['eligible_fault_errors']},{m['eligible_error_rate']:.4f},{m['eligible_ci_95'][0]:.4f},{m['eligible_ci_95'][1]:.4f},{m['false_positive_negation_rate']:.4f},{p_val:.2e}"
    )

csv_content = "\n".join(csv_lines) + "\n"
(ROOT / "research_artifacts" / "LN-08" / "holdout_evaluation" / "holdout_results.csv").write_text(csv_content, encoding="utf-8")
(ROOT / "manuscripts_v5" / "results" / "LN-08_holdout_results.csv").write_text(csv_content, encoding="utf-8")

# LaTeX Table Export: Overall Benchmark
tex_lines = [
    r"\begin{table*}[t]",
    r"\centering",
    r"\small",
    r"\caption{Empirical evaluation on independent holdout dataset ($N=120$, 24 cases per fault stratum) comparing diagnostic reasoning architectures against the ground-truth historical oracle.}",
    r"\label{tab:ln08-holdout-benchmark}",
    r"\begin{tabular}{llrrrrrc}",
    r"\toprule",
    r"Condition & Architecture & Errors (All) & Overall Err & Errors (Elig.) & Diagnostic Err (95\% CI) & FP Neg. Rate & McNemar $p$ vs.\ I1 \\",
    r"\midrule",
]

for cond, m in metrics.items():
    p_str = f"{paired[f'I1_vs_{cond}']['p_value']:.2e}" if cond != "I1" else r"\textit{ref}"
    ci_str = f"[{m['eligible_ci_95'][0]*100:.1f}\\%, {m['eligible_ci_95'][1]*100:.1f}\\%]"
    tex_lines.append(
        f"{cond} & {cond_labels[cond]} & {m['total_errors']}/120 & {m['overall_error_rate']*100:.1f}\\% & {m['eligible_fault_errors']}/96 & {m['eligible_error_rate']*100:.1f}\\% {ci_str} & {m['false_positive_negation_rate']*100:.1f}\\% & {p_str} \\\\"
    )

tex_lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\par\smallskip",
    r"\begin{minipage}{0.98\linewidth}\footnotesize",
    r"\textbf{Notes}: $N=120$ independent holdout cases partitioned across five balanced strata (24 cases each): \textit{nominal\_correct}, \textit{logical\_negation\_misconception}, \textit{synonym\_variation}, \textit{partial\_reasoning}, and \textit{unverified\_historical\_assertion}. Eligible fault denominator ($N=96$) excludes nominal cases. Confidence intervals denote Wilson 95\% score intervals. Paired differences against intervention I1 are computed via two-sided McNemar's test with continuity correction.",
    r"\end{minipage}",
    r"\end{table*}",
]

tex_content = "\n".join(tex_lines) + "\n"
(ROOT / "research_artifacts" / "LN-08" / "holdout_evaluation" / "holdout_results.tex").write_text(tex_content, encoding="utf-8")
(ROOT / "manuscripts_v5" / "results" / "LN-08_holdout_results.tex").write_text(tex_content, encoding="utf-8")

# LaTeX Table Export: Granular Fault Breakdown
fb_lines = [
    r"\begin{table*}[t]",
    r"\centering",
    r"\small",
    r"\caption{Granular fault breakdown error counts across reasoning archetypes ($n=24$ cases per column).}",
    r"\label{tab:ln08-fault-breakdown}",
    r"\begin{tabular}{lccccc}",
    r"\toprule",
    r"Condition & Nominal Correct & Logical Negation & Synonym Variation & Partial Reasoning & Unverified Assertion \\",
    r" & ($n=24$) & ($n=24$) & ($n=24$) & ($n=24$) & ($n=24$) \\",
    r"\midrule",
]

fault_cols = [
    "nominal_correct",
    "logical_negation_misconception",
    "synonym_variation",
    "partial_reasoning",
    "unverified_historical_assertion",
]

for cond, m in metrics.items():
    fb = m["fault_breakdown"]
    errs = [f"{fb[fc]['errors']}/24" for fc in fault_cols]
    fb_lines.append(f"{cond} ({cond_labels[cond].split('(')[0].strip()}) & " + " & ".join(errs) + r" \\")

fb_lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\par\smallskip",
    r"\begin{minipage}{0.98\linewidth}\footnotesize",
    r"\textbf{Summary}: Naive keyword matcher (B0) fails completely on negation (false positive), synonym variation (false negative), and unverified sources (false positive). Embedding baseline (B1) resolves synonyms via semantic vector proximity but retains high vulnerability to negation and citation fabrication. Component ablations confirm that negation parsing (A2) and source validation (A3) are individually necessary and collectively sufficient (I1) to eliminate diagnostic errors.",
    r"\end{minipage}",
    r"\end{table*}",
]

fb_content = "\n".join(fb_lines) + "\n"
(ROOT / "research_artifacts" / "LN-08" / "holdout_evaluation" / "holdout_breakdown.tex").write_text(fb_content, encoding="utf-8")
(ROOT / "manuscripts_v5" / "results" / "LN-08_holdout_breakdown.tex").write_text(fb_content, encoding="utf-8")

print("Successfully exported all tables!")
