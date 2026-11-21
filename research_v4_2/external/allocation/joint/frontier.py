"""Upper bounds on retrospective capture under the original course budgets."""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from screen import course_choices, prepare


def options(course, labels, label_order):
    f, m = course['f'], course['m']
    y = course['frame'].key.map(labels).to_numpy(dtype=int)
    if label_order:
        f = f[np.argsort(-y[f], kind='stable')]
        m = m[np.argsort(-y[m], kind='stable')]
    f_cases = np.r_[0, np.cumsum(y[f])]
    m_cases = np.r_[0, np.cumsum(y[m])]
    return [(int(n),int(f_cases[n]),int(m_cases[course['k']-n])) for n in course['choices']]


def optimal(courses, tables, female_cases, male_cases, floor):
    # For the same number of captured female cases, a state with more captured
    # male cases dominates for both the utility floor and the recall objective.
    states = {0: (0, ())}
    for table in tables:
        after = {}
        for f, (m, witness) in states.items():
            for n, a, b in table:
                if f+a not in after or m+b > after[f+a][0]:
                    after[f+a] = (m+b, witness+(n,))
        states = after
    feasible = [(min(f/female_cases,m/male_cases),f+m,f,m,witness)
                for f,(m,witness) in states.items() if f+m >= floor]
    result = dict(reachable_female_counts=len(states), feasible_female_counts=len(feasible))
    if feasible:
        recall, captures, f, m, witness = max(feasible)
        result.update(worst_recall=recall, captured=captures, female_captured=f, male_captured=m,
                      female_seats={course['course']:n for course,n in zip(courses,witness)})
    return result


def evaluate(name, raw, saved):
    frame, scores, target, _ = prepare(name, raw)
    courses = course_choices(frame,scores)
    y = target(set(frame.key))
    unrestricted = saved['methods']['unrestricted']
    seats = unrestricted['seats']
    captured = unrestricted['captures_f']+unrestricted['captures_m']
    floor = math.ceil((100*captured-seats)/100)
    out = dict(seats=seats, unrestricted_captured=captured, required_captures=floor)
    for label_order, title in [(False, 'fixed_score_order'), (True, 'free_within_group_order')]:
        tables = [options(c,y,label_order) for c in courses]
        out[title] = optimal(courses,tables,saved['female_cases'],saved['male_cases'],floor)
        out[title]['course_tables'] = {c['course']:rows for c,rows in zip(courses,tables)}
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',type=Path)
    parser.add_argument('results',type=Path)
    args = parser.parse_args()
    saved = json.loads(args.results.read_text())
    print(json.dumps({d:evaluate(d,args.raw,saved[d]) for d in saved}, indent=2))
