"""Compare early activity shifts with changes in a separate course design table."""
import argparse
import hashlib
import json
import zipfile
from collections import Counter
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score

ARCHIVE = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
GROUP = ["code_module", "code_presentation"]
SCORES = ["weekly_quiz_js", "weekly_full_js", "pooled_full_js", "pooled_quiz_js",
          "raw_click_js", "inventory_js", "different_season", "weekly_quiz_abs"]


def read_inputs(archive):
    with archive.open("rb") as handle:
        assert hashlib.file_digest(handle, "sha256").hexdigest() == ARCHIVE
    with zipfile.ZipFile(archive) as source:
        inventory = pd.read_csv(source.open("vle.csv"))
        assessments = pd.read_csv(source.open("assessments.csv"))
        courses = pd.read_csv(source.open("courses.csv"))
        parts = []
        with source.open("studentVle.csv") as handle:
            for part in pd.read_csv(handle, chunksize=240000):
                early = part.loc[part.date.between(0, 55)].copy()
                early["week"] = early.date // 7
                early = early.merge(inventory[GROUP + ["id_site", "activity_type"]],
                                    on=GROUP + ["id_site"], how="left", validate="many_to_one")
                assert early.activity_type.notna().all()
                keys = GROUP + ["id_student", "week", "activity_type"]
                parts.append(early.groupby(keys).sum_click.sum())
    counts = pd.concat(parts).groupby(level=keys).sum().reset_index()
    halves = {i: hashlib.sha256(str(i).encode()).digest()[0] % 2 for i in counts.id_student.unique()}
    counts["half"] = counts.id_student.map(halves)
    return counts, inventory, assessments, courses


def profiles(counts, inventory, columns):
    keys = ["id_student", "week"]
    matrix = counts.pivot_table(index=keys, columns="activity_type", values="sum_click",
                                aggfunc="sum", fill_value=0).reindex(columns=columns, fill_value=0)
    matrix = matrix.loc[matrix.sum(axis=1) > 0]
    week = matrix.div(matrix.sum(axis=1), axis=0).groupby(level="week").mean()
    assert week.index.tolist() == list(range(8))
    quiz = week.loc[:, columns.isin(["quiz", "externalquiz"])].sum(axis=1)
    reduced = np.column_stack([quiz, 1 - quiz]).clip(0, 1)
    resource = inventory.activity_type.value_counts().reindex(columns, fill_value=0)
    return week.to_numpy(), reduced, matrix.sum().to_numpy(), resource.to_numpy()


def distances(a, b, season):
    full_a, quiz_a, raw_a, inventory_a = a
    full_b, quiz_b, raw_b, inventory_b = b
    return [jensenshannon(quiz_a, quiz_b, axis=1).mean(),
            jensenshannon(full_a, full_b, axis=1).mean(),
            jensenshannon(full_a.mean(axis=0), full_b.mean(axis=0)),
            jensenshannon(quiz_a.mean(axis=0), quiz_b.mean(axis=0)),
            jensenshannon(raw_a, raw_b), jensenshannon(inventory_a, inventory_b),
            float(season), np.abs(quiz_a[:, 0] - quiz_b[:, 0]).mean()]


def edges(counts, inventory, assessments, courses):
    columns = pd.Index(sorted(inventory.activity_type.unique()))
    rows = []
    for module, schedule in courses.groupby("code_module"):
        features, signatures = {}, {}
        for term in sorted(schedule.code_presentation):
            def select(frame):
                return frame.loc[(frame.code_module == module) & (frame.code_presentation == term)]
            features[term] = profiles(select(counts), select(inventory), columns)
            signatures[term] = Counter(select(assessments).assessment_type)
        for first, last in pairwise(sorted(features)):
            values = distances(features[first], features[last], first[-1] != last[-1])
            rows.append(dict(module=module, source=first, target=last,
                             changed=int(signatures[first] != signatures[last]), **dict(zip(SCORES, values))))
    result = pd.DataFrame(rows)
    assert np.isfinite(result[SCORES]).all().all()
    return result


def operating_point(train, method):
    best = (0, np.inf)
    for threshold in train[method].unique():
        refs = train.loc[train[method] >= threshold, "changed"]
        tp = int(refs.sum())
        if (len(refs) - tp) * 10 <= len(refs):
            best = max(best, (tp, threshold))
    return best[1]


def run(archive, out):
    counts, inv, checks, courses = read_inputs(archive)
    out.mkdir(parents=True, exist_ok=True)
    full = edges(counts, inv, checks, courses)
    halves = [edges(counts.loc[counts.half == h], inv, checks, courses) for h in (0, 1)]
    summary = {}
    for method in SCORES:
        selected = pd.Series(False, index=full.index)
        for module in full.module.unique():
            mask = full.module.eq(module)
            threshold = operating_point(full.loc[~mask], method)
            selected.loc[mask] = full.loc[mask, method] >= threshold
        matches = int(full.loc[selected, "changed"].sum())
        positives = int(full.changed.sum())
        summary[method] = dict(ap=float(average_precision_score(full.changed, full[method])),
                               selected=int(selected.sum()), tp=matches,
                               fdp=(selected.sum()-matches)/max(1,int(selected.sum())),
                               recall=matches/positives,
                               half_rank_rho=float(spearmanr(halves[0][method], halves[1][method]).statistic))
        full["alert_"+method] = selected.astype(int)
    for i, half in enumerate(halves):
        half.to_csv(out / f"half{i}.csv", index=False)
    full.to_csv(out / "edges.csv", index=False)
    candidate = summary[SCORES[0]]
    passed = all(candidate["ap"] - c["ap"] >= .05 and candidate["recall"] > c["recall"]
                 for k,c in summary.items() if k != SCORES[0]) and candidate["fdp"] <= .10
    report = dict(modules=full.module.nunique(), edges=len(full), positive=int(full.changed.sum()),
                  active_learners=counts.id_student.nunique(), methods=summary, advance=bool(passed))
    (out / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    run(args.archive, args.out)
