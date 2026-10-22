# AIR-041..AIR-045 — 5 CODE PACKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V4.B`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

## `AIR-041` — 3-relief pilot with experts

**Priority:** `P0`. **Dependencies:** `AIR-039`. **Planned code boundary:** `docs/research_factory/pilot/` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** all 12 phases with audited human signoff. **Prevent regression:** pilot dossier review.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-041` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “3-relief pilot with experts” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “pilot dossier review”; run it to capture pre-fix failure.

5. Implement target in `docs/research_factory/pilot/` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-041` contract tests, verify positive scenario “all 12 phases with audited human signoff”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_041_happy`: valid authorized fixture reaches `all 12 phases with audited human signoff`.

- `test_air_041_negative`: `pilot dossier review` is blocked deterministically.

- `test_air_041_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_041_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_041_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-039`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-041 ONLY. Goal: 3-relief pilot with experts. Target: docs/research_factory/pilot/. Deps: AIR-039. Tests: all 12 phases with audited human signoff; block pilot dossier review. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-042` — 9×18 batch rollout controlled by global cap

**Priority:** `P1`. **Dependencies:** `AIR-041`. **Planned code boundary:** `backend/services/research_factory/batch.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** 162 scheduled fairly without quota storm. **Prevent regression:** CONC-012.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-042` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “9×18 batch rollout controlled by global cap” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “CONC-012”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/batch.py` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-042` contract tests, verify positive scenario “162 scheduled fairly without quota storm”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_042_happy`: valid authorized fixture reaches `162 scheduled fairly without quota storm`.

- `test_air_042_negative`: `CONC-012` is blocked deterministically.

- `test_air_042_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_042_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_042_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-041`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-042 ONLY. Goal: 9×18 batch rollout controlled by global cap. Target: backend/services/research_factory/batch.py. Deps: AIR-041. Tests: 162 scheduled fairly without quota storm; block CONC-012. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-043` — Research reproducibility export for Q2/AI papers

**Priority:** `P1`. **Dependencies:** `AIR-041`. **Planned code boundary:** `backend/services/research_factory/research_export.py` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** provenance and eval release frozen, no student PII. **Prevent regression:** paper audit.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-043` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Research reproducibility export for Q2/AI papers” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “paper audit”; run it to capture pre-fix failure.

5. Implement target in `backend/services/research_factory/research_export.py` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-043` contract tests, verify positive scenario “provenance and eval release frozen, no student PII”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_043_happy`: valid authorized fixture reaches `provenance and eval release frozen, no student PII`.

- `test_air_043_negative`: `paper audit` is blocked deterministically.

- `test_air_043_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_043_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_043_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-041`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-043 ONLY. Goal: Research reproducibility export for Q2/AI papers. Target: backend/services/research_factory/research_export.py. Deps: AIR-041. Tests: provenance and eval release frozen, no student PII; block paper audit. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-044` — Deployment runbooks provider outage/rollback

**Priority:** `P1`. **Dependencies:** `AIR-035, AIR-041`. **Planned code boundary:** `docs/runbooks/research_factory.md` [TARGET or VERIFY AT CHECKOUT]. **Category:** `qa`.

**Implementation outcome:** on-call steps and drills tested. **Prevent regression:** recovery rehearsal.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-044` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Deployment runbooks provider outage/rollback” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “recovery rehearsal”; run it to capture pre-fix failure.

5. Implement target in `docs/runbooks/research_factory.md` or the verified actual module. Focus: Gold fixtures + adversarial tests + severity ledger; no production uncontrolled web.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-044` contract tests, verify positive scenario “on-call steps and drills tested”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_044_happy`: valid authorized fixture reaches `on-call steps and drills tested`.

- `test_air_044_negative`: `recovery rehearsal` is blocked deterministically.

- `test_air_044_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_044_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_044_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-035, AIR-041`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-044 ONLY. Goal: Deployment runbooks provider outage/rollback. Target: docs/runbooks/research_factory.md. Deps: AIR-035, AIR-041. Tests: on-call steps and drills tested; block recovery rehearsal. Follow V4.0–V4.4 and V4.10. Never deploy.`

## `AIR-045` — Per-provider permission and TDM compliance audit

**Priority:** `P1`. **Dependencies:** `AIR-015, AIR-041`. **Planned code boundary:** `docs/legal/research_factory_rights.md` [TARGET or VERIFY AT CHECKOUT]. **Category:** `source`.

**Implementation outcome:** evidence of approved scope and grant. **Prevent regression:** lawyer/policy signoff.

**Files to inspect first:** `AGENTS.md`, `backend/main.py`, `backend/models.py` (only if models change), exact target parent, tests/related routes, `backend-rust/config/route-modes.toml` for new Python routes.

**Detailed implementation steps:**

1. Read current code and confirm whether equivalent feature already exists; search symbols, record caller/consumer and API shapes; do not duplicate.

2. Write a one-page impact+ADR for `AIR-045` (scope, risks, alternatives, rollback); request owner decision if schema/provider/rights unclear.

3. Define strict input and output contract for “Per-provider permission and TDM compliance audit” including types, status enum, error envelope, idempotency and evidence hashes.

4. Create negative test that demonstrates “lawyer/policy signoff”; run it to capture pre-fix failure.

5. Implement target in `docs/legal/research_factory_rights.md` or the verified actual module. Focus: Canonicalize DOI/URL + edition + source version; content rights and hash; do not elevate candidate snippet.

6. Connect SQLAlchemy migration/service/API/frontend only where needed; keep public behavior backward-compatible and do not edit legacy root files.

7. Run unit tests + `AIR-045` contract tests, verify positive scenario “evidence of approved scope and grant”, then negative/security regression.

8. Run repo-level static checks applicable to changed files, inspect git diff, remove debug secrets/PII; record exact command exit codes.

9. Generate handoff JSON with changed paths, measured test evidence, outstanding blockers and human approvals required; stop here.

**Minimum test suite:**

- `test_air_045_happy`: valid authorized fixture reaches `evidence of approved scope and grant`.

- `test_air_045_negative`: `lawyer/policy signoff` is blocked deterministically.

- `test_air_045_retry`: duplicate request/worker retry is idempotent or intentionally not retryable.

- `test_air_045_rbac`: unauthorized actor denied for mutation/publication where relevant.

- `test_air_045_compat`: existing history/lesson/tutor response unchanged unless versioned.

**Implementation commands (choose only when applicable and safe):** `python -m compileall -q backend`; `DATABASE_URL=<disposable-test-db> pytest -q tests/research_factory/`; `npm --prefix frontend run type-check`; `cargo fmt --check` from backend-rust. If dependencies unavailable, mark `NOT_RUN` and attach error log.

**Explicit stop conditions:** missing dependency `AIR-015, AIR-041`, migration HEAD ambiguity, rights unknown, wrong base commit, unavailable code owner approval, provider quota denial, test failure unresolved, or new behavior leaking draft claims.

**Copy-paste task header:** `IMPLEMENT AIR-045 ONLY. Goal: Per-provider permission and TDM compliance audit. Target: docs/legal/research_factory_rights.md. Deps: AIR-015, AIR-041. Tests: evidence of approved scope and grant; block lawyer/policy signoff. Follow V4.0–V4.4 and V4.10. Never deploy.`


