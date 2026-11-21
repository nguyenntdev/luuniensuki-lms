# Can action history identify course exit?

The SNAP/JODIE action task identifies 4,066 flagged actions among 411,749. Its 97 targets are learning activities, and a recorded exit after an action need not correspond to a formal withdrawal. We used the first 329,399 actions for fitting and the next 41,175 for model and blend selection. The final 41,175 actions include 1,760 learners and 369 positives. The same learner can recur across periods. Results concern continuing-stream prediction with released features. [Stanford source](https://snap.stanford.edu/data/act-mooc.html) · [Protocol](protocol.md)

| Model | Future ROC AUC | Average precision | Blend minus model in AUC, simultaneous 95% interval |
|---|---:|---:|---|
| Current-action tree | .67891 | .02217 | +.13043 [.09250, .16434] |
| History logistic regression | .77054 | .04930 | +.03880 [.02002, .05898] |
| History tree | .79686 | .06252 | +.01248 [−.00277, .02912] |
| Eight-action recurrent model | .80531 | .08586 | +.00403 [−.00231, .01174] |
| Validation-selected blend | .80934 | .08391 | |

Validation selected a blend with 25% recurrent-model weight and 75% tree weight. The recurrent model alone yielded higher average precision on the future stream. Under the required .01 AUC advantage and positive simultaneous lower endpoint, the candidate passed two of four comparisons. The protocol therefore ended at the first stage. Intervals use 2,000 paired bootstrap replicates over learners in the fixed test period and a Bonferroni family of four. Deployment on another course and training variability lie outside those intervals. [Fitting and validation choices](run/fit.json) · [All contrasts](run/result.json) · [Per-action predictions](run/predictions.csv.gz)

## Data integrity

The raw label file has 411,749 rows and 396,633 unique ACTIONID values. Reading it as a one-to-one keyed table raised an error before fitting. The JODIE authors distribute a single file containing the aligned user, activity, timestamp, four attributes and label. We checked all 411,749 rows against the SNAP action and feature tables. User, activity and time matched exactly. The maximum absolute discrepancy among numeric attributes was below 3e−14. Every label in the raw file in its original row order equalled the corresponding JODIE label. The evaluator takes labels from the combined author file and fixes both source digests. Numeric tolerance for parsing the two feature exports is 1e−12. This repair left the endpoint, event membership, splits, candidates and comparisons intact. [Author download](https://snap.stanford.edu/jodie/mooc.csv) · [Archived copy](https://zenodo.org/records/7213796)

## Replay

Run at repository root in Bash with curl, unzip, Python, PyTorch, pandas, NumPy, SciPy and scikit-learn. Training used a CUDA-enabled RTX 4060 Ti, torch 2.6.0+cu124, NumPy 2.5.4 and scikit-learn 1.9.1. Epoch and tree selection use validation data exclusively. The independently executable scorer recomputes ROC AUC, average precision and intervals from the saved forecasts.

```bash
set -eu
e=research_v4_2/external/landmark/interaction
r=private_data/raw/act-mooc
o=$(mktemp -d)
mkdir -p "$r"
curl -fsSL --retry 3 https://snap.stanford.edu/data/act-mooc.tar.gz -o "$r/act-mooc.tar.gz"
curl -fsSL --retry 3 https://zenodo.org/records/7213796/files/mooc.zip -o "$r/zenodo-mooc.zip"
unzip -p "$r/zenodo-mooc.zip" mooc/mooc.csv > "$r/author-mooc.csv"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python "$e/study.py" "$r/act-mooc.tar.gz" "$r/author-mooc.csv" "$o"
OPENBLAS_NUM_THREADS=1 python "$e/score.py" "$o"
```
