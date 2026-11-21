"""Multi-family weighted set cover experiment. Run on Linux, with the pinned SetCoverPy checkout."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time
import warnings

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
import scipy

BASE = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/"
PIN = "a1ff3c5cec45cc1b16541999a4adb593fa652363"
NAMES = [f"scp{family}{i}" for family in "456abcd"
         for i in range(1, 1 + (10 if family in "45" else 5))]
SEEDS = (11, 29, 47)
CPU_LIMIT = 90
PROFILES = {"short": (3, 2, 6), "extended": (6, 4, 18)}


def fetch_matrix(name, folder):
    target = folder / (name + ".txt")
    subprocess.run(["curl", "-fsSL", "--retry", "3", "--max-time", "90",
                    BASE + target.name, "-o", str(target)], check=True)
    return target


def parse_cover(raw):
    values = iter(map(int, raw.split()))
    m, n = next(values), next(values)
    costs = [next(values) for _ in range(n)]
    masks = [0] * n
    matrix = np.zeros((m, n), dtype=bool)
    for i in range(m):
        count = next(values)
        row = [next(values) - 1 for _ in range(count)]
        if not row or min(row) < 0 or max(row) >= n or len(set(row)) != count:
            raise ValueError("invalid row")
        matrix[i, row] = True
        for j in row:
            masks[j] |= 1 << i
    if min(costs) <= 0 or next(values, None) is not None:
        raise ValueError("invalid source")
    return matrix, masks, costs


def fill_cover(unmet, masks, costs, excluded=None):
    added = []
    while unmet:
        # Cross multiplication avoids floating point tie changes.
        best_gain, best_cost, best = 0, 1, None
        for j, mask in enumerate(masks):
            gain = (mask & unmet).bit_count()
            if j != excluded and gain * best_cost > best_gain * costs[j]:
                best_gain, best_cost, best = gain, costs[j], j
        if best is None:
            return None
        added.append(best)
        unmet &= ~masks[best]
    return added


def union_masks(columns, masks):
    covered = 0
    for j in columns:
        covered |= masks[j]
    return covered


def trim_cover(columns, masks, full):
    keep = list(columns)
    for j in reversed(columns):
        trial = [k for k in keep if k != j]
        if union_masks(trial, masks) == full:
            keep = trial
    return keep


def exchange_cover(start, masks, costs, full):
    current = start
    trajectory = []
    while True:
        best = current
        best_cost = sum(costs[k] for k in current)
        trajectory.append(best_cost)
        for j in current:
            kept = [k for k in current if k != j]
            repair = fill_cover(full ^ union_masks(kept, masks), masks, costs, excluded=j)
            if repair is None:
                continue
            candidate = trim_cover(kept + repair, masks, full)
            value = sum(costs[k] for k in candidate)
            if value < best_cost:
                best, best_cost = candidate, value
        if best is current:
            return current, trajectory
        current = best


def cap_exceeded(signum, frame):
    raise TimeoutError("CPU budget exhausted")


def measure_cover(operation):
    signal.signal(signal.SIGPROF, cap_exceeded)
    signal.setitimer(signal.ITIMER_PROF, CPU_LIMIT)
    start = time.process_time()
    try:
        result = operation()
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
    return result, time.process_time() - start


def run_instance(args):
    name, folder, source, reference, profile = args
    raw = fetch_matrix(name, folder).read_bytes()
    matrix, masks, costs = parse_cover(raw)
    full = (1 << matrix.shape[0]) - 1
    results = {}

    def save(label, columns, elapsed, **details):
        if len(columns) != len(set(columns)) or not matrix[:, columns].any(axis=1).all():
            raise ValueError(f"invalid {label} witness on {name}")
        results[label] = dict(cost=sum(costs[j] for j in columns),
                              columns_one_based=[int(j)+1 for j in columns],
                              cpu_seconds=elapsed, **details)

    greedy, t1 = measure_cover(lambda: fill_cover(full, masks, costs))
    save("greedy", greedy, t1)
    pruned, t2 = measure_cover(lambda: trim_cover(greedy, masks, full))
    save("pruned", pruned, t1 + t2)
    (local, trace), t3 = measure_cover(lambda: exchange_cover(pruned, masks, costs, full))
    save("exchange", local, t1 + t2 + t3, accepted_costs=trace)
    sys.path.insert(0, str(source))
    from SetCoverPy.setcover import SetCover
    # Positive-cost empty columns can never help. Remove before upstream initialization.
    active = np.flatnonzero(matrix.any(axis=0))
    outer, steps, inner = PROFILES[profile]
    for seed in SEEDS:
        def solve():
            np.random.seed(seed)
            solver = SetCover(matrix[:, active], np.array(costs)[active],
                              maxiters=outer, subg_nsteps=steps, subg_maxiters=inner)
            value, _ = solver.SolveSCP()
            columns = active[solver.s].tolist()
            if value != sum(costs[j] for j in columns):
                raise ValueError("upstream cost disagrees with witness")
            return columns
        with warnings.catch_warnings(record=True) as notes, contextlib.redirect_stdout(io.StringIO()):
            warnings.simplefilter("always")
            columns, elapsed = measure_cover(solve)
        save(f"zhu_{seed}", columns, elapsed, warnings=sorted({str(w.message) for w in notes}))
    return name, dict(sha256=hashlib.sha256(raw).hexdigest(), rows=matrix.shape[0],
                      columns=len(costs), incidences=int(matrix.sum()), empty_columns=len(costs)-len(active),
                      reference=reference, runs=results)


def launch_study():
    cli = argparse.ArgumentParser()
    cli.add_argument("data_dir", type=Path)
    cli.add_argument("checkout", type=Path)
    cli.add_argument("result", type=Path)
    cli.add_argument("--jobs", type=int, default=4)
    cli.add_argument("--profile", choices=PROFILES, default="short")
    args = cli.parse_args()
    source = args.checkout.resolve()
    revision = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(["git", "-C", source, "diff", "--quiet", "HEAD", "--", "SetCoverPy"], check=True)
    if revision != PIN:
        raise ValueError("wrong solver revision")
    args.data_dir.mkdir(exist_ok=True, parents=True)
    table = (source / "SetCoverPy/scp_BeasleyOR_test_results.txt").read_text()
    refs = {"scp"+family.lower()+i: int(ref) for family, i, ref in
            re.findall(r"^([456ABCD])\.(\d+)\s*\|[^|]+\|[^|]+\|\s*(\d+)", table, re.M)}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        instances = dict(pool.map(run_instance, [(n, args.data_dir, source, refs[n], args.profile) for n in NAMES]))
    args.result.write_text(json.dumps(dict(
        started_from="fresh HTTPS GET for each matrix", base_url=BASE, solver_revision=PIN,
        python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
        platform=platform.platform(), workers=args.jobs, seeds=SEEDS, cpu_limit_per_stage_seconds=CPU_LIMIT,
        profile=args.profile, constructor_parameters=PROFILES[args.profile], instances=instances), indent=1) + "\n")


if __name__ == "__main__":
    launch_study()
