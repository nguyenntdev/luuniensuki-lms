# P12 double human-review protocol — TEMPLATE, EXECUTION BLOCKED (P12-T19)

**Status: `BLOCKED — awaiting real expert reviewers and archival access
approval. No simulated reviewers, no synthetic consensus, ever.**

## Purpose (spec §3)
Two independent experts compare each ledger claim against the primary source
(anchor → kỷ/quyển/page) and record agreement, disagreement and any correction.
This protocol operationalizes the "chuyên gia đối chiếu và ghi bất đồng/chỉnh
sửa" requirement. It cannot be executed by code.

## Reviewer requirements (all mandatory, all currently missing)
1. Two named human reviewers with documented Vietnamese historiography /
   Hán–Nôm competence. Pseudonymous IDs assigned *in scoring code*; real
   identities stay private (ETHICS_AND_INTEGRITY §4).
2. Archival access permission for the cited editions (ĐNTL, HĐSL, ĐNNTC,
   Châu bản) — the same permission that keeps automated ingestion BLOCKED.
3. A signed ethics/permission record (P12-T19) before any ratings are collected.

## Procedure (to execute only after unblocking)
For every claim in the frozen audit corpus:
1. Reviewer A reads the claim text and opens the cited locator *independently*.
2. Reviewer A records: `supports | refutes | cannot_locate | page_mismatch`
   plus free-text note. No visibility into Reviewer B's judgement.
3. Reviewer B repeats, also blind.
4. Agreement recorded with Krippendorff α (nominal) — computed via
   `research_v3/eval/statistics.py` family functions; assumptions documented.
5. Conflicts resolved in a third adjudication session; original decisions and
   timestamps preserved immutably (appended to the ledger as `annotate`
   events — never rewritten).
6. Every correction becomes a **new** ledger annotation; history stays
   append-only and hash-chained.

## Outputs when executed (none exist yet)
- `research_artifacts_v3/runs/p12/human_review/ratings.csv` (pseudonymous)
- `research_artifacts_v3/runs/p12/human_review/agreement.json` (α, CI)
- `research_artifacts_v3/runs/p12/human_review/adjudication_log.jsonl`

## Explicit non-goals until unblocked
- No "expert consensus" may be fabricated for the manuscript.
- No archival page number may be typed in from memory or from secondary web
  pages — locators come from the archival object itself.
- Metrics that depend on ratings (verified-claim rate, annotation agreement,
  editor time, conflict-resolution rate) remain UNMEASURED, reported as
  BLOCKED in every results table.
