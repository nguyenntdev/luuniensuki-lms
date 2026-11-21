# P13 — Early-warning from clickstream (SRL claims gated) — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `VERY_HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 SRL-proxy model UNDERPERFORMS click-count (ΔAUC -0.008 group, -0.019 time), no validated measured SRL construct.

## B. Nearest known prior art (claim collision audit)
- **SRL2025** — Boulahmel et al. (2025), Investigating Self-Regulated Learning Measurement Based on Trace Data — https://doi.org/10.1007/s10758-025-09816-y
- **SRLREVIEW2025** — Nath et al. (2025), Balancing Contextualization and Generalization in Trace-based Measurement of SRL — https://doi.org/10.3102/00346543251382238
- **SRLRUBRIC** — De Barba et al. (2025), Development and validation of a learning analytics rubric for SRL — https://link.springer.com/article/10.1007/s11423-025-10521-x

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Early warning risk under naturally irregular course schedule and measurement effort, beyond generic time-series encoder; no SRL construct claims without real instrument.

### Required comparator pool (minimum; check new 2026 competitors)
Click-count LR; XGBoost/LightGBM with time-window; calibrated discrete-time hazard survival; GRU/TCN; transformer/state-space on identical event streams; proper SRL questionnaire baseline if real labels.

### Source requirements / task parity
OULAD time windows with strict future cutoff; second rights-cleared learning events data; actual SRL questionnaire only under consent (separate endpoint).

### Diagnostic protocol: V3 → baseline champion → common failures
Split errors by cadence and missing activity, term, module, last active day and censoring; compare time-window GBDT and survival models; check label leakage.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If event observations are informative missingness and standard time-window baselines misread schedule-induced silence as dropout, a schedule-normalized observation process can improve calibrated early-warning risk under term shift.

## E. Candidate mechanism ONLY if D is supported
Joint event/observation model: course schedule prior + sparse learner event-time hazard with separate exposure mask; conditional hazard on observed opportunity; nested lightweight calibrator; reduce to click-only baseline if absence of schedule effect.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary AUROC or NLL at a fixed prediction horizon vs strongest time-window GBDT and temporal baseline, second cohort replication; worst-term stability and ECE noninferiority. Calling it measured SRL requires a completely separate instrument study.

**Proof/invariant boundary:** No-future-events feature cutoff is mechanically enforceable; no predictive win guarantee.

**No-win / pivot:** If stronger temporal model never beats click/GBDT, redesign as negative-result early-warning study; do not mislabel it SRL.

**Ablation/negative controls:** Click-only; schedule-normalized simple LR; no observation mask; no schedule; no time-conditioning; future-click leakage canary.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p13/
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
