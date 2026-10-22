# MOBILE DEVELOPMENT WAVE M00

> Đây là phần được tách từ `MOBILE_60_TICKET_ROADMAP.md` để Gemini chỉ cần mở nhóm source/route/ticket liên quan. Source lines được giữ nguyên.

## M00 — Preflight, true baseline, build and contracts

**Prerequisite:** W00 + Mobile Master.

| Slot | Ticket | Change | Authorized file scope | Blocker/negative test |
|---|---|---|---|---|
| A01 | `M00-A01` | Repository pin & mobile dependency report | `docs/mobile/audit.md` | Invalid source ZIP provenance => BLOCKED |
| A02 | `M00-A02` | API spec registry & client DTO owner | `mobile/lib/core/network/api_client.dart` | incompatible OpenAPI => CI fails |
| A03 | `M00-A03` | Navigation + placeholder route audit | `mobile/lib/routing/app_router.dart` | active Quest route skeleton => FAIL |
| A04 | `M00-A04` | Android release signing fail-closed | `mobile/android/app/build.gradle` | release debug-signed => BLOCKED |
| A05 | `M00-A05` | Offline backend endpoint contract inventory | `backend/routers/ (read only), docs/mobile/offline_sync_contract.md` | wrong route assumed implemented => BLOCKED |
| A06 | `M00-A06` | Flutter unit/widget baseline | `mobile/test/ (new isolated test file)` | tests unavailable => NOT_RUN not PASS |
| A07 | `M00-A07` | iOS platform preflight (planning only) | `docs/mobile/ios_platform_plan.md` | claim iOS-ready before created => FAIL |
| A08 | `M00-A08` | Mock/fake-success source scan | `docs/mobile/mobile_mock_registry.md` | unmarked prod mock => BLOCKED |
| A09 | `M00-A09` | Privacy and minormode threat review | `docs/mobile/child_privacy_model.md` | PII to LLM => BLOCKED |
| A10 | `M00-A10` | Mobile dev/staging sandbox boot plan | `docs/mobile/mobile_env_bootstrap.md` | script touches prod => FAIL |

### `M00-A01` — Repository pin & mobile dependency report

- **Owner:** `mobile-m00-a01` separate worktree; **allowed scope:** `docs/mobile/audit.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** git SHA/flutter version, feature inventory. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** Invalid source ZIP provenance => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A01/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A02` — API spec registry & client DTO owner

- **Owner:** `mobile-m00-a02` separate worktree; **allowed scope:** `mobile/lib/core/network/api_client.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** generated client contract plan + drift check. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** incompatible OpenAPI => CI fails. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A02/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A03` — Navigation + placeholder route audit

- **Owner:** `mobile-m00-a03` separate worktree; **allowed scope:** `mobile/lib/routing/app_router.dart`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** route list with active placeholder tests. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** active Quest route skeleton => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A03/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A04` — Android release signing fail-closed

- **Owner:** `mobile-m00-a04` separate worktree; **allowed scope:** `mobile/android/app/build.gradle`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** missing-keystore release fails. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** release debug-signed => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A04/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A05` — Offline backend endpoint contract inventory

- **Owner:** `mobile-m00-a05` separate worktree; **allowed scope:** `backend/routers/ (read only), docs/mobile/offline_sync_contract.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** route present/absent finding, API proposal. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** wrong route assumed implemented => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A05/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A06` — Flutter unit/widget baseline

- **Owner:** `mobile-m00-a06` separate worktree; **allowed scope:** `mobile/test/ (new isolated test file)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** existing tests run/report. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** tests unavailable => NOT_RUN not PASS. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A06/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A07` — iOS platform preflight (planning only)

- **Owner:** `mobile-m00-a07` separate worktree; **allowed scope:** `docs/mobile/ios_platform_plan.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** macOS/team/entitlements prerequisites. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** claim iOS-ready before created => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A07/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A08` — Mock/fake-success source scan

- **Owner:** `mobile-m00-a08` separate worktree; **allowed scope:** `docs/mobile/mobile_mock_registry.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** enumerated mock call sites and classification. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** unmarked prod mock => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A08/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A09` — Privacy and minormode threat review

- **Owner:** `mobile-m00-a09` separate worktree; **allowed scope:** `docs/mobile/child_privacy_model.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** user/role data flow, consent scopes. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** PII to LLM => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A09/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M00-A10` — Mobile dev/staging sandbox boot plan

- **Owner:** `mobile-m00-a10` separate worktree; **allowed scope:** `docs/mobile/mobile_env_bootstrap.md`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** repro startup config, no prod DB. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** script touches prod => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M00-A10/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

**Barrier M00:** merge sequentially, run `flutter analyze` + targeted widget/integration test + backend contract test, verify all 10 reported statuses and actual concurrency telemetry; no P0 exposed.

