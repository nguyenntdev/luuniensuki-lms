# P12 METHOD — Source–claim–locator provenance ledger (frozen before engine code)

Paper P12 — *Thẩm định nguồn tư liệu và hệ thống hóa bằng chứng lịch sử phục vụ
dạy học* (source auditing & historical-evidence systematization for heritage
teaching). Status: `HUMAN_HISTORICAL_REVIEW_REQUIRED`. This document specifies
the apparatus; it proves nothing about historical truth.

## 1. Scope and honesty boundaries

- The code provides (a) an append-only claim ledger, (b) a fail-closed
  validator, (c) baselines C0/C1, (d) audit metrics. It **does not** verify any
  historical claim against any archive.
- Vietnamese primary archives (ĐNTL, HĐSL, ĐNNTC) are **BLOCKED for automated
  ingestion**; the module never fetches, scrapes or fabricates page numbers.
- The only corpus processed is the repo's **already-documented** read-only
  claim registry (`data/imperial/`), treated as *documented claims pending
  human archival verification*, not as verified ground truth.
- External provenance data may come from Wikidata (CC0) only, with the exact
  SPARQL query text and response SHA-256 recorded. Wikidata statements are a
  linking aid; per the repo data gate, they can never establish historical
  truth on their own.

## 2. Dataclasses and invariants (input/output contract)

```
SourceRecord   : source_id, title, source_type, edition, rights_status,
                 verification_status, catalog_sha256 (of the registry row)
ClaimEntry     : claim_id, claim_text, source_id?, locator?, stance?,
                 confidence_status?, evidence_kind?
Locator        : edition, volume, page    (all non-empty when present)
LedgerEvent    : seq, timestamp_utc, action(append|annotate), payload, prev_hash, entry_hash
```

Vocabularies (closed sets; anything else is a typed `LedgerError`):

| Field | Allowed values |
|---|---|
| `stance` | `supports`, `refutes`, `undetermined` |
| `confidence_status` | `archival_primary`, `expert_verified`, `editor_reviewed`, `provisional_hypothesis` |
| `evidence_kind` | `primary`, `secondary`, `translation`, `exhibition_copy` |
| `action` | `append`, `annotate` |

`NOT_APPLICABLE` and `ABSTAIN` are first-class values (spec §3.1): a claim may
be admitted with `stance = "undetermined"` and a validator verdict of `ABSTAIN`
("cannot decide without human review") is distinct from `REJECT` (a definite
defect) and from `PASS`.

## 3. State transition rules (fixed constraints, no learned weights)

Validator checks, in order, all fail-closed (`VALIDATION_ERROR` reason recorded,
never silently repaired):

1. **V1 sourced**: `source_id` present and non-empty → else FAIL `missing_source`.
2. **V2 resolvable**: `source_id` resolves in the source registry → else FAIL
   `unknown_source`.
3. **V3 locator present**: a locator exists and has non-empty
   `edition`+`volume`+`page` → else FAIL `missing_locator`.
4. **V4 stance consistency**: for a given `claim_text`, a `supports` entry and a
   `refutes` entry from *different sources* form a contradiction finding
   (`contradiction`), routed to the human conflict log; `undetermined` never
   contradicts anything.
5. **V5 chain integrity**: hash chain of all ledger events verifies
   (`prev_hash` linkage + canonical re-hash) → else FAIL `tampered_chain`.

The chain hash is `sha256(canonical_json({seq, timestamp, action, payload,
prev_hash}))` reusing the shared `research_v2.contracts.canonical_hash`
standard (`sha256(sort_keys,compact,utf8)`), so all V3 artifacts share one hash
convention. Timestamps may be injected for determinism (tests) but the ledger
refuses a *new* append whose timestamp is earlier than the last event's.

## 4. Baselines (exact semantics used by the audit CLI)

- **C0 — no-citation pass-through**: every claim passes with verdict PASS and
  no checks. Serves as the sanity floor; by construction it detects nothing.
- **C1 — citation-presence**: PASS iff the claim record contains any non-empty
  citation-ish string (`citation`, `source_id`, `locator`, or `source_text`).
  This is the "ordinary bibliography" comparator of the RQ.
- **PROPOSED — full validation**: V1–V5 above.

Same input records, same corpus, same reporting script; no tuning of any arm.

## 5. Learning parameters

None. All rules are fixed constraints; there is nothing to fit, so no split /
calibration / overfitting surface exists. Statistical inference (McNemar
paired, cluster bootstrap, multiplicity control) is deferred to the human
phase and will reuse `research_v3/eval/statistics.py` unchanged.

## 6. Complexity and pseudocode

`validate_claim` is O(1) per claim plus O(|registry|) dictionary lookups
(O(1) hashed); chain verification is O(n_events). For a corpus of n claims and
m sources the full audit is O(n + m + n log n) for the stance-conflict grouping
by `claim_text`.

```
audit(corpus, registry):
  events := []
  for claim in corpus:                  # append phase
    events.append(ledger.append(normalize(claim)))
  verdicts := [validate(c, registry, contradictions_index) for c in corpus]
  metrics := {
    unsourced_rate          := #{verdict == FAIL missing_source|unknown_source} / n,
    locator_completeness    := #{sourced ∧ valid locator} / #{sourced},
    contradictions          := |{claim_text: supports ∧ refutes from distinct sources}|
  }
  verify_chain(events)                  # raises on tamper
  return {verdicts, metrics, chain_digest}
```

## 7. Novel vs reused components (spec §3.4)

- **Reused, standard**: canonical JSON hashing
  (`research_v2/contracts/canonical_hash.py`, original: this project, V2
  waves); statistics planned for the human phase (`research_v3/eval/statistics.py`,
  wrapping Wilson/Clopper–Pearson, McNemar, Holm/BH — standard methods, see
  original citations inside that module).
- **Novel here (engineering contribution, not yet scientific evidence)**: the
  P12 locator/stance/confidence-status schema bound to an append-only hash
  chain with fail-closed human-routing of contradictions, and the C0/C1
  baseline semantics defined above.

## 8. Limitations (Threats to Validity — full version in the manuscript)

- **No human archival verification yet**: every `archival_primary` label in the
  smoke corpus is an *inherited documented assertion* (repo v5.1.0), not
  independently re-verified; P12-T19/T20/T21 remain BLOCKED.
- No external corpus: single-collection smoke corpus ⇒ external generalization
  unverified (spec §6).
- The validator detects *internal* consistency defects (missing/unresolvable
  source, missing locator, stance contradiction, tamper) — it cannot detect a
  plausible but wrong page number; that is exactly what the blocked human
  double-review phase is for.
- Metrics on 63 claims are engineering smoke numbers only; they must never be
  quoted as scientific results in the manuscript.

## 9. Replication requirements

Python ≥ 3.11; no third-party packages beyond the repo's own research packages.
Artifacts: `research_artifacts_v3/runs/p12/` (prereg snapshot, corpus ingest
manifest with SHA-256 of every read-only input, C0/C1/proposed run manifests,
conflict log, BLOCKED cards). Rerun command is recorded in each manifest.
