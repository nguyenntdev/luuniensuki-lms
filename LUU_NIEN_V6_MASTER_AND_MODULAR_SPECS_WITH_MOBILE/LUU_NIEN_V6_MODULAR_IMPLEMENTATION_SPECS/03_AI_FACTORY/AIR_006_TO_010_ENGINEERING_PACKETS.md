# AIR-006..AIR-010 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-006` — Add idempotency keys + leases + DLQ

**Priority:** `P0`. **Dependencies:** `AIR-003`. **Planned code boundary:** `backend/services/research_factory/queues.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `queue`.

**Implementation outcome:** retry never double writes claims. **Prevent regression:** CONC-005/006.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-006` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Add idempotency keys + leases + DLQ” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-005/006”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/queues.py` or the verified actual module. Focus: Persistent leases/idempotency. Prove claim transaction concurrency and resume after worker SIGKILL. No in-memory-only production state.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-006` contract tests, verify positive scenario “retry never double writes claims”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_006_happy`: valid authorized fixture reaches `retry never double writes claims`.

- `test_air_006_negative`: `CONC-005/006` is blocked deterministically.

- `test_air_006_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_006_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_006_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-003`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-006 ONLY. Goal: Add idempotency keys + leases + DLQ. Target: backend/services/research_factory/queues.py. Deps: AIR-003. Tests: retry never double writes claims; block CONC-005/006. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-007` — Implement private immutable artifacts+hashes

**Priority:** `P0`. **Dependencies:** `AIR-002`. **Planned code boundary:** `backend/services/research_factory/artifacts.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `runner`.

**Implementation outcome:** mutations create new SHA objects. **Prevent regression:** tamper/hash test.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-007` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Implement private immutable artifacts+hashes” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “tamper/hash test”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/artifacts.py` or the verified actual module. Focus: Implement hidden infrastructure API behind feature flag, no public endpoint; create strict Pydantic schemas, file-scoped tests.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-007` contract tests, verify positive scenario “mutations create new SHA objects”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_007_happy`: valid authorized fixture reaches `mutations create new SHA objects`.

- `test_air_007_negative`: `tamper/hash test` is blocked deterministically.

- `test_air_007_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_007_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_007_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-002`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-007 ONLY. Goal: Implement private immutable artifacts+hashes. Target: backend/services/research_factory/artifacts.py. Deps: AIR-002. Tests: mutations create new SHA objects; block tamper/hash test. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-008` — Admin RBAC and audit for research factory

**Priority:** `P0`. **Dependencies:** `AIR-002`. **Planned code boundary:** `backend/routers/research_factory.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `ui`.

**Implementation outcome:** nonstaff denied; per-scope access. **Prevent regression:** IDOR/role matrix.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-008` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Admin RBAC and audit for research factory” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “IDOR/role matrix”; run it to capture pre-fix failure.

5. Implement target in `backend/routers/research_factory.py` or the verified actual module. Focus: Admin-only route with RBAC; typed API hooks; loading/empty/error/blocked/permission states; keyboard accessibility.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-008` contract tests, verify positive scenario “nonstaff denied; per-scope access”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_008_happy`: valid authorized fixture reaches `nonstaff denied; per-scope access`.

- `test_air_008_negative`: `IDOR/role matrix` is blocked deterministically.

- `test_air_008_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_008_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_008_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-002`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-008 ONLY. Goal: Admin RBAC and audit for research factory. Target: backend/routers/research_factory.py. Deps: AIR-002. Tests: nonstaff denied; per-scope access; block IDOR/role matrix. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-009` — Rate and cost accounting

**Priority:** `P0`. **Dependencies:** `AIR-005`. **Planned code boundary:** `backend/services/research_factory/budget.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `provider`.

**Implementation outcome:** hard stop at configured budget. **Prevent regression:** quota simulation.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-009` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Rate and cost accounting” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “quota simulation”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/budget.py` or the verified actual module. Focus: Adapter with fake/mock implementation for tests; explicit quota, timeout, policy, provider model ID and structured response validation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-009` contract tests, verify positive scenario “hard stop at configured budget”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_009_happy`: valid authorized fixture reaches `hard stop at configured budget`.

- `test_air_009_negative`: `quota simulation` is blocked deterministically.

- `test_air_009_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_009_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_009_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-005`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-009 ONLY. Goal: Rate and cost accounting. Target: backend/services/research_factory/budget.py. Deps: AIR-005. Tests: hard stop at configured budget; block quota simulation. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-010` — Ten-lane frontend dashboard

**Priority:** `P1`. **Dependencies:** `AIR-004, AIR-008`. **Planned code boundary:** `frontend/src/app/admin/research-factory/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `ui`.

**Implementation outcome:** dispatched and actually running separate. **Prevent regression:** playwright accessibility.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-010` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Ten-lane frontend dashboard” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “playwright accessibility”; run it to capture pre-fix failure.

5. Implement target in `frontend/src/app/admin/research-factory/` or the verified actual module. Focus: Admin-only route with RBAC; typed API hooks; loading/empty/error/blocked/permission states; keyboard accessibility.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-010` contract tests, verify positive scenario “dispatched and actually running separate”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_010_happy`: valid authorized fixture reaches `dispatched and actually running separate`.

- `test_air_010_negative`: `playwright accessibility` is blocked deterministically.

- `test_air_010_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_010_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_010_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-004, AIR-008`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-010 ONLY. Goal: Ten-lane frontend dashboard. Target: frontend/src/app/admin/research-factory/. Deps: AIR-004, AIR-008. Tests: dispatched and actually running separate; block playwright accessibility. Follow V4.0–V4.4 and V4.10. Never deploy.`

