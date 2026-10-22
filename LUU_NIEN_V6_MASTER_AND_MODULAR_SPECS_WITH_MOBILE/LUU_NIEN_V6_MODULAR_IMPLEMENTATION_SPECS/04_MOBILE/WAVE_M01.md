# MOBILE DEVELOPMENT WAVE M01

> Đây là phần được tách từ `MOBILE_60_TICKET_ROADMAP.md` để Gemini chỉ cần mở nhóm source/route/ticket liên quan. Source lines được giữ nguyên.

## M01 — Core auth, typed networking, offline durability

**Prerequisite:** M00 + backend contract owners.

| Slot | Ticket | Change | Authorized file scope | Blocker/negative test |
|---|---|---|---|---|
| A01 | `M01-A01` | Token refresh single-flight implementation | `mobile/lib/core/network/interceptors/token_refresh_interceptor.dart` | 401 storm multiple refresh => FAIL |
| A02 | `M01-A02` | Flavored API config | `mobile/lib/core/constants/api_constants.dart` | hardcoded prod on staging => FAIL |
| A03 | `M01-A03` | Child/guardian consent gates | `mobile/lib/features/auth/ (new consent module)` | minor bypasses consent => BLOCKED |
| A04 | `M01-A04` | Per-user encrypted cache keys | `mobile/lib/core/storage/secure_storage.dart` | A data appears for B => FAIL |
| A05 | `M01-A05` | Server offline-sync API owner contract | `backend/routers/ (owner creates new route only if missing)` | duplicate offline commit => FAIL |
| A06 | `M01-A06` | Outbox local schema migration | `mobile/lib/core/offline/offline_queue_service.dart` | app crash loses acknowledged state => FAIL |
| A07 | `M01-A07` | Offline retry conflict controller | `mobile/lib/core/offline/ (new file, not queue service)` | silent overwrite => FAIL |
| A08 | `M01-A08` | Session/identity instrumentation tests | `mobile/test/features/auth/ (new tests)` | session leaked => BLOCKED |
| A09 | `M01-A09` | Network error and request id UX | `mobile/lib/core/errors/` | 500 presented as success => FAIL |
| A10 | `M01-A10` | Auth API contract integration tests | `tests/mobile_contracts/ (new backend tests)` | client role bypass => BLOCKED |

### `M01-A01` — Token refresh single-flight implementation

- **Owner:** `mobile-m01-a01` separate worktree; **allowed scope:** `mobile/lib/core/network/interceptors/token_refresh_interceptor.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** one refresh, replay-safe requests. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** 401 storm multiple refresh => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A01/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A02` — Flavored API config

- **Owner:** `mobile-m01-a02` separate worktree; **allowed scope:** `mobile/lib/core/constants/api_constants.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** staging/prod HTTPS routing and fail build. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** hardcoded prod on staging => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A02/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A03` — Child/guardian consent gates

- **Owner:** `mobile-m01-a03` separate worktree; **allowed scope:** `mobile/lib/features/auth/ (new consent module)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** consent UX, role-scoped state. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** minor bypasses consent => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A03/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A04` — Per-user encrypted cache keys

- **Owner:** `mobile-m01-a04` separate worktree; **allowed scope:** `mobile/lib/core/storage/secure_storage.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** namespaced lifecycle/logout purge. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** A data appears for B => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A04/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A05` — Server offline-sync API owner contract

- **Owner:** `mobile-m01-a05` separate worktree; **allowed scope:** `backend/routers/ (owner creates new route only if missing)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** validated per-item sync + ACL + idempotency. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** duplicate offline commit => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A05/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A06` — Outbox local schema migration

- **Owner:** `mobile-m01-a06` separate worktree; **allowed scope:** `mobile/lib/core/offline/offline_queue_service.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** versioned encrypted durable queue. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** app crash loses acknowledged state => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A06/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A07` — Offline retry conflict controller

- **Owner:** `mobile-m01-a07` separate worktree; **allowed scope:** `mobile/lib/core/offline/ (new file, not queue service)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** 409 flow and exponential backoff. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** silent overwrite => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A07/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A08` — Session/identity instrumentation tests

- **Owner:** `mobile-m01-a08` separate worktree; **allowed scope:** `mobile/test/features/auth/ (new tests)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** logout/login+token expiry negative suite. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** session leaked => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A08/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A09` — Network error and request id UX

- **Owner:** `mobile-m01-a09` separate worktree; **allowed scope:** `mobile/lib/core/errors/`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** typed transient/perm errors with trace id. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** 500 presented as success => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A09/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M01-A10` — Auth API contract integration tests

- **Owner:** `mobile-m01-a10` separate worktree; **allowed scope:** `tests/mobile_contracts/ (new backend tests)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** 2-tenant unauthorized test fixtures. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** client role bypass => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M01-A10/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

**Barrier M01:** merge sequentially, run `flutter analyze` + targeted widget/integration test + backend contract test, verify all 10 reported statuses and actual concurrency telemetry; no P0 exposed.

