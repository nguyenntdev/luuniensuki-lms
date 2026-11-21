"""Run from this directory with the parent prepared matrix as the sole argument."""
import json
import sys

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score


def design(rows):
    return np.column_stack((np.ones(len(rows)), np.log1p(rows[["clicks", "days", "recency", "sites"]]) / 4))


def fit(groups):
    clients = [(design(g), g.y.to_numpy()) for g in groups]
    count = sum(len(y) for _, y in clients)
    weights = np.zeros(5)
    ridge = np.diag([0, .001, .001, .001, .001])
    upper = np.triu_indices(5)
    for rounds in range(1, 16):
        score = np.zeros(5)
        packed = np.zeros(15)
        for x, y in clients:
            p = expit(x @ weights)
            score += x.T @ (p - y)
            packed += (x.T @ ((p * (1 - p))[:, None] * x))[upper]
        gradient = score / count + ridge @ weights
        if abs(gradient).max() < 1e-12:
            return weights, rounds
        matrix = np.zeros((5, 5))
        matrix[upper] = packed / count
        matrix[(upper[1], upper[0])] = matrix[upper]
        weights -= np.linalg.solve(matrix + ridge, gradient)
    raise RuntimeError("Newton fit did not converge")


frame = pd.read_csv(sys.argv[1])
train = frame.query("split == 'train'")
dev = frame.query("split == 'dev'")
assert set(train.learner).isdisjoint(dev.learner)
fed, rounds = fit([g for _, g in train.groupby("code_module")])
central, _ = fit([train])
keys = ["row", "learner", "code_module", "code_presentation", "y"]
archived = pd.read_csv("../run/predictions.csv.gz")
rows = dev[keys].merge(archived, on=keys, validate="one_to_one", how="left")
assert len(rows) == len(archived) and rows.notna().all().all()
for name, weights in [("exact", fed), ("central", central)]:
    rows[name] = expit(design(dev) @ weights)
error = abs(rows.exact - rows.central).max()
assert error < 1e-10
rows[keys + ["exact", "central"]].to_csv("predictions.csv.gz", index=False, compression={"method":"gzip", "mtime":0})
scores = pd.DataFrame({c: {name: roc_auc_score(g.y, g[name]) for name in rows.columns.drop(keys)}
                       for c, g in rows.groupby("code_module")}).T
scores.loc["equal_module"] = scores.mean()
scores.to_csv("auc.csv")
print(json.dumps(dict(rounds=rounds, clients=train.code_module.nunique(), bytes_per_client=48+200*rounds,
                      max_prediction_difference=error, federated_weights=fed.tolist(), centralized_weights=central.tolist()), indent=2))
