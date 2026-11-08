#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluation runner for Study LN-08 Holdout Dataset.

Evaluates 6 conditions across 120 holdout cases:
- B0: Naive exact keyword matcher
- B1: Semantic cosine similarity embedding baseline (without negation parser)
- I1: LN-08 Taxonomic diagnostic reasoner (negation + source grounding + synonym equivalence)
- A1: Ablation 1 (Keyword-only)
- A2: Ablation 2 (Disable negation check)
- A3: Ablation 3 (Disable source linkage check)

Computes:
- Diagnostic Error Rate (overall and per-fault breakdown)
- False Positive Negation Rate
- 95% Wilson Confidence Intervals
- Paired McNemar's tests (with continuity correction and exact p-values)
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import sys
from typing import Any

# Add project root to sys.path
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.feedback.diagnostic_feedback import (
    evaluate_ablation,
    evaluate_baseline,
    evaluate_intervention,
    normalize_text,
)

HOLDOUT_FILE = ROOT / "research" / "fixtures" / "holdout" / "LN-08_holdout.jsonl"
OUTPUT_DIR = ROOT / "research_artifacts" / "LN-08" / "holdout_evaluation"


# --------------------------------------------------------------------------- #
# B1: Semantic Cosine Similarity Baseline (Embedding / Bag-of-Words TF-IDF)
# --------------------------------------------------------------------------- #

def get_word_ngrams(text: str, n: int = 2) -> list[str]:
    words = text.lower().split()
    grams = list(words)
    for i in range(len(words) - n + 1):
        grams.append(" ".join(words[i:i+n]))
    return grams

def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in vec_a)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def text_to_vector(text: str) -> dict[str, float]:
    tokens = get_word_ngrams(normalize_text(text))
    counts = collections.Counter(tokens)
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}

CANONICAL_TARGET = (
    "công trình nằm trên trục nghi lễ hoặc không gian nghi thức tế tự của hoàng thành Huế theo quy chuẩn sử liệu"
)
TARGET_VEC = text_to_vector(CANONICAL_TARGET)

def evaluate_b1_embedding_baseline(scenario_input: dict[str, Any]) -> dict[str, Any]:
    """B1: Stronger baseline using cosine similarity embeddings without negation parser.
    
    Lacks:
    - Negation parser (treats negated claims as highly similar to reference)
    - Source provenance validator (ignores invalid/fabricated source metadata)
    """
    answer = scenario_input.get("answer", "")
    ans_vec = text_to_vector(answer)
    sim = cosine_similarity(ans_vec, TARGET_VEC)
    
    # Thresholding: >= 0.18 indicates semantic alignment with ritual axis / spatial function
    # Correctly identifies synonyms due to vector proximity, but fails on negation & source
    if sim >= 0.18:
        # If it has synonym phrasing characteristics, predict preserve_semantics; else feedback_supported
        lower = answer.lower()
        has_syn = any(p in lower for p in [
            "tuyến không gian phục vụ nghi thức",
            "tuyến không gian nghi thức",
            "không gian phục vụ nghi thức",
            "trục nghi thức",
            "trục trung tâm nghi thức",
        ])
        if has_syn:
            decision = "preserve_semantics"
            category = "supported_equivalent"
        else:
            decision = "feedback_supported"
            category = "supported"
        reason = f"B1 embedding cosine similarity {sim:.3f} >= threshold"
    else:
        decision = "feedback_incomplete"
        category = "incomplete"
        reason = f"B1 low similarity {sim:.3f} < threshold"
        
    return {
        "decision": decision,
        "diagnostic_category": category,
        "policy_version": "baseline-v1-embedding-cosine",
        "similarity_score": sim,
        "reason_codes": [reason],
        "observables": {
            "diagnostic_category": category,
            "similarity_score": sim,
            "negation_checked": False,
            "source_checked": False,
        }
    }


# --------------------------------------------------------------------------- #
# Statistical Utilities: Wilson Score CI & McNemar's Test
# --------------------------------------------------------------------------- #

def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # for 95% confidence
    p = k / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)

def mcnemar_test(errors_a: list[int], errors_b: list[int]) -> dict[str, Any]:
    """Compute McNemar's test with continuity correction between two paired classifiers.
    
    errors_a, errors_b are binary lists where 1 = error, 0 = correct.
    Contingency table:
      b = a made error, b correct (errors_a == 1 and errors_b == 0)
      c = a correct, b made error (errors_a == 0 and errors_b == 1)
    """
    assert len(errors_a) == len(errors_b), "Paired lists must have equal length"
    b = sum(1 for ea, eb in zip(errors_a, errors_b) if ea == 1 and eb == 0)
    c = sum(1 for ea, eb in zip(errors_a, errors_b) if ea == 0 and eb == 1)
    
    total_discordant = b + c
    if total_discordant == 0:
        return {"chi2": 0.0, "p_value": 1.0, "b": b, "c": c}
        
    # Edwards continuity correction
    chi2 = (abs(b - c) - 1.0)**2 / total_discordant
    
    # Exact binomial p-value for small or large discordant pairs:
    # Under H0, b ~ Binomial(n=b+c, p=0.5)
    try:
        from scipy import stats
        p_val = float(stats.binomtest(b, n=total_discordant, p=0.5).pvalue)
    except (ImportError, AttributeError):
        # Binomial sum fallback for two-sided p-value
        k_min = min(b, c)
        p_val = float(min(1.0, 2.0 * sum(math.comb(total_discordant, i) * (0.5**total_discordant) for i in range(k_min + 1))))
        
    return {
        "chi2": chi2,
        "p_value": p_val,
        "b": b,
        "c": c,
        "discordant": total_discordant,
    }


# --------------------------------------------------------------------------- #
# Main Holdout Evaluation Routine
# --------------------------------------------------------------------------- #

def run_evaluation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load holdout dataset
    cases = []
    with HOLDOUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
                
    n_total = len(cases)
    print(f"Loaded {n_total} holdout cases.")
    
    conditions = ["B0", "B1", "I1", "A1", "A2", "A3"]
    results = {c: [] for c in conditions}
    
    # Run all conditions
    for case in cases:
        inp = case["input"]
        
        # B0: Naive keyword baseline
        res_b0 = evaluate_baseline(inp)
        results["B0"].append(res_b0)
        
        # B1: Semantic cosine embedding baseline
        res_b1 = evaluate_b1_embedding_baseline(inp)
        results["B1"].append(res_b1)
        
        # I1: Full LN-08 Intervention
        res_i1 = evaluate_intervention(inp)
        results["I1"].append(res_i1)
        
        # A1: Ablation keyword-only
        res_a1 = evaluate_ablation(inp, {"ablation": "keyword_only"})
        results["A1"].append(res_a1)
        
        # A2: Ablation disable negation
        res_a2 = evaluate_ablation(inp, {"ablation": "disable_negation"})
        results["A2"].append(res_a2)
        
        # A3: Ablation disable source link
        res_a3 = evaluate_ablation(inp, {"ablation": "disable_source_link"})
        results["A3"].append(res_a3)
        
    # Analyze errors
    # Error definition: decision does not match expected_decision
    error_vectors = {}
    summary_metrics = {}
    
    fault_types = [
        "nominal_correct",
        "logical_negation_misconception",
        "synonym_variation",
        "partial_reasoning",
        "unverified_historical_assertion",
    ]
    
    for cond in conditions:
        outputs = results[cond]
        err_vec = []
        fp_neg_vec = []  # False positive negation vector
        
        fault_errs = collections.defaultdict(lambda: {"total": 0, "errors": 0})
        
        for case, out in zip(cases, outputs):
            f_id = case["fault_id"]
            oracle_dec = case["oracle"]["expected_decision"]
            pred_dec = out["decision"]
            
            # An error occurs if pred_dec does not match oracle_dec
            is_err = int(pred_dec != oracle_dec)
            err_vec.append(is_err)
            
            fault_errs[f_id]["total"] += 1
            if is_err:
                fault_errs[f_id]["errors"] += 1
                
            # False positive negation check:
            # When fault is logical_negation_misconception, if policy grants supported -> false positive!
            if f_id == "logical_negation_misconception":
                is_fp_neg = int(pred_dec in ("feedback_supported", "preserve_semantics"))
                fp_neg_vec.append(is_fp_neg)
                
        error_vectors[cond] = err_vec
        
        total_errors = sum(err_vec)
        # Eligible non-nominal errors
        non_nominal_indices = [i for i, c in enumerate(cases) if c["fault_id"] != "nominal_correct"]
        non_nom_total = len(non_nominal_indices)
        non_nom_errors = sum(err_vec[i] for i in non_nominal_indices)
        
        err_rate_all = total_errors / n_total
        ci_all_low, ci_all_high = wilson_ci(total_errors, n_total)
        
        err_rate_eligible = non_nom_errors / non_nom_total
        ci_elig_low, ci_elig_high = wilson_ci(non_nom_errors, non_nom_total)
        
        fp_neg_count = sum(fp_neg_vec)
        fp_neg_total = len(fp_neg_vec)
        fp_neg_rate = fp_neg_count / fp_neg_total
        ci_neg_low, ci_neg_high = wilson_ci(fp_neg_count, fp_neg_total)
        
        summary_metrics[cond] = {
            "condition": cond,
            "total_cases": n_total,
            "total_errors": total_errors,
            "overall_error_rate": err_rate_all,
            "overall_ci_95": [ci_all_low, ci_all_high],
            "eligible_fault_cases": non_nom_total,
            "eligible_fault_errors": non_nom_errors,
            "eligible_error_rate": err_rate_eligible,
            "eligible_ci_95": [ci_elig_low, ci_elig_high],
            "false_positive_negation_count": fp_neg_count,
            "false_positive_negation_total": fp_neg_total,
            "false_positive_negation_rate": fp_neg_rate,
            "fp_negation_ci_95": [ci_neg_low, ci_neg_high],
            "fault_breakdown": {
                f: {
                    "total": fault_errs[f]["total"],
                    "errors": fault_errs[f]["errors"],
                    "error_rate": fault_errs[f]["errors"] / fault_errs[f]["total"] if fault_errs[f]["total"] else 0.0,
                }
                for f in fault_types
            }
        }
        
    # Paired McNemar tests: I1 vs all other conditions
    paired_tests = {}
    for other in ["B0", "B1", "A1", "A2", "A3"]:
        test_res = mcnemar_test(error_vectors[other], error_vectors["I1"])
        paired_tests[f"I1_vs_{other}"] = test_res
        
    output_payload = {
        "holdout_n": n_total,
        "summary_metrics": summary_metrics,
        "paired_tests": paired_tests,
    }
    
    # Save output JSON
    res_path = OUTPUT_DIR / "holdout_results.json"
    res_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Holdout results saved to {res_path}")
    
    # Print formatted summary table
    print("\n" + "=" * 95)
    print(f"{'Cond':<6} | {'Err (All)':<10} | {'Err (Eligible)':<14} | {'95% CI (Eligible)':<22} | {'FP Neg Rate':<12} | {'McNemar p vs I1':<15}")
    print("-" * 95)
    for cond in conditions:
        m = summary_metrics[cond]
        p_val_str = f"{paired_tests[f'I1_vs_{cond}']['p_value']:.2e}" if cond != "I1" else "ref (0.0)"
        ci_str = f"[{m['eligible_ci_95'][0]*100:.1f}%, {m['eligible_ci_95'][1]*100:.1f}%]"
        print(f"{cond:<6} | {m['overall_error_rate']*100:>5.1f}%     | {m['eligible_error_rate']*100:>5.1f}% ({m['eligible_fault_errors']}/{m['eligible_fault_cases']})  | {ci_str:<22} | {m['false_positive_negation_rate']*100:>5.1f}%       | {p_val_str:<15}")
    print("=" * 95 + "\n")
    
    # Fault breakdown table
    print("Fault Breakdown Errors (Errors / Total N=24 per fault):")
    print(f"{'Condition':<10} | {'Nominal':<10} | {'Negation':<10} | {'Synonym':<10} | {'Partial':<10} | {'Unverified':<12}")
    print("-" * 75)
    for cond in conditions:
        fb = summary_metrics[cond]["fault_breakdown"]
        print(f"{cond:<10} | {fb['nominal_correct']['errors']:>2}/24       | {fb['logical_negation_misconception']['errors']:>2}/24       | {fb['synonym_variation']['errors']:>2}/24       | {fb['partial_reasoning']['errors']:>2}/24       | {fb['unverified_historical_assertion']['errors']:>2}/24")
    print("-" * 75)
    
    return output_payload

if __name__ == "__main__":
    run_evaluation()
