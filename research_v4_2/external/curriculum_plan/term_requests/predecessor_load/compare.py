"""Compare precedence-closure credit bounds on saved balanced development requests."""

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from graphlib import TopologicalSorter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import screen

VARIANTS = ('prefix', 'prefix_suffix', 'all_intervals')


def closures(count, edges):
    """Get the longest prerequisite path for each reachable ordered pair."""
    graph = TopologicalSorter()
    parents = [[] for _ in range(count)]
    for parent, child in edges:
        graph.add(child, parent)
        parents[child].append(parent)
    ancestors = [{i: 0} for i in range(count)]
    for course in graph.static_order():
        for parent in parents[course]:
            for ancestor, lag in ancestors[parent].items():
                ancestors[course][ancestor] = max(ancestors[course].get(ancestor, 0), lag + 1)
    descendants = [{} for _ in range(count)]
    for course, closure in enumerate(ancestors):
        for ancestor, lag in closure.items():
            descendants[ancestor][course] = lag
    return ancestors, descendants


def tighten(bound, closure, term, earlier):
    for course, lag in closure.items():
        if earlier:
            bound[course] = min(bound[course], term - lag)
        else:
            bound[course] = max(bound[course], term + lag)


def conflict(periods, weights, peak, lower, upper, variant='all_intervals'):
    """Find an overloaded interval using compulsory credit and uniform term capacity."""
    if variant == 'prefix' or variant == 'prefix_suffix':
        deadline = [0] * (periods + 1)
        release = [0] * (periods + 1)
        for lo, hi, weight in zip(lower, upper, weights):
            deadline[hi] += weight
            release[lo] += weight
        demand = 0
        for right in range(1, periods + 1):
            demand += deadline[right]
            supply = peak * right
            if demand > supply:
                return dict(interval=[1, right], demand=demand, supply=supply)
        if variant == 'prefix_suffix':
            demand = 0
            for left in range(periods, 0, -1):
                demand += release[left]
                supply = peak * (periods - left + 1)
                if demand > supply:
                    return dict(interval=[left, periods], demand=demand, supply=supply)
        return None

    # The cumulative sum at (left, right) counts only windows entirely inside.
    enclosed = [[0] * (periods + 1) for _ in range(periods + 2)]
    for lo, hi, weight in zip(lower, upper, weights):
        enclosed[lo][hi] += weight
    for left in range(periods, 0, -1):
        for right in range(left, periods + 1):
            enclosed[left][right] += (
                enclosed[left + 1][right] + enclosed[left][right - 1]
                - enclosed[left + 1][right - 1]
            )
            demand = enclosed[left][right]
            supply = peak * (right - left + 1)
            if demand > supply:
                return dict(interval=[left, right], demand=demand, supply=supply)
    return None


def rounded_conflict(periods, credits, peak, lower, upper):
    for divisor in range(2, max(credits) + 1):
        weights = [credit // divisor for credit in credits]
        cut = conflict(periods, weights, peak // divisor, lower, upper)
        if cut is not None:
            return dict(divisor=divisor, **cut)
    return None


def probe(periods, credits, peak, closure, lower, upper, variant):
    """Remove endpoints whose tentative placement overloads a credit interval."""
    ancestors, descendants = closure
    lower, upper = lower.copy(), upper.copy()
    removed = []
    probes = 0
    while True:
        before = len(removed)
        for course in range(len(credits)):
            for earlier in (False, True):
                while True:
                    term = (upper if earlier else lower)[course]
                    lo, hi = lower.copy(), upper.copy()
                    tighten(lo, descendants[course], term, False)
                    tighten(hi, ancestors[course], term, True)
                    probes += 1
                    cut = conflict(periods, credits, peak, lo, hi, variant)
                    if cut is None:
                        break
                    removed.append(dict(course=course, term=term, side='upper' if earlier else 'lower', **cut))
                    if earlier:
                        tighten(upper, ancestors[course], term - 1, True)
                    else:
                        tighten(lower, descendants[course], term + 1, False)
                    empty = next((i for i, (a, b) in enumerate(zip(lower, upper)) if a > b), None)
                    if empty is not None:
                        return lower, upper, removed, probes, empty
        if len(removed) == before:
            return lower, upper, removed, probes, None


def validate_assignment(params, credits, edges, request, witness):
    assert len(witness) == len(credits)
    periods = range(1, params['n_periods'] + 1)
    assert all(term in periods for term in witness)
    assert all(witness[course] == term for course, term in request)
    assert all(witness[parent] < witness[child] for parent, child in edges)
    for term in periods:
        loads = [w for w, placement in zip(credits, witness) if placement == term]
        assert params['courses_per_period_lb'] <= len(loads) <= params['courses_per_period_ub']
        assert params['load_per_period_lb'] <= sum(loads) <= params['load_per_period_ub']


def run(job):
    archive, case, original, exact_replay = job
    number = case['instance']
    params, credits, edges = screen.read_instance(archive, number)
    attempts = case['cap_attempts']
    peak, status = attempts[-1]
    assert status == 'FEASIBLE'
    periods = params['n_periods']
    assert math.ceil(sum(credits) / periods) <= peak <= params['load_per_period_ub']
    assert attempts[:-1] == [[cap, 'INFEASIBLE'] for cap in range(math.ceil(sum(credits) / periods), peak)]
    params['load_per_period_ub'] = peak
    closure = closures(len(credits), edges)
    validate_assignment(params, credits, edges, (), case['base'])
    assert len(case['rows']) == len(original) == 32
    results = []
    for row, admin in zip(case['rows'], original):
        request = row['request']
        assert (request, row['distribution']) == (admin['request'], admin['distribution'])
        lower, upper = screen.windows(len(credits), periods, edges, request)
        precedence = any(lo > hi for lo, hi in zip(lower, upper))
        interval = not precedence and bool(screen.capacity_conflict(params, credits, lower, upper, False))
        assert (precedence, interval) == (row['precedence'], row['interval'])

        exact = row['exact']
        witnesses = [row['witness']] if row['witness'] is not None else []
        if exact_replay:
            status, witness = screen.exact(params, credits, edges, request, .5)
            assert status == exact
            if witness is not None:
                witnesses.append(witness)
        for witness in witnesses:
            validate_assignment(params, credits, edges, request, witness)

        result = dict(request=request, distribution=row['distribution'], exact=exact,
                      precedence=precedence, interval=interval, cumulative=row['cumulative'])
        rejected = precedence or interval
        if not rejected:
            cut = rounded_conflict(periods, credits, peak, lower, upper)
            assert cut is None or exact == 'INFEASIBLE'
            result['rounded'] = cut
            result['probing'] = {}
            for variant in VARIANTS:
                lo, hi, removed, probes, empty = probe(periods, credits, peak, closure, lower, upper, variant)
                assert empty is None or exact == 'INFEASIBLE'
                for witness in witnesses:
                    assert all(a <= t <= b for a, t, b in zip(lo, witness, hi))
                entry = dict(probes=probes, deletions=len(removed), empty_course=empty)
                if empty is not None:
                    entry['trace'] = removed
                result['probing'][variant] = entry
        assert not rejected or exact == 'INFEASIBLE'
        results.append(result)
    return dict(instance=number, peak=peak, rows=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--exact-replay', action='store_true')
    args = parser.parse_args()
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == screen.DIGEST
    saved = json.loads((ROOT / 'balanced/results.json').read_text())['instances']
    original = json.loads((ROOT / 'results.json').read_text())['instances']
    development = list(range(1, 28, 2))
    assert [case['instance'] for case in saved] == [case['instance'] for case in original] == development
    jobs = [(args.archive, case, admin['rows'], args.exact_replay)
            for case, admin in zip(saved, original)]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(run, jobs))

    rows = [row for case in results for row in case['rows']]
    summary = dict(instances=len(results), requests=len(rows), exact=dict(Counter(r['exact'] for r in rows)),
                   precedence=sum(r['precedence'] for r in rows),
                   interval_additional=sum(r['interval'] for r in rows),
                   cumulative_additional=sum(r['cumulative'] == 'INFEASIBLE' for r in rows),
                   rounded_additional=sum(r.get('rounded') is not None for r in rows),
                   probing={})
    for variant in VARIANTS:
        entries = [row['probing'][variant] for row in rows if 'probing' in row]
        summary['probing'][variant] = dict(additional=sum(e['empty_course'] is not None for e in entries),
                                          requests_with_deletions=sum(e['deletions'] > 0 for e in entries),
                                          deletions=sum(e['deletions'] for e in entries),
                                          probes=sum(e['probes'] for e in entries))
    args.output.write_text(json.dumps(dict(summary=summary, instances=results), separators=(',', ':')) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
