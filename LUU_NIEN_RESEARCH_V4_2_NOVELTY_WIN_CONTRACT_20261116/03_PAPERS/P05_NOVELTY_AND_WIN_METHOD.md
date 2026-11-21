# P05 — Forgetting-aware knowledge tracing — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `VERY_HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 advantage +0.0088 AUC over one classical C1 on OULAD; no true LefoKT/HawkesKT/simpleKT comparator; course-level OULAD may not be KT supervision.

## B. Nearest known prior art (claim collision audit)
- **LEFOKT** — Bai et al. (2025), Rethinking and Improving Student Learning and Forgetting Processes for Attention based KT — https://ojs.aaai.org/index.php/AAAI/article/view/34998
- **HKT** — Knowledge Tracing: A Survey (ACM) — https://doi.org/10.1145/3569576
- **PYKT** — pyKT: standardized knowledge tracing toolkit — https://github.com/pykt-team/pykt-toolkit
- **SIMPLEKT** — simpleKT: A Simple but Tough-to-beat Baseline for Knowledge Tracing — https://pykt.org/simplekt
- **KT2026** — Beyond AUC: Evaluating Deep Knowledge Tracing Through Temporal Coherence and Post Hoc Explanations (2026) — https://www.mdpi.com/2079-9292/15/21/4975
- **CMDKT2025** — Enhancing knowledge tracing through course map and question difficulty analysis (2025) — https://www.sciencedirect.com/science/article/pii/S259000562500150X
- **KT_LEAK2026** — Enhancing Knowledge Tracing through Leakage-Free and Recency-Aware Embeddings (2026) — https://link.springer.com/article/10.1007/s42979-026-05344-3

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Evidence for cross-concept interference with observation-time uncertainty after controlling skill difficulty and relative forgetting; both LefoKT and HawkesKT directly overlap with simple time decay.

### Required comparator pool (minimum; check new 2026 competitors)
BKT, GBDT with all time-gap features, HawkesKT, DKT-Forget, FoLiBi, AKT, simpleKT, DTransformer, LefoKT, recency-aware KT, question+skill difficulty competitor; matched question/skill labels.

### Source requirements / task parity
Question/skill correctness logs from a rights-cleared KT dataset (ASSISTments or Junyi if licensed). OULAD retained only as separate course-risk task, not decisive KT benchmark.

### Diagnostic protocol: V3 → baseline champion → common failures
Record per-skill time-gap effects, long/short gap, multi-skill overlap, mislabeled interactions, cold start, history length, difficulty; inspect whether LefoKT and HawkesKT retain the same residual gap.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If the strongest time-aware KT baselines misattribute cross-skill interference to forgetting in long-gap sparse histories, a graph-conditioned competing-risk memory model with uncertainty-disentangled observation updates could improve next-question NLL.

## E. Candidate mechanism ONLY if D is supported
Constrain latent skill memory with nonnegative decay hazards plus signed cross-skill interaction effects estimated from TRAIN only; separate observation confidence, question difficulty and memorization state; regularize to reduce to HawkesKT/LefoKT subcases and identify added mechanism by falsifiable ablation.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary preregistered next-question NLL or AUC (choose before TEST); must beat max(dev-ranked C2 candidates) on test on >=2 datasets with Holm-corrected cluster bootstrap and no serious calibration regression; long-gap result supportive unless preregistered primary.

**Proof/invariant boundary:** Constrained hazard construction enforces monotone self-decay under zero practice, not superiority; check identifiability and parameter count.

**No-win / pivot:** If no consistent C2 gap on DEV, end novel KT model track; reframe V3 OULAD as calibrated early warning. Never re-use dev experiments to select one-shot TEST.

**Ablation/negative controls:** LefoKT/HawkesKT; no cross-skill terms; no uncertainty gate; difficulty-only; temporal shuffle; skill-label shuffle; future leakage canaries.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p05/
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
