"""Learner-cluster bootstrap of the difference from random review at fixed seats."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from replay import PARENT, prepare_landmark


def precision_gain(m, captured, boundaries, budget):
    """Compare cutoff-tie allocation to uniform allocation in the same weighted list."""
    block_mass = np.add.reduceat(m, boundaries)
    block_cases = np.add.reduceat(m * captured, boundaries)
    running = block_mass.cumsum()
    last = np.searchsorted(running, budget)
    assert last < len(block_mass) and block_mass[last] > 0
    needed = budget - (running[last] - block_mass[last])
    ranked = block_cases[:last].sum() + needed * block_cases[last] / block_mass[last]
    return ranked - budget * block_cases.sum()/running[-1]


def measure(archive):
    frame = prepare_landmark(archive)
    frame = frame[frame.code_presentation == "2014J"].reset_index(drop=True)
    pred = pd.read_csv(PARENT/"run/predictions.csv.gz")
    ids = pd.factorize(frame.id_student, sort=True)[0]
    assert np.array_equal(ids, pred.learner)
    frame["score"] = pred.catboost_all
    cells = []
    for _, group in frame.groupby("code_module"):
        budget = int(group.eligible.sum()//10)
        for condition in ("current","unfiltered"):
            pool = group[group.eligible] if condition == "current" else group
            pool = pool.sort_values("score", ascending=False)
            splits = np.flatnonzero(np.r_[True,np.diff(pool.score) != 0])
            cells.append((condition, ids[pool.index], (pool.eligible & pool.outcome).to_numpy(), splits, budget))
    def gains(weights):
        result = dict(current=0., unfiltered=0.)
        for condition, members, cases, splits, budget in cells:
            result[condition] += precision_gain(weights[members], cases, splits, budget)
        return np.array([result["current"], result["unfiltered"]])/878
    n = int(ids.max()+1)
    rng = np.random.default_rng(1701)
    observed = gains(np.ones(n, dtype=int))
    draws = np.array([gains(np.bincount(rng.integers(n,size=n), minlength=n)) for _ in range(2000)])
    return {key:dict(gain=observed[i], simultaneous_percentile_95=np.quantile(draws[:,i],[.0125,.9875]).tolist())
            for i,key in enumerate(("current","unfiltered"))}


if __name__ == "__main__":
    print(json.dumps(measure(Path(sys.argv[1])),indent=2))
