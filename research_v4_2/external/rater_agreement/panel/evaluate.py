"""Exact finite-panel prediction from released ChaosNLI count vectors."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import comb, gammaln
from sklearn.linear_model import LogisticRegression

CLASSES = ("entailment", "neutral", "contradiction")
CHECKSUM = {"snli": "99f9015ddda7d85f66a087452bc30d53974314fe27e7d589e2f41ad44bd509c1",
            "mnli_m": "8eb49b589488e7b1a9ec95fb8a864bd50f0509b4f808eed0aed3f8167617664d"}


def histogram(size):
    return np.array([(a, b, size-a-b) for a in range(size+1) for b in range(size-a+1)])


OLD = histogram(5)
NEW = histogram(4)
JEFF = (NEW + .5) / 5.5


def read_rows(path, corpus):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CHECKSUM[corpus]
    rows = [json.loads(line) for line in raw.splitlines()]
    for row in rows:
        premise = " ".join(row["example"]["premise"].casefold().split())
        row["group"] = hashlib.sha256(premise.encode()).hexdigest()
    return rows


def matrices(rows):
    counts = np.array([r["label_count"] for r in rows])
    h = np.array([[r["old_labels"].count(k) for k in CLASSES] for r in rows])
    group = {tuple(key): i for i, key in enumerate(OLD)}
    idx = np.array([group[tuple(key)] for key in h])
    mass = np.prod(comb(counts[:, None], NEW[None]), axis=-1) / math.comb(100, 4)
    remaining = np.maximum(0, counts[:, None, :] - NEW[None]) / 96
    assert np.allclose(mass.sum(axis=1), 1)
    assert np.allclose((mass[..., None]*remaining).sum(axis=(1,2)), 1)
    return counts, idx, mass, remaining


def dirichlet(counts, weights):
    def objective(logalpha):
        alpha = np.exp(logalpha)
        terms = (gammaln(counts+alpha) - gammaln(alpha)).sum(axis=1)
        terms += gammaln(alpha.sum()) - gammaln(counts.sum(axis=1) + alpha.sum())
        return -float(weights @ terms)
    opt = minimize(objective, np.zeros(3), method="L-BFGS-B", bounds=[(-8, 12)]*3)
    assert opt.success, opt.message
    alpha = np.exp(opt.x)
    return (NEW + alpha) / (4 + alpha.sum())


def fit(rows):
    counts, idx, mass, remain = matrices(rows)
    shape = (len(OLD), len(NEW), 3)
    tables = {k: np.empty(shape) for k in ("candidate","jeffreys","pooled","dirichlet",
                                            "local_dirichlet","saturated","logistic")}
    tables["jeffreys"][:] = JEFF
    tables["dirichlet"][:] = dirichlet(counts, np.ones(len(rows)))
    tables["pooled"][:] = (OLD[:, None] + NEW[None] + .5) / 10.5
    # Direct contingency table over observed contexts and remaining vote classes.
    joint = np.zeros(shape)
    np.add.at(joint, idx, mass[..., None] * remain)
    for i in range(len(OLD)):
        weights = (idx == i).astype(float) + 20/len(rows)
        tables["local_dirichlet"][i] = dirichlet(counts, weights)
        cells = joint[i] + 20 * joint.sum(axis=0)/len(rows)
        tables["saturated"][i] = (cells + JEFF)/(cells.sum(axis=1,keepdims=True) + 1)
        # Independent implementation of the prior posterior rule on individual panels.
        for j in range(len(NEW)):
            likelihood = weights * mass[:, j]
            tables["candidate"][i,j] = (likelihood @ remain[:,j] + JEFF[j]) / (likelihood.sum() + 1)
    ii, jj = np.indices(shape[:2]).reshape(2,-1)
    features = np.column_stack((np.eye(len(OLD))[ii], np.eye(len(NEW))[jj], np.eye(len(ii))))
    features_all = np.repeat(features, 3, axis=0)
    w = joint.ravel()
    model = LogisticRegression(C=1,max_iter=1000,tol=1e-9)
    model.fit(features_all[w>0],np.tile(np.arange(3),len(ii))[w>0],sample_weight=w[w>0])
    tables["logistic"][:] = model.predict_proba(features).reshape(shape)
    for t in tables.values():
        assert np.all(t>0) and np.allclose(t.sum(axis=2),1)
    return tables


def run(data, corpus, excluded, out):
    def eligible(r):
        return (r["group"] not in excluded and len(r["old_labels"])==5 and
                all(v in CLASSES for v in r["old_labels"]) and sum(r["label_count"])==100)
    rows = [r for r in data if eligible(r)]
    train = [r for r in rows if int(r["group"],16)%5]
    test = [r for r in rows if not int(r["group"],16)%5]
    assert {r["group"] for r in train}.isdisjoint(r["group"] for r in test)
    tables = fit(train)
    target_dir = out/corpus
    target_dir.mkdir(parents=True,exist_ok=True)
    (target_dir/"forecasts.json").write_text(json.dumps({k:v.tolist() for k,v in tables.items()})+"\n")
    _, idx, mass, remain = matrices(test)
    names = list(tables)
    losses = np.column_stack([-(remain*np.log(t[idx])*mass[:,:,None]).sum(axis=(1,2)) for t in tables.values()])
    groups, g = np.unique([r["group"] for r in test],return_inverse=True)
    with (target_dir/"items.csv").open("w") as stream:
        writer=csv.writer(stream,lineterminator="\n")
        writer.writerow(["uid","group",*names])
        for row, loss in zip(test,losses):
            writer.writerow([row["uid"],row["group"],*loss])
    totals=np.zeros((len(groups),len(names)))
    np.add.at(totals,g,losses)
    sizes=np.bincount(g)
    rng=np.random.default_rng(71017)
    resampled=[]
    for _ in range(50):
        draws=rng.multinomial(len(groups),np.ones(len(groups))/len(groups),size=100)
        resampled.extend((draws @ totals)/(draws @ sizes)[:,None])
    resampled=np.array(resampled)
    diff=resampled-resampled[:,:1]
    estimates={}
    for j,k in enumerate(names):
        delta=float((losses[:,j]-losses[:,0]).mean())
        ci=np.quantile(diff[:,j],[.025/12,1-.025/12]).tolist()
        estimates[k]=dict(loss=float(losses[:,j].mean()),gain=delta,ci=ci,passes=bool(delta>=.005 and ci[0]>0))
    result=dict(source_rows=len(data),fitted=len(train),test=len(test),test_groups=len(groups),scores=estimates,
                max_saturated_discrepancy=float(abs(tables["saturated"]-tables["candidate"]).max()),
                passes=all(estimates[k]["passes"] for k in names[1:]))
    (target_dir/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw",type=Path)
    parser.add_argument("out",type=Path)
    a=parser.parse_args()
    data={k:read_rows(a.raw/f"chaosNLI_{k}.jsonl",k) for k in CHECKSUM}
    overlap=set.intersection(*[{r["group"] for r in rows} for rows in data.values()])
    for k,rows in data.items():
        print(k,json.dumps(run(rows,k,overlap,a.out)))
