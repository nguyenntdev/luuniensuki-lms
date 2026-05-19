# Implementation Plan: Full Rust Backend Migration

## Overview

This plan executes the strangler-fig migration of the Luuniensuki LMS HTTP backend from
Python FastAPI (`backend/`, ~290 endpoints across 47 service modules) to Rust
(`backend-rust/`, Axum + Tokio + SQLx). The plan is organized as 16 sequential phases
matching the design's Phase Catalog. Each phase begins with a "Foundations" sub-task
(routing scaffold, DTOs, sqlx queries) and ends with a "Phase complete" sub-task that
ticks `docs/plan/full-rust-backend-migration-ledger.md` and re-runs the contract suite.

Every sub-task is small enough to review in isolation. Routes are grouped 3–6 per
sub-task. Each sub-task explicitly names the requirements and properties it validates,
and references an `Endpoint_Group` from the design. Test sub-tasks are marked optional
(`*`) but core implementation sub-tasks never are.

## Tasks

### Phase 0 — Foundations & Dispatcher

- [x] 1. Foundations & dispatcher
  - [x] 1.1 Add Axum + Tokio + Tower scaffold
    - Replace the std-lib TCP server in `backend-rust/src/main.rs` with `axum::serve` + `#[tokio::main]`.
    - Add pinned exact-version deps to `backend-rust/Cargo.toml`: `tokio`, `axum`, `tower`, `tower-http`, `serde`, `serde_json`, `anyhow`, `thiserror`, `dotenvy`, `tracing`, `tracing-subscriber`.
    - Wire a graceful-shutdown handler driven by `tokio::signal::unix::SIGTERM`/`SIGINT`.
    - Record peak release-build RSS in `backend-rust/docs/build-budget.md` for every dep added.
    - **Validates:** Req 11.1, 11.3, 11.4, 12.1; Property 20

  - [x] 1.2 Wire `sqlx::PgPool` and config
    - Add `sqlx = "0.7.x"` (postgres + chrono + uuid + json + runtime-tokio-rustls), pinned exact.
    - Implement `db::pool(&Settings)` with `PgPoolOptions::max_connections` and 5s acquire timeout.
    - Extend `config::Settings` with `database_url`, `database_max_connections`, `route_modes_path`, `route_inventory_path`, `bind_addr`, `uploads_dir`, JWT fields.
    - Implement `db::ping(&pool)` issuing `SELECT 1`.
    - Use runtime `sqlx::query` / `query_as` only (no `query!` macros), so the build needs no live DB.
    - **Validates:** Req 6.1, 11.1, 11.3, 11.4, 12.2

  - [x] 1.3 Implement structured tracing + request_id middleware
    - Configure `tracing-subscriber` with JSON formatter and the field set `request_id, method, path, status, latency_ms, mode`.
    - Build a `tower_http::trace::TraceLayer` + custom `request_id` layer that reads or mints `X-Request-Id`, sets it on the span, and writes it to the response.
    - **Validates:** Req 3.6, 12.3, 12.4; Property 10, Property 18

  - [ ]* 1.4 Property test for per-request structured log
    - **Property 10: Per-request structured log** — every served request emits exactly one info-level JSON line with the required fields and `mode ∈ {native, gateway}`.
    - **Property 18: 5xx error logging** — every 5xx response emits exactly one error-level JSON line with `request_id`, route, and error chain.
    - **Validates:** Req 3.6, 12.3, 12.4

  - [x] 1.5 Implement strangler dispatcher with hot-reload
    - Create `backend-rust/src/dispatcher.rs` holding `ArcSwap<HashMap<MethodPath, Mode>>`.
    - Parse `backend-rust/config/route-modes.toml` (`[routes]` and `[defaults]`) at startup; reject values other than `"native"` / `"gateway"`.
    - Spawn a reload task: `tokio::signal::unix::SIGHUP` for immediate reload + `tokio::time::interval(30s)` poll using mtime check.
    - Preserve in-flight requests across reloads (no abort on hot-swap).
    - **Validates:** Req 13.1, 13.2, 13.4

  - [ ]* 1.6 Property test for route-mode dispatcher
    - **Property 17: Route-mode dispatcher and AI tutor pinning** — for any `(route, mode)` mutation, new requests pick up the mode within 30s (or immediately on SIGHUP) and in-flight requests complete under their original mode.
    - **Validates:** Req 9.1, 13.1, 13.2, 13.4

  - [x] 1.7 Implement `gateway::proxy_to_python` with reqwest 0.12
    - Add pinned `reqwest = "0.12.x"` with rustls-tls + stream + json features.
    - Build a long-lived `reqwest::Client` stored in `AppState`.
    - Forward `Authorization`, `Cookie`, `Content-Type`, `Accept`, `X-Forwarded-*`, `X-Request-Id` byte-for-byte; rewrite `Host`.
    - Stream request and response bodies (`reqwest::Body::wrap_stream`); preserve status, body bytes, `Content-Type`, `Content-Length`.
    - Map `reqwest::Error` (connect refused / timeout / read timeout) → `AppError::UpstreamUnavailable` returning HTTP 502 with body exactly `{"detail":"upstream unavailable"}`.
    - Wire `Router::fallback(gateway::fallback_to_python)` for any path not matched natively.
    - **Validates:** Req 3.2, 3.3, 3.4, 3.5; Property 7, Property 8, Property 9

  - [ ]* 1.8 Property tests for gateway preservation, header forwarding, upstream-unavailable
    - **Property 7: Gateway response preservation** — random `(status, body bytes, headers)` from a fake Python upstream are returned byte-identically.
    - **Property 8: Gateway header forwarding** — `Authorization`, `Cookie`, `Content-Type`, `Accept` arrive at upstream byte-identical.
    - **Property 9: Upstream-unavailable error shape** — connect failure / timeout always yields HTTP 502 + `{"detail":"upstream unavailable"}`.
    - **Validates:** Req 3.2, 3.3, 3.4, 3.5

  - [x] 1.9 Implement error envelope (`error::AppError` → `IntoResponse`)
    - Variants: `Validation { details }` (422, `VALIDATION_ERROR`), `Http { status, message }` (`HTTP_ERROR`), `Domain { status, code, message, details }`, `Unauthorized` (401 + `WWW-Authenticate: Bearer`), `UpstreamUnavailable` (502, FastAPI shape).
    - Body envelope `{"error": {"code", "message", "details"}}` matches `backend/errors.py::app_exception_handler` byte-for-byte.
    - Wire `tower_http::catch_panic` mapping panics → 500 `INTERNAL_SERVER_ERROR`.
    - **Validates:** Req 3.5, 5.6, 12.4

  - [x] 1.10 Build `inventory.rs` and `GET /api/v1/internal/route-coverage`
    - Load `backend-rust/docs/route-inventory.json` at startup into an `Arc<Vec<InventoryEntry>>`.
    - Implement `inventory::assert_full_coverage(&Router, &Dispatcher)`: every entry must match a registered native handler OR `gateway::fallback_to_python`. On gap: return error → `main()` exits non-zero.
    - Implement `routes::internal::route_coverage` returning the JSON shape from the design (`routes[]` with `method/path/group/status/native_handler_registered/override` and `summary` with `total/native/gateway/groups_complete/groups_total/ready_for_cutover`).
    - **Validates:** Req 2.4, 2.5, 10.1, 10.3, 13.3; Property 3, Property 5

  - [ ]* 1.11 Property tests for inventory coverage and route-coverage shape
    - **Property 3: Inventory coverage** — startup succeeds iff every inventory route is matched by a native handler or fallback.
    - **Property 5: Route-coverage endpoint correctness** — JSON `status` always equals the effective dispatcher mode for every route.
    - **Validates:** Req 2.1, 2.3, 2.4, 2.5, 10.3, 13.3

  - [x] 1.12 Build `scripts/dev/generate_route_inventory.py`
    - Import `backend.main:app` and walk `app.routes`; emit `(method, path, group)` tuples.
    - Sort deterministically by `(group, path, method)` and write `backend-rust/docs/route-inventory.json` with stable formatting.
    - Add CI lint that regenerates the file and fails on non-empty diff.
    - **Validates:** Req 1.6, 2.1, 2.2, 2.3; Property 4

  - [ ]* 1.13 Property test for inventory generator determinism
    - **Property 4: Inventory generator determinism** — two consecutive runs against the same FastAPI app state produce byte-identical JSON.
    - **Validates:** Req 2.2

  - [x] 1.14 Seed the migration ledger
    - Create `docs/plan/full-rust-backend-migration-ledger.md` with the 16 phase headers and unchecked nested checkboxes for every route in the inventory.
    - Render rules: nested `- [ ]` per route, `_(commit_sha, YYYY-MM-DD)_` italic suffix on tick, `Completed: <sha> <date>` line on full-phase tick.
    - Regenerate the `Summary` section from document state.
    - **Validates:** Req 1.1, 1.2, 1.5; Property 1, Property 2

  - [ ]* 1.15 Property tests for ledger structural invariants and atomicity
    - **Property 1: Ledger structural invariants** — exactly one top-level checkbox per group, exactly one nested checkbox per route, single `Completed:` line on group completion.
    - **Property 2: Ledger atomicity** — a phase header is checked iff every route in the phase is checked, every route is `native` in `route-modes.toml`, and every route's contract test passes.
    - **Validates:** Req 1.1, 1.2, 1.4, 1.5, 7.3

  - [x] 1.16 Migrate currently-native routes to the new Axum router
    - Move `GET /health`, `GET /api/v1/internal/db-health`, `GET /api/v1/content/ratings`, `GET /api/v1/ranks`, `GET /api/v1/tags`, `GET /api/v1/badges` (list), `GET /api/v1/users/me/streak` from `backend-rust/src/main.rs` (std-lib HTTP) to Axum handlers in `routes/health.rs`, `routes/content.rs`, `routes/badges.rs`, `routes/users.rs`.
    - Delete the hand-rolled HTTP parsing once Axum routes pass their existing unit tests.
    - **Validates:** Req 3.1, 12.1, 12.2; Property 6

  - [x] 1.17 Wire `axum-prometheus` `/metrics`
    - Add pinned `axum-prometheus = "0.6.x"`.
    - Apply `PrometheusMetricLayer` to the top-level router; expose `GET /metrics`.
    - Label per-route counters and latency histograms with `(method, path, status, mode)`.
    - **Validates:** Req 12.5; Property 19

  - [ ]* 1.18 Property test for metrics emission
    - **Property 19: Metrics emission per request** — exactly one counter increment and one latency observation per request, labeled `(method, path, status, mode)`.
    - **Validates:** Req 12.5

  - [x] 1.19 Update Dockerfile with cargo-chef multi-stage build
    - Replace current Dockerfile with `chef → planner → builder → runtime` stages from the design.
    - Set `CARGO_BUILD_JOBS=1`, `CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1`, `CARGO_PROFILE_RELEASE_LTO=thin`.
    - Copy `backend-rust/config/` and `backend-rust/docs/route-inventory.json` into the runtime image.
    - Document build host RSS measurement in `backend-rust/docs/build-budget.md`.
    - **Validates:** Req 11.1, 11.2, 11.3

  - [x] 1.20 Build the contract test harness
    - Create `backend-rust/tests/contract/` with a `harness.rs` that loads snapshot fixtures and a per-route ignore-list from `tests/contract/ignore.toml`.
    - Implement equivalence: status equal, `Content-Type` equal, JSON structurally equal modulo per-route `ignore_fields`.
    - Add `scripts/testing/capture_python_snapshots.py` that exercises Python with a deterministic seed corpus and writes `tests/contract/fixtures/<group>/<route>/<case>.json`.
    - For every migrated route, the harness MUST run at minimum: 1 happy path, 1 input-validation-error case, 1 auth/authz-error case.
    - **Validates:** Req 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8; Property 11

  - [x] 1.21 Add CI lints
    - Ledger sync lint: rejects PRs that flip a route to `native` in `route-modes.toml` without ticking the matching ledger box.
    - Inventory drift lint: regenerates `route-inventory.json` and fails on non-empty diff.
    - Pinned-deps lint: scans `Cargo.toml` for unpinned versions (Property 20 enforcement).
    - Build-budget lint: every direct dep in `Cargo.toml` must have a row in `build-budget.md`.
    - AI-tutor pinning lint: every route listed in `backend-rust/docs/ai-tutor-routing.md` must be pinned `gateway` in `route-modes.toml`.
    - Migration safety lint: rejects new SQL migrations containing `DROP TABLE | DROP COLUMN | ALTER COLUMN | RENAME` against existing tables.
    - **Validates:** Req 1.3, 1.6, 2.3, 6.2, 9.2, 11.2, 11.4; Property 17, Property 20

  - [x] 1.22 Phase 0 complete: tick ledger and verify foundations
    - Ensure all foundations tests pass (`cargo test`, contract harness smoke).
    - Tick the Phase 0 routes (`/health`, `/api/v1/internal/db-health`, `/api/v1/internal/route-coverage`) in `docs/plan/full-rust-backend-migration-ledger.md` with commit SHA + date.
    - Verify `GET /api/v1/internal/route-coverage` reports the foundations routes as `native` and all unmigrated routes as `gateway`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.5, 7.2, 7.3

### Phase 1 — Public Reads (Cleanup)

- [x] 2. Public reads cleanup
  - [x] 2.1 Verify Phase-1 native routes pass contract tests under new Axum
    - Run the contract suite for `GET /api/v1/content/ratings`, `GET /api/v1/ranks`, `GET /api/v1/tags`, `GET /api/v1/badges` (list), `GET /api/v1/users/me/streak`.
    - Each must show status equality, `Content-Type` equality, and JSON equivalence vs Python snapshots.
    - **Validates:** Req 4.2, 4.3, 4.4, 7.6; Property 11

  - [ ]* 2.2 Property tests for native dispatch isolation on public reads
    - **Property 6: Native dispatch isolation** — for these registered routes, the gateway client is never invoked.
    - **Validates:** Req 3.1

  - [x] 2.3 Phase 1 complete: tick ledger
    - Tick all Phase-1 route boxes with SHA + date and tick the phase header (`Completed:` line) in the ledger.
    - Re-run the contract suite and confirm `route-coverage` reports all Phase-1 routes as `native`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 1.5, 7.3

### Phase 2 — Auth

- [x] 3. Auth migration
  - [x] 3.1 Auth foundations
    - Add pinned `jsonwebtoken = "9"`, `bcrypt = "0.15"`, `argon2 = "0.5"`, `validator = "0.18"`.
    - Implement `auth::issue_access_token` / `auth::issue_refresh_token` with HS256 + claims `{sub, iat, exp, role, type}` matching `backend/security.py::create_jwt_token`.
    - Implement `auth::verify_access_token` / `verify_refresh_token` rejecting wrong `type`.
    - Implement `auth::verify_password` dispatching on hash prefix (`$2[aby]$` → bcrypt, `$argon2id$|$argon2i$` → argon2); never rehash on success.
    - Build `routes/auth.rs` module skeleton + DTOs (`LoginRequest`, `RegisterRequest`, `TokenResponse`, etc.).
    - **Validates:** Req 5.1, 5.2, 5.3, 5.4, 5.5, 5.7

  - [x] 3.2 Migrate `GET /api/v1/auth/me`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`
    - Implement Axum handlers using sqlx queries against `users`.
    - `/auth/me` returns the current user DTO; `/auth/refresh` rotates token using stored refresh-token rules; `/auth/logout` invalidates the session.
    - Add Phase-2 contract fixtures and ignore-list entries.
    - **Validates:** Req 5.1, 5.2, 5.5, 5.6, 7.6

  - [x] 3.3 Migrate `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
    - `/auth/register` creates the user with a bcrypt hash at the same cost (`rounds=12`) Python uses.
    - `/auth/login` verifies the password against the stored hash without rehashing.
    - Issue access + refresh cookies (`luuniensuki_access`, `luuniensuki_refresh`) with the same flags Python sets.
    - **Validates:** Req 5.3, 5.4, 5.7

  - [x] 3.4 Migrate `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`, `POST /api/v1/auth/age-verify`
    - Implement reset-token lifecycle reusing the existing `password_reset_tokens` table.
    - `age-verify` writes to the user profile and returns the same DTO Python returns.
    - **Validates:** Req 5.6, 6.1

  - [ ]* 3.5 Property test for bidirectional JWT interop
    - **Property 12: Bidirectional JWT interop** — random `(sub, role, type, iat, exp)` claim sets signed by either Python (`jose`) or Rust (`jsonwebtoken`) verify on the other side.
    - **Validates:** Req 5.1, 5.2, 5.5

  - [ ]* 3.6 Property test for password verify across schemes and new-hash format parity
    - **Property 13: Password verify across schemes; new-hash format parity** — random passwords with bcrypt or argon2id reference hashes verify true without rehashing; new Rust-issued hashes have the same prefix and cost as Python's.
    - **Validates:** Req 5.3, 5.4

  - [ ]* 3.7 Property test for auth-error envelope parity
    - **Property 14: Auth-error envelope parity** — for expired / malformed / unknown-key tokens, Rust returns HTTP 401 with body and headers byte-equal to Python.
    - **Validates:** Req 5.6

  - [x] 3.8 Phase 2 complete: tick ledger
    - Flip every `/api/v1/auth/*` route to `native` in `route-modes.toml`.
    - Tick the eight auth routes in the ledger with SHA + date; tick the phase header.
    - Re-run the contract suite (auth fixtures) and confirm `route-coverage` shows all auth routes native.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3, 7.6

### Phase 3 — Users & Profile

- [x] 4. Users & profile migration
  - [x] 4.1 Users foundations: DTOs and sqlx queries
    - Add `models/user.rs` with row DTO + response DTO (mirroring `backend/models.py::User`).
    - Build `services/user_service.rs` with `update_profile`, `change_password`, `set_starting_path`, `get_public_profile`, `set_onboarding`, `get_onboarding`.
    - Build `routes/users.rs` skeleton with `with_state(pool)`.
    - **Validates:** Req 6.1, 6.4

  - [x] 4.2 Migrate `PATCH /api/v1/users/me`, `POST /api/v1/users/me/change-password`, `POST /api/v1/users/me/starting-path`, `GET|POST /api/v1/users/me/onboarding`
    - Implement Axum handlers wired to `user_service`.
    - Apply `validator` to enforce the same field rules Python applies (length, charset, allowed enums).
    - **Validates:** Req 5.3, 5.4, 6.1, 6.4

  - [x] 4.3 Migrate `POST /api/v1/users/me/avatar` (multipart upload)
    - Use `axum::extract::Multipart` to accept the same field name (`file`) Python accepts.
    - Enforce identical MIME-type allow-list and file-size limit.
    - Write to the same uploads directory and return the same publicly addressable URL pattern (`/uploads/avatars/{uuid}.{ext}`) as Python.
    - On size or MIME rejection, return the same status and JSON body Python returns.
    - **Validates:** Req 8.1, 8.2, 8.3, 8.4

  - [ ]* 4.4 Property test for upload parity
    - **Property 16: Upload parity** — for any multipart upload, accept iff Python accepts; on-disk path and public URL match Python's; rejections return identical status + body.
    - **Validates:** Req 8.1, 8.2, 8.3, 8.4

  - [x] 4.5 Migrate `GET /api/v1/users/{id}/public` and `GET /u/{username_or_id}`
    - Resolve username vs UUID with the same precedence Python uses.
    - Return the public profile DTO (omitting private fields) byte-equivalent to Python's response.
    - **Validates:** Req 4.5, 6.1

  - [ ]* 4.6 Property tests for database write parity (users)
    - **Property 15: Database write parity and constraint-violation status parity** — generated profile updates produce rows equal to Python's; constraint violations (duplicate username/email) return the same status as Python.
    - **Validates:** Req 6.2, 6.3, 6.4, 6.5

  - [x] 4.7 Phase 3 complete: tick ledger
    - Flip Phase-3 routes to `native` in `route-modes.toml`; tick boxes with SHA + date; tick the phase header.
    - Re-run contract suite (users fixtures); verify `route-coverage`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3, 7.6

### Phase 4 — Lessons & Content

- [x] 5. Lessons & content migration
  - [x] 5.1 Lessons foundations: DTOs and sqlx queries
    - Add `models/{urn,motif,lesson}.rs` with row + response DTOs mirroring `backend/models.py`.
    - Build `services/lesson_service.rs` covering urns, motifs, lesson sequence, prerequisites, cache manifest, next-lesson, motif coordinates, complete-lesson.
    - **Validates:** Req 6.1

  - [x] 5.2 Migrate `GET /api/v1/urns`, `GET /api/v1/urns/{id}`
    - Implement list and detail handlers; preserve Python's deterministic ordering (e.g., `ORDER BY created_at, id`).
    - **Validates:** Req 4.5, 6.1

  - [x] 5.3 Migrate `GET /api/v1/motifs`, `GET /api/v1/motifs/{id}`, `GET /api/v1/motifs/{id}/coordinates`
    - Implement list, detail, and coordinates handlers.
    - **Validates:** Req 4.5, 6.1

  - [x] 5.4 Migrate `GET /api/v1/lessons/{id}/cache-manifest`, `/sequence`, `/prerequisites`, `/is-unlocked`, `/next`
    - Translate `services/lesson_sequence.py` and `services/recommendations.py` business rules to Rust faithfully.
    - **Validates:** Req 4.5, 6.1, 6.4

  - [x] 5.5 Migrate `POST /api/v1/motifs/{id}/complete-lesson`
    - Update progress + streak + XP + hearts atomically in a `sqlx::Transaction`; emit the same XP/streak deltas Python emits.
    - **Validates:** Req 6.4, 6.5

  - [ ]* 5.6 Property tests for lessons (write parity + contract)
    - **Property 11: Contract equivalence for native routes** for every Phase-4 read route.
    - **Property 15: Database write parity** for `complete-lesson`.
    - **Validates:** Req 4.2, 4.3, 4.4, 4.5, 6.4, 6.5

  - [ ] 5.7 Phase 4 complete: tick ledger
    - Flip Phase-4 routes to `native`; tick boxes + phase header.
    - Re-run contract suite; verify `route-coverage`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 5 — Quizzes & Adaptive

- [x] 6. Quizzes & adaptive migration
  - [x] 6.1 Quizzes foundations: DTOs and sqlx queries
    - Add `models/quiz.rs`, `services/quiz_service.rs` mirroring `services/adaptive_quiz.py`, `services/quiz_hints.py`, `services/spaced_repetition.py`.
    - **Validates:** Req 6.1

  - [x] 6.2 Migrate `GET /api/v1/quizzes/{id}`
    - Return the full quiz DTO; preserve question ordering and answer-shuffling deterministically (seed by `(user_id, quiz_id)` if Python does).
    - **Validates:** Req 4.5, 6.1

  - [x] 6.3 Migrate `POST /api/v1/quizzes/{id}/submit` and `POST /api/v1/quizzes/adaptive`
    - Score the submission, update `quiz_attempts`, write spaced-repetition state, return same DTO Python returns.
    - **Validates:** Req 6.4, 6.5

  - [x] 6.4 Migrate `GET /api/v1/quizzes/{id}/hints`
    - Implement hint retrieval and gating identical to Python.
    - **Validates:** Req 4.5

  - [ ]* 6.5 Property tests for quiz write parity and contract equivalence
    - **Property 11** for read routes; **Property 15** for `submit` and adaptive.
    - **Validates:** Req 4.2–4.5, 6.4, 6.5

  - [ ] 6.6 Phase 5 complete: tick ledger
    - Flip Phase-5 routes to `native`; tick boxes + phase header; re-run contract suite; verify `route-coverage`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 6 — Progress & Streaks

- [x] 7. Progress & streaks migration
  - [x] 7.1 Progress foundations: DTOs and sqlx queries
    - Add `models/{progress,streak,hearts,daily_goal,milestone}.rs`.
    - Build `services/progress_service.rs` mirroring `services/student_progress.py`, `services/streak.py`, `services/hearts.py`, `services/daily_goal_settings.py`, `services/milestones.py`.
    - **Validates:** Req 6.1

  - [x] 7.2 Migrate `POST /api/v1/progress/unlock`, `GET|POST /api/v1/users/me/streak`
    - Apply streak rules with the same timezone handling Python uses.
    - **Validates:** Req 6.4, 6.5

  - [x] 7.3 Migrate `GET|POST /api/v1/users/me/hearts`, `GET|PUT /api/v1/users/me/daily-goal`, `GET /api/v1/users/me/milestones`
    - Implement heart regen + spend rules; daily-goal CRUD; milestone read.
    - **Validates:** Req 6.4

  - [ ]* 7.4 Property tests for streak and hearts write parity
    - **Property 15** — generated heart spend / streak update sequences produce rows identical to Python.
    - **Validates:** Req 6.4

  - [ ] 7.5 Phase 6 complete: tick ledger
    - Flip Phase-6 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 7 — Badges, Quests, Achievements

- [x] 8. Badges, quests, achievements migration
  - [x] 8.1 Migrate `POST /api/v1/badges/{id}/award`
    - Award badge with idempotent insert (`ON CONFLICT DO NOTHING`); return Python's exact response on first vs subsequent award.
    - **Validates:** Req 6.4, 6.5

  - [x] 8.2 Migrate `GET /api/v1/quests`, `GET /api/v1/quests/{id}`, `POST /api/v1/quests/{id}/start`, `GET /api/v1/quests/weekly`
    - Mirror `services/quest_assignments.py` and `services/weekly_quests.py`.
    - **Validates:** Req 4.5, 6.4

  - [x] 8.3 Migrate `GET /api/v1/missions/daily` (daily missions)
    - Return the same daily-mission DTO Python returns; preserve deterministic ordering.
    - **Validates:** Req 4.5

  - [ ]* 8.4 Property tests for badges & quests
    - **Property 11** for reads; **Property 15** for award and quest start.
    - **Validates:** Req 4.2–4.5, 6.4

  - [ ] 8.5 Phase 7 complete: tick ledger
    - Flip Phase-7 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 8 — Classrooms & Memberships

- [x] 9. Classrooms migration
  - [x] 9.1 Classrooms foundations: DTOs and sqlx queries
    - Add `models/classroom.rs`; build `services/classroom_service.rs` mirroring `services/classroom.py` and the membership/sharing parts of `services/sharing.py`.
    - **Validates:** Req 6.1

  - [x] 9.2 Migrate classrooms CRUD: `POST|GET /api/v1/classrooms`, `GET|PATCH|DELETE /api/v1/classrooms/{id}`
    - Owner/teacher authorization checks identical to Python's role guards.
    - **Validates:** Req 5.5, 6.4

  - [x] 9.3 Migrate members + lessons: `GET|POST|DELETE /api/v1/classrooms/{id}/members`, `GET|POST /api/v1/classrooms/{id}/lessons`
    - Enforce membership constraints; preserve Python's response on duplicate-member 409.
    - **Validates:** Req 6.4, 6.5

  - [x] 9.4 Migrate `GET /api/v1/classrooms/{id}/analytics`
    - Aggregation queries returning the same DTO shape Python returns.
    - **Validates:** Req 4.5

  - [ ]* 9.5 Property tests for classrooms
    - **Property 11** for reads; **Property 15** for CRUD + member operations.
    - **Validates:** Req 4.2–4.5, 6.4, 6.5

  - [ ] 9.6 Phase 8 complete: tick ledger
    - Flip Phase-8 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 9 — Leaderboards & Leagues

- [x] 10. Leaderboards & leagues migration
  - [x] 10.1 Migrate `GET /api/v1/leaderboard`, `GET /api/v1/leaderboard/friends`
    - Translate `services/leaderboard.py` window/timeframe rules.
    - **Validates:** Req 4.5

  - [x] 10.2 Migrate `GET /api/v1/leagues`, `GET /api/v1/leagues/me`, `GET /api/v1/leagues/{id}`
    - Mirror `services/leagues.py` league assignment + rank window logic.
    - **Validates:** Req 4.5

  - [ ]* 10.3 Property tests for leaderboards & leagues
    - **Property 11** for all read routes; verify ordering parity.
    - **Validates:** Req 4.5

  - [ ] 10.4 Phase 9 complete: tick ledger
    - Flip Phase-9 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 10 — Notifications

- [ ] 11. Notifications migration
  - [ ] 11.1 Migrate `GET|PUT /api/v1/users/me/notification-settings`
    - CRUD over `notification_settings` row; preserve all field defaults.
    - **Validates:** Req 6.4

  - [ ] 11.2 Migrate `POST /api/v1/push/register`, `POST /api/v1/push/unregister`
    - Token registration / unregistration mirroring `services/push_notifications.py`.
    - **Validates:** Req 6.4, 6.5

  - [ ] 11.3 Migrate `GET /api/v1/notifications/history`, `GET /api/v1/notifications/should-prompt-permission`
    - History query with pagination + permission-prompt heuristic identical to Python.
    - **Validates:** Req 4.5

  - [ ]* 11.4 Property tests for notifications
    - **Property 11** for reads; **Property 15** for register/unregister.
    - **Validates:** Req 4.2–4.5, 6.4

  - [ ] 11.5 Phase 10 complete: tick ledger
    - Flip Phase-10 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 11 — Sessions, Heartbeat, Analytics Events

- [ ] 12. Sessions & analytics migration
  - [ ] 12.1 Migrate `POST /api/v1/sessions`, `POST /api/v1/sessions/heartbeat`, `POST /api/v1/sessions/end`
    - Mirror session lifecycle from `services/live_session_reporting.py` (HTTP face only — the live AI worker stays in Python).
    - **Validates:** Req 6.4, 6.5

  - [ ] 12.2 Migrate `POST /api/v1/analytics/events`, `POST /api/v1/analytics/batch`
    - Batch insert into the analytics-event table; honor the same payload validation Python applies.
    - **Validates:** Req 6.4

  - [ ]* 12.3 Property tests for analytics write parity
    - **Property 15** — generated event payloads produce DB rows identical to Python's.
    - **Validates:** Req 6.4

  - [ ] 12.4 Phase 11 complete: tick ledger
    - Flip Phase-11 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 12 — Crash Reports

- [ ] 13. Crash reports migration
  - [ ] 13.1 Migrate `POST /api/v1/crash-reports`
    - Accept the same payload shape Python accepts; persist to the crash-report table.
    - **Validates:** Req 6.4

  - [ ]* 13.2 Property tests for crash-reports write parity
    - **Property 15** — generated crash payloads produce rows identical to Python's.
    - **Validates:** Req 6.4

  - [ ] 13.3 Phase 12 complete: tick ledger
    - Flip `POST /api/v1/crash-reports` to `native` (admin-face crash routes are deferred to Phase 13).
    - Tick the route + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 13 — Admin

- [ ] 14. Admin migration
  - [ ] 14.1 Admin foundations: DTOs and authorization
    - Add `models/admin.rs`; centralize `require_admin` extractor checking the `role` claim.
    - **Validates:** Req 5.5, 6.1

  - [ ] 14.2 Migrate `POST /api/v1/admin/push-broadcast`
    - Validate audience filters; enqueue / send via the existing push backend.
    - **Validates:** Req 6.4

  - [ ] 14.3 Migrate audit and abuse-reports admin: `GET /api/v1/admin/audit`, `GET|POST /api/v1/admin/abuse-reports`, `POST /api/v1/admin/abuse-reports/{id}/resolve`
    - Mirror `services/audit.py` and `services/abuse_reports.py`.
    - **Validates:** Req 4.5, 6.4

  - [ ] 14.4 Migrate experiments + feature flags: `GET|POST /api/v1/admin/experiments`, `GET|POST /api/v1/admin/feature-flags`
    - Mirror `services/experiments.py`, `services/experiment_analytics.py`, `services/feature_flags.py`.
    - **Validates:** Req 4.5, 6.4

  - [ ] 14.5 Migrate analytics dashboards: `GET /api/v1/admin/analytics/*`
    - Mirror `services/analytics_dashboard.py` aggregation queries.
    - **Validates:** Req 4.5

  - [ ] 14.6 Migrate AI insights + embeddings admin: `GET /api/v1/admin/ai-insights`, `GET /api/v1/admin/embeddings`
    - Mirror `services/ai_insights.py`, `services/embeddings.py` (HTTP face only).
    - **Validates:** Req 4.5

  - [ ] 14.7 Migrate admin crash-reports: `GET /api/v1/admin/crash-reports`, `GET /api/v1/admin/crash-reports/{id}`, `POST /api/v1/admin/crash-reports/{id}/resolve`, `GET /api/v1/admin/crash-reports/stats`
    - Complete the admin face deferred from Phase 12.
    - **Validates:** Req 4.5, 6.4

  - [ ] 14.8 Migrate admin content management: `GET|POST /api/v1/admin/content/*`
    - Mirror admin content CRUD endpoints registered in `backend/main.py`.
    - **Validates:** Req 4.5, 6.4

  - [ ]* 14.9 Property tests for admin write parity and contract equivalence
    - **Property 11** for reads; **Property 15** for writes (experiments, feature flags, abuse-report resolution).
    - **Validates:** Req 4.2–4.5, 6.4

  - [ ] 14.10 Phase 13 complete: tick ledger
    - Flip Phase-13 routes to `native`; tick boxes + phase header; re-run contract suite.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3

### Phase 14 — Live AI Teacher Routing (Gateway-Pinned)

- [ ] 15. Live AI teacher routing
  - [ ] 15.1 Pin all `/api/v1/live/*` and `/api/v1/ai-tutor/*` routes to gateway
    - Add explicit `"<METHOD> <path>" = "gateway"` entries in `backend-rust/config/route-modes.toml` for every route in the inventory under `services/live_*` and `services/ai_tutor.py`.
    - Verify the dispatcher reports `override = "gateway"` for these routes via `route-coverage`.
    - **Validates:** Req 9.1, 9.4, 13.1, 13.2; Property 17

  - [ ] 15.2 Document AI tutor routing decisions
    - Create `backend-rust/docs/ai-tutor-routing.md` listing every AI/live route with its routing strategy (`gateway` for this migration; `native rewrite` is out of scope).
    - **Validates:** Req 9.2, 9.4

  - [ ] 15.3 Wire AI-tutor pinning CI lint
    - The lint asserts every route in `ai-tutor-routing.md`'s gateway list is pinned `gateway` in `route-modes.toml`. Fail CI on drift.
    - **Validates:** Req 9.1, 9.2; Property 17

  - [ ]* 15.4 Property test for AI tutor pinning
    - **Property 17 (AI tutor pinning clause)** — every AI-worker route is dispatched in `gateway` mode regardless of whether a native handler exists.
    - **Validates:** Req 9.1

  - [ ] 15.5 Phase 14 complete: tick ledger as "gateway-pinned, no native migration intended"
    - In the ledger, mark each AI/live route with a note `(gateway-pinned)` instead of a tick; tick the phase header with `Completed (gateway-pinned): <sha> <date>`.
    - Re-run the contract suite for AI routes against the gateway.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 9.1, 9.2, 9.4

### Phase 15 — Misc / Cleanup

- [ ] 16. Miscellaneous migration
  - [ ] 16.1 Diff inventory vs migrated routes
    - Run a script that compares `route-inventory.json` against the routes flipped to `native` in `route-modes.toml`. Output the leftover set.
    - **Validates:** Req 1.6, 2.1, 2.3

  - [ ] 16.2 Migrate leftover routes (preview, social, sharing helpers, content helpers)
    - Implement Axum handlers for any inventory route not yet placed (e.g., `services/social.py`, sharing helpers, lesson-preview routes).
    - Group leftovers 3–6 per commit; add contract fixtures and ignore-list entries for each.
    - **Validates:** Req 4.2–4.5, 6.1, 6.4, 7.4

  - [ ]* 16.3 Property tests for leftover routes
    - **Property 11** for reads; **Property 15** for any writes among leftovers.
    - **Validates:** Req 4.2–4.5, 6.4

  - [ ] 16.4 Phase 15 complete: tick ledger
    - Flip leftovers to `native`; tick boxes + phase header.
    - Re-run the full contract suite. Confirm `route-coverage` summary shows `native + gateway-pinned == total`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.3, 1.4, 7.3, 7.4

### Phase 16 — Cutover

- [ ] 17. Cutover
  - [ ] 17.1 Verify cutover readiness
    - Run the full contract suite green against production-like data.
    - Verify `GET /api/v1/internal/route-coverage` reports `summary.ready_for_cutover = true`: every inventory route is `native` or documented gateway-pinned, no incident `override = "gateway"` remains.
    - **Validates:** Req 10.1, 10.3; Property 3, Property 11

  - [ ]* 17.2 Property tests for inventory coverage and contract equivalence at cutover
    - **Property 3: Inventory coverage** — startup-time invariant holds across the entire inventory.
    - **Property 11: Contract equivalence for native routes** — re-run for the full corpus.
    - **Validates:** Req 2.5, 4.2–4.5, 10.1, 10.3

  - [ ] 17.3 Switch nginx upstream from `api` to `api_rust`
    - Update nginx config to point upstream at `api_rust:8001`.
    - Reload nginx with `nginx -s reload` (zero-downtime).
    - **Validates:** Req 10.2, 10.3

  - [ ] 17.4 Remove Python `api` service from `docker-compose.yml`
    - Delete the `api` service block; keep `ai_teacher_agent`.
    - Flip every entry in `route-modes.toml` to `native` (no `gateway` overrides allowed post-cutover); the dispatcher refuses to start with a `gateway` value when no `api` upstream exists.
    - **Validates:** Req 10.4, 13.3; Property 17

  - [ ]* 17.5 Property test for post-cutover dispatcher invariant
    - **Property 3 (post-cutover clause)** — every inventory route is served natively without contacting `Python_Service`.
    - **Validates:** Req 10.3, 13.3

  - [ ] 17.6 Final ledger update; spec marked complete
    - Tick the Phase 16 header in `docs/plan/full-rust-backend-migration-ledger.md` with cutover SHA + date.
    - Update the `Summary` section: `Native: N/N`, `Phases complete: 16/16`.
    - Ensure all tests pass; ask the user if questions arise.
    - **Validates:** Req 1.1, 1.4, 1.5, 7.3, 10.1

## Notes

- Tasks marked with `*` are optional (test sub-tasks). They can be skipped for a faster MVP, but Property 11 (contract equivalence) and Property 15 (DB write parity) should be run at minimum before any phase ledger tick.
- Each task references specific requirements and the design's correctness properties for traceability.
- Checkpoints are the per-phase "Phase complete" sub-tasks, which always re-run the contract suite and update `docs/plan/full-rust-backend-migration-ledger.md`.
- Routes per phase are grouped 3–6 per sub-task to keep PRs reviewable.
- All AI tutor / live routes (Phase 14) are intentionally pinned `gateway`; they are not migrated natively and are documented in `backend-rust/docs/ai-tutor-routing.md`.
- **Total phases:** 16 (Phase 0 through Phase 16, with Phase 0 = foundations and Phase 16 = cutover).
- **Total leaf sub-tasks:** 91 (across 17 top-level epics).
- **Ledger file:** `docs/plan/full-rust-backend-migration-ledger.md` is updated in every "Phase complete" sub-task and is the single source of truth for migration progress.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.5", "1.7", "1.9", "1.12"] },
    { "id": 2, "tasks": ["1.4", "1.6", "1.8", "1.10", "1.13", "1.14", "1.17", "1.19", "1.20"] },
    { "id": 3, "tasks": ["1.11", "1.15", "1.16", "1.18", "1.21"] },
    { "id": 4, "tasks": ["1.22"] },
    { "id": 5, "tasks": ["2.1"] },
    { "id": 6, "tasks": ["2.2", "2.3"] },
    { "id": 7, "tasks": ["3.1"] },
    { "id": 8, "tasks": ["3.2", "3.3", "3.4"] },
    { "id": 9, "tasks": ["3.5", "3.6", "3.7"] },
    { "id": 10, "tasks": ["3.8"] },
    { "id": 11, "tasks": ["4.1"] },
    { "id": 12, "tasks": ["4.2", "4.3", "4.5"] },
    { "id": 13, "tasks": ["4.4", "4.6"] },
    { "id": 14, "tasks": ["4.7"] },
    { "id": 15, "tasks": ["5.1"] },
    { "id": 16, "tasks": ["5.2", "5.3", "5.4", "5.5"] },
    { "id": 17, "tasks": ["5.6"] },
    { "id": 18, "tasks": ["5.7"] },
    { "id": 19, "tasks": ["6.1"] },
    { "id": 20, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 21, "tasks": ["6.5"] },
    { "id": 22, "tasks": ["6.6"] },
    { "id": 23, "tasks": ["7.1"] },
    { "id": 24, "tasks": ["7.2", "7.3"] },
    { "id": 25, "tasks": ["7.4"] },
    { "id": 26, "tasks": ["7.5"] },
    { "id": 27, "tasks": ["8.1", "8.2", "8.3"] },
    { "id": 28, "tasks": ["8.4"] },
    { "id": 29, "tasks": ["8.5"] },
    { "id": 30, "tasks": ["9.1"] },
    { "id": 31, "tasks": ["9.2", "9.3", "9.4"] },
    { "id": 32, "tasks": ["9.5"] },
    { "id": 33, "tasks": ["9.6"] },
    { "id": 34, "tasks": ["10.1", "10.2"] },
    { "id": 35, "tasks": ["10.3"] },
    { "id": 36, "tasks": ["10.4"] },
    { "id": 37, "tasks": ["11.1", "11.2", "11.3"] },
    { "id": 38, "tasks": ["11.4"] },
    { "id": 39, "tasks": ["11.5"] },
    { "id": 40, "tasks": ["12.1", "12.2"] },
    { "id": 41, "tasks": ["12.3"] },
    { "id": 42, "tasks": ["12.4"] },
    { "id": 43, "tasks": ["13.1"] },
    { "id": 44, "tasks": ["13.2"] },
    { "id": 45, "tasks": ["13.3"] },
    { "id": 46, "tasks": ["14.1"] },
    { "id": 47, "tasks": ["14.2", "14.3", "14.4", "14.5", "14.6", "14.7", "14.8"] },
    { "id": 48, "tasks": ["14.9"] },
    { "id": 49, "tasks": ["14.10"] },
    { "id": 50, "tasks": ["15.1", "15.2"] },
    { "id": 51, "tasks": ["15.3", "15.4"] },
    { "id": 52, "tasks": ["15.5"] },
    { "id": 53, "tasks": ["16.1"] },
    { "id": 54, "tasks": ["16.2"] },
    { "id": 55, "tasks": ["16.3"] },
    { "id": 56, "tasks": ["16.4"] },
    { "id": 57, "tasks": ["17.1", "17.2"] },
    { "id": 58, "tasks": ["17.3"] },
    { "id": 59, "tasks": ["17.4", "17.5"] },
    { "id": 60, "tasks": ["17.6"] }
  ]
}
```
