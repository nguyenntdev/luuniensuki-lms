# Communication and predictive discrimination in federated day-60 withdrawal prediction

## Abstract

Can a more accurate federated optimizer or a local update improve withdrawal-risk ranking across courses? We studied seven simulated module clients in the Open University Learning Analytics Dataset (OULAD). Earlier presentations supplied 16,063 training registrations. A learner-disjoint development presentation supplied 8,815 registrations and 1,384 subsequent withdrawals. Summing client derivatives recovered a pooled ridge-logistic fit to numerical precision in six rounds. Equal-module AUC rose from .59629 for FedAvg to .61587 for the pooled-objective solution, .62528 for regularized local adaptation and .63116 for weakly regularized adaptation. A neural half-transfer control reached .64578. These four improvements over FedAvg persisted under every single-module deletion from scoring. The communication result concerns one low-dimensional objective. The predictive results favor testing personalization against strong local and neural controls before advancing a federated warning system.

## Background

OULAD links registration, virtual learning environment activity and final outcomes across repeated presentations. McMahan and colleagues introduced example-weighted averaging of local model updates to reduce communication rounds. Li and colleagues proposed a proximal local objective for heterogeneous networks. Modules offer a setting to examine heterogeneous activity–outcome associations under common institutional data definitions. Our question concerns optimizer behavior and comparative discrimination under this partition. [Kuzilek et al., 2017](https://doi.org/10.1038/sdata.2017.171) · [McMahan et al., 2017](https://proceedings.mlr.press/v54/mcmahan17a.html) · [Li et al., 2020](https://proceedings.mlsys.org/paper_files/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html)

## Population and methods

We predicted released final Withdrawn status among registrations eligible for support at day 60. Presentations 2013B, 2013J and 2014B contributed 16,063 eligible training registrations, including 2,034 withdrawals. Preparation excluded earlier records of learners registered by the landmark in 2014J. That previously inspected presentation included 8,505 distinct eligible learners. Counts of clicks, active days and resources, and recency, were transformed with log(1+x)/4. Each module supplied one simulated client. Macro AUC weights modules equally and measures within-module ordering of a withdrawing and a continuing registration. It gives a small course the same influence as a large course. [Cohort counts](run/counts.csv) · [Design](design.md)

FedAvg used 40 full-participation rounds of five full-batch steps at learning rate .25. FedProx used proximal coefficient .1. At the last broadcast the adapted model took one local Newton step with slope penalty .02 and intercept penalty .005. Matched alternatives shifted the intercept alone or used weak ridge of .00001. Each used the same global history. Other controls included pooled and independent gradient fits, pooled boosting, schedule-conditioned adaptation and a half-transfer MLP. [Local fits](train.py) · [Schedule comparison](schedule/README.md) · [Neural controls](shadow/README.md)

For the shared ridge objective, the example-weighted logistic loss is additive over client rows. At a common iterate, summing the unnormalized score vectors and symmetric Hessians, dividing by the total registration count and adding the common ridge derivatives gives the centralized gradient and curvature. The pooled and distributed Newton systems therefore yield the same update in exact arithmetic under common initialization and full participation. The slope penalty was .001 and the intercept was free. Each client sent five gradient and fifteen Hessian entries each round. This argument requires recomputation at each iterate. The curvature payload scales quadratically with parameter dimension. [Newton protocol](sufficient_stats/protocol.md)

## Results

The distributed and pooled Newton fits differed by at most 2.50 × 10⁻¹⁶ in development probabilities. Six rounds, including the convergence check, cost 1,248 numerical payload bytes per client (8,736 total), including sample count and final broadcast. The five-parameter FedAvg exchange required 3,240 bytes per client (40 uploads and 41 downloads), so the observed reduction was 61.5%. These are logical byte counts in a simulation. [Execution and scoring](sufficient_stats/README.md)

Regularized local adaptation gained .02899 AUC over FedAvg (simultaneous 95% interval .01744 to .04053), .00525 over independent local fits (−.00136 to .01186), and lost .00588 against weak ridge (−.03654 to .02477). The intervals pair forecasts, cluster by learner across registrations and correct seven comparisons by Bonferroni. Intercept adjustment preserved the FedAvg ranking. Distributed Newton lost .01529 against weak ridge (simultaneous interval −.05379 to .02320). Schedule conditioning gained .00150 over matched adaptation (.00045 to .00255), below the exploratory .02 practical margin. Neither candidate cleared the requirement for a .02 gain and positive simultaneous lower bound against every comparator. [Adaptation contrasts](run/summary.json) · [Newton contrasts](sufficient_stats/run/summary.json) · [Schedule contrasts](schedule/run/summary.json)

### Sensitivity to the seven observed clients

We independently rescored frozen probabilities using tie-aware ROC AUC. For each deletion we averaged the six retained module scores without refitting. Columns AAA through GGG in the accompanying table identify the omitted module. The neural half-transfer control led all twelve listed fits after every deletion (.63009–.65623). Weak ridge exceeded regularized adaptation after every deletion, although excluding GGG narrowed the difference to .00036. Newton exceeded FedAvg in all seven analyses but remained below weak ridge throughout. Schedule conditioning exceeded weak ridge only upon removing AAA (.64585 versus .64580). These descriptive perturbations assess dependence on the composition of the scoring cohort. Predicting a previously unseen training client would require a different experiment. [Complete deletion estimates](client_sensitivity/macro_auc.csv)

## Discussion and evidence gaps

Faster optimization can recover a specified pooled objective while leaving substantial variation in module-specific ranking. A pooled likelihood weights registrations whereas the evaluation weights modules equally. The weak-ridge and neural controls show how limiting comparison to FedAvg and FedProx would change the scientific conclusion. Numerical parity establishes neither predictive equivalence across methods nor utility at a fixed advising capacity.

The archive represents one institution, prior label availability dates are unknown, and development outcomes informed successive experiments. Seven course deletions provide no sampling distribution over institutions. No fresh cohort was consumed. A predictive-method submission still needs prospective temporal or external validation, tuned published personalized comparators, calibration at actionable thresholds and evidence of benefit to learners. A systems submission needs measured network and computation costs, larger model dimensions, partial participation and a specified privacy threat model. Aggregating derivatives alone provides no formal confidentiality guarantee. The contribution here is a reproducible comparative case study.

## Reproducibility and data availability

The parent study documents the public source, eligibility implementation, original fitting dependencies and verification commands. The sensitivity extractor uses Python, pandas and scikit-learn. From this directory run the command below to regenerate all full-cohort and deletion scores from the two joined prediction archives. The analysis accesses only archived development predictions. [Source and parent reproduction](README.md) · [Sensitivity code](client_sensitivity/extract.py)

```sh
taskset -c 12-23 python client_sensitivity/extract.py
```
