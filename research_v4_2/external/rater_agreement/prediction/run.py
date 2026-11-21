"""Fit on matched development and score the frozen lookup tables on mismatched data."""
import argparse
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import digamma, gammaln, logsumexp

LABELS = ["entailment", "neutral", "contradiction"]
ARCHIVE_HASH = "049f507b9e36b1fcb756cfd5aeb3b7a0cfcb84bf023793652987f7e7e0957822"
CELLS = [tuple([i, j, 4-i-j]) for i in range(5) for j in range(5-i)]
X = np.array(CELLS)
FULL = np.array([(i, j, 5-i-j) for i in range(6) for j in range(6-i)])
EYE = np.eye(3, dtype=int)
BACKOFF = [0, 1, 5, 25, 125, 625]


def read_split(archive, split, forbidden=None):
    rows, audit = [], Counter()
    with archive.open(f"multinli_1.0/multinli_1.0_dev_{split}.jsonl") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            audit["raw"] += 1
            prompt = row["promptID"]
            premise = hashlib.sha256(" ".join(row["sentence1"].casefold().split()).encode()).hexdigest()
            if forbidden and (prompt in forbidden[0] or premise in forbidden[1]):
                audit["overlap"] += 1
                continue
            votes = row["annotator_labels"]
            if len(votes) != 5 or set(votes) - set(LABELS):
                audit["invalid"] += 1
                continue
            pair = f"{row['pairID']}@{line_number}"
            rows.append((pair, prompt, premise, row["genre"], tuple(votes.count(k) for k in LABELS)))
    return rows, audit


def groups(rows):
    # Connected components of the bipartite prompt-to-premise graph.
    parent = {}
    def root(key):
        while parent.setdefault(key, key) != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key
    for _, prompt, premise, _, _ in rows:
        a, b = root(prompt), root(premise)
        parent[max(a, b)] = min(a, b)
    return [root(r[1]) for r in rows]


def counts(rows):
    c = Counter(r[4] for r in rows)
    return np.array([c[tuple(row)] for row in FULL])


def conditional_counts(weights):
    table = np.zeros((len(X), 3))
    for h, w in zip(FULL, weights):
        for k in np.flatnonzero(h):
            table[CELLS.index(tuple(h-EYE[k])), k] += w*h[k]
    return table


def dirichlet(weights):
    def objective(log_a):
        a = np.exp(log_a)
        total = a.sum()
        ll = gammaln(total)-gammaln(total+5) + (gammaln(FULL+a)-gammaln(a)).sum(axis=1)
        grad = digamma(total)-digamma(total+5) + digamma(FULL+a)-digamma(a)
        return -weights @ ll, -(weights @ grad)*a
    fit = minimize(objective, np.zeros(3), jac=True, bounds=[(-10, 10)]*3, method="L-BFGS-B")
    if not fit.success:
        raise RuntimeError(fit.message)
    a = np.exp(fit.x)
    return (X+a)/(4+a.sum())


def mixture(weights, k):
    rng = np.random.default_rng(41021)
    best = -np.inf
    for _ in range(20):
        p = rng.dirichlet(np.ones(3), size=k)
        pi = np.full(k, 1/k)
        previous = -np.inf
        for step in range(501):
            log_joint = FULL @ np.log(p).T + np.log(pi)
            norm = logsumexp(log_joint, axis=1)
            score = weights @ norm + .5*(np.log(p).sum()+np.log(pi).sum())
            if abs(score-previous) < 1e-8 or step == 500:
                break
            previous = score
            memberships = weights[:, None]*np.exp(log_joint-norm[:, None])
            p = memberships.T @ FULL + .5
            p /= p.sum(axis=1, keepdims=True)
            pi = memberships.sum(axis=0)+.5
            pi /= pi.sum()
        if score > best:
            best = score
            post = X @ np.log(p).T + np.log(pi)
            result = np.exp(post-logsumexp(post, axis=1, keepdims=True)) @ p
    return result


def smooth(freq, prior, strength):
    denom = freq.sum(axis=1, keepdims=True)+strength
    return np.divide(freq+strength*prior, denom, out=prior.copy(), where=denom>0)


def fit_tables(dev):
    ids = groups(dev)
    folds = [int(hashlib.sha256(g.encode()).hexdigest(), 16)%5 for g in ids]
    cv = np.zeros(len(BACKOFF))
    whole = counts(dev)
    for fold in range(5):
        held = counts([r for r, f in zip(dev, folds) if f == fold])
        train = whole-held
        freq, prior, targets = conditional_counts(train), dirichlet(train), conditional_counts(held)
        for i, strength in enumerate(BACKOFF):
            pred = smooth(freq, prior, strength)
            cv[i] += np.sum(targets*(1+(pred**2).sum(axis=1, keepdims=True)-2*pred))
    strength = BACKOFF[np.argmin(cv)]
    major = X == X.max(axis=1, keepdims=True)
    prior = dirichlet(whole)
    tables = dict(mixture6=mixture(whole, 6), empirical=X/4, majority=major/major.sum(axis=1, keepdims=True),
                  jeffreys=(X+.5)/5.5, laplace=(X+1)/7, dirichlet=prior, latent3=mixture(whole, 3),
                  histogram=smooth(conditional_counts(whole), prior, strength))
    for p in tables.values():
        assert np.all(p >= 0) and np.allclose(p.sum(axis=1), 1)
    return tables, strength, (cv/(5*len(dev))).tolist()


def evaluate(rows, tables, dest):
    group = groups(rows)
    _, idx = np.unique(group, return_inverse=True)
    losses = np.zeros((len(FULL), len(tables)))
    for i, h in enumerate(FULL):
        for k in np.flatnonzero(h):
            cell = CELLS.index(tuple(h-EYE[k]))
            for j, p in enumerate(tables.values()):
                losses[i,j] += h[k]/5 * np.sum((p[cell]-EYE[k])**2)
    full_idx = {tuple(h): i for i, h in enumerate(FULL)}
    item = losses[[full_idx[r[4]] for r in rows]]
    with (dest/"test_items.csv").open("x") as f:
        w = csv.writer(f)
        w.writerow(["pair_id_at_line", "group", "genre", *LABELS])
        for r, g in zip(rows, group):
            w.writerow([r[0], g, r[3], *r[4]])
    sizes = np.bincount(idx)
    group_delta = np.zeros((len(sizes), len(tables)-1))
    np.add.at(group_delta, idx, item[:, 1:]-item[:, :1])
    boot = []
    rng = np.random.default_rng(41021)
    for _ in range(10000):
        draw = rng.integers(len(sizes), size=len(sizes))
        boot.append(group_delta[draw].sum(axis=0)/sizes[draw].sum())
    tail = .025/(len(tables)-1)
    intervals = np.quantile(boot, [tail, 1-tail], axis=0).T
    scores = {}
    for j, method in enumerate(tables):
        scores[method] = {"brier": item[:, j].mean()}
        if j:
            scores[method].update(delta=(item[:,j]-item[:,0]).mean(), interval=intervals[j-1].tolist())
    return dict(scores=scores, groups=len(sizes), strict_superiority=bool((intervals[:,0]>0).all()),
                genres=dict(Counter(r[3] for r in rows)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.archive.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != ARCHIVE_HASH:
            raise ValueError("Unexpected source archive")
    args.output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.archive) as archive:
        dev, dev_audit = read_split(archive, "matched")
        tables, strength, cv = fit_tables(dev)
        predictions = dict(labels=LABELS, counts=X.tolist(), tables={k:v.tolist() for k,v in tables.items()},
                           backoff=strength, grid=BACKOFF, cv=cv)
        (args.output/"predictions.json").write_text(json.dumps(predictions, indent=2)+"\n")
        test, test_audit = read_split(archive, "mismatched", ({r[1] for r in dev}, {r[2] for r in dev}))
        result = evaluate(test, tables, args.output)
        result.update(dev_n=len(dev), test_n=len(test), dev_groups=len(set(groups(dev))),
                      dev_counts=dev_audit, test_counts=test_audit, dev_genres=dict(Counter(r[3] for r in dev)))
        (args.output/"result.json").write_text(json.dumps(result, indent=2)+"\n")


if __name__ == "__main__":
    main()
