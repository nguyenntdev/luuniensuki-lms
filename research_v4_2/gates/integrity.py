"""Gate 6: Cryptographic and Procedural Integrity Validator (integrity.py).

Recomputes content SHA of all cards, verifies train/dev/test artifact digests,
detects machine-specific absolute path leakage, and prevents duplicate test trials (test peeking).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Dict, List, Optional

from research_v4_2.contracts.types import GateResult, canonical_hash


def _file_sha256(path: str) -> str:
    """Compute standard SHA-256 digest of a raw file on disk."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _check_non_portable_paths(obj: Any) -> List[str]:
    """Recursively search for machine-specific absolute paths (e.g. /home/clue, /Users/, C:\\)."""
    violations = []
    forbidden_pattern = re.compile(r"(/home/[^/\s]+|/Users/[^/\s]+|[a-zA-Z]:\\)", re.IGNORECASE)

    def _walk(item: Any):
        if isinstance(item, str):
            if forbidden_pattern.search(item):
                violations.append(item)
        elif isinstance(item, dict):
            for v in item.values():
                _walk(v)
        elif isinstance(item, (list, tuple)):
            for v in item:
                _walk(v)

    _walk(obj)
    return violations


def validate_integrity(
    card_file_paths: Optional[List[str]] = None,
    card_objects: Optional[List[Dict[str, Any]]] = None,
    split_files: Optional[Dict[str, str]] = None,
    expected_split_hashes: Optional[Dict[str, str]] = None,
    test_receipts: Optional[List[Dict[str, Any]]] = None,
) -> GateResult:
    """Validate cryptographic digests, file hash agreements, path portability, and one-shot test execution."""
    messages = []
    details = {}

    cards_to_check: List[tuple[str, Dict[str, Any]]] = []

    if card_file_paths:
        for p in card_file_paths:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cards_to_check.append((p, data))
            except Exception as e:
                messages.append(f"CARD_READ_ERROR: Could not read card file {p}: {e}")

    if card_objects:
        for idx, obj in enumerate(card_objects):
            name = obj.get("claim_id") or obj.get("dataset_id") or obj.get("baseline_id") or f"card_{idx}"
            cards_to_check.append((name, obj))

    details["num_cards_verified"] = len(cards_to_check)

    # 1. Card content SHA verification
    for name, card_dict in cards_to_check:
        recorded_sha = card_dict.get("card_sha256")
        computed_sha = canonical_hash(card_dict, exclude_keys={"card_sha256"})
        if not recorded_sha:
            messages.append(f"MISSING_CARD_SHA: Card '{name}' does not contain 'card_sha256'.")
        elif recorded_sha != computed_sha:
            messages.append(
                f"CARD_SHA_MISMATCH: Card '{name}' has recorded sha {recorded_sha}, "
                f"but computed canonical sha is {computed_sha}. Card was tampered or is stale."
            )

        # Path portability check
        path_violations = _check_non_portable_paths(card_dict)
        if path_violations:
            messages.append(
                f"NON_PORTABLE_PATH_DETECTED: Card '{name}' contains machine-specific absolute path(s): {path_violations[:3]}"
            )

    # 2. Split file hashes verification
    if split_files and expected_split_hashes:
        details["splits_checked"] = list(split_files.keys())
        for split_name, fpath in split_files.items():
            expected = expected_split_hashes.get(split_name)
            if expected:
                try:
                    actual = _file_sha256(fpath)
                    if actual != expected:
                        messages.append(
                            f"SPLIT_HASH_MISMATCH: {split_name} file '{fpath}' actual sha256 ({actual}) "
                            f"does not match expected hash ({expected})."
                        )
                except Exception as e:
                    messages.append(f"SPLIT_READ_ERROR: Could not compute hash for {split_name} at {fpath}: {e}")

    # 3. One-shot test trial audit (preventing multi-trial test leakage)
    if test_receipts:
        details["num_test_trials"] = len(test_receipts)
        # Check distinct candidate model configs evaluated on test set
        test_evals = [t for t in test_receipts if t.get("split") == "test" or t.get("is_test", False)]
        distinct_configs = {
            t.get("config_hash") or t.get("model_hash") or t.get("model_id")
            for t in test_evals
        }
        distinct_configs.discard(None)
        if len(distinct_configs) > 1:
            messages.append(
                f"DUPLICATE_TEST_TRIAL_DETECTED: Found {len(distinct_configs)} distinct candidate model configs "
                f"evaluated on the sealed test set ({distinct_configs}). Only one-shot test evaluation is permitted."
            )

    passed = len(messages) == 0
    if passed:
        messages.append("Integrity check passed: canonical hashes match, paths portable, one-shot test verified.")

    return GateResult(
        gate_name="integrity",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate cryptographic integrity and one-shot test conformance.")
    parser.add_argument("--cards", nargs="+", default=[], help="Paths to contract card JSON files.")
    parser.add_argument("--receipts", type=str, default=None, help="Path to trial receipts JSON file.")

    args = parser.parse_args()

    receipts_data = None
    if args.receipts:
        try:
            with open(args.receipts, "r", encoding="utf-8") as f:
                receipts_data = json.load(f)
        except Exception as e:
            print(f"[INTEGRITY] Error loading receipts: {e}")
            sys.exit(1)

    result = validate_integrity(card_file_paths=args.cards, test_receipts=receipts_data)
    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
