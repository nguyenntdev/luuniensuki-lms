"""Transport fixed queue rankings to an independently collected first-flag stream."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

DIGEST = "5e29679063c6e416c2ae741d94a8f2b8e996f21e7cbf278488687fb6cb1df15a"


def fill(group, mass, outcome, capacity):
    total = np.bincount(group, weights=mass)
    positives = np.bincount(group, weights=mass*outcome)
    used = np.cumsum(total)
    assert used[-1] >= capacity
    cut = np.searchsorted(used, capacity)
    fraction = (capacity - (used[cut]-total[cut]))/total[cut]
    return positives[:cut].sum() + positives[cut]*fraction


def landmark(events, first_flag, time, primary):
    prefix = events[events.time <= time].groupby("user").time.agg(["max","size"])
    exit_time = first_flag.reindex(prefix.index).fillna(np.inf).to_numpy()
    current = exit_time > time
    case = current & np.isfinite(exit_time)
    seats = current.sum() // 10
    assert seats > 0
    groups = {}
    for method, scores in {"inactivity":time-prefix["max"],"few_actions":-prefix["size"],
                           "recent_activity":prefix["max"], "many_actions":prefix["size"],
                           "uniform":np.zeros(len(prefix))}.items():
        groups[method] = np.unique(-np.asarray(scores), return_inverse=True)[1]
    policies = []
    available = {}
    for days in (0,1,7,30,None):
        name = str(days) if days is not None else "all"
        available[name] = np.ones(len(case),bool) if days is None else exit_time > time-days*86400
        roster = available[name]
        for method, group in groups.items():
            capture = fill(group, roster, case, seats)
            stale = fill(group, roster, ~current, seats)
            policies.append(dict(lag=name,method=method,roster=int(roster.sum()),capture=capture,
                                 stale=stale,precision=capture/seats))
    result = dict(time=time,seats=int(seats),seen=len(case),eligible=int(current.sum()),
                  future_cases=int(case.sum()),queues=policies)
    if primary:
        # All policies in a draw see the same learner multiplicities and capacity.
        draws = []
        order = [(lag,m) for lag in ("0","all") for m in groups if m!="uniform"]
        rng = np.random.default_rng(20261122)
        for _ in range(2000):
            counts = np.bincount(rng.integers(len(case),size=len(case)), minlength=len(case))
            row = []
            for lag in ("0","all"):
                mass = available[lag]*counts
                uniform = np.dot(mass,case)/mass.sum()
                row.extend(fill(group,mass,case,seats)/seats-uniform
                           for method,group in groups.items() if method!="uniform")
            draws.append(row)
        bounds = np.quantile(draws,[.025/len(order),1-.025/len(order)],axis=0).T
        precisions = {(r["lag"],r["method"]):r["precision"] for r in policies}
        result["vs_uniform"] = [dict(lag=l,method=m,gain=precisions[l,m]-precisions[l,"uniform"],
                                     simultaneous_ci95=ci.tolist()) for (l,m),ci in zip(order,bounds)]
    return result


def run(source):
    with source.open("rb") as f:
        assert hashlib.file_digest(f,"sha256").hexdigest() == DIGEST
    data = pd.read_csv(source,skiprows=1,header=None,usecols=[0,2,3])
    data.columns = ["user","time","label"]
    assert len(data)==411749 and data.time.is_monotonic_increasing and data.label.isin([0,1]).all()
    flagged = data[data.label==1].groupby("user").time
    first_flag = flagged.min()
    last = data.groupby("user").time.max().reindex(first_flag.index)
    start,end = float(data.time.min()),float(data.time.max())
    result = dict(source_sha256=DIGEST,actions=len(data),learners=int(data.user.nunique()),
                  flags=int(data.label.sum()),flagged_learners=len(first_flag),start=start,end=end,
                  users_with_multiple_flags=int((flagged.size()>1).sum()),
                  users_with_later_activity=int((last>first_flag).sum()))
    result["landmarks"] = {str(q):landmark(data,first_flag,start+q*(end-start),q==.5)
                           for q in (.25,.5,.75)}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    print(json.dumps(run(parser.parse_args().source),indent=2))
