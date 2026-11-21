"""Time three matched bounded services on queries kept apart during probe development."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
from statistics import geometric_mean, mean, median
import sys
from time import perf_counter_ns

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE/"predecessor_load"), str(BASE/"confirmation")]
import compare
import evaluate as frozen

POLICIES = ("bounded", "interval", "probe")


def answer(method, params, credits, edges, closure, model, terms, request):
    periods = params["n_periods"]
    lo, hi = frozen.screen.windows(len(credits), periods, edges, request)
    if any(a>b for a,b in zip(lo,hi)):
        return "INFEASIBLE", None, "precedence"
    if method != "bounded" and frozen.conflicts(params, credits, lo, hi, True):
        return "INFEASIBLE", None, "interval"
    if method == "probe":
        lo, hi, _, _, empty = compare.probe(periods, credits, params["load_per_period_ub"],
                                            closure, lo, hi, "all_intervals")
        if empty is not None:
            return "INFEASIBLE", None, "probe"
    clone = model.clone()
    for i,term in request:
        clone.add(terms[i] == term)
    for var, low, high in zip(terms, lo, hi):
        clone.add_linear_constraint(var,low,high)
    solver = frozen.cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_deterministic_time = 3
    code = solver.solve(clone)
    if code in (frozen.cp_model.OPTIMAL, frozen.cp_model.FEASIBLE):
        return "FEASIBLE", [solver.value(t) for t in terms], "solver"
    return solver.status_name(code), None, "solver"


def run(job):
    archive, case, core = job
    os.sched_setaffinity(0, {core})
    number = case["instance"]
    params, credits, edges = frozen.screen.read_instance(archive,number)
    params["load_per_period_ub"] = max(int(x) for x in case["caps"])
    base, terms = frozen.template(params,credits,edges)
    start = perf_counter_ns()
    closure = compare.closures(len(credits),edges)
    setup = perf_counter_ns()-start
    rng = random.Random(42+number)
    rows = []
    for row in case["rows"]:
        methods = {}
        for _ in range(3):
            for policy in rng.sample(POLICIES, len(POLICIES)):
                start = perf_counter_ns()
                status,witness,stage = answer(policy,params,credits,edges,closure,base,terms,row["request"])
                elapsed = perf_counter_ns()-start
                archived = row["methods"]["bounded"]["status"]
                if archived != "UNKNOWN" and status != "UNKNOWN":
                    assert status == archived
                if witness is not None:
                    frozen.validate(params,credits,edges,row["request"],witness)
                entry = methods.setdefault(policy,dict(status=status, stage=stage, witness=witness, ns=[]))
                assert (entry["status"],entry["stage"],entry["witness"]) == (status,stage,witness)
                entry["ns"].append(elapsed)
        rows.append(dict(request=row["request"],source=row["source"],methods=methods))
    return dict(instance=number, core=core, closure_ns=setup, rows=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == frozen.screen.DIGEST
    cases = json.loads((BASE/"confirmation/results.json").read_text())["instances"]
    assert [c["instance"] for c in cases] == list(range(2,29,2))
    cores = sorted(os.sched_getaffinity(0))
    with ProcessPoolExecutor(min(len(cases),len(cores))) as pool:
        result = list(pool.map(run, [(args.archive,c,cores[i%len(cores)]) for i,c in enumerate(cases)]))
    ratios = {p:[] for p in POLICIES[:-1]}
    for case in result:
        times = {p:mean(median(r["methods"][p]["ns"]) for r in case["rows"]) for p in POLICIES}
        for p in ratios:
            ratios[p].append(times["probe"]/times[p])
    summary = {p:dict(probe_time_ratio=geometric_mean(v),faster_curricula=sum(x<1 for x in v))
               for p,v in ratios.items()}
    args.out.write_text(json.dumps(dict(summary=summary,instances=result),separators=(",",":"))+"\n")
    print(summary)
