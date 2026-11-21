# P02 — Exact constrained path planning — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
Both V3 proposed and B&B solve 100% exactly; proposed p95 1.228ms, B&B 0.451ms on 1,620 toy instances. Quality is at ceiling.

## B. Nearest known prior art (claim collision audit)
- **OR_TOOLS** — Google OR-Tools CP-SAT official documentation — https://developers.google.com/optimization/cp/cp_solver

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Repeated right-cleared heritage itinerary replanning with changes in crowd, opening windows, accessibility and evidence eligibility; no prior evidence this remains a speed gap vs existing exact solvers.

### Required comparator pool (minimum; check new 2026 competitors)
Existing B&B; OR-Tools CP-SAT; MILP (CBC/HiGHS); dynamic programming on small bounded instances; standard caching, lazy constraints and tuned primal heuristics.

### Source requirements / task parity
Rights-cleared POI/route snapshots with real travel costs and valid prerequisite constraints; real changes/events captured before test; separate larger synthetic scaling benchmarks are supportive only.

### Diagnostic protocol: V3 → baseline champion → common failures
Locate per-instance runtime tail by graph density, constraint type, change frequency; compare solver setup overhead; add ground-truth opt certificates; identify real instance size where reoptimization dominates.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If the exact solver repeatedly recomputes identical invariant subproblems after small updates, versioned constraint-aware incremental certificates can avoid redundant search without changing feasibility or optimality.

## E. Candidate mechanism ONLY if D is supported
Hash a normalized constraint graph and source/right versions; reuse only certified exact subproblem bounds whose dependency sets do not overlap the update; invalidate all affected nodes transitively; fallback to exact B&B/CP-SAT; learned ordering optional as heuristic only.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary: paired p95 end-to-end latency and geometric mean runtime vs fastest eligible exact solver on preregistered dynamic instances; zero invalid routes, zero wrong infeasible claims and proven optimal solutions.

**Proof/invariant boundary:** Sound reuse theorem: if a memoized certificate depends only on unchanged constraint/weight nodes and solver bound conditions, its validity persists; invalidation proof and property-based test. Runtime speedup remains empirical, never mathematically guaranteed for every instance.

**No-win / pivot:** If real end-to-end p95 is slower, publish reproducible dynamic-replanning benchmark/invalidation proof or drop speedup claim.

**Ablation/negative controls:** No memoization; naive global cache; CP-SAT hint; precompile static graph; whole-graph invalidation; adversarial update each edge.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p02/
  00_v3_case_reproduction.json             # source SHA, per-case inputs, label hashes
  01_prior_art_screen.csv                   # 2015-2026 verified title/DOI/assumptions
  02_baseline_champion_manifest.json        # all eligible candidates, strongest DEV B*
  03_residual_failures.jsonl                # case ids, strata, cross-model error overlap
  04_novelty_counterexample.md              # what closest prior method cannot do
  05_method_theory_and_complexity.md        # assumptions + formal spec
  06_dev_trials_append_only.jsonl           # every model family/seed/config, failures
  07_ablation_and_canary_results.json
  08_preregistration.lock.yaml              # signed before TEST; metric and δ frozen
  09_confirmatory_receipt.json              # ONE sealed TEST execution
  10_replication_receipt.json               # independent cohort/provider if applicable
  11_claim_clearance.json                   # rights, human novelty/ethics/venue signoffs
```

## H. Mandatory terminal decision
`FORMAL_PROPERTY_PROVED | REPLICATED_WIN | TESTED_WIN_SINGLE | TESTED_NULL | NO_RESIDUAL_GAP | NOVELTY_FAILED | BLOCKED_DATA | BLOCKED_HUMAN | MERGED`. Never automatically `SUBMISSION_READY` from a technical score.
