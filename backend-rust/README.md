# Luu Nien Su Ki Rust API

This service is the incremental Rust replacement for the legacy FastAPI backend.

Current scope:

- Runs beside the Python API.
- Exposes `GET /health`.
- Works as a gateway in front of the Python API.
- Proxies non-native backend routes to the legacy Python API.
- Handles selected unauthenticated 401 responses natively.
- Uses a minimal standard-library HTTP server so it can build on the current low-memory host.

Local commands:

```bash
cargo test
cargo run
```

Docker Compose:

```bash
docker compose build api_rust
docker compose up -d api_rust
curl http://127.0.0.1:8001/health
```

Migration rule:

- Move one stable endpoint group at a time.
- Keep response shapes compatible with the current frontend.
- Keep the Python API as fallback until contract tests pass.
- Introduce Axum/SQLx when endpoint migration begins and CI/build memory is ready.
