# P08 — Reward-integrity gamification — research design / novelty / win protocol (V4.2)

**Status:** `DESIGN_ONLY` / `NOVELTY_NOT_PROVEN` / `WIN_NOT_OBSERVED`. **Nearest-work overlap risk:** `MEDIUM`. **Audit source:** V3 release at `4e5a792...` with repo follow-up `331c581...`.

## A. Proven failure of V3 (observed, not causal attribution)
V3 shows mechanism contrast on synthetic attack fixtures, no authentic attack prevalence, no external independent attack authors.

## B. Nearest known prior art (claim collision audit)
- **AWS_IDEMPOTENCY** — AWS Well Architected, Make mutating operations idempotent — https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_prevent_interaction_failure_idempotent.html

**Collision warning:** V4.1 generic proposal is NOT novel solely because it combines these known components. Require a literature contrast table with: assumptions, data, target, mechanism, proof, code, licence, failure strata, evaluation. New method permission gate must be signed by a human research lead after C1/C2 replications.

## C. Residual gap to VERIFY before designing model
Formal invariants of distributed, multi-service replay/reordering and independently authored attacks under constrained transaction performance, beyond standard API idempotency.

### Required comparator pool (minimum; check new 2026 competitors)
Unique constraint + idempotency key; transactional event ledger; optimistic CAS; replay-protected outbox/inbox; exactly-once-if-possible under crashes; standard policy-based anti-abuse.

### Source requirements / task parity
Non-production anonymized event traces with permissions; independent red-team generator; immutable synthetic boundary tests only for safety regression, not incident prevalence.

### Diagnostic protocol: V3 → baseline champion → common failures
Identify concrete distributed attack vectors not handled by strong ledger/CAS baselines: cross-session, reordering, outbox retry, clock skew, privilege races.

**Threshold to proceed:** archive matched per-case predictions for C1 and published/comparable C2, label disagreement by actual error slice; show a positive DEV residual error rate for the **strongest** comparator. Missing labels/rights or absence of residual gap => no algorithm design.

## D. Falsifiable hypothesis derived from failure — NOT novelty claim
If realistic duplicated redemption arises from causal misordering across services despite idempotency keys, versioned causal receipts and atomic entitlement state can prevent false awards without disproportionate latency.

## E. Candidate mechanism ONLY if D is supported
Causal sequence receipt H(event identity, actor, benefit, epoch, entitlement state); transactionally enforce monotone award state and revoked/reissued keys; crash-safe replay tests; model-check finite transition systems.

### Modeling/spec acceptance before training
1. Write typed input/output interfaces with timestamps, allowed features, unit of randomization, oracle restriction and missing data semantics.
2. Derive exact optimization loss or probability model, complexity estimate and scope of assumptions.
3. Show **why** nearest prior art cannot represent the same mechanism without modification, with an explicit counterexample; else classify `SAME_AS_PRIOR` and stop.
4. Implement from scratch or licensed upstream, pin commits, container/image digests and dataset/right hashes. Protect TRAIN/DEV/TEST split; no gold in inference payload.
5. Run same backbone and compute budget for ablations; keep every null, instability and cost result.

## F. Explicit win contract (preregister; no guarantee)
Formal primary: zero double-award/unauthorized-award on a stated, independently reviewed threat model (all algorithms tested); quantitative secondary: throughput/p99 and false-reject vs strongest ledger baseline. A proof is a correctness claim, not statistical model win.

**Proof/invariant boundary:** State invariants under atomicity/cryptographic assumptions; model-check all bounded interleavings; explicit unmodeled assumptions (network partitions, Byzantine actors).

**No-win / pivot:** If ledger baseline already meets invariants at equal/better latency, release attack testbed and engineering best practices; no originality claim for mere idempotency.

**Ablation/negative controls:** Standard idempotency ledger; no causal epoch; no revocation; single-service only; unseen red-team attack generator.

## G. Execution gates / artifact receipts
```
research_v4_2/papers/p08/
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
