# P02 — Method: Constraint-Aware Learning Path Planning with Alternative Activities

Paper: `LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/05_PAPERS/P02_*.md`
Status of this implementation: **synthetic-benchmark re-engineering** (T3-style
decision tasks). No external dataset is used; the P02 spec's external data gate
(MOOCCubeX / Junyi / CausalEdu) remains **BLOCKED** until rights cards are
approved (P02-T02..T06), so every number below is a *synthetic planning
benchmark result*, not external evidence.

## 1. Research question (frozen)

> When multiple pedagogically equivalent activities can satisfy one goal, does
> an uncertainty-aware (here: constraint-aware, alternative-aware) selection
> procedure reduce false infeasibility or cost regret under hard resource
> constraints, compared against sanity (C0) and strong exact (C1/C2) baselines?

**Estimand**: per-instance joint optimum of the formal objective below; per-solver
feasibility rate, false-infeasibility count, relative optimality gap, runtime.

**H0 (must be published if not rejected)**: the proposed planner yields no
reduction in false infeasibility or cost regret versus a genuinely strong exact
comparator (C1 branch-and-bound) at matched task quality. Because C1 is exact
on our benchmark scale, H0 is in fact the *expected* outcome at this scale; the
value of the study is (a) the formalization + certified benchmark, (b) honest
status reporting, and (c) the demonstrated legacy false-infeasibility fix
(regression family A/B, see §6).

## 2. Formal objective

Given:

- activities `A`, each with dwell cost `c(a) >= 0` (int minutes), provided
  outcomes `P(a)`, required outcomes `R(a)`, accessibility flag, source tier;
- asymmetric travel matrix `T[(x,y)] >= 0` (0 when absent);
- target outcomes `G`; budget `B`; accessibility/authenticity gates.

A **plan** is an ordered tuple `pi = (a1..ak)` of distinct activities with

1. **Coverage (alternative semantics)**: every `g in G` has some `ai` with
   `g in P(ai)` — ONE provider suffices. This is the LN-06 fix: the legacy
   engine summed all providers of an outcome and falsely rejected
   `(A,B both provide T at 40min, budget 50)`.
2. **Prerequisite feasibility**: for each `ai`, `R(ai)` is provided by some
   `aj`, `j < i` (prefix-closed acquisition).
3. **Gates**: `accessible(ai)` and `tier(ai) >= min_source_tier`.
4. **Budget**: `sum c(ai) + sum T[(ai, ai+1)] <= B`.

Objective: minimise `dwell(pi) + travel(pi)`. Decision taxonomy:
`find_valid_route` (1-4 hold), `cost_exceeded` (min-cost plan > B, proven),
`no_feasible_route` (no plan satisfies 1-3, proven), `abstain` (solver gives
up within its budget — never conflated with infeasibility).

**Complexity.** With `T ≡ 0` and `R ≡ ∅` the problem contains minimum-weight
set cover (activities = sets, outcomes = elements), which is NP-hard
(Karp 1972). With travel it additionally embeds asymmetric TSP order
optimisation on the chosen subset. **No polynomial exactness is claimed
anywhere in this codebase.** Exactness claims are always scoped: branch-and-
bound completed within its node budget; Dijkstra/A* terminated with an
admissible heuristic; ordering DP solved within the state cap (2^18).

## 3. Solvers (all deterministic; status always reported)

| id | class | mechanism | optimality claim |
|----|-------|-----------|------------------|
| `c0_greedy` | C0 sanity | cheapest-covering pick, lexicographic Kahn order | none (heuristic) |
| `c1_branch_and_bound` | C1 strong classical | DFS over provider choices with prerequisite closure; exact dwell prune (`travel >= 0`); exact Held-Karp ordering per covering subset (<= 8 stops, else Kahn) | `optimal` when search + exact order complete; `timeout` otherwise (never infeasible) |
| `c2_dijkstra_state` | C2 published/strong slot | **independent exact search (reimplementation)**: Dijkstra over states `(acquired, chosen, last)`, first settled goal state is optimal (non-negative weights) | `optimal` (Dijkstra argument) when completed; NOT a published library — labelled as reimplementation |
| `p02_proposed` | proposed | A* over the same state space with admissible dwell lower bound (max over pending outcomes of cheapest provider), hard accessibility + source-authenticity gates during expansion, exact re-order of the settled subset | `optimal` only when A* completed AND order DP exact; honest downgrade otherwise |
| `a3_alternative_blind` | ablation | legacy all-providers union semantics (mutation probe) | none; expected false-infeasibility family |

Honesty ladder for statuses: `optimal` > `bound_proven` > `heuristic` >
`timeout` > `abstain`. **No solver may print `optimal` unless it proved it.**
False infeasibility (rejecting an oracle-feasible instance) is the cardinal
error; exact solvers must hold it at 0.

Development note (recorded for reproducibility): an earlier draft of the
proposed A* used the SUM of cheapest providers as the dwell heuristic; it is
**inadmissible** when one activity covers several pending outcomes (found via
a certified brute-force mismatch on a dense-cover instance; see tests
`test_p02_optimality_gap.py::test_proposed_matches_oracle_random_small`). The
shipped bound is the max over pending outcomes (safe, weaker) with the failed
variant documented here as a negative result.

## 4. Instance generator (certified ground truth)

Six topology families (the group key for splits): `chain`,
`alternative_pair`, `dense_cover`, `unreachable_bridge`, `mixed_lattice`,
`blocked_access`. Three budget regimes: `tight` (35% of instances get budgets
BELOW the optimum so `cost_exceeded` gold exists), `mid`, `loose`.
Alternative-provider density in {0.0, 0.5, 1.0}.

Ground truth is **never fabricated**: every instance is certified by the
independent brute-force oracle (`oracle.py`, shares no code with solvers)
using subset enumeration + Held-Karp exact ordering. Instances are capped at
the oracle envelope (12 activities, route DP <= 12). Determinism: per-instance
`random.Random` seeded by `(family, regime, seed, index)`; identical seeds
reproduce byte-identical instances.

## 5. Splits and leakage

Instance families are split by `family_id` (topology family + density) with
`research_v3.eval.splitters.group_split(group_key="family_id")` into
train/calibration/dev/test; `assert_no_leakage` guarantees a family never
spans partitions. Test families are therefore unseen by any tuning performed
on train/dev. Oracle modules are evaluator-side only — solvers never import
`oracle.py` (enforced by test).

## 6. Metrics

- **feasibility_rate**: plans returned / instances.
- **false_infeasibility**: oracle-feasible instances rejected (MUST be 0 for
  c1/c2/proposed; any positive count fails the run).
- **exact_match_rate**: decision AND cost equal the certified oracle.
- **optimality_gap**: mean of `(cost - optimum)/max(1, optimum)` on commonly
  feasible instances.
- **runtime**: wall ms total and p95 per instance.
- Paired contrasts: proposed vs C1 (confirmatory), proposed vs C0; Wilcoxon
  signed-rank on per-instance cost differences + cluster bootstrap CIs by
  family (reuses `research_v2.evaluation.statistical_tests`); Holm correction
  across the 2-contrast confirmatory family.

## 7. Falsification expectations (pre-registered)

- A3 (alternative-blind) MUST reproduce false infeasibility on the A/B family;
  if it does not, the mutation is broken.
- C0 MUST show positive optimality gap and nonzero false infeasibility;
  a C0 "win" would indicate a broken generator.
- On this synthetic scale, proposed == C1 in solution quality is the expected
  null result (H0); any *runtime* advantage/disadvantage is secondary and
  reported per regime.
- If OR-Tools/PuLP were available, C2 would be CP-SAT; in this environment
  neither is installed, so C2 is an **independent exact search
  (reimplementation)** and is labelled as such everywhere — never as a
  published library. The CP-SAT comparison remains future work.

## 8. Limitations

1. Synthetic instances only; external datasets (MOOCCubeX, Junyi, CausalEdu)
   are blocked on rights cards — no external validity is claimed.
2. The proposed method differs from C1 mainly in the gates it enforces and
   its search order; on instances where gates are inactive, identical
   solutions are expected (matched-information comparison).
3. Held-Karp ordering caps at 2^18 states; larger chosen subsets fall back to
   lexicographic Kahn (status downgraded honestly).
4. Wall-clock timing on shared hardware is noisy; only order-of-magnitude
   claims are made.
5. `abstain`/`timeout` never occur at benchmark scale (budgets generous), so
   the honest-degradation path is exercised by unit tests, not by the matrix.

## 9. Provenance

- Reused shared standards: `research_v3.contracts.cards` (typed failures),
  `research_v3.eval.{splitters,leakage,statistics}`,
  `research_v2.contracts.canonical_hash` (all hashes).
- Conceptual port of the tested V2 LN-06 `_min_cost_subset` branch-and-bound
  into C1, rewritten for the joint dwell+travel objective; no code copied.
- New for P02: problems/generator/oracle/proposed-A*/metrics (listed in
  `research_v3/methods/p02/__init__.py`).
