# W10 — 10 DEVELOPMENT AGENT TICKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14/W10`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

### W10 — NEW HERITAGE MARKET / VISITOR & ARTISAN FEATURES

**Priority:** `P2`. **Wave gate:** 2–3 real partners, 1 reliable partner funnel, fair cultural commerce. **Prerequisite waves:** W00 for W01; and scoped domain dependencies.

| Slot | Ticket | Feature / task | Files / boundaries |
|---|---|---|---|

| A01 | `V5-T101` | Partner self-onboarding with verification | `backend/models_rbpc.py; frontend/src/app/rbpc/partner/` |
| A02 | `V5-T102` | Real availability inventory/calendar | `backend/models_rbpc.py; backend/routers/rbpc.py` |
| A03 | `V5-T103` | Inquiry customer notification center | `frontend/src/app/rbpc/inquiries/; backend/routers/rbpc.py` |
| A04 | `V5-T104` | Museum QR guided trails | `frontend/src/app/heritage/[slug]/; backend/routers/heritage.py` |
| A05 | `V5-T105` | Curator-controlled story recommendations | `backend/services/rbpc_ai.py; frontend/src/` |
| A06 | `V5-T106` | Multi-language visitor assist | `frontend/src/lib/rbpc/copy.ts; backend/services/rbpc_ai.py` |
| A07 | `V5-T107` | Verified customer reviews and disputes | `backend/models_rbpc.py; frontend/src/app/rbpc/` |
| A08 | `V5-T108` | Fee/revenue ledger with actual confirmation | `backend/models_rbpc.py; backend/routers/rbpc.py` |
| A09 | `V5-T109` | Creator oral history consent studio | `frontend/src/app/rbpc/partner/; backend/routers/` |
| A10 | `V5-T110` | Public impact dashboard sourced from real events | `frontend/src/app/rbpc/; backend/routers/rbpc.py` |

#### `V5-T101` — Partner self-onboarding with verification

- **Role / slot:** W10-A01; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/models_rbpc.py; frontend/src/app/rbpc/partner/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Identity/consent review, artisan profile edits, listing moderation and rights.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unverified partner cannot publish portrait/listing.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t101.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A01 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T102` — Real availability inventory/calendar

- **Role / slot:** W10-A02; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/models_rbpc.py; backend/routers/rbpc.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Limited slots, capacity, reserve timeout, provider confirmation, no false checkout.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Two users cannot confirm last seat twice.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t102.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A02 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T103` — Inquiry customer notification center

- **Role / slot:** W10-A03; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/rbpc/inquiries/; backend/routers/rbpc.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** True status, email/SMS opt-in, late response escalation, unsubscribe.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Network error never sends fake confirmed status.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t103.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A03 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T104` — Museum QR guided trails

- **Role / slot:** W10-A04; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/heritage/[slug]/; backend/routers/heritage.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** QR to verified context and source, offline 2D, wheelchair/route info when known.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unknown accessibility data not advertised as accessible.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t104.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A04 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T105` — Curator-controlled story recommendations

- **Role / slot:** W10-A05; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/services/rbpc_ai.py; frontend/src/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Rule-based object→craft link with verified relationship and no implied imperial lineage.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unverified artisan relationship hidden.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t105.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A05 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T106` — Multi-language visitor assist

- **Role / slot:** W10-A06; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/lib/rbpc/copy.ts; backend/services/rbpc_ai.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** VI/EN first, other languages only when human-reviewed; bounded AI and disclaimers.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Source missing returns uncertainty in visitor language.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t106.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A06 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T107` — Verified customer reviews and disputes

- **Role / slot:** W10-A07; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/models_rbpc.py; frontend/src/app/rbpc/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Only completed verified experience review, anti-fraud and moderation.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Fake/uncompleted inquiry cannot post rating.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t107.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A07 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T108` — Fee/revenue ledger with actual confirmation

- **Role / slot:** W10-A08; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/models_rbpc.py; backend/routers/rbpc.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Contracted take rate, actual amount, refunds, taxes, payouts after compliance approval.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Changing status confirmed alone produces zero revenue.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t108.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A08 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T109` — Creator oral history consent studio

- **Role / slot:** W10-A09; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/rbpc/partner/; backend/routers/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Audio transcript/version, per-use media consent, revoke/erase, culture context.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Revoked audio unavailable publicly and caches invalidated.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t109.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A09 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T110` — Public impact dashboard sourced from real events

- **Role / slot:** W10-A10; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/rbpc/; backend/routers/rbpc.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Only anonymized actual completed experiences/artist payouts; forecast clearly separated.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Empty DB displays 0/no metrics, never numbers from pitch.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t110.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A10 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

**Wave W10 completion barrier:** 10/10 slots terminal, verified observed concurrency and cap, every blocking ticket integrated and tested, shared migrations approved, no production mock success, coordinator signed report. If any P0 issue or human sign-off pending: state `BLOCKED`; may start downstream design tasks but do not release dependent features.

