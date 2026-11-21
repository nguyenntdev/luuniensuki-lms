"""Run with the cached input directory as the sole argument; writes JSON to stdout."""
import collections
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1])
def load(name, digest):
    raw = (root / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    return json.loads(raw)

def norm(text):
    return ' '.join(text.lower().split())

def key(row):
    return row['conversation_id'], norm(row['conversation_history'])

records = load('mrbench_v3_devset.json', 'a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c')
sources = {key(r): r['Data'] for r in load('MRBench_V2.json', 'a8792225075533d15c23e1c903d0c649f19708ee93f5c3d8267eaa6ab623aac1')}
names = sorted('Gemini GPT4 Llama31405B Llama318B Mistral Sonnet'.split())
rubrics = 'Mistake_Identification Mistake_Location Providing_Guidance Actionability'.split()
counts = {k: collections.Counter() for k in rubrics}
cases = []
for r in records:
    values = []
    for name in names:
        labels = r['tutor_responses'].get(name, {}).get('annotation', {})
        values.append([labels.get(k, '<missing>') for k in rubrics])
        for k, value in zip(rubrics, values[-1]):
            counts[k][value] += 1
    labels = np.array(values)
    if np.isin(labels, ['Yes', 'No', 'To some extent']).all():
        opening = re.split(r'\bstudent\s*:', key(r)[1], maxsplit=1)[0].strip()
        cases.append((sources.get(key(r)), opening, np.stack([labels[:, 2]=='Yes', (labels=='Yes').all(axis=1)])))
out = dict(labels=counts, eligible=len(cases), tutors=names, endpoints=['guidance','joint'])
for target, origin in [('MathDial','Bridge'), ('Bridge','MathDial')]:
    test = [c for c in cases if c[0]==target]
    groups, ix = np.unique([c[1] for c in test], return_inverse=True)
    train = [c[2] for c in cases if c[0]==origin and c[1] not in groups]
    picks = np.sum(train,axis=0).argmax(axis=1)
    scores = np.array([c[2] for c in test])
    ranks = scores.sum(axis=0).astype(int)
    reversals = [[names[i], names[j]] for i,j in itertools.combinations(range(len(names)),2)
                 if np.prod(ranks[:,i]-ranks[:,j])<0]
    result = dict(train=len(train), test=len(test), groups=len(groups), picks=[names[i] for i in picks],
                  totals=ranks.tolist(), reversals=reversals, comparisons={})
    draws = np.random.default_rng(42).integers(len(groups), size=(10000,len(groups)))
    sizes = np.bincount(ix)[draws].sum(axis=1)
    for e, endpoint in enumerate(out['endpoints']):
        a = scores[:,e,:]
        base = a[:,picks[0]].astype(float)
        for policy, val in [('guidance_fixed',base),('joint_fixed',a[:,picks[1]]),('uniform',a.mean(axis=1)),('oracle',a.max(axis=1))]:
            diff = val-base
            boot = np.bincount(ix, weights=diff)[draws].sum(axis=1)/sizes
            result['comparisons'][endpoint+'_'+policy] = dict(rate=val.mean(),delta=diff.mean(),interval=np.quantile(boot,[.025,.975]).tolist())
    out[target] = result
print(json.dumps(out,indent=2))
