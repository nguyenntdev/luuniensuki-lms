# P14 — Heritage learning-object accessibility — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM_HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 13 synthetic objects, automated criteria count but no user outcomes or realistic licensed media.

## B. Nearest known prior art (claim collision audit)
- **WCAG2024** — W3C WCAG 2.2 Recommendation — https://www.w3.org/TR/wcag/
- **CAST2024** — CAST Universal Design for Learning Guidelines 3.0 — https://udlguidelines.cast.org/more/about-guidelines-3-0/
- **GENA11Y2025** — Enhancing Web Accessibility: Automated Detection of Issues with Generative AI (FSE 2025) — https://seal.ics.uci.edu/publications/2025_FSE_GenA11y.pdf
- **A11Y2026** — An empirical investigation of Large Language Models for automated software compliance testing (2026) — https://doi.org/10.1016/j.infsof.2026.108215

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Historical-media semantic alt-text appropriateness and source-grounded accessibility testing distinct from general WCAG source-code audits.

### Required comparator pool (minimum; check new 2026 competitors)
axe-core; Pa11y; Lighthouse; published LLM accessibility auditor; human WCAG/UDL expert; image captioner with and without source.

### Source requirements / task parity
Licensed historic learning objects with images, inscriptions, audio, captions and browser accessibility tree; human expert labels; assistive-technology participants if studying usability.

### Diagnostic protocol: V3 → baseline champion → common failures
Separate semantic alt-text hallucination, missing transcript, contrast/DOM issues, wrong chronology, rights metadata and actual task success; compare error overlap for tools.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If WCAG tools detect markup violations but cannot verify semantic appropriateness of historical alt-text and source claims, a provenance-grounded multimodal auditor with explicit abstention may reduce false accessible passes.

## E. Candidate mechanism ONLY if D is supported
Combine WCAG rule engine + multimodal reference retrieval + historical citation-span verification + 3-way criterion decision (PASS/FAIL/REVIEW), human approval for semantic alt text; never equate automated rule verdict to overall UDL.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary expert-judged critical semantic-accessibility recall at same false-alarm burden versus axe/Pa11y+strong LLM baseline; secondary user task completion only if human study done.

**Proof/invariant boundary:** Rule coverage and provenance presence can be certified, not UDL or accessibility for actual people.

**No-win / pivot:** Without actual human-labelled media, limit to conformance checker report and do not claim better learning accessibility.

**Ablation/negative controls:** axe alone; LLM alone; same LLM with source; remove provenance; modality holdout; rights-conflict negative control.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p14/
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
