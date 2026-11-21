# P03 — Pedagogically faithful generated AI tutor — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `HIGH`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
Decision-layer score saturates at 1.0 and a C0 comparator also 1.0; real generated tutor turns and human teacher reference absent.

## B. Nearest known prior art (claim collision audit)
- **MATH_TUTOR** — Macina et al. (2025), MathTutorBench, EMNLP — https://aclanthology.org/2025.emnlp-main.11/
- **TUTOR_SURVEY_2026** — What makes an LLM a tutor? A component-centric survey of LLM-based and agentic tutoring systems (2026) — https://link.springer.com/article/10.1007/s44336-026-00047-y

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Evidence-sufficiency versus misconception-targeted scaffolding in multi-turn math dialogue; not generic RAG or another instruction prompt.

### Required comparator pool (minimum; check new 2026 competitors)
Same frozen LLM direct response; Socratic prompt; RAG+citations; plan-then-generate; self-critique; pedagogical reward-model reranker; MathTutorBench published tutors if reproducible.

### Source requirements / task parity
MathTutorBench/MRBench with verified split, licence and generated prompts; new teacher-rated challenge dialogues; no claim on real student learning without consented intervention.

### Diagnostic protocol: V3 → baseline champion → common failures
Score model-generated answers by misconception class, answer leakage, grounding, scaffold appropriateness, ambiguity and teacher disagreement; identify residual failures vs best tutor prompt/reranker.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If hard-case failure stems from missing a verifiable mistake-step state (not just weak prompting), error-localized evidence states with calibrated deferral may reduce unsupported correction while preserving teacher-rated scaffolding.

## E. Candidate mechanism ONLY if D is supported
Represent student work as ordered step graph; retrieve canonical rule citations; generate a bounded next-hint plan using certified error localization; separate decision and natural language generator; expert review fallback for ambiguous state; freeze generator/checkpoint.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Primary: blinded, randomized expert paired preference (pedagogical rubric) for real generated responses, same base LLM/token budget; co-primary answer leakage limit and grounding failure safety; no success from decision-layer accuracy alone.

**Proof/invariant boundary:** A deterministic planning stage can certify no forbidden full-solution tokens in structured plan, NOT that arbitrary generated natural language can never leak answers. Use output audits.

**No-win / pivot:** If human-rated win not present, retain dataset/evaluation contribution; do not report 1.0 decision score as tutoring SOTA.

**Ablation/negative controls:** Plain LLM; RAG; no error-step graph; no citation verifier; reward reranking; swap in irrelevant evidence; long-dialog challenge.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p03/
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
