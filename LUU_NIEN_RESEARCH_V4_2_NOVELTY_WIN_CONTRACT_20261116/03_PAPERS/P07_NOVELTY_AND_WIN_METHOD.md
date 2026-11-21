# P07 — Resource- and rights-aware multimedia selection — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
8 external cases, 17 synthetic; nominal 8/8 vs 4/8 raw p=0.125, Holm 0.75; second provider, B00–B03 and licence checks missing.

## B. Nearest known prior art (claim collision audit)
- **SIGLIP2** — SigLIP 2 multilingual vision-language encoders (2025) — https://arxiv.org/abs/2502.14786

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Independent rights eligibility and evidence completeness across multilingual cultural-media providers under per-session resource constraints, not just retrieval+knapsack.

### Required comparator pool (minimum; check new 2026 competitors)
BM25; multilingual-e5/mBERT; SigLIP2 or CLIP image/text retrieval; cross-encoder rerank; oracle ILP/CP-SAT item selection; constraint-aware re-ranking with same candidates.

### Source requirements / task parity
Smithsonian CC0 verified; additional independent rights-cleared provider (Europeana if key/licences provided) plus manually judged media-query pairs with deduped rights and group disjointness.

### Diagnostic protocol: V3 → baseline champion → common failures
Identify whether failure is retrieval recall, cross-language grounding, rights invalidity, bandwidth cost, or diversity. Report numerator/denominator and provider-disjoint shifts.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If strong multimodal retrieval finds semantically relevant objects but violates rights or claims about inscription/date certainty, a provenance/rights-complete selection closure can improve trusted utility at fixed resource budgets.

## E. Candidate mechanism ONLY if D is supported
Two-stage frozen retriever/reranker + versioned media rights certificate graph + ILP selection requiring every selected media-claim pair have verified licence and support; abstain items with unsupported claims; memoized exact budget feasibility.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary expert-rated rights-valid nDCG@k under matched candidate pool/budget; secondary false-permission rate 0 within defined policy, recall loss, source diversity. Compare to strongest rights-aware reranker/ILP.

**Proof/invariant boundary:** All output items satisfy registered rights constraints if rights metadata is correct; cannot prove actual legal permissions or semantic accuracy from hashes.

**No-win / pivot:** If strong baseline does rights filtering equally well or media labels insufficient, contribute interoperable audit benchmark, not novel optimization SOTA.

**Ablation/negative controls:** Same retriever no rights closure; ILP without provenance; strong retrieval with filter; second-provider holdout; corrupted rights metadata.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p07/
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
