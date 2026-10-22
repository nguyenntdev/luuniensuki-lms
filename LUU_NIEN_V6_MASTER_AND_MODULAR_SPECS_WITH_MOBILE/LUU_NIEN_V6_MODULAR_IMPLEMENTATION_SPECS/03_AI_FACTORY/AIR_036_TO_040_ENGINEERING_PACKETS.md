# AIR-036..AIR-040 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-036` — Connect approved content to History Tutor

**Priority:** `P0`. **Dependencies:** `AIR-035, R5-001`. **Planned code boundary:** `backend/services/history_tutor.py` [EXISTS]. **Category:** `writer`.

**Implementation outcome:** draft never searchable; version lock. **Prevent regression:** unreviewed leakage.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-036` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Connect approved content to History Tutor” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “unreviewed leakage”; run it to capture pre-fix failure.

5. Implement target in `backend/services/history_tutor.py` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-036` contract tests, verify positive scenario “draft never searchable; version lock”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_036_happy`: valid authorized fixture reaches `draft never searchable; version lock`.

- `test_air_036_negative`: `unreviewed leakage` is blocked deterministically.

- `test_air_036_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_036_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_036_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-035, R5-001`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-036 ONLY. Goal: Connect approved content to History Tutor. Target: backend/services/history_tutor.py. Deps: AIR-035, R5-001. Tests: draft never searchable; version lock; block unreviewed leakage. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-037` — Connect article/ELLO content UI and exports

**Priority:** `P1`. **Dependencies:** `AIR-035, AIR-029`. **Planned code boundary:** `frontend/src/app/` [EXISTS]. **Category:** `writer`.

**Implementation outcome:** citation click resolves locators, 2D works. **Prevent regression:** public e2e.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-037` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Connect article/ELLO content UI and exports” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “public e2e”; run it to capture pre-fix failure.

5. Implement target in `frontend/src/app/` or the verified actual module. Focus: Content sections with per-sentence claim_refs and prompt provenance. Never write directly to published tables.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-037` contract tests, verify positive scenario “citation click resolves locators, 2D works”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_037_happy`: valid authorized fixture reaches `citation click resolves locators, 2D works`.

- `test_air_037_negative`: `public e2e` is blocked deterministically.

- `test_air_037_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_037_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_037_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-035, AIR-029`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-037 ONLY. Goal: Connect article/ELLO content UI and exports. Target: frontend/src/app/. Deps: AIR-035, AIR-029. Tests: citation click resolves locators, 2D works; block public e2e. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-038` — Historical correction/rights revoke cascade

**Priority:** `P0`. **Dependencies:** `AIR-035, AIR-015`. **Planned code boundary:** `backend/services/research_factory/corrections.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `monitor`.

**Implementation outcome:** rights withdrawal invalidates public assets. **Prevent regression:** EV-010/011.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-038` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Historical correction/rights revoke cascade” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-010/011”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/corrections.py` or the verified actual module. Focus: Immutable correction events, dependency walk, scheduled bounded reruns; no silent mutation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-038` contract tests, verify positive scenario “rights withdrawal invalidates public assets”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_038_happy`: valid authorized fixture reaches `rights withdrawal invalidates public assets`.

- `test_air_038_negative`: `EV-010/011` is blocked deterministically.

- `test_air_038_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_038_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_038_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-035, AIR-015`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-038 ONLY. Goal: Historical correction/rights revoke cascade. Target: backend/services/research_factory/corrections.py. Deps: AIR-035, AIR-015. Tests: rights withdrawal invalidates public assets; block EV-010/011. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-039` — Scheduled P11 watchers + incremental reruns

**Priority:** `P1`. **Dependencies:** `AIR-038`. **Planned code boundary:** `backend/services/research_factory/monitoring.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `monitor`.

**Implementation outcome:** changes create new run not overwrite. **Prevent regression:** CONC-010.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-039` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Scheduled P11 watchers + incremental reruns” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-010”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/monitoring.py` or the verified actual module. Focus: Immutable correction events, dependency walk, scheduled bounded reruns; no silent mutation.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-039` contract tests, verify positive scenario “changes create new run not overwrite”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_039_happy`: valid authorized fixture reaches `changes create new run not overwrite`.

- `test_air_039_negative`: `CONC-010` is blocked deterministically.

- `test_air_039_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_039_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_039_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-038`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-039 ONLY. Goal: Scheduled P11 watchers + incremental reruns. Target: backend/services/research_factory/monitoring.py. Deps: AIR-038. Tests: changes create new run not overwrite; block CONC-010. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-040` — Costs/latency/quality dashboard

**Priority:** `P1`. **Dependencies:** `AIR-009, AIR-031`. **Planned code boundary:** `frontend/src/app/admin/research-factory/analytics/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `ui`.

**Implementation outcome:** denominators and active concurrency shown. **Prevent regression:** telemetry reproducibility.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-040` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Costs/latency/quality dashboard” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “telemetry reproducibility”; run it to capture pre-fix failure.

5. Implement target in `frontend/src/app/admin/research-factory/analytics/` or the verified actual module. Focus: Admin-only route with RBAC; typed API hooks; loading/empty/error/blocked/permission states; keyboard accessibility.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-040` contract tests, verify positive scenario “denominators and active concurrency shown”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_040_happy`: valid authorized fixture reaches `denominators and active concurrency shown`.

- `test_air_040_negative`: `telemetry reproducibility` is blocked deterministically.

- `test_air_040_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_040_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_040_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-009, AIR-031`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-040 ONLY. Goal: Costs/latency/quality dashboard. Target: frontend/src/app/admin/research-factory/analytics/. Deps: AIR-009, AIR-031. Tests: denominators and active concurrency shown; block telemetry reproducibility. Follow V4.0–V4.4 and V4.10. Never deploy.`

