# AIR-016..AIR-020 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-016` — Source passages/pages schema migration

**Priority:** `P0`. **Dependencies:** `AIR-002`. **Planned code boundary:** `migrations/versions/` [EXISTS]. **Category:** `db`.

**Implementation outcome:** page/index/bbox/span/edition linked. **Prevent regression:** FK/deletion tests.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-016` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Source passages/pages schema migration” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “FK/deletion tests”; run it to capture pre-fix failure.

5. Implement target in `migrations/versions/` or the verified actual module. Focus: Inspect actual Alembic revision graph; write add-only PostgreSQL migration under migrations/versions; register models through backend.models; fresh/upgraded DB tests.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-016` contract tests, verify positive scenario “page/index/bbox/span/edition linked”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_016_happy`: valid authorized fixture reaches `page/index/bbox/span/edition linked`.

- `test_air_016_negative`: `FK/deletion tests` is blocked deterministically.

- `test_air_016_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_016_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_016_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-002`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-016 ONLY. Goal: Source passages/pages schema migration. Target: migrations/versions/. Deps: AIR-002. Tests: page/index/bbox/span/edition linked; block FK/deletion tests. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-017` — PDF/HTML page parser + OCR quality ledger

**Priority:** `P1`. **Dependencies:** `AIR-014, AIR-016`. **Planned code boundary:** `backend/services/research_factory/extraction.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** source passage offsets verifiable. **Prevent regression:** two-column/missing-glyph fixtures.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-017` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “PDF/HTML page parser + OCR quality ledger” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “two-column/missing-glyph fixtures”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/extraction.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-017` contract tests, verify positive scenario “source passage offsets verifiable”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_017_happy`: valid authorized fixture reaches `source passage offsets verifiable`.

- `test_air_017_negative`: `two-column/missing-glyph fixtures` is blocked deterministically.

- `test_air_017_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_017_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_017_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-014, AIR-016`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-017 ONLY. Goal: PDF/HTML page parser + OCR quality ledger. Target: backend/services/research_factory/extraction.py. Deps: AIR-014, AIR-016. Tests: source passage offsets verifiable; block two-column/missing-glyph fixtures. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-018` — Han-Nom transcription human review UI

**Priority:** `P0`. **Dependencies:** `AIR-017, AIR-008`. **Planned code boundary:** `frontend/src/app/admin/research-factory/ocr/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** no unreviewed original strings published. **Prevent regression:** EV-005.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-018` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Han-Nom transcription human review UI” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-005”; run it to capture pre-fix failure.

5. Implement target in `frontend/src/app/admin/research-factory/ocr/` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-018` contract tests, verify positive scenario “no unreviewed original strings published”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_018_happy`: valid authorized fixture reaches `no unreviewed original strings published`.

- `test_air_018_negative`: `EV-005` is blocked deterministically.

- `test_air_018_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_018_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_018_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-017, AIR-008`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-018 ONLY. Goal: Han-Nom transcription human review UI. Target: frontend/src/app/admin/research-factory/ocr/. Deps: AIR-017, AIR-008. Tests: no unreviewed original strings published; block EV-005. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-019` — Atomic claim/passage extraction pipeline

**Priority:** `P0`. **Dependencies:** `AIR-017`. **Planned code boundary:** `backend/services/research_factory/claims.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** claims must bind source passage or gap. **Prevent regression:** EV-001/002/012.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-019` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Atomic claim/passage extraction pipeline” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-001/002/012”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/claims.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-019` contract tests, verify positive scenario “claims must bind source passage or gap”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_019_happy`: valid authorized fixture reaches `claims must bind source passage or gap`.

- `test_air_019_negative`: `EV-001/002/012` is blocked deterministically.

- `test_air_019_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_019_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_019_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-017`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-019 ONLY. Goal: Atomic claim/passage extraction pipeline. Target: backend/services/research_factory/claims.py. Deps: AIR-017. Tests: claims must bind source passage or gap; block EV-001/002/012. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-020` — Quote+locator deterministic verifier

**Priority:** `P0`. **Dependencies:** `AIR-016, AIR-019`. **Planned code boundary:** `backend/services/research_factory/citations.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `citation`.

**Implementation outcome:** fake quote or wrong page blocked. **Prevent regression:** EV-001/002.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-020` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Quote+locator deterministic verifier” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-001/002”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/citations.py` or the verified actual module. Focus: Deterministic exact span match against immutable source version and offset, not LLM yes/no.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-020` contract tests, verify positive scenario “fake quote or wrong page blocked”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_020_happy`: valid authorized fixture reaches `fake quote or wrong page blocked`.

- `test_air_020_negative`: `EV-001/002` is blocked deterministically.

- `test_air_020_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_020_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_020_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-016, AIR-019`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-020 ONLY. Goal: Quote+locator deterministic verifier. Target: backend/services/research_factory/citations.py. Deps: AIR-016, AIR-019. Tests: fake quote or wrong page blocked; block EV-001/002. Follow V4.0–V4.4 and V4.10. Never deploy.`

