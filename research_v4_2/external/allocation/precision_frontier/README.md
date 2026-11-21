# How many score-prefix replacements would close the precision gap?

With the archived CatBoost scores, fixed within-group score prefixes can
capture at most 185 of the 201 cases required in OULAD and 101 of the 104
required in UCI 697. Allowing same-group replacements only within ten ranks
on either side of each cutoff makes the precision floor feasible in both
cohorts. OULAD still cannot reach the worst-group recall target. UCI 697 can
reach both targets with three replacements, each adjacent to a cutoff.
These are best-case counts computed with evaluation outcomes.

| Allowed rank distance on each side | OULAD maximum captures | OULAD minimum replacements for precision / both | UCI 697 maximum captures | UCI 697 minimum replacements for precision / both |
|---|---:|---:|---:|---:|
| 0 (fixed order) | 185 | infeasible / infeasible | 101 | infeasible / infeasible |
| 1 | 186 | infeasible / infeasible | 108 | 3 / 3 |
| 5 | 192 | infeasible / infeasible | 139 | 3 / 3 |
| 10 | 204 | 20 / infeasible | 147 | 3 / 3 |
| Unrestricted distance | 635 | 16 / 40 | 168 | 3 / 3 |

Both means meeting the original precision floor and exceeding the strongest
archived constrained policy's worst-group recall by at least two percentage
points. OULAD uses 695 seats across six courses and has 526 female and 579
male cases. Its 20.13% recall target requires 106 and 117 captures,
respectively. UCI 697 uses 168 seats across 16 courses and has 283 female
and 260 male cases. Its 18.15% target requires 52 and 48 captures. Course
budgets and FA*IR prefix requirements apply in every row.

The OULAD joint target needs at least 223 captures, so the ten-rank band's
ceiling of 204 rules it out before checking group balance. At that band,
meeting the original precision floor costs 20 replacements, four above the
minimum with unrestricted distance. UCI 697 reaches the best possible edit
count with only adjacent exchanges. Lowering the floor to the boosted
scorer's own unrestricted precision minus one point changes the fixed-order
result in Portugal, where zero replacements can meet both targets at the
94-case floor. In OULAD the 169-case floor allows zero replacements for
precision alone and still requires 40 with unrestricted distance for the
joint target. All archived comparisons, band arms, and infeasible cells are
retained. [Full results](run/results.json) · [Frozen design](design.md)

The replacement bound allows the reference group seat split to vary by
course, so it is optimistic relative to changing a particular archived
selection. A replacement counts even across tied scores because the
archived lexical ordering fixes membership. Feasibility uses realized case
counts. The bound gives no estimate of which replacements a prospectively
chosen policy could identify, the paired precision lower confidence bound,
or what support would change. Both public cohorts had been inspected in
earlier development studies. [Prior joint study](../joint/README.md) ·
[Archived boosted study](../joint/boosted/README.md)

## Reproduction

Run from the repository root. Use Python 3.12.3 with NumPy 2.4.4, pandas
3.0.2, SciPy 1.17.1, scikit-learn 1.8.0 and pytest 9.1.1. The two source
archives are `private_data/raw/oulad/2013-2014/oulad.zip` and
`private_data/raw/uci/dropout-697/source.zip`. The parent loaders check the
source checksums. The replay also checks the committed CatBoost forecast
hash and evaluation row-order digest for each cohort. It freezes both
cohorts' score orders and targets before requesting their evaluation
labels. It writes aggregate results only. No model fitting is needed.

```sh
set -eu
d=research_v4_2/external/allocation/precision_frontier
b=research_v4_2/external/allocation/joint/boosted
out=$(mktemp -d)
(cd "$d" && sha256sum -c design.sha256)
(cd "$b/run" && sha256sum -c forecasts.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$d/run.py" private_data/raw "$out/results.json"
diff -u "$d/run/results.json" "$out/results.json"
python "$b/verify_floors.py" "$b/run"
python -m pytest -q tests/research_v4_2 "$d/test_minimum.py"
```

The replay checks that both endpoint arms reproduce every course's archived
capture table and both archived recall ceilings. A budget-indexed dynamic
program confirms each integer optimum and rejects every smaller budget.
The focused tests enumerate learner subsets and compare them with both
optimization formulations on small courses.
