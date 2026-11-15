# P08 — Active-Adversary Reward Integrity: Attack-Detection Defenses for Evidence-Gated Mastery Badges

**MANUSCRIPT SKELETON — v0.1 (2026-11-15). Written by the P08 code agent; per
the ownership protocol, novelty certification (P08-T20) and submission
signoff (P08-T21) remain with the human research lead and are BLOCKED.**

---

## Framing (binding)

- **Venue class:** software security / integrity of educational reward
  systems (e.g., an engineering track or a security venue). *Not* a
  design-science or user-study paper: DiGRA-style human RQs (trust,
  engagement, motivation) are **out of scope and unsupported** — no
  participants, no IRB, no data. P08-T19 (ethics/human approval) is BLOCKED.
- **Evaluation class:** SOFTWARE SECURITY EVALUATION
  (`research_v3/experiments/p08/pre_registration.yaml`).
- **Zero human-outcome claims.** This paper must never state or imply that
  gamification, badges, or any defense improves motivation, engagement,
  trust, completion, or learning. The words "engagement", "trust", and
  "motivation" appear only as *unmeasured constructs from the original spec*,
  explicitly marked unmeasured.

## 1. Introduction (bullets)

- Educational platforms increasingly gate rewards (badges, XP) on evidence
  of mastery. The correctness of such gating under *honest* delivery has a
  predecessor result in this project: LN-05, a five-gate policy with a
  single-batch content-derived replay ledger, verified on 120 synthetic
  policy cases [LN-05, `research_artifacts/LN-05/`].
- LN-05's boundary is honest delivery: one evaluation batch, no adversary
  control of the transport channel. We measure what happens at that boundary
  (Section 3) and defend it (Section 4).
- Contribution: a frozen, deterministic attack suite (6 vectors x 500
  deliveries + 2 stress strata + 1000 honest controls) and a defender
  combining HMAC-SHA256 reward attestation, persistent cross-session
  idempotency, velocity control, and server-side evidence re-verification.

## 2. Related work (to be completed by research lead)

- Reward-attack and gamification-abuse literature: [PLACEHOLDER — research
  lead to fill; agent must not certify novelty]. Candidate themes: point
  manipulation attacks in gamified systems, idempotency in payment-like
  ledgers, API replay defenses (nonce/timestamp windows), attestation
  (TPM-style signed claims), velocity/rate limiting (RFC-backed practice).
- LN-05 [internal predecessor] — cited as the single-batch policy-correctness
  result whose invariant concept (identity = content minus transport) P08
  reuses and extends to a persistent epoch.

## 3. Threat model and measured LN-05 boundary (evidence: PROBES.md)

Adversary: controls the delivery channel to the reward endpoint; can replay
captured deliveries, rotate transport identifiers, forge evidence and the
`actor` string, restart sessions, change devices, and burst-submit. The
adversary cannot compute the server HMAC key.

Measured single-batch LN-05 behavior under this adversary (2026-11-15,
HEAD 4e5a792):

| Attack | LN-05 result |
|---|---|
| 100x duplicate, same batch | 1 award, 99 rejected (correct) |
| Timestamp/event_id mutation, same batch | rejected (correct) |
| Cross-session replay (fresh batch) | **granted (vulnerable)** |
| Forged `actor="server"` + forged evidence | **granted (vulnerable)** |
| Fast-click farming (30 distinct) | **30/30 granted (vulnerable)** |

Interpretation constraint: LN-05 never claimed the vulnerable rows. The
contribution of P08 is the *defense* of those rows, not a criticism of LN-05.

## 4. Method (METHOD.md is the frozen spec)

Defender stack, gate order (first trigger decides):
1. policy freshness -> reject_stale_policy
2. HMAC attestation of the semantic payload -> reject_forged_attestation
3. velocity window (5 / 60 virtual seconds per learner) -> reject_velocity
4. server-side evidence re-verification -> reject_invalid_evidence
5. persistent identity ledger (content-derived, transport-stripped)
   -> reject_replay (+cross_session_replay reason)
6. award (bounded by XP cap 150)

No learned parameters. Deterministic; no RNG, no wall clock. Complexity O(n)
over the delivery stream; memory O(consumed identities + velocity windows).

## 5. Evaluation (frozen, seed 20261115)

Protocol: pre-registered in `pre_registration.yaml` BEFORE the campaign.
Results: `research_artifacts_v3/runs/p08/evaluation_results.json`
(checksum-pinned in `evaluation_manifest.json`).

Primary table (one run, exact counts):

| Metric | Result | Frozen gate |
|---|---|---|
| False-award rate (3000 adversarial) | 0.0 | == 0 |
| Duplicate-award count | 0 | == 0 |
| Pooled attack-detection recall | 1.0 | >= 0.999 |
| Per-vector recall (6 vectors) | 1.0 each | >= 0.999 each |
| Honest false rejections (1000) | 0 | <= 1 |
| 100x idempotency | exactly 1 award | == 1 |
| 30-burst farming | 5 grants (velocity cap) | <= 5 |

Every attack vector fully detected: identical replay, timestamp mutation,
event-id rotation, forged server actor, stale policy, cross-device replay.

## 6. Limitations (mandatory)

- SOFTWARE SECURITY ONLY: no human participants; no motivation/engagement/
  trust/learning evidence; those constructs are UNMEASURED.
- Synthetic attacker and defender; no production telemetry.
- Single-node ledger; distributed races out of scope.
- First-delivery capture (replay before any award exists in the epoch) is
  indistinguishable from an honest first delivery by design; the suite
  models capture-after-award and this is disclosed.
- No external reward-attack dataset exists (registry: assistments BLOCKED,
  ednet BLOCKED, oulad lacks reward semantics); results cannot be
  generalized to human attacker behavior.
- Baseline comparison uses LN-05's published single-batch behavior
  (measured probes), not a re-implementation inside the P08 harness.

## 7. Reproducibility

```
python3 -m research_v3.methods.p08.runner --out research_artifacts_v3/runs/p08
python3 -m pytest tests/research_v3/method/p08 -q      # 24 tests
python3 -m pytest tests/research_v2/ln05 -q            # predecessor: 57 tests
```

## 8. Status

- Implemented: P08-T01 (hypothesis freeze + collision check), T09 (method +
  typed failures), T10 (attack/ablation stress strata), T13 (stress), T15
  (source-to-table: campaign -> results -> manifest checksums), T17
  (this skeleton).
- BLOCKED (human-only, per spec): P08-T19 (ethics/IRB), P08-T20 (novelty
  signoff), P08-T21 (coauthor/venue). DiGRA design-science track BLOCKED —
  requires user studies that do not exist.
- Merge condition: if a reviewer determines the active-adversary delta does
  not justify a separate paper, merge into the LN-05 engineering writeup as
  a hardening section (independence_decision.json records the trigger).
