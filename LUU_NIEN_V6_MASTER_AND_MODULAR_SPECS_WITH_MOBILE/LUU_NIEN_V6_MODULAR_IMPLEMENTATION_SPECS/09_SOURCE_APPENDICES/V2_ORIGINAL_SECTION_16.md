# V2 original archival technical chapter — SECTION_16

> Extracted without rewriting from V2 snapshot documentation, **not verified current code**.

## 16. ACCEPTANCE GATES, DOD, FAILURE POLICIES

### Gate G0 — Reality Check / Snapshot

- SHA and file manifest archived; branch name and commit SHA checked against actual Git history when available.
- `ci` on PR; all core services lock dependencies; disposable DB booted; migration branches analyzed.
- Every feature labeled `implemented`, `verified-by-test`, `pilot`, `proposal` or `blocked`.

### Gate G1 — Knowledge Integrity (BLOCKER)

- 9 urns and 162 reliefs reconciled against certified source; no duplicate/misaligned IDs.
- 100% published historical claims have source locator, named editor, rights status; all 162 initial AI seed records reviewed or withheld.
- Hán/Nôm names have verification status and do not silently appear as authoritative when unverified.

### Gate G2 — ELLO / Historical Inquiry

- At least 3 complete actual published ELLOs (geography, symbolism, comparison) with versions, answer artifacts and evidence rubric; one can be demonstrated offline/2D.
- Teacher can create/assign/score/review lesson; learner can revise; source packet remains frozen for each attempt.
- No statement “historical reasoning improved” without a proper study.

### Gate G3 — Accessible Multi-Device

- Source/lesson accessible with only 2D, keyboard and slow connection; 3D fallback tested.
- No unauthorized content leaks; multilingual source statuses visible.

### Gate G4 — Rights, Consent and Commercial Honesty

- Zero false inquiry acknowledgment when backend fails; zero sample partner records in production; consent revocation works on public routes and caches; RBPC claims supported.

### Gate G5 — AI Trustworthiness

- Corpus snapshot + human-graded gold evaluation + regression suite; coverage/accuracy/abstention, failure examples openly tracked. No “zero-hallucination” advertising absent impossible proof.

### Gate G6 — Research Reproducibility

- Pseudonymized Forms input, questionnaire/version, script export, all tables reproduced, disclosure of limitations, ethics/permissions verified.

### Gate G7 — Publication / Conference Evidence

- Each paper has unique question/contribution, supporting evidence and overlap declaration; posters/abstract/full paper do not inflate claims.

### Gate G8 — Operations

- Build all components, migration single-head strategy proven, backups restored, smoke tests pass, observability and SLO thresholds measured, rollback practiced.

### Definition of Done per ticket

Requirement mapped → code → unit test → integration test → security check → data migration/rollback if relevant → UX accessibility → docs/runbook → source/rights/research status → reviewer signoff. Không nghiệm thu “done” bằng README hoặc screenshot đơn lẻ.

---

