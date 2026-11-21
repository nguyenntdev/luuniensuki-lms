# What can the published predictions establish when exited learners have no score?

The published day-84 OULAD supplement scores all 8,566 eligible enrollments and omits earlier exits. At 30 days of reporting delay, 320 earlier exits could take seats in the fixed queue of 857. Whatever scores they would receive, the published assessment logistic model would capture **199–291** actionable cases, against 109.37 expected for uniform ranking of that stale roster. All eight published scoring models still exceed uniform at that delay. With no filter, 2,684 earlier exits have missing scores, and the corresponding bounds for logistic regression widen to **0–291**. Uniform review would capture 86.39. The sign of the unfiltered comparison is unidentified on these exports. [Verified prior-work replay](../published_capacity/README.md) · [All 48 bounds](results.csv)

Let m be the number of newly admitted stale records and K the fixed number of seats. The selected eligible prefix can range from max(0,K−m) to K. Count subsequent cases in those two prefixes, averaging over cutoff ties. Their interval gives sharp bounds on expected capture under the score-completion assumption. All published probabilities lie strictly inside (0,1); assigning the missing records probability 1 or 0 realizes the respective endpoints. The code verifies both completed queues directly. These bounds quantify missing scores in a finite cohort. They do not measure the probability of either completion, sampling uncertainty or actual delivery delays. The published endpoint includes 87 withdrawals with no recorded exit date.

Use the source archives from the [published replay](../published_capacity/README.md). From the repository root run the command below.

```sh
p=research_v4_2/external/landmark/status_bounds
python "$p/bounds.py" private_data/raw/oulad/2013-2014 | diff - "$p/results.csv"
```
