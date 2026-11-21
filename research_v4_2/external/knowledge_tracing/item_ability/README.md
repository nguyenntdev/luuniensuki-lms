# Does item-adjusted learner history improve EdNet forecasts?

The current question appeared in training for 8,616 of 8,981 development responses. The 240 development learners were disjoint from training. The clock model already used question ID, skill, past success counts and delays. We asked whether adding cross-fitted difficulty estimates and a posterior ability estimate from the last sixteen completed responses explains its residual errors. The model uses one primary skill per item. It assumes conditional independence of past responses at a single latent ability over this short window. Item difficulty and ability are predictive summaries of platform interactions. [Source and before-bundle protocol](../temporal/README.md) · [Upstream simpleKT comparator](../published_simplekt/README.md) · [Frozen development design](protocol.md)

Mean next-answer log loss rose from **.57663** with the clock model to **.60596** with the item-adjusted model. Relative to the matched model with current difficulty, prior expected difficulty, window size and raw accuracy, the loss increased by **.00494** (simultaneous 95% interval for the candidate gain −.01231 to .00206). The candidate gained .01585 on upstream item-aware simpleKT, but its simultaneous lower bound was −.00162. Two of fourteen comparisons cleared the .015-nat development margin and had a positive lower bound. Four previous blends in this screen had zero attention weight and duplicate their underlying tree. The multiplicity adjustment retains those prespecified entries. [All losses, intervals and support strata](run/result.json)

| Earlier observations of the current question in training | Development answers | Clock model | Matched model | With ability posterior |
|---|---:|---:|---:|---:|
| 0 | 365 | .56335 | .56384 | .56953 |
| 1–5 | 2,143 | .56584 | .66007 | .67471 |
| 6–19 | 2,360 | .56581 | .57375 | .57770 |
| 20 or more | 4,113 | .58963 | .58920 | .58959 |

The largest loss increase came from items with one to five training observations. For common items the clock and posterior models gave nearly identical mean loss. The observation counts and effects refer to this subsampled release and finite training history. The test does not isolate the causal effect of an exercise on learner ability. The reserved learners remain unused. A separate calculation checked all development labels and support counts and reproduced 300 posterior updates across feature folds. A JavaScript scorer checked 134,715 forecasts against two preceding prediction ledgers. [Feature audit](run/source_check.json) · [Forecast verification](run/verification.json)

## Reproduction

Use the pinned data and environment from the two preceding EdNet studies. Regenerate the same before-bundle cache and the simpleKT item windows. Run the feature construction on the local CPU. Copy its derived compressed table and the training script to a CUDA host, run the three CatBoost fits there, and bring the compressed forecasts back. The original fits used an RTX 4060 Ti. GPU fitting can vary numerically. The scoring and audit commands replay the saved forecasts on CPU.

```bash
set -eu
d=research_v4_2/external/knowledge_tracing/item_ability
cache=private_data/raw/ednet/temporal/cache
(cd "$d" && sha256sum -c protocol.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$d/features.py" "$cache" "$cache/item_ability.csv.gz"
# CUDA host
python "$d/train.py" "$cache/item_ability.csv.gz" estimates.csv.gz
# Put estimates.csv.gz into "$d/run" before scoring a new fit.
python "$d/score.py" "$d"
node --check "$d/verify.mjs"
node "$d/verify.mjs" "$d"
python "$d/audit.py" "$cache" "$d"
```
