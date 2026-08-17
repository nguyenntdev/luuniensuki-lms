# CURRENT SYSTEM STATE — Lưu Niên Sử Kí LMS

Audit date: 2026-08-17. This document is the runtime-truth ledger for the History-First rebuild (REPO-001). Code/config/tests/migrations are truth; prose docs are claims to verify.

## Repo & branch

- Default branch: `main`. Audited HEAD: `cd637b5` (2026-08-17, pushed to GitHub).
- Canonical remote: `https://github.com/nguyenntdev/luuniensuki-lms.git`.
- Production server: `/opt/luuniensuki-lms` is a git checkout synced to `origin/main`.
- Note: the initial local working copy (`luuniensuki-lms-snapshot-backup`) was a stale non-git snapshot; work moved to a git clone (see DEC-0001).

## Service inventory

| Service | Dir | Port | Role |
|---------|-----|------|------|
| Nginx | — | 80/443 | Reverse proxy, static assets |
| Next.js web | `frontend/` | 3000 | Client UI (App Router, mixed JS/TSX) |
| Rust API gateway | `backend-rust/` | 8001 | Native Axum routes + gateway proxy |
| FastAPI (legacy) | `backend/` | 8000 | Fallback origin for un-migrated routes |
| AI teacher worker | `services/ai_teacher_agent/` | — | Background worker for live AI teacher |
| LiveKit | — | 7881 | Live learning audio/video |
| Janus gateway | `janus/` | 7088/8188 | Alternate WebRTC gateway |
| PostgreSQL 15 | — | 5432 | Primary DB |

Request flow: Browser → Nginx → Next.js (:3000) → Rust gateway (:8001) → native route OR proxy to FastAPI (:8000) → PostgreSQL.

## Rust API route inventory

- `backend-rust/docs/route-inventory.json` lists **291 routes** (admin 77, misc 116, lessons 22, classrooms 20, users 20, etc.).
- **Route dispatch is config-driven and hot-reloadable** via `config/route-modes.toml` (`Dispatcher` in `src/dispatcher.rs`). Default for unlisted routes: **`unknown_routes = "native"`** — all registered Axum handlers serve natively; unregistered routes fall through to `gateway::fallback_to_python`.
- Routes pinned to `gateway` in `route-modes.toml`: Live AI teacher (`/api/v1/live/*`), AI tutor (`/api/v1/ai-tutor/*`), live demo-enter — proxied to Python.
- **Stale doc note:** the `"status"` field inside `route-inventory.json` is **not** a live native/gateway indicator (all currently read `"gateway"`); the actual serving mode is decided by `Dispatcher` + `route-modes.toml` + which Axum handlers are registered in `main.rs` (`build_router`). The route-inventory is used for coverage assertion (`inventory::assert_full_coverage`) and the `/api/v1/internal/route-coverage` endpoint.
- Native modules (`backend-rust/src/routes/`): health, auth, users, content, badges, lessons, quizzes, progress, quests, classrooms, leaderboard, notifications, sessions, crash_reports, admin, admin_render, streak_* (admin/comeback/friend/repair), fsrs/reviews, timeline, trails, live, misc, metrics.
- Background jobs: streak rollover, friend streak, trail reminder, trail certificate retry (`src/jobs/`).
- Cargo deps are exact-pinned (`=`); release profile tuned for low-memory build host (`codegen-units=1`, `lto="thin"`). Build budget documented in `backend-rust/docs/build-budget.md` (CI-enforced parity).
- Server toolchain quirk: system cargo is 1.75 (too old for lockfile v4); use `/root/.cargo/bin/cargo` (rustup 1.95).

## Python backend responsibilities

- **Modularized**: `backend/main.py` is a thin shim → `backend/app.py` `create_app()` factory → `backend/routers/*` (auth, users, content, gamification, classrooms, live, admin, ai, social, misc). Business logic in `backend/services/*`, helpers in `backend/domain/*`.
- **Root-level `main.py`, `models.py`, `schemas.py`, `seed.py`, `config.py` and root `versions/` are stale pre-modularization copies.** Dockerfile copies only `backend/`, `data`, `alembic.ini`, `migrations`. Never edit root copies.
- Auth: JWT in httpOnly cookies (`luuniensuki_access`/`luuniensuki_refresh`), OAuth2 header kept for tests. Roles: guest < learner < teacher < admin < super_admin (`backend/rbac.py`).
- Config fails closed at import in production (rejects sentinel JWT secrets, wildcard CORS + credentials) — `backend/config.py` validator.
- Error envelope: `{"error": {"code", "message", "details"}}`.
- Static mounts: `/assets` → `backend/assets`, `/uploads/avatars` → `avatar_dir`.
- AI (Python): AI tutor/coach/explain/feedback/insights, RAG documents + embeddings, adaptive quiz, quiz hints, lesson/quiz generation, conversation history, AI jobs. DeepSeek-compatible endpoint (`DEEPSEEK_BASE_URL`).

## AI / live worker responsibilities

- `services/ai_teacher_agent/realtime_worker.py` — realtime AI teacher worker (runs as separate compose service `ai_teacher_agent`).
- Live voice: STT/TTS streaming, VAD endpointing, turn-taking state machine, WebRTC audio bridge (aiortc), circuit breaker, rate limits, cost ceilings — `backend/services/live_*.py` + `backend/tests/test_live_*.py`.

## PostgreSQL schemas & migrations

- 61 migration files in `migrations/versions/` (up to `0047_revoked_refresh_tokens`), plus shared `migrations/env.py`.
- **~80 ORM models** in `backend/models.py` (users, urns, motifs, lesson_content, quiz_questions, quiz_attempts, user_progress, spaced_repetition_cards, badges, user_badges, streaks-on-user, classes, class_members, quests, daily_missions, weekly_quests, hearts, leaderboard settings, leagues, certificates, live sessions, ai_conversations, rag_documents, tags, content_provenance, content_flags, analytics_events, audit_logs, user_sessions, feature_flags, experiments, and more).
- **Rust-owned tables (raw-SQL migrations, no Python ORM/routes):** `heritage_eras`, `historical_events`, `motif_eras` (0043), `trails`, `trail_steps`, `trail_checkpoints`, `user_trail_progress`, `user_trail_checkpoint_responses`, `trail_certificates` (0044), FSRS columns/params on `spaced_repetition_cards` + `user_fsrs_params` + `fsrs_cohort_params` (0045), `live_janus_rooms` (0046).
- **Migration history is branched.** `alembic heads` reports 3 heads: `0047_revoked_refresh_tokens`, `0033_feature_flags_experiments`, `0032_email_scheduling`. Production DB's `alembic_version` contains 14 version rows. New migrations MUST chain onto the intended lineage (currently `0047_revoked_refresh_tokens`) and avoid re-branching.
- Production DB currently has **100 tables** (`information_schema` count).

## FSRS implementation state

- FSRS (FSRS-6 style, `DEFAULT_W` weights) is **implemented in Rust** (`backend-rust/src/services/fsrs_service.rs`, `src/models/fsrs.rs`). DB columns added by migration 0045. Review routes: `/api/v1/reviews/due`, `/api/v1/reviews/:card_id/rate`, `/api/v1/users/me/fsrs-settings`.
- Python's `spaced_repetition.py` is **SM-2** (older review path at `/api/v1/review/*`). Do not conflate.

## Lesson / quiz model

- Lessons = `lesson_content` per motif (intro, description, historical_context, symbolism, fun_fact, `is_ai_generated`).
- Quizzes = `quiz_questions` per motif + `urn_exams` + `quiz_attempts`. Question types: multiple_choice, true_false, image_select, mesh_location.
- Progress flow: `hidden → discovered → learned → mastered`. XP: discovery 25 / lesson 50 / mastered 75; quiz pass ≥ 80%; urn exam 300.

## Timeline / trail state

- **Timeline** (Rust): `/api/v1/timeline/*` — heritage eras + historical events (from 0043). Frontend `/timeline` page exists (`TimelineClient`, `TimelineTrack`, `EventPanel`, `CompareModal`).
- **Trails** (Rust): `/api/v1/trails/*`, `/api/v1/admin/trails`, `/api/v1/teacher/trails` — public trails, admin, teacher (classroom). Frontend `/trails` + `/trails/[slug]`.
- These predate the History-First entity model; the rebuild extends rather than replaces them.

## 3D assets & supported urns

- Web: `frontend/public/assets/models/CAO-DINH-v1*.glb` (512/1k/2k + symlink). Only **Cao Đỉnh** has a committed model; other urns rely on backend `model_url`.
- Viewer: `frontend/src/components/UrnViewer.tsx` (R3F/three), hotspots from DB `pos_x/y/z` + `bounding_radius` + `mesh_name`. `UrnExperience.tsx` wraps viewer+sidebar. Mobile uses `model_viewer_plus` (WebView bridge) with local/remote GLB + quality selection.
- Coordinates: `motif-coordinates-{cao,chuong,huyen}-dinh.json` (18 items each); only 3 urns have coordinate files.

## Mobile (Flutter)

- `mobile/` — Flutter, Riverpod (codegen) + freezed + GoRouter + Dio (httpOnly cookie auth) + Hive/secure storage.
- Feature modules: achievements, ai_chat, auth, collection, daily_goals, explore, gems, hearts, help, learning_path, lesson, mascot, notifications, onboarding, practice, profile, quiz, settings, social, streak, urn_viewer.
- **No atlas, no map, no timeline, no trails screens** in mobile (timeline/trails are web-only).
- 3D: `features/urn_viewer/` with quality selection + hotspot overlay. Assets: `mobile/assets/models/CAO-DINH-v1*.glb`.

## Auth model

- JWT HS256, iss `luuniensuki`, aud `luuniensuki-app` (cross-backend contract; transition flag `JWT_VALIDATE_NEW_CLAIMS`). httpOnly cookies, refresh rotation, revoked-refresh-token tracking (0047).
- Guest role: only `is_demo: true` content. Age-verify gating, starting-path onboarding.

## Deployment topology

- Local/dev: `docker-compose.yml`; production: `docker-compose.prod.yml` + `.env.prod` (secrets outside git), prod at `https://lms.histolab.icu`.
- CI: `.github/workflows/ci.yml` (backend pytest w/ Postgres service, frontend lint:ci + build + Playwright `@smoke`); `deploy.yml` (tests → SSH deploy to `/opt/luuniensuki-lms`, `git reset --hard origin/main`, compose pull/build/up, `alembic upgrade head`, health check).
- Manual safe deploy: `scripts/deployment/deploy-safe.sh`. Smoke after deploy: pages return 200, `/api/v1/ranks` returns 401 unauthenticated.
- **Operational constraint (Aug 2026):** production host `/` is at ~95–98% full. Any image build/test on the host must first free space. Server test DB container `lms-test-db` exposes Postgres on `127.0.0.1:5433` (db `luuniensuki_test`).

## CI checks (current)

- `ci.yml`: backend `pytest` (DATABASE_URL to service Postgres `luuniensuki`); frontend `npm run lint:ci`, `npm run build`, Playwright smoke (`PLAYWRIGHT_GREP=@smoke`).
- `deploy.yml` test job: `pytest tests/backend`, `lint:ci`, `build`.

## Automated test coverage (baseline, 2026-08-17)

- **Python:** `tests/backend/` — 116 passed (incl. `test_openapi_snapshot.py` byte-for-byte HTTP contract pin, `test_cross_backend_contract.py` Python/Rust parity, security/ownership/integrity tests). Run via `DATABASE_URL=... pytest tests/backend`. Requires a reachable Postgres (default `luuniensuki_test`; server test DB on :5433).
- `backend/tests/` — live audio bridge, cancel, realtime, stt/tts/vad/turn unit tests.
- **Rust:** `backend-rust/tests/` (integration + property/proptest). Baseline run in progress at audit time; server toolchain must be rustup cargo.
- **Frontend:** type-check (tsc --noEmit) green; `lint:ci` green; vitest 27 tests green; Playwright suite exists (`e2e/`: auth, collection, explore, quiz, smoke).

## Public routes (no auth required)

- Current: only `/login`, `/register` + static assets are public; `frontend/middleware.ts` redirects everything else to `/login?returnUrl=...` (force-login).
- **History-first rebuild must add public prefixes** for `/cuu-dinh`, `/atlas`, `/map`, `/timeline`, `/stories`, `/sources`, `/explore`, and the homepage.
- Rust native unauth'd read endpoints already exist (e.g. `/api/v1/ranks` returns 401 without token; `/health` open; `/api/v1/tags` open; content ratings open).

## Admin / teacher routes

- Admin: `/api/v1/admin/*` — lessons, quiz-questions, content (versions/revert/tags/flags/pending-review), rag, ai seed, tags, analytics, experiments, feature-flags, abuse reports, crash reports, email templates, app versions, live-sessions maintenance.
- Teacher: classroom assignments, trails (`/api/v1/teacher/trails`).

## Remaining explicit unchecked tasks in `.kiro/specs`

- `full-rust-backend-migration/tasks.md` — 43 unchecked (mostly property-test hardening items marked `[ ]*`, e.g. dispatcher/gateway property tests).
- `frontend-consolidation-typing/tasks.md` — 4 unchecked.
- `live-room-rust-janus-migration/tasks.md` — 16 unchecked.
- `backend-modularization`, `security-hardening-remediation`, `fsrs-spaced-repetition`, `heritage-time-lapse`, `heritage-trail-mode`, `streak-repair-economy` — all checked complete.

## Stale documents & planned corrections

- `README.md` — describes early Rust scope (4 native endpoints); update to reflect current config-driven native routing + history-first vision.
- `docs/ARCHITECTURE.md` — refresh route ownership (dispatcher config, not fixed endpoint list).
- `docs/DOCUMENTATION_INDEX.md` — add history-first docs.
- Feature-proposal docs that list implemented systems (FSRS, trails, timeline) as proposals — mark historical/archived.
- Mobile implementation-state docs — mark stale where they predate urn_viewer/quiz modules.
- `backend-rust/README.md` — outdated "current scope" (still says only health/ranks/ratings/tags native).

## Architecture decisions (summary)

- Extend current stack: PostgreSQL 15, Rust gateway (native-first), FastAPI fallback, Next.js, Flutter, existing AI worker. No Elasticsearch/graph DB/new auth/frontend rewrite.
- History domain will live in new tables/migrations chained onto `0047`, served via Python FastAPI (new `/api/v1/history/*` router) and proxied natively by Rust gateway fallback; stable read groups may later move to Rust native.
- Guest/public access to historical content is mandatory (no login wall).