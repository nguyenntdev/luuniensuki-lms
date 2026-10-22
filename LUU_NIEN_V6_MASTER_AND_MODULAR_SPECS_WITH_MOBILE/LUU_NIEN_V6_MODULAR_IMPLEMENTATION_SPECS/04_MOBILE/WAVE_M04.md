# MOBILE DEVELOPMENT WAVE M04

> Đây là phần được tách từ `MOBILE_60_TICKET_ROADMAP.md` để Gemini chỉ cần mở nhóm source/route/ticket liên quan. Source lines được giữ nguyên.

## M04 — Grounded AI tutor, load, privacy and quality gates

**Prerequisite:** M03 + evidence approved + AIR phase gates.

| Slot | Ticket | Change | Authorized file scope | Blocker/negative test |
|---|---|---|---|---|
| A01 | `M04-A01` | AI tutor guarded UI | `mobile/lib/features/ai_chat/presentation/` | provider failure yields generic fact => FAIL |
| A02 | `M04-A02` | Bilingual VI/EN and Hán–Nôm display | `mobile/lib/features/history/ (new localization)` | inferred translation marked verified => FAIL |
| A03 | `M04-A03` | Citation drilldown | `mobile/lib/features/ai_chat/ (new citation widget)` | nonexistent source shown => FAIL |
| A04 | `M04-A04` | 3D performance and memory budget | `mobile/test/performance/ (new)` | unmeasured FPS claimed => FAIL |
| A05 | `M04-A05` | AI cost/cancel/error states | `mobile/lib/features/ai_chat/data/` | cost overrun or looping retry => FAIL |
| A06 | `M04-A06` | AI prompt injection validation | `tests/ai_security/mobile/ (new)` | source text overrides policy => BLOCKED |
| A07 | `M04-A07` | Reward/social abuse controls | `tests/gamification/ (new)` | reward replay => BLOCKED |
| A08 | `M04-A08` | Offline fault injection | `mobile/test/core/offline/ (new)` | duplicate mutated server => FAIL |
| A09 | `M04-A09` | Push integration test | `mobile/test/features/notifications/ (new)` | wrong account notify => FAIL |
| A10 | `M04-A10` | Threat model review and consent audit | `docs/mobile/security_review.md` | missing approval => BLOCKED |

### `M04-A01` — AI tutor guarded UI

- **Owner:** `mobile-m04-a01` separate worktree; **allowed scope:** `mobile/lib/features/ai_chat/presentation/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** ask/abstain/fail states. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** provider failure yields generic fact => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A01/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A02` — Bilingual VI/EN and Hán–Nôm display

- **Owner:** `mobile-m04-a02` separate worktree; **allowed scope:** `mobile/lib/features/history/ (new localization)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** reliable glyph/font and source attribution. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** inferred translation marked verified => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A02/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A03` — Citation drilldown

- **Owner:** `mobile-m04-a03` separate worktree; **allowed scope:** `mobile/lib/features/ai_chat/ (new citation widget)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** source passage navigation. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** nonexistent source shown => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A03/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A04` — 3D performance and memory budget

- **Owner:** `mobile-m04-a04` separate worktree; **allowed scope:** `mobile/test/performance/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** measured low-memory fallback. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** unmeasured FPS claimed => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A04/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A05` — AI cost/cancel/error states

- **Owner:** `mobile-m04-a05` separate worktree; **allowed scope:** `mobile/lib/features/ai_chat/data/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** 429/timeout/quota UI. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** cost overrun or looping retry => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A05/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A06` — AI prompt injection validation

- **Owner:** `mobile-m04-a06` separate worktree; **allowed scope:** `tests/ai_security/mobile/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** malicious source in tutor tests. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** source text overrides policy => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A06/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A07` — Reward/social abuse controls

- **Owner:** `mobile-m04-a07` separate worktree; **allowed scope:** `tests/gamification/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** server rate-limit/report/bypass checks. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** reward replay => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A07/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A08` — Offline fault injection

- **Owner:** `mobile-m04-a08` separate worktree; **allowed scope:** `mobile/test/core/offline/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** retry after ACK loss, conflict, kill. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** duplicate mutated server => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A08/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A09` — Push integration test

- **Owner:** `mobile-m04-a09` separate worktree; **allowed scope:** `mobile/test/features/notifications/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** token logout/revoke/quiet hours. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** wrong account notify => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A09/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M04-A10` — Threat model review and consent audit

- **Owner:** `mobile-m04-a10` separate worktree; **allowed scope:** `docs/mobile/security_review.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** test receipts by school, privacy, source. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** missing approval => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M04-A10/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

**Barrier M04:** merge sequentially, run `flutter analyze` + targeted widget/integration test + backend contract test, verify all 10 reported statuses and actual concurrency telemetry; no P0 exposed.

