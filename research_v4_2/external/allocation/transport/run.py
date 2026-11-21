from pathlib import Path
import hashlib
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "confirmatory"))
from benchmark import cohort, outcomes, predict, verified_archive
from policies import allocate, fair_rank

with verified_archive("oulad", "private_data/raw") as archive:
    data, _, cat, num = cohort("oulad", archive)
    early = data[data.code_presentation.eq("2013B")]
    even = early.sid.map(lambda s: hashlib.sha256(s.encode()).digest()[0] % 2 == 0)
    fit, calibration = early[even], early[~even].copy()
    target = data[data.code_presentation.eq("2013J") & data.pool.isin(calibration.pool)].copy()
    history = outcomes(archive, "oulad", set(early.key))
    inputs = pd.concat([calibration, target])
    scores = predict(fit, inputs, cat, num, history)
    calibration["p"] = scores[0, :len(calibration)]
    calibration["y"] = calibration.key.map(history)
    target["column"] = np.arange(len(calibration), len(inputs))
    target["p"] = scores[0, target.column]
    pools = []
    for name, pool in target.groupby("pool"):
        pool = pool.sort_values(["p", "sid"], ascending=[False, True]).copy()
        k = max(1, len(pool)//10)
        p, female = pool.p.to_numpy(), pool.female.to_numpy()
        ranks, table = allocate(scores[:, pool.column], female, k)
        f, m = np.flatnonzero(female), np.flatnonzero(~female)
        ceiling = p[ranks["fair"]].sum()
        for policy, ref in [("transport", calibration[calibration.pool.eq(name)]),
                            ("pooled", calibration)]:
            corrected = p.copy()
            for group in (True, False):
                subset = ref[ref.female.eq(group)]
                corrected[female == group] *= (5+subset.y.sum())/(5+subset.p.sum())
            corrected = corrected.clip(0, 1)
            options = []
            for n in range(max(table[-1], k-len(m)), min(k,len(f))+1):
                ids = np.r_[f[:n], m[:k-n]]
                utility = p[ids].sum()
                if utility >= ceiling-.01*k-1e-10:
                    recall = min(corrected[f[:n]].sum()/corrected[f].sum(),
                                 corrected[m[:k-n]].sum()/corrected[m].sum())
                    options.append((recall, utility, -n))
            n = -max(options)[2]
            ranks[policy] = fair_rank(f[:n], m[:k-n], table)
        for policy, selected in ranks.items():
            pool[policy] = np.isin(np.arange(len(pool)), selected)
            assert pool[policy].sum() == k
        pools.append(pool)
    rows = pd.concat(pools, ignore_index=True)
    digest = hashlib.sha256(rows[["key","p",*ranks]].to_csv(index=False).encode()).hexdigest()
    labels = outcomes(archive, "oulad", set(rows.key))
    rows["y"] = rows.key.map(labels)
print("Decision digest", digest)
decisions = rows[list(ranks)].to_numpy()
y, f = rows.y.to_numpy(), rows.female.to_numpy()
def metrics(i):
    selected = decisions[i]
    cases = selected & y[i,None]
    return np.minimum(cases[f[i]].sum(0)/(y[i]&f[i]).sum(),
                      cases[~f[i]].sum(0)/(y[i]&~f[i]).sum()), cases.sum(0)/selected.sum(0)

rng = np.random.default_rng(1701)
strata = list(rows.groupby("pool").indices.values())
recall, precision = metrics(np.arange(len(rows)))
boot = np.array([metrics(np.concatenate([rng.choice(i,len(i)) for i in strata])) for _ in range(5000)])
j = list(ranks).index("transport")
out = []
for i, name in enumerate(ranks):
    ci = np.quantile(boot[:,:,j]-boot[:,:,i], [.025,.975],axis=0)
    out.append([name,len(rows),decisions[:,i].sum(),recall[i],precision[i],
                (decisions[:,j]&~decisions[:,i]).sum(),*ci[:,0],*ci[:,1]])
pd.DataFrame(out,columns="policy learners seats recall precision replaced recall_lo recall_hi precision_lo precision_hi".split()).to_csv(HERE/"results.csv",index=False)
