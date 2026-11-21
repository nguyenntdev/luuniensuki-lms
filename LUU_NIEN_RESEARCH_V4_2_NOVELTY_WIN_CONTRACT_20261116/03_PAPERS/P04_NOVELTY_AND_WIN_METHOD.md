# P04 — Curriculum-shift benchmark — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 found shift degradation, but task invariance, comparable KT C2 baselines and true removal ablations still unverified.

## B. Nearest known prior art (claim collision audit)
- **WILDS** — WILDS: A Benchmark of in-the-Wild Distribution Shifts (ICML 2021) — https://proceedings.mlr.press/v139/koh21a.html
- **KT2026** — Beyond AUC: Evaluating Deep Knowledge Tracing Through Temporal Coherence and Post Hoc Explanations (2026) — https://www.mdpi.com/2079-9292/15/21/4975

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Verified grade/curriculum ontology shifts with fixed prediction semantics and documented provenance, not a generic synthetic OOD corruption pipeline.

### Required comparator pool (minimum; check new 2026 competitors)
ERM LR and GBDT; CORAL/DANN/group DRO where task-matched; pyKT baselines on genuine KT event data only; generic corrupted-input benchmarks.

### Source requirements / task parity
OULAD/UCI in matching early-warning tasks; real curricula mapped across grade/presentation; external educational outcomes with rights. Never merge labels across incompatible tasks.

### Diagnostic protocol: V3 → baseline champion → common failures
Define what stays invariant and what shifts: curricular tag, content version, presentation, course; multiple annotators validate label fidelity and construct soundness.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If rule-checked curriculum mapping induces genuine predictor rank reversals that random feature corruption misses, a provenance-labeled benchmark can reveal a new robustness failure mode.

## E. Candidate mechanism ONLY if D is supported
A benchmark protocol: versioned curriculum ontology + real mapping edges + shift operation certificates + label-preservation verifier; provide exact split, baselines and human spot checks. Optional detector is a separate paper only if independent.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary: benchmark discrimination: fraction of independently validated real failure strata recovered at pre-specified false-discovery limit versus strong generic OOD audit; rank reproducibility, not model AUC.

**Proof/invariant boundary:** Deterministic checks enforce schema, ownership of mappings, no label mutation and group separation; ecological validity requires human validation.

**No-win / pivot:** If all shift strata are artificial or models rank identically, release negative benchmark report, not a novel robustness claim.

**Ablation/negative controls:** Random corruption; unverified ontology shuffle; trivial course split; no mappings; annotator consistency.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p04/
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
