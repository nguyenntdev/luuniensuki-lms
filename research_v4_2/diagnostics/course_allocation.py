"""Exploratory cross-course allocation audit on the UCI 697 public snapshot."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

SOURCE_SHA = "e90e55fd65ec462ae283ebeb2cca409319e3460ed898d8754f62fb35cc83a65d"
FEATURES = [
    "Admission grade", "Previous qualification (grade)", "Application order",
    "Curricular units 1st sem (enrolled)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (evaluations)",
]


def score_courses(frame, model):
    scores = np.full(len(frame), np.nan)
    for course in frame.Course.unique():
        held = frame.Course == course
        model.fit(frame.loc[~held, FEATURES], frame.loc[~held, "dropout"])
        scores[held] = model.predict_proba(frame.loc[held, FEATURES])[:, 1]
    assert np.isfinite(scores).all()
    return scores


def compare_allocations(frame):
    """Reserve proportional seats by largest remainder. Compare on identical scores."""
    groups = frame.Gender.to_numpy()
    gold = frame.dropout.to_numpy()
    order = np.lexsort((frame.tie.to_numpy(), -frame.score.to_numpy()))
    k = max(1, len(order) // 10)
    labels, sizes = np.unique(groups, return_counts=True)
    quotas, residues = np.divmod(k * sizes, len(frame))
    for j in np.argsort(-residues, kind="stable")[:k - quotas.sum()]:
        quotas[j] += 1
    quota_order = np.concatenate([order[groups[order] == g][:q] for g, q in zip(labels, quotas)])
    assert len(set(quota_order)) == k
    result = {"n": len(frame), "k": k, "seats_changed": len(set(order[:k]) - set(quota_order))}
    for name, selected in (("risk", order[:k]), ("quota", quota_order)):
        result[name] = {"captured": int(gold[selected].sum()), "by_group": {}}
        for g in labels:
            result[name]["by_group"][str(g)] = {
                "captured": int(gold[selected][groups[selected] == g].sum()),
                "positives": int(gold[groups == g].sum()),
            }
    return result


def audit(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Unexpected UCI 697 archive")
    source = pd.read_csv(path, sep=";")
    if set(source.Target) != {"Enrolled", "Dropout", "Graduate"}:
        raise ValueError("Unexpected outcome labels")
    frame = source.loc[source.Target != "Enrolled"].copy()
    frame["dropout"] = frame.Target == "Dropout"
    frame["tie"] = np.random.default_rng(42).permutation(len(frame))
    result = {"dataset_sha256": SOURCE_SHA, "sklearn": sklearn.__version__,
              "source_rows": len(source), "resolved_rows": len(frame), "features": FEATURES,
              "folds": "leave one course out, no tuning", "models": {}}
    for name, model in [
        ("logistic", make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))),
        ("boosting", HistGradientBoostingClassifier(max_iter=100, random_state=42)),
    ]:
        frame["score"] = score_courses(frame, model)
        courses = {str(course): compare_allocations(rows) for course, rows in frame.groupby("Course")}
        result["models"][name] = {
            "auc": roc_auc_score(frame.dropout, frame.score),
            "nll": log_loss(frame.dropout, frame.score),
            "courses": courses,
            "binding_courses": sum(r["seats_changed"] > 0 for r in courses.values()),
            "review_slots": sum(r["k"] for r in courses.values()),
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    with threadpool_limits(limits=1):
        print(json.dumps(audit(parser.parse_args().archive), indent=2, allow_nan=False))
