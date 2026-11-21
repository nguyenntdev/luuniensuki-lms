"""Replay development controls and test joint enrollment/credit interval cuts."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import screen


def certificate(params, credits, lower, upper):
    periods = params['n_periods']
    for left in range(1, periods + 1):
        for right in range(left, periods + 1):
            width = right - left + 1
            fixed, optional = [], []
            for credit, lo, hi in zip(credits, lower, upper):
                if left <= lo and hi <= right:
                    fixed.append(credit)
                elif lo <= right and left <= hi:
                    optional.append(credit)
            optional.sort()
            outside = periods - width
            need = max(0, width * params['courses_per_period_lb'] - len(fixed),
                       len(credits) - outside * params['courses_per_period_ub'] - len(fixed))
            room = min(len(optional), width * params['courses_per_period_ub'] - len(fixed),
                       len(credits) - outside * params['courses_per_period_lb'] - len(fixed))
            minimum = sum(fixed) + sum(optional[:need])
            maximum = sum(fixed) + sum(optional[len(optional)-room:])
            floor = max(width * params['load_per_period_lb'], sum(credits) - outside * params['load_per_period_ub'])
            ceiling = min(width * params['load_per_period_ub'], sum(credits) - outside * params['load_per_period_lb'])
            if need > room or minimum > ceiling or maximum < floor:
                return dict(interval=[left, right], optional_count=[need, room],
                            possible_load=[minimum, maximum], required_load=[floor, ceiling])


def main():
    archive = Path(sys.argv[1])
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == screen.DIGEST
    instances = json.loads((ROOT / 'balanced/results.json').read_text())['instances']
    assert [case['instance'] for case in instances] == list(range(1, 28, 2))
    rows = []
    for case in instances:
        params, credits, edges = screen.read_instance(archive, case['instance'])
        cap, status = case['cap_attempts'][-1]
        assert status == 'FEASIBLE'
        params['load_per_period_ub'] = cap
        for row in case['rows']:
            lower, upper = screen.windows(len(credits), params['n_periods'], edges, row['request'])
            precedence = any(lo > hi for lo, hi in zip(lower, upper))
            interval = not precedence and bool(screen.capacity_conflict(params, credits, lower, upper, False))
            assert (precedence, interval) == (row['precedence'], row['interval'])
            cut = None if precedence or interval else certificate(params, credits, lower, upper)
            assert not cut or row['exact'] == 'INFEASIBLE'
            rows.append(dict(instance=case['instance'], request=row['request'], baseline=precedence or interval,
                             certificate=cut, exact=row['exact']))
    print(json.dumps(rows, separators=(',', ':')))


if __name__ == '__main__':
    main()
