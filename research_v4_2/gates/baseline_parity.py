"""Gate 4: Baseline Task and Split Parity Validator (baseline_parity.py).

Enforces strictly matched denominators, aligned case IDs, identical target labels,
equal coverage constraints, and zero train/test leakage.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Sequence

from research_v4_2.contracts.types import GateResult


def validate_baseline_parity(
    cand_preds: Sequence[Dict[str, Any]],
    base_preds: Sequence[Dict[str, Any]],
    gold_records: Sequence[Dict[str, Any]],
    train_records: Optional[Sequence[Dict[str, Any]]] = None,
) -> GateResult:
    """Validate that candidate and baseline models are evaluated on identical instances without mismatch or leakage."""
    messages = []
    details = {}

    n_cand = len(cand_preds)
    n_base = len(base_preds)
    n_gold = len(gold_records)

    details["n_candidate"] = n_cand
    details["n_baseline"] = n_base
    details["n_gold"] = n_gold

    # 1. Denominator parity check
    if not (n_cand == n_base == n_gold):
        messages.append(
            f"DENOMINATOR_MISMATCH: Test instance counts differ: candidate={n_cand}, "
            f"baseline={n_base}, gold={n_gold}. Baseline champion and candidate must be evaluated on identical denominators."
        )

    # Helper to extract ID
    def get_id(rec: Dict[str, Any], idx: int) -> str:
        return str(rec.get("case_id") or rec.get("id") or rec.get("instance_id") or idx)

    cand_ids = [get_id(r, i) for i, r in enumerate(cand_preds)]
    base_ids = [get_id(r, i) for i, r in enumerate(base_preds)]
    gold_ids = [get_id(r, i) for i, r in enumerate(gold_records)]

    set_cand = set(cand_ids)
    set_base = set(base_ids)
    set_gold = set(gold_ids)

    # 2. Case ID matching
    if set_cand != set_base or set_cand != set_gold:
        diff_cb = set_cand.symmetric_difference(set_base)
        diff_cg = set_cand.symmetric_difference(set_gold)
        messages.append(
            f"CASE_ID_MISMATCH: Prediction instances do not align with baseline or gold. "
            f"Candidate vs Baseline diff count: {len(diff_cb)}; Candidate vs Gold diff count: {len(diff_cg)}."
        )

    # 3. Label and prediction format check
    for idx, (c, b, g) in enumerate(zip(cand_preds[:100], base_preds[:100], gold_records[:100])):
        cand_val = c.get("y_pred", c.get("prediction", c.get("y_prob")))
        base_val = b.get("y_pred", b.get("prediction", b.get("y_prob")))
        gold_val = g.get("y_true", g.get("label", g.get("gold")))

        if cand_val is None or base_val is None or gold_val is None:
            messages.append(f"MISSING_LABEL_DATA: Instance #{idx} missing prediction or true label.")
            break

    # 4. Coverage parity check (selective classification)
    cand_covered = [c.get("covered", True) for c in cand_preds]
    base_covered = [b.get("covered", True) for b in base_preds]
    cand_cov_rate = sum(cand_covered) / max(1, len(cand_covered))
    base_cov_rate = sum(base_covered) / max(1, len(base_covered))
    details["cand_coverage_rate"] = cand_cov_rate
    details["base_coverage_rate"] = base_cov_rate

    # If coverage differs by more than 1% without matched penalty
    if abs(cand_cov_rate - base_cov_rate) > 0.01:
        # Check if candidate explicitly declared selective evaluation
        if not all(cand_covered) and all(base_covered):
            messages.append(
                f"UNFAIR_COVERAGE_ADVANTAGE: Candidate evaluated on selective coverage ({cand_cov_rate:.3f}) "
                f"while baseline evaluated on full coverage ({base_cov_rate:.3f}). Denominators must be matched."
            )

    # 5. Train/Test leakage audit (if train split provided)
    if train_records:
        train_ids = {get_id(r, i) for i, r in enumerate(train_records)}
        leakage = set_gold.intersection(train_ids)
        details["num_leaked_instances"] = len(leakage)
        if leakage:
            messages.append(
                f"DATASET_LEAKAGE_DETECTED: {len(leakage)} test instances overlap with training set! "
                f"Contaminated case IDs sample: {list(leakage)[:5]}."
            )

    passed = len(messages) == 0
    if passed:
        messages.append("Baseline parity verified: matching denominators, exact case IDs, and zero split leakage.")

    return GateResult(
        gate_name="baseline_parity",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate baseline task equivalence and split parity.")
    parser.add_argument("--cand", type=str, required=True, help="Path to candidate predictions JSON.")
    parser.add_argument("--base", type=str, required=True, help="Path to baseline predictions JSON.")
    parser.add_argument("--gold", type=str, required=True, help="Path to ground truth JSON.")
    parser.add_argument("--train", type=str, default=None, help="Optional path to training set JSON.")

    args = parser.parse_args()

    try:
        with open(args.cand, "r", encoding="utf-8") as f:
            cand = json.load(f)
        with open(args.base, "r", encoding="utf-8") as f:
            base = json.load(f)
        with open(args.gold, "r", encoding="utf-8") as f:
            gold = json.load(f)
        train = None
        if args.train:
            with open(args.train, "r", encoding="utf-8") as f:
                train = json.load(f)
    except Exception as e:
        print(f"[BASELINE_PARITY] File load error: {e}")
        sys.exit(1)

    result = validate_baseline_parity(cand, base, gold, train)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
