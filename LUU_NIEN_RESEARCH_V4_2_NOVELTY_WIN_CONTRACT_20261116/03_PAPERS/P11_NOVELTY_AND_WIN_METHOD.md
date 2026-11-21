# P11 — Reliability-aware historical reasoning rubric — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
No human raters, synthetic toy reliability cannot establish rubric gains.

## B. Nearest known prior art (claim collision audit)
- **HISTORY2025** — Regrounding Inquiry-Based Learning in History (2025) — https://www.tandfonline.com/doi/full/10.1080/07370008.2025.2503193

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Source-chain-specific score categories and disagreement-guided adjudication for historical argumentation in Vietnamese heritage tasks; many established sourcing rubrics exist.

### Required comparator pool (minimum; check new 2026 competitors)
Holistic teacher grade; standard sourcing/contextualization/corroboration analytic rubric; criterion-level published historical argument rubric with rights; adjudication random sampling.

### Source requirements / task parity
Real students’ consenting anonymized historical responses and >=3 trained independent scorers; stratify argument length, citation quality and language; separate held-out cohort.

### Diagnostic protocol: V3 → baseline champion → common failures
Estimate rater disagreements by facet (authenticity, temporal placement, corroboration, counterevidence) and time-to-grade, blind gold; check validity beyond raw agreement.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If existing holistic/analytic rubrics conflate evidence presence with reasoning quality and misalign raters, evidence-path decision anchors plus uncertainty-triggered adjudication can improve agreement at constant scoring time.

## E. Candidate mechanism ONLY if D is supported
Hierarchical scoring facets with decision anchors and evidence span pointers; rater-independent scoring then active arbitration of low-agreement facets; no post-hoc regrading same confirmation set.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary Krippendorff α (or appropriate weighted κ) gain above predeclared practical margin on held-out real responses AND no construct validity/time penalty; cluster bootstrap by response/rater.

**Proof/invariant boundary:** A deterministic rubric schema can be complete/monotone by design, but inter-rater α cannot be guaranteed.

**No-win / pivot:** No raters => BLOCKED; if existing rubric same reliability, publish adaptation/validation not new scoring method.

**Ablation/negative controls:** Holistic; published analytic; unanchored new rubric; naive adjudication; alternative training length equalized.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p11/
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
