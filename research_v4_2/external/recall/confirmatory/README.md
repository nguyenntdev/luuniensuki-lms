# Does learner history improve recall prediction beyond a matched CatBoost model?

The forecast target is the proportion of correct responses to one lexeme in one recorded Duolingo lesson or practice. At prediction time the learner, item, language pair, practice timestamp, elapsed time since prior practice of the item, and its prior counts are known. Several lexemes can belong to one learner timestamp. Their current responses enter the learner history together after that practice. This design requires a platform capable of supplying these fields at prediction time. [Dataset and terms](https://doi.org/10.7910/DVN/N8XJME) · [Data dictionary and reference models](https://github.com/duolingo/halflife-regression/tree/0041df0dcd436bf1b4aa7a17a020d9c670db70d8)

## Models and information

The proposed ensemble combines four forecasts. Development learners select each component's settings and then supply the paired predictions used to fit nonnegative weights summing to one. Each component also competes individually with the ensemble. Raw and sigmoid-recalibrated probabilities compete for every model, with separate calibration learners fitting the intercept and nonnegative slope. Every reported score averages item-session log losses within each learner, then averages across learners.

| Comparator | Implementation and fitting choices |
|---|---|
| Constant | Learner-weighted training mean. Recalibration can change its level. |
| Authors' HLR | Upstream model with bias, square-root correct and incorrect practice counts, and lexeme. One seed-42 shuffled pass. Four learning rates from 0.0003 to 0.01, with the half-life loss enabled. |
| Authors' HLR ablation | Same reference implementation and learning-rate grid, omitting the auxiliary half-life loss. |
| Authors' logistic | Upstream logistic with elapsed days and HLR's feature vector, same four learning rates. |
| Log-feature logistic | Fractional binomial log likelihood with learner weighting, intercept, standardized log delay and counts, and one-hot lexeme. Two ridge penalties (1, 10) on the summed weighted loss. |
| Original-feature CatBoost | Fractional cross entropy on elapsed days, counts and lexeme. Depth and iterations (4, 400) or (6, 650), each with uniform row or equal learner weighting. |
| History logistic | Same logistic likelihood and penalties, full numeric and categorical predictors listed below. |
| History HLR | Fits exponential forgetting directly to the observed fractional outcomes with learner-weighted likelihood and ridge. Log half-life is linear in the enriched design, including log elapsed time. This permits the effective half-life to vary with delay. A one-second floor handles zero delays. |
| Histogram gradient boosting | Learner-weighted binomial loss; split fractional targets into success and failure rows with the corresponding weights. 31 leaves, 200 or 500 iterations. The four categorical features retain the 250 most frequent values each, pooling the rest. |
| Matched CatBoost | The same full feature set and the exact same fitted component used in the ensemble. Depth and iterations (4, 400), (6, 650) or (8, 800), each with uniform row or equal learner weighting. |

The four enriched models receive log elapsed days, log correct and incorrect practice counts, smoothed historical item accuracy, log time since the last recorded lesson, smoothed learner and learner-item accuracy from earlier timestamps, last learner and learner-item accuracy, log earlier exposure counts, exponentially weighted learner accuracy (weight 0.3 for the latest session), sine and cosine of UTC hour, and a training-only lexeme difficulty estimate. The categorical predictors are course, lexeme, surface/lemma string before the first tag, and first grammatical tag. Smoothed online accuracies start with 4.5 successes in five exposures. The item difficulty lookup adds 20 training-mean pseudo-observations and excludes the training row's entire learner fold, using five folds. All learners outside training use the lookup estimated from the training cohort alone. A learner's first observed practice can already have item counts from before the released trace begins.

### How much history does the trace expose?

The training cohort contained 257,203 item encounters from 2,307 learners. At the first observed encounter for each of 118,004 learner–item pairs, the release already reported at least one earlier exposure. For 139,199 transitions between consecutive recorded encounters with the same item, the next cumulative exposure count equalled the earlier count plus the earlier session size in 136,951 cases. The earlier observed timestamp and the reported elapsed interval agreed to the second in 122,980 cases. Counts, successes and elapsed seconds all reconciled in 121,755 transitions (87.5%). These comparisons use the same language-qualified lexeme string as the forecaster. They establish partial observability of earlier practice and quantify how frequently the two available clocks agree. Unseen practice, string-based grouping and differences in timestamp semantics remain possible explanations for discrepancies. [Training-only audit](history_audit.py) · [Counts and input digest](run/history_audit.json)

## Reproduction

From the repository root, use Python 3.12 and the pinned external-study requirements. Fetch the archive and reference script using the commands in the parent manuscript. Both inputs are checked by SHA-256. The released trace is licensed CC BY-NC 4.0. The upstream HLR code is MIT-licensed. Keep raw data and fitted objects local. [Parent reproduction instructions](../manuscript.md) · [Environment pins](../../requirements.txt)

```bash
study=research_v4_2/external/recall/confirmatory
out=$(mktemp -d)
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=3 PYTHONDONTWRITEBYTECODE=1
python "$study/study.py" train "$out"
python "$study/reference_controls.py" train "$out"
python "$study/study.py" score "$out"
python "$study/reference_controls.py" score "$out"
python "$study/audit.py" "$out"
node "$study/audit-source.mjs" private_data/raw/duolingo-hlr/traces.csv.gz "$out" --reference
```

Training serializes the exact fit locally and seals hashes of the evaluator, protocol, inputs and fitted models before scoring is possible. Each stage refuses to overwrite its existing final record. The freeze is a local reproducibility record without independent timestamping. The audit checks same-time outcome exclusion on a deliberately shuffled synthetic trace and independently recomputes the paired margin tests from the saved learner losses. The loss table identifies learners by a within-bucket ordinal. It is sufficient to reproduce all reported contrasts without redistributing raw practice records. [Protocol](protocol.md) · [Training and scoring code](study.py) · [Audit](audit.py)

## Published comparators and remaining scope

A supplemental comparison adds six controls before opening the test cohort. These cover the original ACL paper’s Leitner and Pimsleur rules, its no-lexeme regressions, and a smoothed proportion of past correct responses. The single ensemble faces sixteen controls in the expanded family. Both the original and expanded family decisions are retained. [Supplemental protocol](reference_protocol.md) · [Implementation](reference_controls.py) · [Settles and Meeder, Table 2](https://aclanthology.org/P16-1174/)

Two later comparisons require further evidence. Zaidi and colleagues used English-target words in the same Duolingo release and supplied their neural HLR with external word difficulty, concreteness and frequency measures. The matched history HLR in this study uses different inputs. Sun and colleagues' KDD SPsyINN repository provides code for symbolic and neural memory models. Its loader expects preconstructed sequence tensors and its published scores do not use this cohort or endpoint. No measured gain against either neural method can be inferred here. [Zaidi et al., AIED 2020](https://doi.org/10.1007/978-3-030-52240-7_65) · [Sun et al., KDD 2025](https://doi.org/10.1145/3711896.3736886) · [Released SPsyINN loader](https://github.com/JiaqiDijon/SPsyINN/blob/23778bf83bc4773b4d0923a05864a627b1017fdb/model/data_loader.py)

## Scope of inference

Forecasts concern new learners in the same historical release and observed schedule. Training and test learners can practice during overlapping calendar periods. This evaluates transfer across learners within a snapshot. Learner-level uncertainty conditions on one fitted ensemble and omits retraining, platform drift, dependence between learners, and uncertainty from the historical scheduling policy. A difference in predictive loss does not establish how changing a review schedule would affect retention.

### Resuming long CPU fits

An initial CPU process ended during the development grid before writing the model freeze. The retry uses the same training and prediction functions and stores completed fitted trials in the private cache. Calibration, development selection and ensemble fitting still run in the original order. The cache key covers the evaluator, protocol, reference implementation, trace archive, Python and library versions, model family and configuration. Use the following command in place of the original training command when resuming. [Cache wrapper](resume_train.py)

```bash
python "$study/resume_train.py" "$out" private_data/raw/duolingo-hlr/fit-cache
```

After both scoring stages, render the sixteen-comparator table with the command below. It checks the learner keys, intervals and Holm tests directly from the two loss files. The source audit recomputes the constant forecast and the three fixed-rule controls from the public trace in JavaScript.

```bash
python "$study/report.py" "$out"
```
