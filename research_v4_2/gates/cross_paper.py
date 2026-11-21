"""Gate 8: Cross-Paper Independence and Collision Validator (cross_paper.py).

Compares primary outcomes, estimands, and contributions across research papers (P01-P14).
Prevents duplicate estimands and enforces distinct scopes between known overlapping papers
(specifically P07/P14 multimedia vs accessibility, and P09/P12 evidence grounding vs archival ledger).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from research_v4_2.contracts.types import GateResult


def validate_cross_paper_independence(
    win_cards_data: List[Dict[str, Any]],
) -> GateResult:
    """Validate that all submitted papers have distinct, independent research contributions and estimands."""
    messages = []
    details = {"num_papers_analyzed": len(win_cards_data)}

    seen_claims: Dict[str, str] = {}
    seen_estimands: Dict[str, str] = {}
    papers_by_id: Dict[str, Dict[str, Any]] = {}

    for idx, card in enumerate(win_cards_data):
        paper_id = str(card.get("paper_id", f"P{idx}")).upper()
        claim_id = str(card.get("claim_id", f"claim_{idx}"))
        estimand = str(card.get("estimand", "")).strip().lower()
        primary_metric = str(card.get("primary_metric", "")).strip().lower()

        papers_by_id[paper_id] = card

        # 1. Unique claim IDs
        if claim_id in seen_claims:
            messages.append(
                f"DUPLICATE_CLAIM_ID: Claim ID '{claim_id}' used by both {seen_claims[claim_id]} and {paper_id}."
            )
        else:
            seen_claims[claim_id] = paper_id

        # 2. Duplicate estimand collision check
        key = f"{estimand}___{primary_metric}"
        if estimand and key in seen_estimands:
            messages.append(
                f"DUPLICATE_ESTIMAND_COLLISION: Papers {seen_estimands[key]} and {paper_id} share "
                f"identical estimand and primary metric: '{estimand}' ({primary_metric}). "
                "Each paper must address an independent research question."
            )
        else:
            seen_estimands[key] = paper_id

    # 3. Known overlap check: P07 (multimedia selection) vs P14 (accessibility)
    if "P07" in papers_by_id and "P14" in papers_by_id:
        p07_card = papers_by_id["P07"]
        p14_card = papers_by_id["P14"]
        p07_estimand = str(p07_card.get("estimand", "")).lower()
        p14_estimand = str(p14_card.get("estimand", "")).lower()

        # Both must not claim generic accessibility or generic retrieval
        if p07_estimand == p14_estimand or ("accessibility" in p07_estimand and "accessibility" in p14_estimand):
            messages.append(
                "P07_P14_COLLISION: P07 (rights-aware multimedia selection) and P14 (heritage accessibility) "
                "have overlapping scopes or identical estimands. P07 must focus on rights-constrained retrieval/knapsack, "
                "while P14 must focus on semantic accessibility and UDL."
            )

    # 4. Known overlap check: P09 (evidence grounding) vs P12 (archival ledger)
    if "P09" in papers_by_id and "P12" in papers_by_id:
        p09_card = papers_by_id["P09"]
        p12_card = papers_by_id["P12"]
        p09_estimand = str(p09_card.get("estimand", "")).lower()
        p12_estimand = str(p12_card.get("estimand", "")).lower()

        if p09_estimand == p12_estimand:
            messages.append(
                "P09_P12_COLLISION: P09 (evidence-grounded heritage exploration) and P12 (archival claim ledger) "
                "share identical primary estimand. P12 must either focus on locator-level verification / tamper audit, "
                "or be merged into P09 technical appendix."
            )

    passed = len(messages) == 0
    if passed:
        messages.append("Cross-paper independence verified: unique estimands, no duplicate claims or unmerged overlaps.")

    return GateResult(
        gate_name="cross_paper",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate cross-paper independence and detect duplicate estimands.")
    parser.add_argument("--win-cards", nargs="+", required=True, help="Paths to WinCard JSON files for all papers.")

    args = parser.parse_args()

    cards_data = []
    for path in args.win_cards:
        try:
            with open(path, "r", encoding="utf-8") as f:
                cards_data.append(json.load(f))
        except Exception as e:
            print(f"[CROSS_PAPER] File load error for {path}: {e}")
            sys.exit(1)

    result = validate_cross_paper_independence(cards_data)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
