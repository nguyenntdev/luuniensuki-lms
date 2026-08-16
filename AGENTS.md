<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **luuniensuki-lms** (23912 symbols, 33359 relationships, 299 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/luuniensuki-lms/context` | Codebase overview, check index freshness |
| `gitnexus://repo/luuniensuki-lms/clusters` | All functional areas |
| `gitnexus://repo/luuniensuki-lms/processes` | All execution flows |
| `gitnexus://repo/luuniensuki-lms/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

# AGENTS.md

Gamified LMS for Vietnamese heritage (Cửu Đỉnh). Polyglot monorepo mid-migration from Python to Rust.

## Critical: where the real code lives

- The real Python backend is the **`backend/` package**, run as `uvicorn backend.main:app`. `backend/main.py` is a thin shim → app factory in `backend/app.py`, routes in `backend/routers/*`, business logic in `backend/services/*`, shared helpers in `backend/domain/*`.
- **Root-level `main.py` (~18k lines), `models.py`, `schemas.py`, `seed.py`, `config.py`, etc. and root `versions/` are stale pre-modularization copies of the old monolith.** Nothing imports them and Docker does not copy them. Never edit them — edit the counterpart in `backend/`.
- Alembic migrations live in `migrations/` (`alembic.ini` sets `script_location = migrations`); root `versions/` is a stale duplicate.

## Architecture

Request flow: Browser → Nginx → Next.js (`frontend/`, :3000) → Rust API gateway (`backend-rust/`, :8001) → either native Rust route or fallback proxy to FastAPI (`backend/`, :8000) → PostgreSQL 15.

- Strangler-fig migration: Rust gateway owns `GET /health`, `GET /api/v1/ranks`, `GET /api/v1/content/ratings`, `GET /api/v1/tags`, and proxies everything else to Python.
- `services/ai_teacher_agent/realtime_worker.py` — background worker for AI teacher live sessions (runs as separate compose service).
- Live learning uses LiveKit (compose service `livekit`) with a Janus gateway alternative.
- `mobile/` — Flutter client. `ban-duc-noi/` — motif image assets served by Nginx at `/assets/ban-duc-noi`.
- Production: `https://lms.histolab.icu`, stack in `docker-compose.prod.yml`.

## Commands

### Python backend

```bash
# Tests require a running PostgreSQL. Test DB defaults to luuniensuki_test
# (conftest.py setdefault; CI uses luuniensuki). The DB must exist; conftest
# drop_all/create_all's it per session.
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest

# Single test
pytest tests/backend/test_auth.py::test_register -v

# Migrations / seed
alembic upgrade head
python -m backend.seed --seed-path data --image-path ban-duc-noi

# In docker
docker compose exec api pytest
```

- `tests/backend/test_openapi_snapshot.py` pins the HTTP contract byte-for-byte. For intentional contract changes only: `REGENERATE_OPENAPI_SNAPSHOT=1 pytest tests/backend/test_openapi_snapshot.py`, then commit the fixture. Never regenerate as a side effect of refactoring.
- `tests/backend/test_cross_backend_contract.py` verifies Python/Rust parity — relevant whenever migrating a route.

### Frontend (`cd frontend`)

```bash
npm run dev          # Next.js on :3000
npm run lint:ci      # strict lint (ESLINT_USE_FLAT_CONFIG=true, --max-warnings=0)
npm run type-check   # tsc --noEmit (also runs via prebuild)
npm run test         # vitest run
npx playwright test  # E2E; starts its own dev server (webServer in playwright.config.ts)
PLAYWRIGHT_GREP=@smoke npx playwright test   # smoke subset (what CI runs)
npm run gen:api      # regenerate src/types/api.ts from backend OpenAPI schema (openapi-typescript)
```

- Frontend is mixed JS/TSX; don't assume TS everywhere.

### Rust (`cd backend-rust`)

```bash
cargo fmt --check
cargo test
cargo run
```

- All Cargo dependencies are exact-pinned (`=`) for the strangler-fig migration. When adding/bumping a dep, record peak release-build RSS in `backend-rust/docs/build-budget.md` — a CI lint enforces parity between the manifest and that doc.

### Local stack

```bash
cp .env.example .env
docker compose up -d db api api_rust web
curl -s http://127.0.0.1:8001/health
```

## Conventions & gotchas

- Error envelope everywhere: `{"error": {"code": ..., "message": ..., "details": {}}}`.
- Auth: JWT in httpOnly cookies (`luuniensuki_access`/`luuniensuki_refresh`); OAuth2 header kept for tests. Guest role can only access `is_demo: true` content.
- Rust migration rules: one stable endpoint group per small PR, keep response shapes frontend-compatible, keep the Python fallback until contract tests + production smoke test pass, run `cargo test` before deploy.
- XP: discovery 25 / lesson 50 / mastered 75; quiz pass ≥ 80%. Progress flow: `hidden → discovered → learned → mastered`.
- Config fails closed at import time (rejects sentinel JWT secrets, wildcard CORS + credentials) — see `backend/config.py` validator before adding settings.
- Deploy scripts in `scripts/deployment/` (`deploy-safe.sh` is the safe path). Smoke test after deploy: pages return 200, `/api/v1/ranks` returns 401 unauthenticated.
- Never commit secrets. The production server at `/opt/luuniensuki-lms` may not be a git checkout — use a GitHub clone for commits/PRs.
- Flutter codegen (freezed/riverpod): `scripts/build/generate_hearts_code.sh`.

## Key docs

- `docs/DOCUMENTATION_INDEX.md` — map of all docs
- `docs/ARCHITECTURE.md` — current architecture + Rust migration
- `docs/plan/2026-05-12-rust-backend-refactor-plan.md` — phased migration plan
- `CLAUDE.md` — older but detailed domain notes (XP/badges/streaks/quiz logic); trust code over it where they diverge
