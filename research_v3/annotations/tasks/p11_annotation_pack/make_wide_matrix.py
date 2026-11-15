#!/usr/bin/env python3
"""Export long-format P11 ratings CSV -> wide units x raters matrix for the reliability harness.

Usage:
    python make_wide_matrix.py ratings_filled.csv --criterion S1_sourcing > wide_S1.csv

Input (ratings_template.csv format, one row per unit x rater x criterion):
    unit_id,rater_id,criterion,rating,uncertain,seconds_elapsed,batch_id,codebook_version,rated_at

Output: unit_id,rater_A,rater_B,... with ratings 0-3; NOT_APPLICABLE/ABSTAIN become empty
cells (excluded from agreement math per preregistered rule; never imputed).

This tool contains NO data and NO annotator IDs; it operates only on files supplied by the
human research lead after real rating sessions exist.
"""
from __future__ import annotations

import argparse
import csv
import sys

NON_RATINGS = {"", "NA", "NOT_APPLICABLE", "ABSTAIN"}


def to_wide(rows: list[dict[str, str]], criterion: str) -> tuple[list[str], list[list[str]]]:
    raters: list[str] = []
    units: dict[str, dict[str, str]] = {}
    for r in rows:
        if r["criterion"].strip() != criterion:
            continue
        rater = r["rater_id"].strip()
        unit = r["unit_id"].strip()
        if rater not in raters:
            raters.append(rater)
        units.setdefault(unit, {})[rater] = (r["rating"] or "").strip()
    header = ["unit_id", *sorted(raters)]
    out = [header]
    for unit in sorted(units):
        out.append([unit, *(units[unit].get(rt, "") for rt in sorted(raters))])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ratings_csv")
    ap.add_argument("--criterion", required=True, help="e.g. S1_sourcing")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    with open(args.ratings_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    wide = to_wide(rows, args.criterion)
    target = sys.stdout if args.out == "-" else open(args.out, "w", newline="", encoding="utf-8")
    writer = csv.writer(target)
    writer.writerows(wide)
    if target is not sys.stdout:
        target.close()
    n_missing = sum(1 for row in wide[1:] for cell in row[1:] if cell in NON_RATINGS)
    print(f"[make_wide_matrix] criterion={args.criterion} units={len(wide) - 1} missing_cells={n_missing} (excluded, not imputed)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
