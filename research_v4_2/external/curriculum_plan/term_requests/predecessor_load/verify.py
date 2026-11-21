"""Check synthetic schedules and independently replay saved rejection certificates."""

import argparse
import hashlib
import json
from itertools import combinations, product
from pathlib import Path

from compare import VARIANTS, closures, probe, rounded_conflict, screen, tighten
from balanced.screen_balanced import fractional
from certificates.compare import certificate


def params(periods, peak, count):
    return dict(n_periods=periods, load_per_period_lb=1, load_per_period_ub=peak,
                courses_per_period_lb=1, courses_per_period_ub=count)


def schedules(credits, limits, edges):
    periods = range(1, limits['n_periods'] + 1)
    for placements in product(periods, repeat=len(credits)):
        if not all(placements[a] < placements[b] for a, b in edges):
            continue
        loads = [sum(w for w, t in zip(credits, placements) if t == p) for p in periods]
        if all(limits['load_per_period_lb'] <= load <= limits['load_per_period_ub'] for load in loads):
            yield placements


def check_canaries():
    cases = [
        # Direct quantized demand: three 2-credit predecessors must share two terms of capacity 3.
        ([2, 2, 2, 1, 2], 4, 3, [(0, 3), (1, 3), (2, 3)], [(3, 3), (4, 4)], True),
        # The unpinned 4-credit successor can fit fractionally beside either requested course.
        ([4, 1, 4, 2], 3, 4, [(0, 2), (0, 3)], [(3, 3), (1, 2)], False),
    ]
    for credits, periods, peak, edges, request, rounded in cases:
        count = len(credits)
        limits = params(periods, peak, count)
        lower, upper = screen.windows(count, periods, edges, request)
        assert screen.exact(limits, credits, edges, ())[0] == 'FEASIBLE'
        assert screen.exact(params(periods, peak - 1, count), credits, edges, ())[0] == 'INFEASIBLE'
        assert screen.exact(limits, credits, edges, request)[0] == 'INFEASIBLE'
        assert next(schedules(credits, limits, edges), None) is not None
        assert not any(all(p[c] == t for c, t in request) for p in schedules(credits, limits, edges))
        assert not screen.capacity_conflict(limits, credits, lower, upper, False)
        assert certificate(limits, credits, lower, upper) is None
        assert fractional(limits, credits, edges, lower, upper, True) == 'FEASIBLE'
        assert bool(rounded_conflict(periods, credits, peak, lower, upper)) == rounded
        if not rounded:
            assert probe(periods, credits, peak, closures(count, edges),
                         lower, upper, 'all_intervals')[-1] is not None


def check_small_dags():
    count, periods = 4, 3
    pairs = list(combinations(range(count), 2))
    terms = range(1, periods + 1)
    checked = surviving = 0
    for flags in product((False, True), repeat=len(pairs)):
        edges = [edge for edge, flag in zip(pairs, flags) if flag]
        closure = closures(count, edges)
        for credits, peak in [([1, 2, 2, 3], 4), ([3, 2, 1, 4], 4)]:
            limits = params(periods, peak, count)
            feasible = list(schedules(credits, limits, edges))
            for (a, b), (ta, tb) in product(pairs, product(terms, repeat=2)):
                request = [(a, ta), (b, tb)]
                witnesses = [p for p in feasible if p[a] == ta and p[b] == tb]
                lower, upper = screen.windows(count, periods, edges, request)
                checked += 1
                if any(lo > hi for lo, hi in zip(lower, upper)):
                    assert not witnesses
                    continue
                if screen.capacity_conflict(limits, credits, lower, upper, False):
                    assert not witnesses
                    continue
                surviving += 1
                for course, (lo, hi) in enumerate(zip(lower, upper)):
                    for term in range(lo, hi + 1):
                        test_lo, test_hi = lower.copy(), upper.copy()
                        tighten(test_lo, closure[1][course], term, False)
                        tighten(test_hi, closure[0][course], term, True)
                        # The additional placement must agree with the baseline propagation.
                        assert (test_lo, test_hi) == screen.windows(
                            count, periods, edges, request + [(course, term)]
                        )
                if rounded_conflict(periods, credits, peak, lower, upper):
                    assert not witnesses
                for variant in VARIANTS:
                    lo, hi, _, _, empty = probe(periods, credits, peak, closure, lower, upper, variant)
                    if empty is not None:
                        assert not witnesses
                    for p in witnesses:
                        assert all(a <= term <= b for a, term, b in zip(lo, p, hi))
    print(f'Enumerated {checked} synthetic request cases, including {surviving} baseline survivors.')


def propagate_edges(lower, upper, edges):
    # A DAG on n courses has paths of at most n-1 edges. Repeat to avoid
    # depending on input order or the longest-path implementation under test.
    for _ in lower:
        for source, target in edges:
            lower[target] = max(lower[target], lower[source] + 1)
            upper[source] = min(upper[source], upper[target] - 1)


def verify_trace(periods, credits, peak, edges, lower, upper, entry, variant):
    lower, upper = lower.copy(), upper.copy()
    assert len(entry['trace']) == entry['deletions'] <= entry['probes']
    for step in entry['trace']:
        assert all(lo <= hi for lo, hi in zip(lower, upper))
        course, term = step['course'], step['term']
        side = step['side']
        assert side in ('lower', 'upper')
        assert term == (lower if side == 'lower' else upper)[course]
        lo, hi = lower.copy(), upper.copy()
        lo[course] = hi[course] = term
        propagate_edges(lo, hi, edges)
        assert all(a <= b for a, b in zip(lo, hi))
        left, right = step['interval']
        assert 1 <= left <= right <= periods
        if variant == 'prefix':
            assert left == 1
        if variant == 'prefix_suffix':
            assert left == 1 or right == periods
        demand = sum(w for w, a, b in zip(credits, lo, hi) if left <= a and b <= right)
        supply = (right - left + 1) * peak
        assert demand == step['demand'] > step['supply'] == supply
        if side == 'lower':
            lower[course] = term + 1
        else:
            upper[course] = term - 1
        propagate_edges(lower, upper, edges)
    course = entry['empty_course']
    assert lower[course] > upper[course]


def verify_saved(archive, results):
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == screen.DIGEST
    outcome = json.loads(results.read_text())
    balanced = json.loads((Path(__file__).resolve().parents[1] / 'balanced/results.json').read_text())
    assert len(outcome['instances']) == len(balanced['instances']) == 14
    verified = 0
    for case, control in zip(outcome['instances'], balanced['instances']):
        assert case['instance'] == control['instance']
        assert case['peak'] == control['cap_attempts'][-1][0]
        limits, credits, edges = screen.read_instance(archive, case['instance'])
        periods, peak = limits['n_periods'], case['peak']
        assert len(case['rows']) == len(control['rows']) == 32
        for row, saved in zip(case['rows'], control['rows']):
            assert row['request'] == saved['request'] and row['exact'] == saved['exact']
            lower, upper = screen.windows(len(credits), periods, edges, row['request'])
            for variant, entry in row.get('probing', {}).items():
                assert (entry['empty_course'] is not None) == ('trace' in entry)
                if 'trace' in entry:
                    assert saved['exact'] == 'INFEASIBLE'
                    verify_trace(periods, credits, peak, edges, lower, upper, entry, variant)
                    verified += 1
    assert verified == sum(c['additional'] for c in outcome['summary']['probing'].values())
    print(f'Independently replayed {verified} rejection certificates.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    check_canaries()
    check_small_dags()
    verify_saved(args.archive, args.results)


if __name__ == '__main__':
    main()
