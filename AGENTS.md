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

Gamified LMS for Vietnamese heritage (Cửu Đỉnh). Polyglot monorepo: Axum/Rust API gateway + FastAPI/Python backend + Next.js frontend + Flutter mobile.

## Critical: Where the Real Code Lives

- **Active Python Backend**: The modular **`backend/`** package. Factory in `backend/app.py`, thin entrypoint shim in `backend/main.py`, routers in `backend/routers/`, schemas in `backend/apischemas/`, services in `backend/services/`, domain helpers in `backend/domain/`.
- **DO NOT TOUCH STALE MONOLITH FILES**: Root-level `main.py` (~18.3k lines), `models.py`, `schemas.py`, `seed.py`, `config.py`, `rbac.py`, `security.py`, `errors.py`, and root `versions/` are obsolete pre-modularization artifacts. Nothing in runtime or Docker imports them. Always edit inside `backend/`.
- **Database Migrations**: Real Alembic migrations live in **`migrations/`** (`alembic.ini` sets `script_location = migrations`). Root `versions/` is an obsolete duplicate.
- **Two Dockerfiles**: `backend/Dockerfile` is the real one (non-root user, copies `services/`). Root `Dockerfile` is less hardened — prefer `backend/Dockerfile`.

## Architecture & Request Routing

Request flow: `Browser -> Nginx (:80/:443) -> Next.js (frontend/, :3000) -> Rust Gateway (backend-rust/, :8001) -> PostgreSQL 15`.

- **Rust Gateway**: `backend-rust/` has ~168 native Axum handler bindings across 20 route groups (auth, users, lessons, quizzes, progress, quests, classrooms, leaderboard, admin, timeline, trails, FSRS, streak economy, live, history, etc.). Unmatched routes fall back to the Python gateway.
- **Python Proxy Routes**: Managed via `backend-rust/config/route-modes.toml` (hot-reloaded on SIGHUP / every 30s). Routes pinned to `"gateway"` (`/api/v1/live/*`, `/api/v1/ai-tutor/*`) are proxied to Python (`backend/`, :8000). Default for unknown routes is `"native"`.
- **AI Background Worker**: `services/ai_teacher_agent/realtime_worker.py` (compose service `ai_teacher_agent`).
- **Real-Time Media**: LiveKit (`livekit`, :7880/:7881) with Janus WebRTC gateway (`janus-gateway`, :8188/:8088/:7088) as alternative.
- **Static Assets**:
  - `ban-duc-noi/` — motif images (served at `/assets/ban-duc-noi`).
  - `public/models/` — 3D GLB models and urn manifests (`manifests/*.json`).
  - `data/` — JSON seed data for urns, motifs, coordinates, and exams.

## Commands

### Rust Backend (`cd backend-rust`)

```bash
cargo fmt --check
cargo test              # Unit & contract tests
cargo run               # Runs gateway on 0.0.0.0:8001
```

**Manual lint scripts** (run from repo root; not wired into GitHub Actions CI):
```bash
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
# conftest.py drops and recreates ALL tables per session (scope="session").
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
npm run dev          # Next.js dev server on :3000
npm run lint:ci      # Strict ESLint (flat config, --max-warnings=0, --exit-on-fatal-error)
npm run type-check   # tsc --noEmit (also runs as prebuild hook)
npm run test         # Vitest unit test suite
npm run test:watch   # Vitest interactive watcher
npx playwright test  # E2E test suite
PLAYWRIGHT_GREP=@smoke npx playwright test  # Smoke subset (used in CI)
npm run gen:api      # Regenerate src/types/api.ts from backend OpenAPI schema
```

### Mobile Client (`cd mobile`)

```bash
# Code generation for Freezed / Riverpod models
flutter pub run build_runner build --delete-conflicting-outputs
# Or from repo root:
./scripts/build/generate_hearts_code.sh
```

### Local Docker Stack

```bash
cp .env.example .env
docker compose up -d db api api_rust web
curl -s http://127.0.0.1:8001/health  # Verify gateway health
```

## CI & What It Actually Runs

GitHub Actions (`.github/workflows/ci.yml`): pushes/PRs to `main`.

| Job | Python / Node | What runs | What does NOT run |
|-----|--------------|-----------|-------------------|
| `backend` | Python 3.11, PG 15 | `pytest` (all tests) | `cargo test`, lint scripts |
| `frontend` | Node 20 | `npm run lint:ci`, `npm run build`, Playwright `@smoke` | `npm run type-check`, `npm run test` (Vitest) |

Deploy workflow (`deploy.yml`) uses Python 3.12 and runs `pytest tests/backend` before deploying.

**Note**: The Rust gateway has no automated CI job. The 6 `scripts/ci/lint-*.sh` scripts exist but are manual-only. Run them locally before committing Rust changes.

## Testing Quirks & Contract Enforcement

- **OpenAPI Snapshot Pinning**: `tests/backend/test_openapi_snapshot.py` locks the FastAPI contract byte-for-byte. To deliberately update:
  ```bash
  REGENERATE_OPENAPI_SNAPSHOT=1 pytest tests/backend/test_openapi_snapshot.py
  ```
  Never regenerate as an unreviewed side effect.
- **Route Inventory**: Update when modifying endpoints: `python scripts/dev/generate_route_inventory.py`.
- **Cross-Backend Parity**: `tests/backend/test_cross_backend_contract.py` validates JWT acceptance across Python and Rust.
- **CI vs Local DB name**: CI creates DB `luuniensuki`; local conftest defaults to `luuniensuki_test`. The `DATABASE_URL` env var controls which is used — conftest picks it up via `os.environ.setdefault`.
- **Test directories**: Integration tests in `tests/backend/`, unit tests in `tests/unit/` and `backend/tests/`.

## Conventions & Gotchas

- **Error Envelope Standard**: Every API error must follow:
  ```json
  {"error": {"code": "ERROR_CODE", "message": "Human readable message", "details": {}}}
  ```
- **Authentication**: JWT in httpOnly cookies (`luuniensuki_access` / `luuniensuki_refresh`); Bearer header for tests. Guest users (`role: "guest"`) can only access `is_demo: true` content. Shared JWT secret (HS256) and claim set (`sub, iat, exp, role, type, jti, iss, aud`) between Rust and Python.
- **Config Fails Closed**: `backend/config.py` validates at startup. In production (`ENVIRONMENT=production`), fails fatally if: (1) `JWT_SECRET_KEY` is a sentinel, (2) wildcard CORS + credentials, or (3) `PASSWORD_RESET_RETURN_TOKEN=true`.
- **Migration Safety**: Schema changes must be purely additive (`CREATE TABLE`, `CREATE INDEX`, `ADD COLUMN`). Destructive ops blocked by `scripts/ci/lint-migration-safety.sh`.
- **Rust Dependency Rule**: Every direct dep in `backend-rust/Cargo.toml` must use exact pin (`=x.y.z`) with peak RSS recorded in `backend-rust/docs/build-budget.md`. Build is memory-constrained (~3.9 GiB RAM).
- **Gamification Domain Logic**:
  - XP: Discovery (25), Lesson (50), Mastered (75). Quiz pass: >= 80%.
  - Progression: `hidden -> discovered -> learned -> mastered`.
- **Deployment**: Production at `https://lms.histolab.icu` via `docker-compose.prod.yml`. Deploy: `./scripts/deployment/deploy-safe.sh`. Post-deploy smoke: `./scripts/testing/rust_gateway_contracts.sh`.

## Production Delivery Waves Execution Log

### Wave W00: Baseline / Truth & Contract Inventory (COMPLETED)
- **Status**: 10/10 slots complete. 78/78 tests passing.
- **Artifacts**: `artifacts/implementation/W00/` (`W00_A01`–`W00_A10`).
- **Scope**: Route inventory freeze across FastAPI & Rust Gateway, dev env reproducibility, mock call-site registry, migration graph unification (`0057_merge_all_heads.py`), API contract snapshot, identity/consent baseline, demo tenant isolation, 162 relic inventory, media rights inventory, observability baseline.

### Wave W01: Real Marketplace / Partner Transaction Integrity (COMPLETED)
- **Status**: 10/10 slots complete. 77/77 tests passing.
- **Artifacts**: `artifacts/implementation/W01/` (`W01_A01`–`W01_A10`).
- **Verified Invariants**:
  - `V5-T011` (W01-A01): Removed fabricated inquiry success in `frontend/src/lib/rbpc/inquiries.ts`. Strictly throws typed errors on network/backend 404/5xx failures.
  - `V5-T012` (W01-A02): Token status strict server lookup without matchedSeed fallback. Zero PII returned to public status lookup.
  - `V5-T013` (W01-A03): Partner inbox has zero synthetic seeding in production (`[]` for empty tenants; demo data restricted to preview mode).
  - `V5-T014` (W01-A04): Partner status PATCH persistence with explicit optimistic UI rollback on backend rejection (400/403/500).
  - `V5-T015` (W01-A05): Inquiry idempotency and retry safety with DB-level `uq_rbpc_inquiries_idempotency` race condition handling.
  - `V5-T016` (W01-A06): Inquiry consent lifecycle, retention due date enforcement (90 days), and visitor consent withdrawal endpoint.
  - `V5-T017` (W01-A07): Provider membership scope enforcement. Non-admin queries strictly filtered by `current_user.id`; cross-tenant mutations return 403.
  - `V5-T018` (W01-A08): Canonical inquiry event ledger with append-only cryptographic hash chaining and idempotent replay deduplication.
  - `V5-T019` (W01-A09): Durable notification outbox queue with partner 24h SLA deadline tracking and fault-tolerant inquiry creation.
  - `V5-T020` (W01-A10): Complete end-to-end integration acceptance test suite across visitor submission, partner inbox, state transitions, and tracking.

### Wave W02: Evidence Library / 162 Real Heritage Records (COMPLETED)
- **Status**: 10/10 slots complete. 106/106 tests passing.
- **Artifacts**: `artifacts/implementation/W02/` (`W02_A01`–`W02_A10`).
- **Verified Invariants**:
  - `V5-T021` (W02-A01): Canonical urn/motif mapping verifying 9 Urns and 162 motifs (9x18) with stable IDs, legacy aliases, and cross-urn misassignment rejection.
  - `V5-T022` (W02-A02): Stop auto-verified seed claims. Novel seed claims strictly default to `unreviewed`/`needs_source`; human approvals preserved across re-imports.
  - `V5-T023` (W02-A03): Bibliographic source registry with rights protection, restricted excerpt redaction, and deduplication engine.
  - `V5-T024` (W02-A04): Atomic historical claims linking support/refute sources and granular epistemic status.
  - `V5-T025` (W02-A05): Human editorial workflow enforcing role permissions (`admin`/`staff`/`teacher`), state machines, and immutable audit logs.
  - `V5-T026` (W02-A06): Hán–Nôm review tracking 4 known unconfirmed motifs (`urn_nghi_dinh_03`, `urn_thuan_dinh_13`, `urn_tuyen_dinh_11`, `urn_huyen_dinh_12`) and rejecting unverified AI glyph promotion.
  - `V5-T027` (W02-A07): Image & 3D mesh attribution linkage across 171 relics with 2D rubbing fallback and rights distribution gates.
  - `V5-T028` (W02-A08): Story renderer with bilingual footnote parsing `[^1]`, interactive citation drawer, and epistemic uncertainty indicators.
  - `V5-T029` (W02-A09): Source-guided curriculum mapping enforcing publication gates against unreviewed or disputed claims.
  - `V5-T030` (W02-A10): Reproducible 162 publication audit CLI (`scripts/dev/audit_162_publication.py`) checking 5 mandatory quality gates per relic.

### Wave W03: Real LMS / Rubric / Classroom (COMPLETED)
- **Status**: 10/10 slots complete. 78/78 tests passing.
- **Artifacts**: `artifacts/implementation/W03/` (`W03_A01`–`W03_A10`).
- **Verified Invariants**:
  - `V5-T031` (W03-A01): Retire mock gradebook localStorage in `submissions-api.ts`. Production users receive zero fictional student names or mock grades.
  - `V5-T032` (W03-A02): School, teacher and classroom models with guardian consent flow, join codes, and horizontal classroom isolation.
  - `V5-T033` (W03-A03): Source-locked lesson assignments with immutable pinned assessment basis and publication gates against unverified claims.
  - `V5-T034` (W03-A04): Submission server persistence with M-E-E historical content validation, idempotency key deduplication, and deadline enforcement.
  - `V5-T035` (W03-A05): Teacher rubric grading API (0-3 criteria scale), reviewer attribution, and tamper-resistant student submission contracts.
  - `V5-T036` (W03-A06): Teacher gradebook and authenticated CSV export with strict IDOR protections blocking cross-school data leaks.
  - `V5-T037` (W03-A07): Student learning progression (hidden->discovered->learned->mastered) driven by genuine server actions, with anti-replay and rate limiting.
  - `V5-T038` (W03-A08): Peer/group historical inquiry with collaborative evidence synthesis, teacher moderation, and cross-group privacy isolation.
  - `V5-T039` (W03-A09): Learning outcome measurement scaffold enforcing dual-assessor scoring and blocking causal labels derived from subjective surveys.
  - `V5-T040` (W03-A10): Complete classroom end-to-end acceptance suite across multi-school setups, assignments, submissions, grading, and exports.

### Wave W04: 3D/AR / Map / Visual Asset Integrity (COMPLETED)
- **Status**: 10/10 slots complete. 115/115 tests passing.
- **Artifacts**: `artifacts/implementation/W04/` (`W04_A01`–`W04_A10`).
- **Verified Invariants**:
  - `V5-T041` (W04-A01): 3D asset manifest validation enforcing size, checksum, license, mesh ID joins, WebGL health, and 2D rubbing fallbacks.
  - `V5-T042` (W04-A02): Replace fake map annotation mutations with real server persistence, separate local drafts, and optimistic concurrency.
  - `V5-T043` (W04-A03): Admin map access control enforcing server-side RBAC (`STAFF_ROLES`), editor ownership, and CSRF/Bearer defense.
  - `V5-T044` (W04-A04): Hotspot and claim binding ensuring 3D coordinates link to approved source-based claims and rejecting unreviewed/disputed claims.
  - `V5-T045` (W04-A05): AR fallback and device capability checks with turntable fallback, ensuring denied camera permission still allows equivalent learning completion.
  - `V5-T046` (W04-A06): 3D rendering QA under load with progressive LOD resolution, WebGL context loss recovery, and zero VRAM leaks.
  - `V5-T047` (W04-A07): 360 virtual museum source links connecting viewpoints to verified monuments, with alt text and reduced-motion support.
  - `V5-T048` (W04-A08): Offline licensing and cache headers enforcing immutable cache on hashed assets and blocking stale CDN serving of revoked assets.
  - `V5-T049` (W04-A09): Accessibility audits across media enforcing keyboard navigation, screen reader ARIA roles, captions, and 2D text equivalence.
  - `V5-T050` (W04-A10): Museum operator media CMS with secure file magic byte validation, licensing metadata, and staged publication approval.

### Wave W05: Flutter Mobile / Offline / Coherent Auth (COMPLETED)
- **Status**: 10/10 slots complete. 120/120 tests passing.
- **Artifacts**: `artifacts/implementation/W05/` (`W05_A01`–`W05_A10`).
- **Verified Invariants**:
  - `V5-T051` (W05-A01): Route audit and live screen replacement in `mobile/lib/routing/app_router.dart`. Zero placeholder screens or "Coming Soon" dummy text in production routes.
  - `V5-T052` (W05-A02): Mobile authentication and session lifecycle with Bearer header refresh flow, logging interceptor token masking, and secure storage purge on expiry.
  - `V5-T053` (W05-A03): Mobile catalog & metadata parity across 9 Urns and 162 Motifs with HTTP ETag caching and 304 conditional responses.
  - `V5-T054` (W05-A04): 3D mobile viewer real manifests with thermal/memory budgeting and 100% authentic 2D rubbing fallback rejecting fictional 3D shapes.
  - `V5-T055` (W05-A05): Mobile source citation UI with draggable sheet, bilingual translations, epistemic uncertainty indicators, and redaction of restricted snippets.
  - `V5-T056` (W05-A06): Offline action queue with client idempotency keys, server ACK deduplication, conflict resolution, and anti-replay zero duplicate XP awards.
  - `V5-T057` (W05-A07): Mobile lesson quiz sync against backend assessment tasks. Replaced mock questions in `practice_provider.dart` with authoritative server grading.
  - `V5-T058` (W05-A08): Mobile quests and achievements wired to `/api/v1/quests` with prerequisite locking, objective tracking, and atomic reward claiming.
  - `V5-T059` (W05-A09): Push notification consent with opt-in/opt-out master switch, teacher/partner alert routing, and strict zero student PII enforcement.
  - `V5-T060` (W05-A10): Flutter QA and release pipeline with Flutter SDK 3.29.0 toolchain verification, zero static analysis errors, unit tests, cold start safety, and CI workflow.

### Wave W06: Historical AI Tutor / Grounded Answers (COMPLETED)
- **Status**: 10/10 slots complete. 121/121 tests passing.
- **Artifacts**: `artifacts/implementation/W06/` (`W06_A01`–`W06_A10`).
- **Verified Invariants**:
  - `V5-T061` (W06-A01): RAG retrieval restricted to approved claims and sources; draft, unreviewed, or disputed claims return explicit abstention.
  - `V5-T062` (W06-A02): 5-point citation faithfulness validator binding generated answer spans to real retrieved source passages with precise archival locators.
  - `V5-T063` (W06-A03): Hint-first Socratic learning mode guiding students to observe motifs and cite evidence before revealing answers, with provenance inspection.
  - `V5-T064` (W06-A04): AI provider policy, model discovery, sliding-window rate limiting, and safe deterministic fallback labeled with retry policies.
  - `V5-T065` (W06-A05): Live AI provenance visibility exposing provider mode, guardrail status, and fallback indicators across WebRTC/audio and captions.
  - `V5-T066` (W06-A06): Prompt injection defenses neutralizing instruction overrides, roleplay jailbreaks, tool abuse, and credential exfiltration.
  - `V5-T067` (W06-A07): Multilingual evaluation gold-set benchmark (30 cases) penalizing plausible unsupported assertions and preserving artisan dignity.
  - `V5-T068` (W06-A08): AI child privacy and protection filters with PII sanitization in conversation logs and zero training on minor student messages without guardian consent.
  - `V5-T069` (W06-A09): AI observability and token budgeting tracking usage with zero-PII hashes and enforcing capacity limits on exhausted budgets.
  - `V5-T070` (W06-A10): Comprehensive end-to-end integration contract across History Tutor, RBPC Cultural Bridge, and Multimodal Live AI Teacher.






