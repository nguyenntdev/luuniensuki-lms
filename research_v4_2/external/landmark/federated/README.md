# Can local adaptation improve federated day-60 early warning?

Seven Open University modules served as simulated clients. On 8,815 eligible 2014J registrations from 8,505 learners, local slope adaptation increased module-macro AUC from **.59629 for FedAvg to .62528**. Independent local training reached .62003, and a weakly regularized local update reached **.63116**. The candidate cleared the exploratory criterion for four of seven comparators. This development screen therefore leaves the original P13 superiority claim open. [Design](design.md) · [Paired effects](run/summary.json) · [Module-level AUC and log loss](run/scores.csv)

## Design and interpretation

The 2014J presentation and its day-60 labels had already been evaluated in the parent study. All 2014J learners with registration by day 60 were excluded from all earlier training records. Training retained only students still eligible for support on day 60. The four fixed features come from the parent risk-set study. The seven modules have different learner populations and different early engagement patterns. We tested whether their training labels support different slopes for recency and participation. The unit of federation is a course within a single institution. Source preprocessing used the published archive centrally, and each optimizer then consumed only the rows permitted to its client or centralized baseline. Earlier presentation codes define temporal order. Exact dates on which archived final labels became available were unobserved. [Dataset paper](https://doi.org/10.1038/sdata.2017.171) · [Training and evaluation counts by client and presentation](run/counts.csv) · [Original risk-set study](../manuscript.md)

We implemented synchronous example-weighted FedAvg and the FedProx local objective with full participation. The shared logistic fits used 40 rounds and five full-batch steps per round. The candidate computes one additional local Newton step with ridge stabilization after the last broadcast. All three adaptations have the same global training history and communication budget. The weak-ridge control uses a near-zero penalty; the intercept-only control can shift probabilities but preserves ordering within a module. The model-vector traffic is 3,240 bytes per client for training and final distribution, excluding protocol headers. Pooled logistic and independent local fits each receive 200 steps; centralized CatBoost uses 200 depth-4 trees. All training ran on the external RTX 4060 Ti. Single configurations limit the comparison; the development data can guide future tuning. Neither differential privacy nor the operational cost of a cross-institution deployment was evaluated. [McMahan et al., AISTATS 2017](https://proceedings.mlr.press/v54/mcmahan17a.html) · [Li et al., MLSys 2020](https://proceedings.mlsys.org/paper_files/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html) · [Execution record](run/execution.json)

| Model | Equal-module mean AUC |
|---|---:|
| Pooled logistic | .59150 |
| FedAvg | .59629 |
| FedProx | .59651 |
| Pooled CatBoost | .60160 |
| Independent local logistic | .62003 |
| FedAvg + intercept adjustment | .59629 |
| FedAvg + local regularized Newton step | .62528 |
| FedAvg + weak-ridge local Newton step | .63116 |

AUC gain over FedAvg was .02899 (simultaneous 95% interval .01744–.04053). Against locally trained logistic regression, the gain was .00525 (−.00136 to .01186). Against weak-ridge local adjustment, the difference was −.00588 (−.03654 to .02477). Intervals use paired AUC placement influence functions, clustered by learner across registrations, and a Bonferroni correction over seven comparisons. They condition on the observed modules and fitted models. The screen requires a point gain of at least .02 and a positive simultaneous lower bound. An independently implemented pairwise scorer recovered all eight macro AUCs and checked 70,520 forecasts against the official row memberships and labels. [Forecasts](run/predictions.csv.gz) · [Verification](run/verification.json)

## Reproduction

Use Python 3.12, NumPy, pandas, SciPy, scikit-learn, CatBoost 1.2.8, PyTorch 2.6.0 with CUDA, Node.js and unzip. The current data source is the public UCI release, with the pinned archive verified during preparation. Follow the OULAD provider terms on reuse. CPU preparation can be performed locally; copy the resulting table and training script to the CUDA host and run the fitting command there. Copy the three fitting artifacts back before scoring locally. GPU CatBoost can differ slightly in repeated fits. The stored forecasts reproduce the reported scores offline. [UCI release](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset) · [Source acquisition and archive hash](../manuscript.md)

```bash
set -eu
study=research_v4_2/external/landmark/federated
raw=private_data/raw/oulad/2013-2014/oulad.zip
work=$(mktemp -d)
(cd "$study" && sha256sum -c protocol.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
python "$study/prepare.py" "$raw" "$work/input.csv"
# Execute on a CUDA host.
python "$study/train.py" "$work/input.csv" "$work/run"
python "$study/score.py" "$work/run"
node --check "$study/verify.mjs"
node "$study/verify.mjs" "$raw" "$work/run"
```
