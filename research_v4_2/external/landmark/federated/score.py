"""Development score and learner-clustered paired AUC influence intervals."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import log_loss, roc_auc_score

run = Path(sys.argv[1])
candidate = sys.argv[2] if len(sys.argv) > 2 else "adapted"
frame = pd.read_csv(run / "predictions.csv.gz")
methods = list(frame.columns[5:])
assert frame.columns[4] == "y" and candidate in methods
groups = list(frame.groupby("code_module"))
rows = []
influences = {k: np.zeros(len(frame)) for k in methods}
for course, group in groups + [("pooled",frame)]:
    y = group.y.to_numpy()
    for method in methods:
        prob = group[method].to_numpy()
        auc = roc_auc_score(y, prob)
        rows.append(dict(course=course, method=method, registrations=len(y), positives=int(y.sum()),
                         auc=auc, log_loss=log_loss(y, prob)))
        if course == "pooled":
            continue
        # Positive/negative placements give tie-corrected influence on the U-statistic.
        for label in (0,1):
            mask = y == label
            ref = np.sort(prob[~mask])
            left = np.searchsorted(ref,prob[mask],"left")
            right = np.searchsorted(ref,prob[mask],"right")
            placement = (left + right) / (2 * len(ref))
            if label == 0:
                placement = 1 - placement
            assert np.isclose(placement.mean(), auc)
            influences[method][group.index[mask]] = (placement - auc) / (mask.sum() * len(groups))
scores = pd.DataFrame(rows)
scores.to_csv(run/"scores.csv",index=False)
macro = scores[scores.course != "pooled"].groupby("method").auc.mean()
cluster = pd.DataFrame(influences).groupby(frame.learner).sum()
z = norm.isf(.025 / (len(methods)-1))
contrasts = {}
for name in methods:
    if name == candidate:
        continue
    diff = cluster[candidate] - cluster[name]
    se = np.sqrt(np.square(diff).sum() * len(diff) / (len(diff)-1))
    gain = macro[candidate] - macro[name]
    contrasts[name] = dict(auc_gain=gain, simultaneous_ci95=[gain-z*se,gain+z*se],
                           clears_margin=bool(gain >= .02 and gain-z*se>0))
result=dict(registrations=len(frame), learners=len(cluster), clients=len(groups), macro_auc=macro.to_dict(),
            contrasts=contrasts, advances=all(c["clears_margin"] for c in contrasts.values()))
(run/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
