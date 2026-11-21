"""Verify the 15 transitions, source labels, ranking metrics and module-held-out alerts."""
from collections import Counter, defaultdict
from csv import DictReader
from io import TextIOWrapper
from itertools import pairwise
import json
from math import isclose
from pathlib import Path
import sys
from zipfile import ZipFile

archive, run = map(Path, sys.argv[1:])
with ZipFile(archive) as data:
    terms = defaultdict(list)
    for r in DictReader(TextIOWrapper(data.open("courses.csv"))):
        terms[r["code_module"]].append(r["code_presentation"])
    counts = defaultdict(Counter)
    for r in DictReader(TextIOWrapper(data.open("assessments.csv"))):
        counts[r["code_module"], r["code_presentation"]][r["assessment_type"]] += 1
labels = {(m,a,b): int(counts[m,a] != counts[m,b])
          for m, entries in terms.items() for a,b in pairwise(sorted(entries))}
report = json.loads((run/"result.json").read_text())
with (run/"edges.csv").open() as f:
    rows = list(DictReader(f))
assert len(rows) == report["edges"] == len(labels)
for r in rows:
    assert labels.pop((r["module"],r["source"],r["target"])) == int(r["changed"])
assert not labels
for method, metrics in report["methods"].items():
    threshold_set = {float(r[method]) for r in rows}
    ap, total = 0., sum(int(r["changed"]) for r in rows)
    for s in threshold_set:
        top = [r for r in rows if float(r[method]) >= s]
        ties = sum(int(r["changed"]) for r in top if float(r[method]) == s)
        ap += ties / total * sum(int(r["changed"]) for r in top) / len(top)
    assert isclose(ap, metrics["ap"])
    tp = fp = 0
    for m in terms:
        training = [r for r in rows if r["module"] != m]
        best = (0, float("inf"))
        for s in {float(r[method]) for r in training}:
            alerts = [int(r["changed"]) for r in training if float(r[method]) >= s]
            if 10 * alerts.count(0) <= len(alerts):
                best = max(best, (sum(alerts), s))
        for r in rows:
            if r["module"] == m:
                flag = float(r[method]) >= best[1]
                assert flag == bool(int(r["alert_"+method]))
                tp += flag * int(r["changed"])
                fp += flag * (1-int(r["changed"]))
    assert tp == metrics["tp"] and tp+fp == metrics["selected"]
    assert isclose(metrics["fdp"],fp/max(1,tp+fp)) and isclose(metrics["recall"],tp/total)
print(json.dumps({"transitions": len(rows), "positive": total, "detectors":len(report["methods"]),
                  "held_out_decisions": len(rows)*len(report["methods"])}))
