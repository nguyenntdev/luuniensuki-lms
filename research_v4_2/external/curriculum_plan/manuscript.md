# Does screening a course-placement request save search time at the optimal curriculum load?

## Abstract

A curriculum planner can reject some proposed placements before calling an integer solver. Whether this saves time depends on the propagation already available to the solver. We tested six decision services on 448 simulated two-course requests from fourteen reserved Balanced Academic Curriculum Problem instances. Checking every contiguous interval for capacity conflicts avoided 234 integer calls and reduced service time by 17.77% against an unfiltered solver. Against a solver supplied with precedence-narrowed domains, the reduction was 0.90% (simultaneous bootstrap interval −3.91% to 7.55%). All services exhausted their budget on one feasible request. Neither registered success criterion was met. An ancillary enumeration of Boolean prerequisite repairs found a mean saving of 0.110 courses on one catalog table and zero on another. These results characterize two computational decisions in curriculum revision. They supply no observations of human editing.

## Problem and contribution

Given an existing curriculum, can two courses move to requested terms while retaining the smallest achievable maximum term load? The published BACP minimizes that maximum subject to prerequisite arcs and lower and upper bounds on credits and course counts. We condition on its certified optimum and ask a sequence of separate feasibility questions. Earlier work formulated educational planning in constraint programming and studied richer load-balancing models. Interval overload checks specialize the established cumulative-resource reasoning of Baptiste, Le Pape and Nuijten to unit-duration courses with fixed credit demands. Our contribution is the measured incremental value of this inexpensive screen against domain narrowing, singleton tests, fractional assignment and integer search under a common service budget. [CSPLib problem and original references](https://www.csplib.org/Problems/prob030/) · [Chiarandini et al.](https://doi.org/10.1007/s10732-011-9158-2) · [Baptiste et al., 1999](https://doi.org/10.1023/A:1009822502231)

## Decision procedure and guarantees

Let course i occupy integer term tᵢ with positive credit weight wᵢ. A prerequisite edge i→j requires tⱼ ≥ tᵢ+1. Initialize each domain to the full horizon or the singleton requested term. Propagate earliest terms forward in topological order and latest terms backward.

**Proposition 1.** On a DAG with interval domains these passes decide precedence-only feasibility. Every bound update follows from an edge, so a crossed bound certifies impossibility. Otherwise the earliest-term vector belongs to the original domains and satisfies every edge by the forward recurrence. The two passes take linear time in vertices plus edges.

**Proposition 2.** For a term interval I, sum the weights of courses whose surviving windows lie inside I, and separately those whose windows intersect I. The first sum lower-bounds the actual mass in I and the second upper-bounds it, by set inclusion. Hence rejection is sound if the first exceeds |I| times the period ceiling or the second falls below |I| times the floor. Unit weights give the enrollment tests. A two-dimensional prefix sum indexed by earliest and latest terms permits all contiguous intervals to be checked in O(n + H²) time and O(H²) extra storage for n courses and H terms after propagation. Passing is inconclusive because the same course can contribute to several availability bounds and courses cannot be split. Surviving requests go to integer search.

## Design and controls

The pinned benchmark has 28 instances, each with 50 courses and ten terms. Development used the fourteen odd identifiers. At the administrative ceilings, precedence alone rejected 190/448 requests, including 182/224 drawn across all terms and 8/224 drawn within individual precedence windows. Every survivor had a timetable. Tightening the credit ceiling to the smallest feasible peak raised infeasibility to 252 on the same requests. Starting at the ceiling of average load, each smaller candidate peak required an infeasibility decision before acceptance of a witnessed peak. All-interval capacity found 39 additional conflicts. Neither expected-term nor cumulative-precedence fractional assignment found another. Integer search identified the last 23. This motivated freezing the simpler interval policy. [Development decisions](term_requests/balanced/results.json) · [Confirmation protocol](term_requests/confirmation/design.md)

On each even identifier the locked sampler generated sixteen requests of each type with two placements per request. All six services reused a base template and peak certificate. The LP control adds cumulative fractional precedence inequalities after interval tests. The bounded-domain control passes precedence bounds into the integer model. CP-SAT used one worker and three deterministic time units per query. Three shuffled complete timing blocks on a fixed core included method-specific work, model cloning, search and witness materialization. Base certification and offline verification were excluded. We averaged request medians within curricula and took geometric means of paired curriculum ratios. The intervals use 10,000 paired curriculum bootstrap draws with Bonferroni adjustment over five comparisons. Requests share curricula and repetitions share requests.

## Confirmation results

| Comparator | Integer calls | Time saved by interval service | Simultaneous interval |
|---|---:|---:|---:|
| Unfiltered CP-SAT | 448 | 17.77% | 7.02 to 31.87% |
| Precedence precheck | 260 | 7.89% | 1.89 to 17.53% |
| Singleton capacity | 219 | 1.88% | −0.15 to 6.49% |
| Interval plus cumulative LP | 214 | 42.10% | 29.28 to 53.91% |
| Precedence-narrowed CP-SAT | 260 | 0.90% | −3.91 to 7.55% |

The interval service called CP-SAT 214 times. Extending singleton checks avoided only five additional calls. All six agreed on 188 feasible, 259 infeasible and one unresolved request. An independent integer encoding corroborated the negative decisions and, with a larger budget, found a timetable for the unresolved request on instance 18. This preserves the original timeout in the timed endpoint. [Decisions and measurements](term_requests/confirmation/results.json) · [Independent verification](term_requests/confirmation/verification.json)

### Request mix and dependence

A descriptive extraction from frozen repetitions gives the following breakdown. The extraction performs no fitting or policy selection.

| Placement sampler | Feasible | Infeasible | Unknown | Interval calls | Curricula faster than bounded control |
|---|---:|---:|---:|---:|---:|
| All terms | 35 | 189 | 0 | 39 | 4/14 |
| Within individual windows | 153 | 70 | 1 | 175 | 6/14 |

Window sampling admits many more placements that need integer search. Even at the fixed 50:50 mixture the interval service was faster than the bounded control on only five curricula. Its paired time ratio ranged from 0.7535 (instance 12) to 1.1113 (instance 10). Thus the positive geometric-mean saving coexists with a slowdown on the majority of curricula. The split is descriptive and supplies no new independent test set. [Per-instance and sampler table](term_requests/strata/results.csv)

## Ancillary experiment on direct prerequisite repair

A different revision occurs before term assignment. Given three simultaneous targets, find the fewest distinct added courses satisfying their direct monotone Boolean rules from an empty transcript. Nyland's versioned deposit provides nested rules. Its computing and mathematics tables contributed 23/32 and 18/26 eligible rows respectively. Nine rules were empty and eight contained opaque conditions such as placement or credits. Excluding 404 and 269 triples containing a target prerequisite left 1,367 and 547 eligible triples. [Nyland, source deposit](https://doi.org/10.5281/zenodo.23313887) · [Selection protocol](protocol.md)

**Proposition 3.** Maintain inclusion-minimal satisfying addition sets. A leaf contributes its singleton, disjunction pools alternatives, and conjunction takes all pairwise unions. Structural induction gives a subset of every satisfying choice in the resulting family. Removing supersets is safe because A ⊆ B implies A ∪ C ⊆ B ∪ C for every future choice C. Conjoining targets and minimizing cardinality therefore yields a global minimum. The frontier can be exponential: k disjoint binary choices yield 2ᵏ incomparable sets.

| Table | Independent least-cost choices | Sequential overlap | Exact, pruned or unpruned | Improved over independent |
|---|---:|---:|---:|---:|
| Computing | 3.509 | 3.458 | 3.399 | 150/1,367 |
| Mathematics | 3.786 | 3.786 | 3.786 | 0/547 |

An independent postfix evaluator checked witnesses and ruled out every smaller cardinality. Both tables missed the one-course mean development margin. For simulated appends, reusing a two-target frontier cost 6,933 and 3,551 post-edit unions versus 14,283 and 5,838 with identical cold pruning (14,864 and 6,075 unpruned). Building the cached prefixes cost exactly the respective differences, 7,350 and 2,287. The benefit shifts previously completed work outside the append operation. Counts omit dominance comparisons and storage. [Repair witnesses](run/repairs.csv) · [Append episodes](incremental/episodes.csv)

## Interpretation and readiness

The two experiments cohere as decisions made during curriculum revision, but they have different inputs, objectives and reference answers. The catalog enumeration supplies a separate direct-repair case study and cannot corroborate a scheduling speed effect. Neither corpus measures recursive prerequisite acquisition, actual requests, transcript variation or teacher effort. Catalog triples reuse rules. Timetable instances share one benchmark family, and machine timings condition on the host, solver version, budget and service boundary. The interval around the strongest control permits both a slowdown and a small gain. No runtime equivalence margin was specified.

The manuscript is ready as a bounded empirical comparison with a negative confirmatory result. The evidence falls short of the registered 10% gain against every comparator and full-service resolution. It supports neither a new general propagation algorithm nor deployment-level productivity claims.

## Reproduction

From the repository root use Python 3.12, NumPy and OR-Tools 9.14.6206. Obtain both digest-checked archives with the download commands in the [catalog instructions](README.md) and [CSPLib instructions](term_requests/README.md). The following single-core confirmation run respects a twelve-core allocation. The original timing protocol used fourteen separate cores concurrently, so fresh wall times will vary.

```sh
set -eu
d=research_v4_2/external/curriculum_plan
r=private_data/raw/csplib-bacp/bacp.zip
z=private_data/raw/otago-prereqs/release.zip
t=$(mktemp -d)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
run() { taskset -c 0-11 python3 "$@"; }
(cd "$d" && sha256sum -c protocol.sha256)
(cd "$d/term_requests/confirmation" && sha256sum -c protocol.sha256)
run "$d/screen.py" "$z" "$t/catalog"
run "$d/verify.py" "$z" "$t/catalog" > "$t/catalog/verification.json"
diff -r "$t/catalog" "$d/run"
run "$d/incremental/study.py"
run "$d/incremental/verify.py"
run "$d/term_requests/screen.py" "$r" "$t/admin" --workers 4
cmp "$t/admin" "$d/term_requests/results.json"
run "$d/term_requests/balanced/screen_balanced.py" "$r" "$t/balanced" --workers 4
cmp "$t/balanced" "$d/term_requests/balanced/results.json"
run "$d/term_requests/confirmation/evaluate.py" "$r" "$t/fresh.json" --cores 0
run "$d/term_requests/confirmation/verify.py" "$r" --workers 4 > "$t/verified"
cmp "$t/verified" "$d/term_requests/confirmation/verification.json"
run "$d/term_requests/strata/extract.py" > "$t/strata.csv"
cmp "$t/strata.csv" "$d/term_requests/strata/results.csv"
run -m pytest tests/research_v4_2
```

A development follow-up jointly bounded term enrollments and credit loads. Of 448 requests the existing screen rejected 229. The extra certificate rejected none of the remaining 219, including 23 subsequently proved infeasible by the matched solver. This limits the prospect of accelerating this sample through the additional bound. [Certificate derivation and controls](term_requests/certificates/README.md)
