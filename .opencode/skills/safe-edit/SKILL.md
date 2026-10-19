---
name: safe-edit
description: Use when unsure whether a file is stale or active, or when navigating the monorepo structure. Guards against editing obsolete root-level files and routes to the correct active code locations.
---

# Safe Edit — Stale File Guard

## NEVER edit these root-level files

These are **obsolete pre-modularization artifacts** (~18k+ lines each). Nothing in runtime or Docker imports them:

| Stale file | Active replacement |
|---|---|
| `main.py` (root, ~18.3k lines) | `backend/app.py` + `backend/routers/` |
| `models.py` (root) | `backend/models.py` |
| `schemas.py` (root) | `backend/apischemas/` |
| `seed.py` (root) | `backend/seed.py` (run via `python -m backend.seed`) |
| `config.py` (root) | `backend/config.py` |
| `rbac.py` (root) | `backend/rbac.py` |
| `security.py` (root) | `backend/security.py` |
| `errors.py` (root) | `backend/errors.py` |
| `versions/` (root) | `migrations/versions/` |

## Active code map

| What | Where |
|---|---|
| FastAPI factory | `backend/app.py` (`create_app()`) |
| ASGI entrypoint | `backend/main.py` (thin shim, `backend.main:app`) |
| API routers | `backend/routers/*.py` (16 files) |
| Request/response schemas | `backend/apischemas/*.py` |
| Business logic services | `backend/services/*.py` (55 files) |
| Domain helpers | `backend/domain/*.py` |
| Configuration | `backend/config.py` (Pydantic BaseSettings) |
| Database models | `backend/models.py` |
| Alembic migrations | `migrations/versions/` |
| Rust gateway | `backend-rust/src/` |
| Frontend | `frontend/` (Next.js 15) |
| Mobile | `mobile/` (Flutter) |
| AI worker | `services/ai_teacher_agent/` |

## Two Dockerfiles

- `backend/Dockerfile` — **preferred** (non-root user, copies `services/`)
- Root `Dockerfile` — less hardened, avoid unless necessary

## Quick heuristic

If you find yourself opening a Python file at the repo root (not inside `backend/`, `tests/`, `services/`, `scripts/`, or `migrations/`), it is almost certainly stale. Check the table above before editing.
