# P10 — Spiral curriculum plan under evidence constraints — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM_HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 162 AI-generated objects, 27/30 anchors unreviewed; no expert teacher evidence.

## B. Nearest known prior art (claim collision audit)
- **HISTORY2025** — Regrounding Inquiry-Based Learning in History (2025) — https://www.tandfonline.com/doi/full/10.1080/07370008.2025.2503193

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Minimum-correction teacher-review planning with verified anchor provenance, rather than generating routes on invented curriculum mappings.

### Required comparator pool (minimum; check new 2026 competitors)
Teacher-authored curriculum sequences; plain topological sort; shortest valid path; curriculum prerequisite planner; human-in-loop greedy edits.

### Source requirements / task parity
Teacher-verified GDPT 2018 content mapping, dated anchors and versioned source pointers; blinded teachers grade/repair plans; consented institutional review.

### Diagnostic protocol: V3 → baseline champion → common failures
Compare errors in grade progression, historical evidence use, prerequisite omissions and total teacher correction time across real tasks.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If verification burden concentrates on low-confidence anchors, a proof-carrying planner that minimizes expected teacher corrections and explicitly defers unverifiable anchors can reduce rework.

## E. Candidate mechanism ONLY if D is supported
Versioned curriculum DAG, expert confidence interval on edges, lexicographic objective (hard validity, source evidence, edits, review cost); provide minimal edit explanation and provenance receipt for each path.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary blind teacher correction time or number of correction actions under noninferior validity, compared to teacher-authored and exact DAG baselines; both graders blinded.

**Proof/invariant boundary:** DAG acyclicity, grade ordering, hard evidence guard can be proven within encoded ontology; quality requires teachers.

**No-win / pivot:** If teacher reviewers do not agree or no approved anchors, stay BLOCKED; no synthetic student outcome claim.

**Ablation/negative controls:** No anchor confidence; teacher correction after generation; plain path; remove provenance; random expert tasks.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p10/
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
