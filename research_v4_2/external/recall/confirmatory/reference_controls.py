"""Complete the original ACL comparator table on the sealed, learner-held-out forecast."""
import argparse
import json
import math
import pickle
import random
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import t

import study

FIXED = ["leitner", "pimsleur", "smoothed_history"]
TRAINED = ["hlr_no_lexeme", "hlr_no_lexeme_no_h", "lr_no_lexeme"]
CONFIG = Path(__file__).with_name("reference_protocol.md")


def examples(frame, ref, method, training):
    observed = frame.session_correct / frame.session_seen if training else np.full(len(frame), .5)
    elapsed = frame.delta.to_numpy() / 86400
    rows = []
    for days, seen, right, gold in zip(elapsed, frame.history_seen, frame.history_correct, observed):
        if method == "leitner":
            features = [("diff", 2 * right - seen)]
        elif method == "pimsleur":
            features = [("total", seen)]
        else:
            features = [("right", math.sqrt(1 + right)), ("wrong", math.sqrt(1 + seen - right))]
            if method == "lr":
                features.append(("time", days))
        features.append(("bias", 1.))
        p = ref.pclip(gold)
        h = ref.hclip(-days / math.log2(p)) if training else 1.
        rows.append(ref.Instance(p, days, features, h, 0, "", 0, 0, 0, "", ""))
    return rows


def form(name):
    return name.split("_")[0]


def forecast(model, frame, rows):
    if model is None:
        return (frame.history_correct.to_numpy() + 2) / (frame.history_seen.to_numpy() + 4)
    return np.array([model.predict(row)[0] for row in rows])


def data_pins():
    return {p.name: study.digest(p) for p in [CONFIG, Path(__file__), Path(study.__file__),
                                             study.ARCHIVE, study.REFERENCE]}


def train(out, ref):
    data = study.cohort(10, 13)
    tr, cal, dev = [data.loc[data.bucket.between(lo, hi)] for lo, hi in [(10, 11), (12, 12), (13, 13)]]
    cal_gold = (cal.session_correct / cal.session_seen).to_numpy()
    dev_gold = (dev.session_correct / dev.session_seen).to_numpy()
    wc, wd = study.weights(cal), study.weights(dev)
    best_models = {}
    trials = []
    selected = {}
    for name in FIXED + TRAINED:
        method = form(name)
        cr, dr = (examples(f, ref, method, False) if name != "smoothed_history" else None for f in (cal, dev))
        train_rows = examples(tr, ref, method, True) if name in TRAINED else None
        best = np.inf
        for rate in ([.0003, .001, .003, .01] if name in TRAINED else [None]):
            model = None
            if name != "smoothed_history":
                model = ref.SpacedRepetitionModel(method=method, omit_h_term=name.endswith("_no_h"),
                                                  lrate=rate if rate else .001)
                if train_rows is not None:
                    random.seed(42)
                    model.train(train_rows.copy())
            pc, pdv = forecast(model, cal, cr), forecast(model, dev, dr)
            fit = minimize(lambda ab: np.average(study.loss(cal_gold, study.calibrated(pc, ab)), weights=wc),
                           [0., 1.], bounds=[(-10, 10), (0, 10)], method="L-BFGS-B")
            if not fit.success:
                raise RuntimeError(fit.message)
            for coefs in [[0., 1.], fit.x.tolist()]:
                nll = float(np.average(study.loss(dev_gold, study.calibrated(pdv, coefs)), weights=wd))
                trial = dict(name=name, rate=rate, coefs=coefs, dev_loss=nll)
                trials.append(trial)
                if nll < best:
                    best, selected[name], best_models[name] = nll, trial, model
    model_path = out / "reference_models.pkl"
    with model_path.open("xb") as handle:
        pickle.dump(best_models, handle)
    study.write_json(out / "reference_freeze.json", dict(selected=selected, trials=trials, inputs=data_pins(),
                    models_sha256=study.digest(model_path)))


def score(out, ref):
    seal = json.loads((out / "reference_freeze.json").read_text())
    assert data_pins() == seal["inputs"]
    model_path = out / "reference_models.pkl"
    assert study.digest(model_path) == seal["models_sha256"]
    with model_path.open("rb") as handle:
        models = pickle.load(handle)
    f = study.cohort(14, 17)
    gold = (f.session_correct / f.session_seen).to_numpy()
    row_losses = {}
    for name in FIXED + TRAINED:
        rows = examples(f, ref, form(name), False) if name != "smoothed_history" else None
        pred = forecast(models[name], f, rows)
        row_losses[name] = study.loss(gold, study.calibrated(pred, seal["selected"][name]["coefs"]))
        del rows
    learner = pd.DataFrame(row_losses).groupby([f.bucket, f.user_id]).mean().reset_index()
    learner["learner_ordinal"] = learner.groupby("bucket").cumcount()
    learner = learner.drop(columns="user_id")
    primary = json.loads((out / "result.json").read_text())
    original_losses = out / "learner_losses.csv.gz"
    assert primary["losses_sha256"] == study.digest(original_losses)
    original = pd.read_csv(original_losses)
    keys = ["bucket", "learner_ordinal"]
    pd.testing.assert_frame_equal(original[keys], learner[keys])
    ledger = learner.merge(original, validate="one_to_one", on=keys)
    learner.to_csv(out / "reference_learner_losses.csv.gz", index=False, compression={"method":"gzip","mtime":0})
    candidates = list(primary["contrasts"]) + FIXED + TRAINED
    gains = ledger[candidates].sub(ledger.ensemble, axis=0)
    avg, sem = gains.mean(), gains.sem()
    n, k = len(gains), len(candidates)
    adjusted = study.holm(t.sf((avg - .005) / sem, n - 1))
    widths = t.isf(.025 / k, n - 1) * sem
    contrasts = {name:dict(gain=avg[name], mean_nll=ledger[name].mean(), holm_p_margin=adjusted[i],
                           simultaneous_ci95=[avg[name] - widths[name], avg[name] + widths[name]],
                           pass_margin=bool(adjusted[i] < .05 and avg[name] >= .005))
                 for i, name in enumerate(candidates)}
    study.write_json(out / "reference_result.json", dict(learners=n, rows=len(f), ensemble=ledger.ensemble.mean(),
                     contrasts=contrasts, counts_as_superior=all(c["pass_margin"] for c in contrasts.values()),
                     original_sha256=study.digest(out/"result.json"), freeze_sha256=study.digest(out/"reference_freeze.json"),
                     losses_sha256=study.digest(out/"reference_learner_losses.csv.gz")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["train", "score"])
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    marker = args.out / ("reference_freeze.json" if args.stage == "train" else "reference_result.json")
    if marker.exists():
        raise FileExistsError(marker)
    pins = json.loads((study.ROOT.parent / "protocol.json").read_text())
    if study.digest(study.ARCHIVE) != pins["dataset_sha256"] or study.digest(study.REFERENCE) != pins["upstream_sha256"]:
        raise ValueError("Input digest mismatch")
    (train if args.stage == "train" else score)(args.out, study.load_reference())
