# Rust gateway stability plan

## Goal

Keep the Rust gateway deployed as the API entrypoint while making it stable on the production Docker network and cheap to build on the server.

## Changes

1. Resolve the legacy Python API by Docker hostname on every proxied request instead of caching one container IP at startup.
2. Keep the native `/api/v1/ranks` auth guard in Rust.
3. Remove third-party Rust crypto dependencies from the sidecar so the server build does not need to download or compile the dependency tree.
4. Rebuild and redeploy `api_rust`.
5. Smoke test public pages, unauthenticated API guard, authenticated login, `/auth/me`, and `/ranks`.

## Validation

- `cargo fmt --check`
- `cargo test`
- `docker compose -f docker-compose.prod.yml build api_rust`
- `docker compose -f docker-compose.prod.yml up -d api_rust`
- HTTPS smoke tests on `lms.histolab.icu`
