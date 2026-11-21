"""Check two period requests on CSPLib development instances."""
import argparse
import hashlib
import json
import random
import re
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from graphlib import TopologicalSorter
from pathlib import Path

from ortools.sat.python import cp_model


DIGEST = '306d21eebab2e95105b319c9baa53b723073ed7202513eb72163e69b33f024b0'


def read_instance(archive, number):
    with zipfile.ZipFile(archive) as data:
        source = data.read(f'bacp_MiniZinc_Benchmarks/bacp-{number}.mzn').decode()
    params = {k: int(v) for k, v in re.findall(r'^(\w+) = (\d+);', source, re.M)}
    credits = list(map(int, re.findall(r'\d+', re.search(r'course_load = \[([^\]]+)', source)[1])))
    edges = [(int(b) - 1, int(a) - 1) for a, b in re.findall(r'prerequisite\((\d+), (\d+)\)', source)]
    assert len(credits) == params['n_courses'] and len(edges) == source.count('constraint')
    return params, credits, edges


def windows(count, periods, edges, request):
    graph = TopologicalSorter()
    lower, upper = [1] * count, [periods] * count
    for course, term in request:
        lower[course] = upper[course] = term
    children = [[] for _ in lower]
    for parent, child in edges:
        graph.add(child, parent)
        children[parent].append(child)
    order = list(graph.static_order())
    for parent in order:
        for child in children[parent]:
            lower[child] = max(lower[child], lower[parent] + 1)
    for parent in reversed(order):
        for child in children[parent]:
            upper[parent] = min(upper[parent], upper[child] - 1)
    return lower, upper


def capacity_conflict(params, credits, lower, upper, single):
    for left in range(1, params['n_periods'] + 1):
        for right in range(left, (left if single else params['n_periods']) + 1):
            compulsory = [i for i in range(len(credits)) if left <= lower[i] and upper[i] <= right]
            possible = [i for i in range(len(credits)) if lower[i] <= right and upper[i] >= left]
            length = right - left + 1
            for group, amount, key, direction in [
                (compulsory, len(compulsory), 'courses_per_period_ub', 1),
                (compulsory, sum(credits[i] for i in compulsory), 'load_per_period_ub', 1),
                (possible, len(possible), 'courses_per_period_lb', -1),
                (possible, sum(credits[i] for i in possible), 'load_per_period_lb', -1),
            ]:
                if direction * (amount - length * params[key]) > 0:
                    return [left, right, key, amount, length * params[key], group]
    return None


def exact(params, credits, edges, request, budget=3):
    model = cp_model.CpModel()
    periods = range(1, params['n_periods'] + 1)
    terms = [model.new_int_var(1, len(periods), f't{i}') for i in range(len(credits))]
    rows = []
    for i, term in enumerate(terms):
        row = [model.new_bool_var(f'x{i}_{p}') for p in periods]
        model.add_exactly_one(row)
        model.add(term == sum(p * bit for p, bit in zip(periods, row)))
        rows.append(row)
    for p in periods:
        flags = [row[p - 1] for row in rows]
        load = sum(credit * flag for credit, flag in zip(credits, flags))
        model.add_linear_constraint(sum(flags), params['courses_per_period_lb'], params['courses_per_period_ub'])
        model.add_linear_constraint(load, params['load_per_period_lb'], params['load_per_period_ub'])
    for parent, child in edges:
        model.add(terms[parent] < terms[child])
    for i, p in request:
        model.add(terms[i] == p)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_deterministic_time = budget
    status = solver.solve(model)
    assert status != cp_model.MODEL_INVALID
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return solver.status_name(status), None
    assignment = [solver.value(t) for t in terms]
    assert all(assignment[i] == p for i, p in request)
    assert all(assignment[a] < assignment[b] for a, b in edges)
    for p in periods:
        enrolled = [credit for t, credit in zip(assignment, credits) if t == p]
        assert params['courses_per_period_lb'] <= len(enrolled) <= params['courses_per_period_ub']
        assert params['load_per_period_lb'] <= sum(enrolled) <= params['load_per_period_ub']
    return 'FEASIBLE', assignment


def evaluate(job):
    archive, number = job
    params, credits, edges = read_instance(archive, number)
    count, periods = len(credits), params['n_periods']
    original = windows(count, periods, edges, ())
    if any(a > b for a, b in zip(*original)):
        return {'instance': number, 'empty_base_window': True, 'rows': []}
    rng = random.Random(number)
    seen, rows = set(), []
    for distribution in ('unrestricted', 'individual_windows'):
        while sum(row['distribution'] == distribution for row in rows) < 16:
            indices = sorted(rng.sample(range(count), 2))
            request = tuple((i, rng.randint(original[0][i], original[1][i]) if
                             distribution == 'individual_windows' else rng.randint(1, periods)) for i in indices)
            if request in seen:
                continue
            seen.add(request)
            lo, hi = windows(count, periods, edges, request)
            impossible = any(a > b for a, b in zip(lo, hi))
            single = None if impossible else capacity_conflict(params, credits, lo, hi, True)
            interval = None if impossible else capacity_conflict(params, credits, lo, hi, False)
            status, assignment = exact(params, credits, edges, request)
            assert not (single and not interval)
            assert not ((impossible or interval) and assignment is not None)
            rows.append(dict(distribution=distribution, request=request, precedence=impossible,
                             singleton=single, interval=interval, status=status, assignment=assignment))
    return {'instance': number, 'empty_base_window': False, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == DIGEST
    jobs = [(args.archive, i) for i in range(1, 29, 2)]
    with ProcessPoolExecutor(args.workers) as pool:
        instances = list(pool.map(evaluate, jobs))
    summary = {}
    for dist in ('unrestricted', 'individual_windows'):
        rows = [r for instance in instances for r in instance['rows'] if r['distribution'] == dist]
        summary[dist] = dict(n=len(rows), oracle=dict(Counter(r['status'] for r in rows)),
                             precedence=sum(r['precedence'] for r in rows),
                             singleton=sum(bool(r['precedence'] or r['singleton']) for r in rows),
                             interval=sum(bool(r['precedence'] or r['interval']) for r in rows))
    args.output.write_text(json.dumps(dict(summary=summary, instances=instances), separators=(',', ':')) + '\n')
    print(json.dumps(summary))
