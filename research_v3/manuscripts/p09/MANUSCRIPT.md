# P09 — Provenance-Aware Interactive Cultural Heritage Exploration
# Manuscript skeleton (CHIRA-oriented; venue CFP/rank to be re-verified at submission time)

**Status: `ENGINEERING_PASS — HUMAN_STUDY_AND_SIGNOFFS_BLOCKED`.** This skeleton complies
with the prereg (`research_v3/experiments/p09/pre_registration.yaml`). The offline gate
evaluation is complete on a real licensed corpus; **every human-subject and human-signoff
cell is BLOCKED** (P09-T19/T20/T21). **No usability, comprehension, or source-verification
claim is made anywhere in this manuscript** because no participant study has run. The
paper will not be submitted in its current state.

---

## 1. Introduction & RQ

Heritage exploration interfaces increasingly surface historical claims drawn from knowledge
graphs and digitized archives. Two failure families recur: (a) claims presented without
checkable citations; (b) citation-only interfaces that display a reference string the user
cannot resolve to the actual evidence. Digital-heritage provenance standards (Europeana Data
Model; CIDOC-CRM) model record-level provenance for interoperability, but do not prescribe a
*surfacing policy*: which claims may be shown, which must be withheld, and what the user sees
when evidence is missing.

**RQ (frozen, from spec).** Does interactive visibility of disputed evidence, source
provenance and historical uncertainty improve source attribution decisions and user
comprehension?

**What this wave establishes (and only this).** On a real CC0 Wikidata mini-corpus of the
Complex of Huế Monuments, a fail-closed claim-level provenance gate achieves an
unsupported-claim surfacing rate of exactly **0.0** (primary endpoint) while surfacing every
structurally-verified claim, whereas surface-everything (C0) and keyword-text (C1) baselines
surface 45/51 and 40/51 unsupported claims respectively on the identical corpus. This is an
**engineering result about the gate**, not a user-study result. H0 (a conventional
citation-only interface performs equally well on independent source-verification tasks) is
carried forward **untested**; it requires the human study.

**Novelty boundary.** P09 owns the interactive exploration layer with fail-closed per-claim
provenance gating and visible epistemic badges. P12 owns scholarly source curation (backend);
P03 owns tutor-side citation faithfulness. No other P paper shares this RQ, sample type, or
principal table. The distinct mechanism is: abstention is a first-class visible outcome
(never silent), and invalid citations are rejected, not displayed.

## 2. Related work

- **Digital heritage provenance:** Europeana Data Model (EDM) for object/agent/rights
  provenance; CIDOC-CRM (ISO 21127) for event-based documentation; Linked Open Data in
  museums (e.g., Smithsonian Open Access, Rijksmuseum LOD). These provide *record* schemas;
  none defines a claim-surfacing policy with fail-closed semantics.
- **Wikidata as provenance substrate:** Wikidata (CC0) data access via SPARQL and
  Special:EntityData snapshots; statement-level references (P248 "stated in", reference
  URLs). *We treat Wikidata source statements as secondary evidence only* — following the
  project's ethics rule that historical truth cannot be inferred from Wikidata alone.
- **Epistemic uncertainty in interfaces:** work on uncertainty visualization and
  confidence/trust badges in decision support; citation-needed UI patterns on collaborative
  platforms. These study user trust effects; none couples the badge to a hard surfacing gate
  evaluated on unsupported-claim leakage.
- **KG+RAG citation systems:** attributed QA systems attach retrieved passages as citations
  but typically optimize answer accuracy, not zero unsupported-surfacing under adversarial
  citation mutation.
- **Gap:** no prior system we could license and rerun combines (i) per-claim fail-closed
  gating, (ii) visible abstention, (iii) evaluation on a real heritage corpus with
  byte-hashed sources and adversarial citation counterexamples. (See
  `experiments/p09/baseline_cards.yaml` for the dated BLOCKED rationale for the nearest
  published comparators.)

## 3. Method (implemented; see `research_v3/methods/p09/METHOD.md`)

- **Provenance model:** `claim → source → locator` typed dataclasses. Locators are
  kind-validated (statement GUID / property / page / section); statement GUIDs must resolve
  inside the frozen source snapshot. Every source carries license + retrieval date + raw
  response SHA-256.
- **Verification gate (fail-closed):** structural validation → registry existence → source
  fidelity (declared source must byte-match the registry: detects license/URL/sha tampering)
  → statement-GUID resolution → badge check. Output ∈ {verified, unverified, invalid}.
  The gate never upgrades a claim; default badge on ingestion is `unverified`
  (unverified-until-linked).
- **Exploration policy:** gate-verified → `surface` with full citation bundle and visible
  `verified` badge; unverified → `abstain_unverified` (visible placeholder, no claim text);
  invalid → `reject_invalid_source`. Deterministic, pure, no learned parameters.
- **Corpus (real, licensed):** frozen SPARQL discovery query (transitive `P361+` members of
  the Complex of Huế Monuments Q10810560, built-heritage classes) → 23 entities; per-entity
  `Special:EntityData` JSON snapshots (byte SHA-256 each) → 51 claims across 6 properties,
  each bound to a real statement GUID. Wikidata CC0. Discovery response + query text hashed
  in `corpus_manifest.json`.
- **Deterministic verification rule (versioned):** a claim is marked `verified` iff its GUID
  resolves in the snapshot AND the statement carries ≥ 1 reference block. This is a
  *structural* rule, explicitly **not** expert adjudication.
- **Baselines:** C0 surface-everything; C1 keyword match on claim text (fixed heritage
  vocabulary; deterministic heuristic proxy — labeled as such, not a real deployed system).
- **Metrics:** unsupported-claim surfacing rate (primary), citation-grounding rate,
  abstention rate; zero-error cells report Wilson + Clopper-Pearson CIs (never [0, 0]);
  adversarial counterexample suite (false citation, non-existent source, forged GUID,
  missing rights statement).
- **Complexity:** O(1) per claim against a hash-map source index; no GPU; < 2 min wall time
  including live retrieval.

## 4. Results (offline gate evaluation; no human outcomes)

From `research_artifacts_v3/runs/p09/manifest.json` (all cells computed from frozen files;
checksums round-trip; no hand-entered numbers):

| Method | n | surfaced | grounded | unsupported surfaced | unsupported rate | grounding rate | abstention |
|---|---|---|---|---|---|---|---|
| C0 surface-everything | 51 | 51 | 6 | 45 | 0.882 | 0.118 | 0.000 |
| C1 keyword-match | 51 | 46 | 6 | 40 | 0.784 | 0.118 | 0.098 |
| **Proposed provenance-gated** | 51 | 6 | 6 | **0** | **0.000** | 0.118 | 0.882 |

- **H1 supported (engineering tier):** proposed unsupported-claim surfacing rate = 0.0
  exactly (Clopper-Pearson 95% upper bound reported in metrics.json).
- **H2 supported:** proposed surfaces exactly the 6 gate-verified claims; no verified claim
  withheld.
- **H3 supported:** C0 leaks all 45 non-verified claims; C1 leaks 40 on the same corpus.
- **H4 supported:** all four adversarial counterexamples rejected with typed reason codes
  (`unresolvable_statement_guid`, `nonexistent_source_id`, `source_registry_mismatch`,
  `invalid_locator`).
- **Interpretation guard:** the abstention rate of the proposed policy (0.882) is the honest
  cost of the gate under the deterministic reference verification rule: most Wikidata
  statements in the corpus carry no reference block. This is a *feature of the corpus*, and
  it is the expected failure family a human editorial pass would shrink (future work).
- **No SOTA claim is made**: comparators are C0/C1 only; the nearest published baseline is
  BLOCKED (`baseline_cards.yaml`).

## 5. Human audit (list produced; labels NOT produced)

`research_artifacts_v3/runs/p09/audit/audit_sample.json`: 10 claims (20%, min 8, seed 42,
deterministic), each with claim text, declared source/locator, both methods' decisions, and
**null auditor fields** plus instructions for an independent human auditor. This pipeline
does not label the sample and does not claim expert verification of any item. The audit
result (agreement rates, locator resolution failures) will be reported only after a real
auditor completes it, under a recorded protocol.

## 6. Threats to Validity

1. **No expert adjudication yet.** The verified/unverified split uses a deterministic
   structural rule (GUID resolves + ≥1 reference block). It does not measure historical
   accuracy. A human editorial pass (T19) could reclassify claims; all code paths re-run
   deterministically on a new frozen corpus.
2. **Wikidata is secondary evidence.** Statement references inside Wikidata are themselves
   unverified pointers; nothing here infers historical truth from Wikidata alone.
3. **Construct validity of the primary metric.** Unsupported-claim surfacing is measured
   against the gate's own outcome definitions; a skeptic may ask the gate to be validated
   against independent human judgment — that is exactly the blocked audit/study.
4. **Single collection.** One heritage domain (Huế monuments) from one provider (Wikidata);
   external generalization unverified (spec requires ≥ 2 domains for a generalization claim).
5. **Baselines are weak by design.** C0/C1 are sanity/matched-classical comparators; a win
   over them is not evidence of superiority over published interactive-provenance systems.
6. **No user study.** All interface-level outcomes (source-verification accuracy,
   time-to-correct-source, conflict recognition, task completion, usability,
   false-confidence rate) are **BLOCKED**, not merely pending.
7. **Corpus drift.** Wikidata is live; snapshots are frozen by byte-hash, but a rebuild on a
   later date can differ. Rebuilds must re-freeze hashes and re-run the matrix.
8. **Deterministic seed.** The single seed (42) affects only the audit sample draw; no
   stochastic training exists, so no seed-variance is reportable (and none is claimed).

## 7. Ethics & rights

- Huế heritage corpus: **BLOCKED** (no written archival permission); untouched in the
  registry; not scraped.
- Europeana: **BLOCKED** (no API key; item-level rights unresolved).
- Wikidata: used under **CC0 1.0** via public SPARQL endpoint + EntityData snapshots, with
  declared User-Agent, recorded query text, and per-response SHA-256.
- No human subjects, no minors, no PII; no fabricated permissions, expert labels, or
  "expert consensus" anywhere in the pipeline or artifacts.

## 8. Task status (paper spec §8)

| Task | Status | Evidence |
|---|---|---|
| T01 RQ/null/collision | DONE (this wave) | prereg + this skeleton §1 |
| T02 rights & source selection | DONE (Wikidata CC0; Hue/Europeana BLOCKED) | corpus_manifest.json; registry untouched |
| T03 schema definition | DONE | provenance.py dataclasses + METHOD.md §3 |
| T04 ingestion & immutable provenance | DONE | entity snapshots + SHA-256 manifest |
| T05 leakage-proof split | N/A → documented | deterministic rule system, no training split; sidecar sealed from policies |
| T06 descriptive baseline | DONE | metrics.json distribution block |
| T07 classical baseline | DONE (C1, heuristic, labeled) | baselines.py |
| T08 closest published | BLOCKED (dated rationale) | baseline_cards.yaml |
| T09 method + invariants | DONE | METHOD.md I1–I4; tests |
| T10 ablations/mutations | PARTIAL (counterexamples done; interface ablations A1–A4 are UI-level → user study) | counterexamples.json |
| T11 training/calibration | N/A → documented | zero learned parameters |
| T12 preregistered matrix | DONE (offline tier) | manifest.json |
| T13 robustness/stress | PARTIAL (citation-mutation strata done) | counterexamples.json |
| T14 statistics | DONE (offline tier; CIs for zero cells) | metrics.json |
| T15 source-to-table | DONE | manifest checksums round-trip; tests |
| T16 failure review & collision | DONE (this skeleton §6; collision in §1) | failure notes in prereg |
| T17 manuscript build | PARTIAL (skeleton; results frozen) | this file |
| T18 external reproduction | PENDING (clean-clone rerun instructions in METHOD.md §7/§9) | run_p09.py stages |
| **T19 ethics/annotation signoff** | **BLOCKED (human-only)** | — |
| **T20 novelty signoff (research lead)** | **BLOCKED (human-only)** | — |
| **T21 coauthor/venue signoff** | **BLOCKED (human-only)** | — |

**Release status:** `ENGINEERING_PASS`. Not `SCIENTIFIC_REVIEW_READY`, not
`SUBMISSION_READY`. Done-means per spec: unverifiable human tasks remain blocked, never
silently accepted.

## 9. Reproduction

```bash
PYTHONPATH=. python3 research_v3/experiments/p09/run_p09.py build     # live CC0 retrieval, hashes frozen
PYTHONPATH=. python3 research_v3/experiments/p09/run_p09.py evaluate  # offline matrix + audit sample + counterexamples
PYTHONPATH=. python3 -m pytest tests/research_v3/method/ -k p09       # 35 contract tests
```

## Appendix A — Figures (planned; UI-level ablations blocked pending user study)

- Fig. 1: provenance bundle card (source, locator, badge, license) — mock from citation JSON.
- Fig. 2: abstention placeholder (visible, honest) vs silent drop.
- Fig. 3: unsupported-surfacing by method (bars from metrics.json).
- These figures show *system behavior*, not user outcomes.
