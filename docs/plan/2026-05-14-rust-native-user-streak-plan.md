# Plan: Rust-native user streak endpoint

## Goal

Move `GET /api/v1/users/me/streak` from the legacy Python handler to the Rust gateway.

## Current behavior

- Route: `GET /api/v1/users/me/streak`
- Auth: requires bearer token or `luuniensuki_access` cookie.
- Source: current user row.
- Response:
  - `current_streak`
  - `longest_streak`
  - `streak_freezes`
  - `last_active_at`
  - `days_since_last_active`

## GitNexus impact

- `handle_connection`: LOW, direct caller `main`.
- `verify_access_token`: LOW, direct caller `handle_connection`.
- `badges_json`: LOW, existing DB JSON route pattern.
- `simple_query`: CRITICAL because it is shared by DB health, tags, and badges. This phase must not modify its body.

## Implementation

1. Add native route branch for `GET /api/v1/users/me/streak`.
2. Reuse existing Rust JWT verification.
3. Extract `sub` from verified token claims as `user_id`.
4. Add `pg::user_streak_json(database_url, user_id)`:
   - read streak columns from `users`
   - return Python-compatible JSON
   - compute `days_since_last_active` in PostgreSQL from UTC dates
5. Fall back to legacy Python only if DB query fails after auth succeeds.

## Tests

1. Unit-test JSON shape for streak rows with and without `last_active_at`.
2. Extend production contract script:
   - unauthenticated `/api/v1/users/me/streak` returns 401
   - authenticated `/api/v1/users/me/streak` returns 200 and streak keys
3. Run Rust tests in the Rust Docker image.
4. Deploy `api_rust`.
5. Run production contracts with auth.

## Rollout

1. Commit plan.
2. Commit implementation and tests.
3. Push branch and open PR.
4. Merge after production contracts pass.
5. Reindex GitNexus and commit stats if changed.
