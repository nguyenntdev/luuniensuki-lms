# Published day-84 withdrawal queue on OULAD

Sánchez Trujillo et al.'s Table 7 top-10% queue reproduced exactly. The assessment logistic regression selected 291 eventual withdrawals and 566 other enrollments in 857 review slots. It missed 843 of the 1,134 eligible withdrawals, for 33.96% precision and 25.66% recall. Uniform review of 857 of the same 8,566 enrollments would capture 113.45 in expectation. The unit is an enrollment, and the endpoint is the final administrative status `Withdrawn`. Of the eligible positives, 87 have no dated exit. [Paper, Table 7](https://doi.org/10.3390/data11110281) · [Exact counts and full precision](result.json)

All eight prediction exports match the independent 2014J risk set exactly by module, presentation and learner. Labels and disjoint flags also match, including 7,329 enrollments and 882 positives belonging to learners absent from all earlier presentations. Table 7 uses the full temporal test, including returning learners. All seven source CSV hashes match the authors' manifest and the pinned UCI download.

## Equal-capacity replay

All rows use 857 pooled slots and the same 8,566 cases. The paper reports the workload for assessment logistic regression. Queue counts for the other models come from applying the same policy to their archived probabilities. No score ties cross the cutoff. Assessment logistic regression captures the most withdrawals and has the highest average precision. Assessment random forest has the highest AUC by 0.00017 over logistic regression, and captures three fewer withdrawals at this budget. The strongest score-free queue uses VLE and captures 261 withdrawals. These differences describe the archived holdout. The models were already fit by the source authors.

| Features | Model | Withdrawals captured | Precision | Recall | ROC AUC | Average precision |
|---|---|---:|---:|---:|---:|---:|
| Assessment | Logistic regression | 291 | 33.96% | 25.66% | .71025 | .28611 |
| Assessment | Random forest | 288 | 33.61% | 25.40% | .71041 | .28077 |
| Assessment | XGBoost | 280 | 32.67% | 24.69% | .70345 | .27078 |
| Score-free | Logistic regression | 246 | 28.70% | 21.69% | .68222 | .24954 |
| Score-free | Random forest | 245 | 28.59% | 21.60% | .69651 | .25477 |
| Score-free | XGBoost | 253 | 29.52% | 22.31% | .67462 | .25424 |
| Assessment + VLE | Logistic regression | 288 | 33.61% | 25.40% | .70534 | .27779 |
| Score-free + VLE | Logistic regression | 261 | 30.46% | 23.02% | .68355 | .24829 |

## Score availability with delayed status

The archived prediction files score only the day-84 risk set. A hypothetical seven-day status delay admits 39 additional enrollments, and a 30-day delay admits 320. All of the additional enrollments have a dated exit and final status `Withdrawn`. Rankings over a stale roster are unidentified because these enrollments have no archived probabilities. OULAD also lacks grade release timestamps, so real-time availability of the features using grades cannot be verified.

| Withdrawal status | Admitted | With all eight scores | Prior exits without scores |
|---|---:|---:|---:|
| Current | 8,566 | 8,566 | 0 |
| 1 day stale | 8,570 | 8,566 | 4 |
| 7 days stale | 8,605 | 8,566 | 39 |
| 14 days stale | 8,694 | 8,566 | 128 |
| 30 days stale | 8,886 | 8,566 | 320 |
| Unfiltered | 11,250 | 8,566 | 2,684 |

The [day-60 status-lag study](../status_lag/README.md) uses a different decision time, eligible roster and module-specific budgets. Its precision does not estimate improvement relative to this day-84 replay.

## Sources and reproduction

The publisher's direct ZIP returned HTTP 200 on 2026-11-21 UTC (59,102,095 bytes). The article landing page, the journal-path `/s1` endpoint and the DOI-path `/s1` endpoint linked in the PDF returned HTTP 403 from this environment. The publisher's direct PDF also returned HTTP 200 (1,590,736 bytes, SHA-256 `68e1270354642d03b1f2d49299ffc737721aef70997f8570d2f7eeb62b07cbf6`). [Supplement ZIP](https://mdpi-res.com/d_attachment/data/data-11-00281/article_deploy/data-11-00281-s001.zip) · [Publisher PDF](https://mdpi-res.com/d_attachment/data/data-11-00281/article_deploy/data-11-00281.pdf) · [PDF's supplement endpoint](https://www.mdpi.com/article/10.3390/data11110281/s1)

The pinned ZIP and PDF are under ignored `private_data/raw/oulad/2013-2014/published_capacity/`. The replay checks both archive hashes before reading predictions and independently reconstructs the roster from the UCI ZIP. It prints aggregate results only. A second calculation using pandas top-k selection and scikit-learn metrics agreed on all eight confusion matrices, ROC AUCs and average precision scores. [Frozen protocol](protocol.md) · [Replayer](replay.py) · [UCI OULAD](https://doi.org/10.24432/C5KK69)

Run from the repository root with Python 3.11 or later.

```sh
set -eu
d=research_v4_2/external/landmark/published_capacity
a=private_data/raw/oulad/2013-2014
(cd "$d" && sha256sum -c protocol.sha256)
taskset -c 0-9 python "$d/replay.py" "$a/published_capacity/data-11-00281-s001.zip" "$a/oulad.zip" |
  diff -u "$d/result.json" -
taskset -c 0-9 python -m pytest tests/research_v4_2 -q
```
