# How quickly does a stale enrollment register consume a review budget?

At day 60 we assigned 878 hypothetical review slots across seven OULAD modules. With current eligibility information, the archived CatBoost ranking selected 285 students who subsequently withdrew, compared with 137.83 expected under uniform selection. Without an eligibility filter CatBoost selected only 47.73 such students, compared with 107.23 under uniform selection. A strong retrospective risk score thus changed from helping to hurting actionable case capture when the queue admitted prior withdrawals. This comparison varies the administrative information supplied to the same scores. Actual delays and intervention effects were unobserved.

| Simulated status delay | CatBoost slots spent on earlier withdrawals | Subsequent cases identified | Actionable precision |
|---|---:|---:|---:|
| Current | 0 | 285 | 32.46% |
| 1 day | 7 | 283 | 32.23% |
| 7 days | 35 | 278 | 31.66% |
| 14 days | 77 | 260.50 | 29.67% |
| 30 days | 185 | 236 | 26.88% |
| Unfiltered | 731.75 | 47.73 | 5.44% |

At each delay we ranked all registrations known to have started by day 60 and removed those whose exit date would already have arrived. Every scenario used the same course-specific budget, floor(10% of true active registrations). A 30-day delay spent 185 slots on people who had left and displaced 49 subsequent cases. The other displaced students would have remained enrolled. Fractional counts are expectations under uniform selection within a tied score block crossing the budget. Each module has a finite eligible roster. The tables are conditional on observed scores, outcomes and the stated delay. They do not estimate sampling uncertainty over future cohorts.

Logistic ranking showed a similar reversal, from 279 subsequent cases with current status to 40.83 without filtering. Results at 5%, 10% and 20% of active enrollment, including the random control at each delay, are available in the [pooled counts](run/summary.csv) and [module counts](run/modules.csv). These are secondary analyses on the previously inspected 2014J presentation. The budget assumes a fixed number of seats supplied to each queue. It cannot estimate the number of staff hours actually available. [Frozen design](design.md) · [Original landmark population and source](../manuscript.md)

## Reproduction

From the repository root, use the parent study's scientific Python environment. The second implementation reads the original registration and outcome tables using the standard library and verifies the 378 module-level comparisons with SQL ranks and tie counts.

```sh
set -eu
d=research_v4_2/external/landmark/status_lag
a=private_data/raw/oulad/2013-2014/oulad.zip
out=$(mktemp -d)
(cd "$d" && sha256sum -c design.sha256)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$d/replay.py" "$a" "$out"
python "$d/verify.py" "$a" "$out"
diff -r "$d/run" "$out"
```

## A fixed-rule check across three other presentations

Before evaluating the remaining presentations, we fixed two rules that require no trained classifier. One ranks students with a longer period since their last activity first. The other ranks students with fewer clicks first. In each of the three earlier presentations, both rules captured more subsequent withdrawals than uniform selection with current status and fewer with an unfiltered queue. For instance, in 2013J the recency rule captured 167.02 cases versus 96.29 with uniform selection when status was current. Without filtering, the corresponding counts were 20.08 and 79.93. The three presentations share modules and some learners and had contributed training data to the separate 2014J model experiment. This is evidence of the same operational effect within one archive. [Protocol](other_presentations.md) · [All earlier-term results](transport_run/transport_terms.csv)

Run `python "$d/transport.py" "$a" "$out/earlier"` and compare that directory with `"$d/transport_run"`. The [module breakdown](transport_run/transport_modules.csv) retains every term, budget and ranking contrast.

## Conditional uncertainty for the ranking reversal

After seeing the queue counts, we resampled learners with replacement 2,000 times. Each bootstrap sample preserves a learner's linked registrations, recomputes the rankings and cutoff ties within each module, and holds the 878 service slots and trained scores fixed. The CatBoost advantage over random review was 16.76 actionable cases per 100 slots with current status (simultaneous 95% interval 13.13 to 20.07), and −6.78 cases per 100 slots without filtering (−8.30 to −5.26). Percentile endpoints use Bonferroni adjustment across these two comparisons. They omit uncertainty from model fitting and institution selection. [Bootstrap estimates](bootstrap.json)

Run `python "$d/uncertainty.py" "$a" | diff - "$d/bootstrap.json"` to reproduce both intervals. Run `python "$d/figure.py"` to regenerate the [queue figure](queues.png).
