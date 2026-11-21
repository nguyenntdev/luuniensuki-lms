"""Decompose fixed-model AUC into eligible and ineligible case-control pairs."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evaluate import ARCHIVE, FEATURES, KEY


def decompose(scores, outcomes, eligible):
    y = np.asarray(outcomes, dtype=bool)
    scores = np.asarray(scores)
    groups = {"active": np.asarray(eligible, dtype=bool), "exited": ~np.asarray(eligible, dtype=bool)}
    total = int(y.sum()) * int((~y).sum())
    contributions = []
    for pos, pos_mask in groups.items():
        high = scores[y & pos_mask]
        for neg, neg_mask in groups.items():
            low = np.sort(scores[~y & neg_mask])
            count = len(high) * len(low)
            if count:
                # Each lower score contributes one win and each tied score half a win.
                wins = (low.searchsorted(high, side="left") + low.searchsorted(high, side="right")).sum() / 2
                contributions.append(dict(positive=pos, negative=neg, pairs=count, auc=float(wins/count)))
    pooled = roc_auc_score(y, scores)
    reconstructed = sum(v["auc"] * v["pairs"] for v in contributions) / total
    if sum(v["pairs"] for v in contributions) != total or not np.isclose(reconstructed, pooled):
        raise ValueError("Pair contributions do not recover the full AUC")
    return {"all_auc": pooled, "eligible_auc": roc_auc_score(y[eligible], scores[eligible]),
            "pair_strata": contributions}


def run(archive_path):
    with archive_path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ARCHIVE:
            raise ValueError("Unexpected OULAD archive")
    with zipfile.ZipFile(archive_path) as archive:
        roster = pd.read_csv(archive.open("studentInfo.csv")).merge(
            pd.read_csv(archive.open("studentRegistration.csv"), na_values=["?"]), on=KEY, validate="one_to_one")
        clicks = pd.read_csv(archive.open("studentVle.csv"), dtype={"code_module": "category",
                             "code_presentation": "category", "id_student": "int32",
                             "id_site": "int32", "date": "int16", "sum_click": "int32"})
    reports = []
    for day in (14, 56, 60):
        activity = clicks.loc[clicks.date.between(0, day)].groupby(KEY, observed=True).agg(
            clicks=("sum_click", "sum"), days=("date", "nunique"), last=("date", "max"),
            sites=("id_site", "nunique"))
        data = roster.loc[roster.date_registration <= day].merge(activity, on=KEY, how="left",
                                                                 validate="one_to_one")
        data["recency"] = day - data["last"].fillna(-1)
        data[FEATURES] = data[FEATURES].fillna(0)
        test = data.code_presentation == "2014J"
        train = ~test & ~data.id_student.isin(data.loc[test, "id_student"])
        eligible = (data.date_unregistration.isna() | (data.date_unregistration > day))[test].to_numpy()
        for label, y in (("withdrawal", data.final_result == "Withdrawn"),
                         ("unsuccessful", data.final_result.isin(["Fail", "Withdrawn"]))):
            for name, model in (("logistic", make_pipeline(StandardScaler(), LogisticRegression())),
                                ("catboost", CatBoostClassifier(iterations=200, depth=4, learning_rate=.05,
                                 random_seed=42, verbose=False, thread_count=2, allow_writing_files=False))):
                model.fit(data.loc[train, FEATURES], y[train])
                p = model.predict_proba(data.loc[test, FEATURES])[:, 1]
                reports.append(dict(day=day, target=label, model=name, test=int(test.sum()),
                                    eligible=int(eligible.sum()), **decompose(p, y[test], eligible)))
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(run(parser.parse_args().archive), indent=2, allow_nan=False))
