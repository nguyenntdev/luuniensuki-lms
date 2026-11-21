"""Gate 7: Data Rights, License, and Ethics Clearance Validator (license_ethics.py).

Verifies legal data licensing, human-subject ethics clearance, and baseline code rights.
Explicitly accounts for authorized institutional / user research rights for
historical imperial records (Châu bản triều Nguyễn, Đại Nam thực lục, Cửu Đỉnh).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional

from research_v4_2.contracts.types import GateResult

PERMISSIBLE_OPEN_LICENSES = {
    "mit",
    "apache-2.0",
    "apache 2.0",
    "bsd-3-clause",
    "bsd-2-clause",
    "cc0",
    "cc-by",
    "cc-by-4.0",
    "cc-by-sa",
    "cc-by-sa-4.0",
    "open_data_commons",
    "gpl-3.0",
    "gpl-2.0",
    "agpl-3.0",
}

HERITAGE_ARCHIVE_KEYWORDS = [
    "châu bản",
    "chau ban",
    "thực lục",
    "thuc luc",
    "triều nguyễn",
    "trieu nguyen",
    "cửu đỉnh",
    "cuu dinh",
    "nguyen dynasty",
    "imperial archive",
]


def _is_authorized_heritage_archive(rights_info: Dict[str, Any], text_to_check: str) -> bool:
    """Check if source is part of authorized imperial Vietnamese historical archives."""
    if rights_info.get("authorized_heritage_source") or rights_info.get("user_authorized"):
        return True
    lower_txt = text_to_check.lower()
    return any(kw in lower_txt for kw in HERITAGE_ARCHIVE_KEYWORDS)


def validate_license_ethics(
    dataset_card_data: Dict[str, Any],
    baseline_cards: Optional[List[Dict[str, Any]]] = None,
) -> GateResult:
    """Validate legal license rights, human subject ethics, and authorized heritage source clearance."""
    messages = []
    details = {}

    # 1. Dataset license check
    rights = dataset_card_data.get("rights_and_license", {})
    license_name = str(rights.get("license", "")).strip()
    dataset_id = dataset_card_data.get("dataset_id", "unknown_dataset")
    details["dataset_license"] = license_name

    norm_license = license_name.lower().replace("_", "-")
    is_permissible_open = any(norm_license.startswith(pl) for pl in PERMISSIBLE_OPEN_LICENSES)
    combined_desc = f"{dataset_id} {json.dumps(rights)}"
    is_heritage_cleared = _is_authorized_heritage_archive(rights, combined_desc)

    if not license_name:
        messages.append(
            f"MISSING_DATASET_LICENSE: Dataset '{dataset_id}' does not specify a legal license in rights_and_license."
        )
    elif not is_permissible_open and not is_heritage_cleared:
        messages.append(
            f"UNAUTHORIZED_DATA_LICENSE: Dataset '{dataset_id}' license '{license_name}' is not recognized "
            "as an approved open license or authorized heritage research source."
        )
    elif is_heritage_cleared:
        details["heritage_archive_authorization"] = "AUTHORIZED_IMPERIAL_ARCHIVE_RESEARCH_SOURCE"

    # 2. Human subjects ethics clearance check
    ethics = dataset_card_data.get("ethics_clearance")
    details["has_ethics_clearance"] = bool(ethics)

    # Determine if dataset involves human subjects
    task_onto = dataset_card_data.get("task_ontology", {})
    allowed_use = dataset_card_data.get("allowed_use", [])
    onto_text = f"{json.dumps(task_onto)} {json.dumps(allowed_use)}".lower()

    human_indicators = ["student", "learner", "teacher", "user", "human_rater", "annotator", "clickstream"]
    involves_humans = any(ind in onto_text for ind in human_indicators)

    if involves_humans:
        if not ethics:
            messages.append(
                f"ETHICS_CLEARANCE_MISSING: Dataset '{dataset_id}' involves human participants "
                "or raters, but lacks an ethics_clearance approval record."
            )
        else:
            if not ethics.get("cleared", False):
                messages.append(
                    f"ETHICS_CLEARANCE_NOT_APPROVED: Ethics record for '{dataset_id}' has cleared=False."
                )
            if not ethics.get("protocol_id") and not ethics.get("irb_id") and not ethics.get("committee"):
                messages.append(
                    f"ETHICS_CLEARANCE_INCOMPLETE: Ethics record for '{dataset_id}' missing protocol/IRB ID or committee."
                )

    # 3. Baseline code licenses check
    if baseline_cards:
        details["num_baselines_checked"] = len(baseline_cards)
        for base_card in baseline_cards:
            b_id = base_card.get("baseline_id", "unknown_baseline")
            b_lic = str(base_card.get("license", "")).strip().lower().replace("_", "-")
            if not b_lic:
                messages.append(f"MISSING_BASELINE_LICENSE: Baseline '{b_id}' does not declare a software license.")
            elif not any(b_lic.startswith(pl) for pl in PERMISSIBLE_OPEN_LICENSES) and b_lic != "open-source":
                messages.append(
                    f"UNAPPROVED_BASELINE_LICENSE: Baseline '{b_id}' uses unapproved license '{b_lic}'."
                )

    passed = len(messages) == 0
    if passed:
        messages.append("License and ethics gate passed: valid dataset license, heritage authorization, and ethics approved.")

    return GateResult(
        gate_name="license_ethics",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate data license, heritage authorization, and ethics clearance.")
    parser.add_argument("--dataset-card", type=str, required=True, help="Path to DatasetCard JSON.")
    parser.add_argument("--baseline-cards", nargs="*", default=[], help="Paths to BaselineCard JSONs.")

    args = parser.parse_args()

    try:
        with open(args.dataset_card, "r", encoding="utf-8") as f:
            ds_data = json.load(f)
        b_data = []
        for bp in args.baseline_cards:
            with open(bp, "r", encoding="utf-8") as f:
                b_data.append(json.load(f))
    except Exception as e:
        print(f"[LICENSE_ETHICS] File load error: {e}")
        sys.exit(1)

    result = validate_license_ethics(ds_data, b_data)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
