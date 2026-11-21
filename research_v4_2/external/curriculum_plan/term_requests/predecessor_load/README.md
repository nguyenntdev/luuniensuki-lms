# Precedence-closure credit bounds for fixed course terms

Probing tentative placements with the full interval credit check rejected **12 additional requests** across eight of the 14 development curricula. The original precedence and interval screen rejected 229 of 448 requests. Probing raised that total to **241 of 448 (53.8%)**, a gain of 2.68 percentage points. It resolved 12 of the 23 infeasible requests left by the original screen and left 207 requests for CP-SAT, including 11 infeasible ones. All 196 feasible requests retained their saved witnesses. Fresh CP-SAT runs reproduced all 448 saved statuses under the same fixed peaks and per-request search budget.

| Request sampler | Requests | CP-SAT infeasible | Precedence | Added by original intervals | Added by full interval probing |
|---|---:|---:|---:|---:|---:|
| Unrestricted | 224 | 196 | 182 | 9 | 4 |
| Individual original windows | 224 | 56 | 8 | 30 | 8 |
| Total | 448 | 252 | 190 | 39 | 12 |

## Why the direct closure bound is redundant

For a course \(v\) fixed in term \(t_v\), any ancestor \(a\) with a longest prerequisite path of length \(d(a,v)\) to \(v\) must finish by \(t_v-d(a,v)\). Propagating every fixed request gives \(U_a\leq\min_v(t_v-d(a,v))\) over the reachable requested courses. The existing screen already computes these upper bounds along with lower bounds \(L_a\) and checks for empty windows.

For every cutoff \(k\), the union of all courses with derived deadlines at most \(k\) is a subset of the courses with \(U_a\leq k\). The existing \([1,k]\) interval check already charges the full credit of every such course once against \(k\) times the peak. This covers individual closures, overlapping closures across requests and the earlier deadlines implied by longer paths. It includes fixed courses whose terms lie inside the prefix. Analogous release bounds for descendants are covered by suffixes. Any course whose entire propagated window lies inside an interior interval also contributes its full credit there.

The fractional model assigns one unit per course and restricts all its mass to its propagated window. Summing the fractional credit ceilings over an interval therefore gives the same unconditional compulsory-credit inequality, even before adding cumulative precedence constraints.

## Stronger necessary conditions

**Tentative placements.** Start from the windows propagated under both fixed requests. Test a course at its earliest or latest surviving term \(t\). Its ancestors acquire deadlines \(t-d(a,v)\) and its descendants acquire release terms \(t+d(v,b)\), intersected with their current windows. If compulsory credit in any checked interval exceeds its length times the peak, that tentative term is impossible. Remove the tested endpoint, propagate the tightened bound along the same longest paths, and repeat until a window is empty or a full pass makes no deletions. The argument is inductive. Each tested conflict rules out every completion using that endpoint and each bound update follows from the original strict prerequisites. An empty window certifies infeasibility. A surviving request still goes to CP-SAT.

**Rounded compulsory credit.** For every integer divisor \(q\geq2\) through the largest course credit, give course \(a\) weight \(\lfloor w_a/q\rfloor\) and each term capacity \(\lfloor P/q\rfloor\), where \(P\) is the fixed peak. The sum of rounded-down credits in a term is at most the rounded-down total, which is at most the rounded-down peak. Apply this upper bound to the compulsory courses in every interval of the original propagated windows. This separately tests a consequence of indivisible courses.

| Additional check on the same 219 baseline survivors | Further rejections | Endpoints deleted | Tentative placements tested |
|---|---:|---:|---:|
| Saved cumulative fractional relaxation | 0 | | |
| Rounded compulsory credit on original windows | 0 | | |
| Probe prefixes | 0 | 295 | 29,195 |
| Probe prefixes and suffixes | 0 | 2,013 | 44,213 |
| Probe all contiguous intervals | 12 | 3,897 | 57,631 |

Full interval probing tightened at least one endpoint in 217 of the 219 baseline survivors. It averaged 263 tentative checks per survivor. The experiment measured avoided CP-SAT calls and probe counts. Net runtime remains unmeasured. All variants were explored on the same development data. Reserved instances and confirmation requests were excluded.

## Counterchecks

Two small curricula with CP-SAT-certified optimal base peaks establish strict additions to the existing screens. A rounded-credit example needs three 2-credit predecessors in two terms of capacity 3. A probing example fixes a 1-credit course in term 2 and a 2-credit course in term 3. A 4-credit successor is released in term 2. It can split its credit across terms 2 and 3 in the fractional model. Either integer term overloads when fixed. The original interval, joint credit/enrollment certificate and cumulative LP pass both examples. Exhaustive schedule enumeration and CP-SAT agree that both requested schedules are infeasible.

The verifier also enumerates all schedules for 6,912 synthetic two-placement cases across 64 four-course DAGs and two credit profiles. It checks every feasible schedule against the retained windows for each probing variant. For the development rejections, it independently propagates along edges and recomputes compulsory credit for all 247 logged endpoint deletions across the 12 certificates.

## Reproduction

Use Python 3.12, OR-Tools 9.14.6206 and the same pinned private benchmark archive as the [parent study](../README.md). The runner verifies the archive digest and matches the saved requests and distributions against the administrative study. It reads the last certified peak from the balanced comparison. Each fresh request solve uses one CP-SAT worker and 0.5 units of deterministic time. No raw benchmark files are written by these scripts.

```sh
set -eu
d=research_v4_2/external/curriculum_plan/term_requests/predecessor_load
r=private_data/raw/csplib-bacp/bacp.zip
out=$(mktemp)
trap 'rm -f "$out"' EXIT
taskset -c 12-23 python "$d/compare.py" "$r" "$out" --workers 12 --exact-replay
cmp "$d/results.json" "$out"
taskset -c 12-23 python "$d/verify.py" "$r" "$out"
taskset -c 12-23 python -m pytest tests/research_v4_2 -q
```

[Per-request decisions and rejection certificates](results.json) · [Saved balanced controls](../balanced/results.json)
