# Who is still at risk? A day-60 audit of withdrawal prediction

**Abstract.** Early-warning systems allocate attention to students who can still receive support. A withdrawal benchmark can instead score students who have already left. We use dated registrations and click logs from the Open University Learning Analytics Dataset (OULAD) to quantify the difference. At day 60, a fixed CatBoost model achieved an AUC of 0.834 across registrations in the latest presentation. Restricting evaluation to students still registered reduced AUC to 0.623. The paired difference was 0.211 (learner-bootstrap 95% interval 0.199–0.222). Logistic regression showed almost the same change. Of all positive–negative pairs at day 60, 63.75% contained a student who had already withdrawn. The model correctly ordered 95.33% of those pairs, counting ties as one half. Changing the target to failure or withdrawal reduced the gap.

## Question and design

A feature recorded by day 60 can satisfy a temporal cutoff and still describe the consequences of an earlier withdrawal. Zero recent clicks are particularly ambiguous. They could signal an active student's impending withdrawal or simply reflect that a former student has stopped participating. Our estimand is discrimination among registrations that can still experience withdrawal after the decision date.

We linked registration, outcome and virtual learning environment tables by module, presentation and learner. We included dated registrations that began by day 60. The risk set additionally required an absent withdrawal date or a date strictly greater than 60. Calendar dates are relative to the module start. The outcome was the released final status “Withdrawn.” We aggregated click count, distinct active days, recency and distinct resources from day 0 through day 60. Registration end dates determined eligibility only. We reserved presentation 2014J for testing and excluded its learners from earlier training presentations. OULAD records daily activity rather than the exact time of a teacher's decision. [Dataset descriptor](https://doi.org/10.1038/sdata.2017.171)

## Experiment and results

We fit fixed logistic and CatBoost models to all training registrations and repeated fitting on the eligible subset. The full and eligible training sets contained 19,500 and 16,063 registrations. The corresponding test sets contained 11,249 and 8,815. We resampled learners jointly across the nested test populations to quantify uncertainty in the primary contrast. [CatBoost, NeurIPS 2018](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html)

| Training population and model | All test registrations | Eligible test registrations |
|---|---:|---:|
| All, logistic | 0.832 | 0.621 |
| All, CatBoost | 0.834 | 0.623 |
| Eligible, logistic | 0.800 | 0.599 |
| Eligible, CatBoost | 0.671 | 0.595 |

Each cell is AUC. The first two rows isolate evaluation membership by holding predictions fixed. The last two ask a different question about training on eligible registrations. Restricting training did not recover the discrimination seen on the broader test population.

## Which comparisons produce the gap?

AUC gives the probability that a randomly chosen positive scores above a randomly chosen negative, counting a tie as half correct. Partition the pairs by eligibility of both members. Pooled AUC is the sum of the stratum AUCs weighted by their shares of all pairs. In this release all registrations removed at day 60 have a positive withdrawal outcome. The negatives therefore stay fixed. The entire pooled-minus-eligible gap is the fraction of pairs involving an exited positive multiplied by the difference between the two stratum AUCs.

Among 28,371,558 day-60 withdrawal pairs, 18,087,054 involved an exited positive and 10,284,504 involved an active positive. CatBoost's stratum AUCs were respectively 0.9533 and 0.6228. Their weighted average reconstructs 0.8335. The resulting 0.2107 gap reflects both the prevalence of a comparison unavailable to a day-60 intervention and the model's ability to win that comparison. The identity holds for any fixed scores. The shares and stratum AUCs are empirical.

## Sensitivity to time and outcome definition

A published OULAD study compared all-registered and landmark cohorts at days 14 and 56, predicting unsuccessful completion (Fail or Withdrawn). Its pooled day-56 AUCs were 0.856 and 0.776. It used richer covariates, different estimators and year/period matching. We adopted its two horizons and composite target in a secondary factorial analysis. For each horizon and target, we retrained the same two models on the earlier presentations, excluding test learners, and then held all predictions fixed during the population comparison. This isolates the paired comparisons within our design. It does not reproduce the other study's numerical estimates. [Prior OULAD comparison, sections 3.6 and 4.3](https://doi.org/10.3390/computers15090560)

| Day | Target | All / eligible registrations | CatBoost AUC, all / eligible | Share of pairs with an exited positive | AUC within those pairs |
|---:|---|---:|---:|---:|---:|
| 14 | Withdrawal | 11,221 / 9,330 | .727 / .587 | 49.7% | .869 |
| 14 | Fail or Withdrawn | 11,221 / 9,330 | .740 / .662 | 32.7% | .899 |
| 56 | Withdrawal | 11,249 / 8,876 | .825 / .620 | 62.1% | .949 |
| 56 | Fail or Withdrawn | 11,249 / 8,876 | .817 / .710 | 41.0% | .971 |
| 60 | Withdrawal | 11,249 / 8,815 | .834 / .623 | 63.8% | .953 |
| 60 | Fail or Withdrawn | 11,249 / 8,815 | .824 / .714 | 42.0% | .976 |

Adding students who ultimately failed to the positive class reduces the weight of already-exited positives. At day 56 this cut the CatBoost gap from .204 to .107 even though the model ranked the exited positives more accurately under the broader target. Logistic regression showed the same direction at every horizon. The sensitivity estimates reuse registrations across horizons and are descriptive. [Factorial evaluator](horizons.py) · [All model cells and pair counts](run/horizons.json)

## Interpretation

For a day-60 early-warning decision, the relevant AUC among eligible students is about .62. A retrospective population can still be a legitimate target for another question, such as classifying the final outcomes of everyone originally registered. The analysis distinguishes these questions and quantifies which pairs change the answer. We did not observe support decisions, subsequent intervention effects or predictive performance at a different institution. Missing registration dates exclude some students from both populations.

[Protocol](protocol.md) · [Evaluator](evaluate.py) · [Results](run/result.json) · [Predictions](run/predictions.csv.gz)

## External course-exit forecasting

A second dataset supplies an action-level target at a different institution and supports a prospective model comparison. Of 41,175 future MOOC actions, 369 carried a recorded exit. A tree–recurrent blend raised AUC from .679 for a current-action tree to .809. The gain over the full recurrent model was .0040 (simultaneous 95% interval −.0023 to .0117), below the prespecified .01. The blend also had lower average precision than the recurrent model. The aligned comparison did not pass its first stage. [Protocol, source audit, results and replay](interaction/README.md)
