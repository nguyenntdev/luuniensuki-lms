# AIR-011..AIR-015 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-011` — Build source candidate registry

**Priority:** `P0`. **Dependencies:** `AIR-007`. **Planned code boundary:** `backend/services/research_factory/discovery.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** query traces and DOI lineage stored. **Prevent regression:** fake metadata reject.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-011` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Build source candidate registry” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “fake metadata reject”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/discovery.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-011` contract tests, verify positive scenario “query traces and DOI lineage stored”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_011_happy`: valid authorized fixture reaches `query traces and DOI lineage stored`.

- `test_air_011_negative`: `fake metadata reject` is blocked deterministically.

- `test_air_011_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_011_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_011_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-007`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-011 ONLY. Goal: Build source candidate registry. Target: backend/services/research_factory/discovery.py. Deps: AIR-007. Tests: query traces and DOI lineage stored; block fake metadata reject. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-012` — Build provider allowlists and usage policies

**Priority:** `P0`. **Dependencies:** `AIR-011`. **Planned code boundary:** `backend/services/research_factory/providers/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `provider`.

**Implementation outcome:** forbidden domains/uses blocked. **Prevent regression:** license/captcha negative.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-012` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Build provider allowlists and usage policies” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “license/captcha negative”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/providers/` or the verified actual module. Focus: Adapter with fake/mock implementation for tests; explicit quota, timeout, policy, provider model ID and structured response validation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-012` contract tests, verify positive scenario “forbidden domains/uses blocked”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_012_happy`: valid authorized fixture reaches `forbidden domains/uses blocked`.

- `test_air_012_negative`: `license/captcha negative` is blocked deterministically.

- `test_air_012_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_012_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_012_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-011`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-012 ONLY. Goal: Build provider allowlists and usage policies. Target: backend/services/research_factory/providers/. Deps: AIR-011. Tests: forbidden domains/uses blocked; block license/captcha negative. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-013` — Official/museum/research metadata connectors

**Priority:** `P1`. **Dependencies:** `AIR-012`. **Planned code boundary:** `backend/services/research_factory/providers/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `provider`.

**Implementation outcome:** metadata candidates with exact URLs+times. **Prevent regression:** stub adapter contracts.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-013` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Official/museum/research metadata connectors” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “stub adapter contracts”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/providers/` or the verified actual module. Focus: Adapter with fake/mock implementation for tests; explicit quota, timeout, policy, provider model ID and structured response validation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-013` contract tests, verify positive scenario “metadata candidates with exact URLs+times”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_013_happy`: valid authorized fixture reaches `metadata candidates with exact URLs+times`.

- `test_air_013_negative`: `stub adapter contracts` is blocked deterministically.

- `test_air_013_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_013_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_013_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-012`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-013 ONLY. Goal: Official/museum/research metadata connectors. Target: backend/services/research_factory/providers/. Deps: AIR-012. Tests: metadata candidates with exact URLs+times; block stub adapter contracts. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-014` — Authorized download & source snapshotter

**Priority:** `P1`. **Dependencies:** `AIR-012, AIR-007`. **Planned code boundary:** `backend/services/research_factory/acquisition.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `provider`.

**Implementation outcome:** immutable snapshot only rights permitted. **Prevent regression:** MIME/redirect/payload tests.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-014` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Authorized download & source snapshotter” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “MIME/redirect/payload tests”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/acquisition.py` or the verified actual module. Focus: Adapter with fake/mock implementation for tests; explicit quota, timeout, policy, provider model ID and structured response validation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-014` contract tests, verify positive scenario “immutable snapshot only rights permitted”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_014_happy`: valid authorized fixture reaches `immutable snapshot only rights permitted`.

- `test_air_014_negative`: `MIME/redirect/payload tests` is blocked deterministically.

- `test_air_014_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_014_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_014_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-012, AIR-007`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-014 ONLY. Goal: Authorized download & source snapshotter. Target: backend/services/research_factory/acquisition.py. Deps: AIR-012, AIR-007. Tests: immutable snapshot only rights permitted; block MIME/redirect/payload tests. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-015` — Source rights action matrix

**Priority:** `P0`. **Dependencies:** `AIR-012`. **Planned code boundary:** `backend/services/research_factory/rights.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** no unknown=>grant conversion. **Prevent regression:** rights decision fuzz.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-015` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Source rights action matrix” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “rights decision fuzz”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/rights.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-015` contract tests, verify positive scenario “no unknown=>grant conversion”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_015_happy`: valid authorized fixture reaches `no unknown=>grant conversion`.

- `test_air_015_negative`: `rights decision fuzz` is blocked deterministically.

- `test_air_015_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_015_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_015_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-012`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-015 ONLY. Goal: Source rights action matrix. Target: backend/services/research_factory/rights.py. Deps: AIR-012. Tests: no unknown=>grant conversion; block rights decision fuzz. Follow V4.0–V4.4 and V4.10. Never deploy.`

