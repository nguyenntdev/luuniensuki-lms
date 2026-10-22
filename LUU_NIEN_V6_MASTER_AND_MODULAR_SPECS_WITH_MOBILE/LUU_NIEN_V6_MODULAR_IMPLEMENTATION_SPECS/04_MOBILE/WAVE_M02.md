# MOBILE DEVELOPMENT WAVE M02

> Đây là phần được tách từ `MOBILE_60_TICKET_ROADMAP.md` để Gemini chỉ cần mở nhóm source/route/ticket liên quan. Source lines được giữ nguyên.

## M02 — Verified heritage + media + complete game functionality

**Prerequisite:** M01 + sources approved.

| Slot | Ticket | Change | Authorized file scope | Blocker/negative test |
|---|---|---|---|---|
| A01 | `M02-A01` | Relief/urn DTO and read repo | `mobile/lib/features/explore/` | draft displayed as verified => BLOCKED |
| A02 | `M02-A02` | Citation, claim source viewer | `mobile/lib/features/history/` | fake citation => BLOCKED |
| A03 | `M02-A03` | Offline verified heritage cache | `mobile/lib/features/collection/` | revoked source still public => FAIL |
| A04 | `M02-A04` | Media asset manifests | `mobile/lib/features/urn_viewer/data/ (new)` | expired signed URL reused => FAIL |
| A05 | `M02-A05` | 3D load and accessibility fallback | `mobile/lib/features/urn_viewer/presentation/` | GLB fail black screen => FAIL |
| A06 | `M02-A06` | AR capability checks | `mobile/lib/features/urn_viewer/ (new AR module)` | forced camera => FAIL |
| A07 | `M02-A07` | Replace runtime mock practice | `mobile/lib/features/practice/` | MockQuizData real flow => FAIL |
| A08 | `M02-A08` | Quest route and real completion | `mobile/lib/features/learning_path/` | placeholder Quest in production => FAIL |
| A09 | `M02-A09` | Server wallet and reward ledger UI | `mobile/lib/features/gems/ (or hearts)` | forged balance accepted => BLOCKED |
| A10 | `M02-A10` | Privacy-safe friends actions | `mobile/lib/features/social/` | demo identity in live friends => FAIL |

### `M02-A01` — Relief/urn DTO and read repo

- **Owner:** `mobile-m02-a01` separate worktree; **allowed scope:** `mobile/lib/features/explore/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** 9×18 catalog verified revision. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** draft displayed as verified => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A01/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A02` — Citation, claim source viewer

- **Owner:** `mobile-m02-a02` separate worktree; **allowed scope:** `mobile/lib/features/history/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** source passage exact locator. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** fake citation => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A02/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A03` — Offline verified heritage cache

- **Owner:** `mobile-m02-a03` separate worktree; **allowed scope:** `mobile/lib/features/collection/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** rights-safe cache versioned. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** revoked source still public => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A03/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A04` — Media asset manifests

- **Owner:** `mobile-m02-a04` separate worktree; **allowed scope:** `mobile/lib/features/urn_viewer/data/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** asset SHA, license, hotspots contract. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** expired signed URL reused => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A04/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A05` — 3D load and accessibility fallback

- **Owner:** `mobile-m02-a05` separate worktree; **allowed scope:** `mobile/lib/features/urn_viewer/presentation/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** 2D fallback on load fail. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** GLB fail black screen => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A05/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A06` — AR capability checks

- **Owner:** `mobile-m02-a06` separate worktree; **allowed scope:** `mobile/lib/features/urn_viewer/ (new AR module)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** capability/provider permissions. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** forced camera => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A06/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A07` — Replace runtime mock practice

- **Owner:** `mobile-m02-a07` separate worktree; **allowed scope:** `mobile/lib/features/practice/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** real question/due server model. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** MockQuizData real flow => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A07/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A08` — Quest route and real completion

- **Owner:** `mobile-m02-a08` separate worktree; **allowed scope:** `mobile/lib/features/learning_path/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** Quest screens with backend state. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** placeholder Quest in production => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A08/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A09` — Server wallet and reward ledger UI

- **Owner:** `mobile-m02-a09` separate worktree; **allowed scope:** `mobile/lib/features/gems/ (or hearts)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** never client authoritative XP/gems. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** forged balance accepted => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A09/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M02-A10` — Privacy-safe friends actions

- **Owner:** `mobile-m02-a10` separate worktree; **allowed scope:** `mobile/lib/features/social/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** empty/friends/blocked/report server state. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** demo identity in live friends => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M02-A10/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

**Barrier M02:** merge sequentially, run `flutter analyze` + targeted widget/integration test + backend contract test, verify all 10 reported statuses and actual concurrency telemetry; no P0 exposed.

