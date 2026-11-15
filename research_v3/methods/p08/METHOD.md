# P08 METHOD — Active-adversary reward-integrity defense (frozen spec)

**Evaluation class: SOFTWARE SECURITY.** No human-outcome evidence exists or
is claimed anywhere in P08. Nothing here estimates motivation, engagement,
trust, or learning effects. P08-T19/T20/T21 remain BLOCKED (human-only).

## 1. Reuse boundary (from independence gate)

- REUSED concept from V2 LN-05: anti-replay idempotency (one award per
  submission identity; transport metadata stripped from identity).
- LN-05 boundary (measured, see `research_v3/experiments/p08/PROBES.md`):
  single-batch policy correctness under honest delivery. LN-05 grants
  cross-session replays, accepts forged `actor="server"` events from a
  channel-controlling adversary, and has no velocity control.
- P08 delta: ACTIVE adversary with channel control; defenses LN-05 lacks:
  HMAC attestation, persistent ledger, velocity gates.

## 2. Input/output dataclasses and invariants

Defined in `research_v3/methods/p08/types.py` (single source of truth):
`Submission`, `RewardEvent`, `Delivery`, `AwardVerdict`, `PolicyConfig`,
`Session`, `LearnerProfile`.

Invariants:
- I1 (oracle hygiene): the defender never reads `Delivery.evaluator_meta`;
  `strip_evaluator_meta` structurally enforces this (LN-05 leakage contract).
- I2 (closed vocabulary): decisions are exactly the `AwardDecision` enum;
  `ABSTAIN` is reserved for defender-side capacity/config failure and is
  distinct from every negative verdict.
- I3 (typed failures): structurally invalid inputs raise `PolicyInputError`;
  no silent defaults.
- I4 (identity determinism): award identity = SHA-256 over canonical JSON of
  learner_id, badge_id, requirement, threshold, evidence map, verified_task,
  sorted event semantics. ALL transport fields excluded (event_id,
  session_id, device_id, client_timestamp, actor, HMAC).

## 3. State transition rules (gate order; first trigger decides)

```
deliver(d):
  1  d.policy_version != config.policy_version   -> reject_stale_policy
  2  !HMAC_verify(d.submission, d.hmac_hex)      -> reject_forged_attestation
     OR any ev.actor != "server" in d.submission -> reject_forged_attestation
  3  velocity window exceeded (learner)          -> reject_velocity
  4  evidence missing / < threshold / task
     not verified                                -> reject_invalid_evidence
  5  identity_key(d.submission) in ledger        -> reject_replay
     (+ cross_session_replay reason when
      session/device differ from first award)
  6  else                                        -> award
     ledger[identity] = {session, device, xp}
     learner_xp += min(award_amounts[kind], cap - current)
```

HMAC payload (D1): canonical JSON of the full semantic submission (learner,
badge, requirement, threshold, evidence, verified_task, event semantics) +
policy_version. Transport fields are NOT signed (delivery variance).
Key: server-side; research runs derive it deterministically from the frozen
seed for reproducibility; production keys must come from a KMS.

Velocity policy (D3): sliding window of 60 virtual seconds (one second per
arrival index — deterministic, no wall clock), max 5 submissions per learner.

## 4. Fixed constraints vs learned parameters

- LEARNED parameters: NONE. This is a deterministic policy with fixed
  constants frozen in `pre_registration.yaml` (threshold 0.75, velocity 5/60s,
  XP amounts 25/50/75, cap 150, policy_version 8). No optimization, no
  training data, no calibration — therefore no certificates/heuristics/runtime
  caps beyond the ledger capacity (10M entries -> abstain, fail-closed).
- NOVEL components (implemented here, first-party): HMAC attestation binding,
  persistent identity ledger, velocity window, gate composition.
- STANDARD/reused (cite originals): SHA-256/canonical-JSON hashing and HMAC
  (RFC 2104) via Python stdlib `hmac`/`hashlib`; the anti-replay idempotency
  concept and delivery-variant stripping concept are reused from LN-05
  (`research_v2/methods/ln05/proposed.py`), cited as the predecessor.

## 5. Pseudocode of the defender

```
class Defender:
  consumed: map identity_key -> {session, device, xp}
  velocity: map learner -> sliding window hits

  evaluate(stream):
    for i, d in enumerate(stream):
      d = strip_evaluator_meta(d)              # I1
      v = gate1(d) or gate2(d) or gate3(d, i) or gate4(d) or gate5(d) or award(d)
      emit verdict(i, v)
```

Complexity: O(n) over the delivery stream (each gate O(1) amortized; identity
hash O(payload size), payload bounded by submission size). Memory O(consumed +
velocity windows). The 100x idempotency proof is O(100) after one award.

## 6. Determinism & reproducibility

- No RNG, no wall clock (virtual time = arrival index).
- Fixtures are pure functions of seed 20261115.
- Campaign: `python -m research_v3.methods.p08.runner --out <dir>`; identical
  input -> byte-identical verdicts (tested).

## 7. Failure modes and honest accounting

- First-delivery capture: a replayed delivery whose original was never
  delivered to THIS defender epoch is indistinguishable from an honest first
  delivery; the frozen suite models capture-after-award (the harness delivers
  the original once before the attack stream). This is disclosed, not hidden.
- Velocity rejection of honest bursts: possible by design; the honest control
  spread is fixed and measured (0/1000 false rejections in the frozen run).
- Ledger capacity exhaustion -> abstain (never award) — fail-closed.
- Distributed multi-node race behavior is OUT OF SCOPE (single-node ledger);
  disclosed limitation.
