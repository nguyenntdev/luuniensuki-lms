"""Score count-preserving revisions to published assessment weights."""
import csv
import hashlib
import sys
from collections import defaultdict
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

from sklearn.metrics import average_precision_score

archive = Path(sys.argv[1])
print("archive sha256", hashlib.sha256(archive.read_bytes()).hexdigest())
profiles = defaultdict(lambda: defaultdict(list))
with ZipFile(archive) as source:
    for row in csv.DictReader(TextIOWrapper(source.open("assessments.csv"))):
        profiles[row["code_module"], row["code_presentation"]][row["assessment_type"]].append(
            Decimal(row["weight"])
        )
edges = Path(__file__).resolve().parents[1] / "assessment/run/edges.csv"
labels = []
scores = defaultdict(list)
with edges.open() as stream:
    for row in csv.DictReader(stream):
        a, b = (profiles[row["module"], row[k]] for k in ("source", "target"))
        assert a and b
        counts_changed = {k: len(v) for k, v in a.items()} != {k: len(v) for k, v in b.items()}
        assert counts_changed == bool(int(row["changed"]))
        if counts_changed:
            continue
        changed = any(sorted(a[k]) != sorted(b[k]) for k in a)
        print(row["module"], row["source"], row["target"], int(changed))
        labels.append(changed)
        for k in list(row)[4:12]:
            scores[k].append(float(row[k]))
print("events / eligible", sum(labels), len(labels))
for k, values in scores.items():
    print(k, round(average_precision_score(labels, values), 4))
