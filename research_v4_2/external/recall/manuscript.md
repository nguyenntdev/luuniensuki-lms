# How much does boosting improve on calibrated half-life regression for learner recall?

**Abstract.** We compared the authors' implementation of half-life regression (HLR) with CatBoost on publicly released Duolingo learning traces. Both models saw the same pre-session information and had equal opportunities to tune and recalibrate. Across 42,144 test sessions from 360 learners, mean learner-level negative log likelihood was 0.33484 for HLR and 0.33096 for CatBoost. The gain of 0.00389 nats was distinguishable from zero (95% interval 0.00198–0.00593). Its point estimate missed the prespecified practical margin of 0.005. On 4,611 additional learners from the same release, the frozen-model gain was 0.00519 (0.00446–0.00595). Raw HLR produced extreme predictions even for groups with similar observed recall. In a third cohort of 4,523 learners, boosting gained 0.00255 (0.00192–0.00321) over learner-weighted logistic regression with log-transformed history features. The practical advantage depended on the comparator.

## Problem and comparator

A recall forecast is a probability that a learner will retrieve an item after a particular delay. Errors in that probability can matter even when two models rank items similarly. Settles and Meeder parameterized half-life with a learned function of item and practice history. We used their released training and prediction code at revision `0041df0`, including the half-life training term, item features and bias. Our comparison changes the evaluation split and objective from the original article. [HLR paper](https://aclanthology.org/P16-1174/) · [Author implementation](https://github.com/duolingo/halflife-regression/tree/0041df0dcd436bf1b4aa7a17a020d9c670db70d8)

## Design

We selected learners by a deterministic 2% hash sample and kept their traces together. Separate learner partitions supplied 148,978 training sessions, 29,726 calibration sessions, 38,220 development sessions and 42,144 test sessions. Inputs were elapsed time, previous correct and incorrect practice counts, and lexeme with learning language. The target was the fraction correct in the current session. We retained the released archive locally under its noncommercial research license. [Duolingo data](https://doi.org/10.7910/DVN/N8XJME)

Each family had four training configurations. Each fitted configuration could use raw probabilities or learn an intercept and slope on held-out calibration learners. Development loss selected one configuration per family. We weighted each learner equally after averaging over their sessions. This measures performance for a sampled learner rather than allowing a few frequent users to dominate the comparison. [CatBoost paper](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html)

## Findings

Development selected the original HLR learning rate of 0.001 and a depth-four, 400-iteration boosting model. Both selected recalibration. The HLR calibration slope was 0.0071 on the log-odds scale, compared with 0.841 for boosting. In this implementation and sample the calibrator compressed most of the HLR score variation. This finding limits what the loss contrast can establish about the underlying forgetting curve.

We resampled paired learner losses 10,000 times. A paired sign-flip test returned approximately 0.00010. The interval includes gains both below and above 0.005, and the prespecified decision required the observed gain to reach that value. The practical-improvement criterion was unmet. The comparison is confined to recorded sessions and a single historical snapshot. It does not identify a better review schedule or measure retention under an intervention.

[Protocol](protocol.json) · [Evaluator](evaluate.py) · [Model settings and results](run/result.json) · [Predictions](run/predictions.csv.gz)

## Fixed-model validation on additional learners

After seeing the primary result, we recorded a follow-up design for four previously unused learner hash buckets. We retrained the two selected models using the original training data, seed and row order and applied the archived calibration coefficients. Before scoring the new cohort, we checked all 42,144 original test rows against the archived predictions. The maximum absolute difference was zero for HLR and 1.12 × 10⁻¹⁶ or less for CatBoost. A learner-ID intersection check returned zero across the new cohort and the union of the four original partitions. This is validation on additional learners from the same historical data release. [Follow-up protocol](validation_protocol.json) · [Aggregate results](run/validation.json)

On 517,541 sessions from 4,611 additional learners, calibrated HLR scored 0.34085 nats and calibrated CatBoost scored 0.33566. The paired gain was **0.00519 nats** (95% learner-bootstrap interval 0.00446–0.00595). The four constituent buckets gave gains of 0.00521, 0.00495, 0.00481 and 0.00581. The follow-up point estimate exceeds 0.005, while its interval spans that margin. The original decision remains the primary one. Both bootstrap intervals condition on the fitted models and omit uncertainty from training on different learners.

### Why the HLR slope was so small

On the follow-up cohort, the selected raw HLR reached the author's lower probability bound of 0.0001 in 20.63% of sessions. Its half-life reached the 15-minute lower bound in 0.67%. The following session-weighted means show what recalibration had to correct. The model assigned very different probabilities to groups with relatively similar observed recall.

| Raw HLR score | Sessions | Mean raw probability | Mean calibrated probability | Mean observed recall |
|---|---:|---:|---:|---:|
| ≤ 0.01 | 157,683 | 0.00095 | 0.88466 | 0.88418 |
| > 0.01 to 0.25 | 81,183 | 0.09033 | 0.88872 | 0.89373 |
| > 0.25 to 0.50 | 39,754 | 0.36832 | 0.89019 | 0.89701 |
| > 0.50 to 0.75 | 18,383 | 0.62245 | 0.89093 | 0.90131 |
| > 0.75 to 0.99 | 91,707 | 0.94382 | 0.89282 | 0.90792 |
| > 0.99 | 128,831 | 0.99543 | 0.89434 | 0.91267 |

Under equal learner weighting, raw HLR had loss 3.76478 and recalibration reduced it to 0.34085. Predicting 0.88906 for every session, the mean learner recall from calibration, gave loss 0.34119. Thus calibrated HLR improved on the constant by only 0.00033 nats. Raw CatBoost scored 0.33562. Score-band means weight sessions equally and can differ from an equal-learner calibration assessment.

Changing only the HLR training shuffle produced calibration slopes of 0.00709, 0.00420 and 0.00449 for seeds 42, 43 and 44. Removing the auxiliary half-life loss using the authors' switch and comparing one or three training passes also produced small slopes (0.00570 and 0.00560). Development selected one pass with calibration. The resulting follow-up loss was 0.34087. The paired loss difference between original and ablated HLR was −0.000019 (95% interval −0.000045 to 0.000008). These probes show that the compression persisted across these choices. They do not isolate its cause or establish its prevalence under different training populations or scheduling systems.

## Sensitivity to the choice of comparator

After the first validation, we reserved buckets 6–9 for a second comparison and recorded a separate protocol before scoring them. The authors' logistic model uses square-root counts, elapsed days, a bias and a lexeme feature. It had the same four learning rates and raw/calibrated choices as primary HLR. A second logistic model used log(1+x) for delay and each count, one-hot lexemes, an intercept, L2 regularization (C = 1) and equal total training weight per learner. Weighted positive and negative copies of each session represented its fractional recall exactly. Original development learners selected recalibration for both logistic models. The new cohort comprised 500,316 sessions from 4,523 learners. Its hash buckets exclude every learner eligible for either preceding comparison. [Comparator protocol](comparator_protocol.json) · [Comparator results](run/logistic.json)

| Model | Mean learner NLL | Model NLL minus CatBoost NLL (paired 95% interval) |
|---|---:|---:|
| Authors' logistic regression, learning rate 0.003 | 0.33853 | 0.00580 (0.00501–0.00659) |
| Learner-weighted logistic regression with log features | 0.33528 | 0.00255 (0.00192–0.00321) |
| Frozen CatBoost | 0.33273 | Reference |

On these same learners, the stronger logistic comparator cut the estimated advantage of boosting by more than half relative to the authors' logistic model. Its entire descriptive interval fell below 0.005. The logistic fits differ in optimization, feature scale, regularization and learner weighting, so this comparison cannot attribute the difference to any one choice. The intervals use 10,000 paired learner resamples without adjustment for the secondary comparisons.

## Prospectively reserved learner-history challenge

Can a learner-history ensemble add practical predictive value beyond a tuned boosting model given those same histories? A fourth design reserves disjoint learner-ID buckets for training (10–11), calibration (12), model selection (13) and testing (14–17). Each learner contributes equal total weight. Past performance enters the features only after all rows at a practice timestamp have been predicted. A boosting component sees the complete history feature set and is compared with the ensemble using the identical fitted model. The expanded comparison also includes the ACL reference variants, Leitner, Pimsleur and a smoothed count predictor. Every control must clear the common 0.005-nat margin under multiplicity-adjusted paired learner tests. The software seals the trained fits and development choices before opening the test cohort. [Protocol](confirmatory/protocol.md) · [Additional control registration](confirmatory/reference_protocol.md) · [Data, competitors and reproduction](confirmatory/README.md)

The training traces covered 2,307 learners. For every one of their 118,004 learner–item pairs the first observed encounter already had prior exposure. Of 139,199 observed transitions for the same learner and lexeme, 121,755 reconciled on elapsed seconds, prior exposures and prior correct responses simultaneously. This limits what the history features can recover about earlier practice. [Training-only source audit](confirmatory/run/history_audit.json)

## Interpretation and scope

Across the three disjoint evaluation cohorts, model choice affected the size of the measured gain. The primary comparison missed its specified margin. The follow-up supports a small predictive advantage over the chosen HLR implementation, and the stronger logistic comparison shows how little of that advantage may require boosting. Only one historical Duolingo snapshot and one source of review schedules contributed data. Recorded practice times and learner choices govern which sessions have observable outcomes. Neither performance on a new schedule or platform nor an effect on learning from changing review times is identified here. A session with one prompt and one with several prompts each contribute one session loss within their learner. Different weighting or an intervention would answer a different question.

## Reproduction and data use

Use Python 3.12 and run the following from the repository root in a virtual environment. The archive (Harvard Dataverse file 3091087) is licensed CC BY-NC 4.0 by Burr Settles. Obtain it from the source for noncommercial use, and retain attribution and the license when reusing derived material. The upstream implementation carries the MIT license. Follow-up outputs contain only aggregate diagnostics. [Data and terms](https://doi.org/10.7910/DVN/N8XJME) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · [Upstream code](https://github.com/duolingo/halflife-regression/tree/0041df0dcd436bf1b4aa7a17a020d9c670db70d8)

```bash
python -m pip install -r research_v4_2/external/requirements.txt
study=research_v4_2/external/recall
cache=private_data/raw/duolingo-hlr
mkdir -p "$cache"
curl -fL --retry 3 https://dataverse.harvard.edu/api/access/datafile/3091087 -o "$cache/traces.csv.gz"
curl -fL --retry 3 https://raw.githubusercontent.com/duolingo/halflife-regression/0041df0dcd436bf1b4aa7a17a020d9c670db70d8/experiment.py -o "$cache/experiment.py"
out=$(mktemp -d "$cache/reproduction.XXXXXX")
export OPENBLAS_NUM_THREADS=1
python "$study/evaluate.py" "$cache/traces.csv.gz" "$cache/experiment.py" "$out/primary"
python "$study/validate.py" "$cache/traces.csv.gz" "$cache/experiment.py" "$out/validation.json"
python "$study/compare_logistic.py" "$cache/traces.csv.gz" "$cache/experiment.py" "$out/logistic.json"
```

A full rerun on Python 3.12.3 reproduced the primary result JSON and compressed predictions byte for byte. Each evaluator verifies the archive and upstream code checksums. The follow-up checks the primary predictions in the study directory before evaluating new learners. Compare the rerun files with the corresponding reports in the study's run directory. Exact floating-point values can depend on the numerical libraries. [Primary evaluator](evaluate.py) · [Fixed-model validation](validate.py) · [Logistic comparison](compare_logistic.py)

On 526,770 item encounters from 4,596 reserved learners, the ensemble achieved mean learner log loss .325446. Its paired gain over the upstream HLR was .009898 nats. The gain over its history-matched CatBoost component was .000028 nats, with simultaneous 95% interval [−.000023, .000080]. Twelve of sixteen controls cleared the registered .005-nat margin under Holm adjustment. Independent source scoring verified membership and the reference equations. This result supports the value of the history-rich predictor relative to HLR and quantifies the very small incremental gain from mixing its four components. All learners come from the same historical release. [Complete comparison](confirmatory/RESULTS.md) · [Frozen development choices](confirmatory/run/freeze.json)

A subsequent development study tested whether discrepancies in cumulative practice counters explain a material part of the remaining error. On 1,133 learners, the matched gain was .000414 nats, below the .005 threshold. Only 208 of 122,592 encounters had admissible excess practice counts, and these contributed a small negative difference. [Counter reconciliation and source replay](counters/README.md)
