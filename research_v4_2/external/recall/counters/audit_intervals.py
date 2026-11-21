"""Recompute all simultaneous intervals and the screen decision from archived forecasts."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

out=Path(sys.argv[1])
r=json.loads((out/"result.json").read_text())
p=pd.read_csv(out/"forecasts.csv.gz")
methods=list(r["mean_learner_loss"])
prob=np.clip(p[methods].values,1e-8,1-1e-8)
y=p.y.to_numpy()[:,None]
nll=-(np.log(prob)*y+np.log1p(-prob)*(1-y))
by_learner=pd.DataFrame(nll,columns=methods).groupby(p.learner).mean()
assert len(by_learner)==r["learners"]
passed={}
for name in r["gains"]:
    differences=by_learner[name]-by_learner["reconciled"]
    ci=ttest_1samp(differences,popmean=0).confidence_interval(confidence_level=1-.05/len(r["gains"]))
    np.testing.assert_allclose(r["simultaneous_ci95"][name],ci,atol=1e-12,rtol=0)
    passed[name]=bool(differences.mean()>=.005 and ci.low>0)
assert all(passed.values())==r["advance"]
print(json.dumps({"intervals_checked":len(passed),"comparisons_passing":sum(passed.values()),"passes":passed},indent=2))
