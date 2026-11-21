"""Measure exact query services on the reserved CSPLib curriculum instances."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter_ns

import numpy as np
from ortools.sat.python import cp_model

PARENT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PARENT), str(PARENT / 'balanced')]
import screen
from screen_balanced import fractional

POLICIES = ('integer', 'precedence', 'singleton', 'interval', 'lp', 'bounded')


def sample(number, params, credits, edges):
    periods = params['n_periods']
    lo, hi = screen.windows(len(credits), periods, edges, ())
    rng = random.Random(number)
    selected = set()
    for distribution in ('all', 'windows'):
        for _ in range(16):
            while True:
                pair = sorted(rng.sample(range(len(credits)), 2))
                request = tuple((i, rng.randint(lo[i], hi[i]) if distribution == 'windows'
                                 else rng.randint(1, periods)) for i in pair)
                if request not in selected:
                    selected.add(request)
                    yield distribution, request
                    break


def template(params, credits, edges):
    model = cp_model.CpModel()
    periods = params['n_periods']
    terms = [model.new_int_var(1, periods, '') for _ in credits]
    assigned = []
    for term in terms:
        row = [model.new_bool_var('') for _ in range(periods)]
        model.add_map_domain(term, row, offset=1)
        assigned.append(row)
    for col in zip(*assigned):
        model.add_linear_constraint(sum(col), params['courses_per_period_lb'], params['courses_per_period_ub'])
        load = sum(x * c for x, c in zip(col, credits))
        model.add_linear_constraint(load, params['load_per_period_lb'], params['load_per_period_ub'])
    for parent, child in edges:
        model.add(terms[parent] < terms[child])
    return model, terms


def conflicts(params, credits, lo, hi, extended):
    p = params['n_periods']
    # Index mass by (earliest, latest) to reuse for multiple intervals.
    n = p + 2
    counts = np.bincount(np.asarray(lo)*n + hi, minlength=n*n).reshape(n, n)
    weight = np.bincount(np.asarray(lo)*n + hi, weights=credits, minlength=n*n).reshape(n, n)
    for hist, prefix in ((counts, 'courses'), (weight, 'load')):
        integral = hist.cumsum(0).cumsum(1)
        lower = params[f'{prefix}_per_period_lb']
        upper = params[f'{prefix}_per_period_ub']
        for length in range(1, (p if extended else 1) + 1):
            for left in range(1, p - length + 2):
                right = left + length - 1
                required = integral[p, right] - integral[left-1, right]
                available = integral[right, p] - integral[right, left-1]
                if required > upper * length or available < lower * length:
                    return True
    return False


def answer(policy, params, credits, edges, base, terms, request):
    if policy != 'integer':
        lo, hi = screen.windows(len(credits), params['n_periods'], edges, request)
        if any(a > b for a, b in zip(lo, hi)):
            return 'INFEASIBLE', None, 'precedence'
        if policy in ('singleton', 'interval', 'lp') and conflicts(params, credits, lo, hi, policy != 'singleton'):
            return 'INFEASIBLE', None, 'capacity'
        if policy == 'lp' and fractional(params, credits, edges, lo, hi, True) == 'INFEASIBLE':
            return 'INFEASIBLE', None, 'lp'
    model = base.clone()
    for i, term in request:
        model.add(terms[i] == term)
    if policy == 'bounded':
        for i, variable in enumerate(terms):
            model.add_linear_constraint(variable, lo[i], hi[i])
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_deterministic_time = 3
    status = solver.solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return 'FEASIBLE', [solver.value(t) for t in terms], 'solver'
    assert status in (cp_model.INFEASIBLE, cp_model.UNKNOWN)
    return solver.status_name(status), None, 'solver'


def validate(params, credits, edges, request, witness):
    for i, t in request:
        assert witness[i] == t
    assert len(witness) == len(credits)
    assert min(witness) >= 1 and max(witness) <= params['n_periods']
    assert all(witness[a] < witness[b] for a, b in edges)
    for p in range(1, params['n_periods'] + 1):
        sizes = [c for t, c in zip(witness, credits) if t == p]
        assert params['load_per_period_lb'] <= sum(sizes) <= params['load_per_period_ub']
        assert params['courses_per_period_lb'] <= len(sizes) <= params['courses_per_period_ub']


def evaluate(job):
    archive, number, core = job
    os.sched_setaffinity(0, {core})
    params, credits, edges = screen.read_instance(archive, number)
    attempts = {}
    for cap in range(math.ceil(sum(credits)/params['n_periods']), params['load_per_period_ub'] + 1):
        params['load_per_period_ub'] = cap
        status, initial = screen.exact(params, credits, edges, ())
        attempts[cap] = status
        if status != 'INFEASIBLE':
            break
    result = dict(instance=number, core=core, caps=attempts, initial=initial, rows=[])
    if initial is None:
        return result
    base, terms = template(params, credits, edges)
    rng = random.Random(1709 + number)
    for distribution, request in sample(number, params, credits, edges):
        row = dict(source=distribution, request=request, methods={})
        # Re-shuffle a fresh complete block on every repetition.
        for _ in range(3):
            order = rng.sample(POLICIES, len(POLICIES))
            for policy in order:
                start = perf_counter_ns()
                status, witness, stage = answer(policy, params, credits, edges, base, terms, request)
                elapsed = perf_counter_ns() - start
                if witness is not None:
                    validate(params, credits, edges, request, witness)
                entry = row['methods'].setdefault(policy, dict(status=status, witness=witness, stage=stage, ns=[]))
                assert (status, witness, stage) == (entry['status'], entry['witness'], entry['stage'])
                entry['ns'].append(elapsed)
        result['rows'].append(row)
    return result


def summarize(results):
    all_rows = [row for i in results for row in i['rows']]
    quality = {p: dict(Counter(row['methods'][p]['status'] for row in all_rows)) for p in POLICIES}
    discrepancies = sum(len({row['methods'][p]['status'] for p in POLICIES}) > 1 for row in all_rows)
    calls = {p: sum(row['methods'][p]['stage'] == 'solver' for row in all_rows) for p in POLICIES}
    times = {p: [statistics.mean(statistics.median(r['methods'][p]['ns']) for r in i['rows'])
                 for i in results if i['rows']] for p in POLICIES}
    rng = np.random.default_rng(6723)
    n = len(times['integer'])
    comparisons = {}
    if n:
        boot = rng.integers(n, size=(10000, n))
        for p in POLICIES:
            if p == 'interval':
                continue
            log_ratio = np.log(np.array(times['interval'])/times[p])
            draws = 1 - np.exp(np.mean(log_ratio[boot], axis=1))
            comparisons[p] = dict(gain=float(1 - np.exp(log_ratio.mean())),
                                  interval=np.quantile(draws, [.005,.995]).tolist(),
                                  ratio_by_instance=np.exp(log_ratio).tolist())
    return dict(requests=len(all_rows), solved_base_instances=n, quality=quality, discrepancies=discrepancies,
                calls=calls, mean_ns_by_instance=times, comparisons=comparisons)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cores', default='39')
    args = parser.parse_args()
    cores = list(map(int, args.cores.split(',')))
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == screen.DIGEST
    jobs = [(args.archive, number, cores[(number//2-1) % len(cores)]) for number in range(2, 29, 2)]
    # Pin all measurements for a given curriculum to one core. No two
    # instances run simultaneously on a core when one worker is used per job.
    if len(cores) not in (1, len(jobs)) or len(cores) != len(set(cores)):
        parser.error('supply either one core or fourteen distinct cores')
    with ProcessPoolExecutor(max_workers=len(cores)) as pool:
        results = list(pool.map(evaluate, jobs))
    summary = summarize(results)
    args.output.write_text(json.dumps(dict(summary=summary, instances=results), separators=(',', ':')) + '\n')
    print(json.dumps({p: v['gain'] for p, v in summary['comparisons'].items()}), flush=True)
