# Implementation Plan: Backend Modularization

## Overview

This plan decomposes the monolithic `main.py` into a structured FastAPI package without changing any
endpoint behavior. It proceeds infrastructure-first, then domain by domain, with the full test suite
gating each increment. An OpenAPI snapshot serves as the behavior-preservation oracle.

## Tasks

- [x] 1. Establish the package skeleton and behavior oracle
  - [x] 1.1 Create `backend/app.py` with a `create_app() -> FastAPI` that constructs the app, attaches the existing CORS middleware and exception handlers, and is imported by `main.py` as `app = create_app()`. _Requirements: 1.2, 2.1_
  - [x] 1.2 Add an OpenAPI snapshot test that serializes the current schema to a fixture and asserts equality, to be run after every increment. _Requirements: 2.1, 2.3_
  - [x] 1.3 Add an import smoke test that imports `create_app()` and (incrementally) each new module, asserting no `ModuleNotFoundError`. _Requirements: 1.1, 4.1_

- [x] 2. Extract shared dependencies into `deps.py`
  - [x] 2.1 Move `get_db`, `get_current_user`, `get_current_user_optional`, role guards (`get_staff_user`, `get_admin_user`, `get_super_admin_user`), `require_feature`, and ownership deps into `backend/deps.py`, leaving temporary re-exports in `main.py`. _Requirements: 1.1, 4.3_
  - [x] 2.2 Run the full test suite and OpenAPI snapshot test; confirm green before proceeding. _Requirements: 2.2, 4.2_

- [x] 3. Extract pure domain helpers into `domain/`
  - [x] 3.1 Move rank/XP/streak/badge/certificate helper functions (e.g. `_compute_rank`, `_update_streak`, `_apply_xp_boost`, `_award_badge`, `_issue_certificate`) into `backend/domain/` modules with re-exports retained. _Requirements: 1.1_
  - [x] 3.2 Run the full test suite and OpenAPI snapshot; confirm green. _Requirements: 2.2, 4.2_

- [x] 4. Extract Pydantic schemas into `schemas/`
  - [x] 4.1 Relocate request/response models from `main.py` into `backend/schemas/` grouped by domain (auth, users, content, quests, progress, admin, live), preserving field sets and validators verbatim. _Requirements: 1.1, 2.1_
  - [x] 4.2 Run the full test suite and OpenAPI snapshot; confirm the schema is unchanged. _Requirements: 2.2, 2.3, 4.2_

- [x] 5. Extract routers one domain at a time
  - [x] 5.1 Create `backend/routers/auth.py` with an `APIRouter`, move the auth endpoints verbatim, and register via `app.include_router` in `create_app()`. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_
  - [x] 5.2 Repeat for users/profile endpoints. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_
  - [x] 5.3 Repeat for motifs/urns/lessons/quizzes endpoints. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_
  - [x] 5.4 Repeat for quests/progress/gamification endpoints. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_
  - [x] 5.5 Repeat for admin/content/RAG/analytics endpoints. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_
  - [x] 5.6 Repeat for live-session/classroom and any remaining endpoints. Run suite + snapshot. _Requirements: 1.2, 2.1, 4.1_

- [x] 6. Reduce the entry module and clean up
  - [x] 6.1 Reduce `main.py` to a thin shim (`from backend.app import create_app; app = create_app()`) and remove all temporary re-exports. _Requirements: 1.3, 4.3_
  - [x] 6.2 Remove the empty `routes/` package. _Requirements: 3.1, 3.2_
  - [x] 6.3 Add a structure test/lint asserting no empty `routes/` package and that `main.py` is below a line threshold. _Requirements: 3.1, 4.1_

- [x] 7. Final verification
  - [x] 7.1 Run the full test suite and the OpenAPI snapshot test; confirm the schema is byte-identical to the pre-refactor fixture. _Requirements: 2.1, 2.2, 2.3_
  - [x] 7.2 Run the import smoke test confirming no `ModuleNotFoundError` and no remaining re-exports. _Requirements: 1.1, 4.3_

## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": ["1"]},
    {"tasks": ["2"]},
    {"tasks": ["3", "4"]},
    {"tasks": ["5"]},
    {"tasks": ["6"]},
    {"tasks": ["7"]}
  ]
}
```

## Notes

- Strictly behavior-preserving: move code, do not rewrite logic. Any logic change belongs to another spec.
- The OpenAPI snapshot fixture (Task 1.2) is the contract oracle; regenerate it only if an intended,
  reviewed contract change occurs (none expected here).
- Each router extraction in Task 5 is independently shippable and reversible; keep increments small.
- Temporary re-exports in `main.py` are removed in Task 6.1 only after all routers are extracted.
