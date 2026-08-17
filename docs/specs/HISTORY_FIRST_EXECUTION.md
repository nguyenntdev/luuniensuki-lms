# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `055fcef` (main, 2026-08-17) — Phase 2 legacy migration committed + pushed.

## Current phase

Phase 2 — Legacy Corpus Migration (core done; questions migration pending real seed data). Phase 1 complete.

## Current branch

`main`

## Completed task IDs

- REPO-001..004: Phase 0 deliverables (system state, doc reconcile, baseline artifact, baseline tests).
- Phase 1: migration `0048_history_governance`, models, governance services + state machine/invariant, public + admin history APIs, 15 tests, OpenAPI snapshot regenerated.
- Phase 2: `scripts/history/migrate_legacy.py` (idempotent, dry-run/write, resumable); migration `0049_content_validation_status`; migrated 9 urns + 153 reliefs + 765 claims (AI/unreviewed) + 153 relations on test DB; 5 migration tests.

## In-progress task IDs

- Phase 2: questions blocked_for_authoritative_learning — script logic written; actual rows depend on seeded DB (test DB not seeded). Migration report artifact to be generated from a seeded run.
- REPO-004 (Rust baseline test): re-running after JWT parity fix.

## Tests run and results

- Python: `pytest tests/backend` → **136 passed** (131 + 5 history migration).
- Frontend: type-check pass, lint:ci pass, vitest 27 passed.
- Rust: first run 248 passed / 32 failed (JWT transition-off bug); fixed; re-running.

## Migrations added

- `0048_history_governance` — historical domain tables + search indexes.
- `0049_content_validation_status` — quiz_questions/lesson_content content_validation_status.

## API contracts changed

- Phase 1 history endpoints (public + admin) — see previous entry.
- OpenAPI snapshot regenerated twice (intentional).

## Frontend routes changed

- (none yet — Phase 3)

## Mobile changes

- (none yet)

## Historical content imported

- Test DB: 9 urns, 153 reliefs, 765 claims (all origin=ai_generated, verification=unreviewed, confidence=unknown), 153 located_on relations. No sources invented.

## Historical content awaiting review

- 765 claims (unreviewed/needs_source) — full human review backlog after real-seed migration.

## Architectural decisions

- DEC-0001..0005 — see DECISIONS doc.
- Migration report artifacts go under `artifacts/`; mapping via deterministic slug (legacy id → slug).

## Known blockers

- Production host disk tight during Rust cold builds; freed ~2.3G (node_modules, git gc, caches).
- Migration history branched; new migrations chain onto `0047`/`0048`.

## Known regressions

- (none; fixed pre-existing Rust JWT transition-off parity bug)

## Next executable tasks

1. Confirm Rust `cargo test` green.
2. Phase 2 finish: run migration on a seeded DB (prod-style) to generate `artifacts/history-migration-report.json`; verify question blocking.
3. Phase 3 — History-first public shell: middleware public paths, homepage V2, `/cuu-dinh`, urn routes, atlas stub.
4. Phase 4 — Atlas 162 (list/search/filter/relief pages + evidence UI).