"""Run a CFT prefix, recombine the observed witnesses, and run paired controls."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

for key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import highspy
import numpy as np
from scipy.sparse import csr_matrix

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'multifamily'))
from study import fill_cover, parse_cover, trim_cover, union_masks

BUDGET = 5.
SEEDS = [11, 29, 47]


def witness(columns, costs, masks, full):
    if len(set(columns)) != len(columns) or any(j < 0 or j >= len(costs) for j in columns):
        raise ValueError('malformed witness')
    if union_masks(columns, masks) != full:
        raise ValueError('infeasible witness')
    return sum(costs[j] for j in columns)


def native(binary, path, capsule, seed, costs, masks, full, limit):
    data = subprocess.check_output([binary, path, capsule, 'cft', str(seed)], text=True)
    lines = data.splitlines()
    tag, stamp = lines.pop().split()
    if tag != 'end':
        raise ValueError('missing end marker')
    entries = []
    for line in lines:
        stamp_text, cost, *columns = line.split()
        selected = list(map(int, columns))
        when = float(stamp_text)
        if not 0 <= when <= limit or witness(selected, costs, masks, full) != int(cost):
            raise ValueError('invalid native entry')
        entries.append(dict(cpu=when, cost=int(cost), cols=sorted(j + 1 for j in selected)))
    return entries, float(stamp)


def exact(method, matrix, masks, costs, full, seed, best, elite, prefix_cpu):
    start = time.process_time()

    def elapsed():
        return prefix_cpu + time.process_time() - start

    incumbent = [j - 1 for j in best['cols']]
    pool = sorted({*incumbent, *(j - 1 for record in elite for j in record['cols'])})
    if method == 'random':
        chosen = set(incumbent)
        rest = [j for j in range(len(costs)) if j not in chosen]
        pool = sorted(incumbent + random.Random(seed).sample(rest, len(pool) - len(chosen)))
    elif method == 'full':
        pool = list(range(len(costs)))
    result = dict(cost=best['cost'], cols=best['cols'], improved_cpu=None,
                  pool=None if method == 'full' else [j + 1 for j in pool],
                  size=len(pool), certified=False, status='budget before setup')

    def finish():
        result['return_cpu'] = elapsed()
        return result

    if elapsed() >= BUDGET:
        return finish()
    rows, n = matrix.shape[0], len(pool)
    a = csr_matrix(matrix[:, pool], dtype=np.float64)
    engine = highspy.Highs()

    def ok(status):
        if status != highspy.HighsStatus.kOk:
            raise RuntimeError(str(status))

    for key, value in [('output_flag', False), ('threads', 1), ('mip_rel_gap', 0.),
                       ('mip_abs_gap', 0.), ('random_seed', seed)]:
        ok(engine.setOptionValue(key, value))
    indices = np.arange(n, dtype=np.int32)
    ok(engine.addVars(n, np.zeros(n), np.ones(n)))
    ok(engine.changeColsCost(n, indices, np.array([costs[j] for j in pool], dtype=float)))
    ok(engine.changeColsIntegrality(n, indices, np.ones(n, dtype=np.uint8)))
    ok(engine.addRows(rows, np.ones(rows), np.full(rows, highspy.kHighsInf), a.nnz,
                      a.indptr, a.indices, a.data))
    x = np.zeros(n)
    x[np.searchsorted(pool, incumbent)] = 1.
    ok(engine.setSolution(n, indices, x))

    def record(values):
        if elapsed() >= BUDGET:
            return
        selected = [pool[i] for i in np.flatnonzero(np.asarray(values) > 0.5)]
        score = witness(selected, costs, masks, full)
        cols = [j + 1 for j in selected]
        stamp = elapsed()
        if stamp <= BUDGET and score < result['cost']:
            result.update(cost=score, cols=cols, improved_cpu=stamp)

    engine.cbMipImprovingSolution.subscribe(lambda event: record(event.data_out.mip_solution))
    engine.cbMipInterrupt.subscribe(lambda event: event.interrupt(elapsed() >= BUDGET))
    if elapsed() >= BUDGET:
        return finish()
    # A large wall guard protects against stalled calls. The callback enforces CPU eligibility.
    ok(engine.setOptionValue('time_limit', 60.))
    run_status = engine.run()
    status = engine.getModelStatus()
    if run_status == highspy.HighsStatus.kError or status not in (
            highspy.HighsModelStatus.kOptimal, highspy.HighsModelStatus.kInterrupt,
            highspy.HighsModelStatus.kHighsInterrupt, highspy.HighsModelStatus.kTimeLimit):
        raise RuntimeError(f'unexpected HiGHS status {status}')
    result['status'] = engine.modelStatusToString(status)
    if status == highspy.HighsModelStatus.kOptimal:
        record(engine.getSolution().col_value)
        result['certified'] = (elapsed() <= BUDGET and
                               abs(engine.getObjectiveValue() - result['cost']) < 1e-7)
    return finish()


def work(task):
    path, out, build, core = task
    os.sched_setaffinity(0, {core})
    raw = path.read_bytes()
    matrix, masks, costs = parse_cover(raw)
    full = (1 << matrix.shape[0]) - 1
    warm = trim_cover(fill_cover(full, masks, costs), masks, full)
    common = dict(cpu=0., cost=witness(warm, costs, masks, full), cols=sorted(j + 1 for j in warm))
    results = []
    with tempfile.NamedTemporaryFile(mode='w') as capsule:
        capsule.write(' '.join(map(str, warm)))
        capsule.flush()
        for seed in SEEDS:
            baseline, baseline_cpu = native(build / 'solve', path, capsule.name, seed, costs, masks, full, 5)
            start = time.process_time()
            prefix, native_cpu = native(build / 'pool', path, capsule.name, seed, costs, masks, full, 2)
            # The same observed prefix is reused by each counterfactual branch.
            unique = {}
            for entry in prefix:
                unique.setdefault(tuple(entry['cols']), entry)
            elite = sorted(unique.values(), key=lambda entry: entry['cost'])[:12]
            best = min([common, *elite], key=lambda entry: entry['cost'])
            prefix_cpu = native_cpu + time.process_time() - start
            branches = {method: exact(method, matrix, masks, costs, full, seed, best, elite, prefix_cpu)
                        for method in ('pool', 'random', 'full')}
            results.append(dict(seed=seed, baseline_trace=baseline, baseline_cpu=baseline_cpu,
                                prefix_trace=prefix, prefix_native_cpu=native_cpu, prefix_cpu=prefix_cpu,
                                prefix_best=best, branches=branches))
    report = dict(instance=path.stem, sha256=hashlib.sha256(raw).hexdigest(), cpu=core,
                  warm=common, runs=results)
    target = out / f'{path.stem}.json'
    target.write_text(json.dumps(report, separators=(',', ':')) + '\n')
    print(path.stem, flush=True)


def group(tasks):
    for task in tasks:
        work(task)


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    for key in ('data', 'build', 'out'):
        cli.add_argument(key, type=Path)
    cli.add_argument('--jobs', type=int, default=10)
    args = cli.parse_args()
    args.out.mkdir(exist_ok=True, parents=True)
    names = [f'scpnr{family}{i}' for family in 'efgh' for i in range(1, 6)]
    cores = sorted(os.sched_getaffinity(0))
    if not 1 <= args.jobs <= min(len(cores), len(names)):
        raise ValueError('invalid worker count')
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        groups = [[(args.data / (name + '.txt'), args.out, args.build, cores[i])
                   for name in names[i::args.jobs]] for i in range(args.jobs)]
        list(executor.map(group, groups))
