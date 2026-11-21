"""Secondary logistic comparators evaluated on new hash buckets 6 through 9."""
import argparse
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import sklearn
from scipy.sparse import csr_matrix, hstack, vstack
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder

import evaluate as primary
from validate import ROOT, calibrate, contrast


def new_cohort(archive):
    chunks = []
    buckets = {}
    cols = ["user_id", "delta", "history_correct", "history_seen", "lexeme_string",
            "learning_language", "session_correct", "session_seen"]
    for f in pd.read_csv(archive, chunksize=200_000, usecols=cols):
        for uid in set(f.user_id.unique()) - buckets.keys():
            digest = hashlib.sha256(uid.encode()).digest()
            buckets[uid] = int.from_bytes(digest[:4], "big") % 100
        chunks.append(f.loc[f.user_id.map(buckets).between(6, 9)])
    f = pd.concat(chunks, ignore_index=True)
    return f.assign(days=f.delta/86400., right=f.history_correct, wrong=f.history_seen-f.history_correct,
                    lexeme=f.learning_language+":"+f.lexeme_string, gold=f.session_correct/f.session_seen,
                    cluster=pd.factorize(f.user_id, sort=True)[0])


def lr_rows(frame, source, training=False):
    rows = primary.hlr_input(frame, source, training)
    for row in rows:
        row.fv.insert(2, ("time", row.t))
    return rows


def design(frame, encoder):
    history = np.log1p(frame[["days", "right", "wrong"]].to_numpy())
    return hstack([csr_matrix(history), encoder.transform(frame[["lexeme"]])], format="csr")


def compare(archive, code, output):
    prot = json.loads(primary.PROTOCOL.read_text())
    for path, digest in [(archive, prot["dataset_sha256"]), (code, prot["upstream_sha256"])]:
        if primary.digest_file(path) != digest:
            raise ValueError(f"Unexpected input {path}")
    spec = importlib.util.spec_from_file_location("duolingo_hlr", code)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    train, cal, dev, original_test = primary.load_traces(archive)
    selected = json.loads((ROOT / "run/result.json").read_text())["selected"]["catboost"]
    depth, rounds = selected["setting"]
    boost = catboost.CatBoostClassifier(loss_function="CrossEntropy", depth=depth, iterations=rounds,
        learning_rate=.05, cat_features=["lexeme"], random_seed=42, verbose=False,
        allow_writing_files=False, thread_count=2)
    boost.fit(train[primary.COLUMNS], train.gold)
    old_predictions = pd.read_csv(ROOT / "run/predictions.csv.gz")
    old_boost = primary.infer(boost.predict_proba(original_test[primary.COLUMNS])[:,1], selected["calibration"])
    np.testing.assert_allclose(old_predictions.catboost, old_boost, atol=1e-7, rtol=0)
    train_rows = lr_rows(train, source, True)
    cal_rows, dev_rows = lr_rows(cal, source), lr_rows(dev, source)
    trials = []
    best = np.inf
    for lr in prot["hlr_learning_rates"]:
        model = source.SpacedRepetitionModel(method="lr", lrate=lr)
        random.seed(42)
        model.train(train_rows.copy())
        cal_p, dev_p = [np.array([model.predict(i)[0] for i in rows]) for rows in (cal_rows, dev_rows)]
        for coeff in ([0.,1.], calibrate(cal, cal_p)):
            loss = primary.learner_losses(dev, primary.infer(dev_p, coeff)).mean()
            trial = dict(lrate=lr, calibration=coeff, dev_loss=loss)
            trials.append(trial)
            if loss < best:
                best, author, author_choice = loss, model, trial
    encoder = OneHotEncoder(handle_unknown="ignore")
    encoder.fit(train[["lexeme"]])
    x = design(train, encoder)
    # Weighted binary copies reproduce the exact cross-entropy of a fractional target.
    w = 1. / train.groupby("cluster").cluster.transform("size")
    w = w / w.mean()
    labels = np.repeat([0., 1.], len(train))
    weight = np.r_[w*(1.-train.gold), w*train.gold]
    linear = LogisticRegression(C=1., solver="lbfgs", max_iter=3000, tol=1e-9)
    linear.fit(vstack([x,x]), labels, sample_weight=weight)
    if linear.n_iter_[0] >= linear.max_iter:
        raise RuntimeError("Logistic regression did not converge")
    cal_p, dev_p = [linear.predict_proba(design(f, encoder))[:,1] for f in (cal, dev)]
    linear_trials = []
    for coeff in ([0.,1.], calibrate(cal, cal_p)):
        loss = primary.learner_losses(dev, primary.infer(dev_p, coeff)).mean()
        linear_trials.append(dict(calibration=coeff, dev_loss=loss))
    linear_choice = min(linear_trials, key=lambda t: t["dev_loss"])

    f = new_cohort(archive)
    if set(f.user_id).intersection(set.union(*(set(a.user_id) for a in (train, cal, dev, original_test)))):
        raise ValueError("Learner overlap")
    if not f.gold.between(0,1).all() or f[primary.COLUMNS].isna().any().any():
        raise ValueError("Invalid secondary cohort")
    raw = [author.predict(i)[0] for i in lr_rows(f, source)]
    predictions = dict(author_lr=primary.infer(raw, author_choice["calibration"]),
        log_feature_lr=primary.infer(linear.predict_proba(design(f,encoder))[:,1],linear_choice["calibration"]),
        catboost=primary.infer(boost.predict_proba(f[primary.COLUMNS])[:,1], selected["calibration"]))
    losses = {name: primary.learner_losses(f,p) for name,p in predictions.items()}
    report = dict(rows=len(f), learners=f.cluster.nunique(), original_overlap=0,
        script_sha256=primary.digest_file(Path(__file__)),
        validation_helpers_sha256=primary.digest_file(ROOT/"validate.py"),
        comparator_protocol_sha256=primary.digest_file(ROOT/"comparator_protocol.json"),
        sklearn_version=sklearn.__version__, author_trials=trials, author_selected=author_choice,
        linear_trials=linear_trials, linear_selected=linear_choice, linear_iterations=int(linear.n_iter_[0]),
        mean_learner_nll={k:v.mean() for k,v in losses.items()},
        comparator_minus_catboost={k:contrast(v-losses["catboost"]) for k,v in losses.items() if k != "catboost"})
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["archive","upstream_code","output"]:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    compare(args.archive, args.upstream_code, args.output)
