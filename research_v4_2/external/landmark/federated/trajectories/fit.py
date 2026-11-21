"""Fit reduced client Newton systems and a dense reference on CUDA."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from catboost import CatBoostClassifier

BASE = ["clicks", "days", "recency", "sites"]
torch.set_default_device("cuda")
torch.set_default_dtype(torch.float64)


def matrix(frame, cols):
    x = torch.tensor(np.log1p(frame[cols].to_numpy()) / 4)
    return torch.cat((torch.ones(len(x), 1), x), dim=1)


def logistic(x, y, penalty):
    w = torch.zeros(x.shape[1])
    for _ in range(30):
        prob = (x @ w).sigmoid()
        gradient = x.T @ (prob-y) + penalty*w
        hessian = x.T @ ((prob*(1-prob))[:, None]*x) + torch.diag(penalty)
        step = torch.linalg.solve(hessian, gradient)
        w -= step
        if step.abs().max().item() < 1e-10:
            return w
    raise ArithmeticError("full-system Newton failed to converge")


def shared_private(groups, ridge):
    size = len(ridge)
    common = torch.zeros(size)
    offsets = [torch.zeros(size) for _ in groups]
    for iteration in range(1, 31):
        reduced = torch.diag(ridge)
        residual = ridge*common
        back = []
        for (x, y), offset in zip(groups, offsets):
            p = (x @ (common+offset)).sigmoid()
            g = x.T @ (p-y)
            h = x.T @ ((p*(1-p))[:, None]*x)
            penalty = len(y)*.01
            local = h + penalty*torch.eye(size)
            coupling = torch.linalg.solve(local, h)
            correction = torch.linalg.solve(local, g + penalty*offset)
            residual += g - h @ correction
            reduced += h - h @ coupling
            back.append((coupling, correction))
        step = torch.linalg.solve(reduced, residual)
        common -= step
        moves = [correction - coupling @ step for coupling, correction in back]
        for offset, move in zip(offsets, moves):
            offset -= move
        if max(v.abs().max().item() for v in [step, *moves]) < 1e-10:
            return [common + u for u in offsets], iteration
    raise ArithmeticError("reduced Newton failed to converge")


def main(folder):
    train, dev = [pd.read_csv(folder/f"{split}.csv") for split in ("train", "dev")]
    assert "y" not in dev
    pred = dev[["row"]].copy()
    audit = {"gpu": torch.cuda.get_device_name()}
    for name, cols in [("totals", BASE), ("temporal", BASE + list(train.filter(regex="^(volume|active)_")))]:
        x, z = matrix(train, cols), matrix(dev, cols)
        y = torch.tensor(train.y.to_numpy(dtype=float))
        modules = sorted(train.code_module.unique())
        masks = [train.code_module.eq(c).to_numpy() for c in modules]
        groups = [(x[m], y[m]) for m in masks]
        ridge = torch.full((x.shape[1],), .001)
        ridge[0] = 0
        weights, iterations = shared_private(groups, len(x)*ridge)
        joint = torch.cat([x, *[x*torch.tensor(m)[:, None] for m in masks]], dim=1)
        penalty = torch.cat([len(x)*ridge, *[torch.full_like(ridge, .01*sum(m)) for m in masks]])
        reference = logistic(joint, y, penalty).reshape(len(groups)+1, -1)
        maximum = max((w-reference[0]-v).abs().max().item() for w,v in zip(weights, reference[1:]))
        assert maximum < 1e-8
        audit[name] = dict(rounds=iterations, max_coefficient_difference=maximum)
        for c,(xc,yc),w in zip(modules, groups, weights):
            subset = dev.code_module.eq(c).to_numpy()
            pred.loc[subset, "hier_"+name] = (z[subset] @ w).sigmoid().cpu().numpy()
            if name == "temporal":
                local = logistic(xc, yc, len(xc)*ridge)
                pred.loc[subset, "local"] = (z[subset] @ local).sigmoid().cpu().numpy()
        if name == "temporal":
            pred["shared"] = (z @ logistic(x,y,len(x)*ridge)).sigmoid().cpu().numpy()
        model = CatBoostClassifier(iterations=300, depth=4, learning_rate=.05, random_seed=1701,
                                   cat_features=["code_module"], task_type="GPU", thread_count=2,
                                   verbose=False, allow_writing_files=False)
        features = ["code_module", *cols]
        model.fit(train[features], train.y)
        pred["boost_"+name] = model.predict_proba(dev[features])[:, 1]
    assert pred.notna().all().all()
    pred.to_csv(folder/"forecasts.csv", index=False)
    (folder/"audit.json").write_text(json.dumps(audit, indent=2)+"\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
