# W00 — 10 DEVELOPMENT AGENT TICKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14/W00`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

### W00 — BASELINE/TRUTH & CONTRACT INVENTORY

**Priority:** `P0`. **Wave gate:** preflight và truth register đủ; không sửa production trước khi dữ liệu đầu vào rõ. **Prerequisite waves:** clean safe snapshot, no prior wave.

| Slot | Ticket | Feature / task | Files / boundaries |
|---|---|---|---|

| A01 | `V5-T001` | Freeze snapshot & lock route inventory | `AGENTS.md; backend-rust/config/route-modes.toml; backend/app.py` |
| A02 | `V5-T002` | Reproducible local development | `docker-compose.yml; backend/Dockerfile; frontend/package.json` |
| A03 | `V5-T003` | Production mock call-site registry | `frontend/src/lib/rbpc/inquiries.ts; frontend/src/lib/imperial/map-api.ts; frontend/src/lib/imperial/v51-api.ts` |
| A04 | `V5-T004` | Migrations graph and drift baseline | `alembic.ini; migrations/versions/; backend/models.py` |
| A05 | `V5-T005` | API contract snapshot | `backend/main.py; backend/routers/; frontend/src/types/api.ts` |
| A06 | `V5-T006` | Identity/consent baseline | `backend/domain/auth_session.py; backend/routers/auth.py; backend/models_rbpc.py` |
| A07 | `V5-T007` | RBPC demo tenant isolation | `docs/rbpc/; frontend/src/app/rbpc/; backend/services/demo_fixtures.py` |
| A08 | `V5-T008` | 162 relic dataset inventory | `data/*Data*Dinh.json; backend/services/heritage_import.py` |
| A09 | `V5-T009` | Media and rights inventory | `public/models/; ban-duc-noi/; docs/rbpc/MEDIA_ASSETS_MANIFEST.md` |
| A10 | `V5-T010` | Observability & deployment baseline | `docker-compose.prod.yml; nginx-luunien-staging.conf; .github/workflows/` |

#### `V5-T001` — Freeze snapshot & lock route inventory

- **Role / slot:** W00-A01; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `AGENTS.md; backend-rust/config/route-modes.toml; backend/app.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Lấy checkout SHA thật, lập route list với owner Rust/Python, auth, request/response, trạng thái reachable; tự động diff OpenAPI.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Một route không có backend vẫn hiện trên UI phải bị đánh UNKNOWN, không gán ready.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t001.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A01 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T002` — Reproducible local development

- **Role / slot:** W00-A02; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docker-compose.yml; backend/Dockerfile; frontend/package.json`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Thiết kế local disposable DB, object store, secret placeholders, HTTPS proxy test; viết bootstrap script idempotent và README chính xác.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Lần chạy thứ hai không được reset database hay mất tài khoản test.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t002.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A02 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T003` — Production mock call-site registry

- **Role / slot:** W00-A03; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `frontend/src/lib/rbpc/inquiries.ts; frontend/src/lib/imperial/map-api.ts; frontend/src/lib/imperial/v51-api.ts`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** AST/static scan catch paths của runtime fake-success và seed; lập manifest theo exported function, consumer screen, release risk.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Mock unit tests không bị false-positive; production code seed flagged.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t003.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A03 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T004` — Migrations graph and drift baseline

- **Role / slot:** W00-A04; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `alembic.ini; migrations/versions/; backend/models.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Kiểm tra multiple heads/down_revision, schema drift và data preservation; tạo disposable migration verify.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Không tự merge nhiều heads khi chưa có DBA review; failing path ghi BLOCKED.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t004.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A04 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T005` — API contract snapshot

- **Role / slot:** W00-A05; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/main.py; backend/routers/; frontend/src/types/api.ts`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Xuất OpenAPI từ app active, phân chia public/admin/partner/teacher; đối chiếu TS generator và mobile clients.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Breaking endpoint/path thiếu mapping làm CI fail.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t005.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A05 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T006` — Identity/consent baseline

- **Role / slot:** W00-A06; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/domain/auth_session.py; backend/routers/auth.py; backend/models_rbpc.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Lập matrix role/student/teacher/partner/staff/editor, cookie hardening và consent policy; ghi chưa xác nhận thực thi.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Partner A get Partner B -> 403; inactive consent blocks public profile.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t006.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A06 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T007` — RBPC demo tenant isolation

- **Role / slot:** W00-A07; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docs/rbpc/; frontend/src/app/rbpc/; backend/services/demo_fixtures.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Thiết kế demo namespace/toggle/DB riêng, biểu ngữ DEMO DATA và zero fixture in prod.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Empty prod tenant returns no test inquiries even if demo has records.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t007.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A07 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T008` — 162 relic dataset inventory

- **Role / slot:** W00-A08; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `data/*Data*Dinh.json; backend/services/heritage_import.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Kiểm kê 162 IDs, 9×18, duplicate/Chinese text, sources flags, invalid images, mesh refs; xuất signed machine report.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unknown Hán–Nôm and invented source are not auto accepted.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t008.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A08 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T009` — Media and rights inventory

- **Role / slot:** W00-A09; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `public/models/; ban-duc-noi/; docs/rbpc/MEDIA_ASSETS_MANIFEST.md`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Map each 3d_mesh_id to actual asset checksum/format/rights and suitable 2D fallback; identify missing.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Mesh reference without valid file is marked missing rather than rendered fake.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t009.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A09 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T010` — Observability & deployment baseline

- **Role / slot:** W00-A10; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docker-compose.prod.yml; nginx-luunien-staging.conf; .github/workflows/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Collect verified commands for logs, health, alerts, backup and rollback; mark docs claims not measured.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No uptime/security PASS from docs alone without probe or log.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t010.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A10 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

**Wave W00 completion barrier:** 10/10 slots terminal, verified observed concurrency and cap, every blocking ticket integrated and tested, shared migrations approved, no production mock success, coordinator signed report. If any P0 issue or human sign-off pending: state `BLOCKED`; may start downstream design tasks but do not release dependent features.

