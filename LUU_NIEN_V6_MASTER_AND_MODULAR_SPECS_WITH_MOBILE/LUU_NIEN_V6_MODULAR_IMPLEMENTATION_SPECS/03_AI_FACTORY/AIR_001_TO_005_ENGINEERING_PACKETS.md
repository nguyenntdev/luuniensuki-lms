# AIR-001..AIR-005 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-001` — Create durable pipeline domain package

**Priority:** `P0`. **Dependencies:** `R0-006`. **Planned code boundary:** `backend/services/research_factory/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `runner`.

**Implementation outcome:** Run manifests and agent roles pinned. **Prevent regression:** schema and unit.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-001` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Create durable pipeline domain package” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “schema and unit”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/` or the verified actual module. Focus: Implement hidden infrastructure API behind feature flag, no public endpoint; create strict Pydantic schemas, file-scoped tests.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-001` contract tests, verify positive scenario “Run manifests and agent roles pinned”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_001_happy`: valid authorized fixture reaches `Run manifests and agent roles pinned`.

- `test_air_001_negative`: `schema and unit` is blocked deterministically.

- `test_air_001_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_001_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_001_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `R0-006`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-001 ONLY. Goal: Create durable pipeline domain package. Target: backend/services/research_factory/. Deps: R0-006. Tests: Run manifests and agent roles pinned; block schema and unit. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-002` — Add Alembic run/phase/job migrations

**Priority:** `P0`. **Dependencies:** `AIR-001`. **Planned code boundary:** `migrations/versions/` [EXISTS]. **Category:** `db`.

**Implementation outcome:** 10-slot constraints and foreign keys pass. **Prevent regression:** migration forward/back.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-002` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Add Alembic run/phase/job migrations” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “migration forward/back”; run it to capture pre-fix failure.

5. Implement target in `migrations/versions/` or the verified actual module. Focus: Inspect actual Alembic revision graph; write add-only PostgreSQL migration under migrations/versions; register models through backend.models; fresh/upgraded DB tests.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-002` contract tests, verify positive scenario “10-slot constraints and foreign keys pass”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_002_happy`: valid authorized fixture reaches `10-slot constraints and foreign keys pass`.

- `test_air_002_negative`: `migration forward/back` is blocked deterministically.

- `test_air_002_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_002_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_002_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-001`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-002 ONLY. Goal: Add Alembic run/phase/job migrations. Target: migrations/versions/. Deps: AIR-001. Tests: 10-slot constraints and foreign keys pass; block migration forward/back. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-003` — Implement broker+worker engine selection ADR

**Priority:** `P0`. **Dependencies:** `AIR-002`. **Planned code boundary:** `backend/services/research_factory/orchestrator.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `queue`.

**Implementation outcome:** restart-safe persistent jobs and gate. **Prevent regression:** crash kill -9.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-003` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Implement broker+worker engine selection ADR” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “crash kill -9”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/orchestrator.py` or the verified actual module. Focus: Persistent leases/idempotency. Prove claim transaction concurrency and resume after worker SIGKILL. No in-memory-only production state.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-003` contract tests, verify positive scenario “restart-safe persistent jobs and gate”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_003_happy`: valid authorized fixture reaches `restart-safe persistent jobs and gate`.

- `test_air_003_negative`: `crash kill -9` is blocked deterministically.

- `test_air_003_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_003_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_003_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-002`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-003 ONLY. Goal: Implement broker+worker engine selection ADR. Target: backend/services/research_factory/orchestrator.py. Deps: AIR-002. Tests: restart-safe persistent jobs and gate; block crash kill -9. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-004` — Implement strict 10-worker fan-out/fan-in

**Priority:** `P0`. **Dependencies:** `AIR-003`. **Planned code boundary:** `backend/services/research_factory/orchestrator.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `queue`.

**Implementation outcome:** 10 distinct slots per wave; all terminal before fanin. **Prevent regression:** CONC-001/002/003.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-004` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Implement strict 10-worker fan-out/fan-in” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-001/002/003”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/orchestrator.py` or the verified actual module. Focus: Persistent leases/idempotency. Prove claim transaction concurrency and resume after worker SIGKILL. No in-memory-only production state.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-004` contract tests, verify positive scenario “10 distinct slots per wave; all terminal before fanin”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_004_happy`: valid authorized fixture reaches `10 distinct slots per wave; all terminal before fanin`.

- `test_air_004_negative`: `CONC-001/002/003` is blocked deterministically.

- `test_air_004_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_004_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_004_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-003`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-004 ONLY. Goal: Implement strict 10-worker fan-out/fan-in. Target: backend/services/research_factory/orchestrator.py. Deps: AIR-003. Tests: 10 distinct slots per wave; all terminal before fanin; block CONC-001/002/003. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-005` — Implement global provider/concurrency quotas

**Priority:** `P0`. **Dependencies:** `AIR-003`. **Planned code boundary:** `backend/services/research_factory/providers/base.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `provider`.

**Implementation outcome:** limits across all runs not just per process. **Prevent regression:** CONC-003/004/012.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-005` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Implement global provider/concurrency quotas” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-003/004/012”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/providers/base.py` or the verified actual module. Focus: Adapter with fake/mock implementation for tests; explicit quota, timeout, policy, provider model ID and structured response validation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-005` contract tests, verify positive scenario “limits across all runs not just per process”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_005_happy`: valid authorized fixture reaches `limits across all runs not just per process`.

- `test_air_005_negative`: `CONC-003/004/012` is blocked deterministically.

- `test_air_005_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_005_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_005_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-003`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-005 ONLY. Goal: Implement global provider/concurrency quotas. Target: backend/services/research_factory/providers/base.py. Deps: AIR-003. Tests: limits across all runs not just per process; block CONC-003/004/012. Follow V4.0–V4.4 and V4.10. Never deploy.`

