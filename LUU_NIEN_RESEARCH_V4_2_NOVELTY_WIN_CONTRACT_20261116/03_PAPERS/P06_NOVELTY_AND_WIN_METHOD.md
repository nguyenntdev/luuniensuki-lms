# P06 — Fair budget-limited teacher prioritization — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 tied C1 on 6 contrasts; fairness constraint never bound; no observed teacher treatment effect.

## B. Nearest known prior art (claim collision audit)
- **FAIR2024** — Verma et al. (2024), Group Fairness in Predict-Then-Optimize Settings for Restless Bandits, UAI — https://proceedings.mlr.press/v244/verma24a.html

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
An externally observed nontrivial fairness–utility tradeoff under binding capacity constraints, not contrived allocation where a constraint never activates.

### Required comparator pool (minimum; check new 2026 competitors)
Risk top-K; quota-constrained top-K; greedy knapsack; calibrate-then-allocate; robust fairness allocation; fair predict-then-optimize with matched action/counterfactual requirements.

### Source requirements / task parity
Public early-warning outcome dataset for retrospective selection only; logged teacher interventions and propensities for any counterfactual value claim. Groups defined ethically and pre-registered.

### Diagnostic protocol: V3 → baseline champion → common failures
Quantify naturally observed capacity K and group disparities; measure fraction of cases fairness actually binds; report total utility and worst-group recall; avoid invented treatment gains.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If genuine uncertainty and drift cause unconstrained top-K to repeatedly underserve a pre-specified group, distributionally robust allocation with verified feasible group minima may reduce worst-group error at bounded total-utility cost.

## E. Candidate mechanism ONLY if D is supported
Joint confidence intervals for group-specific risks, discrete robust min–max selection under exactly-K capacity; optional doubly robust OPE only if logged actions and positivity support assumptions; formal feasibility/fairness certificates.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary worst-group recall/utility at equal K and equal permitted protected attributes, plus strict cap on total utility loss. Winner needs meaningful binding fairness constraint on held-out natural cohorts; no RCT/no causal effect claims.

**Proof/invariant boundary:** Exact group minimum quotas and capacity constraints can be certified when feasible; uplift cannot be proven without causal identification.

**No-win / pivot:** If no natural disparity/constraint activation, stop superiority claim, report negative observational allocation audit.

**Ablation/negative controls:** Same risk model + quota; calibrated score threshold; group DRO; random selection; inactive fairness sham; no uncertainty.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p06/
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
