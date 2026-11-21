# Does client-local selection on AUC improve later course rankings?

On 8,815 registrations from 8,505 OULAD learners, confidence-guarded selection reached .64328 equal-module AUC, compared with .63436 for ungated selection and .64578 for fixed half-transfer. The gain against FedAvg was .04140 (simultaneous 95% interval .00500 to .07780). The difference against fixed half-transfer was −.00250 (−.00582 to .00081). Seven of the 32 paired comparisons cleared both registered thresholds. Seven module clients belong to a single university. The later term had already informed other development studies. [Frozen protocol](protocol.md) · [All contrasts](run/summary.json)

DDD was the only client with enough calibration evidence to switch. Its local-only calibration gain was .01358 (.00369 to .02348 after the four-weight adjustment). On the later DDD cohort the same switch reduced AUC from .64045 to .62293. The fitted rule reuses earlier GPU forecasts and incurs no additional model fit. [All calibration weights](run/weights.json) · [Later scores by course](run/scores.csv)

A post hoc upper bound enumerates the five allowed weights within each client. The macro average is separable, so summing the seven largest local AUCs gives the exact maximum for this family on these observations. Even selecting with full knowledge of the later outcomes could gain only .00628 over fixed half-transfer. The original .02 practical margin is out of reach for this family of frozen scores on this roster. The oracle cannot forecast learners. [Upper bound](run/bound.json)

From the repository root, use the scientific Python environment with NumPy, pandas, SciPy and scikit-learn.

```sh
d=research_v4_2/external/landmark/federated/rank_gate
out=$(mktemp -d)
OPENBLAS_NUM_THREADS=1 python "$d/evaluate.py" "$out"
for f in scores.csv summary.json predictions.csv.gz weights.json; do cmp "$d/run/$f" "$out/$f"; done
OPENBLAS_NUM_THREADS=1 python "$d/verify.py" | diff - "$d/run/bound.json"
```
