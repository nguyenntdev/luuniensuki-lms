# Luu Nien Su Ki Rust API

This service is the incremental Rust replacement for the legacy FastAPI backend.

Current scope:

- Runs beside the Python API as the front-line API gateway (Nginx → api_rust → native or Python fallback).
- Exposes `GET /health`.
- Serves the full route surface natively (see `src/routes/*` and `docs/route-inventory.json`, 291 routes across auth, users, content, lessons, quizzes, progress, quests, classrooms, leaderboards, admin, timeline, trails, fsrs/reviews, streak economy, live).
- Route dispatch is config-driven and hot-reloadable: `config/route-modes.toml` defaults unknown routes to `native`; only routes pinned to `gateway` (live AI teacher, AI tutor, live demo-enter) are proxied to Python via `gateway::fallback_to_python`.
- Handles unauthenticated 401 responses natively.
- Exposes `GET /api/v1/internal/db-health` to verify Rust can authenticate with PostgreSQL and run `SELECT 1`.
- Runs background jobs: streak rollover, friend streaks, trail reminders, trail certificate retry.
- All Cargo deps exact-pinned; release profile tuned for low-memory build host (`codegen-units=1`, `lto="thin"`).

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
