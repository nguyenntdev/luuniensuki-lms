# AIR-026..AIR-030 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-026` — EN writer and bilingual sentence alignment

**Priority:** `P1`. **Dependencies:** `AIR-025`. **Planned code boundary:** `backend/services/research_factory/writers_en.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** EN adds no unsupported facts. **Prevent regression:** EV-013.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-026` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “EN writer and bilingual sentence alignment” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-013”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/writers_en.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-026` contract tests, verify positive scenario “EN adds no unsupported facts”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_026_happy`: valid authorized fixture reaches `EN adds no unsupported facts`.

- `test_air_026_negative`: `EV-013` is blocked deterministically.

- `test_air_026_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_026_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_026_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-025`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-026 ONLY. Goal: EN writer and bilingual sentence alignment. Target: backend/services/research_factory/writers_en.py. Deps: AIR-025. Tests: EN adds no unsupported facts; block EV-013. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-027` — Han-Nom editorial notes generator

**Priority:** `P1`. **Dependencies:** `AIR-018, AIR-024`. **Planned code boundary:** `backend/services/research_factory/han_nom_writer.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** no unverified transcript accepted. **Prevent regression:** glyph review gate.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-027` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Han-Nom editorial notes generator” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “glyph review gate”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/han_nom_writer.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-027` contract tests, verify positive scenario “no unverified transcript accepted”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_027_happy`: valid authorized fixture reaches `no unverified transcript accepted`.

- `test_air_027_negative`: `glyph review gate` is blocked deterministically.

- `test_air_027_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_027_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_027_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-018, AIR-024`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-027 ONLY. Goal: Han-Nom editorial notes generator. Target: backend/services/research_factory/han_nom_writer.py. Deps: AIR-018, AIR-024. Tests: no unverified transcript accepted; block glyph review gate. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-028` — Museum label/captions/3D-AR scripts

**Priority:** `P1`. **Dependencies:** `AIR-024`. **Planned code boundary:** `backend/services/research_factory/media_writers.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** rights + hotspot + citations + 2D fallback. **Prevent regression:** asset rights blocked.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-028` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Museum label/captions/3D-AR scripts” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “asset rights blocked”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/media_writers.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-028` contract tests, verify positive scenario “rights + hotspot + citations + 2D fallback”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_028_happy`: valid authorized fixture reaches `rights + hotspot + citations + 2D fallback`.

- `test_air_028_negative`: `asset rights blocked` is blocked deterministically.

- `test_air_028_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_028_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_028_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-024`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-028 ONLY. Goal: Museum label/captions/3D-AR scripts. Target: backend/services/research_factory/media_writers.py. Deps: AIR-024. Tests: rights + hotspot + citations + 2D fallback; block asset rights blocked. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-029` — ELLO/LMS assessment content generator

**Priority:** `P1`. **Dependencies:** `AIR-024, R3-001`. **Planned code boundary:** `backend/services/research_factory/lesson_writer.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** quiz answer source traceable. **Prevent regression:** ELLO evidence rubric tests.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-029` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “ELLO/LMS assessment content generator” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “ELLO evidence rubric tests”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/lesson_writer.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-029` contract tests, verify positive scenario “quiz answer source traceable”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_029_happy`: valid authorized fixture reaches `quiz answer source traceable`.

- `test_air_029_negative`: `ELLO evidence rubric tests` is blocked deterministically.

- `test_air_029_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_029_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_029_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-024, R3-001`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-029 ONLY. Goal: ELLO/LMS assessment content generator. Target: backend/services/research_factory/lesson_writer.py. Deps: AIR-024, R3-001. Tests: quiz answer source traceable; block ELLO evidence rubric tests. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-030` — Full article structured block assembly

**Priority:** `P0`. **Dependencies:** `AIR-025, AIR-026`. **Planned code boundary:** `backend/services/research_factory/content_assembler.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `writer`.

**Implementation outcome:** all sections diff/version + citations. **Prevent regression:** missing block alerts.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-030` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Full article structured block assembly” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “missing block alerts”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/content_assembler.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-030` contract tests, verify positive scenario “all sections diff/version + citations”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_030_happy`: valid authorized fixture reaches `all sections diff/version + citations`.

- `test_air_030_negative`: `missing block alerts` is blocked deterministically.

- `test_air_030_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_030_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_030_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-025, AIR-026`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-030 ONLY. Goal: Full article structured block assembly. Target: backend/services/research_factory/content_assembler.py. Deps: AIR-025, AIR-026. Tests: all sections diff/version + citations; block missing block alerts. Follow V4.0–V4.4 and V4.10. Never deploy.`

