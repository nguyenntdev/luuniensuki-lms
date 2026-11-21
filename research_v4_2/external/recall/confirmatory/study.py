"""Train and seal models, or evaluate a previously sealed fit."""
import argparse
import hashlib
import importlib.util
import json
import math
import pickle
import platform
import random
import sys
from pathlib import Path

import catboost
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.optimize import minimize
from scipy.sparse import csr_matrix, hstack
from scipy.special import expit, logit
from scipy.stats import t
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
ARCHIVE = Path("private_data/raw/duolingo-hlr/traces.csv.gz")
REFERENCE = ARCHIVE.with_name("experiment.py")
BASE = ["days", "right", "wrong", "lexeme"]
CATS = ["lexeme", "course", "lemma", "pos"]
RICH = ["log_days", "log_right", "log_wrong", "item_history_rate", "log_gap",
        "prior_user", "recent_user", "last_user", "log_user_exposure",
        "prior_item", "last_item", "log_item_exposure", "hour_sin", "hour_cos",
        "item_difficulty"]
COMPONENTS = ["matched_catboost", "hist_boost", "history_logistic", "history_hlr"]
THREADS = 3


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def load_reference():
    spec = importlib.util.spec_from_file_location("duolingo_reference", REFERENCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def cohort(start, stop):
    cols = ["user_id", "timestamp", "session_seen", "session_correct", "history_seen",
            "history_correct", "delta", "learning_language", "ui_language", "lexeme_string"]
    selected, buckets = [], {}
    for chunk in pd.read_csv(ARCHIVE, usecols=cols, chunksize=250000):
        for uid in set(chunk.user_id.unique()) - buckets.keys():
            buckets[uid] = int.from_bytes(hashlib.sha256(uid.encode()).digest()[:4], "big") % 100
        b = chunk.user_id.map(buckets)
        selected.append(chunk.loc[b.between(start, stop)].assign(bucket=b))
    return pd.concat(selected, ignore_index=True)


def histories(frame, keys, prefix):
    keys = keys + ["timestamp"]
    blocks = frame.groupby(keys, sort=True, as_index=False).agg(
        seen=("session_seen", "sum"), correct=("session_correct", "sum"))
    grouped = blocks.groupby(keys[:-1], sort=False)
    seen = grouped.seen.cumsum() - blocks.seen
    correct = grouped.correct.cumsum() - blocks.correct
    blocks["prior_" + prefix] = (correct + 4.5) / (seen + 5)
    blocks["log_" + prefix + "_exposure"] = np.log1p(seen)
    blocks["rate"] = blocks.correct / blocks.seen
    blocks["last_" + prefix] = grouped.rate.shift().fillna(.9)
    if prefix == "user":
        blocks["log_gap"] = np.log1p(grouped.timestamp.diff().fillna(0) / 3600)
        blocks["recent_user"] = grouped.rate.transform(
            lambda rates: rates.ewm(alpha=.3, adjust=False).mean().shift()).fillna(.9)
    return frame.merge(blocks.drop(columns=["rate", "seen", "correct"]), on=keys,
                       how="left", validate="many_to_one", sort=False)


def features(frame):
    f = frame.copy()
    f["course"] = f.ui_language + "/" + f.learning_language
    f["lexeme"] = f.learning_language + ":" + f.lexeme_string
    f["lemma"] = f.learning_language + ":" + f.lexeme_string.str.split("<").str[0]
    f["pos"] = f.lexeme_string.str.extract(r"<([^>]+)>", expand=False).fillna("_")
    f["days"] = f.delta / 86400
    f["right"] = f.history_correct
    f["wrong"] = f.history_seen - f.history_correct
    for col in ["days", "right", "wrong"]:
        f["log_" + col] = np.log1p(f[col])
    f["item_history_rate"] = (f.right + 4.5) / (f.history_seen + 5)
    phase = (f.timestamp % 86400) * (2 * np.pi / 86400)
    f["hour_sin"], f["hour_cos"] = np.sin(phase), np.cos(phase)
    f["gold"] = f.session_correct / f.session_seen
    if not f.gold.between(0, 1).all() or (f.wrong < 0).any():
        raise ValueError("Invalid session history or target")
    return histories(histories(f, ["user_id"], "user"), ["user_id", "lexeme"], "item")


def lookup(train):
    stats = train.groupby("lexeme").gold.agg(["sum", "size"])
    prior = train.gold.mean()
    return ((stats["sum"] + 20 * prior) / (stats["size"] + 20)).to_dict(), prior


def encode(f, table):
    return f.lexeme.map(table[0]).fillna(table[1])


def weights(f):
    w = 1 / f.groupby("user_id").user_id.transform("size").to_numpy()
    return w / w.mean()


def loss(y, pred):
    p = np.clip(pred, 1e-8, 1 - 1e-8)
    return -y * np.log(p) - (1 - y) * np.log1p(-p)


def sparse_design(f, enriched, fitted=None):
    cols = RICH if enriched else ["log_days", "log_right", "log_wrong"]
    cats = CATS if enriched else ["lexeme"]
    if fitted is None:
        fitted = StandardScaler().fit(f[cols]), OneHotEncoder(handle_unknown="ignore").fit(f[cats])
    scale, encoder = fitted
    x = hstack([csr_matrix(np.ones((len(f), 1))), csr_matrix(scale.transform(f[cols])),
                encoder.transform(f[cats])], format="csr")
    return x, fitted


def linear_prob(x, coef, days, hazard):
    eta = x @ coef
    if hazard:
        z = np.clip(np.log(np.maximum(days, 1/86400)) + np.log(np.log(2)) - eta, -20, 4)
        return np.exp(-np.exp(z))
    return expit(eta)


def fit_linear(f, enriched, hazard, penalty):
    x, design = sparse_design(f, enriched)
    days, y, w = f.days.to_numpy(), f.gold.to_numpy(), weights(f)
    def objective(beta):
        pred = linear_prob(x, beta, days, hazard)
        if hazard:
            z = np.log(np.maximum(days, 1/86400)) + np.log(np.log(2)) - x @ beta
            h = np.exp(np.clip(z, -20, 4))
            grad = (pred - y) * h / (-np.expm1(-h)) * ((z > -20) & (z < 4))
            nll = y * h - (1 - y) * np.log(-np.expm1(-h))
        else:
            grad = pred - y
            nll = np.logaddexp(0, x @ beta) - y * (x @ beta)
        value = w @ nll + .5 * penalty * (beta[1:] @ beta[1:])
        derivative = np.asarray(x.T @ (w * grad))
        derivative[1:] += penalty * beta[1:]
        return value, derivative
    result = minimize(objective, np.zeros(x.shape[1]), jac=True, method="L-BFGS-B",
                      options={"maxiter":1800, "ftol":1e-10})
    if not result.success:
        raise RuntimeError(result.message)
    return design, result.x


def author_rows(f, ref, family, train):
    rows = []
    for r in f.itertuples():
        fv = [("right", math.sqrt(1+r.right)), ("wrong", math.sqrt(1+r.wrong)),
              ("bias", 1.), (r.lexeme, 1.)]
        if family == "author_lr":
            fv.insert(2, ("time", r.days))
        p = ref.pclip(r.gold) if train else .5
        h = ref.hclip(-r.days/math.log2(p)) if train else 1.
        rows.append(ref.Instance(p, r.days, fv, h, 0, "", 0, 0, 0, "", ""))
    return rows


def fit(f, name, setting, ref):
    if name == "constant":
        return np.average(f.gold, weights=weights(f))
    if name.startswith("author"):
        model = ref.SpacedRepetitionModel(method="hlr" if name == "author_hlr_ablated" else name[7:],
                                          omit_h_term=name == "author_hlr_ablated", lrate=setting)
        random.seed(42)
        model.train(author_rows(f, ref, name, True))
        return model
    if name in ["history_hlr", "logistic", "history_logistic"]:
        return fit_linear(f, name != "logistic", name == "history_hlr", setting)
    if name == "hist_boost":
        # Sparse categories have a train-only cross-fitted item rate in RICH.
        # Also expose frequent category identities (plus one rare/unknown code).
        tables = {c:{v:i for i,v in enumerate(f[c].value_counts().head(250).index)} for c in CATS}
        x = hist_design(f, tables)
        model = HistGradientBoostingClassifier(max_iter=setting, learning_rate=.07,
            categorical_features=CATS, max_leaf_nodes=31, l2_regularization=2,
            early_stopping=False, random_state=42)
        w = weights(f)
        model.fit(pd.concat([x, x]), np.repeat([0, 1], len(x)),
                  sample_weight=np.r_[w * (1 - f.gold), w * f.gold])
        return tables, model
    depth, rounds, weighted = setting
    cols = BASE if name == "base_catboost" else RICH + CATS
    model = catboost.CatBoostClassifier(loss_function="CrossEntropy", depth=depth, iterations=rounds,
        learning_rate=.05, cat_features=[c for c in cols if c in CATS], thread_count=THREADS,
        random_seed=42, verbose=False, allow_writing_files=False)
    model.fit(f[cols], f.gold, sample_weight=weights(f) if weighted else None)
    return model


def hist_design(f, tables):
    return f[RICH].assign(**{c:f[c].map(table).fillna(250).astype(int) for c,table in tables.items()})


def predict(f, name, model, ref):
    if name == "constant":
        return np.full(len(f), model)
    if name.startswith("author"):
        return np.array([model.predict(r)[0] for r in author_rows(f, ref, name, False)])
    if name in ["history_hlr", "logistic", "history_logistic"]:
        x, _ = sparse_design(f, name != "logistic", model[0])
        return linear_prob(x, model[1], f.days.to_numpy(), name == "history_hlr")
    if name == "hist_boost":
        return model[1].predict_proba(hist_design(f, model[0]))[:, 1]
    return model.predict_proba(f[BASE if name == "base_catboost" else RICH + CATS],
                               thread_count=THREADS)[:,1]


def calibrated(raw, coef):
    return expit(coef[0] + coef[1]*logit(np.clip(raw, 1e-8, 1-1e-8)))


def partition(f):
    return dict(rows=len(f), learners=f.user_id.nunique(), buckets=sorted(map(int, f.bucket.unique())))


def train(ref, out, paths):
    raw = cohort(10,13)
    tr, cal, dev = [features(raw[raw.bucket.between(a,b)]) for a,b in [(10,11),(12,12),(13,13)]]
    del raw
    table = lookup(tr)
    folds = tr.user_id.map({uid:hashlib.sha256(uid.encode()).digest()[4] % 5 for uid in tr.user_id.unique()})
    for fold in range(5):
        mask = folds == fold
        tr.loc[mask,"item_difficulty"] = encode(tr[mask], lookup(tr[~mask]))
    for f in (cal,dev):
        f["item_difficulty"] = encode(f, table)
    grids = dict(constant=[None], author_hlr=[.0003,.001,.003,.01],
                 author_hlr_ablated=[.0003,.001,.003,.01], author_lr=[.0003,.001,.003,.01], logistic=[1.,10.],
                 history_logistic=[1.,10.], history_hlr=[1.,10.],
                 hist_boost=[200,500], base_catboost=[(d,n,w) for d,n in [(4,400),(6,650)]
                                                      for w in (False,True)],
                 matched_catboost=[(d,n,w) for d,n in [(4,400),(6,650),(8,800)] for w in (False,True)])
    parts = {n:partition(f) for n,f in zip(["train","calibration","development"],[tr,cal,dev])}
    trials, models, dev_scores, best_choices = [], {}, {}, {}
    wc, wd = weights(cal), weights(dev)
    for name, settings in grids.items():
        best = np.inf
        for setting in settings:
            model = fit(tr, name, setting, ref)
            pc, pdv = (predict(f,name,model,ref) for f in (cal,dev))
            result = minimize(lambda v:np.average(loss(cal.gold,calibrated(pc,v)),weights=wc),
                [0.,1.], bounds=[(-10,10),(0,10)], method="L-BFGS-B")
            if not result.success:
                raise RuntimeError(result.message)
            for coeff in ([0.,1.], result.x.tolist()):
                p = calibrated(pdv, coeff)
                score = np.average(loss(dev.gold,p),weights=wd)
                trial = dict(model=name, setting=setting, calibration=coeff, dev_loss=score)
                trials.append(trial)
                if score < best:
                    best, models[name], dev_scores[name], best_choices[name] = score, (model, coeff), p, trial
            print(name, setting, best, flush=True)
    mat = np.column_stack([dev_scores[n] for n in COMPONENTS])
    count = len(COMPONENTS)
    sol = minimize(lambda v:np.average(loss(dev.gold,mat@v),weights=wd), np.ones(count)/count,
        method="SLSQP", bounds=[(0,1)]*count, constraints=[dict(type="eq",fun=lambda v:v.sum()-1)],
        options={"ftol":1e-13,"maxiter":500})
    if not sol.success:
        raise RuntimeError(sol.message)
    mix = np.maximum(0, sol.x)
    mix /= mix.sum()
    with (out/"models.pkl").open("wb") as fp:
        pickle.dump((models, table, mix),fp)
    write_json(out/"freeze.json",dict(sha256={str(p.name):digest(p) for p in paths+[out/"models.pkl"]},
        versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
            scipy=scipy.__version__, sklearn=sklearn.__version__, catboost=catboost.__version__),
        partitions=parts, selected=best_choices, trials=trials, weights=dict(zip(COMPONENTS,mix))))


def holm(p):
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    adjusted[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p),0,-1)))
    return adjusted


def score(ref, out, paths):
    freeze = json.loads((out/"freeze.json").read_text())
    for path in paths + [out/"models.pkl"]:
        if digest(path) != freeze["sha256"][path.name]:
            raise ValueError(f"Freeze mismatch for {path}")
    with (out/"models.pkl").open("rb") as fp:
        models, table, mix = pickle.load(fp)
    f = features(cohort(14,17))
    f["item_difficulty"] = encode(f, table)
    predictions = {name:calibrated(predict(f,name,model,ref),coeff)
                   for name,(model,coeff) in models.items()}
    predictions["ensemble"] = np.column_stack([predictions[n] for n in COMPONENTS]) @ mix
    scores = pd.DataFrame({name:loss(f.gold, p) for name,p in predictions.items()})
    learners = scores.groupby([f.bucket,f.user_id]).mean()
    # Retain exact paired learner losses with within-bucket ordinal identifiers.
    portable = learners.reset_index()
    portable["user_id"] = portable.groupby("bucket").cumcount()
    portable.rename(columns={"user_id":"learner_ordinal"}).to_csv(out/"learner_losses.csv.gz",
        index=False, compression={"method":"gzip","mtime":0})
    diff = learners[list(models)].sub(learners.ensemble, axis=0)
    gain, se = diff.mean().to_numpy(), diff.sem().to_numpy()
    k, df = len(models), len(learners)-1
    if (se <= 0).any():
        raise ValueError("Degenerate paired contrast")
    margin = .005
    prob = lambda delta: t.sf((gain-delta)/se, df)
    p0, pm = holm(prob(0)), holm(prob(margin))
    rej = pm < .05
    rem = int((~rej).sum())
    if rem:
        lower = np.where(rej, margin, gain - t.isf(.05/rem,df)*se)
    else:
        lower = np.maximum(margin, gain - t.isf(.05/k,df)*se)
    width = t.isf(.025/k,df)*se
    contrasts = {n:dict(gain=gain[i], simultaneous_ci95=[gain[i]-width[i],gain[i]+width[i]],
        holm_lower95_at_margin=lower[i], raw_p_zero=prob(0)[i], holm_p_zero=p0[i],
        raw_p_margin=prob(margin)[i], holm_p_margin=pm[i],
        pass_margin=bool(rej[i] and gain[i] >= margin)) for i,n in enumerate(models)}
    write_json(out/"result.json",dict(partition=partition(f), freeze_sha256=digest(out/"freeze.json"),
        losses_sha256=digest(out/"learner_losses.csv.gz"), mean_learner_nll=learners.mean().to_dict(),
        contrasts=contrasts, counts_as_superior=all(c["pass_margin"] for c in contrasts.values()),
        gain_by_bucket=diff.groupby(level="bucket").mean().to_dict("index")))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage",choices=["train","score"])
    ap.add_argument("out",type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    paths = [Path(__file__).resolve(), ROOT/"protocol.md", ARCHIVE, REFERENCE]
    pins = json.loads((ROOT.parent/"protocol.json").read_text())
    if digest(ARCHIVE) != pins["dataset_sha256"] or digest(REFERENCE) != pins["upstream_sha256"]:
        raise ValueError("Source digest mismatch")
    marker = args.out / ("freeze.json" if args.stage == "train" else "result.json")
    if marker.exists():
        raise FileExistsError(marker)
    (train if args.stage == "train" else score)(load_reference(), args.out, paths)


if __name__ == "__main__":
    main()
