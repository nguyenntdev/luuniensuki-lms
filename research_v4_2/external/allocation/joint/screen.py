"""Compare independently chosen course thresholds with a coordinated allocation."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'confirmatory'))
from benchmark import cohort, outcomes, predict, verified_archive
from policies import allocate, fair_rank


def prepare(name, raw):
    if name == 'oulad':
        with verified_archive(name, raw) as archive:
            rows, _, cat, num = cohort(name, archive)
            train = rows[rows.code_presentation.eq('2013B')].copy()
            test = rows[rows.code_presentation.eq('2013J')].copy()
            history = outcomes(archive, name, set(train.key))
        def target(keys):
            with verified_archive(name, raw) as archive:
                return outcomes(archive, name, keys)
    else:
        path = raw / 'uci/dropout-697/source.zip'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == 'e90e55fd65ec462ae283ebeb2cca409319e3460ed898d8754f62fb35cc83a65d'
        cat = ['Course', 'Gender', 'Previous qualification', 'Application mode']
        num = ['Age at enrollment', 'Admission grade', 'Previous qualification (grade)']
        with ZipFile(path) as archive:
            rows = pd.read_csv(archive.open('data.csv'), sep=';', usecols=cat+num)
        rows['sid'] = rows['key'] = rows.index.astype(str)
        rows['pool'] = rows.Course.astype(str)
        assert set(rows.Gender) == {0,1}
        rows['female'] = rows.Gender.eq(0)
        fit = rows.key.map(lambda key: int(hashlib.sha256(key.encode()).hexdigest(),16) % 10 < 6)
        train, test = rows[fit].copy(), rows[~fit].copy()
        def target(keys):
            with ZipFile(path) as archive:
                labels = pd.read_csv(archive.open('data.csv'), sep=';', usecols=['Target']).Target
            labels.index = labels.index.astype(str)
            selected = labels.loc[sorted(keys)]
            assert set(selected).issubset({'Dropout', 'Enrolled', 'Graduate'})
            return selected.eq('Dropout').to_dict()
        history = target(set(train.key))
    assert set(train.sid).isdisjoint(test.sid) and test.sid.is_unique
    eligible = test.groupby('pool').female.transform(lambda x: len(x) >= 10 and 0 < x.sum() < len(x))
    excluded = test.loc[~eligible].groupby('pool').size().to_dict()
    test = test[eligible].reset_index(drop=True)
    scores = predict(train, test, cat, num, history)
    return test.assign(p=scores[0]), scores, target, dict(train=len(train), excluded=excluded)


def course_choices(test, scores):
    courses = []
    for course, frame in test.groupby('pool'):
        frame = frame.sort_values(['p','sid'], ascending=[False,True])
        k = len(frame)//10
        p = frame.p.to_numpy()
        female = frame.female.to_numpy()
        ranks, table = allocate(scores[:, frame.index], female, k)
        f, m = np.flatnonzero(female), np.flatnonzero(~female)
        choices = np.arange(max(int(table[-1]), k-len(m)), min(k,len(f))+1)
        fc = np.r_[0.,np.cumsum(p[f])][choices]
        mc = np.r_[0.,np.cumsum(p[m])][k-choices]
        courses.append(dict(course=str(course), frame=frame, k=k, ranks=ranks, table=table,
                            f=f, m=m, choices=choices, fc=fc, mc=mc, total=fc+mc,
                            fmass=p[f].sum(), mmass=p[m].sum()))
    return courses


def exact(courses, local_cap):
    # Each binary variable selects a within-course threshold pair. The final
    # continuous variable is the lesser of the two pooled predicted recalls.
    ends = np.cumsum([len(c['choices']) for c in courses])
    starts = np.r_[0,ends[:-1]]
    size = ends[-1]+1
    lows, highs = np.zeros(size), np.ones(size)
    rows, lower, upper = [], [], []
    for index, c in enumerate(courses):
        begin, end = starts[index], ends[index]
        row = np.zeros(size)
        row[begin:end] = 1
        rows.append(row)
        lower.append(1.)
        upper.append(1.)
        if local_cap:
            highs[begin:end] = c['total'] >= max(c['total']) - .01*c['k'] - 1e-10
    for capture, mass in [('fc','fmass'), ('mc','mmass')]:
        values = np.concatenate([c[capture] for c in courses]) / sum(c[mass] for c in courses)
        rows.append(np.r_[values,-1.])
        lower.append(0.)
        upper.append(np.inf)
    utility = np.r_[np.concatenate([c['total'] for c in courses]),0.]
    rows.append(utility)
    lower.append(sum(max(c['total']) - .01*c['k'] for c in courses))
    upper.append(np.inf)
    constraints = LinearConstraint(np.array(rows), lower, upper)
    def solve(obj):
        res = milp(obj, integrality=np.r_[np.ones(size-1),0], bounds=Bounds(lows, highs),
                   constraints=constraints, options={'mip_rel_gap':0.})
        if not res.success:
            raise RuntimeError(res.message)
        return res
    best = solve(np.r_[np.zeros(size-1),-1.])
    # Fix utility tiebreak in normalized recall units.
    lows[-1] = best.x[-1] - 1e-8
    chosen = solve(-utility)
    picks = [int(np.argmax(chosen.x[a:b])) for a,b in zip(starts,ends)]
    return picks, float(best.x[-1])


def greedy(courses):
    choices = [int(np.argmax(c['total'])) for c in courses]
    def value(indices):
        sums = {key: sum(c[key][x] for c,x in zip(courses,indices)) for key in ('fc','mc','total')}
        return min(sums['fc']/sum(c['fmass'] for c in courses),
                   sums['mc']/sum(c['mmass'] for c in courses)), sums['total']
    floor = value(choices)[1] - .01*sum(c['k'] for c in courses)
    while True:
        current = value(choices)
        best_val, best_pick = current, choices
        for j,c in enumerate(courses):
            for step in (-1,1):
                val = choices[j]+step
                if 0 <= val < len(c['choices']):
                    trial = choices.copy()
                    trial[j] = val
                    objective = value(trial)
                    if objective[1] >= floor-1e-10 and objective > best_val:
                        best_val, best_pick = objective, trial
        if choices == best_pick:
            return choices
        choices = best_pick


def report(name, raw, output):
    frame, scores, target, source = prepare(name, raw)
    courses = course_choices(frame,scores)
    primary, optimum = exact(courses,False)
    local, local_opt = exact(courses,True)
    choices = dict(pooled=primary, pooled_local_cap=local, pooled_greedy=greedy(courses))
    cases = []
    for j,c in enumerate(courses):
        for policy, picks in choices.items():
            n = int(c['choices'][picks[j]])
            c['ranks'][policy] = fair_rank(c['f'][:n],c['m'][:c['k']-n],c['table'])
        ordered = c['frame'].copy()
        for policy, idx in c['ranks'].items():
            assert len(set(idx)) == c['k']
            if policy != 'unrestricted':
                assert (ordered.female.to_numpy()[idx].cumsum() >= c['table']).all()
            ordered[policy] = np.isin(np.arange(len(ordered)), idx)
        cases.append(ordered)
    data = pd.concat(cases,ignore_index=True)
    policies = list(courses[0]['ranks'])
    predicted = data.p.to_numpy()
    f = data.female.to_numpy()
    chosen = data[policies].to_numpy()
    util = predicted @ chosen
    predicted_worst = np.minimum(predicted[f] @ chosen[f]/predicted[f].sum(),
                                 predicted[~f] @ chosen[~f]/predicted[~f].sum())
    primary_index = policies.index('pooled')
    assert predicted_worst[primary_index] >= optimum-2e-7
    assert predicted_worst[policies.index('pooled_local_cap')] >= local_opt-2e-7
    assert predicted_worst[primary_index] >= predicted_worst[policies.index('pooled_greedy')]-2e-7
    raw_labels = target(set(data.key))
    y = data.key.map(raw_labels).to_numpy(bool)
    def measure(ix):
        selected = chosen[ix]
        positives = y[ix]
        a = f[ix] & positives
        b = ~f[ix] & positives
        return np.stack([np.minimum(selected[a].sum(0)/a.sum(), selected[b].sum(0)/b.sum()),
                         selected[positives].sum(0)/selected.sum(0)])
    ix = np.arange(len(y))
    observed = measure(ix)
    rng = np.random.default_rng(1701)
    pools = list(data.groupby('pool').indices.values())
    draws = np.array([measure(np.concatenate([rng.choice(g,len(g)) for g in pools])) for _ in range(5000)])
    differences = draws[:,:,primary_index,None]-draws
    intervals = np.nanquantile(differences, [.025,.975],axis=0)
    results = {}
    for i,p in enumerate(policies):
        results[p] = dict(seats=int(chosen[:,i].sum()), swaps=int((chosen[:,primary_index]&~chosen[:,i]).sum()),
                          captures_f=int((chosen[:,i]&f&y).sum()), captures_m=int((chosen[:,i]&~f&y).sum()),
                          score_utility=float(util[i]), predicted_worst=float(predicted_worst[i]),
                          recall=float(observed[0,i]),precision=float(observed[1,i]),
                          gain_recall_ci=intervals[:,0,i].tolist(),gain_precision_ci=intervals[:,1,i].tolist(),
                          defined_draws=np.isfinite(differences[:,:,i]).sum(axis=0).tolist())
    with (output/f'{name}_options.csv').open('w',newline='') as fp:
        cols = ['course','k','f_count','female_capture','male_capture','female_mass','male_mass','pooled','local_cap','greedy']
        w = csv.writer(fp); w.writerow(cols)
        for j,c in enumerate(courses):
            for i,n in enumerate(c['choices']):
                w.writerow([c['course'],c['k'],n,c['fc'][i],c['mc'][i],c['fmass'],c['mmass'],
                            int(primary[j]==i),int(local[j]==i),int(choices['pooled_greedy'][j]==i)])
    return dict(**source, learners=len(data), pools=len(pools), female_cases=int((f&y).sum()),
                male_cases=int((~f&y).sum()), optimum=optimum, local_cap_optimum=local_opt, methods=results)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw',type=Path)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    summary={d:report(d,args.raw,args.output) for d in ('oulad','uci697')}
    (args.output/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
