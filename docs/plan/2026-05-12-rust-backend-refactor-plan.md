# Plan: Refactor Codebase And Migrate Backend To Rust

Date: 2026-05-12

Backup created before changes:

- `backups/code-backup-before-rust-refactor-20260512-085756.tar.gz`

## Goals

- Make the codebase smaller, easier to navigate, and safer to evolve.
- Move the backend from a large FastAPI monolith toward a Rust backend without breaking production.
- Keep the current web experience online during migration.
- Preserve the existing database, public API contracts, auth behavior, and Docker deployment flow.

## Current State

- Frontend: Next.js app under `frontend/`.
- Backend: FastAPI app under `backend/`, with a very large `backend/main.py`.
- Database: PostgreSQL via SQLAlchemy models in `backend/models.py`.
- Background worker: Python Live AI teacher worker under `services/ai_teacher_agent/`.
- Deployment: Docker Compose with `api`, `web`, `db`, `ai_teacher_agent`, `livekit`, and optional `nginx`.

## Main Problems

- Backend route logic, DTOs, DB queries, and business rules are concentrated in `backend/main.py`.
- Service boundaries exist under `backend/services/`, but the route layer still imports too much.
- Full Rust replacement in one cut would be high risk because the frontend depends on many existing API shapes.
- The AI/live worker uses Python-specific libraries and should not be migrated in the first Rust pass.
- The repo contains generated/runtime artifacts and multiple root-level legacy files that make navigation noisy.

## Migration Strategy

Use an incremental strangler migration:

1. Keep the current Python API as the production fallback.
2. Add a Rust API service beside it.
3. Move stable, low-risk endpoints first.
4. Route selected endpoints to Rust only after contract tests pass.
5. Keep Python-only AI/live features until the core LMS API is stable in Rust.

## Target Architecture

```text
frontend/
  Next.js app

backend/
  Python FastAPI legacy API
  AI/live worker dependencies

backend-rust/
  Axum API
  SQLx/PostgreSQL data access
  JWT auth middleware
  versioned route modules
  contract tests against existing API shapes

docker-compose.yml
  db
  api              -> Python legacy API
  api_rust         -> Rust migration API
  web
  ai_teacher_agent -> Python worker
```

## Rust Backend Stack

- Initial skeleton: standard-library HTTP health server to fit the current low-memory host.
- Target runtime: `tokio`
- Target HTTP: `axum`
- Target DB: `sqlx` with PostgreSQL
- Serialization: `serde`
- Validation: `validator`
- Auth: `jsonwebtoken`, `argon2` or `bcrypt` compatibility where needed
- Config: environment variables via `config`/`dotenvy`
- Errors: typed app errors mapped to stable JSON responses
- Observability: `tracing`, `tracing-subscriber`

## API Migration Order

### Phase 1: Rust Skeleton

- Create `backend-rust/`.
- Add health endpoint: `GET /health`.
- Add Dockerfile.
- Add `api_rust` service to Compose on internal port `8001`.
- Do not change production traffic yet.

### Phase 2: Shared Contracts

- Document current frontend API calls.
- Add contract smoke tests for the most used endpoints.
- Freeze response shapes before moving routes.
- Add Rust error envelope compatible with current frontend expectations.

### Phase 3: Low-Risk Read Endpoints

Move endpoints with simple DB reads first:

- public app metadata
- urn list/detail reads
- motif list/detail reads
- leaderboard reads if query shape is stable
- badges/achievements reads

### Phase 4: Auth And User Reads

- Port JWT verification.
- Port `/me`-style current user reads.
- Keep login/register on Python until password compatibility is verified.

### Phase 5: Learning Write Flows

Move write endpoints only after read contracts are stable:

- progress updates
- quiz attempts
- spaced repetition review actions
- XP/streak updates

### Phase 6: Admin And RAG

- Keep admin, uploads, RAG, AI tutor, and live class features in Python until core LMS traffic is stable.
- Migrate only after file upload, permissions, and provider integrations have dedicated tests.

## Immediate Refactor Scope

This first implementation pass should stay deployable:

- Add Rust service skeleton without replacing Python.
- Add clean docs and scripts for local Rust API work.
- Reduce repo noise with documented boundaries instead of moving high-risk files.
- Keep frontend and current Python API untouched unless needed for service discovery.

## Files To Add

- `backend-rust/Cargo.toml`
- `backend-rust/Dockerfile`
- `backend-rust/src/main.rs`
- `backend-rust/src/config.rs`
- `backend-rust/src/error.rs`
- `backend-rust/src/http/mod.rs`
- `backend-rust/src/http/health.rs`
- `backend-rust/README.md`
- `docs/plan/2026-05-12-rust-backend-refactor-plan.md`

## Files To Edit

- `docker-compose.yml`
- optional: root docs/readme files if they exist and need pointers

## Safety Rules

- Do not delete the Python backend in this pass.
- Do not point the frontend to Rust until route parity exists.
- Do not alter database schema in this pass.
- Do not change auth/session cookies in this pass.
- Keep Docker Compose rollback simple: stop `api_rust` and keep `api`.

## Verification

- Build Rust API container.
- Run Rust unit tests.
- Start `api_rust`.
- Check:
  - `GET http://127.0.0.1:8001/health`
  - existing Python API remains available on `127.0.0.1:8000`
  - frontend remains available on production route checks

## Deployment Plan

1. Build `api_rust`.
2. Start `api_rust` alongside existing services.
3. Verify Rust health endpoint.
4. Verify current production web and Python API are still healthy.
5. Do not route public traffic to Rust yet.

## Rollback

- Remove or stop `api_rust`:

```bash
docker compose stop api_rust
```

- Current `api` service remains the source of truth.

## Non-Goals For This Pass

- Full backend rewrite in one deployment.
- Replacing AI/live teacher worker.
- Rewriting database models.
- Rewriting frontend API client.
- Deleting Python backend files.
