# When does a cheap repair compete with Lagrangian set cover?

On 45 weighted OR-Library instances, removing one chosen column and repairing the resulting cover improved reverse-deletion greedy on 41 instances and tied it on four. Its ranking against Zhu’s Lagrangian heuristic depended on search effort. Repair beat the median of three short comparator runs on 23 instances, tied on 11 and lost on 11. With the comparator’s larger iteration budget, repair won eight, tied six and lost 31. Family D was the exception to the overall ranking. Repair beat or tied the extended comparator median on all five instances there. [Instance-level comparisons](instances.csv)

## Instances and methods

We took every instance in Beasley’s families 4, 5, 6, A, B, C and D. These include related matrices of different sizes and densities. Families 4 and 6 each have 200 rows and 1,000 columns at nominal densities of 2% and 5%. Family 5 doubles the column count at 2%. Families A/B and C/D pair the same two nominal densities at 300 × 3,000 and 400 × 4,000. Each budget profile downloaded every original text file afresh from Brunel. Both sets of bytes passed the recorded SHA-256 checks, and the family 4 bytes and both greedy witnesses matched the initial benchmark exactly. The sample excludes the E, large NRE–NRH, unicost and railway collections. [OR-Library catalogue](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html) · [Initial experiment](../manuscript.md)

1. **Greedy** adds the column maximizing newly covered rows per unit cost, breaking ties by original column order. **Pruned** then checks the chosen columns in reverse insertion order and deletes each redundant column.
2. **Exchange** starts from Pruned. For each selected column in turn, remove it, forbid its immediate reselection, and greedily cover the newly exposed rows. Reverse-prune the entire trial, including previously retained columns. Accept the trial with the greatest strictly positive saving, keeping the first in a tie. Stop when a full pass yields no saving. This evaluates one greedy repair per dropped column. Strict descent on a positive integer objective guarantees termination. Each accepted cost is recorded.
3. **Zhu** runs the author's unmodified SetCoverPy implementation of Lagrangian relaxation, subgradient updates and multiplier-guided greedy construction. The published method and code were already evaluated on Beasley's instances. This study measures their behavior under the specified budgets on a familiar benchmark. Reference costs were read only for scoring. [Zhu’s paper](https://arxiv.org/abs/1606.07156) · [Pinned solver source](https://github.com/guangtunbenzhu/SetCoverPy/blob/a1ff3c5cec45cc1b16541999a4adb593fa652363/SetCoverPy/setcover.py)

## Budget and comparison

For each instance both comparator profiles use NumPy seeds 11, 29 and 47. The short profile sets the constructor parameters `(maxiters, subg_nsteps, subg_maxiters)` to `(3, 2, 6)`. The extended profile uses `(6, 4, 18)`. Upstream multiplies the middle setting by 20 internally and applies its own convergence rules. The extended profile was added after the short results showed frequent iteration-limit warnings. It is an explicit budget sensitivity analysis on the same data. At least one inner-limit warning occurred in 135/135 short and 130/135 extended solves. All runs returned feasible witnesses within the 90 process-CPU-second safety cap per stage.

On an Intel Xeon E5-2696 v4, median cumulative CPU times for greedy, pruning through completion and exchange through completion were 0.031, 0.032 and 0.250 s across the 45 short-profile instances. Comparator median CPU per individual solve was 1.381 s for short and 5.608 s for extended, with maxima of 3.213 and 14.931 s. Each worker ran a single instance at a time with BLAS and OpenMP thread limits of one. Eight workers ran the short profile and twelve ran the extended profile. CPU accounting covers construction and optimization after parsing. Networking, parsing, witness auditing and the separate LP bound computation are outside the solver timings. The methods use different amounts of compute. The paired costs establish what each implementation returned at its own stopping rule.

## Results by family

Each cell is the mean instance percentage excess over the published reference cost, with equal weight for each instance within its family. For Zhu we first take the median objective over the three seeds on each instance. The last column counts instances where Exchange costs less than, the same as, or more than this extended median. Full seed ranges appear in the CSV and individual witnesses in the two JSON files. [Reference table, fourth field](https://github.com/guangtunbenzhu/SetCoverPy/blob/a1ff3c5cec45cc1b16541999a4adb593fa652363/SetCoverPy/scp_BeasleyOR_test_results.txt) · [Short runs](runs.json) · [Extended runs](extended.json)

| Family | Instances | Greedy % | Pruned % | Exchange % | Zhu short % | Zhu extended % | Exchange W/T/L |
|---|---:|---:|---:|---:|---:|---:|---:|
| 4 | 10 | 11.47 | 3.52 | 1.03 | 1.51 | 0.04 | 0/2/8 |
| 5 | 10 | 12.33 | 4.93 | 2.76 | 1.14 | 0.19 | 1/0/9 |
| 6 | 5 | 15.63 | 8.22 | 2.74 | 3.61 | 1.50 | 1/0/4 |
| A | 5 | 15.31 | 4.88 | 2.15 | 2.40 | 0.57 | 0/0/5 |
| B | 5 | 11.40 | 4.03 | 2.08 | 3.46 | 1.88 | 2/1/2 |
| C | 5 | 14.15 | 4.51 | 2.04 | 3.29 | 1.49 | 1/1/3 |
| D | 5 | 15.67 | 9.65 | 2.97 | 5.93 | 6.26 | 3/2/0 |

On scpd1, reverse deletion left cost 67. Successive exchanges reduced it to 65, 63, 62 and 61. Every extended Zhu run returned 67 against a reference of 60. On scp410 the pattern differed. Exchange reached the certified optimum of 514, all short comparator runs exceeded it, and all three extended runs reached it. Across all families the extended median matched the published reference on 17 instances and Exchange matched it on four. Extended seed costs differed within 21 instances, compared with 40 for the short profile. Family D improved little with extra solver effort in this range. Five instances at that size and density do not isolate which matrix property drove the difference.

## Bounds and independent checks

For every matrix we also solved the continuous covering LP, rounded its nonnegative row prices to rational numbers and increased their common denominator as needed to satisfy every column budget. If row prices sum to at most each column’s cost over the rows that column covers, summing the prices of all rows gives a lower bound on any feasible cover. Integer costs permit rounding the bound upward. The verifier checks all those inequalities in integer arithmetic. Twelve of the 45 bounds match the published reference, and on eleven of those the new runs supply a feasible cover of the same cost. Those eleven therefore have independently checkable optimality certificates. For other instances the table reports distance to an external reference, supplemented by the certified lower bound in the CSV. The earlier family 4 integer-program certificates remain available in the initial experiment. [Dual certificates](dual.json) · [Bound generator](bounds.py)

The independent verifier reads the text matrices directly as row membership lists, checks coverage and recomputes objective values from one-based column IDs. It checks 540 recorded witnesses across two profiles, including the deterministic baselines repeated in each. Three seeds measure limited within-instance variation. Related synthetic families and an implementation tuned on Beasley's test bed limit transfer to other workloads. The planning interpretation covers positive-cost alternative providers with no travel, time windows or prerequisites.

## Reproduce

From this directory on Linux, use Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, Git and curl. Pick a CPU allowed by your machine for the separate LP command. The original host used CPU 0. Running the following into a temporary directory preserves the recorded evidence.

```bash
work=$(mktemp -d)
git clone https://github.com/guangtunbenzhu/SetCoverPy "$work/SetCoverPy"
git -C "$work/SetCoverPy" checkout a1ff3c5cec45cc1b16541999a4adb593fa652363
python study.py "$work/short-data" "$work/SetCoverPy" "$work/runs.json" --jobs 8 --profile short
python study.py "$work/extended-data" "$work/SetCoverPy" "$work/extended.json" --jobs 12 --profile extended
taskset -c 0 python bounds.py "$work/short-data" "$work/dual.json"
python verify.py "$work/short-data" --csv "$work/instances.csv"
diff instances.csv "$work/instances.csv"
```

The verifier defaults to the archived JSON files beside the script. Pass `--evidence "$work"` to verify the replayed outputs as well. Timing fields vary by machine. Per-instance comparison rows, witness columns and rational certificates can be checked independently of timing.
