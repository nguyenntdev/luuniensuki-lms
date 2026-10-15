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

Gamified LMS for Vietnamese heritage (Cửu Đỉnh). Polyglot monorepo with Axum/Rust API gateway + FastAPI/Python backend + Next.js frontend + Flutter mobile.

## Critical: Where the Real Code Lives

- **Active Python Backend**: The real Python backend is the modular **`backend/`** package (factory in `backend/app.py`, thin entrypoint shim in `backend/main.py`, routers in `backend/routers/*`, schemas in `backend/apischemas/*`, business logic in `backend/services/*`, domain helpers in `backend/domain/*`).
- **DO NOT TOUCH STALE MONOLITH FILES**: Root-level `main.py` (~18.3k lines), `models.py`, `schemas.py`, `seed.py`, `config.py`, `rbac.py`, `security.py`, `errors.py`, and root `versions/` are obsolete pre-modularization artifacts. Nothing in runtime or Docker imports them. Always edit files inside `backend/`.
- **Database Migrations**: Real Alembic migrations live in **`migrations/`** (`alembic.ini` sets `script_location = migrations`). Root `versions/` is an obsolete duplicate.

## Architecture & Request Routing

Request flow: `Browser -> Nginx (:80/:443) -> Next.js (frontend/, :3000) -> Rust Gateway (backend-rust/, :8001) -> PostgreSQL 15`.

- **Rust Gateway & Native Endpoints**: `backend-rust/` serves 291 routes natively (auth, users, content, lessons, quizzes, progress, quests, classrooms, leaderboards, admin, timeline, trails, FSRS reviews, streak economy).
- **Python Proxy Fallback**: Managed via `backend-rust/config/route-modes.toml` (hot-reloaded). Routes pinned to `"gateway"` (`/api/v1/live/*`, `/api/v1/ai-tutor/*`, `/api/v1/live/demo-enter`) are proxied to Python (`backend/`, :8000). All other routes serve natively from Rust.
- **AI Background Worker**: `services/ai_teacher_agent/realtime_worker.py` (compose service `ai_teacher_agent`).
- **Real-Time Media**: LiveKit (`livekit`, :7880/:7881) with Janus WebRTC gateway (`janus-gateway`, :8188/:8088/:7088) as alternative.
- **Static Assets**:
  - `ban-duc-noi/` — motif image assets mounted at `/var/www/assets/ban-duc-noi` (served at `/assets/ban-duc-noi`).
  - `public/models/` — 3D GLB models (`CAO-DINH-v1-*.glb`) and urn manifests (`manifests/*.json`).
  - `data/` — JSON seed data for urns, motifs, coordinates, and exams.

## Commands

### Rust Backend (`cd backend-rust`)

```bash
cargo fmt --check
cargo test              # Unit & contract tests
cargo run               # Runs gateway on 0.0.0.0:8001

# CI Lints & Checks (run from repo root)
./scripts/ci/lint-pinned-deps.sh       # Enforces exact (=) Cargo version pins
./scripts/ci/lint-build-budget.sh      # Enforces Cargo.toml <-> build-budget.md parity
./scripts/ci/lint-inventory-drift.sh   # Verifies route-inventory.json is up to date
./scripts/ci/lint-ai-tutor-pinning.sh  # Verifies AI tutor routes stay pinned to gateway
./scripts/ci/lint-migration-safety.sh  # Blocks destructive SQL operations
./scripts/ci/lint-ledger-sync.sh       # Verifies route-modes.toml matches migration ledger
```

### Python Backend

```bash
# Tests require a running PostgreSQL instance. Test DB defaults to luuniensuki_test.
# conftest.py drops and recreates tables per session.
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest

# Run single test file or specific test case
pytest tests/backend/test_auth.py::test_register -v

# Run live audio / STT / TTS unit tests
pytest backend/tests/test_live_audio_bridge.py -v

# Migrations & database seeding
alembic upgrade head
python -m backend.seed --seed-path data --image-path ban-duc-noi

# In docker container
docker compose exec api pytest
```

### Frontend (`cd frontend`)

```bash
npm run dev          # Next.js development server on :3000
npm run lint:ci      # Strict ESLint check (ESLINT_USE_FLAT_CONFIG=true, --max-warnings=0)
npm run type-check   # tsc --noEmit (enforced as prebuild check)
npm run test         # Vitest unit test suite
npm run test:watch   # Vitest interactive watcher
npx playwright test  # E2E test suite (spawns dev server on :3000 automatically)
PLAYWRIGHT_GREP=@smoke npx playwright test  # Smoke test subset for CI
npm run gen:api      # Regenerate src/types/api.ts from backend OpenAPI schema
```

### Mobile Client (`cd mobile`)

```bash
# Code generation for Freezed / Riverpod models
flutter pub run build_runner build --delete-conflicting-outputs
# Alternatively use helper script from root:
./scripts/build/generate_hearts_code.sh
```

### Local Docker Stack

```bash
cp .env.example .env
docker compose up -d db api api_rust web
curl -s http://127.0.0.1:8001/health  # Verify gateway health (returns status: ok)
```

## Testing Quirks & Contract Enforcement

- **OpenAPI Snapshot Pinning**: `tests/backend/test_openapi_snapshot.py` locks the FastAPI HTTP contract byte-for-byte. For deliberate, reviewed contract changes only:
  ```bash
  REGENERATE_OPENAPI_SNAPSHOT=1 pytest tests/backend/test_openapi_snapshot.py
  ```
  Never regenerate snapshots as an unreviewed side effect of a refactor.
- **Route Inventory**: Update when modifying endpoints: `python scripts/dev/generate_route_inventory.py`.
- **Cross-Backend Parity**: `tests/backend/test_cross_backend_contract.py` validates JWT acceptance and token compatibility across Python and Rust.

## Conventions & Gotchas

- **Error Envelope Standard**: Every API error must strictly follow:
  ```json
  {"error": {"code": "ERROR_CODE", "message": "Human readable message", "details": {}}}
  ```
- **Authentication**: JWT stored in httpOnly cookies (`luuniensuki_access` / `luuniensuki_refresh`); Bearer Authorization header supported for tests. Guest users (`role: "guest"`) can only access content with `is_demo: true`. Shared JWT secret (HS256) and claim set (`sub, iat, exp, role, type, jti, iss, aud`) are shared between Rust and Python.
- **Config Fails Closed**: `backend/config.py` validates settings at startup. In production (`ENVIRONMENT=production`), it fails fatally if `JWT_SECRET_KEY` is a sentinel value or if wildcard CORS origins are paired with credentials.
- **Migration Safety**: Schema changes must be purely additive (`CREATE TABLE`, `CREATE INDEX`, `ADD COLUMN`). Destructive operations (`DROP TABLE`, `DROP COLUMN`, `ALTER TYPE`, `RENAME`) are blocked by `scripts/ci/lint-migration-safety.sh`.
- **Rust Dependency Rule**: Every direct dependency in `backend-rust/Cargo.toml` must use an exact version pin (`=x.y.z`) and have its peak RSS recorded in `backend-rust/docs/build-budget.md`.
- **Gamification Domain Logic**:
  - XP awards: Discovery (25 XP), Lesson (50 XP), Mastered (75 XP). Quiz pass threshold: ≥ 80%.
  - Progression lifecycle: `hidden -> discovered -> learned -> mastered`.
- **Deployment**: Production deployed at `https://lms.histolab.icu` via `docker-compose.prod.yml`. Safe deployment script: `./scripts/deployment/deploy-safe.sh`. Post-deploy smoke test: `./scripts/testing/rust_gateway_contracts.sh`.
