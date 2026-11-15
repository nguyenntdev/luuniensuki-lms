# P09 — Provenance-Aware Interactive Cultural Heritage Exploration: Method Contract

Paper ID: `P09` · Method version: `p09-provenance-v1.0.0` · Status: `ENGINEERING_PASS`
(scope: method + offline gate evaluation; **no human-subject study is run here**)

## 1. Research question, estimand, null

**RQ (interface-visibility framing).** Does making claim-level provenance (source,
locator, epistemic status) explicitly visible in an interactive heritage explorer
improve source-attribution decisions and comprehension compared with a conventional
citation-only interface?

**What is actually built in this wave (honest scope).** The *provenance model*,
the *fail-closed surfacing policy*, the *licensed Wikidata mini-corpus* (real HTTP
retrieval, SHA-256 recorded), the *offline gate evaluation* against baselines
C0/C1, and a *manual human-audit sample list* for an independent human auditor.
We do **not** run the interactive user study, do **not** recruit participants,
and do **not** produce expert labels. Time-to-correct-source, usability, and
comprehension outcomes are therefore **BLOCKED**, not reported.

**Estimand.** On a frozen evaluation corpus of `claim → source → locator`
candidates (each claim carrying a verification outcome from the frozen gate),
the surfacing policy maps each claim to one decision:

- `surface` — claim shown with its full provenance bundle (source + locator + badge);
- `abstain_unverified` — claim withheld, visible placeholder stating that the
  claim is unverified (explicit abstention, never silently dropped);
- `reject_invalid_source` — claim's citation fails structural validation
  (malformed locator, non-existent source id, wrong domain); never surfaced.

**Primary metric (pre-registered, single).** *Unsupported-claim surfacing rate* =
(surface decisions on claims whose verification outcome is
`unverified | invalid`) / (all claims in the evaluation corpus). Required value
for the proposed policy: **exactly 0.0** (fail-closed gate).

**Secondary metrics.** Citation-grounding rate = surface decisions on
verified-source claims / all claims (higher is better); abstention rate =
abstain decisions / all claims; counterexample detection on adversarial
mutation cases (false citation, non-existent source id, forged locator).

**H0 (published if not rejected, and only with the human study).** A conventional
citation-only interface performs equally well on independent source-verification
tasks. This wave cannot test H0 (no human outcomes); it is carried forward
unchanged in `pre_registration.yaml`.

**Nearest prior work (collision check, T01).** (a) KG+RAG citation systems
surface retrieved passages with citations but do not fail-closed withhold
individual claims whose source fails a verification gate; (b) digital-heritage
provenance work (Europeana data model, CIDOC-CRM) models provenance for records,
not per-surfaced-claim abstention policies; (c) P12 of this portfolio owns
scholarly source curation (backend), not the interactive exploration layer.
P09's distinct mechanism is the **fail-closed claim-level gate with visible
epistemic badge and explicit abstention**, evaluated on a real licensed corpus.

## 2. Data rights (honest)

| Corpus | Status | Basis |
|---|---|---|
| Huế heritage corpus (registry `hue-heritage-corpus`) | **BLOCKED** | No written archival permission. Not used. Not scraped. |
| Europeana metadata | **BLOCKED** | No API key available; registry card already BLOCKED. Not used. |
| Wikidata SPARQL + EntityData | **USED (CC0)** | Public endpoint, CC0 1.0 declaration. Query text + response SHA-256 recorded. **Limitation stated explicitly: Wikidata source statements are secondary evidence, not primary archival sources; no historical truth is inferred from Wikidata alone** (per `04_METHODOLOGY/ETHICS_AND_INTEGRITY.md` §7). |

A dataset card for `wikidata-hue-heritage-mini` is written with the frozen query
hash; `hue-heritage-corpus` remains BLOCKED in the shared registry (untouched).

## 3. Provenance model (claim → source → locator)

Typed, frozen dataclasses (`provenance.py`):

- `SourceRef(source_id, kind, title, url, license, retrieved_at, sha256?)` —
  one citable source. `kind ∈ {wikidata_entity, wikidata_statement, archive_document,
  published_work}`. `sha256` = SHA-256 of the raw response bytes when the source
  is a fetched snapshot (EntityData JSON).
- `Locator(source_id, kind, value)` — where inside the source the claim lives.
  `kind ∈ {statement_guid, property, section, page}`. Validity depends on `kind`:
  `statement_guid` must match `^Q\d+\$[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
  and its QID prefix must equal the source entity's QID; `property` must be `P\d+`;
  `page` must be a positive integer; `section` must be non-empty.
- `Claim(claim_id, entity_qid, text, source, locator, epistemic)` — one candidate
  claim with `epistemic ∈ {verified, unverified, disputed}` (a *badge* value;
  the default for corpus ingestion is `unverified` — unverified-until-linked).
- `VerificationOutcome` ∈ {`verified`, `unverified`, `invalid`} — the gate's
  decision, distinct from the badge (badge = declared status; outcome = gate check).

**Invariant I1 (locator binding).** A claim is well-formed iff its locator's
`source_id` equals its source's `source_id` and the locator passes the
kind-specific structural validation above. Violations ⇒ gate outcome `invalid`.

**Invariant I2 (existence).** `locator.source_id` must resolve to a source in the
corpus source registry. A claim citing a non-existent source id ⇒ `invalid`
(this is the required negative case; see tests).

**Invariant I3 (statement binding).** For `kind=statement_guid`, the GUID must
exist among the source entity's frozen statement ids (checked against the
corpus snapshot, not re-fetched). Unresolvable GUID ⇒ `invalid`.

**Invariant I4 (determinism).** All gates and policies are pure functions of
`(claim, corpus_state)`; same input bytes ⇒ same decision bytes.

## 4. Verification gate (fail-closed)

`verify_claim(claim, corpus) -> VerificationOutcome`:

1. Structural validation of source + locator (I1, I2). Any failure ⇒ `invalid`.
2. Statement existence check (I3) when applicable. Failure ⇒ `invalid`.
3. If the claim's `epistemic` badge is `verified` **and** steps 1–2 pass ⇒ `verified`.
4. Otherwise (badge `unverified`/`disputed`, or any missing field) ⇒ `unverified`.

Fail-closed: the gate never upgrades a claim; the only path to `verified` is an
explicitly verified badge plus a passing locator check. There is no heuristic
"looks plausible" path. `verified` in this corpus means *verified against the
Wikidata snapshot statement structure* — it does NOT mean expert-adjudicated
historical truth (stated on every export and in the manuscript).

## 5. Exploration policy (proposed)

`propose_surface(claim, corpus, config) -> SurfaceDecision` with

- `decision ∈ {surface, abstain_unverified, reject_invalid_source}`,
- `epistemic_badge ∈ {verified, unverified, disputed}` (surfaced on `surface`
  decisions; `unverified`/`disputed` claims are never surfaced so no badge leak),
- `reason_codes` (typed strings), `evidence_ids` (source id when surfaced).

Decision table: gate `verified` ⇒ `surface`; `unverified` ⇒ `abstain_unverified`
(visible placeholder in the UI contract; modeled here as an explicit decision);
`invalid` ⇒ `reject_invalid_source`. No default surface path exists.

## 6. Baselines

- **C0 "surface everything"** (`baselines.py`): every claim is surfaced with
  badge `verified` regardless of verification outcome. This is the naive
  browsing baseline; its unsupported-claim surfacing rate equals the corpus
  unverified+invalid rate by construction.
- **C1 "keyword match on claim text"** (`baselines.py`): deterministic keyword
  gate — a claim is surfaced iff its text contains a curated heritage-vocabulary
  keyword AND passes no provenance check at all. It models "filter by text, not
  by source". Deterministic and labeled as a heuristic proxy.

Both are honest C0/C1 sanity/matched-classical baselines per
`04_METHODOLOGY/SCIENTIFIC_EVALUATION.md` §3. No published interactive-heritage
baseline implementation is available under a compatible license at freeze time;
the nearest-work BLOCKED card is recorded in `experiments/p09/baseline_cards.yaml`.

## 7. Corpus construction (real, licensed)

Frozen SPARQL discovery query (exact text in
`research_artifacts_v3/runs/p09/corpus/query.sparql`, sha256 recorded in
`corpus_manifest.json`): all Wikidata items that are *part of* (P361) the Complex
of Huế Monuments (Q10810560) — the UNESCO World Heritage property — constrained
to heritage-site instance-of classes. For each discovered entity, the **Special:EntityData
JSON snapshot** (`https://www.wikidata.org/wiki/Special:EntityData/<QID>.json`) is
fetched over HTTP, its raw bytes SHA-256-hashed, and stored immutably under
`corpus/entity_json/`. Claims are derived from the snapshot's statements
(inception P571, coordinates P625, part-of P361, instance-of P31, country P17,
located-in P131), each with a **real statement GUID locator** from the snapshot.
Every factual statement starts `unverified` (unverified-until-linked); the
frozen evaluation seed then verifies a documented deterministic subset
(those whose statement GUID resolves in the snapshot AND whose property has a
reference in the snapshot) — the verification rule is itself versioned and
auditable, and the verified subset is materialized in the frozen corpus JSON so
the split is reproducible. Distinguish clearly:

- **Discovery (SPARQL, CC0):** which entities exist; query text + response hash saved.
- **Evidence (EntityData snapshot, CC0):** claim text + statement GUID locators;
  byte-level SHA-256 per entity.

## 8. Offline evaluation protocol (no humans)

Corpus = frozen claims JSONL (input `claim`, sidecar `verification_outcome`
computed by the frozen gate from the frozen corpus state — sidecar is never an
input to any policy). Each of {C0, C1, proposed} runs over all claims; metrics
computed by `metrics.py`; a deterministic audit sample (seed 42, 20% of claims,
min 8) is exported for a **human** auditor with instructions; the auditor's
labels are NOT produced by this pipeline. Adversarial mutation cases (spec §5:
false citation, non-existent source id, forged locator, missing rights statement)
are generated deterministically and included in the counterexample report.

## 9. Complexity & compute

Gate + policy: O(1) per claim against an in-memory source index (hash map);
corpus build: O(entities × statements); total live retrieval < 30 HTTP requests,
no GPU, wall time < 2 min. No learned parameters exist anywhere in this method —
all thresholds are fixed constraints (spec requirement 3: nothing to fit).

## 10. Limitations (carried into manuscript)

1. Wikidata statements are secondary evidence; claims verified here are
   structurally verified, not historically adjudicated.
2. The verified/unverified split inside the corpus uses a deterministic
   reference-rule; a human editorial pass is future work (T19 BLOCKED).
3. No interactive user study: usability/comprehension outcomes BLOCKED (T19–T21).
4. Single collection (Huế monuments): external generalization unverified.
