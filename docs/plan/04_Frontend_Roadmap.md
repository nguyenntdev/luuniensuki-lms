# 04_Frontend_Roadmap.md (Next.js UI Backlog)

## Goal

Turn the current “viewer + login + dashboard” into a complete LMS interface:

- Explore urns
- Browse motifs (collection/Pokédex)
- Read lessons
- Take quizzes
- View leaderboard + badges + streak
- (Later) Admin panel

## Current State (Implemented)

Pages (App Router):

- `GET /` (homepage)
- `GET /login`
- `GET /dashboard`
- `GET /urns/[urnSlug]` (3D viewer wrapper)

Key components:

- `UrnViewer` (R3F viewer; now loaded client-only via `UrnExperience`)
- `LessonSidebar` (motif info overlay)
- `LoginPage`, `UserProfile`

State:

- `useAuthStore` (JWT tokens, user, stats)
- `useMotifStore` (motifs + local “found” state + unlock calls)

## Missing Pages/Components (From Spec)

### Pages (Priority Order)

1. **Explore (Urn selection)**
   - `GET /explore` (or make `/` the explore page)
2. **Collection**
   - `GET /collection` (grid of locked/unlocked motifs; filters)
3. **Motif lesson page**
   - `GET /motif/[motifId]` (full lesson content + “start quiz” CTA)
4. **Motif quiz page**
   - `GET /motif/[motifId]/quiz`
5. **Leaderboard**
   - `GET /leaderboard`
6. **Profile**
   - `GET /profile` (can alias to `/dashboard`)
7. **Admin**
   - `GET /admin/*` (later)

### Components (Suggested)

- `MotifCard`
- `CollectionGrid`
- `FiltersBar` (category/rarity/urn)
- `LessonViewer` (render lesson description)
- `QuizContainer`
- `MultipleChoiceQuestion` (MVP)
- `ProgressBar` (extract from `UserProfile`)
- `BadgeShelf` + `BadgeCard`
- `StreakWidget`
- `LeaderboardTable`

## State Management (Zustand)

Recommended store split:

- `authStore` (already)
- `urnStore`:
  - urn list
  - selected urn
- `collectionStore`:
  - user collection items
  - filters/sort
- `quizStore`:
  - current quiz session (questions, answers, submit status)

## API Integration Notes

- Prefer same-origin API:
  - Next calls `/api/v1/...` through nginx proxy.
- For public content:
  - `GET /api/v1/urns`
  - `GET /api/v1/motifs/{id}`
- For authenticated progress:
  - attach `Authorization: Bearer <token>`

## Task Breakdown (Ticket-Sized)

### Explore

- [ ] **FE-EXPLORE-01**: Add API call `getUrns()`
- [ ] **FE-EXPLORE-02**: Add page `frontend/src/app/explore/page.jsx`
- [ ] **FE-EXPLORE-03**: Urn grid UI (thumbnail + progress badge)

### Collection

- [ ] **FE-COLL-01**: Add page `frontend/src/app/collection/page.jsx`
- [ ] **FE-COLL-02**: `CollectionGrid` component consuming `/api/v1/users/me/collection`
- [ ] **FE-COLL-03**: Filters for category/rarity/urn + search

### Motif Lesson

- [ ] **FE-MOTIF-01**: Add page `frontend/src/app/motif/[motifId]/page.jsx`
- [ ] **FE-MOTIF-02**: Render full lesson (`description`) + “Complete lesson” button
- [ ] **FE-MOTIF-03**: Wire `complete-lesson` endpoint + update local progress state

### Quiz

- [ ] **FE-QUIZ-00**: Implement quiz API client + store (see `docs/plan/02_Quiz_System.md`)
- [ ] **FE-QUIZ-01**: Quiz page + components (multiple choice MVP)
- [ ] **FE-QUIZ-02**: Results view + “Retry” and “Back to motif”

### Leaderboard + Gamification UI

- [ ] **FE-LB-01**: `/leaderboard` page
- [ ] **FE-BADGE-01**: Badge shelf on dashboard/profile
- [ ] **FE-STREAK-01**: Streak widget on dashboard/profile

### Admin (Later)

- [ ] **FE-ADMIN-00**: Admin layout + route protection
- [ ] **FE-ADMIN-01**: CRUD pages for urns/motifs/lessons/quizzes/badges

## Definition of Done (Frontend “Core LMS”)

- Explore page lists urns and opens the viewer.
- Collection page shows locked/unlocked motifs with filters.
- Motif page shows full lesson and can transition to quiz.
- Quiz page works end-to-end with backend submit.
- Dashboard shows rank + progress + badges/streak (at least MVP).

