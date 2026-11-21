"""Verify score optima by a separate concave-envelope model, and capture bounds by bitsets."""
import csv
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def check_optimum(records, local):
    courses = sorted({r['course'] for r in records})
    n = len(courses)
    size = 3*n + 1
    low = np.zeros(size)
    high = np.full(size,np.inf)
    constraints, bounds = [], []
    masses = np.zeros(2)
    floors = []
    for i,course in enumerate(courses):
        group=[r for r in records if r['course']==course]
        counts=np.array([int(r['f_count']) for r in group])
        assert np.array_equal(counts,np.arange(counts[0],counts[-1]+1))
        low[i],high[i]=counts[0],counts[-1]
        caps=np.array([[float(r[k]) for r in group] for k in ('female_capture','male_capture')])
        floor=caps.sum(axis=0).max()-.01*int(group[0]['k'])
        floors.append(floor)
        for j,key in enumerate(('female_mass','male_mass')):
            masses[j]+=float(group[0][key])
            slopes=np.diff(caps[j])
            assert np.all(np.diff(slopes)<=1e-9)
            # A concave PWL function is the minimum of its extended segment lines.
            for t,slope in enumerate(slopes if len(slopes) else [0.]):
                row=np.zeros(size)
                row[i]=-slope
                row[(j+1)*n+i]=1
                constraints.append(row)
                bounds.append(caps[j,t]-slope*counts[t])
        if local:
            row=np.zeros(size)
            row[n+i]=row[2*n+i]=-1
            constraints.append(row); bounds.append(-floor)
    row=np.zeros(size)
    row[n:3*n]=-1
    constraints.append(row); bounds.append(-sum(floors))
    for j in range(2):
        row=np.zeros(size)
        row[(j+1)*n:(j+2)*n]=-1
        row[-1]=masses[j]
        constraints.append(row); bounds.append(0)
    objective=np.zeros(size)
    objective[-1]=-1
    res=milp(objective,integrality=np.r_[np.ones(n),np.zeros(2*n+1)],bounds=Bounds(low,high),
             constraints=LinearConstraint(np.array(constraints),-np.inf,bounds),options={'mip_rel_gap':0.})
    assert res.success
    return -res.fun


def check_frontier(table, required, group_cases):
    states={0:1}
    for options in table['course_tables'].values():
        next_states={}
        for _,f,m in options:
            for total,mask in states.items():
                next_states[f+total]=next_states.get(f+total,0) | mask<<m
        states=next_states
    eligible=[(f,mask.bit_length()-1) for f,mask in states.items() if f+mask.bit_length()-1>=required]
    assert len(eligible)==table['feasible_female_counts'] and len(states)==table['reachable_female_counts']
    if eligible:
        best=max(min(f/group_cases[0],m/group_cases[1]) for f,m in eligible)
        assert abs(best-table['worst_recall'])<1e-12
        assert (1<<table['male_captured']) & states[table['female_captured']]


def verify(folder):
    summary=json.loads((folder/'results.json').read_text())
    frontier=json.loads((folder/'frontier.json').read_text())
    for name,study in summary.items():
        with (folder/f'{name}_options.csv').open() as fp:
            records=list(csv.DictReader(fp))
        for local,key in [(False,'optimum'),(True,'local_cap_optimum')]:
            other=check_optimum(records,local)
            assert abs(other-study[key])<2e-7, (name, key, other, study[key])
        for key in ('fixed_score_order','free_within_group_order'):
            check_frontier(frontier[name][key],frontier[name]['required_captures'],
                           (study['female_cases'],study['male_cases']))
        print(name, 'both score optima and both observed-outcome frontiers verified')


if __name__=='__main__':
    verify(Path(sys.argv[1]))
