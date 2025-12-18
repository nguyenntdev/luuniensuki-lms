# 08_Testing_and_QA.md

## Goal

Introduce a minimal but real test suite so new endpoints (quiz/gamification/admin) can be shipped safely.

## Current State

- No `tests/` directory.
- No CI running tests.

## Testing Levels

1. **Unit tests** (fast): pure functions/services (XP rules, streak logic, badge rules)
2. **API integration tests** (medium): FastAPI endpoints with a real DB
3. **Smoke tests** (slow/manual): curl/w3m against staging/prod

## Backend Test Stack (Recommended)

- `pytest`
- `httpx` (or `starlette.testclient`)
- `pytest-cov`
- PostgreSQL test DB (preferred; avoids SQLite/JSONB differences)

## Proposed Test Layout

```
tests/
  backend/
    conftest.py
    test_auth.py
    test_motifs.py
    test_progress.py
    test_lesson.py
    test_quiz.py
    test_badges.py
    test_leaderboard.py
```

## Core Test Cases (MVP)

### Auth

- register success
- register duplicate email → 409
- login success
- login wrong password → 401
- `/api/v1/auth/me` requires token

### Motifs/Urns

- `GET /motifs/{urn}` returns list
- unknown urn → 404
- versioned urn endpoints once implemented

### Progress

- `/progress/unlock` requires token
- idempotent XP award (unlocking same motif doesn’t double-award)

### Lesson + Quiz

- complete lesson upgrades state once
- quiz fetch hides correct answers
- quiz submit:
  - computes score correctly
  - upgrades to mastered on pass
  - no duplicate mastery XP on retry

### Badges + Leaderboard

- badge awarded on first discovery
- leaderboard returns sorted results and (optionally) current user rank

## Smoke Tests (Staging/Prod)

Maintain a simple script for:

- GET `/`, `/login`, `/dashboard`, `/urns/cao-dinh`
- Register → login → me → unlock → collection

This can be executed with curl/w3m (matches current ops practice).

## Tasks

- [ ] **TEST-SETUP-01**: Add test deps to `backend/requirements.txt` (or a `backend/requirements-dev.txt`)
- [ ] **TEST-SETUP-02**: Add `tests/backend/conftest.py`:
  - create/drop schema via migrations (once Alembic is added)
  - DB session fixture
  - FastAPI app fixture
- [ ] **TEST-AUTH-01**: implement `test_auth.py`
- [ ] **TEST-PROG-01**: implement `test_progress.py`
- [ ] **TEST-QUIZ-01**: implement `test_quiz.py` (after quiz endpoints exist)
- [ ] **TEST-COV-01**: add coverage gate (start at 40–50%, raise gradually)

## Definition of Done

- CI runs backend tests on every PR.
- Quiz/progress/auth have coverage for main flows + key failures.
- “Bugfix without test” becomes an exception, not the norm.

