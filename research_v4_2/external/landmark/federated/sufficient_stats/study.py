"""Run on the CSV produced by ../prepare.py. Outputs are relative to this file."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.special import expit

root = Path(__file__).resolve().parent
out = root / "run"
out.mkdir(exist_ok=True)
frame = pd.read_csv(sys.argv[1])
train = frame.query("split == 'train'")
dev = frame.query("split == 'dev'")
triangle = np.triu_indices(5)
ridge = np.diag([0, .001, .001, .001, .001])


def matrix(group):
    features = group[["clicks", "days", "recency", "sites"]]
    return np.column_stack([np.ones(len(group)), np.log1p(features) / 4])


def fit(groups):
    clients = [(matrix(g), g.y.to_numpy()) for g in groups]
    weights = np.zeros(5)
    gradients = []
    for _ in range(15):
        message = np.zeros(20)
        for x, y in clients:
            p = expit(x @ weights)
            h = x.T @ (x * (p * (1 - p))[:, None])
            message += np.r_[x.T @ (p - y), h[triangle]]
        message /= len(train)
        grad = message[:5] + ridge @ weights
        gradients.append(float(abs(grad).max()))
        if gradients[-1] < 1e-12:
            break
        hessian = np.zeros((5, 5))
        hessian[triangle] = message[5:]
        hessian[(triangle[1], triangle[0])] = message[5:]
        weights -= np.linalg.solve(hessian + ridge, grad)
    return expit(matrix(dev) @ weights), dict(weights=weights.tolist(), gradients=gradients)


archived = pd.read_csv(root.parent / "run/predictions.csv.gz")
keys = list(archived.columns[:5])
pd.testing.assert_frame_equal(archived[keys], dev[keys].reset_index(drop=True))
fed, distributed = fit([g for _, g in train.groupby("code_module")])
central, pooled = fit([train])
error = float(abs(fed - central).max())
assert error <= 1e-10
archived["newton"] = fed
archived["pooled_newton"] = central
archived.to_csv(out / "predictions.csv.gz", index=False, compression=dict(method="gzip", mtime=0))
rounds = len(distributed["gradients"])
clients = train.code_module.nunique()
traffic = 200 * rounds + 48
record = dict(distributed=distributed, pooled=pooled, max_prediction_error=error,
              rounds=rounds, bytes_per_client=traffic, total_bytes=traffic * clients)
(out / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
