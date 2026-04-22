# 00_Roadmap.md (Phased Delivery Plan)

## Goal

Deliver a playable LMS loop fast, then harden for production.

## Phase 0 — Stability (Done)

- Core deploy stack works on `lms.histolab.icu`
- Auth works + protected progress saving
- Viewer route `/urns/{slug}` no longer crashes SSR
- Dify coexistence handled (port separation)

## Phase 1 — Core Gameplay Loop (Priority 1)

**Objective:** user can finish “discover → learn → quiz → mastery”.

Deliverables:

- Versioned content endpoints (`/api/v1/urns`, `/api/v1/motifs/{id}`)
- Lesson completion endpoint
- Quiz fetch + submit endpoints
- Frontend lesson page + quiz page

References:

- Backend backlog: `docs/plan/01_Backend_API_Backlog.md`
- Quiz plan: `docs/plan/02_Quiz_System.md`
- Frontend plan: `docs/plan/04_Frontend_Roadmap.md`

## Phase 2 — Gamification (Priority 2)

**Objective:** add streak/badges/leaderboard to increase retention.

Deliverables:

- Badge seed + badge awarding on events
- Streak endpoint + UI widget
- Leaderboard endpoint + UI page

Reference:

- `docs/plan/03_Gamification.md`

## Phase 3 — Content + 3D Upgrade (Priority 3)

**Objective:** ship real GLB urn models with clickable motifs.

Deliverables:

- GLB pipeline + mesh naming contract
- Loader + graceful fallback
- Data extraction for motif positions/bounding radii

Reference:

- `docs/plan/05_3D_Assets_Integration.md`
- `docs/plan/06_Data_and_Seeding.md`

## Phase 4 — Production Readiness (Priority 4)

**Objective:** controlled schema changes + tests + automation.

Deliverables:

- Alembic migrations
- CI pipeline for backend tests + frontend build
- Basic observability (health endpoint + request IDs)

References:

- `docs/plan/07_DB_Migrations_Alembic.md`
- `docs/plan/08_Testing_and_QA.md`
- `docs/plan/09_CICD.md`
- `docs/plan/10_Observability.md`

## Phase 5 — Admin & Operations (Priority 5)

**Objective:** content management without engineers.

Deliverables:

- Admin endpoints + UI
- Audit logging (minimum: server logs; later: DB audit table)

Reference:

- `docs/plan/11_Admin_Panel.md`

