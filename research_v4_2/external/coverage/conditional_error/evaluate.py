"""Run from this directory with the extracted OULAD directory as argument."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

source = Path(sys.argv[1])
keys = ['code_module', 'code_presentation', 'id_student']
names = ['studentInfo.csv', 'studentRegistration.csv']
info, registration = [pd.read_csv(source / n, na_values='?') for n in names]
earlier = info.loc[info.code_presentation < '2014J', 'id_student']
data = info.merge(registration, on=keys, validate='one_to_one')
eligible = data.date_registration.le(0) & data.date_unregistration.fillna(np.inf).gt(0)
train = data[eligible & data.code_presentation.str.startswith('2013')].reset_index(drop=True)
test = data[eligible & data.code_presentation.eq('2014J') & ~data.id_student.isin(earlier)].reset_index(drop=True)
cols = ['code_module', 'highest_education', 'age_band', 'num_of_prev_attempts', 'studied_credits', 'date_registration']

def encode(a, b):
    vec = DictVectorizer()
    x = vec.fit_transform(a[cols].to_dict('records'))
    scaler = StandardScaler(with_mean=False).fit(x)
    return scaler.transform(x), scaler.transform(vec.transform(b[cols].to_dict('records')))

def predict(a, b):
    x, z = encode(a, b)
    model = LogisticRegression(max_iter=1000).fit(x, a.final_result)
    prob = model.predict_proba(z)
    ordered = np.sort(prob, axis=1)
    return np.column_stack([ordered[:, -1], ordered[:, -1]-ordered[:, -2]]), model.classes_[prob.argmax(axis=1)], (prob*np.log(prob)).sum(axis=1)

fold = train.id_student % 5
oof = np.empty((len(train), 2))
correct = np.empty(len(train), dtype=bool)
for k in range(5):
    mask = fold.eq(k)
    scores, labels, _ = predict(train[~mask], train[mask])
    oof[mask] = scores
    correct[mask] = labels == train.loc[mask, 'final_result']
scores, labels, entropy = predict(train, test)
x, z = encode(train, test)
ranking = {'confidence': scores[:, 0], 'negative_entropy': entropy}
for name, a, b in [('margin_control', oof, scores), ('conditional', hstack([oof,x]), hstack([scores,z]))]:
    ranking[name] = LogisticRegression(max_iter=1000).fit(a, correct).predict_proba(b)[:, 1]

out = test[keys + ['final_result']].copy()
out['prediction'] = labels
err = labels != test.final_result.to_numpy()
ids, inverse = np.unique(test.id_student, return_inverse=True)
rng = np.random.default_rng(42)
counts = {}
risks = {}
samples = {}
for name, score in ranking.items():
    out[name] = score
    accepted = np.zeros(len(test), bool)
    for _, ix in test.groupby('code_module').indices.items():
        accepted[ix[np.argsort(-score[ix], kind='stable')[:7*len(ix)//10]]] = True
    out[name+'_accepted'] = accepted
    counts[name] = {}
    matrices = []
    for course, ix in test.groupby('code_module').indices.items():
        selected = ix[accepted[ix]]
        counts[name][course] = [len(ix), len(selected), int(err[selected].sum())]
        matrices.append([np.bincount(inverse[selected], weights=w, minlength=len(ids)) for w in (None, err[selected])])
    matrix = np.asarray(matrices)
    def worst(totals):
        return (totals[:,1]/totals[:,0]).max(axis=0)
    risks[name] = {'worst': worst(matrix.sum(axis=2)), 'pooled': err[accepted].mean()}
    rng = np.random.default_rng(42)
    samples[name] = np.asarray([worst(matrix @ np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))) for _ in range(2000)])
out.to_csv('predictions.csv.gz', index=False, compression={'method':'gzip','mtime':0})
result = dict(source_sha256={n: hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names}, train=len(train), test=len(test), counts=counts, risk=risks, paired_worst_difference_ci={n:np.percentile(samples['conditional']-s,[2.5,97.5]).tolist() for n,s in samples.items() if n!='conditional'})
Path('result.json').write_text(json.dumps(result, indent=2)+'\n')
print(risks, result['paired_worst_difference_ci'])
