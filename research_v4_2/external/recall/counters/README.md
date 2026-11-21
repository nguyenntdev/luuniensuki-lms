# Can cumulative practice counters recover useful missing history?

The Duolingo release records a lexeme's elapsed time, prior exposure and prior success counts, even for learners whose earlier encounters fall outside the observed trace. For a repeated lexeme we subtract both the last observed counters and all observed exposures at that earlier timestamp. We compare this signed discrepancy with a forecast that receives the underlying raw counters. An observed time disagreement may reflect a missing review, label timing, or aggregation across lexeme variants. This design tests predictive information available from the recorded fields. [Duolingo data and CC BY-NC terms](https://doi.org/10.7910/DVN/N8XJME) · [Settles and Meeder, ACL 2016](https://aclanthology.org/P16-1174/) · [Prior trace audit](../confirmatory/run/history_audit.json)

The candidate also uses the past gap between observed recall and a training-only lexeme difficulty estimate. We average residuals at the learner and learner–part-of-speech levels and include the immediately previous learner timestamp's mean residual. The same features enter the matched control. Smoothed per-item accuracy, the previous frozen CPU CatBoost, a refitted GPU CatBoost using the former full history, a GPU learner with previous counters only, and a GPU learner with residuals only provide further comparisons. Signed differences can expose irregular records to a finite tree ensemble. The underlying counter and clock inputs are available to the matched control. This question concerns incremental prediction under a particular observed practice schedule. [Sampling, features and practical criterion](design.md) · [Previous 16-control evaluation](../confirmatory/RESULTS.md)

## Reproduction

Use the prior study's verified Duolingo archive, reference implementation, Python dependencies and sealed local model. The CPU model is needed solely for its unchanged forecast on development learners. The preparation stage verifies its stored hash. All new CatBoost fits run serially on a CUDA-capable host using 32% of the device's accessible memory budget per fit. CUDA training can vary across runs. Model fitting and source replay were performed separately. Only the earlier learner buckets 10–13 enter the prepared table. [Input acquisition and prior model reproduction](../confirmatory/README.md)

```bash
set -eu
p=research_v4_2/external/recall/counters
private=$(mktemp -d)
out=$(mktemp -d)
(cd "$p" && sha256sum -c protocol.sha256)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python "$p/test_cutoff.py"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python "$p/prepare.py" "$private/frames.csv.gz"
# Run on the CUDA host with its copy of the prepared table and fit.py.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python "$p/fit.py" "$private/frames.csv.gz" "$out"
node --check "$p/verify.mjs"
node "$p/verify.mjs" private_data/raw/duolingo-hlr/traces.csv.gz "$out"
OPENBLAS_NUM_THREADS=1 python "$p/strata.py" "$private/frames.csv.gz" "$out"
```

## Development results

All five GPU fits completed. Across 122,592 sessions from 1,133 development learners, the reconciled model reduced learner-average log loss by .000414 nats against the matched tree (simultaneous 95% interval .000065 to .000762). One of six comparisons cleared the .005-nat threshold. The frozen CPU predictor scored .333401 against the candidate's .333593. Rows with admissible excess counts represented 208 sessions from 22 learners and contributed −.00000066 nats to the matched gain. Most of the overall difference arose on sessions without earlier counters. These predictions give little support to missing practice as the mechanism. Source replay verified 858,144 forecasts. The separate interval check reproduced all six intervals. [Results](run/result.json) · [Strata](run/strata.json) · [Source verification](run/verification.json)
