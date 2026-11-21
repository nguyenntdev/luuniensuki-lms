# Cross-course dropout prediction with a small feature set: outcome sensitivity and a later-cohort test

**Abstract.** Does an additive model transfer between degree courses as well as two published boosting methods? We tested this question on 3,630 students with resolved graduation or dropout outcomes in the UCI Portuguese higher-education dataset. Each of 17 courses served once as an unseen test course. Mean course negative log likelihood was 0.453 for CatBoost, 0.487 for additive logistic splines and 0.500 for XGBoost. A prespecified requirement to outperform both tree ensembles was unmet. Including 794 still-enrolled students in three-status fits preserved CatBoost’s lead, but one course showed 42.9 percentage points of mean dropout overprediction. On a later UK cohort of 10,228 module registrations, locally refit splines had the lowest loss (.561 versus .568 for CatBoost and .575 for XGBoost). The target, features and decision date differed between institutions.

## Data and motivation

Courses differ in enrollment, assessment and completion patterns. A random student split can place examples of the destination course in training, even when the intended deployment concerns a new course. We held out entire courses and weighted the loss of each course equally. The dataset contains 4,424 records. We excluded the 794 cases labeled “Enrolled,” so the target is dropout conditional on a resolved recorded outcome. The secondary analysis below retains all three released statuses. [Dataset and attribution](https://doi.org/10.24432/C5MC89)

## Methods

Every model received admission grade, previous qualification grade, application order, and first-semester counts or grades for enrolled units, approved units and evaluations as specified in the protocol. Two shared ratios described approvals and evaluations per enrolled unit. We excluded second-semester features. The candidate used cubic splines and a regularized additive logit. The baselines used the published CatBoost and XGBoost implementations. [CatBoost](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html) · [XGBoost](https://www.kdd.org/kdd2016/papers/files/rfp0697-chenAemb.pdf)

Within each outer training partition, three group folds selected among four configurations per model using mean course loss. No student from the held-out course contributed to tuning its model. This was a retrospective comparison on a dataset that had already been explored. We fixed the comparison before running the nested evaluator. We compared paired course losses using a course bootstrap and sign-flip tests, with Holm adjustment for the two planned comparisons.

## Results and interpretation

Against CatBoost, the spline's gain in nats was −0.0339 (95% interval −0.0807 to −0.0063, adjusted p=0.0161). Against XGBoost it was +0.0131 (−0.0155 to +0.0557, adjusted p=0.676). Positive values favor splines. Reporting only the second comparison would give a misleading account of the candidate's performance. The empirical advantage of CatBoost concerns the evaluated settings and feature set.

The unit of generalization is one of 17 courses at one institution. Course sizes are uneven, leaving the equal-course mean sensitive to small programs. Flexible tree interactions offer one possible explanation for CatBoost's result, but the experiment did not isolate that mechanism. Negative log likelihood measures probability quality and does not measure student benefit or staff workload.

[Protocol](protocol.json) · [Evaluator](evaluate.py) · [Development trials](run/dev_trials.json) · [Results](run/result.json) · [Predictions](run/predictions.csv)

## What changes when the 794 enrolled students are included?

The Portuguese source records status at the end of the normal duration of the course. Among 4,424 students, 1,421 had dropped out, 794 were still enrolled and 2,209 had graduated. We refit the three model families to predict all three statuses, keeping the same held-out courses and the settings already chosen on each training partition. This asks how the primary comparison behaves when all released labels enter training. The primary tuning criterion still favors performance on resolved outcomes. [Original dataset study](https://doi.org/10.1007/978-3-030-72657-7_16)

The table gives mean course negative log likelihood in nats. Lower values are better within a row. Each row below the first uses probabilities from the same multinomial fits. For the last row, we divide predicted dropout probability by the sum of dropout and graduation probabilities before scoring the resolved students. The reference uses the training courses' class frequencies.

| Status scored | Students | CatBoost | Spline | XGBoost | Frequency reference |
|---|---:|---:|---:|---:|---:|
| Dropout among resolved students, original binary fit | 3,630 | .453 | .487 | .500 | .717 |
| All three statuses | 4,424 | .838 | .866 | .861 | 1.067 |
| Recorded dropout versus enrolled or graduated | 4,424 | .501 | .543 | .524 | .675 |
| Enrolled or dropped out versus graduated | 4,424 | .519 | .537 | .539 | .701 |
| Dropout conditional on resolution, multinomial fit | 3,630 | .465 | .491 | .485 | .717 |

CatBoost had the lowest mean loss on every Portuguese target. The other two families changed order even with fixed predictions. XGBoost scored better for recorded dropout and splines scored slightly better for absence of graduation. The 794 enrollment labels support both comparisons at the recorded horizon. Their eventual outcomes remain unknown. The release supplies neither entry dates for a prospective cohort split nor individual exit dates for identifying students still eligible for support after semester one. First-semester performance may already reflect withdrawal for some students. Source row order supplies no chronology.

## A course with no training examples at zero registered units

In Animation and Multimedia Design (course 171), 180 of 215 students had zero first-semester enrolled units. Across the other 16 courses, zero of 4,209 students had that value. Among the 180, 77 dropped out, 28 remained enrolled and 75 graduated. The same recorded zero therefore occurred across all outcomes in a course the models could encounter only at test time. The archive gives no reason for this coding pattern. [Counts by course, units and target](run/portugal_unit_support.csv)

For this course CatBoost assigned a mean dropout probability of .810 against an observed .381 on all 215 students. The mean prediction was .870 against .461 on the 178 resolved students in the primary test. The all-student CatBoost dropout gap averaged 8.8 percentage points in absolute value across the 17 courses, masking the 42.9-point overprediction here. These differences measure calibration of the course mean. Individual risk calibration within each course is a separate question.

Keeping the primary predictions fixed and omitting course 171 **only from the descriptive average** gives losses of .371 for CatBoost, .378 for XGBoost and .383 for splines across 16 courses. That one course reverses the arithmetic ordering of XGBoost and splines in the primary average. The original decision still uses all 17 courses. [All course losses, observed rates and predictions](run/course_scores.csv)

## A later cohort at the Open University

We also asked whether the same three families kept their order on another institution's withdrawal label. The Open University Learning Analytics Dataset provides module-presentation start periods and registration and withdrawal dates. We fit models locally using registration lead time, studied credits and previous attempts as registration-time features. Eligible registrations had started by day zero and had no exit recorded by the end of that day. The outcome was final withdrawal from the module. The model used the exit date only to establish day-zero eligibility. We excluded module, learner and presentation identifiers from its features. The archive supplies one registration-level credit total, so we cannot independently verify when that field was last updated. [Kuzilek, Hlosta and Zdrahal, dataset descriptor](https://doi.org/10.1038/sdata.2017.171) · [UCI archive](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset)

We used the February and October 2013 presentations for development, excluded every learner present in October 2014 from development, and reserved October 2014 for testing. February 2014 was excluded because its modules could still be running at the start of the test presentation. We selected settings on 7,042 October 2013 registrations after fitting on 4,139 February registrations from distinct learners. Both development presentations had ended by the outer test. The refit used 11,299 registrations. October 2014 supplied 10,228 eligible registrations from 9,767 learners across seven modules, including 2,898 withdrawals. One module, CCC, was absent from 2013. [Grid and partition sizes](run/uk_development.json)

| End-of-day-zero prediction | Spline | CatBoost | XGBoost | Training withdrawal rate |
|---|---:|---:|---:|---:|
| Equal-module negative log likelihood | .561 | .568 | .575 | .571 |
| Mean absolute module gap, percentage points | 8.0 | 8.7 | 8.9 | 8.4 |

The spline had the lowest mean loss in this later UK cohort. Its advantage over the frequency reference was .010 nats after rounding, and the frequency reference scored best on the unseen module CCC. These estimates describe families refit locally at a different decision date, with a different feature set and outcome. The contribution of each difference to the ordering remains unknown. Seven modules in one test presentation provide limited evidence about future presentations. Neither archive measures the benefit of acting on a prediction.

## Reproduction and checks

From the repository root, with the portfolio's pinned Python dependencies installed and the two UCI archives at the paths below, run the following. The primary predictions and development settings in this directory are inputs to the secondary checks.

```bash
D=research_v4_2/external/dropout
PT=private_data/raw/uci/dropout-697/source.zip
OU=private_data/raw/oulad/2013-2014/oulad.zip
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$D/robustness.py" "$PT" "$OU" "$D/run"
python "$D/score_robustness.py" "$PT" "$OU" "$D/run"
```

A separate scorer reconstructs eligible rows from both raw releases, rejoins gold labels by source position, checks the UK partition counts, and computes both library log loss and the negative log of the assigned probability. It also checks the frozen primary means to numerical tolerance. The signed course gaps and grouped losses can be inspected without model fitting. [Secondary protocol](sensitivity.md) · [Refit code](robustness.py) · [Portuguese three-status predictions](run/portugal_three_status.csv.gz) · [UK withdrawal predictions](run/uk_later_cohort.csv.gz) · [Independent scoring code](score_robustness.py) · [Summary](run/robustness_summary.csv) · [Source and output hashes](run/robustness_sha256.json)
