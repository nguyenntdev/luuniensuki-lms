# Plan: Native Rust Ranks Endpoint

Date: 2026-05-12

## Goal

Move the first authenticated endpoint response fully into Rust.

## Endpoint

- `GET /api/v1/ranks`

## Behavior To Preserve

- Missing token: 401 with existing error JSON.
- Invalid token: 401.
- Valid access token: return the same static XP rank list as Python.

## Rust Work

- Add small crypto/JSON dependencies:
  - `base64`
  - `hmac`
  - `sha2`
  - `serde_json`
- Verify JWT HS256 signature with `JWT_SECRET_KEY`.
- Enforce:
  - `type == "access"`
  - `exp >= now`
- Return static ranks from Rust.
- Keep all other authenticated routes proxied to Python.

## Risk

Low. Rank data is static and does not require DB. This endpoint is safe as the first native authenticated response.

## Verification

- Unit tests:
  - missing token gets unauth guard
  - invalid JWT rejected
  - generated valid JWT accepted
  - `/api/v1/ranks` response shape
- Docker build `api_rust`.
- Deploy `api_rust`.
- Smoke:
  - unauth `/api/v1/ranks` returns 401
  - web routes stay 200
  - `/health` returns Rust gateway

## Next Step

After this, add DB access and move `/api/v1/auth/me` or `/api/v1/badges`.
