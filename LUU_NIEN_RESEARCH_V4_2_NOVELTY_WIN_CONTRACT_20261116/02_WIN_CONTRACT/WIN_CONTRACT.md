# Win Contract — strict rules

## 1. Scope and baseline champion
Let `S = (task, label, horizon, cohort, dataset_version, split, features, action_space, constraints, compute_budget, metric)` be pre-specified. Every baseline must match `S` (or be explicitly labeled ineligible). Select `B*` as **strongest eligible** from *all pre-registered C1/C2 comparator families* using a DEV set, never held-out test.

## 2. Objective and success
Orient primary metric so larger is better: `Δ = M(candidate) - M(B*)` on exactly the same sealed instances. Success is declared only when:
1. `NOVELTY_GATE=PASS` and `DATA_RIGHTS_GATE=PASS`; the nearest existing method is included as eligible strong comparator.
2. `Δ >= δ` where δ is a **predefined meaningful minimum difference** based on the task, power and stakeholder requirement, not chosen after seeing results.
3. 95% cluster-resampled CI lower bound for Δ > 0 AND pre-registered familywise correction (Holm or hierarchical correction) passes α=0.05, with explicit analysis of dependence and sample size. Correct method for metric (e.g. paired bootstrap for AUC, randomization/permutation for human preference, cluster bootstrap for sessions); do not mechanically apply McNemar to continuous metrics.
4. All required feasibility/safety/coverage/p99 resource guards hold on the same test set; stronger baseline has not been excluded based on its score.
5. The same directional effect is verified on an **independent dataset, held-out provider, new cohort or separately gathered future study** where scientifically feasible. If this is unavailable, label `SINGLE_DATASET_WIN` not robust/generalized win.
6. Human-only outcomes have actual ethical approval and blinded human raters; synthetic labels cannot establish validity.

A single test failure triggers a pre-registered **no-win decision**. Multiple candidate models/families may be searched ONLY on train+dev with logged budget (example: 3 *families* × 20 configs, independently budget-matched baselines). Rerunning on same sealed test after revising architecture is leakage, never a new confirmatory result. A new pre-registered, genuinely independent study is needed.

## 3. Can a win be guaranteed by design? Very narrowly, yes
- **P02 (known deterministic objective):** if two algorithms output feasible routes and a trusted checker independently computes their objective under the same constraints, a *portfolio wrapper that selects the better checked solution* guarantees quality no worse than either constituent on those inputs. If an exact optimality certificate is required, return only a certified optimum, with an exact solver fallback. This guarantees objective validity/optimality under assumptions, **not** faster runtime or a strict improvement; parallel/serial comparison adds compute and is not automatically novel.
- **P08 (formal safety):** under a precise transaction/state model, prove that every permitted transition preserves no-double-award and authorization invariants. This guarantees safety within assumptions, but does not establish unique research contribution if standard idempotent ledgers are equally safe.
- **P06 (known surrogate objective):** comparing two feasible allocations and selecting the better value of an *observed deterministic optimization surrogate* guarantees non-regression on that surrogate only. It **cannot guarantee teacher intervention benefit** if utility depends on unobserved counterfactual outcomes.
- **P07/P09/P12/P14 (metadata/chain guard):** formal rights-card/locator/hash invariants can hold under recorded metadata validity, but neither actual item permission, historical truth, semantic image relevance nor human accessibility is mathematically guaranteed by a hash.
- **P01/P03/P05/P11/P13:** no inference, human judgement, AUROC/NLL/α or cross-domain win can be guaranteed before genuinely independent evaluation.
- A pure exact-solver portfolio wrapper, copy of a baseline, or hardcoded easier benchmark is **NOT** a novel algorithm paper. The novelty gate remains separate.

## 4. Win types — never conflate
- `FORMALLY_PROVEN`: property of algorithm for specified inputs/assumptions (e.g. constraint validity; sound exact reuse; non-duplication of rewards, hash chain tampering). Does NOT imply faster runtime or better learner outcomes.
- `PREDICTIVE_SUPERIORITY`: predeclared predictive metric against strongest task-fit baseline with uncertainty; impossible to promise before seeing test.
- `BETTER_SAFETY_EFFICIENCY_FRONTIER`: same safety constraint, improvement in predeclared latency/cost or the reverse with same primary performance; all tradeoffs reportable.
- `BETTER_INSTRUMENT_OR_BENCHMARK`: human-validated measurement/reliability, controlled false-discovery and reproducibility; NOT a neural win.
- `NULL_OR_INFERIOR`: publish, pivot to new scientific question or merge with another paper; not relabelled victory.

## 5. Win probability / power planning
Provide a power calculation using dev-estimated effect, n_eff at the proper clustered unit, Holm alpha, dependency-adjusted variance and pre-specified δ before sealing. DEV evidence is conditional and biased upward under model selection; plan pessimistically and use hold-out validation. Small n=8 media cases cannot support a stable statistically significant generalizable claim.

## 6. Explicit leakage and gaming bans
No: easy baselines, cherry-picked subgroup/post hoc benchmark, changing n/denominator or coverage after results, omitting strongest relevant comparator, treating CI green with failed pytest as passing, published-number comparison, manufactured ground truth, using test labels for tuning, repeated test peeking, conflating technical certificates with scientific effects, inventing ethics approval. Any violation => `INVALID_WIN`.

## 7. Release schema
`claim_id, paper_id, claim_type, estimand, primary_metric, delta_min, baseline_champion_id, baseline_candidates_all, excluded_with_reasons, prereg_sha256, train_dev_test_hashes, model_sha256, dataset_rights, effect, ci95, p_raw, p_adjusted, constraint_pass, n_clusters, independent_replication, negative_controls, human_approval, claim_status`.
Status enum: `BLOCKED`, `BASELINE_INCOMPLETE`, `NO_RESIDUAL_GAP`, `NOVELTY_FAILED`, `DEVELOPMENT_CANDIDATE`, `FROZEN`, `TESTED_NULL`, `TESTED_WIN_SINGLE`, `REPLICATED_WIN`, `FORMAL_PROPERTY_PROVED`, `SUBMISSION_READY`.
