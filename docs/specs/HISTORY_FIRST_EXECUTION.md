# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `cd637b5` (main, 2026-08-17) — pushed to GitHub. Includes spec at `docs/specs/`, baseline frontend fixes, `docs/CURRENT_SYSTEM_STATE.md`, baseline artifact.

## Current phase

Phase 0 — Truth Reconciliation (nearly complete; Rust baseline test running on server).

## Current branch

`main`

## Completed task IDs

- REPO-001: `docs/CURRENT_SYSTEM_STATE.md` created (full service/route/DB/test/ops inventory).
- REPO-002: Reconcile docs — `README.md` (history-first + current Rust scope), `backend-rust/README.md` (current scope). `docs/ARCHITECTURE.md` verified current; stale docs logged in CURRENT_SYSTEM_STATE.
- REPO-003: Frontend consolidation debt — type-check green, lint:ci green, vitest 27 green. api.ts committed already; committed lint/test-fix leftovers (c2a727d).
- REPO-004: `artifacts/baseline-system-verification.json` created.

## In-progress task IDs

- REPO-004 (Rust baseline test): running `cargo test` on server via rustup cargo (system cargo 1.75 too old). 116 Python tests pass.

## Tests run and results

- Python: `pytest tests/backend` → **116 passed** (server test DB on 127.0.0.1:5433, db luuniensuki_test).
- Frontend: type-check pass, lint:ci pass, vitest 27 passed.
- Rust: cargo test in progress (cold build).

## Migrations added

- (none yet)

## API contracts changed

- (none yet)

## Frontend routes changed

- (none yet)

## Mobile changes

- (none yet)

## Historical content imported

- (none yet)

## Historical content awaiting review

- (none yet — pending legacy migration)

## Architectural decisions

- DEC-0001: work in git clone `luuniensuki-lms-main` (not stale snapshot).
- History domain will be built as new tables/migrations chained onto `0047_revoked_refresh_tokens`, served via a new Python FastAPI `/api/v1/history/*` router, proxied by the Rust gateway fallback; stable read groups may move to Rust native later. (See DECISIONS doc.)

## Known blockers

- Production host `/` at 95-98% capacity. Free space before any image builds. Test DB available on 127.0.0.1:5433.
- Migration history branched (3 alembic heads; prod alembic_version has 14 rows). New migrations chain onto `0047`.

## Known regressions

- (none yet)

## Next executable tasks

1. Confirm Rust baseline test result; finalize `artifacts/baseline-system-verification.json`.
2. Begin Phase 1 — Historical Governance Foundation:
   - Migration `0048_history_governance` (entities, claims, sources, claim_sources, relations, geographies, assets, audit log).
   - SQLAlchemy models in `backend/models.py`.
   - New `backend/routers/history.py` + `backend/services/history/*` + schemas.
   - RBAC roles (history_*).
   - Admin CRUD + public read endpoints under `/api/v1/history/*`.
   - Unit + integration tests (verification invariant, source eligibility).