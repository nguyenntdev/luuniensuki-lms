"""V3-G06: fail-closed reproducibility harness stub.

REFUSES to train unless:
1. an ExperimentCard JSON is supplied (``--experiment-card``), and
2. every dataset the card names is APPROVED in the dataset registry.

When data is BLOCKED the harness RAISES (DataBlockedError) — it never degrades
into a silent success or a fabricated metric. On acceptance it writes a run
manifest recording the card hash, dataset hashes, seed, git SHA and outputs.
The actual model fitting is a stub: this command exists to enforce the
reproducibility *contract*, not to claim results that do not exist yet.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.contracts.cards import ContractError, ExperimentCard
from research_v3.datasets.registry import LicenseGateError, load_registry, require_approved
from research_v3.scripts._paths import RUNS_DIR

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CARD_INVALID = 11
EXIT_DATA_BLOCKED = 12


class DataBlockedError(LicenseGateError):
    """Raised (never swallowed) when training data is BLOCKED/unapproved."""


class ExperimentCardError(ContractError):
    """Raised when the ExperimentCard is missing or invalid."""


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(__file__).resolve().parents[2]),
            text=True,
        ).strip()
    except Exception:  # pragma: no cover
        return "unknown"


def load_experiment_card(path: Path) -> ExperimentCard:
    if not path.is_file():
        raise ExperimentCardError(f"experiment card not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentCardError(f"{path}: invalid JSON: {exc}") from exc
    try:
        return ExperimentCard(**payload)
    except ContractError as exc:
        raise ExperimentCardError(f"{path}: {exc}") from exc
    except TypeError as exc:
        raise ExperimentCardError(f"{path}: unexpected card field: {exc}") from exc


def gate_datasets(card: ExperimentCard, registry_path: Path | None = None) -> list:
    """Fail-closed license gate. Raises DataBlockedError — never returns None."""
    registry = load_registry(registry_path)
    needed = list(card.train_dataset_ids) + list(card.holdout_dataset_ids)
    if not needed:
        raise DataBlockedError(
            f"{card.paper_id}: card names no datasets; refusing to train on nothing"
        )
    # require_approved raises LicenseGateError (=> DataBlockedError contract).
    return require_approved(registry, needed, paper_id=card.paper_id)


def build_manifest(card: ExperimentCard, approved_cards: list, *, seed: int | None) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "research_v3.run_manifest/v1",
        "task_id": "V3-G06",
        "paper_id": card.paper_id,
        "rq_id": card.rq_id,
        "created_at_utc": now,
        "experiment_card_sha256": card.sha256(),
        "method_commit_sha": _git_head(),
        "method_hash": card.method_hash,
        "seed": (card.seed if seed is None else seed),
        "datasets": [
            {
                "dataset_id": c.dataset_id,
                "status": c.status,
                "original_sha256": c.original_sha256,
                "license_text_sha256": c.license_text_sha256,
            }
            for c in approved_cards
        ],
        "split_hash": card.split_hash,
        "prereg_sha256": card.prereg_sha256,
        "hyperparameter_budget": card.hyperparameter_budget,
        "status": "MANIFEST_WRITTEN_TRAINING_STUB",
        "note": (
            "Harness gate passed; actual model fitting is NOT implemented. No "
            "metric is produced by this command — evaluate.py consumes saved "
            "predictions, never invented ones."
        ),
    }


def run_training_gate(card: ExperimentCard, *, seed: int | None = None, registry_path: Path | None = None) -> dict:
    """Full gate + manifest assembly. Raises on any blocked state (fail-closed)."""
    approved = gate_datasets(card, registry_path)
    manifest = build_manifest(card, approved, seed=seed)
    manifest["manifest_sha256"] = sha256_input(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.train",
        description=(
            "Fail-closed reproducibility harness: refuses to train without an "
            "ExperimentCard and APPROVED datasets; writes a run manifest (V3-G06)."
        ),
    )
    parser.add_argument("--paper", default=None, help="Paper id (informational; card is authoritative)")
    parser.add_argument("--experiment-card", type=Path, required=True, help="ExperimentCard JSON")
    parser.add_argument("--seed", type=int, default=None, help="Override the card seed (recorded, not tuned)")
    parser.add_argument("--registry", type=Path, default=None, help="Alternate dataset registry path")
    parser.add_argument("--output", type=Path, default=None, help="Manifest output path")
    parser.add_argument("--dry-run", action="store_true", help="Run gates only; do not write the manifest")
    args = parser.parse_args(argv)

    try:
        card = load_experiment_card(args.experiment_card)
        manifest = run_training_gate(card, seed=args.seed, registry_path=args.registry)
    except DataBlockedError as exc:
        # Fail-closed: a blocked state RAISES through to a nonzero exit; it is
        # never converted into a silent success. require_approved raises a
        # bare LicenseGateError for non-approved datasets, which we normalize
        # into DataBlockedError here.
        print(f"BLOCKED train: {exc}", file=sys.stderr)
        return EXIT_DATA_BLOCKED
    except LicenseGateError as exc:
        print(f"BLOCKED train: {exc}", file=sys.stderr)
        return EXIT_DATA_BLOCKED
    except (ExperimentCardError, ContractError) as exc:
        print(f"BLOCKED train: {exc}", file=sys.stderr)
        return EXIT_CARD_INVALID

    if args.dry_run:
        print(
            f"OK train (dry-run): gates passed for {card.paper_id}; "
            f"{len(manifest['datasets'])} approved dataset(s); manifest not written"
        )
        return EXIT_OK

    output = args.output or RUNS_DIR / card.paper_id / f"{card.rq_id}" / "train_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"OK train: manifest written for {card.paper_id}/{card.rq_id} "
        f"(card sha {card.sha256()[:12]}) -> {output}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
