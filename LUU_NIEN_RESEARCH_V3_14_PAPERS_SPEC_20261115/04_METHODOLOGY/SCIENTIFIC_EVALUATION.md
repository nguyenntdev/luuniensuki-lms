# Statistical, experimental, benchmark and reporting standards

## 1. Prespecification
Each manuscript must freeze primary endpoint, direction, effect size and smallest meaningful effect, power assumptions where human sampling, comparison family, exclusions, sampling unit and subgroup risks BEFORE final test.

## 2. Splits and leakage
- KT: learner-level and held-out-skill/domain plus temporal holdout; no future concept tags or post-outcome features.
- Recommender/path optimization: hold out whole course/objective/provider graph; compare on same feasible instances, constraints and budget.
- Tutor: hold out dialogues/tasks/documents/LLM prompt examples and rating rubrics; separate blind teacher rating from model tuning.
- OULAD: split by presentation/course and freeze prediction time; never use final outcome or activity after horizon in inputs.
- Multimedia: hold out object/source families and remove near-duplicate media/text/translations.
- Human studies: preregistration, anonymized consent, blinded evaluators; recruitment limitations documented.

## 3. Comparable baselines
C0 sanity, C1 matched classical, C2 published current comparator (if code and license available) and P-specific conventional industrial baseline. Require same input information, compute budget, hyperparameter tuning budget, data splits, and stopping policy. Do not infer SOTA from C1 only.

## 4. Metrics and inference
- Probabilistic: ROC-AUC + PR-AUC, NLL/Brier/ECE and subgroup calibration where applicable; report prevalence.
- Decision: constraints/utility/regret with exact-oracle certification where tractable; matched paired comparisons.
- Human: ICC/weighted κ/α selected based on measurement level, rater design, CI with cluster-aware bootstrap; effect sizes.
- Risks: coverage-selective risk curves, failure rates stratified by missingness/source uncertainty/latency, privacy and device capabilities.
- Confidence intervals cluster on learner, source family, course or annotator as preregistered; multiple testing corrected within declared family (Holm or BH).
- Never pretend 3 identical deterministic hashes are 3 independent stochastic seeds; use learner bootstrap for uncertainty and label limitations.
- Detect missing predictions, duplicate IDs, unexpected extra predictions and mismatched denominator; fail closed.

## 5. Core experimental matrix
| ID | Run | Acceptance proof |
|---|---|---|
| E00 | dataset and license gate | source + terms + checksums + data card approved |
| E01 | schema+split integrity | leak checks, group/time constraints, sealed gold |
| E02 | sanity baseline | nontrivial negative control; no SOTA claim |
| E03 | matched classical | tuned honestly with same budgets |
| E04 | closest published model | original code where possible, or BLOCKED reason |
| E05 | proposed method | config, commit, training logs, model card |
| E06 | mechanism ablations | targeted divergence; no manufactured labels |
| E07 | robustness and shift | preregistered shifts and subgroup cuts |
| E08 | calibration and cost | risk/coverage, latency, compute/carbon where relevant |
| E09 | statistical comparison | paired tests, uncertainty, multiple correction |
| E10 | error analysis | false positives/negatives, independent manual review |
| E11 | secondary replication | different external dataset/collection or explicit single-dataset limitation |
| E12 | manuscript verification | all table cells computed from frozen evidence ledger |

## 6. Decision statuses
`ENGINEERING_PASS` = contracts/tests pass; `BENCHMARK_COMPLETE` = external data + comparator runs and audit; `SCIENTIFIC_REVIEW_READY` = independent contribution, complete tables, valid ethics, no leak; `SUBMISSION_READY` = proofs, license, venue formatting and coauthor checks. No automatic transitions.
