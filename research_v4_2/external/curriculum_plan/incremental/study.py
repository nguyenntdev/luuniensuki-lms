"""Exact direct repairs after simulated course additions."""
import ast
import csv
import hashlib
import io
import itertools
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from screen import ARCHIVE, COURSE, cheapest, clauses


def extend(frontier, parts, prune):
    attempts = 0
    for choices in parts:
        attempts += len(frontier) * len(choices)
        merged = {a | b for a in frontier for b in choices}
        frontier = {a for a in merged if not any(b < a for b in merged)} if prune else merged
    return frontier, attempts


archive = Path("private_data/raw/otago-prereqs/release.zip")
assert hashlib.sha256(archive.read_bytes()).hexdigest() == ARCHIVE
summary = {}
with zipfile.ZipFile(archive) as z, (HERE / "episodes.csv").open("w", newline="") as out:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["table", "targets", "witness", "setup", "incremental", "cold_pruned", "cold_plain"])
    for table in ("comp", "math"):
        member, = (m for m in z.namelist() if m.endswith(f"/{table}_prereqs.csv"))
        rules = {}
        for row in csv.DictReader(io.StringIO(z.read(member).decode())):
            expr = row["Primary prerequisite"]
            if not expr.strip() or re.sub(r"\band\b|\bor\b|[()\s]", "", COURSE.sub("", expr)):
                continue
            body = COURSE.sub(lambda m: m[0].replace(" ", "_"), expr)
            rules[row["Paper"]] = clauses(ast.parse(body, mode="eval").body)
        totals = dict.fromkeys(("episodes", "setup", "incremental", "cold_pruned", "cold_plain"), 0)
        for targets in itertools.combinations(rules, 3):
            parts = [rules[t] for t in targets]
            atoms = set().union(*itertools.chain.from_iterable(parts))
            if any(t.replace(" ", "_") in atoms for t in targets):
                continue
            empty = {frozenset()}
            prefix, setup = extend(empty, parts[:2], True)
            updated, inc = extend(prefix, parts[2:], True)
            matched, cold = extend(empty, parts, True)
            plain, full = extend(empty, parts, False)
            witness = cheapest(updated)
            assert witness == cheapest(matched) == cheapest(plain)
            writer.writerow([table, "|".join(targets), "|".join(sorted(witness)), setup, inc, cold, full])
            for key, value in zip(totals, (1, setup, inc, cold, full)):
                totals[key] += value
        summary[table] = totals
(HERE / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
