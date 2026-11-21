"""Audit frozen held-out requests using a second assignment encoding."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import screen


def witness_check(witness, params, credits, edges, request):
    assert len(witness) == len(credits) and all(1 <= t <= params['n_periods'] for t in witness)
    assert all(witness[a] < witness[b] for a, b in edges)
    assert all(witness[i] == p for i, p in request)
    for t in range(1, params['n_periods'] + 1):
        c = [w for i, w in enumerate(credits) if witness[i] == t]
        assert params['courses_per_period_lb'] <= len(c) <= params['courses_per_period_ub']
        assert params['load_per_period_lb'] <= sum(c) <= params['load_per_period_ub']


def verify_instance(job):
    path, result = job
    params, credits, edges = screen.read_instance(path, result['instance'])
    cap = max(map(int, result['caps']))
    params['load_per_period_ub'] = cap
    witness_check(result['initial'], params, credits, edges, ())
    checked = Counter()
    unknowns = []
    for row in result['rows']:
        request = row['request']
        reported = {k['status'] for k in row['methods'].values()}
        assert len(reported) == 1
        status = reported.pop()
        if status == 'FEASIBLE':
            for v in row['methods'].values():
                witness_check(v['witness'], params, credits, edges, request)
        else:
            oracle, alternative = screen.exact(params, credits, edges, request, budget=25)
            assert oracle in ('INFEASIBLE', 'FEASIBLE')
            if status == 'INFEASIBLE':
                assert oracle == status
            else:
                assert status == 'UNKNOWN'
                unknowns.append(dict(instance=result['instance'], request=request, decision=oracle, witness=alternative))
        checked[status] += 1
    return checked, unknowns


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    assert hashlib.sha256(args.archive.read_bytes()).hexdigest() == screen.DIGEST
    data = json.loads((HERE/'results.json').read_text())['instances']
    assert [d['instance'] for d in data] == list(range(2, 29, 2))
    with ProcessPoolExecutor(args.workers) as pool:
        records = list(pool.map(verify_instance, [(args.archive, r) for r in data]))
    counts = sum((r[0] for r in records), Counter())
    print(json.dumps(dict(original=dict(counts), resolved_after_timing=[u for r in records for u in r[1]]), indent=2))
