"""Evaluate direct course additions on explicit Boolean catalog requirements."""
import argparse
import ast
import csv
import hashlib
import io
import itertools
import json
import re
import zipfile
from pathlib import Path

ARCHIVE = "d820aa4d013a398784e7541a0815a737eade8142542bb6088aa00aae96fddb6c"
COURSE = re.compile(r"\b[A-Z]{4} [0-9]{3}\b")


def clauses(node):
    if isinstance(node, ast.Name):
        return {frozenset([node.id])}
    if not isinstance(node, ast.BoolOp):
        raise ValueError("Unexpected prerequisite syntax")
    parts = [clauses(child) for child in node.values]
    if isinstance(node.op, ast.Or):
        return set.union(*parts)
    return {frozenset.union(*terms) for terms in itertools.product(*parts)}


def cheapest(options):
    return min(options, key=lambda s: (len(s), sorted(s)))


def compose(parts, prune):
    plans = {frozenset()}
    for choices in parts:
        merged = {a | b for a in plans for b in choices}
        plans = {a for a in merged if not any(b < a for b in merged)} if prune else merged
    return cheapest(plans)


def evaluate(path, out):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ARCHIVE
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    with zipfile.ZipFile(path) as data, (out / "repairs.csv").open("w", newline="") as log:
        writer = csv.writer(log)
        writer.writerow(["table","targets","independent","sequential","unpruned","pruned","witness"])
        for table in ("comp", "math"):
            [member] = [f for f in data.namelist() if f.endswith("/"+table+"_prereqs.csv")]
            rows = list(csv.DictReader(io.StringIO(data.read(member).decode())))
            rules, empty, opaque = {}, [], []
            for row in rows:
                target, expr = row["Paper"], row["Primary prerequisite"]
                if not expr.strip():
                    empty.append(target)
                    continue
                remainder = re.sub(r"\band\b|\bor\b|[()\s]", "", COURSE.sub("", expr))
                if remainder:
                    opaque.append(target)
                    continue
                body = COURSE.sub(lambda m: m[0].replace(" ", "_"), expr)
                rules[target] = clauses(ast.parse(body, mode="eval").body)
            totals = [0]*4
            wins, excluded, n = 0, 0, 0
            for group in itertools.combinations(rules, 3):
                parts = [rules[t] for t in group]
                atoms = frozenset.union(*(v for part in parts for v in part))
                if any(t.replace(" ", "_") in atoms for t in group):
                    excluded += 1
                    continue
                local = frozenset.union(*(cheapest(p) for p in parts))
                greedy = frozenset()
                for p in parts:
                    greedy = cheapest([greedy | term for term in p])
                plain, pruned = compose(parts, False), compose(parts, True)
                assert len(pruned) == len(plain) <= min(len(local), len(greedy))
                costs = list(map(len, [local, greedy, plain, pruned]))
                totals = [a+b for a,b in zip(totals,costs)]
                n += 1
                wins += len(pruned) < len(local)
                writer.writerow([table, "|".join(group), *costs, "|".join(sorted(pruned))])
            summary[table] = dict(source_rows=len(rows), retained=len(rules), empty=empty, opaque=opaque,
                                  excluded_dependent_bundles=excluded, bundles=n, exact_beats_local=wins,
                                  mean_added=dict(zip(["independent","sequential","unpruned","pruned"],
                                                      [v/n for v in totals])))
    (out/"result.json").write_text(json.dumps(summary, indent=2)+"\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    evaluate(args.archive, args.out)
