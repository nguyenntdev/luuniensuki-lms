"""Simulate local message updates on the GPU using public OULAD data."""
import gzip
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch
from catboost import CatBoostClassifier

FEATURES = ["clicks", "days", "recency", "sites"]
ROUNDS, STEPS, RATE = 40, 5, .25


def tensor(values):
    return torch.as_tensor(values, device="cuda", dtype=torch.float64)


def gradient_steps(x, y, start, steps, mu=0.):
    w = start.clone()
    for _ in range(steps):
        residual = (x @ w).sigmoid() - y
        w -= RATE * (x.T @ residual / len(y) + mu * (w - start))
    return w


def federate(clients, start, mu):
    w = start
    total = sum(len(y) for x, y in clients.values())
    for _ in range(ROUNDS):
        updates = [len(y) * gradient_steps(x, y, w, STEPS, mu) for x, y in clients.values()]
        w = torch.stack(updates).sum(dim=0) / total
    return w


def adapt(x, y, w, ridge, intercept_only=False):
    p = (x @ w).sigmoid()
    active_x = x[:, :1] if intercept_only else x
    hessian = active_x.T @ (active_x * (p * (1 - p))[:, None]) / len(p)
    penalty = tensor(ridge[:active_x.shape[1]])
    update = torch.linalg.solve(hessian + torch.diag(penalty), active_x.T @ (y - p) / len(p))
    adjusted = w.clone()
    adjusted[:len(update)] += update
    return adjusted


def main(source, dest):
    dest.mkdir(exist_ok=True, parents=True)
    frame = pd.read_csv(source)
    train = frame[frame.split == "train"]
    dev = frame[frame.split == "dev"].copy()
    def matrix(group):
        return tensor(np.column_stack((np.ones(len(group)), np.log1p(group[FEATURES]) / 4.)))
    clients = {c:(matrix(g), tensor(g.y.to_numpy())) for c, g in train.groupby("code_module")}
    start = tensor(np.zeros(5))
    global_w = federate(clients, start, 0.)
    proximal = federate(clients, start, .1)
    pooled = gradient_steps(matrix(train), tensor(train.y.to_numpy()), start, ROUNDS * STEPS)
    model = CatBoostClassifier(iterations=200, depth=4, learning_rate=.05, random_seed=42,
                               task_type="GPU", devices="0", gpu_ram_part=.20, thread_count=2,
                               verbose=False, allow_writing_files=False)
    model.fit(train[FEATURES], train.y)
    dev["pooled_boosting"] = model.predict_proba(dev[FEATURES])[:, 1]
    for c, rows in dev.groupby("code_module"):
        x, y = clients[c]
        ridge = [.005, .02, .02, .02, .02]
        models = {"fedavg":global_w, "fedprox":proximal, "pooled":pooled,
                  "local":gradient_steps(x, y, start, ROUNDS * STEPS),
                  "intercept_only":adapt(x, y, global_w, ridge, True),
                  "weak_ridge":adapt(x, y, global_w, [1e-5]*5),
                  "adapted":adapt(x, y, global_w, ridge)}
        for name, w in models.items():
            dev.loc[rows.index, name] = (matrix(rows) @ w).sigmoid().cpu().numpy()
    with gzip.GzipFile(str(dest/"predictions.csv.gz"), "wb", mtime=0) as stream:
        dev.drop(columns=[*FEATURES,"split"]).to_csv(stream,index=False)
    counts = frame.groupby(["code_module","code_presentation","split"]).agg(
        registrations=("y","size"), learners=("learner","nunique"), withdrawals=("y","sum")).reset_index()
    counts.to_csv(dest/"counts.csv",index=False)
    metadata = dict(device=torch.cuda.get_device_name(0), pytorch=torch.__version__,
                    clients=len(clients), rounds=ROUNDS, local_steps=STEPS,
                    parameter_payload_per_client_bytes=(ROUNDS*2+1)*5*8,
                    training_learners=train.learner.nunique(), development_learners=dev.learner.nunique())
    (dest/"execution.json").write_text(json.dumps(metadata, indent=2)+"\n")

if __name__ == "__main__":
    main(*map(Path,sys.argv[1:]))
