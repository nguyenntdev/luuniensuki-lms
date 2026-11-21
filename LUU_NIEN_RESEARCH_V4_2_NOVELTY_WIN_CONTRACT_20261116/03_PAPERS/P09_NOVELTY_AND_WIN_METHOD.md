# P09 — Evidence-grounded heritage exploration — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM_HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
Wikidata 51 claims, only 6 grounded, 0.118 grounding across all methods; structural guard lowers unsafe surfacing but not expert truth.

## B. Nearest known prior art (claim collision audit)
- **AV2025** — AVerImaTeC (NeurIPS 2025), image-text claims with evidence — https://proceedings.neurips.cc/paper_files/paper/2025/hash/0695cbd1f85f54780e2b351db4252a97-Abstract-Datasets_and_Benchmarks_Track.html
- **COVEGAT** — Bader et al. (2025), CoVeGAT citation-aligned claim verification — https://aclanthology.org/2025.r2lm-1.1/
- **AV2024** — AVeriTeC shared task (2024) — https://aclanthology.org/2024.fever-1.1/
- **FACTSCORE** — FActScore (EMNLP 2023) — https://aclanthology.org/2023.emnlp-main.741/

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Distinguishing truly independent primary historical sources from derivative citation loops with temporal revisions; AVeriTeC and CoVeGAT already cover generic claim verification.

### Required comparator pool (minimum; check new 2026 competitors)
BM25; dense+cross encoder; iterative QA retrieval; AVeriTeC-style fact checker; provenance graph citation verifier; always-abstain; same-retrieval confidence threshold.

### Source requirements / task parity
Legally accessible Hue heritage primary texts with precise page locators and scholarly checks; Wikidata can provide retrieval candidates but not historical gold truth.

### Diagnostic protocol: V3 → baseline champion → common failures
For every unsupported claim, determine missing source, wrong locator, derivative provenance, conflict, ambiguity or retrieved counterevidence; measure independent support availability.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If evidence retrieval appears sufficient but supporting citations derive from the same source lineage or contradict temporal context, a lineage-aware temporally scoped evidence sufficiency test may reduce false support at equal answer coverage.

## E. Candidate mechanism ONLY if D is supported
Retrieve candidate spans; build provenance DAG with source families and revision timestamps; compute independent chain coverage with contradiction edges; NLI + calibrated 3-way SUPPORT/REFUTE/UNRESOLVED; reject evidence cycles.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary expert-judged grounded answer F1 at fixed coverage and fixed maximum false-support, compared to best citation-aware reranker; separate evidence recall from abstention.

**Proof/invariant boundary:** Provenance graph acyclicity and source-family counts are mechanically provable; historical truth not.

**No-win / pivot:** If insufficient licensed Hue text/expert labels, support only structural claim-audit and stop historical truth superiority.

**Ablation/negative controls:** No source-family collapse; no time cutoff; same retriever+NLI; abstain-all; swap references in same family.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p09/
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
