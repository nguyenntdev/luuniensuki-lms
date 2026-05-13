# Plan: Rust-native badges endpoint

## Goal

Move `GET /api/v1/badges` from legacy Python handling to the Rust gateway while keeping the public API shape unchanged.

## Current behavior

- Route: `GET /api/v1/badges`
- Auth: requires current user via bearer token or `luuniensuki_access` cookie.
- Data: active, non-secret badges only.
- Response item fields:
  - `id`
  - `slug`
  - `name`
  - `name_en`
  - `description`
  - `icon_url`
  - `category`
  - `xp_bonus`

## GitNexus impact

- `handle_connection`: LOW, direct caller `main`.
- `verify_access_token`: LOW, used by `handle_connection`.
- `tags_json`: LOW, pattern reused for DB JSON route.
- `simple_query`: HIGH, shared by DB health and tags. Do not modify its body in this phase.

## Implementation

1. Add native route handling for `GET /api/v1/badges`.
2. Reuse existing Rust JWT verification and unauthenticated 401 response.
3. Add `pg::badges_json(database_url)` using the existing PostgreSQL simple query client.
4. Preserve Python response shape and null handling.
5. Fall back to legacy Python if the native DB query fails after auth succeeds.

## Tests

1. Add Rust unit coverage for badge JSON shape and escaping.
2. Extend contract script:
   - unauthenticated `/api/v1/badges` returns 401.
   - authenticated `/api/v1/badges` returns 200 and a JSON array.
3. Run local Rust tests.
4. Deploy `api_rust` and run public + authenticated contract tests against production.

## Rollout

1. Commit plan separately.
2. Commit Rust implementation and tests separately.
3. Build and deploy `api_rust`.
4. Run GitNexus `detect_changes()` before commit/PR.
5. Push branch, open PR, merge after tests pass.
