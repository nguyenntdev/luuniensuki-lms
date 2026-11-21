"""Gate 2: Preregistration Freeze Validator (preregister.py).

Rejects mutable preregistration, post-test method code mutations,
swapped baseline champions, and post-hoc threshold relaxations.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional

from research_v4_2.contracts.types import GateResult, canonical_hash


def validate_preregistration(
    prereg_data: Dict[str, Any],
    win_card_data: Dict[str, Any],
    method_card_data: Optional[Dict[str, Any]] = None,
) -> GateResult:
    """Validate that WinCard strictly adheres to the frozen pre-registration contract."""
    messages = []
    details = {}

    # 1. Verify preregistration content hash against recorded prereg_sha256
    computed_prereg_sha = canonical_hash(prereg_data)
    recorded_prereg_sha = win_card_data.get("prereg_sha256")
    details["computed_prereg_sha256"] = computed_prereg_sha
    details["recorded_prereg_sha256"] = recorded_prereg_sha

    if not recorded_prereg_sha or recorded_prereg_sha != computed_prereg_sha:
        messages.append(
            f"PREREG_HASH_MISMATCH: Computed prereg SHA-256 ({computed_prereg_sha}) "
            f"does not match WinCard recorded prereg_sha256 ({recorded_prereg_sha}). "
            "Preregistration was modified post-freeze."
        )

    # 2. Check baseline champion invariance
    prereg_champion = prereg_data.get("baseline_champion_id")
    win_champion = win_card_data.get("baseline_champion_id")
    details["prereg_champion"] = prereg_champion
    details["win_champion"] = win_champion
    if prereg_champion != win_champion:
        messages.append(
            f"CHAMPION_CHANGED_POST_HOC: Preregistered champion '{prereg_champion}' "
            f"differs from WinCard champion '{win_champion}'. Baseline champion swapping is prohibited."
        )

    # 3. Check primary metric invariance
    prereg_metric = prereg_data.get("primary_metric")
    win_metric = win_card_data.get("primary_metric")
    if prereg_metric != win_metric:
        messages.append(
            f"PRIMARY_METRIC_CHANGED_POST_HOC: Preregistered metric '{prereg_metric}' "
            f"differs from WinCard metric '{win_metric}'."
        )

    # 4. Check minimum meaningful delta invariance (delta_min)
    prereg_delta_min = prereg_data.get("delta_min")
    win_delta_min = win_card_data.get("delta_min")
    if prereg_delta_min is not None and win_delta_min is not None:
        if float(win_delta_min) < float(prereg_delta_min):
            messages.append(
                f"DELTA_MIN_RELAXED: WinCard delta_min ({win_delta_min}) is lower than "
                f"preregistered delta_min ({prereg_delta_min}). Post-hoc relaxation is prohibited."
            )

    # 5. Method code SHA invariance
    prereg_method_sha = prereg_data.get("method_code_sha256")
    if prereg_method_sha and method_card_data:
        actual_method_sha = method_card_data.get("code_sha256")
        details["prereg_method_sha"] = prereg_method_sha
        details["actual_method_sha"] = actual_method_sha
        if actual_method_sha and actual_method_sha != prereg_method_sha:
            messages.append(
                f"POSTTEST_METHOD_HASH_MUTATION: Method code hash '{actual_method_sha}' "
                f"does not match preregistered hash '{prereg_method_sha}'."
            )

    # 6. Timestamp precedence check (if timestamps present)
    frozen_at = prereg_data.get("frozen_at")
    test_at = win_card_data.get("test_completed_at")
    if frozen_at and test_at:
        if str(frozen_at) > str(test_at):
            messages.append(
                f"PREREG_TIMESTAMP_VIOLATION: Test was completed at {test_at} before "
                f"preregistration was frozen at {frozen_at}."
            )

    passed = len(messages) == 0
    if passed:
        messages.append("Preregistration integrity verified: frozen champion, metric, delta_min, and hashes match.")

    return GateResult(
        gate_name="preregister",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate preregistration integrity against WinCard.")
    parser.add_argument("--prereg", type=str, required=True, help="Path to frozen preregistration JSON.")
    parser.add_argument("--win-card", type=str, required=True, help="Path to WinCard JSON.")
    parser.add_argument("--method-card", type=str, default=None, help="Optional path to MethodCard JSON.")

    args = parser.parse_args()

    try:
        with open(args.prereg, "r", encoding="utf-8") as f:
            prereg_data = json.load(f)
        with open(args.win_card, "r", encoding="utf-8") as f:
            win_card_data = json.load(f)
        method_data = None
        if args.method_card:
            with open(args.method_card, "r", encoding="utf-8") as f:
                method_data = json.load(f)
    except Exception as e:
        print(f"[PREREGISTER] File load error: {e}")
        sys.exit(1)

    result = validate_preregistration(prereg_data, win_card_data, method_data)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
