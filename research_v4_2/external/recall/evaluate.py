"""Learner-disjoint comparison on the external Duolingo recall corpus."""
import argparse
import hashlib
import importlib.util
import json
import math
import random
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit

PROTOCOL = Path(__file__).with_name("protocol.json")
COLUMNS = ["days", "right", "wrong", "lexeme"]


def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_traces(path):
    selected = []
    buckets = {}
    for chunk in pd.read_csv(path, chunksize=200_000, usecols=[
        "user_id", "delta", "learning_language", "lexeme_string", "history_seen",
        "history_correct", "session_seen", "session_correct"]):
        for uid in set(chunk.user_id.unique()) - buckets.keys():
            d = hashlib.sha256(uid.encode()).digest()
            included = int.from_bytes(d[:4], "big") % 100 < 2
            buckets[uid] = int.from_bytes(d[4:8], "big") % 100 if included else -1
        part = chunk.loc[chunk.user_id.map(buckets) >= 0].copy()
        part["bucket"] = part.user_id.map(buckets)
        selected.append(part)
    frame = pd.concat(selected, ignore_index=True)
    frame["days"] = frame.delta / 86400.
    frame["right"] = frame.history_correct
    frame["wrong"] = frame.history_seen - frame.history_correct
    frame["lexeme"] = frame.learning_language + ":" + frame.lexeme_string
    frame["gold"] = frame.session_correct / frame.session_seen
    if not frame.gold.between(0, 1).all() or frame[COLUMNS].isna().any().any():
        raise ValueError("Invalid recall targets or predictors")
    frame["cluster"] = pd.factorize(frame.user_id, sort=True)[0]
    return [frame.loc[frame.bucket.between(lo, hi)].reset_index(drop=True)
            for lo, hi in [(0,59),(60,69),(70,84),(85,99)]]


def hlr_input(frame, source, training):
    rows = []
    for r in frame.itertuples():
        fv = [("right", math.sqrt(1+r.right)), ("wrong", math.sqrt(1+r.wrong)),
              ("bias", 1.), (r.lexeme, 1.)]
        p = source.pclip(r.gold) if training else 0.5
        h = source.hclip(-r.days / math.log2(p)) if training else 1.
        rows.append(source.Instance(p, r.days, fv, h, 0, "", 0, 0, 0, "", ""))
    return rows


def cross_entropy(y, p):
    p = np.clip(p, 1e-8, 1-1e-8)
    return -(y * np.log(p) + (1-y) * np.log1p(-p))


def learner_losses(frame, p):
    return pd.Series(cross_entropy(frame.gold, p)).groupby(frame.cluster).mean().to_numpy()


def infer(raw, calibration):
    a, b = calibration
    return expit(a + b*logit(np.clip(raw, 1e-8, 1-1e-8)))


def evaluate(archive, code, output):
    protocol = json.loads(PROTOCOL.read_text())
    if digest_file(archive) != protocol["dataset_sha256"] or digest_file(code) != protocol["upstream_sha256"]:
        raise ValueError("Inputs differ from the protocol")
    spec = importlib.util.spec_from_file_location("duolingo_hlr", code)
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    train, cal, dev, test = load_traces(archive)
    h_train, h_cal, h_dev, h_test = [hlr_input(f, upstream, training=f is train) for f in [train, cal, dev, test]]
    predictions = test[["cluster","gold"]].copy()
    trials, selected = [], {}
    for family, settings in [("hlr", protocol["hlr_learning_rates"]), ("catboost", protocol["catboost_settings"])]:
        best_score = math.inf
        for setting in settings:
            if family == "hlr":
                model = upstream.SpacedRepetitionModel(method="hlr", lrate=setting)
                random.seed(protocol["seed"])
                model.train(h_train.copy())
                cal_p, dev_p = [np.array([model.predict(i)[0] for i in records]) for records in (h_cal,h_dev)]
            else:
                depth, rounds = setting
                model = catboost.CatBoostClassifier(loss_function="CrossEntropy", depth=depth,
                    iterations=rounds, learning_rate=protocol["catboost_learning_rate"], cat_features=["lexeme"],
                    verbose=False, allow_writing_files=False, random_seed=protocol["seed"], thread_count=2)
                model.fit(train[COLUMNS], train.gold)
                cal_p, dev_p = [model.predict_proba(f[COLUMNS])[:,1] for f in (cal,dev)]
            fit = minimize(lambda v: learner_losses(cal, infer(cal_p,v)).mean(),
                           [0.,1.], bounds=[(-10.,10.),(0.,10.)], method="L-BFGS-B")
            if not fit.success:
                raise ValueError(f"Calibration did not converge: {fit.message}")
            for calibration in ([0.,1.], fit.x.tolist()):
                score = learner_losses(dev, infer(dev_p,calibration)).mean()
                trials.append(dict(family=family, setting=setting, calibration=calibration, dev_loss=score))
                if score < best_score:
                    best_score, best_model, best_cal = score, model, calibration
                    selected[family] = trials[-1]
        if family == "hlr":
            raw = np.array([best_model.predict(i)[0] for i in h_test])
        else:
            raw = best_model.predict_proba(test[COLUMNS])[:,1]
        predictions[family] = infer(raw,best_cal)
    scores = {n: learner_losses(test,predictions[n]) for n in ("hlr","catboost")}
    diff = scores["hlr"] - scores["catboost"]
    rng = np.random.default_rng(protocol["seed"])
    samples = [rng.choice(diff, len(diff), replace=True).mean() for _ in range(10000)]
    exceed = sum(abs(np.mean(diff * rng.choice([-1,1],len(diff)))) >= abs(diff.mean()) for _ in range(10000))
    ci = np.quantile(samples, [.025,.975]).tolist()
    p = (1+int(exceed))/10001
    win = diff.mean() >= protocol["margin_nats"] and ci[0] > 0 and p < .05
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output/"predictions.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    report = dict(partitions={n:dict(rows=len(f),learners=f.cluster.nunique()) for n,f in
                  zip(("train","cal","dev","test"),(train,cal,dev,test))}, mean_learner_nll={n:s.mean() for n,s in scores.items()},
                  gain=diff.mean(), ci95=ci, p=p, selected=selected, trials=trials,
                  catboost_version=catboost.__version__, evaluator_sha256=digest_file(Path(__file__)),
                  protocol_sha256=digest_file(PROTOCOL), predictions_sha256=digest_file(output/"predictions.csv.gz"),
                  decision="SINGLE_DATASET_IMPROVEMENT" if win else "NO_DEMONSTRATED_IMPROVEMENT")
    (output/"result.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("archive","upstream_code","output"):
        parser.add_argument(arg,type=Path)
    args = parser.parse_args()
    evaluate(args.archive,args.upstream_code,args.output)
