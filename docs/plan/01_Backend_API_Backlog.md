# 01_Backend_API_Backlog.md

## Goal

Bring the FastAPI backend from “auth + unlock” to a **complete gameplay API** (urn browsing → motif discovery → lesson → quiz → progression), while keeping current production routes compatible.

## Current State (Implemented)

- Auth:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- Content:
  - `GET /motifs/{urn_name}` (legacy/non-versioned route used by the current frontend)
- Progress:
  - `POST /progress/unlock` (protected by JWT)
  - `GET /api/v1/users/me/collection` (protected)

## Guiding Principles

1. **Don’t break production**: keep `/motifs/*` and `/progress/*` routes working.
2. All new APIs go under `/api/v1/...`.
3. Prefer **explicit states**: `hidden → discovered → learned → mastered`.
4. Make write endpoints **idempotent** where possible (mobile double-tap, retries, etc.).

## Near-Term Endpoint Backlog (Priority Order)

### A) Urn discovery (unblocks FE /explore)

- **BE-URN-01**: `GET /api/v1/urns`
  - Returns all urns with `slug`, `name`, `model_url`, `display_order`, `is_demo`
  - Include counts: `motif_total`, `motif_demo_total` (optional but useful)
  - **DoD**: pagination not required (9 urns), but ordering must be stable.

- **BE-URN-02**: `GET /api/v1/urns/{slug}`
  - Returns one urn + metadata (and optionally hero image/model URL).
  - **DoD**: 404 for unknown slug, tests.

- **BE-URN-03** (optional): `GET /api/v1/urns/{slug}/motifs`
  - Versioned alternative to `GET /motifs/{urn_name}`.
  - Keep old route as compatibility alias.

### B) Motif detail + lesson completion (unblocks /motif/[id])

- **BE-MOTIF-01**: `GET /api/v1/motifs/{motif_id}`
  - Returns motif + lesson content (full `LessonContent.description`, not only intro).
  - Include user-specific status when authenticated (optional): `status`.

- **BE-LESSON-01**: `POST /api/v1/motifs/{motif_id}/complete-lesson`
  - Requires auth.
  - If status is `discovered`, transition to `learned` and award XP bonus.
  - Idempotent: repeated calls should not re-award XP.
  - **DoD**: tests for 200/401/404 and idempotency.

### C) User progress views (unblocks dashboard + collection page)

- **BE-USER-01**: `GET /api/v1/users/me/progress`
  - Returns per-urn progress + totals by category/rarity.
  - Designed for dashboards and “quest” display.

- **BE-USER-02**: `GET /api/v1/users/me/activity`
  - Returns last activity timestamps, last unlocked motif, etc. (drives streak logic).

### D) Leaderboard (gamification)

- **BE-LB-01**: `GET /api/v1/leaderboard`
  - Default: top 50 by `total_xp`
  - Include `me_rank` if authenticated.
  - Cache layer can be added later (see `docs/plan/03_Gamification.md`).

### E) Admin APIs (content operations)

- **BE-ADMIN-00**: Admin auth model and access rules
  - Define `admin` and `super_admin` permissions.
  - Decide if admins can edit user XP/progress.

- **BE-ADMIN-01**: CRUD Urns: `GET/POST/PATCH/DELETE /api/v1/admin/urns`
- **BE-ADMIN-02**: CRUD Motifs: `.../admin/motifs`
- **BE-ADMIN-03**: CRUD Lessons: `.../admin/lessons`
- **BE-ADMIN-04**: CRUD Quiz Questions: `.../admin/quiz-questions`
- **BE-ADMIN-05**: CRUD Badges: `.../admin/badges`

## Architecture Tasks (Refactor & Maintainability)

The backend currently has a large “single-file service” shape. Before adding 50+ endpoints, split into modules.

- **BE-CORE-01**: Create backend module layout
  - `backend/config.py` (Settings)
  - `backend/db.py` (engine/session dependencies)
  - `backend/security.py` (already exists)
  - `backend/routers/*.py` (grouped endpoints)
  - `backend/services/*.py` (business rules: xp, progression, streak, badges)
  - `backend/schemas/*.py` (Pydantic DTOs)
  - Update `backend/main.py` to only mount routers.

- **BE-CORE-02**: Add `/api/v1/health`
  - Returns DB connectivity + build metadata (git sha optional).
  - Used by uptime monitors and deploy checks.

- **BE-CORE-03**: Rate limiting strategy
  - Minimum: per-IP for auth endpoints.
  - Optional: API gateway or nginx `limit_req` (see deployment docs).

## Acceptance Criteria (Backend “Core Gameplay”)

1. A user can:
   - list urns → open urn → list motifs → unlock motif → read lesson → complete lesson → take quiz → see XP/rank updated.
2. All write endpoints are safe under retries (no duplicate XP, no duplicate progress rows).
3. OpenAPI reflects all endpoints (with auth + response models).

