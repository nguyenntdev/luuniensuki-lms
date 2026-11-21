"""Attach completed-bundle response lags to the temporal cohort."""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "temporal"))
from prepare import members, BASE, CLOCK

root = Path(sys.argv[1])
with zipfile.ZipFile(root / "contents.zip") as archive:
    answers = {r["question_id"]: r["correct_answer"] for r in csv.DictReader(
        io.TextIOWrapper(archive.open("contents/questions.csv")))}
lags = []
for uid, bucket, raw in members(root / "KT1.prefix"):
    if 60 <= bucket < 70:
        continue
    ordered = sorted(enumerate(raw), key=lambda pair: (int(pair[1]["timestamp"]), pair[0]))
    truncated = {r["solving_id"] for _, r in ordered[160:]}
    bundles = defaultdict(list)
    for idx, r in ordered[:160]:
        if r["solving_id"] not in truncated:
            t = int(r["timestamp"])
            category = "correct" if r["user_answer"] == answers[r["question_id"]] else r["user_answer"]
            bundles[r["solving_id"]].append((t, idx, t + int(r["elapsed_time"]), category))
    ends = {b: max(x[2] for x in rows) for b, rows in bundles.items()}
    for b, rows in bundles.items():
        prior = sorted(x for j, group in bundles.items() if ends[j] < rows[0][0] for x in group)
        if prior:
            values = [x[3] for x in reversed(prior[-4:])]
            for _, idx, _, _ in rows:
                lags.append([uid, idx, *values, *(["missing"] * (4-len(values)))])
frame = pd.read_pickle(root / "cache/rows.pkl")
frame = frame[frame.bucket.lt(60) | frame.bucket.between(70,79)]
joined = frame.merge(pd.DataFrame(lags, columns=["uid","row","lag1","lag2","lag3","lag4"]), validate="one_to_one")
assert len(joined) == len(frame) == len(lags)
joined.to_csv(sys.argv[2], index=False)
