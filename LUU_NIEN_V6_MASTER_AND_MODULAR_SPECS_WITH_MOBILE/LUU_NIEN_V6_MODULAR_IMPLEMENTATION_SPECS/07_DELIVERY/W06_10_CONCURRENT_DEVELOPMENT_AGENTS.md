# W06 — 10 DEVELOPMENT AGENT TICKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14/W06`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

### W06 — HISTORICAL AI TUTOR / GROUNDED ANSWERS

**Priority:** `P1`. **Wave gate:** AI answers sourced with measurable abstention and safely bounded cost. **Prerequisite waves:** W00 for W01; and scoped domain dependencies.

| Slot | Ticket | Feature / task | Files / boundaries |
|---|---|---|---|

| A01 | `V5-T061` | Retrieval only approved claims | `backend/services/history_tutor.py; backend/history_models.py` |
| A02 | `V5-T062` | Citation faithfulness validator | `backend/services/rbpc_ai.py; backend/services/history_tutor.py` |
| A03 | `V5-T063` | Hint-first learning mode | `backend/routers/history_tutor.py; frontend/src/app/dai-noi/ai/page.tsx` |
| A04 | `V5-T064` | AI provider policy & fallback | `backend/config.py; backend/services/rbpc_ai.py` |
| A05 | `V5-T065` | Live AI provenance visibility | `backend/routers/live.py; frontend/src/components/live2/` |
| A06 | `V5-T066` | Prompt-injection defenses | `backend/services/rbpc_ai.py; tests/backend/` |
| A07 | `V5-T067` | Evaluation gold-set & human rubric | `docs/rbpc/AI_EVAL.md; tests/backend/` |
| A08 | `V5-T068` | AI privacy and child protections | `backend/routers/ai.py; backend/services/` |
| A09 | `V5-T069` | AI observability and budgeting | `backend/services/; backend/routers/` |
| A10 | `V5-T070` | AI tutor end-to-end contract | `tests/backend/; frontend/e2e/` |

#### `V5-T061` — Retrieval only approved claims

- **Role / slot:** W06-A01; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/services/history_tutor.py; backend/history_models.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Query only published approved claims/sources, scope and language; no draft leakage.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Ask draft-only fact returns abstention.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t061.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A01 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T062` — Citation faithfulness validator

- **Role / slot:** W06-A02; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/services/rbpc_ai.py; backend/services/history_tutor.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Bind answer claim spans to real retrieved passages with precise locator; reject fake refs.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Invented UUID/page rejected.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t062.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A02 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T063` — Hint-first learning mode

- **Role / slot:** W06-A03; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/routers/history_tutor.py; frontend/src/app/dai-noi/ai/page.tsx`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Tutor guides student to observe/cite before revealing answer, rubric teacher remains authority.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Student can ask for citation provenance and see exact source.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t063.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A03 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T064` — AI provider policy & fallback

- **Role / slot:** W06-A04; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/config.py; backend/services/rbpc_ai.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Model ID runtime-discovered, cost/cap quotas, timeout, safe deterministic fallback labeled.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Provider 429 -> no generic unsupported historical story.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t064.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A04 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T065` — Live AI provenance visibility

- **Role / slot:** W06-A05; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/routers/live.py; frontend/src/components/live2/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Expose `provider_mode`, guardrail status and mock/fallback to UI/telemetry, never mislabel demo as AI live.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Synthetic live response has visible fallback indicator.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t065.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A05 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T066` — Prompt-injection defenses

- **Role / slot:** W06-A06; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/services/rbpc_ai.py; tests/backend/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Source text untrusted, tool allowlist, no code execution; adversarial eval.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Injected archival “ignore instructions” cannot open secrets.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t066.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A06 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T067` — Evaluation gold-set & human rubric

- **Role / slot:** W06-A07; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `docs/rbpc/AI_EVAL.md; tests/backend/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Create multilingual factual/uncertain/adversarial set with domain experts, frozen scoring and reporting.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Benchmark fails when plausible but unsupported answer given.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t067.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A07 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T068` — AI privacy and child protections

- **Role / slot:** W06-A08; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/routers/ai.py; backend/services/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Minimal retention, age/context-based guardrails, redacted logs, no unconsented training reuse.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** PII echo attempt blocked or sanitized.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t068.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A08 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T069` — AI observability and budgeting

- **Role / slot:** W06-A09; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `backend/services/; backend/routers/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Log token usage, cost, model, latency, citation validity, error code without prompt PII.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Budget exhausted returns capacity response with retry policy.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t069.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A09 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T070` — AI tutor end-to-end contract

- **Role / slot:** W06-A10; **priority:** `P1`; **classification:** PRODUCTION_COMPLETION.
- **Paths to inspect first:** `tests/backend/; frontend/e2e/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** A/B approved facts, unsupported claim, culture conflicts, provider unavailable, rights revoked.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** AI never confidently gives undocumented historical source.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t070.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A10 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

**Wave W06 completion barrier:** 10/10 slots terminal, verified observed concurrency and cap, every blocking ticket integrated and tested, shared migrations approved, no production mock success, coordinator signed report. If any P0 issue or human sign-off pending: state `BLOCKED`; may start downstream design tasks but do not release dependent features.

