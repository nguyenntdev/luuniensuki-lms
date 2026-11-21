"""Independently check all eligible bundles against exhaustive truth assignments."""
import csv
import io
import itertools
import json
import re
import sys
import zipfile
from pathlib import Path

archive, run = map(Path, sys.argv[1:])
token = re.compile(r"[A-Z]{4} \d{3}|and|or|[()]")
rank = {"or": 1, "and": 2}
n = 0
with (run/"repairs.csv").open() as f:
    decisions = {(r["table"], tuple(r["targets"].split("|"))): r for r in csv.DictReader(f)}


def postfix(expr):
    words = token.findall(expr)
    if not words or "".join(words).replace(" ", "") != "".join(expr.split()):
        return []
    values, operators = [], []
    for w in words:
        if w == "(":
            operators.append(w)
        elif w == ")":
            while operators[-1] != "(":
                values.append(operators.pop())
            operators.pop()
        elif w in rank:
            while operators and rank.get(operators[-1], 0) >= rank[w]:
                values.append(operators.pop())
            operators.append(w)
        else:
            values.append(w)
    return values + operators[::-1]


def accepts(words, completed):
    stack = []
    for w in words:
        if w in rank:
            a, b = stack.pop(), stack.pop()
            stack.append(a and b if w == "and" else a or b)
        else:
            stack.append(w in completed)
    assert len(stack) == 1
    return stack[0]


with zipfile.ZipFile(archive) as z:
    for table in ("comp", "math"):
        name, = (m for m in z.namelist() if m.endswith("/"+table+"_prereqs.csv"))
        form = {r["Paper"]: postfix(r["Primary prerequisite"])
                for r in csv.DictReader(io.StringIO(z.read(name).decode()))}
        for targets in itertools.combinations((t for t in form if form[t]), 3):
            atoms = set.union(*(set(form[t]) for t in targets)) - rank.keys()
            if atoms.intersection(targets):
                continue
            row = decisions.pop((table, targets))
            witness = {t.replace("_"," ") for t in row["witness"].split("|")}
            assert witness <= atoms and all(accepts(form[t], witness) for t in targets)
            assert int(row["pruned"]) == len(witness) == int(row["unpruned"])
            for k in range(len(witness)):
                assert not any(all(accepts(form[t], subset) for t in targets)
                               for subset in itertools.combinations(atoms, k))
            n += 1
assert not decisions
print(json.dumps({"eligible_bundles_verified": n, "witnesses_and_lower_bounds_checked": n}))
