"""Recover eligible item IDs for the frozen temporal windows from original EdNet rows."""
import argparse
import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "temporal"))
from prepare import members


def build(raw, out):
    table = pd.read_pickle(raw / "cache/rows.pkl").reset_index(drop=True)
    window = np.load(raw / "cache/windows.npy")
    by_user = table.groupby("uid").indices
    items = np.zeros((len(table), 17), dtype=np.int32)
    with zipfile.ZipFile(raw / "contents.zip") as archive:
        stream = io.TextIOWrapper(archive.open("contents/questions.csv"))
        catalog = {x["question_id"]: x for x in csv.DictReader(stream)}
    checked = 0
    for uid, bucket, source in members(raw / "KT1.prefix"):
        ordered = sorted(range(len(source)), key=lambda i: (int(source[i]["timestamp"]), i))
        excluded = {source[i]["solving_id"] for i in ordered[160:]}
        groups = defaultdict(list)
        for i in ordered[:160]:
            if source[i]["solving_id"] not in excluded:
                groups[source[i]["solving_id"]].append(i)
        ends = {b: max(int(source[i]["timestamp"]) + int(source[i]["elapsed_time"]) for i in ix)
                for b, ix in groups.items()}
        for idx in by_user.get(uid, []):
            row = table.iloc[idx]
            qrow = source[row.row]
            bundle = qrow["solving_id"]
            start = min(int(source[i]["timestamp"]) for i in groups[bundle])
            eligible = [i for i in ordered[:160] if ends.get(source[i]["solving_id"], start) < start][-16:]
            skills = [[int(catalog[source[i]["question_id"]]["tags"].split(";")[0] or -1),
                       int(source[i]["user_answer"] == catalog[source[i]["question_id"]]["correct_answer"])] for i in eligible]
            assert qrow["question_id"] == row.question and start == row.start and bucket == row.bucket
            assert int(qrow["user_answer"] == catalog[row.question]["correct_answer"]) == row.y
            assert np.array_equal(skills, window[idx, window[idx,:,0] != -2])
            items[idx,:len(eligible)] = [int(source[i]["question_id"][1:]) for i in eligible]
            items[idx,16] = int(row.question[1:])
            checked += 1
    assert checked == len(table)
    np.savez_compressed(out, items=items, skills=window[:,:,0], responses=window[:,:,1],
                        skill=table.skill.astype(int), bucket=table.bucket, y=table.y)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    build(args.raw, args.out)
