# P12 — Thẩm định nguồn tư liệu và hệ thống hóa bằng chứng lịch sử phục vụ dạy học di sản Cửu Đỉnh–Đại Nội Huế

**Manuscript skeleton — SKELETON ONLY. Venue (định hướng):** Tạp chí Khoa học
Đại học Huế: KHXH&NV (chỉ bài thuộc Giáo dục học) (HĐGSNN) — CFP, rank 2027 và
fit **chưa được xác minh** (P12-T21 BLOCKED). **Trạng thái:**
`HUMAN_HISTORICAL_REVIEW_REQUIRED` — nothing in this file may be submitted
until P12-T19/T20/T21 are signed by real humans.

> Integrity rule: every numeric value below marked ⧗ cites an artifact file in
> `research_artifacts_v3/runs/p12/`; no number may appear in a submitted
> version without such a binding (spec §6, T17).

## 1. Title (working, frozen in prereg v1.0.0)
A Provenance-Ledger Apparatus for Auditing Historical Claims in Vietnamese
Heritage Teaching Materials: Design and Fail-Closed Validation (study protocol)

## 2. Abstract skeleton
- **Context:** heritage LMS teaching materials cite Nguyễn-dynasty primary
  sources; citation defects are hard to detect at scale and human archival
  review is expensive.
- **Gap:** ordinary bibliography workflows check that *a* citation exists, not
  that it resolves, locates the claim, and stays consistent.
- **Contribution (apparatus, not efficacy):** an append-only hash-chained
  claim ledger binding each claim to a resolvable source, a structured locator
  (edition/volume/page), and a stance; a fail-closed validator that rejects
  unsourced/unresolvable/unlocated claims and routes stance contradictions to
  human adjudication; baselines C0 (no-citation) and C1 (citation-presence).
- **Status:** engineering validation on a 63-claim documented smoke corpus ⧗
  `summary.json`; **no scientific efficacy claim** — human double review
  (annotation agreement, editor time, conflict resolution) is BLOCKED.

## 3. Research question (frozen)
Quy trình thẩm định nguồn—mệnh đề—trích dẫn theo phiên bản có nâng chất lượng
học liệu giáo dục di sản so với thư mục thông thường không? (P12-RQ1)

- Estimand: unsourced-or-unlocatable claim rate (lower better); denominator =
  all audited claims. Confirmatory tests: none yet (power requires the human
  phase). Mandatory H0 if not rejected: the ledger does not reduce citation
  defects or review cost vs. the minimal checklist.

## 4. Related work (skeleton — to be filled with verified references only)
1. **Historiography & source criticism** — internal/external criticism
   traditions (Langlois & Seignobos; Vietnamese sử học practice and Quốc Sử
   Quán compilation norms).
   → cite verified editions only; no page invented.
2. **Digital humanities provenance** — named-graph/CRS provenance models
   (W3C PROV), cultural-heritage linked open data (Europeana data model),
   CC0 policy boundaries for metadata vs. objects.
3. **Scholarly citation-quality tooling** — citation-context classification,
   reference-resolution validators, retraction/erratum tracking.
4. **Educational content quality gates** — source-grounded curriculum
   publication gates (repo W02/W03 invariants), rubric-anchored review.
5. **Positioning:** P03 = tutor action policy; P11 = human scoring rubric;
   P09 = interface effectiveness; **P12 = source-verification process** (per
   portfolio collision rules). No other paper owns the source-audit ledger.

## 5. Method
See `research_v3/methods/p12/METHOD.md` (frozen). Summary: dataclasses
(Locator, SourceRecord, ClaimEntry, LedgerEvent), closed vocabularies
(stance/confidence_status/evidence_kind), V1–V5 fail-closed rules, append-only
SHA-256 chain over canonical JSON, C0/C1 baseline semantics, ABSTAIN ≠ REJECT.

## 6. (Blocked) Evaluation plan
- Human double-review protocol: `research_v3/methods/p12/P12_double_review.md`
  (BLOCKED, P12-T19).
- Registered metrics: verified-claim rate, unsupported claims, citation
  specificity, annotation agreement, editor time, conflict-resolution rate —
  **all UNMEASURED**; algorithmic proxies must not be reinterpreted as these
  human measures (spec §6).
- Current engineering smoke metrics (63 documented claims, read-only) ⧗
  `summary.json`: PROPOSED unsourced 0.0, locator-completeness 1.0,
  contradictions 0; 62/63 routed to ABSTAIN pending human verification;
  C1's blindness demonstrated by design (accepts unresolvable ids). These
  numbers validate the *apparatus*, not a pedagogical or historiographic claim.

## 7. Threats to validity (required)
- **No human archival verification yet:** every locator is inherited from the
  repo's documented registry; the apparatus cannot detect a plausible but
  wrong page number — precisely the defect class the blocked human phase
  targets. This is the paper's dominant internal-validity threat.
- **Single-collection smoke corpus:** external generalization unverified;
  HueSources/Europeana gates (rights snapshots, checksums) still BLOCKED.
- **Construct validity:** confidence statuses are inherited labels, not
  re-verified facts; ABSTAIN routing could mask corpus-wide defects if
  mistaken for assurance.
- **Statistical:** 63 claims, no powered test; 3 identical deterministic chain
  hashes are not independent replications.
- **Fabrication guardrails:** no page numbers, citations or archival
  permissions were invented; archives untouched; Wikidata used CC0-only with
  query+SHA provenance ⧗ `wikidata_probe.json`.

## 8. Data & code availability
- Apparatus: `research_v3/methods/p12/` (ledger, baselines, corpus adapter,
  wikidata probe, audit CLI); tests: `tests/research_v3/method/test_p12_*.py`.
- Artifacts: `research_artifacts_v3/runs/p12/` (prereg snapshot, ingest
  manifest with SHA-256 of every read-only input, per-arm manifests, chained
  `ledger.jsonl`, conflict log placeholder, summary).
- Blocked inputs: VN primary archives (rights), HueSources, Europeana
  (unverified terms) — see `dataset_cards.yaml`.

## 9. (Placeholder) Results tables — generated only from artifact files
Table 1: corpus ingest provenance ⧗ `ingest_manifest.json`.
Table 2: per-arm metrics ⧗ `summary.json` §metrics.
Table 3: contradiction/conflict log ⧗ `run_proposed` (currently empty — no
contradiction exists in the documented corpus; placeholder kept honestly).
Table 4 (BLOCKED): human agreement α — empty until P12-T19.

## 10. Ethics & integrity statements (BLOCKED)
Human annotation approval (P12-T19), novelty signoff (P12-T20), and
coauthor/venue signoff (P12-T21) are **not obtained**; the paper cannot leave
skeleton status. No simulated expert consensus appears anywhere in this packet.
