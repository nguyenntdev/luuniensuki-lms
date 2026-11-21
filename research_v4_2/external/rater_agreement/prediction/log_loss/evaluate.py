"""Predict a held recorded vote using only the other four votes."""
import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run as base

EMPIRICAL = [.001, .01, .1, .25, .5, 1, 2, 4, 8, 16, 32, 64]
CONDITIONAL = [.01, .1, 1, 5, 25, 125, 625, 3125]
SNLI_DEV = "9c03faff70182ef086ebfeed2cffbabb5fcc6a84a8b3314decbbb5b01f07f4bf"
SNLI_TEST = "1147550151ca8b16ddb31d8dc0e739a670a65f7c3e64aac5951eaeff103fb220"
COHORTS = ["all", "unanimous", "non_unanimous"]


def check_hash(path, expected):
    with path.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != expected:
            raise ValueError(f"Source checksum mismatch: {path}")


def read_snli(path, expected, forbidden):
    check_hash(path, expected)
    audit, rows = Counter(), []
    with path.open() as f:
        for index, line in enumerate(f, 1):
            r = json.loads(line)
            audit["raw"] += 1
            image = r["captionID"].split("#")[0]
            premise = hashlib.sha256(" ".join(r["sentence1"].casefold().split()).encode()).hexdigest()
            if forbidden and (image in forbidden[0] or premise in forbidden[1]):
                audit["overlap"] += 1
                continue
            labels = r["annotator_labels"]
            if len(labels) != 5 or set(labels) - set(base.LABELS):
                audit["invalid"] += 1
                continue
            rows.append((f"{r['pairID']}@{index}", image, premise, "caption",
                         tuple(labels.count(k) for k in base.LABELS)))
    return rows, audit


def empirical(alpha):
    return (base.X + alpha / 3) / (4 + alpha)


def fit(dev):
    whole = base.counts(dev)
    folds = np.array([int(hashlib.sha256(g.encode()).hexdigest(), 16) % 5 for g in base.groups(dev)])
    losses = [np.zeros(len(grid)) for grid in (EMPIRICAL, CONDITIONAL)]
    for fold in range(5):
        held = base.counts([r for r, f in zip(dev, folds) if f == fold])
        train = whole - held
        prior = base.dirichlet(train)
        table = base.conditional_counts(train)
        targets = base.conditional_counts(held)
        for scores, predictions in zip(losses, (
            [empirical(s) for s in EMPIRICAL],
            [base.smooth(table, prior, s) for s in CONDITIONAL],
        )):
            scores += [-(targets * np.log(p)).sum() for p in predictions]
    alpha = EMPIRICAL[np.argmin(losses[0])]
    strength = CONDITIONAL[np.argmin(losses[1])]
    prior = base.dirichlet(whole)
    models = dict(mixture6=base.mixture(whole, 6), tuned_empirical=empirical(alpha),
                  jeffreys=empirical(1.5), laplace=empirical(3), dirichlet=prior,
                  latent3=base.mixture(whole, 3),
                  conditional=base.smooth(base.conditional_counts(whole), prior, strength))
    for p in models.values():
        assert np.all(p > 0) and np.allclose(p.sum(axis=1), 1)
    tuning = dict(alpha=alpha, strength=strength, grids=[EMPIRICAL, CONDITIONAL],
                  cv_nats=[(v / (5 * len(dev))).tolist() for v in losses])
    return models, tuning


def score(rows, models, dest):
    groups = base.groups(rows)
    group_names, idx = np.unique(groups, return_inverse=True)
    # Cluster vote counts stratified by full five-vote histogram retain the
    # pairing of every method and cohort without storing a bootstrap per item.
    sizes = np.zeros((len(group_names), len(base.FULL)), dtype=int)
    hist_index = {tuple(h): i for i, h in enumerate(base.FULL)}
    with (dest / "items.csv").open("x") as f:
        w = csv.writer(f)
        w.writerow(["pair_id_at_line", "group", *base.LABELS])
        for r, g, i in zip(rows, groups, idx):
            w.writerow([r[0], g, *r[4]])
            sizes[i, hist_index[r[4]]] += 1
    weights = np.zeros((len(base.FULL), 3))
    loss = np.zeros((len(base.FULL), 3, len(models)))
    for i, h in enumerate(base.FULL):
        for k in np.flatnonzero(h):
            visible = h - base.EYE[k]
            cell = base.CELLS.index(tuple(visible))
            values = [-np.log(p[cell, k]) for p in models.values()]
            for c in (0, 1 if max(visible) == 4 else 2):
                weights[i, c] += h[k]
                loss[i, c] += h[k] * np.array(values)

    def means(hist):
        votes = hist @ weights
        return np.einsum("h,hcm->cm", hist, loss) / votes[:, None]

    summed = sizes.sum(axis=0)
    result = means(summed)
    assert (summed @ weights)[0] == 5 * len(rows)
    rng = np.random.default_rng(41021)
    samples = []
    for _ in range(10000):
        draw = rng.integers(len(sizes), size=len(sizes))
        avg = means(np.bincount(draw, minlength=len(sizes)) @ sizes)
        samples.append(avg[:, 1:] - avg[:, :1])
    tail = .025 / 36
    lower, upper = np.quantile(samples, [tail, 1-tail], axis=0)
    cohorts = {}
    for c, name in enumerate(COHORTS):
        summary = {}
        for j, method in enumerate(models):
            summary[method] = dict(nats=result[c, j])
            if j:
                summary[method].update(delta=result[c, j]-result[c, 0],
                                       ci=[lower[c, j-1], upper[c, j-1]])
        cohorts[name] = dict(votes=int((summed @ weights)[c]), models=summary,
                             superiority=bool(np.all(lower[c] > 0)))
    return cohorts, len(sizes)


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def experiment(dest, reader):
    dest.mkdir()
    dev, audit_dev = reader(False, None)
    models, tuning = fit(dev)
    save(dest / "forecasts.json", dict(labels=base.LABELS, inputs=base.X.tolist(),
         tables={k: p.tolist() for k, p in models.items()}, tuning=tuning))
    forbidden = ({r[1] for r in dev}, {r[2] for r in dev})
    test, audit_test = reader(True, forbidden)
    cohorts, test_groups = score(test, models, dest)
    save(dest / "result.json", dict(dev_audit=audit_dev, test_audit=audit_test,
         dev_items=len(dev), test_items=len(test), dev_groups=len(set(base.groups(dev))),
         test_groups=test_groups, cohorts=cohorts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("multinli", "snli_dev", "snli_test", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    check_hash(args.multinli, base.ARCHIVE_HASH)
    with zipfile.ZipFile(args.multinli) as z:
        experiment(args.output / "multinli", lambda test, exclude:
                   base.read_split(z, "mismatched" if test else "matched", exclude))
    experiment(args.output / "snli", lambda test, exclude: read_snli(
        args.snli_test if test else args.snli_dev, SNLI_TEST if test else SNLI_DEV, exclude))
