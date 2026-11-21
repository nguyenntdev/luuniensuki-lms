# Can joint optimization improve worst-group recall across courses?

On 6,959 UK and 1,767 Portuguese evaluation records, coordinating course thresholds improved the *predicted* worst-group recall over separately optimized thresholds. The improvement in *observed* worst-group recall was −0.35 percentage points in the UK and +1.06 points in Portugal. In Portugal, even a decision maker with all the outcome labels could capture at most **102 cases** while preserving the two score orders and satisfying each prefix constraint and course budget. The registered precision floor required **104**. This shortfall identifies a limitation of the score ordering for that cohort. It also limits what further threshold tuning could achieve. [All policy comparisons](run/results.json) · [Attainability analysis](run/frontier.json)

| Evaluation cohort | Course pools / seats | Independent threshold | Coordinated threshold | Coordinated greedy | Unrestricted |
|---|---:|---:|---:|---:|---:|
| OULAD 2013J | 6 / 695 | 17.62% | 17.27% | 18.13% | 11.57% |
| UCI 697 | 16 / 168 | 13.78% | 14.84% | 14.84% | 9.89% |

Values are worst-group recall. The paired recall-gain intervals versus independent thresholds are −0.85 to +0.19 and −1.08 to +2.32 percentage points, respectively. In Portugal, coordinated allocation attained precision 54.17%, against 62.50% without constraints. In OULAD its precision was 29.50%, against 29.78%. Both lower bounds for the precision difference fell below the allowed −1 point. The shared and per-course utility caps selected identical UK lists. In Portugal sharing the slack replaced nine selections relative to the exact solver using per-course utility floors. These are retrospective comparisons of fixed hypothetical review lists. They estimate neither benefit of review nor actual institutional capacity. [Design](design.md) · [Input data and previous allocation study](../manuscript.md)

## Optimization and the retrospective bound

Within each course, any fixed number of female seats determines two score prefixes. A multiple-choice integer program chooses one pair per course, keeps the total predicted captures within .01 per seat of the best prefix-feasible utility, and maximizes the smaller of the two pooled predicted recalls. A matched exact solver additionally enforces each course's own utility floor. Greedy coordination starts at the best estimated capture counts and takes improving single-seat exchanges. Each final list satisfies the course's prefix representation table. The solver generalizes familiar constrained-ranking formulations to this pooled utility comparison. It uses published group-level fields and an adjusted FA*IR-style prefix table. [Celis et al.](https://arxiv.org/abs/1704.06840) · [Zehlike et al.](https://arxiv.org/abs/1706.06368)

After observing the policy outcomes, a separate diagnostic replaced estimated captures with actual case counts and examined all within-course threshold pairs. At each achievable number of female cases a dynamic program retains the largest male count. All other states with the same female count are dominated for total captures and worst-group recall. A bitset verifier independently represents *every* reachable pair of captured counts. In OULAD the score-order upper bound at the precision floor was 18.83%, less than two points above the 18.13% greedy result. In Portugal the floor was infeasible. Permitting reordering with hindsight raised the two upper bounds to 57.41% and 30.77%. These last bounds use outcomes unavailable at decision time. [Diagnostic design](oracle_design.md)

## Reproduction

The OULAD development test uses one registration per learner and excludes learners in the parent study's later test roster. The Portuguese test uses a deterministic source-row split because no public learner ID or event dates are available. Both institutions had been examined in earlier research. Four Portuguese test rows in a small course were excluded by the fixed pool rule. The predictors use only the admission and registration features listed in the design. The scripts verify the raw archives. Record-level features and identifiers remain in the ignored input cache. The result files contain aggregate counts and option tables.

```sh
set -eu
d=research_v4_2/external/allocation/joint
r=private_data/raw
out=$(mktemp -d)
(cd "$d" && sha256sum -c protocol.sha256 && sha256sum -c oracle.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$d/screen.py" "$r" "$out"
python "$d/frontier.py" "$r" "$out/results.json" > "$out/frontier.json"
python "$d/verify.py" "$out"
diff -r "$d/run" "$out"
```
