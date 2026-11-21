"""Check saved service outcomes against certified schedules and summarize paired timing."""
from collections import Counter
import json
from pathlib import Path
from statistics import median
import sys

import numpy as np
from benchmark import BASE, POLICIES, compare, frozen


def audit(archive, filename):
    results = json.loads(filename.read_text())
    control = json.loads((BASE/"confirmation/results.json").read_text())
    resolved = json.loads((BASE/"confirmation/verification.json").read_text())["resolved_after_timing"]
    ref = {(x["instance"],tuple(map(tuple,x["request"]))): x["decision"] for x in resolved}
    outcomes = {p:Counter() for p in POLICIES}
    ratios = {p:[] for p in POLICIES[:-1]}
    checked = 0
    for case, original in zip(results["instances"], control["instances"], strict=True):
        n = case["instance"]
        assert original["instance"] == n
        params, credits, edges = frozen.screen.read_instance(archive,n)
        params["load_per_period_ub"] = max(map(int,original["caps"]))
        samples = {p:[] for p in POLICIES}
        for row, old in zip(case["rows"],original["rows"],strict=True):
            assert row["request"] == old["request"]
            truth = ref.get((n,tuple(map(tuple,row["request"]))),old["methods"]["bounded"]["status"])
            assert truth in ("FEASIBLE","INFEASIBLE")
            for p, cell in row["methods"].items():
                assert cell["status"] in (truth,"UNKNOWN")
                if cell["status"] == "FEASIBLE":
                    compare.validate_assignment(params, credits, edges, row["request"], cell["witness"])
                    checked += 1
                assert len(cell["ns"]) == 3 and min(cell["ns"]) > 0
                samples[p].append(median(cell["ns"]))
                outcomes[p][cell["status"]] += 1
                outcomes[p]["solver_calls"] += cell["stage"] == "solver"
        for p in ratios:
            ratios[p].append(sum(samples["probe"])/sum(samples[p]))
    rng = np.random.default_rng(1701)
    draws = rng.integers(14,size=(10000,14))
    timings = {}
    for p, rat in ratios.items():
        logs = np.log(rat)
        observed = np.exp(logs.mean())
        assert np.isclose(observed,results["summary"][p]["probe_time_ratio"])
        timings[p] = dict(relative_time=observed, simultaneous_interval=np.exp(
            np.quantile(logs[draws].mean(axis=1),[.0125,.9875])).tolist())
    return dict(checked_witnesses=checked,outcomes=outcomes,timings=timings)


if __name__ == "__main__":
    print(json.dumps(audit(*map(Path,sys.argv[1:])),indent=2))
