# Plan: Rust Gateway Migration

Date: 2026-05-12

## Goal

Move all LMS backend traffic through Rust first, then replace Python endpoint groups behind that Rust boundary.

## Why Gateway First

The Python backend has hundreds of routes and many coupled concerns: auth, learning progress, AI, live sessions, admin, RAG, social, email, and mobile compatibility. Rewriting all endpoints directly in one cut would risk breaking response shapes and user sessions.

Gateway-first migration gives a safer path:

- Nginx sends backend traffic to `api_rust`.
- Rust serves native routes when available.
- Rust proxies unknown routes to legacy Python `api`.
- Python remains rollback/fallback.
- Future endpoint groups can be ported behind the same Rust public boundary.

## Scope For This Pass

- Expand `backend-rust` from health-only sidecar into a minimal Rust gateway.
- Add native `GET /health`.
- Proxy all other backend routes to Python:
  - `/api/...`
  - `/motifs/...`
  - `/progress/...`
- Preserve request method, path, query string, selected headers, body, status, response headers, and response body.
- Add gateway config:
  - `LEGACY_API_HOST`
  - `LEGACY_API_PORT`
- Point Nginx LMS backend upstream to `api_rust:8001`.
- Keep Python `api` running for fallback.
- Deploy and smoke test production routes.

## Files To Edit

- `backend-rust/src/config.rs`
- `backend-rust/src/main.rs`
- `backend-rust/README.md`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `nginx-lms.conf`
- `docs/plan/2026-05-12-rust-gateway-migration-plan.md`

## Non-Goals

- No DB schema changes.
- No auth rewrite yet.
- No AI/live worker rewrite yet.
- No deletion of Python backend.
- No direct SQL from Rust in this pass.

## Endpoint Migration After Gateway

1. Native static/read-only routes:
   - `/health`
   - `/api/v1/ranks`
   - `/api/v1/badges`
   - `/api/v1/tags`
2. Public content reads:
   - `/api/v1/urns`
   - `/api/v1/urns/{urn_slug}`
   - `/api/v1/motifs/{motif_id}`
3. Authenticated user reads:
   - `/api/v1/auth/me`
   - `/api/v1/users/me/collection`
   - `/api/v1/dashboard/summary`
4. Learning writes:
   - quiz submit
   - progress unlock
   - review cards
5. Keep complex integrations last:
   - AI tutor/streaming
   - LiveKit/live sessions
   - RAG/admin upload
   - email/push jobs

## Verification

- `cargo fmt`
- `cargo test`
- `docker compose build api_rust`
- `docker compose up -d api_rust nginx`
- `curl http://127.0.0.1:8001/health`
- `curl https://lms.histolab.icu/health`
- route smoke:
  - `/`
  - `/dashboard`
  - `/practice`
  - `/profile`
  - `/ai`
  - `/api/v1/urns`
  - `/api/v1/badges`

## Rollback

- Change Nginx `$api_upstream` back to `http://api:8000`.
- Reload/restart Nginx.
- Stop `api_rust` if needed.

