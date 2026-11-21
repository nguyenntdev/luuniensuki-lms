"""Evaluate a fixed candidate and two published baselines with nested course splits."""
import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
from threadpoolctl import threadpool_limits

PROTOCOL = Path(__file__).with_name("protocol.json")


def fit_model(name, setting, protocol):
    if name == "spline":
        return make_pipeline(StandardScaler(), SplineTransformer(n_knots=4, include_bias=False),
                             LogisticRegression(C=setting, max_iter=2000))
    depth, rounds = setting
    common = dict(learning_rate=protocol["tree_learning_rate"], random_seed=protocol["seed"])
    if name == "catboost":
        return catboost.CatBoostClassifier(depth=depth, iterations=rounds, **common,
                                           thread_count=1, verbose=False, allow_writing_files=False)
    return xgboost.XGBClassifier(max_depth=depth, n_estimators=rounds, tree_method="hist",
                                 learning_rate=common["learning_rate"], random_state=common["random_seed"],
                                 n_jobs=1, eval_metric="logloss")


def loss(y, prob):
    p = np.clip(prob, 1e-12, 1 - 1e-12)
    return -np.where(y, np.log(p), np.log1p(-p))


def nested_predictions(x, y, groups, protocol):
    predictions = pd.DataFrame({"course": groups, "gold": y})
    trials = []
    for course in sorted(set(groups)):
        train, held = np.flatnonzero(groups != course), np.flatnonzero(groups == course)
        folds = list(GroupKFold(3).split(train, groups=groups[train]))
        for name in ("spline", "catboost", "xgboost"):
            grid = protocol["candidate_C" if name == "spline" else "tree_settings"]
            errors = []
            for setting in grid:
                scores = []
                for tr, va in folds:
                    a, b = train[tr], train[va]
                    model = fit_model(name, setting, protocol).fit(x[a], y[a])
                    dev = pd.Series(loss(y[b], model.predict_proba(x[b])[:, 1]))
                    scores.extend(dev.groupby(groups[b]).mean().tolist())
                errors.append(float(np.mean(scores)))
            setting = grid[int(np.argmin(errors))]
            trials.append(dict(course=int(course), model=name, dev_losses=errors, chosen=setting))
            model = fit_model(name, setting, protocol).fit(x[train], y[train])
            predictions.loc[held, name] = model.predict_proba(x[held])[:, 1]
    assert predictions.notna().all().all()
    return predictions, trials


def summarize(preds, protocol):
    metrics = pd.DataFrame({name: loss(preds.gold, preds[name]) for name in ("spline", "catboost", "xgboost")})
    means = metrics.groupby(preds.course).mean()
    rng = np.random.default_rng(protocol["seed"])
    indices = rng.integers(len(means), size=(10000, len(means)))
    signs = np.array(list(product((-1, 1), repeat=len(means))), dtype=np.int8)
    contrasts = {}
    for name in ("catboost", "xgboost"):
        diffs = (means[name] - means.spline).to_numpy()
        ci = np.quantile(diffs[indices].mean(axis=1), [.025, .975])
        p = np.mean(np.abs(signs @ diffs) >= abs(diffs.sum()) - 1e-12)
        contrasts[name] = dict(gain=float(diffs.mean()), ci95=ci.tolist(), p=float(p))
    adjusted = 0.
    for i, row in enumerate(sorted(contrasts.values(), key=lambda r: r["p"])):
        adjusted = max(adjusted, min(1., (2-i)*row["p"]))
        row["holm_p"] = adjusted
    win = all(r["gain"] >= protocol["margin"] and r["ci95"][0] > 0 and r["holm_p"] < .05
              for r in contrasts.values())
    return dict(n=len(preds), courses=len(means), mean_course_nll=means.mean().to_dict(),
                contrasts=contrasts, decision="SINGLE_DATASET_IMPROVEMENT" if win else "NO_DEMONSTRATED_IMPROVEMENT")


def evaluate(archive, output):
    protocol = json.loads(PROTOCOL.read_text())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != protocol["source_sha256"]:
        raise ValueError("Input does not match the frozen snapshot")
    rows = pd.read_csv(archive, sep=";")
    frame = rows.loc[rows.Target.isin(["Graduate", "Dropout"])]
    x = frame[protocol["features"]].copy()
    enrolled = x["Curricular units 1st sem (enrolled)"].clip(lower=1)
    for col in ("approved", "evaluations"):
        x[col + "_per_enrolled"] = x[f"Curricular units 1st sem ({col})"] / enrolled
    with threadpool_limits(limits=1):
        predictions, trials = nested_predictions(x.to_numpy(), (frame.Target == "Dropout").to_numpy(),
                                                 frame.Course.to_numpy(), protocol)
        report = summarize(predictions, protocol)
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output / "predictions.csv", index=False)
    (output / "dev_trials.json").write_text(json.dumps(trials, indent=2) + "\n")
    report.update(protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
                  evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  predictions_sha256=hashlib.sha256((output / "predictions.csv").read_bytes()).hexdigest(),
                  versions=dict(catboost=catboost.__version__, xgboost=xgboost.__version__, sklearn=sklearn.__version__))
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    evaluate(args.archive, args.output)
