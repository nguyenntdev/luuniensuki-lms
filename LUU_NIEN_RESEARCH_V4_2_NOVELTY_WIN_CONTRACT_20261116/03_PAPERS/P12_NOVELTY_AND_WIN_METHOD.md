# P12 — Page-verifiable archival claim ledger — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `HIGH_OVERLAP`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
62/63 ABSTAIN, only hash-chain integrity verified; no real primary archive truth adjudication. Significant scope overlap with P09.

## B. Nearest known prior art (claim collision audit)
- **AV2025** — AVerImaTeC (NeurIPS 2025), image-text claims with evidence — https://proceedings.neurips.cc/paper_files/paper/2025/hash/0695cbd1f85f54780e2b351db4252a97-Abstract-Datasets_and_Benchmarks_Track.html
- **COVEGAT** — Bader et al. (2025), CoVeGAT citation-aligned claim verification — https://aclanthology.org/2025.r2lm-1.1/
- **AV2024** — AVeriTeC shared task (2024) — https://aclanthology.org/2024.fever-1.1/

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Locator-level verification of archival text versions and chain-of-custody under source corrections; must be orthogonal to P09’s evidence retrieval.

### Required comparator pool (minimum; check new 2026 competitors)
Exact locator match; OCR/snippet retrieval+NLI; page-level source verifier; manual archivist adjudication; generic provenance chain.

### Source requirements / task parity
Digitized archive page images or permitted transcripts with explicit page edition/version/rights, independent historian verification. Do not auto-extract rights-restricted text.

### Diagnostic protocol: V3 → baseline champion → common failures
Separate unsupported due to unavailable primary page, genuine contradiction, broken OCR, wrong edition, or incorrect model inference; focus at page-locator level.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If wrong historical assertions mostly result from edition/locator mismatches rather than retrieval rank, a version-specific page proof and contradiction ledger may improve verified-claim coverage without raising false support.

## E. Candidate mechanism ONLY if D is supported
Each claim references archive document ID, edition, page, literal span digest, rights card and provenance path; three-way adjudication merges human decision and cryptographic chain. No model declares true solely from matching hash.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary expert-adjudicated locator-correct support recall at fixed false-support limit, compared to exact-span/NLI; secondary tamper detection (formal/engineering).

**Proof/invariant boundary:** Hash-chain tamper detection assuming collision resistance is provable; factual correctness not.

**No-win / pivot:** If P09 shares same primary estimand and data, MERGE P12 into P09 technical appendix rather than duplicating publication.

**Ablation/negative controls:** No versioning; no page locator; no human signoff; generic retrieval; revise source version after snapshot.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p12/
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
