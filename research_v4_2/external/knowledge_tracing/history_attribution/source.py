"""Reconstruct analysis histories from original release events."""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PARENT), str(PARENT / "temporal")]
import prepare


def assist_histories(raw):
    import study

    # Independent prefix slices verify the incrementally maintained tree inputs.
    pool = study.load_split(raw / "train_valid.csv")
    test = study.load_split(raw / "test.csv")
    users = {uid for uid, _, _, _ in pool + test}
    assert len(users) == len(pool) + len(test)
    features = study.features(test)
    rows = []
    repeated = []
    for uid, _, skills, labels in test:
        for step, (current, y) in enumerate(zip(skills, labels)):
            if step == 0:
                continue
            history = labels[:step]
            same = np.flatnonzero(skills[:step] == current)
            last_other = np.flatnonzero(skills[:step] != current)
            run_start = last_other[-1] + 1 if len(last_other) else 0
            run = history[run_start:]
            streak = 0
            if len(run):
                opposite = np.flatnonzero(run != run[-1])
                streak = len(run) - (opposite[-1] + 1 if len(opposite) else 0)
            right = int(history.sum())
            skill_right = int(labels[same].sum())
            rows.append((uid, step, y, current, right, step - right, skill_right,
                         len(same) - skill_right, step, labels[same[-1]] if len(same) else -1,
                         step - same[-1] if len(same) else 0, len(run),
                         streak if streak and run[-1] else 0,
                         streak if streak and not run[-1] else 0))
            repeated.append(len(same))
    expected = pd.DataFrame(rows, columns=features.columns)
    for name in ["uid", "step", "y", "skill", "previous"]:
        np.testing.assert_array_equal(features[name].astype(int), expected[name])
    for name in set(study.FULL) - {"skill", "previous"}:
        np.testing.assert_allclose(features[name], np.log1p(expected[name]), rtol=0, atol=1e-12)
    return expected[["uid", "step", "y"]].assign(depth=expected.step, same_skill=repeated)


def ednet_histories(raw, cache):
    with zipfile.ZipFile(raw / "contents.zip") as archive:
        with archive.open("contents/questions.csv") as stream:
            catalog = {r["question_id"]: r for r in csv.DictReader(io.TextIOWrapper(stream))}

    table = pd.read_pickle(cache / "rows.pkl")
    windows = np.load(cache / "windows.npy", allow_pickle=False)
    with np.load(cache / "simplekt.npz", allow_pickle=False) as simplekt:
        for name, expected in {"skills": windows[:, :, 0], "responses": windows[:, :, 1],
                               "skill": table.skill.astype(int), "bucket": table.bucket, "y": table.y}.items():
            np.testing.assert_array_equal(simplekt[name], expected)
        items = simplekt["items"]

    screen = table.loc[table.bucket.between(70, 79)].reset_index(names="cache_index")
    archive_users = set()
    checked = set()
    for uid, bucket, source in prepare.members(raw / "KT1.prefix"):
        assert uid not in archive_users
        archive_users.add(uid)
        if 70 <= bucket < 80:
            ordered = sorted(range(len(source)), key=lambda i: (int(source[i]["timestamp"]), i))
            clipped_bundles = {source[i]["solving_id"] for i in ordered[160:]}
            bundles = defaultdict(list)
            for i in ordered[:160]:
                row = source[i]
                if row["solving_id"] in clipped_bundles:
                    continue
                q = catalog[row["question_id"]]
                t = int(row["timestamp"])
                bundle = row["solving_id"]
                bundles[bundle].append((t, i, t + int(row["elapsed_time"]), q["question_id"],
                                        int(q["tags"].split(";")[0] or -1),
                                        int(q["part"]), int(row["user_answer"] == q["correct_answer"])))
            by_id = screen.loc[screen.uid.eq(uid)].set_index("row", verify_integrity=True)
            for bundle, events in bundles.items():
                start = events[0][0]
                prior = sorted(r for b, group in bundles.items()
                               if b != bundle and all(r[2] < start for r in group)
                               for r in group)
                if prior:
                    for _, row_id, _, item, skill, part, y in events:
                        idx = check_ednet_event(by_id.loc[row_id], (start, item, skill, part, y),
                                                prior, windows, items)
                        assert idx not in checked
                        checked.add(idx)
    assert checked == set(screen.cache_index)
    # These counts are checked against independently reconstructed raw prefixes.
    return screen[["uid", "row", "start", "gap_s", "y", "question", "skill", "n", "nskill"]].rename(
        columns={"n": "depth", "nskill": "same_skill"})


def check_ednet_event(row, current, prior, windows, items):
    start, item, skill, part, y = current
    assert (row.start, row.question, int(row.skill), int(row.part), row.y) == current
    same_skill = [r for r in prior if r[4] == skill]
    same_item = [r for r in prior if r[3] == item]
    assert (row.n, row.right, row.nskill, row.rskill, row.nitem, row.ritem) == (
        len(prior), sum(r[6] for r in prior), len(same_skill), sum(r[6] for r in same_skill),
        len(same_item), sum(r[6] for r in same_item))
    assert (row.last, row.lastskill) == (prior[-1][6], same_skill[-1][6] if same_skill else -1)
    gap = (start - prior[-1][0]) / 1000
    assert row.gap_s == gap

    ages = (start - np.array([r[0] for r in prior])) / 1000
    labels = np.array([r[6] for r in prior])
    skill_mask = np.array([r[4] == skill for r in prior])
    item_mask = np.array([r[3] == item for r in prior])
    delays = [np.log1p(a[-1]) if len(a) else -1 for a in (ages, ages[skill_mask], ages[item_mask])]
    recency = []
    for age, label, scale in [(ages, labels, 3600), (ages, labels, 86400),
                              (ages[skill_mask], labels[skill_mask], 86400)]:
        w = np.exp(-age / scale)
        recency.append((1 + w @ label) / (2 + w.sum()))
    last_same = max(np.flatnonzero(skill_mask), default=-1)
    after = prior[last_same + 1:]
    tail = prior[-16:]
    other = [r for r in tail if r[5] == part and r[4] != skill]
    interference = [len(after), sum(r[6] for r in after),
                    (1 + sum(r[6] for r in other)) / (2 + len(other)), len(other),
                    sum(a[4] != b[4] for a, b in zip(tail, tail[1:]))]
    np.testing.assert_allclose(row[prepare.CLOCK + prepare.INTERF].to_numpy(dtype=float),
                               [*delays, *recency, *interference], atol=1e-12, rtol=0)
    i = row.cache_index
    pad = 16 - len(tail)
    np.testing.assert_array_equal(windows[i], [(r[4], r[6]) for r in tail] + [(-2, 0)] * pad)
    np.testing.assert_array_equal(items[i], [int(r[3][1:]) for r in tail] + [0] * pad + [int(item[1:])])
    return i
