"""V3-G03: round-trip validation for the V3 card contracts.

Round-trips every card found on disk (the dataset registry YAML plus any
``*.card.json``/ExperimentCard/EvidenceCard JSON payloads passed on the
command line) through canonical JSON (research_v2.contracts.canonical_hash
standard) and asserts the SHA-256 is STABLE across a second round-trip —
the append-only property: a frozen card must hash identically every time it
is re-serialized; any mutation is detectable.

Also verifies contract construction failures are typed (a card with an
invalid status must raise ContractError, never pass silently).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.contracts.cards import (
    ContractError,
    DatasetCard,
    EvidenceCard,
    ExperimentCard,
)
from research_v3.datasets.registry import load_registry
from research_v3.scripts._paths import RESEARCH_V3_ROOT

DEFAULT_REGISTRY = RESEARCH_V3_ROOT / "datasets" / "registry.yaml"

EXIT_OK = 0
EXIT_VALIDATION_FAILED = 8


class ContractValidationError(RuntimeError):
    """Raised when a card file cannot be parsed into any known card type."""


def _roundtrip_check(card_dict: dict, *, source: str) -> list[str]:
    """Canonicalize twice and require the SHA to be stable; returns findings."""
    findings: list[str] = []
    try:
        hash1 = sha256_input(card_dict)
        hash2 = sha256_input(json.loads(json.dumps(card_dict)))
    except (TypeError, ValueError) as exc:
        findings.append(f"{source}: canonical serialization failed: {exc}")
        return findings
    if hash1 != hash2:
        findings.append(f"{source}: append-only violation — SHA changed across round-trip")
    return findings


def validate_registry(registry_path: Path) -> tuple[list[str], int]:
    findings: list[str] = []
    n = 0
    try:
        cards = load_registry(registry_path)
    except ContractError as exc:
        return [f"{registry_path}: invalid card: {exc}"], 0
    for card in cards:
        n += 1
        source = f"{registry_path.name}:{card.dataset_id}"
        findings.extend(_roundtrip_check(card.to_dict(), source=source))
        # Construction round-trip: rebuilding from the dict must reproduce the
        # identical SHA (catches lossy field coercion, e.g. tuple -> str).
        try:
            rebuilt = DatasetCard(**card.to_dict())
        except ContractError as exc:
            findings.append(f"{source}: reconstruction failed: {exc}")
            continue
        if rebuilt.sha256() != card.sha256():
            findings.append(f"{source}: reconstruction changed the card SHA")
        # Append-only probe: mutating a frozen card must be detectable.
        mutated = dict(card.to_dict())
        mutated["sample_count"] = int(mutated["sample_count"]) + 1
        if sha256_input(mutated) == card.sha256():
            findings.append(f"{source}: mutation NOT detected — hash standard is broken")
    return findings, n


def _parse_card_file(path: Path) -> tuple[str, dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractValidationError(f"{path}: expected a JSON object")
    kind = payload.get("_card_type") or (
        "experiment" if "paper_id" in payload and "split_hash" in payload else "evidence"
    )
    return kind, payload


def validate_card_files(paths: list[Path]) -> tuple[list[str], int]:
    findings: list[str] = []
    n = 0
    for path in paths:
        try:
            kind, payload = _parse_card_file(path)
            if kind == "experiment":
                ExperimentCard(**{k: v for k, v in payload.items() if k != "_card_type"})
            else:
                EvidenceCard(**{k: v for k, v in payload.items() if k != "_card_type"})
        except (ContractValidationError, ContractError, TypeError) as exc:
            findings.append(f"{path}: {exc}")
            continue
        n += 1
        clean = {k: v for k, v in payload.items() if k != "_card_type"}
        findings.extend(_roundtrip_check(clean, source=str(path)))
    return findings, n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.validate_contracts",
        description=(
            "Round-trip every V3 card through canonical JSON and assert the "
            "SHA is stable (append-only). Exits nonzero on any finding (V3-G03)."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Dataset registry YAML to validate",
    )
    parser.add_argument(
        "--cards",
        type=Path,
        nargs="*",
        default=[],
        help="Optional ExperimentCard/EvidenceCard JSON files to validate",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip the default registry validation",
    )
    args = parser.parse_args(argv)

    findings: list[str] = []
    n_cards = 0

    if not args.no_registry:
        reg_findings, n_reg = validate_registry(args.registry)
        findings.extend(reg_findings)
        n_cards += n_reg
        print(f"registry: {n_reg} DatasetCard(s) round-tripped")

    card_findings, n_extra = validate_card_files(args.cards)
    findings.extend(card_findings)
    n_cards += n_extra
    if args.cards:
        print(f"card files: {n_extra} card(s) round-tripped")

    if findings:
        for f in findings:
            print(f"FINDING: {f}", file=sys.stderr)
        print(
            f"FAIL validate_contracts: {len(findings)} finding(s) across {n_cards} card(s)",
            file=sys.stderr,
        )
        return EXIT_VALIDATION_FAILED
    print(f"OK validate_contracts: {n_cards} card(s) stable under canonical round-trip.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
