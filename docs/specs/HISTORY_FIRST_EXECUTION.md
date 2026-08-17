# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `e448828` (main, 2026-08-17) — Phases 6+8+9 committed + pushed.

## Current phase

Phases 0-9 complete (code + tests + prod migration for 6/8/9). Phase 7 (3D hotspots) pending. Phases 10-14 pending.

## Current branch

`main`

## Production deployment state (2026-08-17)

- Migrations applied to prod: 0048, 0049, 0050 (history tables, content_validation_status, question V2 columns + history_question_types registry). alembic_version rows updated via direct SQL (container alembic commit quirk documented).
- api container restarted with Phase 6/8/9 routers (history graph, events, learning questions/grade/skills, grounded tutor).
- Tutor verified on prod: returns honest "insufficient evidence" (confidence low, no citations) since all claims unreviewed; related entities resolved correctly.
- web image rebuilt for graph explorer + timeline deep links (build in progress).
- Golden journey + all public routes verified 200 for guests.

## Completed task IDs

- REPO-001..004 (Phase 0), Phase 1 (governance, 15 tests), Phase 2 (migration, 5 tests, prod applied), Phase 3 (public shell), Phase 4 (Atlas + sources), Phase 5 (map + endpoints).
- Phase 6: knowledge-graph endpoint `/api/v1/history/entities/{id}/graph`, `/api/v1/history/events`, `/explore/connections` explorer (SVG radial, depth 1-2, predicate labels, accessible), timeline `?entity=` deep links.
- Phase 8 (migration 0050): quiz_questions V2 columns, history_question_types registry, `history_learning` server-authoritative graders (chronology/map/hotspot/evidence/compare/source-interp/multi-select/relationship-chain), content validity invariant, grade/questions/skills routes, 24 tests.
- Phase 9: `history_tutor` retrieval (Spec 37.1 precedence), delimited context (40.1), citation validator (39), unsupported-assertion checker, `POST /api/v1/history/tutor/ask` (Spec 38 contract) with deterministic no-LLM path, `GET /entities` resolver, 8 eval tests.

## In-progress task IDs

- web image rebuild (Phase 6 frontend deployment).

## Tests run and results

- Python: `pytest tests/backend` → **168 passed** (Phases 6/8/9 added 32).
- Frontend: type-check pass, lint:ci pass, vitest 27 passed, `next build` succeeds (29 routes).
- Rust: 291 passed (earlier).
- Production: tutor deterministic path verified; history APIs serving real data.

## Migrations added

- `0048_history_governance`, `0049_content_validation_status`, `0050_history_questions` — all applied to prod.

## API contracts changed

- 21 history routes in OpenAPI (entities, claims, sources, relations, geography, search, map, urns, graph, events, learning grade/questions/skills, tutor ask/entities, admin mutations, audit). Snapshot regenerated.

## Frontend routes changed

- Public: `/explore/connections` (graph explorer). `/timeline` now honors `?entity=` deep link. Urn/relief pages link to the graph.

## Mobile changes

- (none yet — Phase 12)

## Historical content imported

- Prod: 9 urns + 153 reliefs + 765 claims (unreviewed) + 153 relations + 12 timeline events exposed.

## Historical content awaiting review

- 765 claims unreviewed/needs_source; 347 quiz questions blocked until source-verified.

## Architectural decisions

- DEC-0001..0005 + container-alembic migration-application approach (direct SQL + manual version row). Tutor deterministic when no LLM key. Streaming tutor deferred (optional per spec).

## Known blockers

- Prod host disk ~91%+; prune build cache before/after web image builds.
- Container alembic 1.18.4 doesn't commit; use host venv via 172.18.0.5.
- Migration 0050 note: PG `question_type` enum not altered in-migration (enum ADD VALUE can't run in transaction); prod enum needs out-of-transaction ALTER before V2 questions seeded (V2 questions default correct_answer="", answer in answer_contract).

## Known regressions

- (none)

## Next executable tasks

1. Finish web deploy for Phase 6 (graph explorer).
2. Phase 7 — 3D hotspot integration: `?relief=` deep link → camera focus on UrnViewer, hotspot registry keyed to historical entity ids, history/source side panel.
3. Phase 10 — stories engine; Phase 11 — teacher collections; Phase 12 — mobile.
4. Phase 13 — accessibility/SEO/i18n/perf hardening.
5. Phase 14 — release: full suites, content validator, release report, final deploy.