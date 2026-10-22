# AIR-031..AIR-035 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-031` — Independent QA runner 10 agents

**Priority:** `P0`. **Dependencies:** `AIR-030, AIR-004`. **Planned code boundary:** `backend/services/research_factory/qa.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** P08 10 results; P0 blockers stop. **Prevent regression:** CONC-007.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-031` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Independent QA runner 10 agents” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-007”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/qa.py` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-031` contract tests, verify positive scenario “P08 10 results; P0 blockers stop”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_031_happy`: valid authorized fixture reaches `P08 10 results; P0 blockers stop`.

- `test_air_031_negative`: `CONC-007` is blocked deterministically.

- `test_air_031_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_031_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_031_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-030, AIR-004`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-031 ONLY. Goal: Independent QA runner 10 agents. Target: backend/services/research_factory/qa.py. Deps: AIR-030, AIR-004. Tests: P08 10 results; P0 blockers stop; block CONC-007. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-032` — Adversarial injection/rights test suite

**Priority:** `P0`. **Dependencies:** `AIR-031`. **Planned code boundary:** `tests/research_factory/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** high severity zero in pilot test suite. **Prevent regression:** EV-007/008/014.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-032` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Adversarial injection/rights test suite” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “EV-007/008/014”; run it to capture pre-fix failure.

5. Implement target in `tests/research_factory/` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-032` contract tests, verify positive scenario “high severity zero in pilot test suite”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_032_happy`: valid authorized fixture reaches `high severity zero in pilot test suite`.

- `test_air_032_negative`: `EV-007/008/014` is blocked deterministically.

- `test_air_032_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_032_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_032_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-031`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-032 ONLY. Goal: Adversarial injection/rights test suite. Target: tests/research_factory/. Deps: AIR-031. Tests: high severity zero in pilot test suite; block EV-007/008/014. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-033` — Two-human signed review/approval

**Priority:** `P0`. **Dependencies:** `AIR-031, AIR-008`. **Planned code boundary:** `backend/services/research_factory/approvals.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `approval`.

**Implementation outcome:** AI cannot self-approve; 2 distinct users. **Prevent regression:** CONC-008.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-033` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Two-human signed review/approval” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-008”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/approvals.py` or the verified actual module. Focus: Auth human principals only; version-bound signatures; no LLM approvals; audit every state transition.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-033` contract tests, verify positive scenario “AI cannot self-approve; 2 distinct users”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_033_happy`: valid authorized fixture reaches `AI cannot self-approve; 2 distinct users`.

- `test_air_033_negative`: `CONC-008` is blocked deterministically.

- `test_air_033_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_033_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_033_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-031, AIR-008`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-033 ONLY. Goal: Two-human signed review/approval. Target: backend/services/research_factory/approvals.py. Deps: AIR-031, AIR-008. Tests: AI cannot self-approve; 2 distinct users; block CONC-008. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-034` — Editorial review UI + diff + conflict notes

**Priority:** `P1`. **Dependencies:** `AIR-033`. **Planned code boundary:** `frontend/src/app/admin/research-factory/reviews/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `ui`.

**Implementation outcome:** lineage and source viewer visible. **Prevent regression:** multi-reviewer conflict.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-034` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Editorial review UI + diff + conflict notes” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “multi-reviewer conflict”; run it to capture pre-fix failure.

5. Implement target in `frontend/src/app/admin/research-factory/reviews/` or the verified actual module. Focus: Admin-only route with RBAC; typed API hooks; loading/empty/error/blocked/permission states; keyboard accessibility.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-034` contract tests, verify positive scenario “lineage and source viewer visible”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_034_happy`: valid authorized fixture reaches `lineage and source viewer visible`.

- `test_air_034_negative`: `multi-reviewer conflict` is blocked deterministically.

- `test_air_034_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_034_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_034_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-033`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-034 ONLY. Goal: Editorial review UI + diff + conflict notes. Target: frontend/src/app/admin/research-factory/reviews/. Deps: AIR-033. Tests: lineage and source viewer visible; block multi-reviewer conflict. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-035` — Atomic release manifest + pointer swap

**Priority:** `P0`. **Dependencies:** `AIR-033, AIR-007`. **Planned code boundary:** `backend/services/research_factory/releases.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `release`.

**Implementation outcome:** no partial public updates. **Prevent regression:** CONC-009.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-035` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Atomic release manifest + pointer swap” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-009”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/releases.py` or the verified actual module. Focus: Two-phase preflight then transactional pointer switch; strict rights/QA/approval gate; rollback.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-035` contract tests, verify positive scenario “no partial public updates”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_035_happy`: valid authorized fixture reaches `no partial public updates`.

- `test_air_035_negative`: `CONC-009` is blocked deterministically.

- `test_air_035_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_035_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_035_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-033, AIR-007`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-035 ONLY. Goal: Atomic release manifest + pointer swap. Target: backend/services/research_factory/releases.py. Deps: AIR-033, AIR-007. Tests: no partial public updates; block CONC-009. Follow V4.0–V4.4 and V4.10. Never deploy.`

