# Wikipedia second-worker attack forecast

On 23,001 held-out revisions, the frozen two-pseudo-item signature smoother reduced Brier loss from 0.11045548 for the binary conditional forecast to 0.10894103. The signed difference was −0.00151445 (simultaneous 95% CI [−0.00165456, −0.00137434]). Dev selected zero shrinkage, so the dev-tuned and unsmoothed forecasts produced identical test predictions. The interval against the dev-tuned forecast crossed zero (difference −0.00000010, simultaneous 95% CI [−0.00000160, 0.00000140]). In this transfer, the subtype flags improved prediction beyond the first vote, and the effect of using two pseudo-items instead of the dev-selected strength remained unresolved.

## Held-out scores

Differences are the fixed smoother's loss minus the comparator's loss. The binary and dev-tuned Brier intervals use the prespecified Bonferroni correction. The other Brier intervals and all log-loss intervals are marginal. All intervals use normalized-text clusters and condition on the final fits and realized workers.

| Forecast | Brier | Brier difference (95% CI) | Natural log loss | Log-loss difference (95% CI) |
|---|---:|---:|---:|---:|
| Fixed, strength 2 | 0.10894103 | — | 0.36633882 | — |
| Dev-tuned, strength 0 | 0.10894114 | −0.00000010 [−0.00000160, 0.00000140] | 0.36633903 | −0.00000021 [−0.00000303, 0.00000261] |
| Binary conditional | 0.11045548 | −0.00151445 [−0.00165456, −0.00137434] | 0.36942467 | −0.00308585 [−0.00333740, −0.00283430] |
| Unsmoothed signature | 0.10894114 | −0.00000010 [−0.00000141, 0.00000121] | 0.36633903 | −0.00000021 [−0.00000303, 0.00000261] |
| Train-plus-dev marginal | 0.13933368 | −0.03039265 [−0.03172631, −0.02905899] | 0.45164395 | −0.08530512 [−0.08848946, −0.08212079] |
| Repeat the first vote | 0.14880550 | −0.03986447 [−0.04090164, −0.03882730] | 0.70731524 | −0.34097642 [−0.34817721, −0.33377563] |

First-positive votes carried 16.73% of test item mass. Conditional on those votes, the descriptive fixed-minus-binary differences were −0.00905110 for Brier and −0.01844258 for log loss. First-negative votes all had the same signature, so the fixed and binary forecasts tied in that stratum. Stratum means retain each pair's original within-item weight and divide by the stratum's total mass. The 16 observed test signatures include a cell with just 287 ordered pairs and 1.56292 units of item mass.

## Input and eligibility audit

| Official split | Source revisions | Source rating rows | Source text groups | Revisions excluded across splits | Eligible revisions | Eligible groups | Eligible workers | Ordered pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Train | 69,526 | 762,046 | 69,297 | 302 | 69,224 | 69,099 | 4,048 | 8,558,884 |
| Dev | 23,160 | 253,589 | 23,123 | 161 | 22,999 | 22,983 | 4,017 | 2,828,374 |
| Test | 23,178 | 349,582 | 23,139 | 177 | 23,001 | 22,991 | 4,037 | 5,973,776 |

The revision join was exact. The published rating literals were `0.0` and `1.0`. The audit found zero binary-versus-OR discrepancies, redundant rating rows, worker–revision conflicts, empty panels, or single-worker panels. Across the 115,304 normalized-text groups, 231 spanned multiple official splits and accounted for all 640 excluded revisions. Within-split repeats remained separate items and shared a cluster. Of the 4,037 test workers, 4,034 also rated eligible train or dev items.

Each eligible revision carries one unit of mass spread evenly over ordered distinct-worker pairs. The evaluator counts those pairs by first-worker signature and second-worker outcome. It fits the dev grid on train and refits on the 92,223 eligible train-plus-dev revisions after choosing the dev strength. All forecasts use the frozen clipping bounds. [Frozen protocol](protocol.md)

The outcome is another archived worker's personal-attack vote on the same revision. The subtype flags are an unordered set of selections. Exact normalized-text grouping addresses duplicate text, and related comments can still share conversation context. Worker overlap and the clustered intervals limit inference to the observed annotator pool and fitted forecasts.

## Reproduce

From this directory, use Python 3.11+ with the two staged source TSVs outside the repository. The published files are [comment metadata (7554634)](https://figshare.com/ndownloader/files/7554634) and [individual ratings (7554637)](https://figshare.com/ndownloader/files/7554637) from Wulczyn, Thain and Dixon's CC0 release. [Version 6](https://doi.org/10.6084/m9.figshare.4054689.v6) · [Publisher schema](https://meta.wikimedia.org/wiki/Research:Detox/Data_Release#Schema_for_attack_annotations.tsv)

```sh
source_dir=/tmp/rater-panel-transfer.uMP7MN9O
sha256sum -c protocol.sha256
taskset -c 0-9 python evaluate.py "$source_dir" | diff - result.json
```

The evaluator verifies the protocol and input hashes before parsing. The saved result was generated with CPython 3.12.3 and Unicode 15.0.0. [Aggregate result](result.json) preserves the full dev grid, final fitted cells and clipped forecasts, test support including zero-mass signatures, stratum losses, signed differences, cluster standard errors and intervals. An independent calculation that explicitly enumerated all 17,361,034 ordered pairs matched the split audits, dev grid, signature masses and forecasts, test losses and intervals.
