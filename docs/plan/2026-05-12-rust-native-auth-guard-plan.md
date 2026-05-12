# Plan: Rust Native Auth Guard

Date: 2026-05-12

## Goal

Move the first real backend behavior into Rust without changing user-visible API contracts.

## Scope

Rust gateway will natively handle unauthenticated requests for selected authenticated read endpoints:

- `/api/v1/ranks`
- `/api/v1/badges`
- `/api/v1/urns`
- `/api/v1/dashboard/summary`
- `/api/v1/users/me/collection`
- `/api/v1/users/me/badges`
- `/api/v1/users/me/streak`
- `/api/v1/auth/me`

Behavior:

- If request has no Bearer token and no `luuniensuki_access` cookie, Rust returns the same 401 JSON shape as Python.
- If request has any auth token, Rust proxies to Python. Python remains the source of truth for JWT validation and DB-backed response.

## Why This Step

Full JWT + DB validation in Rust needs more dependencies and schema mapping. The current host is memory constrained, and the low-risk path is to migrate one behavior at a time.

This step moves auth boundary behavior into Rust while preserving correctness:

- unauthenticated traffic handled directly by Rust
- authenticated/ambiguous traffic still validated by Python
- no DB schema changes
- no frontend changes

## Files To Edit

- `backend-rust/src/main.rs`
- `backend-rust/README.md`
- `docs/plan/2026-05-12-rust-native-auth-guard-plan.md`

## Verification

- Rust tests:
  - auth header detected
  - auth cookie detected
  - selected routes return native 401 when unauthenticated
  - unrelated routes still proxy
- Docker build `api_rust`
- Deploy `api_rust`
- Smoke:
  - `/health` returns Rust gateway
  - `/api/v1/badges` returns 401 with Python-compatible JSON
  - `/api/v1/urns` returns 401 with Python-compatible JSON
  - web routes stay 200

## Next Step

After this, port JWT verification and `/api/v1/auth/me` fully into Rust, then DB-backed reads.
