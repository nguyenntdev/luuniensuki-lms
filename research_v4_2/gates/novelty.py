"""Gate 3: Novelty and Prior Art Validator (novelty.py).

Checks literature contrast against at least 3 nearest works, nearest-work overlap matrices,
formal counterexample/mechanism, N1-N7 criteria, and independent human expert signoff.
Rejects automatic machine-only novelty declarations (Absent review => BLOCKED).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from research_v4_2.contracts.types import GateResult


def validate_novelty(
    novelty_card_data: Dict[str, Any],
    failure_card_data: Optional[Dict[str, Any]] = None,
) -> GateResult:
    """Validate that novelty criteria, literature matrix, and human signoffs are satisfied."""
    messages = []
    details = {}

    # 1. Literature contrast: At least 3 closest works
    closest_works = novelty_card_data.get("closest_works", [])
    details["num_closest_works"] = len(closest_works)
    if len(closest_works) < 3:
        messages.append(
            f"INSUFFICIENT_PRIOR_ART: NoveltyCard lists {len(closest_works)} closest works. "
            "Minimum 3 verified closest works with citations/DOIs required."
        )
    else:
        for idx, work in enumerate(closest_works):
            if not work.get("title") or not (work.get("citation_or_doi") or work.get("doi") or work.get("citation")):
                messages.append(
                    f"INVALID_PRIOR_ART_ENTRY: Closest work #{idx+1} missing title or citation/DOI."
                )

    # 2. Direct overlaps analysis
    overlaps = novelty_card_data.get("direct_overlaps", [])
    details["num_direct_overlaps"] = len(overlaps)
    if not overlaps or len(overlaps) == 0:
        messages.append(
            "MISSING_DIRECT_OVERLAPS: NoveltyCard must explicitly articulate and analyze direct overlaps with prior art."
        )

    # 3. Formal counterexample or distinct mechanism
    counterexample = novelty_card_data.get("formal_counterexample")
    details["has_formal_counterexample"] = bool(counterexample)
    if not counterexample or not str(counterexample).strip():
        messages.append(
            "MISSING_FORMAL_COUNTEREXAMPLE: NoveltyCard must provide a formal counterexample or distinct mechanism."
        )

    # 4. Screening criteria N1 through N7
    n1_n7 = novelty_card_data.get("n1_to_n7_criteria", {})
    details["n1_n7_criteria"] = n1_n7
    expected_criteria = [f"N{i}" for i in range(1, 8)]
    missing_crit = [c for c in expected_criteria if c not in n1_n7]
    if missing_crit:
        messages.append(
            f"INCOMPLETE_N1_N7_EVALUATION: Missing screening criteria: {missing_crit}."
        )

    # 5. Independent human sign-off (CRITICAL INVARIANT: NEVER AUTO-PASSED)
    signoff = novelty_card_data.get("independent_human_signoff")
    details["has_human_signoff"] = bool(signoff)
    if not signoff:
        messages.append(
            "HUMAN_SIGNOFF_BLOCKED: Novelty card lacks independent human review sign-off. "
            "Automated system cannot self-certify novelty. Status is BLOCKED."
        )
    else:
        if not signoff.get("signed", False):
            messages.append(
                "HUMAN_SIGNOFF_NOT_SIGNED: Human signoff present but 'signed' is False. Status is BLOCKED."
            )
        if not signoff.get("reviewer") or not str(signoff.get("reviewer")).strip():
            messages.append("HUMAN_SIGNOFF_ANONYMOUS: Human reviewer name/identifier cannot be empty.")
        if not signoff.get("date") or not str(signoff.get("date")).strip():
            messages.append("HUMAN_SIGNOFF_UNDATED: Human signoff date cannot be empty.")

    # 6. Failure card alignment (if provided)
    if failure_card_data:
        fail_causes = failure_card_data.get("diagnosed_root_causes", [])
        if fail_causes:
            details["verified_failure_alignment"] = True

    passed = len(messages) == 0
    if passed:
        messages.append("Novelty gate passed: 3+ closest works, counterexample, N1-N7, and human signoff verified.")

    return GateResult(
        gate_name="novelty",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate novelty, nearest-work matrix, and human signoff.")
    parser.add_argument("--novelty-card", type=str, required=True, help="Path to NoveltyCard JSON.")
    parser.add_argument("--failure-card", type=str, default=None, help="Optional path to FailureCard JSON.")

    args = parser.parse_args()

    try:
        with open(args.novelty_card, "r", encoding="utf-8") as f:
            novelty_data = json.load(f)
        failure_data = None
        if args.failure_card:
            with open(args.failure_card, "r", encoding="utf-8") as f:
                failure_data = json.load(f)
    except Exception as e:
        print(f"[NOVELTY] File load error: {e}")
        sys.exit(1)

    result = validate_novelty(novelty_data, failure_data)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
