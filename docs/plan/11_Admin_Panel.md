# 11_Admin_Panel.md (Admin APIs + UI)

## Goal

Enable non-developers to manage content safely:

- urns / motifs / lessons / quiz questions / badges
- basic user support tools (optional)

## Current State

- Roles exist: `guest`, `learner`, `admin`, `super_admin`.
- No admin-only endpoints.
- No admin UI.

## Security Requirements (Non-negotiable)

1. All admin endpoints require JWT auth.
2. Role checks:
   - `admin`: content CRUD
   - `super_admin`: user role changes, destructive ops, system config
3. Log admin actions (at least in server logs; DB audit log later).

## Admin API Surface (MVP)

All endpoints under `/api/v1/admin/*`.

### Content

- Urns:
  - `GET /admin/urns`
  - `POST /admin/urns`
  - `PATCH /admin/urns/{id}`
  - `DELETE /admin/urns/{id}`
- Motifs:
  - `GET /admin/motifs?urn_id=...`
  - `POST /admin/motifs`
  - `PATCH /admin/motifs/{id}`
  - `DELETE /admin/motifs/{id}`
- Lessons:
  - `GET /admin/lessons?motif_id=...`
  - `POST /admin/lessons`
  - `PATCH /admin/lessons/{id}`
  - `DELETE /admin/lessons/{id}`
- Quiz questions:
  - `GET /admin/quiz-questions?motif_id=...`
  - `POST /admin/quiz-questions`
  - `PATCH /admin/quiz-questions/{id}`
  - `DELETE /admin/quiz-questions/{id}`
- Badges:
  - `GET /admin/badges`
  - `POST /admin/badges`
  - `PATCH /admin/badges/{id}`
  - `DELETE /admin/badges/{id}`

### Users (MVP+)

- `GET /admin/users` (search by email)
- `PATCH /admin/users/{id}` (role changes only, super_admin)

## Admin UI (Next.js)

Routes:

- `/admin` (dashboard)
- `/admin/urns`
- `/admin/motifs`
- `/admin/motifs/[motifId]`
- `/admin/badges`

UI principles:

- show clear forms + validation errors
- disable destructive ops by default
- confirm dialogs for deletes

## Tasks

### Backend

- [ ] **ADMIN-BE-01**: Add `require_admin` dependency + tests
- [ ] **ADMIN-BE-02**: Implement urn CRUD
- [ ] **ADMIN-BE-03**: Implement motif CRUD
- [ ] **ADMIN-BE-04**: Implement lesson CRUD
- [ ] **ADMIN-BE-05**: Implement quiz question CRUD
- [ ] **ADMIN-BE-06**: Implement badge CRUD
- [ ] **ADMIN-BE-07**: Add pagination + filtering (basic)

### Frontend

- [ ] **ADMIN-FE-01**: Admin layout + route guard
- [ ] **ADMIN-FE-02**: CRUD list pages + forms
- [ ] **ADMIN-FE-03**: Toast notifications + optimistic updates (optional)

## Definition of Done (Admin MVP)

- Admin user can edit a motif lesson text and see it reflected in user-facing pages.
- Admin can add/update quiz questions for a motif.
- All admin routes are protected and tested.

