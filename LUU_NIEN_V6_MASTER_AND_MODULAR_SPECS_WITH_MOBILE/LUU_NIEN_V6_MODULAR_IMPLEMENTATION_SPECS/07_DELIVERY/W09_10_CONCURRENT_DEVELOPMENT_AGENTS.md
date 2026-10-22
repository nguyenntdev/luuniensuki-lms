# W09 — 10 DEVELOPMENT AGENT TICKETS

> **Nguồn:** Trích không lược bỏ từ `LUU_NIEN_V5_PRODUCTION_COMPLETION_AND_NEW_FEATURES_GEMINI_FLASH_FULL_MASTER_SPEC.md` (`V5.14/W09`). **Nhận định mã nguồn trong V5 là audit tĩnh, chưa chứng minh production hoạt động.**
> **Dùng cho Gemini:** Chỉ mở tài liệu này với một ticket và tối đa 3–8 file source tương ứng.

### W09 — NEW B2B SCHOOL PRODUCT / LEARNING DIFFERENTIATION

**Priority:** `P2`. **Wave gate:** viable teacher value proposition with actual lesson task and consent. **Prerequisite waves:** W00 for W01; and scoped domain dependencies.

| Slot | Ticket | Feature / task | Files / boundaries |
|---|---|---|---|

| A01 | `V5-T091` | Teacher 45-minute lesson wizard | `frontend/src/app/dai-noi/giao-vien/; backend/routers/history_learning.py` |
| A02 | `V5-T092` | Verified heritage Passport | `frontend/src/app/dai-noi/ho-chieu/; backend/routers/progress.py` |
| A03 | `V5-T093` | Evidence board for groups | `frontend/src/app/learn/; backend/routers/` |
| A04 | `V5-T094` | Rubric analytics dashboard | `frontend/src/app/dai-noi/giao-vien/; backend/routers/classrooms.py` |
| A05 | `V5-T095` | Curriculum competency catalog | `backend/history_models.py; frontend/src/` |
| A06 | `V5-T096` | Low-bandwidth printable / offline kit | `frontend/src/components/imperial/print/; mobile/lib/` |
| A07 | `V5-T097` | Adaptive evidence practice | `backend/routers/fsrs.py; backend/routers/quests.py` |
| A08 | `V5-T098` | Multilingual learning supports | `frontend/src/lib/history.ts; backend/history_models.py` |
| A09 | `V5-T099` | Teacher onboarding and support center | `frontend/src/app/dai-noi/giao-vien/; docs/` |
| A10 | `V5-T100` | School pilot measurement & ethics | `docs/; backend/routers/` |

#### `V5-T091` — Teacher 45-minute lesson wizard

- **Role / slot:** W09-A01; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/dai-noi/giao-vien/; backend/routers/history_learning.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Wizard objectives→source→media→inquiry→assessment, 2D/3D variants and printable handout.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Lesson cannot publish without approved object/source.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t091.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A01 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T092` — Verified heritage Passport

- **Role / slot:** W09-A02; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/dai-noi/ho-chieu/; backend/routers/progress.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Server check-in, visit stamp distinct from assessed mastery, QR provenance.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Fake local completion not counted in teacher analytics.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t092.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A02 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T093` — Evidence board for groups

- **Role / slot:** W09-A03; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/learn/; backend/routers/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Groups compare sources with claim support/refute, teacher comments and revision.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Student outside group cannot edit board.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t093.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A03 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T094` — Rubric analytics dashboard

- **Role / slot:** W09-A04; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/dai-noi/giao-vien/; backend/routers/classrooms.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** School-safe aggregate per rubric/version, export with suppression minimums.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No inferential gain claim without valid research study.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t094.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A04 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T095` — Curriculum competency catalog

- **Role / slot:** W09-A05; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/history_models.py; frontend/src/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Topics/grade bands/competencies mapped to real lesson objectives, editable by educators.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Teacher flags inaccurate competency mapping.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t095.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A05 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T096` — Low-bandwidth printable / offline kit

- **Role / slot:** W09-A06; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/components/imperial/print/; mobile/lib/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Print/source excerpts within rights, offline images+QR, audio transcripts.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No AR/mobile phone requirement to complete assignment.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t096.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A06 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T097` — Adaptive evidence practice

- **Role / slot:** W09-A07; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `backend/routers/fsrs.py; backend/routers/quests.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Mastery-based schedule uses scored source tasks, transparency and opt-out; XP separate.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Repeated clicks do not produce mastery badge.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t097.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A07 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T098` — Multilingual learning supports

- **Role / slot:** W09-A08; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/lib/history.ts; backend/history_models.py`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** VI/EN pedagogical glossary; Hán–Nôm expert reviewed, bilingual citations and translation provenance.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Mismatched translation flagged, not silently accepted.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t098.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A08 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T099` — Teacher onboarding and support center

- **Role / slot:** W09-A09; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `frontend/src/app/dai-noi/giao-vien/; docs/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Demo vs real onboarding, sample lesson template clearly marked; support tickets and training.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** Unverified school user cannot access real pupil info.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t099.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A09 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

#### `V5-T100` — School pilot measurement & ethics

- **Role / slot:** W09-A10; **priority:** `P2`; **classification:** NEW_PRODUCT_FEATURE.
- **Paths to inspect first:** `docs/; backend/routers/`. Verify exact filenames against live checkout; create only missing target modules deliberately, not duplicate existing routers/tables.
- **Functional change / implementation contract:** Pilot protocol, prior consent, workload metrics, retention, rubric evaluation; separate from 1,502 survey.
- **Server/database interaction:** identify current endpoint, relevant SQLAlchemy row and gateway routing; define typed request-response; mutation must be atomic/idempotent and role scoped. If no backend route, make explicit target contract + tests before UI wiring. Do not claim database change complete until Alembic migration is verified on disposable DB. Record schema changes in `SCHEMA_DIFF`.
- **UI and error states:** cover loading, empty, success_confirmed, forbidden, conflict, offline/unavailable; no fake success and no secret/PII logs; accessibility keyboard/2D when relevant. Respect `DEMO_MODE=false` in production.
- **Negative/abuse test (must fail before fix):** No results labeled learning improvement from sentiment only.
- **Minimum acceptance:** positive flow persists through reload/restart and correct account; required negative test passes; import clients updated; no incompatible HTTP response silently ignored; any risk that remains filed with owner and severity.
- **Test artifacts:** create/extend targeted test near existing test suite (proposed name `tests/v5/test_v5_t100.py`; adapt to current framework), include API integration and, for browser flow, Playwright or verified manual run. Check `git diff --check`, TS typing/Python compile/Rust format for touched stack. A test marked NOT_RUN cannot count as PASS.
- **Isolation contract:** A10 may draft patches only inside described feature boundary. Shared model/migration/router generated types must be submitted as change proposal to coordinator for serialized integration. Do not edit another subagent's committed worktree.
- **Evidence required:** file:line before/after, test commands+outputs, negative case screenshot/log without PII, DB rows count or trace where relevant, feature flag, rollback plan, `HANDOFF_JSON` and reviewer sign-off.
- **Fail policy:** on auth/rights/PII/source issue => BLOCKED and flag OFF; on provider/network failure show typed unavailable; on version conflict ask retry/rebase; on missing dependency report missing details, do not invent API or data.

**Wave W09 completion barrier:** 10/10 slots terminal, verified observed concurrency and cap, every blocking ticket integrated and tested, shared migrations approved, no production mock success, coordinator signed report. If any P0 issue or human sign-off pending: state `BLOCKED`; may start downstream design tasks but do not release dependent features.

