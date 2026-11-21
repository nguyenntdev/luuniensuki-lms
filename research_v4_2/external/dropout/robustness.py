"""Refit the primary model families under alternate targets and a later UK cohort."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits

from evaluate import PROTOCOL, fit_model

ROOT = Path(__file__).parent
P = json.loads(PROTOCOL.read_text())
NAMES = ("spline", "catboost", "xgboost")
CLASSES = ["Dropout", "Enrolled", "Graduate"]
OU_HASH = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
KEY = ["code_module", "code_presentation", "id_student"]


def verify(path, digest):
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Unexpected snapshot: {path}")


def predict(name, setting, x, y, train, test):
    shuffled = np.random.default_rng(P["seed"]).permutation(train)
    model = fit_model(name, setting, P)
    if name == "xgboost" and len(np.unique(y)) == 3:
        model.set_params(eval_metric="mlogloss")
    model.fit(x[shuffled], y[shuffled])
    return model.predict_proba(x[test]).astype(float)


def portugal(path, output):
    verify(path, P["source_sha256"])
    frame = pd.read_csv(path, sep=";")
    x = frame[P["features"]].copy()
    for col in ("approved", "evaluations"):
        x[col + "_ratio"] = x[f"Curricular units 1st sem ({col})"] / x[
            "Curricular units 1st sem (enrolled)"].clip(lower=1)
    gold = pd.Categorical(frame.Target, categories=CLASSES).codes
    assert min(gold) == 0
    result = pd.DataFrame(dict(row=frame.index, course=frame.Course, target=frame.Target))
    trials = json.loads((ROOT / "run/dev_trials.json").read_text())
    settings = {(r["course"], r["model"]): r["chosen"] for r in trials}
    for course in sorted(frame.Course.unique()):
        train = np.flatnonzero(frame.Course != course)
        held = np.flatnonzero(frame.Course == course)
        for name in (*NAMES, "prior"):
            if name == "prior":
                prob = np.tile(np.bincount(gold[train]) / len(train), (len(held), 1))
            else:
                prob = predict(name, settings[course, name], x.to_numpy(), gold, train, held)
            for j, label in enumerate(CLASSES):
                result.loc[held, f"{name}_{label}"] = prob[:, j]
    result.to_csv(output / "portugal_three_status.csv.gz", index=False, compression=dict(method="gzip", mtime=0))


def britain(path, output):
    verify(path, OU_HASH)
    with ZipFile(path) as archive:
        info = pd.read_csv(archive.open("studentInfo.csv")).reset_index(names="row")
        reg = pd.read_csv(archive.open("studentRegistration.csv"), na_values=["?"])
    data = info.merge(reg, on=KEY, validate="one_to_one")
    assert len(data) == len(info) == len(reg)
    final_ids = set(info.loc[info.code_presentation.eq("2014J"), "id_student"])
    eligible = data.date_registration.le(0) & ~data.date_unregistration.le(0)
    data = data.loc[eligible].reset_index(drop=True)
    past = data.code_presentation.isin(["2013B", "2013J"]) & ~data.id_student.isin(final_ids)
    dev = past & data.code_presentation.eq("2013J")
    fit = past & data.code_presentation.eq("2013B") & ~data.id_student.isin(data.loc[dev, "id_student"])
    train, validation, full, test = (np.flatnonzero(mask) for mask in
        (fit, dev, past, data.code_presentation.eq("2014J")))
    assert set(data.final_result) == {"Withdrawn", "Pass", "Fail", "Distinction"}
    features = data.assign(lead=-data.date_registration)[["lead", "num_of_prev_attempts", "studied_credits"]]
    assert features.notna().all().all()
    x = features.to_numpy()
    y = data.final_result.eq("Withdrawn").astype(int).to_numpy()
    result = data.loc[test, ["row", "code_module", "final_result"]].copy()
    result["prior"] = y[full].mean()
    audit = dict(eligible_2013_before_purge=int(data.code_presentation.str.startswith("2013").sum()),
                 fit=len(train), validation=len(validation), refit=len(full), test=len(test),
                 test_learners=int(data.loc[test, "id_student"].nunique()), tuning={})
    for name in NAMES:
        grid = P["candidate_C" if name == "spline" else "tree_settings"]
        losses = []
        for setting in grid:
            prob = predict(name, setting, x, y, train, validation)
            scores = []
            for module in data.loc[validation, "code_module"].unique():
                rows = data.loc[validation, "code_module"].eq(module).to_numpy()
                scores.append(log_loss(y[validation][rows], prob[rows, 1], labels=[0, 1]))
            losses.append(float(np.mean(scores)))
        setting = grid[int(np.argmin(losses))]
        audit["tuning"][name] = dict(grid=grid, losses=losses, chosen=setting)
        result[name] = predict(name, setting, x, y, full, test)[:, 1]
    result.to_csv(output / "uk_later_cohort.csv.gz", index=False, compression=dict(method="gzip", mtime=0))
    (output / "uk_development.json").write_text(json.dumps(audit, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("portugal", type=Path)
    parser.add_argument("oulad", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        portugal(args.portugal, args.output)
        britain(args.oulad, args.output)
