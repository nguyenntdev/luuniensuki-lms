# 13_Execution_Plan_Detailed.md — “Finish the Product” Plan (Backend + Frontend + Infra)

This plan turns the gap analysis into an **execution checklist** with concrete deliverables, acceptance criteria, and tests.

> Target domain (prod): `lms.histolab.icu`  
> Note: do **not** commit secrets (`.env.prod`, SSH creds, JWT secret, DB password).

---

## High-Level Goal

Ship a complete, production-grade MVP of “Lưu Niên Sử Kí”:

- Users can **register/login**
- Explore **urns**, click **motifs**, read **lessons**
- Take **quizzes** to progress `discovered → learned → mastered`
- Track **collection**, **streak**, **badges**, **leaderboard**
- Seed pipeline is repeatable and includes **thumbnails** via `/assets/ban-duc-noi/...`
- A minimum test suite prevents regressions

---

## Phase 0 — Baseline Stability (Already Done)

- Seed thumbnails via scanning `ban-duc-noi/` → `Motif.thumbnail_url` (`backend/seed.py`)
- Nginx serves `/assets/*` from `/var/www/assets/*` (`nginx.conf`)
- Prod compose mounts images into `nginx` and `api` (`docker-compose.prod.yml`)

Acceptance:
- `GET https://lms.histolab.icu/assets/ban-duc-noi/...jpg` returns `200`
- `GET /motifs/{urn_slug}` returns motifs with `thumbnail_url` populated

---

## Phase 1 — Backend API Completion (Core Gameplay)

### BE-API-01 — Urn listing + detail

Deliverables:
- `GET /api/v1/urns` → list urns (sorted by `display_order`)
- `GET /api/v1/urns/{slug}` → urn detail (+ optionally motifs summary)

Acceptance:
- Returns `200` for seeded urns
- `404` for unknown slug

Tests:
- `tests/backend/test_urns.py` (list + detail)

---

### BE-API-02 — Motif detail

Deliverables:
- `GET /api/v1/motifs/{motif_id}` → motif + lesson + quiz availability

Acceptance:
- Does not expose `quiz_questions.correct_answer`
- Returns `404` for unknown motif id

Tests:
- `tests/backend/test_motifs.py`

---

### BE-API-03 — Lesson completion + progress state transitions

Deliverables:
- `POST /api/v1/motifs/{motif_id}/complete-lesson`
  - requires auth
  - upserts `user_progress` for motif
  - sets `lesson_viewed_at`
  - transitions:
    - `hidden/discovered` → `learned` (if unlocked) or `discovered` (if not unlocked yet)
  - awards XP (configurable constants)

Acceptance:
- `401` without token
- `200` with token
- `user.total_xp` increments once per milestone (idempotent)

Tests:
- `tests/backend/test_lessons.py`

---

## Phase 2 — Backend Quiz + Gamification

### BE-QUIZ-01 — Quiz fetch

Deliverables:
- `GET /api/v1/motifs/{motif_id}/quiz`
  - requires auth
  - returns active questions with `options` but NOT `correct_answer`

Tests:
- `tests/backend/test_quiz.py::test_get_quiz_hides_answers`

---

### BE-QUIZ-02 — Quiz submit + attempts

Deliverables:
- `POST /api/v1/quizzes/submit`
  - requires auth
  - computes score + percentage
  - creates `quiz_attempts` row
  - updates `user_progress.quiz_attempts`, `quiz_best_score`
  - transitions:
    - pass threshold → `mastered`
    - otherwise remains `learned/discovered`
  - awards XP on first pass + optional bonus

Acceptance:
- Idempotency: multiple submits create multiple attempts but `best_score` only increases
- Negative cases: missing answers, invalid question ids, motif mismatch

Tests:
- `tests/backend/test_quiz.py::test_submit_quiz_updates_progress`

---

### BE-GAME-01 — Streak system

Deliverables:
- `GET /api/v1/users/me/streak`
- Streak update happens on:
  - unlock progress
  - complete lesson
  - submit quiz

Rules (MVP):
- If last activity is yesterday → `current_streak += 1`
- If last activity is today → no change
- If gap > 1 day → reset to 1 (or 0 if you prefer)

Tests:
- `tests/backend/test_streak.py` (date math)

---

### BE-GAME-02 — Badges (seed + award)

Deliverables:
- `seed.py` (or a separate seed file) ensures baseline badges exist
- Badge award triggers (MVP):
  - first discovery
  - first mastered
  - streak 7
- `GET /api/v1/users/me/badges`

Tests:
- `tests/backend/test_badges.py`

---

### BE-GAME-03 — Leaderboard

Deliverables:
- `GET /api/v1/leaderboard?limit=50`
  - returns display_name, avatar_url, total_xp, rank number

Tests:
- `tests/backend/test_leaderboard.py`

---

## Phase 3 — Frontend MVP Pages

### FE-01 — Explore page

Deliverables:
- `/explore` shows urn grid
- Clicking urn → `/urns/[urnSlug]`

Acceptance:
- Works when logged in or anonymous

---

### FE-02 — Motif lesson page

Deliverables:
- `/motif/[motifId]` renders:
  - title, lesson text, images (thumbnail)
  - CTA: “Complete lesson” → calls backend
  - CTA: “Take quiz” → `/motif/[motifId]/quiz`

---

### FE-03 — Quiz page

Deliverables:
- `/motif/[motifId]/quiz`:
  - renders questions/options
  - submit → calls backend
  - shows result + updates local state

---

### FE-04 — Collection page

Deliverables:
- `/collection` shows collection grid (unlocked vs locked)
  - reuses `/api/v1/users/me/collection`

---

### FE-05 — Leaderboard page

Deliverables:
- `/leaderboard` shows top users

---

## Phase 4 — Production-Ready Engineering

### QA-01 — Backend tests + fixtures

Deliverables:
- `tests/backend/` using FastAPI TestClient
- A `conftest.py` that spins up a test DB (SQLite ok for unit tests, or Postgres via Docker)

Acceptance:
- `pytest` green locally/in CI

---

### DB-01 — Alembic migrations

Deliverables:
- Add Alembic config and initial migration from current models
- Update docs on how to run migrations in prod

---

### CI-01 — GitHub Actions

Deliverables:
- CI workflow:
  - backend lint/format (optional), tests
  - frontend build

---

## Phase 5 — Smoke Tests + Deploy

Local (Docker):
- `docker compose up -d --build` (dev)
- `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` (prod-like)

VPS (after deploy):
- `w3m https://lms.histolab.icu/`
- `curl -sS https://lms.histolab.icu/api/v1/urns | head`
- Login, unlock a motif, complete lesson, submit quiz, verify collection updates.

