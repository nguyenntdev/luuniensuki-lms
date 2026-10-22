# W12 — 10 DEVELOPMENT AGENT TICKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14/W12`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

### W12 — FINAL PRODUCTION LAUNCH / OWNERSHIP / VERIFY

**Priority:** `P0`. **Wave gate:** sign off real reliability, permissions, commerce and science accuracy. **Prerequisite waves:** W00 for W01; and scoped domain dependencies.

| Slot | Ticket | Feature / task | Files / boundaries |
|---|---|---|---|

| A01 | `V5-T121` | Source/rights publication gate final | `backend/history_models.py; backend/routers/heritage.py` |
| A02 | `V5-T122` | Zero-fake-success full-site sweep | `frontend/src/; mobile/lib/; backend/` |
| A03 | `V5-T123` | Critical integration smoke | `tests/backend/; frontend/e2e/; mobile/test/` |
| A04 | `V5-T124` | RBAC privacy and incident tabletop | `backend/; docs/` |
| A05 | `V5-T125` | Load, failover and backups | `docker-compose.prod.yml; nginx.conf; scripts/` |
| A06 | `V5-T126` | AI 10-subagent concurrency measured | `backend/services/research_factory/; tests/research_factory/` |
| A07 | `V5-T127` | Legal and creator agreement sign-off | `docs/rbpc/CONTENT_RIGHTS.md; docs/rbpc/` |
| A08 | `V5-T128` | Research results truth gate | `LuuNien_Q2_EN_Revised.tex; docs/` |
| A09 | `V5-T129` | Pilot go/no-go board | `artifacts/; docs/rbpc/RELEASE_CHECKLIST.md` |
| A10 | `V5-T130` | Post-launch 30/60/90-day plan | `docs/plan/; artifacts/` |

#### `V5-T121` — Source/rights publication gate final

- **Role / slot:** W12-A01; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/history_models.py; backend/routers/heritage.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Sampling verification plus completeness report, retract wrong claim and media under revocation.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** 0 unapproved claim visible on public random audit.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t121.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A01 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T122` — Zero-fake-success full-site sweep

- **Role / slot:** W12-A02; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `frontend/src/; mobile/lib/; backend/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Automated + manual traverse reachable routes under empty DB/5xx/403/offline; remove fixture.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** 0 artificial inquiry/grade/annotation accepted.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t122.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A02 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T123` — Critical integration smoke

- **Role / slot:** W12-A03; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `tests/backend/; frontend/e2e/; mobile/test/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** One student+teacher+partner+visitor flow through Rust/Python/Postgres and true audit.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Data consistent after restart and cross-device.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t123.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A03 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T124` — RBAC privacy and incident tabletop

- **Role / slot:** W12-A04; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/; docs/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Two-school/two-tenant malicious actor tests, consent revocation, incident process.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No sensitive cross-account leakage.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t124.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A04 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T125` — Load, failover and backups

- **Role / slot:** W12-A05; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docker-compose.prod.yml; nginx.conf; scripts/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Load agreed pilot concurrency, failover, restore, provider outage, network flaps, measure SLO.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Recovery evidence reproducible.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t125.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A05 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T126` — AI 10-subagent concurrency measured

- **Role / slot:** W12-A06; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/services/research_factory/; tests/research_factory/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Run 12 phases×10 unique agent slots, observed concurrent peak per phase, cite trace logs, cost.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** 10 concurrency claimed only if measured 10 overlapping leases.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t126.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A06 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T127` — Legal and creator agreement sign-off

- **Role / slot:** W12-A07; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docs/rbpc/CONTENT_RIGHTS.md; docs/rbpc/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Confirm software IP, photos/3D rights, school consent, artisan agreement, consumer/tax terms.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unapproved asset/commerce flag stays off.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t127.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A07 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T128` — Research results truth gate

- **Role / slot:** W12-A08; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `LuuNien_Q2_EN_Revised.tex; docs/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Synchronize self-report n=1502 methodological description, data provenance; do not invent measured gains.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Paper figure numbers reproduced from anonymized export.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t128.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A08 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T129` — Pilot go/no-go board

- **Role / slot:** W12-A09; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `artifacts/; docs/rbpc/RELEASE_CHECKLIST.md`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Collect signed owner decision, blocking issue list, flag plan, rollback triggers, support contact.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Launch blocked if any P0 open.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t129.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A09 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T130` — Post-launch 30/60/90-day plan

- **Role / slot:** W12-A10; **priority:** `P0`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docs/plan/; artifacts/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Weekly quality/retention/partner support review, validated value hypotheses, next feature prioritization.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No feature scale-up based only on demo applause.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t130.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A10 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

**Wave W12 completion barrier:** 10/10 slots terminal, verified observed concurrency and cap, every blocking ticket integrated and tested, shared migrations approved, no production mock success, coordinator signed report. If any P0 issue or human sign-off pending: state `BLOCKED`; may start downstream design tasks but do not release dependent features.



