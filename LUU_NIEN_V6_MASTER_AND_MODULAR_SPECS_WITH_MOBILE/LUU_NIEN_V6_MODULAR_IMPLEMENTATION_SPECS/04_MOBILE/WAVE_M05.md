# MOBILE DEVELOPMENT WAVE M05

> Đây là phần được tách từ `MOBILE_60_TICKET_ROADMAP.md` để Gemini chỉ cần mở nhóm source/route/ticket liên quan. Source lines được giữ nguyên.

## M05 — Startup visitor journeys + stores release

**Prerequisite:** M04 + legal/partner approvals.

| Slot | Ticket | Change | Authorized file scope | Blocker/negative test |
|---|---|---|---|---|
| A01 | `M05-A01` | Heritage passport verified stamps | `mobile/lib/features/passport/ (new)` | replayed stamp => FAIL |
| A02 | `M05-A02` | QR verification and replay defense | `mobile/lib/features/passport/data/ (new)` | arbitrary QR creates reward => BLOCKED |
| A03 | `M05-A03` | Experience listings | `mobile/lib/features/experiences/ (new)` | fabricated partner => FAIL |
| A04 | `M05-A04` | True server inquiry + status | `mobile/lib/features/experiences/data/ (new)` | backend 503 claimed confirmed => FAIL |
| A05 | `M05-A05` | Partner notification hook | `backend/services/ (approved owner)` | no persisted event => FAIL |
| A06 | `M05-A06` | Product traction event evidence | `docs/startup/ (new metric dictionary)` | mock metrics included pitch => BLOCKED |
| A07 | `M05-A07` | Real classroom/visitor pilot plan | `docs/pilot/ (new)` | self-report claimed knowledge gain => FAIL |
| A08 | `M05-A08` | Privacy/right-to-delete signoff | `docs/privacy/ (new)` | unverified policy => BLOCKED |
| A09 | `M05-A09` | Gemini 10-agent test and UAT pack | `tests/release_acceptance/ (new)` | unchecked blocker => FAIL |
| A10 | `M05-A10` | Android/iOS release evidence, handoff | `docs/mobile/release/ (new)` | debug signed/iOS absent => BLOCKED |

### `M05-A01` — Heritage passport verified stamps

- **Owner:** `mobile-m05-a01` separate worktree; **allowed scope:** `mobile/lib/features/passport/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** signed stamp, no fake visits. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** replayed stamp => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A01/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A02` — QR verification and replay defense

- **Owner:** `mobile-m05-a02` separate worktree; **allowed scope:** `mobile/lib/features/passport/data/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** signed/expiry/nonce evidence. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** arbitrary QR creates reward => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A02/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A03` — Experience listings

- **Owner:** `mobile-m05-a03` separate worktree; **allowed scope:** `mobile/lib/features/experiences/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** verified partner inventory only. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** fabricated partner => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A03/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A04` — True server inquiry + status

- **Owner:** `mobile-m05-a04` separate worktree; **allowed scope:** `mobile/lib/features/experiences/data/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** partner-scope transaction and receipt. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** backend 503 claimed confirmed => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A04/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A05` — Partner notification hook

- **Owner:** `mobile-m05-a05` separate worktree; **allowed scope:** `backend/services/ (approved owner)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** inquiry events true inbox. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** no persisted event => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A05/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A06` — Product traction event evidence

- **Owner:** `mobile-m05-a06` separate worktree; **allowed scope:** `docs/startup/ (new metric dictionary)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** first-party events, no synthetic conversion. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** mock metrics included pitch => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A06/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A07` — Real classroom/visitor pilot plan

- **Owner:** `mobile-m05-a07` separate worktree; **allowed scope:** `docs/pilot/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** consent, objective and outcome protocol. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** self-report claimed knowledge gain => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A07/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A08` — Privacy/right-to-delete signoff

- **Owner:** `mobile-m05-a08` separate worktree; **allowed scope:** `docs/privacy/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** consent, rights, deletion cascade. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** unverified policy => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A08/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A09` — Gemini 10-agent test and UAT pack

- **Owner:** `mobile-m05-a09` separate worktree; **allowed scope:** `tests/release_acceptance/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** smoke/rbac/mobile cross-stack. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** unchecked blocker => FAIL. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A09/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

### `M05-A10` — Android/iOS release evidence, handoff

- **Owner:** `mobile-m05-a10` separate worktree; **allowed scope:** `docs/mobile/release/ (new)`. Other shared files are read-only until coordinator merge approves.
- **Read first:** `MASTER_SPEC.md`, `04_MOBILE/MOBILE_MASTER_SPEC.md`, relevant mobile domain spec, this ticket, then at most 3–8 directly related files in ZIP checkout. Confirm file/path existence before editing.
- **Objective / change:** Play AAB + TestFlight proof or NOT_RUN. Never substitute a UI-only mock for backend persistence, rights, auth or validated source.
- **Minimal test-first approach:** reproduce one real failure, write fixture and failing regression test, change narrow module, compile/analyze, test positive and negative, produce screenshot/receipt for the new state.
- **Mandatory negative acceptance:** debug signed/iOS absent => BLOCKED. Failure means `FAIL` or `BLOCKED`, not PASS.
- **Cross-stack check:** if API/schema/migration change required, create typed proposal + backend test; backend owner merges contract before Flutter client compiles. Don't edit another agent's source files.
- **Output artifact:** `artifacts/implementation/M05-A10/HANDOFF.json` containing `source_sha,modified_paths,tests[cmd,exit_code,stdout_path],negative_case,status,request_ids,unresolved_issues`, with no student PII.
- **Exit:** complete when relevant server data persists through restart, survives role-scoped auth and error injection, and Flutter client displays exact server state; platform tests labeled PASS/FAIL/NOT_RUN honestly.

**Barrier M05:** merge sequentially, run `flutter analyze` + targeted widget/integration test + backend contract test, verify all 10 reported statuses and actual concurrency telemetry; no P0 exposed.

## Final mobile integration gates

- Link to corresponding V5 W05 tickets and ensure no duplicate divergent implementation for authentication/offline/quests.
- Nondestructive rollback and staged release only after signing and compliance reviewed.
- Web/mobile both use one stable API contract and one authoritative source and learning schema.
- Source pack hash, code commit SHA, release artifact hashes, privacy evidence and tested device matrices signed by release owner.
