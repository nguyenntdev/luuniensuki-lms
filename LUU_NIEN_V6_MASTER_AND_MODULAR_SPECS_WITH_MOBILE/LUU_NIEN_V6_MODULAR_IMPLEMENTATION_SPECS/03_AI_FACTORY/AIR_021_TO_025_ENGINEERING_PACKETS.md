# AIR-021..AIR-025 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-021` — Historical source independence graph

**Priority:** `P1`. **Dependencies:** `AIR-011`. **Planned code boundary:** `backend/services/research_factory/source_graph.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** two mirrors count one origin. **Prevent regression:** EV-003.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-021` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Historical source independence graph” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-003”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/source_graph.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-021` contract tests, verify positive scenario “two mirrors count one origin”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_021_happy`: valid authorized fixture reaches `two mirrors count one origin`.

- `test_air_021_negative`: `EV-003` is blocked deterministically.

- `test_air_021_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_021_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_021_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-011`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-021 ONLY. Goal: Historical source independence graph. Target: backend/services/research_factory/source_graph.py. Deps: AIR-011. Tests: two mirrors count one origin; block EV-003. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-022` — Cross-source conflict detector

**Priority:** `P1`. **Dependencies:** `AIR-020, AIR-021`. **Planned code boundary:** `backend/services/research_factory/corroboration.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** contradictory evidence not discarded. **Prevent regression:** EV-004.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-022` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Cross-source conflict detector” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-004”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/corroboration.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-022` contract tests, verify positive scenario “contradictory evidence not discarded”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_022_happy`: valid authorized fixture reaches `contradictory evidence not discarded`.

- `test_air_022_negative`: `EV-004` is blocked deterministically.

- `test_air_022_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_022_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_022_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-020, AIR-021`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-022 ONLY. Goal: Cross-source conflict detector. Target: backend/services/research_factory/corroboration.py. Deps: AIR-020, AIR-021. Tests: contradictory evidence not discarded; block EV-004. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-023` — Temporal geo+identity reviewer

**Priority:** `P1`. **Dependencies:** `AIR-019`. **Planned code boundary:** `backend/services/research_factory/ontology.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** date_precision, map status enforced. **Prevent regression:** EV-006.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-023` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Temporal geo+identity reviewer” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-006”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/ontology.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-023` contract tests, verify positive scenario “date_precision, map status enforced”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_023_happy`: valid authorized fixture reaches `date_precision, map status enforced`.

- `test_air_023_negative`: `EV-006` is blocked deterministically.

- `test_air_023_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_023_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_023_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-019`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-023 ONLY. Goal: Temporal geo+identity reviewer. Target: backend/services/research_factory/ontology.py. Deps: AIR-019. Tests: date_precision, map status enforced; block EV-006. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-024` — Evidence dossier builder 162 coverage

**Priority:** `P0`. **Dependencies:** `AIR-022`. **Planned code boundary:** `backend/services/research_factory/dossiers.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** no claims without bindings; gap flags. **Prevent regression:** coverage grid tests.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-024` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Evidence dossier builder 162 coverage” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “coverage grid tests”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/dossiers.py` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-024` contract tests, verify positive scenario “no claims without bindings; gap flags”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_024_happy`: valid authorized fixture reaches `no claims without bindings; gap flags`.

- `test_air_024_negative`: `coverage grid tests` is blocked deterministically.

- `test_air_024_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_024_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_024_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-022`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-024 ONLY. Goal: Evidence dossier builder 162 coverage. Target: backend/services/research_factory/dossiers.py. Deps: AIR-022. Tests: no claims without bindings; gap flags; block coverage grid tests. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-025` — Full VI article source-bound writer

**Priority:** `P0`. **Dependencies:** `AIR-024`. **Planned code boundary:** `backend/services/research_factory/writers.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** long form segmented with sentence_claim_refs. **Prevent regression:** unsupported sentence rejection.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-025` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Full VI article source-bound writer” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “unsupported sentence rejection”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/writers.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-025` contract tests, verify positive scenario “long form segmented with sentence_claim_refs”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_025_happy`: valid authorized fixture reaches `long form segmented with sentence_claim_refs`.

- `test_air_025_negative`: `unsupported sentence rejection` is blocked deterministically.

- `test_air_025_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_025_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_025_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-024`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-025 ONLY. Goal: Full VI article source-bound writer. Target: backend/services/research_factory/writers.py. Deps: AIR-024. Tests: long form segmented with sentence_claim_refs; block unsupported sentence rejection. Follow V4.0–V4.4 and V4.10. Never deploy.`

