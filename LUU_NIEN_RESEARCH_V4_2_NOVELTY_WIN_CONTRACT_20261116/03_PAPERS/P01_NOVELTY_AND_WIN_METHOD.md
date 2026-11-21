# P01 — Selective learner-risk transfer — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
Unfair comparison of prediction accuracy at 36.2% coverage; V3 base predictor 0.2091 vs logistic 0.5536 across unmatched denominators; inferential root cause unknown.

## B. Nearest known prior art (claim collision audit)
- **CRC2026** — Kwon & Kim (2026), Conformal selective prediction with cost aware deferral for safe clinical triage under distribution shift — https://www.nature.com/articles/s41598-026-40637-w
- **WILDS** — WILDS: A Benchmark of in-the-Wild Distribution Shifts (ICML 2021) — https://proceedings.mlr.press/v139/koh21a.html

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Constrained human-review capacity combined with worst-course selective risk under natural term shift, AFTER matching base predictor and matched-coverage policies.

### Required comparator pool (minimum; check new 2026 competitors)
Full-coverage calibrated LR; CatBoost; LightGBM; same-backbone uncertainty threshold; split conformal; Mondrian/weighted conformal; learned-to-defer if teacher costs are known.

### Source requirements / task parity
OULAD course/presentation and student-disjoint splits for early-warning outcome; additional task-compatible learner cohorts for temporal OOD; no DKT comparisons on course-level labels.

### Diagnostic protocol: V3 → baseline champion → common failures
At fixed predictor and coverage {0.4,0.6,0.8}, decompose error by course, presentation, missingness, group and uncertainty; compare full coverage AUROC and risk-coverage; inspect all V3 missed cases.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If conventional selective methods violate a pre-registered worst-course risk bound when review capacity is saturated under term shift, a capacity-coupled robust risk controller with bounded density-ratio uncertainty could improve worst-course selective risk.

## E. Candidate mechanism ONLY if D is supported
Calibrated shared backbone f(x); out-of-fold error model e(x,g); constrained assignment min Σw_i e_i a_i + λ max_g R_g with Σa_i≥K; uncertainty set for density ratios; threshold chosen solely on CAL; no guarantee under arbitrary shift.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary: worst-course selective error or AURC at pre-fixed equal coverage and review budget; bound on group coverage, total risk non-inferiority and ID performance; Holm-corrected paired CI.

**Proof/invariant boundary:** Finite-sample capacity is exact by deterministic sorted selection; only conditional statistical guarantees under stated exchangeability/bounded shift assumptions.

**No-win / pivot:** If no genuine worst-course discrepancy remains, report base model / allocation audit; no new algorithm paper.

**Ablation/negative controls:** Equal f(x) with best conformal policy; random defer; no robustness; no capacity constraint; shift-placebo; random course labels.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p01/
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
