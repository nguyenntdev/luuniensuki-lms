"""V3-G04: materialize, hash and freeze split protocols for a paper.

Uses research_v3.eval.splitters.group_split / time_split on a JSONL row file,
asserts no leakage, and writes the protocol to
``research_v3/config/split_protocols/<PAPER>.json``:

``{paper_id, protocol, group_key/time_key, fractions, split_sha256,
split_ids, frozen_at}``

The split hash is deterministic: re-running the same command on the same rows
must produce the identical hash (checked when ``--verify-only`` is used).
Fail-closed: empty partitions, overlapping ids or a changed hash are nonzero
exits.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v3.contracts.cards import ContractError
from research_v3.eval.leakage import LeakageError, audit_rows
from research_v3.eval.splitters import (
    SplitError,
    assert_no_leakage,
    freeze_hash,
    group_split,
    time_split,
)
from research_v3.scripts._paths import SPLIT_PROTOCOL_DIR

EXIT_OK = 0
EXIT_SPLIT_FAILED = 9


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SplitError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def materialize_protocol(
    *,
    paper_id: str,
    rows: list[dict],
    protocol: str,
    group_key: str = "group_id",
    time_key: str = "time_key",
    fractions: tuple[float, float, float, float] = (0.70, 0.10, 0.10, 0.10),
    train_fraction: float = 0.70,
    skip_leakage_audit: bool = False,
) -> dict:
    """Build the frozen protocol dict (pure; no writes)."""
    if protocol not in {"group", "time"}:
        raise SplitError(f"unknown protocol {protocol!r}; use group|time")
    if not skip_leakage_audit:
        audit_rows(rows, strict=True)  # raises LeakageError on any finding
    if protocol == "group":
        split = group_split(rows, group_key=group_key, paper_id=paper_id, protocol="group", fractions=fractions)
        key_field = group_key
    else:
        split = time_split(rows, time_key=time_key, paper_id=paper_id, train_fraction=train_fraction)
        key_field = time_key
    assert_no_leakage(split)
    return {
        "schema": "research_v3.split_protocol/v1",
        "paper_id": paper_id,
        "protocol": protocol,
        "key_field": key_field,
        "fractions_group": list(fractions) if protocol == "group" else None,
        "train_fraction_time": train_fraction if protocol == "time" else None,
        "n_rows": len(rows),
        "partition_sizes": {k: len(v) for k, v in split.split_ids.items()},
        "split_ids": {k: list(v) for k, v in split.split_ids.items()},
        "split_sha256": freeze_hash(split),
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def verify_protocol(protocol: dict, rows: list[dict], *, protocol_name: str) -> list[str]:
    """Re-materialize and require the identical hash; returns findings."""
    key = protocol["key_field"]
    if protocol["protocol"] == "group":
        split = group_split(
            rows,
            group_key=key,
            paper_id=protocol["paper_id"],
            protocol="group",
            fractions=tuple(protocol["fractions_group"]),
        )
    else:
        split = time_split(
            rows,
            time_key=key,
            paper_id=protocol["paper_id"],
            train_fraction=protocol["train_fraction_time"],
        )
    fresh_hash = freeze_hash(split)
    if fresh_hash != protocol["split_sha256"]:
        return [
            f"{protocol_name}: split hash drift — stored {protocol['split_sha256'][:12]} "
            f"!= re-materialized {fresh_hash[:12]}"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.validate_splits",
        description=(
            "Materialize + hash a leakage-proof split protocol for one paper "
            "and freeze it under research_v3/config/split_protocols/ (V3-G04)."
        ),
    )
    parser.add_argument("--paper", required=True, help="Paper id, e.g. P06")
    parser.add_argument("--rows", type=Path, required=True, help="JSONL rows with group/time keys")
    parser.add_argument("--protocol", choices=["group", "time"], default="group")
    parser.add_argument("--group-key", default="group_id")
    parser.add_argument("--time-key", default="time_key")
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument(
        "--fractions",
        type=float,
        nargs=4,
        default=[0.70, 0.10, 0.10, 0.10],
        metavar=("TRAIN", "CAL", "DEV", "TEST"),
    )
    parser.add_argument("--all", action="store_true", help="Accepted for CI symmetry; requires --paper alternatives")
    parser.add_argument("--verify-only", action="store_true", help="Re-materialize and compare against the frozen hash")
    parser.add_argument("--skip-leakage-audit", action="store_true", help="Skip audit_rows (not recommended)")
    parser.add_argument("--output", type=Path, default=None, help="Override protocol output path")
    args = parser.parse_args(argv)

    try:
        rows = load_rows(args.rows)
        if args.verify_only:
            output = args.output or SPLIT_PROTOCOL_DIR / f"{args.paper}.json"
            protocol = json.loads(output.read_text(encoding="utf-8"))
            findings = verify_protocol(protocol, rows, protocol_name=output.name)
            if findings:
                for f in findings:
                    print(f"FINDING: {f}", file=sys.stderr)
                print("FAIL validate_splits: frozen hash does not reproduce.", file=sys.stderr)
                return EXIT_SPLIT_FAILED
            print(f"OK validate_splits: {output} reproduces split_sha256={protocol['split_sha256'][:12]}")
            return EXIT_OK

        protocol = materialize_protocol(
            paper_id=args.paper,
            rows=rows,
            protocol=args.protocol,
            group_key=args.group_key,
            time_key=args.time_key,
            fractions=tuple(args.fractions),
            train_fraction=args.train_fraction,
            skip_leakage_audit=args.skip_leakage_audit,
        )
        output = args.output or SPLIT_PROTOCOL_DIR / f"{args.paper}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(protocol, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            f"OK validate_splits: {args.paper} protocol={args.protocol} "
            f"rows={protocol['n_rows']} sizes={protocol['partition_sizes']} "
            f"split_sha256={protocol['split_sha256'][:12]} -> {output}"
        )
        return EXIT_OK
    except (SplitError, LeakageError, ContractError) as exc:
        print(f"FAIL validate_splits: {exc}", file=sys.stderr)
        return EXIT_SPLIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
