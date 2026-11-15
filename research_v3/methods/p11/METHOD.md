# P11 Method — Rubric for Historical Reasoning Competency (S1–S4)

Paper: **P11 — Xây dựng và kiểm định rubric đánh giá năng lực suy luận lịch sử trong môi trường học tập số**
Status: **RATER_AND_SAMPLE_REQUIRED** → every human-dependent artifact is BLOCKED until real raters and real (consented) responses exist.
This document is the pre-code contract required by spec §3.2: formal definitions *before* implementation.

## 1. Research question, estimand, hypotheses (P11-T01)

**RQ.** Does the four-criterion rubric S1–S4 (sourcing, corroboration, contextualization, argumentation) achieve content validity (CVI), inter-rater reliability (weighted Cohen's κ, Krippendorff's α, ICC) and level discrimination appropriate for assessing historical reasoning, compared with the current single-holistic marking practice?

**Estimand.** The population inter-rater reliability of the S1–S4 instrument over a defined rater population and a defined response population, expressed as κ_w (quadratic weights, 0–3 ordinal scale) per criterion and overall, with cluster-aware 95% CIs (cluster = response).

**H0 (must be published if not rejected).** The multi-criterion rubric does not increase reliability/validity over the current single-dimension scale (B00/B02 holistic marking; B03 keyword-presence as algorithmic sanity floor).

**Collision check with other P papers (2026-11-15).** P10 uses a *spiral-progression curriculum rubric* as a curriculum-alignment metric; P14 uses a *UDL task-affordance rubric* for accessibility. Neither paper's sample, RQ, or primary table is a historical-reasoning instrument with a rater-reliability study → no MERGE_REQUIRED collision found. Nearest external prior work is the Document-Based Lesson / historical-thinking assessment literature (Wineburg 1991 sourcing–corroboration–contextualization triad; Monte-Sano 2011 rubric-based writing assessment; Breakstone & Smith 2012 disciplined-history item design; the Reading Like a Historian/Document-Based Questions tradition). These inform construct definition only — no external implementation is being adapted, so B01/B02/B03 are specified as local re-implementations with pinned hashes at run time (honest BLOCKED cards if a named upstream cannot be pinned).

## 2. Formal objects

### 2.1 Response schema (input to scoring)

A `HistoricalReasoningResponse` is a **declared structure**, not free text: the student (or an extraction step performed by the teacher) declares claims, evidence items, and citation links. The rubric is intentionally *not* an NLP scorer — per paper scope, it scores declared evidence/claims/citations. Anything that requires reading undeclared prose is out of scope and must be routed to human raters.

```
response_id: str
evidence: list[EvidenceItem]        # each with an evidence_id
claims:   list[Claim]               # each with a claim_id
links:    list[EvidenceLink]        # (claim_id, evidence_id, relation, citation?)
```

`EvidenceItem` carries: `source_type ∈ {primary, secondary, artifact, oral, other}`, `provenance ∈ {cited, described, asserted}`, `is_authentic` flag (a named real archive/source vs. invented/fake citation), and optional `locator` (stable archival page/claim id per ethics rule 7).

`EvidenceLink.relation ∈ {supports, refutes, contextualizes}`.
`Claim` carries `is_causal` (whether the claim asserts a causal relation) and `inference_type ∈ {none, descriptive, explanatory, causal, counterfactual}`.

### 2.2 Rubric (typed, 0–3 ordinal levels per criterion)

Four criteria, each an ordinal 0–3 scale with defined descriptors (see `rubric.py` and the codebook for the full descriptor text):

| Criterion | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **S1 Sourcing** | no evidence used | evidence asserted without provenance | provenance described but not cited | cited authentic source w/ locator |
| **S2 Corroboration** | single/none | ≥2 evidence items but unlinked to claims | linked support but no cross-check | cross-checked links, incl. refuting/limiting evidence |
| **S3 Contextualization** | no context | generic/undated context | dated/spatial context linked to a claim | contextualization constrains the claim's scope/validity |
| **S4 Argumentation** | claim w/o inference | descriptive inference | explanatory inference supporting a claim | explicit reasoning chain incl. refutation handling or counterfactual |

Two distinguished non-ordinal marks (spec §3.1 requirement) — **never** conflated with 0:

- `NOT_APPLICABLE`: the criterion cannot apply (e.g., prompt did not require sourcing).
- `ABSTAIN`: the rater (or scorer) declines to judge (insufficient information to score).

Invariants: levels are integers in `{0,1,2,3}` only; `NA`/`ABSTAIN` are excluded from mean-score statistics and reported as coverage counts; `ABSTAIN` is not imputed.

### 2.3 Scoring functions (deterministic)

```
score_S1(response) = level from max(provenance described anywhere, citations w/ authentic sources, locator presence)
score_S2(response) = joint level over {n_evidence, links-to-claims, cross-checking (≥2 evidence on one claim, refutes present)}
score_S3(response) = level from context-bearing links on claims that carry explanatory/causal inference
score_S4(response) = level from max inference_type, +2-level rule when refutation/counterfactual is handled
overall_score(response) = mean of applicable criterion levels (round-half-even to 2 dp)
```

All scorers are pure functions of the declared structure — same input ⇒ same output (property tested). **Upper-bound rule (negative case):** a response with **zero evidence items** is capped at level 0 on S1/S2/S3 and level ≤ 1 on S4 regardless of claim richness. A response whose citations are all `is_authentic=False` (fabricated sources) is capped at level ≤ 1 on S1 ("từ khóa đúng nhưng đảo quan hệ / dẫn nguồn giả" stress families from spec §5 are realized as deterministic constructed mutations of real cases).

### 2.4 Baselines (spec §4 matrix, algorithmic subset)

- **C0 (≈B03 sanity):** keyword-presence scoring — counts occurrences of sourcing/corroboration/context/argument keyword families in declared text fields; ignores structure. Expected failure family: keyword hits on fabricated or relation-inverted content.
- **C1:** rubric-applied-to-declared-evidence — this document's scorer (§2.3).
- **Proposed (deferred, needs human data):** evidence-link-aware scoring *calibrated against human ratings* (weights fitted on rater training data only, per spec §3.3). Until raters exist this is a hypothesis, not implemented, not claimed.

### 2.5 Reliability estimation (see `reliability.py`)

- **Krippendorff's α** with nominal, ordinal, interval and quadratic-weighted variants, general missing-data (two or more raters, incomplete matrices). Computed from the coincidence matrix — standard published formulation (Krippendorff 2004; Hayes & Krippauer 2007). Implemented locally: `research_v3/scripts/annotations.py` does not exist (checked 2026-11-15), so the agreement math lives in `research_v3/methods/p11/reliability.py` per task instruction.
- **Weighted Cohen's κ** (quadratic weights) for the two-rater case; unweighted κ also reported.
- **ICC(A,1)** two-way random effects, absolute agreement, single rater (Shrout & Fleiss 1979 Case 2 / McGraw & Wong).
- **Cronbach's α** (internal consistency across the 4 criteria) as the spec's "ordinal alpha" internal-consistency proxy — reported as instrument internal consistency only, never as inter-rater reliability.
- Reported **only** on: (a) real human annotation matrices, or (b) clearly-labeled SYNTHETIC/TOY inputs inside tests and harness smoke runs. No toy number may appear in any results table.

## 3. Complexity and artifacts

All scorers are O(N·E·C) in responses, evidence items, criteria — negligible compute; no GPU; no training. Replication artifacts: this file, `rubric.py`, `reliability.py`, `experiments/run_p11_status.py`, `annotations/tasks/p11_annotation_pack/`, constructed case set, tests.

## 4. What this does NOT claim

No content-validity coefficient (needs ≥2 real expert raters, P11-T19). No inter-rater reliability (needs real blind double-marking). No criterion-related validity (needs real outcome data). No population-level discrimination claims. All such numbers are BLOCKED (P11-T12, T13, T14, T19, T20, T21).
