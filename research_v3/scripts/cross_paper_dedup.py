"""V3-G18: cross-paper integrity / dedup enforcement.

Detects two papers claiming the same PRIMARY hypothesis or the same primary
outcome table. Sources (read-only):
- prereg files: research_v3/experiments/*/pre_registration.yaml
- claim ledger: research_v3/governance/claims/claims_ledger.csv (primary rows)

A collision is (a) two papers sharing a primary_metric name, or (b) two papers
whose declared primary hypothesis hashes identically (normalized text), or
(c) two ledger rows claiming the same primary outcome table id. Any collision
=> nonzero exit (MERGE_REQUIRED per the spec's dedup protocol).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from research_v3.scripts._paths import CLAIMS_DIR, RESEARCH_V3_ROOT

EXPERIMENTS_DIR = RESEARCH_V3_ROOT / "experiments"
CLAIMS_CSV = CLAIMS_DIR / "claims_ledger.csv"

EXIT_OK = 0
EXIT_COLLISION = 18
EXIT_CONFIG_ERROR = 7

_WS = re.compile(r"\s+")


class DedupError(RuntimeError):
    """Raised when dedup inputs cannot be read."""


def _normalize(text: str) -> str:
    return _WS.sub(" ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def _hash_text(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise DedupError("PyYAML is required") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def collect_prereg_claims(experiments_dir: Path = EXPERIMENTS_DIR) -> tuple[list[dict], list[str]]:
    """Collect (paper_id, primary_metric, primary_hypothesis_hash) from preregs.

    Unparseable prereg files are reported as skipped (the owning paper agent
    must fix them); they never silently crash the dedup gate.
    """
    claims: list[dict] = []
    skipped: list[str] = []
    for prereg in sorted(experiments_dir.glob("*/pre_registration.yaml")):
        try:
            data = _load_yaml(prereg)
        except Exception:
            skipped.append(str(prereg))
            continue
        paper_id = str(data.get("paper_id") or prereg.parent.name.upper())
        entry: dict = {
            "paper_id": paper_id,
            "source": str(prereg),
            "primary_metric": data.get("primary_metric"),
            "primary_hypothesis_hash": None,
        }
        hyps = data.get("hypotheses") or {}
        if isinstance(hyps, dict):
            h1 = hyps.get("H1")
            if isinstance(h1, str) and h1.strip():
                entry["primary_hypothesis_hash"] = _hash_text(h1)
        elif isinstance(hyps, list) and hyps:
            first = hyps[0]
            text = first.get("hypothesis") if isinstance(first, dict) else first
            if isinstance(text, str) and text.strip():
                entry["primary_hypothesis_hash"] = _hash_text(text)
        claims.append(entry)
    return claims, skipped


def collect_ledger_claims(claims_csv: Path = CLAIMS_CSV) -> list[dict]:
    if not claims_csv.is_file():
        return []
    rows = []
    with claims_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("claim_kind") in ("primary_outcome_table", "PAPER_LEVEL"):
                rows.append(row)
    return rows


def find_collisions(
    prereg_claims: list[dict], ledger_rows: list[dict]
) -> list[dict]:
    collisions: list[dict] = []
    # (a) same primary metric claimed by two papers as PRIMARY
    by_metric: dict[str, list[str]] = {}
    for c in prereg_claims:
        if c["primary_metric"]:
            by_metric.setdefault(str(c["primary_metric"]), []).append(c["paper_id"])
    for metric, papers in sorted(by_metric.items()):
        if len(papers) > 1:
            collisions.append(
                {"kind": "same_primary_metric", "key": metric, "papers": sorted(papers)}
            )
    # (b) identical primary hypothesis text
    by_hash: dict[str, list[str]] = {}
    for c in prereg_claims:
        if c["primary_hypothesis_hash"]:
            by_hash.setdefault(c["primary_hypothesis_hash"], []).append(c["paper_id"])
    for h, papers in sorted(by_hash.items()):
        if len(papers) > 1:
            collisions.append(
                {"kind": "identical_primary_hypothesis", "key": h[:16], "papers": sorted(papers)}
            )
    # (c) same primary outcome table id in the ledger
    by_table: dict[str, list[str]] = {}
    for row in ledger_rows:
        table = row.get("table_cell_ids") or row.get("claim_id")
        if table:
            by_table.setdefault(table, []).append(row.get("paper_id", "?"))
    for table, papers in sorted(by_table.items()):
        if len(set(papers)) > 1:
            collisions.append(
                {"kind": "same_primary_outcome_table", "key": table, "papers": sorted(set(papers))}
            )
    return collisions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.cross_paper_dedup",
        description=(
            "Detect two papers claiming the same primary hypothesis/outcome "
            "table; nonzero exit on collision (V3-G18)."
        ),
    )
    parser.add_argument("--experiments-dir", type=Path, default=EXPERIMENTS_DIR)
    parser.add_argument("--claims-csv", type=Path, default=CLAIMS_CSV)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        prereg, skipped = collect_prereg_claims(args.experiments_dir)
        ledger = collect_ledger_claims(args.claims_csv)
    except (DedupError, OSError) as exc:
        print(f"FAIL cross_paper_dedup: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    for path in skipped:
        print(f"SKIPPED (unparseable prereg, owner must fix): {path}", file=sys.stderr)

    collisions = find_collisions(prereg, ledger)
    print(f"Scanned {len(prereg)} prereg paper(s), {len(ledger)} primary ledger row(s).")
    for c in collisions:
        print(f"COLLISION [{c['kind']}] {c['key']}: {', '.join(c['papers'])}", file=sys.stderr)
    if args.json:
        print(
            json.dumps(
                {
                    "collisions": collisions,
                    "papers_scanned": len(prereg),
                    "skipped_preregs": skipped,
                },
                indent=2,
            )
        )
    if collisions:
        print(
            f"FAIL cross_paper_dedup: {len(collisions)} collision(s) — MERGE_REQUIRED "
            "per the dedup protocol before any submission.",
            file=sys.stderr,
        )
        return EXIT_COLLISION
    print("OK cross_paper_dedup: no duplicated primary claim across papers.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
