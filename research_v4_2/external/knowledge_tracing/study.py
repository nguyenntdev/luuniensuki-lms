"""Fit and score a causal next-response model on the public pyKT user split."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = ["skill", "success", "failure", "skill_success", "skill_failure", "attempts", "previous", "distance"]
FULL = BASE + ["run", "right_streak", "wrong_streak"]
HASHES = {"train_valid.csv": "83ff2090d1ddaa6295854984733b699b52fa3b656d7c814d6c9da56822964ac7",
          "test.csv": "518d8f6c81d487d5c342eedd9a46b4160c974945247baf16e01b432a3101d154",
          "dkt.py": "d6bc51dd70084301619560240a4ba49920e0278448984196fe886dd3993baae6"}


def load_split(path):
    result = []
    for row in pd.read_csv(path).itertuples():
        q = np.fromstring(row.concepts, dtype=int, sep=",")
        r = np.fromstring(row.responses, dtype=int, sep=",")
        assert len(q) == len(r) and (q >= 0).all() and (q < 100).all() and np.isin(r, [0,1]).all()
        result.append((int(row.uid), int(row.fold), q, r))
    return result


def features(rows):
    result = []
    for uid, _, q, r in rows:
        skill_success = np.zeros(100, int)
        skill_attempts = np.zeros(100, int)
        last = np.full(100, -1)
        total = run = right = wrong = 0
        for i, (skill, response) in enumerate(zip(q, r)):
            if i == 0 or skill != q[i-1]:
                run = right = wrong = 0
            if i:
                j = last[skill]
                local = skill_success[skill]
                result.append((uid, i, response, skill, total, i-total, local, skill_attempts[skill]-local,
                               i, r[j] if j >= 0 else -1, i-j if j >= 0 else 0, run, right, wrong))
            skill_success[skill] += response
            skill_attempts[skill] += 1
            total += response
            last[skill] = i
            run += 1
            right = (right+1)*response
            wrong = (wrong+1)*(1-response)
    d = pd.DataFrame(result, columns=["uid", "step", "y", *FULL])
    for col in FULL:
        if col not in ["skill", "previous"]:
            d[col] = np.log1p(d[col])
    d["skill"] = pd.Categorical(d.skill, categories=range(100))
    return d


def batches(rows, ids, device):
    for offset in range(0, len(ids), 96):
        selected = ids[offset:offset+96]
        width = max(len(rows[i][2]) for i in selected)
        q = np.zeros((len(selected), width), int)
        r = q.copy()
        mask = np.zeros(q.shape, bool)
        for n, i in enumerate(selected):
            qs, rs = rows[i][2:]
            q[n, :len(qs)] = qs
            r[n, :len(rs)] = rs
            mask[n, 1:len(rs)] = True
        yield [torch.as_tensor(z, device=device) for z in (q,r,mask)]


def dkt(rows, model, device, train=False, optimizer=None):
    model.train(train)
    ids = np.random.permutation(len(rows)) if train else np.arange(len(rows))
    predictions = []
    with torch.set_grad_enabled(train):
        for q, r, mask in batches(rows, ids, device):
            # The outcome at t enters the recurrence only after forecasting t.
            out = model(q[:, :-1], r[:, :-1]).gather(2, q[:, 1:, None]).squeeze(2)
            valid = mask[:, 1:]
            pred = out[valid]
            if train:
                optimizer.zero_grad()
                torch.nn.functional.binary_cross_entropy(pred, r[:, 1:][valid].float()).backward()
                optimizer.step()
            else:
                predictions.extend(pred.cpu().numpy())
    if not train:
        return np.asarray(predictions)


def loss(y, p):
    p = np.clip(p.astype(float), 1e-7, 1-1e-7)
    return -np.where(y, np.log(p), np.log1p(-p))


def run(raw, out):
    torch.manual_seed(731)
    np.random.seed(731)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for name, digest in HASHES.items():
        assert hashlib.file_digest((raw/name).open("rb"), "sha256").hexdigest() == digest
    spec = importlib.util.spec_from_file_location("upstream_dkt", raw/"dkt.py")
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    pool = load_split(raw/"train_valid.csv")
    tr = [x for x in pool if x[1] != 0]
    va = [x for x in pool if x[1] == 0]
    train, dev = features(tr), features(va)
    y, v = train.y.to_numpy(), dev.y.to_numpy()
    net = upstream.DKT(100, 64, dropout=.1).to(device)
    opt = torch.optim.Adam(net.parameters(), lr=.001)
    best = np.inf
    tuning = {"dkt": [], "device":device}
    for epoch in range(12):
        dkt(tr, net, device, True, opt)
        val = loss(v, dkt(va, net, device)).mean()
        tuning["dkt"].append(val)
        if val < best:
            best, params = val, copy.deepcopy(net.state_dict())
    net.load_state_dict(params)
    val_dkt = dkt(va, net, device)
    models, weights = {}, {}
    for name, cols in [("full",FULL), ("short",BASE)]:
        best = np.inf
        tuning[name] = {}
        for leaves in (15, 31):
            model = HistGradientBoostingClassifier(max_iter=200, max_leaf_nodes=leaves, learning_rate=.07,
                                                    categorical_features="from_dtype", early_stopping=False, random_state=731)
            model.fit(train[cols], y)
            p = model.predict_proba(dev[cols])[:,1]
            val = loss(v, p).mean()
            tuning[name][leaves] = val
            if val < best:
                best, models[name], chosen = val, model, p
        grid = np.arange(5)/4
        weights[name] = grid[np.argmin([loss(v,w*val_dkt+(1-w)*chosen).mean() for w in grid])]
    pre = ColumnTransformer([("onehot",OneHotEncoder(handle_unknown="ignore"),["skill"]),
                             ("scale",StandardScaler(),FULL[1:])])
    logistic = make_pipeline(pre, LogisticRegression(max_iter=500)).fit(train[FULL], y)
    rates = train.groupby("skill", observed=False).y.agg(["sum","count"])
    rates = (rates["sum"]+1)/(rates["count"]+2)
    out.mkdir(parents=True, exist_ok=True)
    tuning.update(weights=weights, train_users=len(tr), validation_users=len(va), train_events=len(y), validation_events=len(v))
    (out/"development.json").write_text(json.dumps(tuning, indent=2)+"\n")
    te = load_split(raw/"test.csv")
    assert len({r[0] for r in tr+va+te}) == len(tr)+len(va)+len(te)
    test = features(te)
    p = test[["uid","step","y"]].copy()
    p["skill_mean"] = test.skill.astype(int).map(rates).to_numpy()
    p["logistic"] = logistic.predict_proba(test[FULL])[:,1]
    p["dkt"] = dkt(te,net,device)
    for name, cols in [("full",FULL), ("short",BASE)]:
        p[name] = models[name].predict_proba(test[cols])[:,1]
        p[name+"_blend"] = weights[name]*p.dkt + (1-weights[name])*p[name]
    assert np.isfinite(p).all().all()
    p.to_csv(out/"predictions.csv.gz", index=False, compression={"method":"gzip","mtime":0})
    summarize(p, out)


def summarize(p, out):
    methods = ["skill_mean","logistic","dkt","full","short","short_blend","full_blend"]
    losses = pd.DataFrame({k:loss(p.y.to_numpy(),p[k].to_numpy()) for k in methods})
    sums = losses.groupby(p.uid).sum().to_numpy()
    counts = p.groupby("uid").size().to_numpy()
    point = sums.sum(axis=0)/counts.sum()
    rng = np.random.default_rng(731)
    draws = []
    for _ in range(50):
        ids = rng.integers(len(sums),size=(100,len(sums)))
        averages = sums[ids].sum(axis=1)/counts[ids].sum(axis=1)[:,None]
        draws.extend(averages[:,:-1] - averages[:,[-1]])
    limits = np.quantile(draws,[.025/6,1-.025/6],axis=0)
    gain = point[:-1]-point[-1]
    res = dict(learners=len(sums), events=len(p), correct=int(p.y.sum()),
               nll=dict(zip(methods,point)), comparisons={k:dict(gain=gain[i], simultaneous_ci=limits[:,i].tolist())
               for i,k in enumerate(methods[:-1])}, stage_pass=bool(np.all((gain>=.015)&(limits[0]>0))))
    (out/"result.json").write_text(json.dumps(res,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    a = parser.parse_args()
    run(a.raw, a.out)
