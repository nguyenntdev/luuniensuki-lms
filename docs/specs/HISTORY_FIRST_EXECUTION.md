# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `e7d8db7` (main, 2026-08-17) — Phase 1 governance foundation committed + pushed.

## Current phase

Phase 1 — Historical Governance Foundation (nearly complete; Rust baseline test re-running after JWT parity fix).

## Current branch

`main`

## Completed task IDs

- REPO-001: `docs/CURRENT_SYSTEM_STATE.md` created (full service/route/DB/test/ops inventory).
- REPO-002: Reconcile docs — `README.md`, `backend-rust/README.md`; stale docs logged.
- REPO-003: Frontend consolidation debt — type-check/lint/unit green.
- REPO-004: `artifacts/baseline-system-verification.json` created.
- Phase 1 core: migration `0048_history_governance` (8 tables + indexes), `backend/history_models.py`, `backend/services/history_governance.py` (state machine + invariant), `backend/routers/history.py` (public reads + admin mutations + audit), 15 tests green, OpenAPI snapshot regenerated.
- Rust JWT parity bug fixed (transition-off `validate_aud`).

## In-progress task IDs

- REPO-004 (Rust baseline test): re-running `cargo test` after JWT fix (cold build).
- Phase 1 remaining: decide RBAC role granularity for history_* roles; add admin review workflow UI later; integrate Rust native read routes (optional).

## Tests run and results

- Python: `pytest tests/backend` → **131 passed** (incl. 15 history governance + regenerated OpenAPI snapshot).
- Frontend: type-check pass, lint:ci pass, vitest 27 passed.
- Rust: `cargo test` — first run 248 passed / 32 failed (mostly JWT InvalidAudience due to pre-existing transition-off bug); fixed, re-running.

## Migrations added

- `0048_history_governance` — chained onto `0047_revoked_refresh_tokens`. Verified on scratch DB (all 8 tables created; branched-history note: fresh `alembic upgrade head` conflicts on pre-existing 0011 duplicate column — apply via `--sql`/targeted upgrade in prod, prod already at 0047).

## API contracts changed

- Added `GET /api/v1/history/entities`, `/by-slug/{slug}`, `/{id}`, `/{id}/claims`, `/{id}/relations`, `/{id}/geography`, `/search`; `GET /api/v1/history/sources`, `/sources/{id}`, `/claims/{id}`, `/claims/{id}/sources`.
- Added admin mutations under `/api/v1/admin/history/*` (entities/sources/claims/claims/{id}/sources/claims/{id}/transition/relations/entities/{id}/geography/assets/audit).
- OpenAPI snapshot regenerated (intentional).

## Frontend routes changed

- (none yet — Phase 3)

## Mobile changes

- (none yet)

## Historical content imported

- (none yet — Phase 2)

## Historical content awaiting review

- (none yet — pending legacy migration)

## Architectural decisions

- DEC-0001: work in git clone `luuniensuki-lms-main`.
- DEC-0002: History domain served via new Python FastAPI router `/api/v1/history/*` (public reads) + `/api/v1/admin/history/*` (staff mutations); Rust gateway fallback proxies them natively. Stable read groups may move to Rust later.
- DEC-0003: Claim verification invariant enforced in service layer (`_can_be_expert_verified` requires eligible source + editor review for reviewable claim types).

## Known blockers

- Production host `/` hits 100% during Rust cold builds (needs ~2GB headroom; node_modules removed server-side, git gc done). Test DB on 127.0.0.1:5433.
- Migration history branched (3 alembic heads; prod alembic_version 14 rows). New migrations chain onto `0047`.

## Known regressions

- (none; existing Rust JWT transition-off bug being fixed)

## Next executable tasks

1. Confirm Rust `cargo test` green after JWT parity fix.
2. Phase 2 — Legacy corpus migration (`scripts/history/*`): inventory, normalize 9 urns + 153 motifs, segment claims (origin=ai_generated, unreviewed), migrate questions, mapping, report.
3. Phase 3 — Public shell (navbar, homepage V2, /cuu-dinh, urn routes, middleware public paths).