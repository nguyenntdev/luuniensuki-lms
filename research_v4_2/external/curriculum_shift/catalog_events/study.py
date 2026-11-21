"""Reproduce the frozen curriculum edit localization comparison."""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import balanced_accuracy_score, confusion_matrix


def fingerprint(tokens):
    return [hashlib.sha256(t.encode()).hexdigest()[:16] for t in tokens]


def extract(records):
    rows = []
    for pr in sorted(records, key=lambda p: p["number"]):
        labels = [label["name"] for label in pr["labels"]]
        if not pr["merged_at"] or not any(s.startswith("Content: ") for s in labels):
            continue
        title = pr["title"].lower()
        grams = [title[i:i+n] for n in (3, 4, 5) for i in range(len(title)-n+1)]
        rows.append(dict(number=pr["number"], merged=pr["merged_at"],
                         y=int("Content: Foundations" in labels),
                         word=fingerprint(re.findall(r"\w+", title)), char=fingerprint(grams)))
    return rows


path = Path("records.json")
if len(sys.argv) == 2:
    path.write_text(json.dumps(extract(json.loads(Path(sys.argv[1]).read_text()))))
rows = json.loads(path.read_text())
k = len(rows)*2//3
y = np.array([r["y"] for r in rows])
pred = {"majority": np.repeat(np.bincount(y[:k]).argmax(), len(y)-k)}
for field in ("word", "char"):
    docs = [" ".join(r[field]) for r in rows]
    vectorizer = TfidfVectorizer()
    train = vectorizer.fit_transform(docs[:k])
    similarity = vectorizer.transform(docs[k:]) @ train.T
    pred[field] = y[np.asarray(similarity.argmax(axis=1)).ravel()]
print("train", k, "test", len(rows)-k)
for name, values in pred.items():
    print(name, balanced_accuracy_score(y[k:], values), confusion_matrix(y[k:], values).tolist())
print("PR actual majority word char")
for i, row in enumerate(rows[k:]):
    print(row["number"], row["y"], *(v[i] for v in pred.values()))
