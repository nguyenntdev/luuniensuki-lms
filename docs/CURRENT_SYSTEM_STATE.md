# CURRENT SYSTEM STATE — Lưu Niên Sử Kí LMS

**Audit Date:** 2026-08-19  
**Specification Reference:** REPO-001 (`docs/specs/HISTORY_FIRST_MASTER_SPEC.md`)  
**Audited Commit HEAD:** `6ebb285791b8f7ef9ac965aadf23f006ca074920`  
**Default Branch:** `main`

This document serves as the authoritative runtime-truth ledger for the History-First rebuild. Code, configuration, migrations, and tests represent system truth; prose documentation represents claims to be audited.

---

## 1. Services Inventory

| Service | Directory / Location | Port | Role & Tech Stack |
|---|---|---|---|
| **Frontend** | `frontend/` | 3000 | Client UI built with Next.js 15 (App Router, mixed TSX/JS, React 19/R3F) |
| **Rust Gateway** | `backend-rust/` | 8001 | High-performance Axum API gateway & native route execution engine |
| **Python Backend** | `backend/` | 8000 | FastAPI application package providing business logic fallback & legacy services |
| **AI Worker** | `services/ai_teacher_agent/` | - | Standalone background worker process for live AI teacher interactions (`realtime_worker.py`) |
| **LiveKit** | Docker compose service | 7881 | Live WebRTC audio/video learning service |
| **Janus Gateway** | `janus/` | 7088/8188 | WebRTC gateway alternative for live room signaling & audio bridges |
| **PostgreSQL** | Docker compose service | 5432 | Primary relational database (PostgreSQL 15) |
| **Nginx** | Docker compose service | 80/443 | Reverse proxy & static asset web server |

**Request Flow Topology:**  
`Browser Client → Nginx (80/443) → Next.js (3000) → Rust Gateway (8001) → [Native Axum Route OR Fallback Proxy] → Python FastAPI (8000) → PostgreSQL 15`

---

## 2. Python Services & Routers (`backend/`)

- **Architecture:** `backend/` is the canonical Python backend package run via `uvicorn backend.main:app` using `create_app()` from `backend/app.py`.
- **Domain Routers (11 main domain router groups in `backend/routers/`):**
  - `auth.py`: Authentication, registration, token refresh, password management, guest preview
  - `users.py`: User profile, preferences, daily goals, learning path
  - `content.py`: Lessons, quiz questions, ratings, tags, content versioning
  - `gamification.py`: XP, streaks, hearts, leaderboards, leagues, badges, quests
  - `classrooms.py`: Teacher classroom management, student rosters, assignments
  - `live.py`: Live sessions, Janus/LiveKit room signaling, VAD, voice configuration
  - `admin.py`: Content moderation, audit logs, feature flags, experiments, abuse reports
  - `ai.py` / `history_tutor.py`: AI tutor, RAG embeddings, feedback, history tutor
  - `history_stories.py` / `history_collections.py` / `history_learning.py` / `history.py`: History-first entities, claims, sources, stories, collections
  - `social.py`: User sharing, activity feeds, social interactions
  - `misc.py`: Health checks, app versions, static asset metadata
- **Services Inventory (50 domain service modules in `backend/services/`):**
  - Live AI & Voice: `live_ai_teacher`, `live_audio_bridge`, `live_cancel`, `live_circuit_breaker`, `live_crypto`, `live_observability`, `live_rate_limits`, `live_realtime`, `live_session_reporting`, `live_sessions`, `live_stt_stream`, `live_tts_chunk`, `live_turn`, `live_vad`, `live_voice`
  - History & Governance: `history_governance`, `history_learning`, `history_stories`, `history_collections`, `history_tutor`
  - Learning & Spaced Repetition: `adaptive_quiz`, `learning_path`, `lesson_sequence`, `quiz_hints`, `spaced_repetition`, `student_progress`
  - Analytics & AI Insights: `ai_insights`, `ai_tutor`, `analytics`, `analytics_dashboard`, `analytics_funnels`, `embeddings`, `experiment_analytics`, `experiments`, `feature_flags`, `funnel`
  - Gamification & Economy: `daily_goal_settings`, `hearts`, `leaderboard`, `leagues`, `milestones`, `quest_assignments`, `social`, `sharing`, `streak`, `weekly_quests`
  - Administration & System: `abuse_reports`, `audit`, `classroom`, `email_scheduler`, `push_notifications`, `retention`, `recommendations`

---

## 3. Rust API Gateway Status (`backend-rust/`)

- **Server:** Axum HTTP framework listening on port `8001`.
- **Serving Behavior:** Config-driven via `config/route-modes.toml` dispatcher (`src/dispatcher.rs`).
- **Native Endpoint Ownership:**
  - `/health`
  - `/api/v1/ranks`
  - `/api/v1/tags`
  - `/api/v1/content/ratings`
  - `/api/v1/timeline/*` (Heritage eras & historical events)
  - `/api/v1/trails/*` (Heritage trails, checkpoints, and user trail progress)
  - `/api/v1/reviews/*` (FSRS native spaced repetition cards, rating, due reviews)
- **Proxy Fallback:** Un-migrated routes (including AI tutor, live sessions, social feeds, admin governance) are transparently proxied to Python FastAPI on port `8000`.

---

## 4. PostgreSQL Schemas & Alembic Migrations

- **Migration Directory:** Canonical Alembic migrations are located in `migrations/` (`alembic.ini` sets `script_location = migrations`).
- **Migration Head:** Migration chain up to `0047_revoked_refresh_tokens.py` (with recent history domain extensions up to `0052_history_collections.py` chained on top).
- **Core Schemas & Tables (~100 tables):**
  - Auth & Users: `users`, `user_profiles`, `user_sessions`, `revoked_refresh_tokens`
  - History Domain: `historical_entities`, `historical_claims`, `historical_sources`, `historical_claim_sources`, `historical_entity_relations`, `historical_geographies`, `historical_assets`, `history_stories`, `history_collections`, `content_provenance`
  - Heritage 3D & Content: `urns`, `motifs`, `lesson_content`, `quiz_questions`, `quiz_attempts`, `heritage_eras`, `historical_events`, `trails`, `trail_steps`, `trail_checkpoints`
  - Spaced Repetition: `spaced_repetition_cards`, `user_fsrs_params`, `fsrs_cohort_params`
  - Live Learning & AI: `live_sessions`, `live_events`, `live_janus_rooms`, `ai_conversations`, `rag_documents`, `rag_embeddings`
  - Gamification & Classroom: `streaks`, `hearts`, `badges`, `user_badges`, `classes`, `class_members`, `quests`, `daily_missions`, `weekly_quests`, `leaderboards`, `leagues`

---

## 5. Auth & Permission Model

- **Tokens:** JWT HS256 algorithm with httpOnly cookie storage (`luuniensuki_access` and `luuniensuki_refresh`).
- **Header Interop:** Supports standard `Authorization: Bearer <token>` headers primarily for API testing and cross-backend contract validation.
- **Revocation & Security:** Server-side token refresh rotation and revoked token tracking (`revoked_refresh_tokens`). Strict validation rules enforced in `backend/config.py`.
- **Role-Based Access Control (RBAC):**
  - Hierarchy: `guest` < `learner` < `teacher` < `admin` < `super_admin` (`backend/rbac.py`).
  - Guest Restrictions: Guests can only access demo-permitted content (`is_demo: true`).

---

## 6. FSRS Implementation State

- **Rust Native Engine:** Primary FSRS-6 algorithm implemented in Rust (`backend-rust/src/models/fsrs.rs`, `backend-rust/src/routes/reviews.rs`).
- **Database Schema:** Extended via migration `0045_fsrs_spaced_repetition.py` (adds stability `s`, difficulty `d`, state, last_review, and FSRS user parameters).
- **Python Fallback Model:** Legacy Python `SpacedRepetitionCard` model retained for SM-2 fallback compatibility (`backend/services/spaced_repetition.py`).

---

## 7. 3D Assets & Motif Data

- **3D Urn Models:** 9 Dynastic Urns (Cao, Nhân, Chương, Thái, Thánh, Tuyên, Dụ, Khẩn, Anh Đỉnh). Web 3D viewer supports Cao Đỉnh (`CAO-DINH-v1*.glb`) with R3F; other urns fallback to remote/backend GLB assets.
- **Motif Coordinates:** 162 motif coordinate files mapped across the urn corpus stored under `data/` (18 reliefs per urn).
- **Image Assets:** Relief photo and texture assets stored in `ban-duc-noi/` and served via Nginx at `/assets/ban-duc-noi`.

---

## 8. Mobile Application (`mobile/`)

- **Framework:** Flutter client utilizing Riverpod (state management with codegen), Freezed (immutable data models), GoRouter, and Dio with httpOnly cookie support.
- **Modules:** Explore, Urn Viewer (WebView bridge using `model_viewer_plus`), Lessons, Quizzes, Practice, Auth, User Profile, Streaks, Hearts, Achievements, Badges, Daily Goals, AI Tutor Chat, Settings.
- **Storage:** Secure storage and local Hive key-value cache.

---

## 9. Baseline Test & Code Quality Status

- **Python Tests:** 126/126 `pytest` tests passing against the local/test PostgreSQL database (`luuniensuki_test`).
  - Covers HTTP contract pinned by `tests/backend/test_openapi_snapshot.py`.
  - Covers Python/Rust contract parity in `tests/backend/test_cross_backend_contract.py`.
- **Frontend Quality:**
  - TypeScript compilation: `npm run type-check` (`tsc --noEmit`) passes cleanly.
  - Linting: Strict ESLint (`npm run lint:ci`) passes with zero warnings.
  - Unit tests: Vitest test suite passes.

---

## 10. Stale Documents & Repository Truth Reconciliation

- **Canonical Code Locations:**
  - `backend/` is the active Python backend package.
  - `backend-rust/` is the active Rust gateway.
  - `frontend/` is the active Next.js web application.
  - `migrations/` is the canonical Alembic migration directory (`alembic.ini`).
- **Legacy Stale Files (Do Not Edit / Do Not Execute):**
  - Root `main.py`, `models.py`, `schemas.py`, `seed.py`, `config.py` (~18k lines pre-modularization monolith) are obsolete.
  - Root `versions/` folder is a stale migration duplicate.
  - Docker containers and build pipelines ignore all root legacy duplicates.
