# P08 empirical collision probes (evidence for independence_decision.json)

Executed 2026-11-15 against V2 LN-05 at HEAD `4e5a792e16250106b9d0a577849e864ab7007c92`
(`research_v2/methods/ln05/proposed.py::predict_batch`, LN-05 suite 57/57 passing).

## Probe 1 — 100x duplicate, one batch
100 deliveries of one valid submission into a single `predict_batch` call.
Result: **exactly 1 grant, 99 rejections** (`deduplicate_events`).
Covered by LN-05: YES (`tests/research_v2/ln05/test_duplicate_concurrency_100x.py`).

## Probe 2 — timestamp + event_id mutation, same batch
Redelivery with mutated timestamp and rotated event ids.
Result: **rejected** — delivery-variant fields are stripped before the
content-derived dedup key. Covered by LN-05: YES.

## Probe 3 — cross-device redelivery
Same submission, new `session_id`/`device_fingerprint`/rotated `event_id`/fresh timestamps.

- Within one batch: **REJECTED** (deduplicate_events).
- Across separate `predict_batch` calls (session restart / second device):
  **GRANTED** — `ReplayLedger` is constructed inside `predict_batch`
  (research_v2/methods/ln05/proposed.py:546), so each session starts with an
  empty ledger and re-earns the award. Covered by LN-05: NO (boundary never claimed).

Probe transcript (delivery1 grant → cross-device redelivery grant):
```
delivery1: grant_if_eligible
cross-device redelivery: grant_if_eligible ('verified_competency_achieved', 'provenance_validated')
new-evidence control: deny_mastery_badge ('missing_competency_evidence', 'uncorroborated_competency')
```

## Probe 4 — forged server actor
Attacker controls the delivery channel; stamps `actor="server"` on reward
events with forged maximal evidence (0.99) and a corroborating profile.
Result: **GRANTED** (`grant_if_eligible`, reasons `verified_competency_achieved,
provenance_validated`). LN-05's provenance gate inspects a client-supplied
actor string — it defends against mislabeled traffic, not a channel-controlling
adversary. Covered by LN-05: NO.

## Probe 5 — fast-click reward farming
30 distinct valid-evidence submissions in one burst (no replay content).
Result: **30/30 GRANTED** — no velocity or burst gate exists in LN-05.
Covered by LN-05: NO.

## Probe 6 — deceptive badge copy
No copy/UI surface exists in LN-05's data model; human-perception stratum is
NOT_APPLICABLE for a software-security evaluation; human claims BLOCKED
(P08-T19/T20/T21).

## Consequence
LN-05 measurably fails three active-adversary classes it never claimed to
cover. P08 PROCEED as SOFTWARE SECURITY EVALUATION; merge trigger fires only
if the P08 defender cannot beat these strata (it must, or MERGE_INTO_V2_LN05).
