# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `4be10f3` (main, 2026-08-17) — deployed to production https://lms.histolab.icu.

## Current phase

Phase 5 complete (map + endpoints). Phases 0-5 deployed to production. Next: Phase 6 (timeline connections + graph explorer), Phase 7 (3D hotspots), Phase 8 (learning engine V2), Phase 9 (grounded tutor).

## Current branch

`main`

## Production deployment state (2026-08-17)

- Migrations 0048 + 0049 applied to prod DB (historical_* tables + content_validation_status columns). Note: alembic version row was manually updated (container alembic 1.18.4 transaction-commit quirk under investigation; DDL verified applied).
- Legacy corpus migrated to prod: 9 urns (canonical slugs cao-dinh..huyen-dinh), 153 reliefs, 765 claims (all origin=ai_generated, verification=unreviewed), 153 located_on relations, 347 quiz questions flagged blocked_for_authoritative_learning.
- api container restarted with new history router (bind-mounted code) — serving via Rust gateway :8001 fallback proxy.
- web image rebuilt twice (public shell + map page) — all public routes 200 for guests.
- Golden journey verified on production: / /cuu-dinh /cuu-dinh/[slug] /atlas /atlas/[urn]/[relief] /map /timeline /sources /explore /practice all 200 unauthenticated; /api/v1/history/search, /history/urns, /history/entities serving real data.

## Completed task IDs

- REPO-001..004: Phase 0 deliverables.
- Phase 1: migration 0048 + governance model/services/APIs + 15 tests.
- Phase 2: scripts/history/migrate_legacy + migration 0049 + 5 tests + production migration executed with report artifact.
- Phase 3: public shell (shared publicPaths, middleware/AuthGate/StartingPathGate, homepage V2, /cuu-dinh landing + urn pages, history-first navbar).
- Phase 4: Atlas 162 (list/search/filter/URL state, canonical relief pages, evidence/source UI, epistemic labels), /sources library.
- Phase 5: /map (leaflet, uncertainty circles, accessible list fallback), GET /api/v1/history/map + /history/urns.

## In-progress task IDs

- (none)

## Tests run and results

- Python: `pytest tests/backend` → **136 passed** (135 + snapshot regen verified separately).
- Phase 8 (learning engine V2): `pytest tests/backend/test_history_learning.py tests/backend/test_history_governance.py` → **39 passed**. Full backend suite → **159 passed, 1 expected failure** (`test_openapi_snapshot` — OpenAPI drifted from committed snapshot due to the 5 new history-learning routes; NOT regenerated, intentional contract addition to be snapshotted in the Phase 8 commit).
- Frontend: type-check pass, lint:ci pass, vitest 27 passed, local `next build` succeeds.
- Rust: 291 passed (server, rustup cargo).
- Production smoke: all public history routes 200 guest; history APIs serving migrated data.

## Migrations added

- `0048_history_governance` (prod applied)
- `0049_content_validation_status` (prod applied)
- `0050_history_questions` (Phase 8, written 2026-08-17; applied to server test DB via direct SQL + manual `alembic_version` update due to the alembic non-commit quirk — same workaround as 0048/0049). Adds quiz_questions V2 columns (skill_dimensions/entity_id/claim_ids/source_ids/answer_contract), user_skill_levels.skill_dimensions, and the seeded `history_question_types` registry.

## API contracts changed

- 13 history endpoints (entities, by-slug, claims, claim sources, sources, relations, geography, search, map, urns + admin mutations + audit). OpenAPI snapshot regenerated ×3 (intentional).
- Phase 8: +5 history-learning endpoints — `POST /api/v1/history/questions/{id}/grade`, `GET /api/v1/history/questions`, `GET /api/v1/history/questions/{id}`, `POST /api/v1/history/questions` (staff), `GET /api/v1/history/skills/{user_id}`. OpenAPI snapshot NOT regenerated (pending the Phase 8 commit).

## Frontend routes changed

- Public (no login): `/` (V2), `/cuu-dinh`, `/cuu-dinh/[urnSlug]`, `/atlas`, `/atlas/[urnSlug]/[reliefSlug]`, `/map`, `/sources`, `/sources/[sourceId]`. Navbar history-first for guests.

## Mobile changes

- (none yet — Phase 12)

## Historical content imported

- Prod: 9 urns + 153 reliefs + 765 claims (ai_generated/unreviewed) + 153 relations. No sources invented.

## Historical content awaiting review

- 765 claims unreviewed/needs_source (full human-review backlog).
- 347 quiz questions blocked_for_authoritative_learning pending source verification.

## Architectural decisions

- DEC-0001..0005 (see DECISIONS). New: prod DB migration applied via direct SQL + manual alembic_version row update due to container alembic commit quirk (documented; DDL verified).

## Known blockers

- Production host disk chronically ~91-100%: web image builds need ~3GB headroom; prune build cache before/after every build.
- api container bind-mount serves new Python code on restart (no rebuild needed) — but the api IMAGE is stale; rebuild before any container recreation.
- Container alembic 1.18.4: `upgrade`/`stamp` transactions do not commit against prod DB (works on test DB with host venv 1.19.1); use host venv via docker bridge IP (172.18.0.5) for migrations until pin upgraded.

## Known regressions

- (none)

## Next executable tasks

1. Phase 6 — Timeline connections: link existing Rust timeline (heritage_eras/historical_events) to historical entities; /explore/connections graph explorer.
2. Phase 7 — 3D hotspot deep links (?relief= param → camera focus), history side panel.
3. Phase 8 — Question model V2 (chronology/map/hotspot/evidence types), mastery dimensions, FSRS integration.
4. Phase 9 — Source-grounded History Tutor (retrieval + citation validator + evals).
5. Phase 10-12 — stories, teacher collections, mobile.
6. Phase 13-14 — hardening + release report.