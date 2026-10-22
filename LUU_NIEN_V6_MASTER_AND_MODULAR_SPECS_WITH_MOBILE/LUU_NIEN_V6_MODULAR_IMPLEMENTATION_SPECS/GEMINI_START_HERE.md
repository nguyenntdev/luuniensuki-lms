# GEMINI START HERE — LƯU NIÊN V6 EXECUTION PROTOCOL

> This file is a **small loader prompt**, not permission to implement everything. Run with the user-authorized coding environment and repository checkout. The 10-subagent requirement is about observed physical concurrency, not merely outputting 10 plans. Preserve code/source truth, privacy and human historical approval.

## Session initialization — one-time

1. Read `MASTER_SPEC.md`; then select **exactly one** target ticket (`V5-Txxx`, `AIR-xxx` or `Mxx-Ayy`) from the relevant wave file. Never preload `99_ARCHIVE/V5_FULL_UNMODIFIED_SOURCE.md` into the model context.
2. Verify `git status`, actual branch `feat/rbpc-cultural-bridge-2026` or a pinned descendant, commit SHA and `AGENTS.md`. ZIP by itself has no trustworthy commit SHA; do not invent one.
3. Record `SOURCE_LOCK.json`: Git SHA, dependency lockfile digests, source paths, API/schema contract version, environment (disposable DB/staging only), test tool versions.
4. Identify whether paths in ticket actually exist; `[TARGET]` means to be built only after baseline scan and typed interface approval.
5. Pick one domain file, one exact ticket and at most 3–8 code files. Map web/Flutter/gateway/FastAPI/DB blast radius before changing code.
6. Write negative regression tests first, implement minimal safe diff, verify typed contracts, test and record logs; no runtime mock-success, speculative historical source, unapproved source rights or student PII in prompts.
7. Emit handoff JSON and stop; coordinator integrates shared code sequentially, approves next ticket.

## Single-ticket command template to issue to Gemini Flash

```text
ROLE: Luu Nien production coding implementer.
READ ONLY: MASTER_SPEC.md, one designated V6 domain spec, one designated ticket, at most eight verified repository source files.
TARGET TICKET: <V5-Txxx | AIR-xxx | Mxx-Ayy>.
BASELINE SOURCE SHA: <must verify; never invent>.
IMPLEMENTATION SCOPE: <owner approved paths>. No unrelated refactor or rewriting the repository.
WORKFLOW: (1) inspect current routes/models/clients, (2) list blockers, (3) failing regression test, (4) narrow patch, (5) scoped test and negative failures, (6) full compatibility test, (7) handoff JSON, then STOP.
BLOCKED IF: provider/source rights, Hán–Nôm validation, child-data consent, signing, API owner, irreversible migration or authentication cannot be verified.
NEVER: claim NOT_RUN tests passed; let Android release sign with debug key; infer iOS exists; fabricate grades/booking/citations/traction; approve historical content on behalf of a human.
OUTPUT: files changed with line references, migration/API diff, commands and exit codes, negative cases, risks, rollback steps, status PASS/FAIL/BLOCKED/NOT_RUN and next dependency.
```

## 10 concurrent subagents packet

```text
COORDINATOR: Spawn exactly ten logically distinct task envelopes for *one* Pxx historical phase, one Wxx engineering wave, or one Mxx mobile wave. Schedule with actual worker concurrency capped globally at ten; record run start/end times and worker overlap. If infrastructure permits fewer physical parallel calls, report CAPACITY_BLOCKED rather than claiming true concurrent execution.
ISOLATION: Separate worktrees/branches and edit scopes; all shared Alembic migrations, API/generated types and app router integration controlled by a single owner. Research agents write immutable artifacts and claim/source refs; never directly publish historical content.
BARRIER: Wait until all ten jobs reach terminal state. Failures require retry/reconciliation; must not silently advance to next phase. Coordinator merges independently reviewed patches sequentially; run integrated test suite and human signoffs.
OUTPUT: {wave_or_phase_id, ten_slots:[{id,source_sha,started_at,finished_at,modified_files,artifact_hash,tests,status}], observed_peak_concurrency, barriers_passed, approvals, blockers}.
```

## Choose your entry point

- Fix fake-success / mock: `01_CORE/V5_03_MOCK_AUDIT.md` → `07_DELIVERY/W00_10_CONCURRENT_DEVELOPMENT_AGENTS.md` then W01.
- Complete Flutter: `04_MOBILE/MOBILE_MASTER_SPEC.md` → `04_MOBILE/MOBILE_SOURCE_AUDIT.md` → M00/M01 wave document.
- Historical source pipeline: `03_AI_FACTORY/V3_C02_FACTORY_ARCHITECTURE.md` → a single `03_AI_FACTORY/PHASE_Pxx_TEN_RESEARCH_AGENTS.md` → corresponding AIR ticket group.
- Startup evidence: `05_CROSS_PLATFORM/PRODUCT_PRODUCTION_AND_STARTUP_GATES.md`; never replace user validation with presentation claims.

## Completion declaration

`SPEC_READY` means documentation built. `IMPLEMENTED` requires code diff. `PRODUCTION_READY` requires rollback, signed builds where applicable, real DB and backend tests, privacy/rights signoffs and independent pilot evidence. Distinguish these states in all handoffs.
