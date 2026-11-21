"""Fixed-cohort validation and HLR ablation for the Duolingo recall study."""
import argparse
import hashlib
import importlib.util
import json
import platform
import random
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import minimize

import evaluate as primary

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "validation_protocol.json"


def holdout_frames(archive, original_users):
    """Stream new learners to avoid building a large upstream instance list."""
    buckets = {}
    cols = ["user_id", "delta", "learning_language", "lexeme_string",
            "history_seen", "history_correct", "session_seen", "session_correct"]
    for chunk in pd.read_csv(archive, chunksize=200_000, usecols=cols):
        for uid in set(chunk.user_id.unique()) - buckets.keys():
            digest = hashlib.sha256(uid.encode()).digest()
            buckets[uid] = int.from_bytes(digest[:4], "big") % 100
        bucket = chunk.user_id.map(buckets)
        f = chunk.loc[bucket.between(2, 5)].copy()
        if f.empty:
            continue
        if set(f.user_id) & original_users:
            raise ValueError("Overlapping validation learner")
        f["bucket"] = bucket.loc[f.index]
        f["days"] = f.delta / 86400.
        f["right"] = f.history_correct
        f["wrong"] = f.history_seen - f.history_correct
        f["lexeme"] = f.learning_language + ":" + f.lexeme_string
        f["gold"] = f.session_correct / f.session_seen
        if not f.gold.between(0, 1).all() or f[primary.COLUMNS].isna().any().any():
            raise ValueError("Invalid follow-up data")
        yield f


def fit_hlr(source, rows, seed=42, omit=False, passes=1):
    model = source.SpacedRepetitionModel(lrate=0.001, omit_h_term=omit)
    random.seed(seed)
    for _ in range(passes):
        model.train(rows.copy())
    return model


def predict_hlr(model, rows):
    return np.array([model.predict(row) for row in rows]).T


def calibrate(frame, raw):
    fit = minimize(lambda v: primary.learner_losses(frame, primary.infer(raw, v)).mean(),
                   [0., 1.], bounds=[(-10., 10.), (0., 10.)], method="L-BFGS-B")
    if not fit.success:
        raise ValueError(fit.message)
    return fit.x.tolist()


def bounded_summary(raw, half, source):
    return {"p_lower": np.mean(raw == .0001), "p_upper": np.mean(raw == .9999),
            "h_lower": np.mean(half == source.MIN_HALF_LIFE),
            "h_upper": np.mean(half == source.MAX_HALF_LIFE)}


def contrast(diff):
    rng = np.random.default_rng(42)
    draws = [rng.choice(diff, len(diff)).mean() for _ in range(10000)]
    return {"gain": diff.mean(), "ci95": np.quantile(draws, [.025, .975]).tolist()}


def validate(archive, code, output):
    report = json.loads((ROOT / "run/result.json").read_text())
    protocol = json.loads(primary.PROTOCOL.read_text())
    plan = json.loads(PLAN.read_text())
    for path, expected in [(archive, protocol["dataset_sha256"]), (code, protocol["upstream_sha256"]),
                           (Path(primary.__file__), report["evaluator_sha256"]),
                           (primary.PROTOCOL, report["protocol_sha256"]),
                           (ROOT / "run/result.json", plan["primary_result_sha256"]),
                           (ROOT / "run/predictions.csv.gz", report["predictions_sha256"])]:
        if primary.digest_file(path) != expected:
            raise ValueError(f"Input mismatch for {path}")
    spec = importlib.util.spec_from_file_location("duolingo_hlr", code)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    train, cal, dev, test = primary.load_traces(archive)
    train_rows = primary.hlr_input(train, source, True)
    cal_rows, dev_rows, test_rows = [primary.hlr_input(f, source, False) for f in (cal, dev, test)]
    selected = report["selected"]
    hlr = fit_hlr(source, train_rows)
    depth, rounds = selected["catboost"]["setting"]
    boost = catboost.CatBoostClassifier(loss_function="CrossEntropy", depth=depth, iterations=rounds,
        learning_rate=protocol["catboost_learning_rate"], cat_features=["lexeme"], random_seed=42,
        verbose=False, allow_writing_files=False, thread_count=2)
    boost.fit(train[primary.COLUMNS], train.gold)
    base_cal = selected["hlr"]["calibration"]
    boost_cal = selected["catboost"]["calibration"]
    archived = pd.read_csv(ROOT / "run/predictions.csv.gz")
    np.testing.assert_array_equal(archived.cluster, test.cluster)
    np.testing.assert_allclose(archived.gold, test.gold, atol=1e-14, rtol=0)
    checks = {}
    for name, raw, coeff in [("hlr", predict_hlr(hlr, test_rows)[0], base_cal),
                             ("catboost", boost.predict_proba(test[primary.COLUMNS])[:, 1], boost_cal)]:
        error = np.abs(primary.infer(raw, coeff) - archived[name]).max()
        if not error < 1e-7:
            raise ValueError(f"Reconstruction mismatch for {name}: {error}")
        checks[name] = error
    order_sensitivity = []
    for seed in (42, 43, 44):
        model = hlr if seed == 42 else fit_hlr(source, train_rows, seed)
        raw, half = predict_hlr(model, cal_rows)
        order_sensitivity.append(dict(seed=seed, calibration=calibrate(cal, raw),
                                      bounds=bounded_summary(raw, half, source)))
    best = np.inf
    trials = []
    for passes in (1, 3):
        model = fit_hlr(source, train_rows, omit=True, passes=passes)
        cal_raw = predict_hlr(model, cal_rows)[0]
        dev_raw = predict_hlr(model, dev_rows)[0]
        for coeff in ([0., 1.], calibrate(cal, cal_raw)):
            loss = primary.learner_losses(dev, primary.infer(dev_raw, coeff)).mean()
            trial = dict(passes=passes, calibration=coeff, dev_loss=loss)
            trials.append(trial)
            if loss < best:
                best, ablated, ablation_cal, winning_trial = loss, model, coeff, trial
    constant = cal.groupby("cluster").gold.mean().mean()
    users = set.union(*(set(f.user_id) for f in [train, cal, dev, test]))
    blocks = []
    for f in holdout_frames(archive, users):
        rows = primary.hlr_input(f, source, False)
        raw, half = predict_hlr(hlr, rows)
        ab_raw, ab_half = predict_hlr(ablated, rows)
        boost_raw = boost.predict_proba(f[primary.COLUMNS])[:, 1]
        blocks.append(f[["user_id", "bucket", "gold"]].assign(
            hlr_raw=raw, half=half, hlr=primary.infer(raw, base_cal),
            ablation_raw=ab_raw, ab_half=ab_half, ablation=primary.infer(ab_raw, ablation_cal),
            catboost_raw=boost_raw, catboost=primary.infer(boost_raw, boost_cal), constant=constant))
    scores = pd.concat(blocks, ignore_index=True)
    losses = scores[["user_id", "bucket"]].copy()
    for name in ["constant", "hlr_raw", "hlr", "ablation_raw", "ablation", "catboost_raw", "catboost"]:
        losses[name] = primary.cross_entropy(scores.gold, scores[name])
    learner = losses.groupby(["bucket", "user_id"]).mean()
    diff = learner.hlr - learner.catboost
    bands = pd.cut(scores.hlr_raw, [-.001,.01,.25,.5,.75,.99,1], include_lowest=True)
    profile = scores.groupby(bands, observed=True).agg(sessions=("gold","size"), raw=("hlr_raw","mean"),
        calibrated=("hlr","mean"), observed=("gold","mean"))
    result = dict(python=platform.python_version(), packages=dict(catboost=catboost.__version__,
        pandas=pd.__version__, numpy=np.__version__, scipy=scipy.__version__),
        validation_protocol_sha256=primary.digest_file(PLAN), script_sha256=primary.digest_file(Path(__file__)),
        max_reconstruction_error=checks, rows=len(scores), learners=len(learner), overlapping_users=0,
        order_sensitivity_calibration=order_sensitivity, ablation_trials=trials, ablation_selected=winning_trial,
        calibration_constant=constant, mean_learner_nll=learner.mean().to_dict(),
        hlr_minus_catboost=contrast(diff.to_numpy()), ablation_minus_catboost=contrast((learner.ablation-learner.catboost).to_numpy()),
        hlr_minus_ablation=contrast((learner.hlr-learner.ablation).to_numpy()),
        by_bucket=diff.groupby(level="bucket").agg(["size","mean"]).to_dict("index"),
        hlr_bounds=bounded_summary(scores.hlr_raw, scores.half, source),
        ablation_bounds=bounded_summary(scores.ablation_raw, scores.ab_half, source),
        score_bands={str(b): rec for b, rec in profile.to_dict("index").items()})
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["archive", "upstream_code", "output"]:
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    validate(args.archive, args.upstream_code, args.output)
