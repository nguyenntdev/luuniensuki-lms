"""Compare assignment relaxations on balance-preserving course placements."""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ortools.linear_solver import pywraplp

PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PARENT))
import screen


def fractional(params, credits, edges, lower, upper, cumulative):
    solver = pywraplp.Solver.CreateSolver('GLOP')
    periods = range(1, params['n_periods'] + 1)
    rows = [[solver.NumVar(0, int(lo <= p <= hi), '') for p in periods]
            for lo, hi in zip(lower, upper)]
    expectation = []
    for row in rows:
        solver.Add(sum(row) == 1)
        expectation.append(sum(p * x for p, x in zip(periods, row)))
    for col in zip(*rows):
        count, load = sum(col), sum(v * w for v, w in zip(col, credits))
        for var, prefix in [(count, 'courses'), (load, 'load')]:
            solver.Add(var >= params[f'{prefix}_per_period_lb'])
            solver.Add(var <= params[f'{prefix}_per_period_ub'])
    for parent, child in edges:
        solver.Add(expectation[parent] + 1 <= expectation[child])
        if cumulative:
            for t in periods:
                solver.Add(sum(rows[child][:t]) <= sum(rows[parent][:t-1]))
    status = solver.Solve()
    if status == solver.INFEASIBLE:
        return 'INFEASIBLE'
    if status == solver.OPTIMAL:
        return 'FEASIBLE'
    return 'UNKNOWN'


def run(job):
    number, archive, original = job
    params, credits, edges = screen.read_instance(archive, number)
    attempts = []
    for cap in range(math.ceil(sum(credits) / params['n_periods']), params['load_per_period_ub'] + 1):
        params['load_per_period_ub'] = cap
        status, base = screen.exact(params, credits, edges, ())
        attempts.append([cap, status])
        if status != 'INFEASIBLE':
            break
    result = dict(instance=number, cap_attempts=attempts, base=base, rows=[])
    if base is None:
        return result
    for case in original:
        request = case['request']
        lower, upper = screen.windows(len(credits), params['n_periods'], edges, request)
        precedence = any(lo > hi for lo, hi in zip(lower, upper))
        interval = not precedence and bool(screen.capacity_conflict(params, credits, lower, upper, False))
        if precedence or interval:
            mean = cumulative = 'SKIPPED'
        else:
            mean = fractional(params, credits, edges, lower, upper, False)
            cumulative = fractional(params, credits, edges, lower, upper, True)
        exact, witness = screen.exact(params, credits, edges, request, .5)
        assert not (mean == 'INFEASIBLE' and cumulative == 'FEASIBLE')
        assert not (witness and (precedence or interval or 'INFEASIBLE' in (mean, cumulative)))
        result['rows'].append(dict(request=request, distribution=case['distribution'], precedence=precedence,
                                   interval=interval, mean=mean, cumulative=cumulative, exact=exact, witness=witness))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--workers', default=1, type=int)
    args = parser.parse_args()
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == screen.DIGEST
    original = json.loads((PARENT / 'results.json').read_text())['instances']
    jobs = [(i['instance'], args.archive, i['rows']) for i in original]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(run, jobs))
    rows = [r for i in results for r in i['rows']]
    counts = Counter(r['exact'] for r in rows)
    filters = {}
    for name in ('precedence', 'interval', 'mean', 'cumulative'):
        rejected = [r for r in rows if r['precedence'] or (name != 'precedence' and r['interval'])
                    or (name in ('mean','cumulative') and r[name] == 'INFEASIBLE')]
        filters[name] = dict(Counter(r['exact'] for r in rejected))
    summary = dict(instances=sum(bool(i['base']) for i in results), requests=len(rows),
                   oracle=dict(counts), rejected=filters)
    args.output.write_text(json.dumps(dict(summary=summary, instances=results), separators=(',', ':'))+'\n')
    print(summary)
