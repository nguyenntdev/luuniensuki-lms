# How the risk model changes attainable review outcomes

One CatBoost point model and forty bootstrap fits per cohort used the same enrollment covariates, training indices, course budgets and prefix rules as the logistic study. All 82 fits ran on an RTX 4060 Ti. The suspected infeasibility in Portugal was known when the [design](design.md) was written. The evaluation is conditional on those two previously observed cohorts.

| Outcome | OULAD | UCI 697 |
|---|---:|---:|
| Eligible learners / review seats | 6,959 / 695 | 1,767 / 168 |
| Logistic / CatBoost ROC AUC | .5870 / .5252 | .7352 / .7347 |
| Logistic / CatBoost log loss | .4506 / .4757 | .5424 / .5429 |
| Pooled thresholds / best comparator worst-group recall under boosting | 15.37% / 15.59% | 15.90% / 16.15% |
| Pooled thresholds / unrestricted precision under boosting | 24.89% / 25.18% | 55.95% / 56.55% |
| Maximum cases attainable under the boosted score order | 185 | 101 |
| Required captures using the original logistic floor | 201 | 104 |
| Required captures using the new boosted floor | 169 | 94 |

Even an allocator given all outcomes would miss the original capture requirement by 16 UK cases and three Portuguese cases under the boosted order. Using each scorer's own unrestricted precision as reference changes the scientific interpretation. In Portugal the new floor is feasible because it fell by ten cases, even though maximum captures fell from 102 to 101. Under the new floor the label-informed upper bounds for worst-group recall are 16.23% and 18.46%. They describe achievable counts after seeing outcomes. Lower bounds for the pooled policy's actual precision difference versus unrestricted were −2.20 and −5.46 percentage points, respectively. Both miss the allowed −1 point. [All nine policies](run/results.json) · [Risk scores by group](run/risk_scores.json) · [Original absolute floor](run/logistic_floor.json) · [Scorer-specific floor](run/frontier.json)

## Reproduction

From the repository root use the Python environment of the [parent study](../README.md) for the local replay. Forecast archives contain probabilities in committed row order, plus an order digest. Each replay checks that digest against the verified source cohort. Two separate runs reproduced every aggregate file byte-for-byte, including option tables. The independent bitset calculation checks both floor definitions and the integer solver verifier checks both predicted optima. GPU training may vary numerically across executions.

```sh
set -eu
b=research_v4_2/external/allocation/joint/boosted
(cd "$b" && sha256sum -c design.sha256)
(cd "$b/run" && sha256sum -c forecasts.sha256)
out=$(mktemp -d)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$b/evaluate.py" private_data/raw "$b/run" "$out"
python "$b/verify_floors.py" "$out"
diff -r --exclude='*.npz' --exclude='forecasts.sha256' "$b/run" "$out"
```

To regenerate forecasts, use `python "$b/export.py" private_data/raw /path/to/staging`. Copy the exported training/evaluation matrices, order digests and train.py to a CUDA host with NumPy, pandas and CatBoost installed. Run `python train.py /path/to/staging` there and supply the two resulting forecast archives as the second positional argument of evaluate.py. The evaluation outcomes stay local throughout GPU training.
