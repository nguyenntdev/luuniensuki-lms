# Implementation Plan: Heritage Time-Lapse

## Overview

This plan implements the Heritage Time-Lapse feature which adds a temporal dimension to the Cửu Đỉnh heritage content. It covers database migrations, backend models/services/routes (Rust/Axum), property-based tests (proptest), and frontend timeline page (Next.js/React).

## Tasks

- [ ] 1. Database migrations (heritage_eras, historical_events, motif_eras)
  Create Alembic migration `0043_heritage_time_lapse.py` that adds the three new tables and seed data.
  - [ ] 1.1 Create migration file `migrations/versions/0043_heritage_time_lapse.py` with `revision = "0043_heritage_time_lapse"` and `down_revision = "0042_streak_repair_economy"`.
  - [ ] 1.2 In `upgrade()`, create `heritage_eras` table with columns: `id` (UUID PK, default gen_random_uuid()), `slug` (VARCHAR(100) UNIQUE NOT NULL), `name_vi` (VARCHAR(200) NOT NULL), `name_en` (VARCHAR(200) NOT NULL), `start_year` (INT NOT NULL), `end_year` (INT NOT NULL, CHECK end_year >= start_year), `color_hex` (VARCHAR(7) NOT NULL, CHECK regex `^#[0-9A-Fa-f]{6}$`), `sort_order` (INT NOT NULL DEFAULT 0), `created_at` (TIMESTAMPTZ NOT NULL DEFAULT now()).
  - [ ] 1.3 In `upgrade()`, create `historical_events` table with columns: `id` (UUID PK, default gen_random_uuid()), `era_id` (UUID NOT NULL FK → heritage_eras(id)), `slug` (VARCHAR(100) UNIQUE NOT NULL), `name_vi` (VARCHAR(300) NOT NULL), `name_en` (VARCHAR(300) NOT NULL), `occurred_on` (DATE NOT NULL), `description_vi` (TEXT NOT NULL), `description_en` (TEXT NOT NULL), `motif_id` (UUID NULLABLE FK → motifs(id)), `urn_id` (UUID NULLABLE FK → urns(id)), `importance` (INT NOT NULL DEFAULT 1, CHECK BETWEEN 1 AND 5), `created_at` (TIMESTAMPTZ NOT NULL DEFAULT now()). Add index `idx_historical_events_occurred_on` on `occurred_on`.
  - [ ] 1.4 In `upgrade()`, create `motif_eras` table with columns: `motif_id` (UUID NOT NULL FK → motifs(id)), `era_id` (UUID NOT NULL FK → heritage_eras(id)), PRIMARY KEY on `(motif_id, era_id)`.
  - [ ] 1.5 In `upgrade()`, insert seed data: 3 eras (`gia-long-minh-mang` 1802–1841 #D4AF37 sort_order=1, `thieu-tri-tu-duc` 1841–1883 #8B4513 sort_order=2, `phap-thuoc-bao-dai` 1883–1945 #2F4F4F sort_order=3) and at least 12 historical events covering the Cửu Đỉnh casting (1835–1837).
  - [ ] 1.6 In `upgrade()`, backfill `motif_eras` so that every existing motif is linked to at least one era (default to `gia-long-minh-mang` for motifs without explicit era assignment).
  - [ ] 1.7 Implement `downgrade()` that drops `motif_eras`, `historical_events`, and `heritage_eras` tables in correct order.

- [ ] 2. Backend models (`models/timeline.rs`)
  Create DTOs for heritage eras, historical events, motif-era associations, and compare responses.
  - [ ] 2.1 Create `backend-rust/src/models/timeline.rs` with structs: `HeritageEra` (row DTO with all columns), `HeritageEraResponse` (API response), `HistoricalEvent` (row DTO with all columns), `HistoricalEventResponse` (API response with nested era, motif, urn), `TimelineEventsResponse` (events array + meta block with min_year, max_year, total_count), `MotifsByEraResponse` (era + motifs array), `CompareResponse` (motifs array + comparison_axes), `TimelineStatsResponse` (weekly_views + top_compared_pairs).
  - [ ] 2.2 Add request DTOs: `CreateEraRequest` (with validator derives for slug, name_vi, name_en, start_year, end_year, color_hex, sort_order), `CreateEventRequest` (with validator derives for era_id, slug, names, occurred_on, descriptions, optional motif_id/urn_id, importance).
  - [ ] 2.3 Add query param structs: `TimelineEventsQuery` (optional from: i32, optional to: i32), `MotifsByEraQuery` (era: String), `CompareQuery` (ids: String).
  - [ ] 2.4 Register the module in `backend-rust/src/models/mod.rs` by adding `pub mod timeline;`.

- [ ] 3. Backend services (`services/timeline_service.rs` and `services/compare_service.rs`)
  Implement business logic for timeline operations and motif comparison.
  - [ ] 3.1 Create `backend-rust/src/services/timeline_service.rs` with function `list_events(pool, from: Option<i32>, to: Option<i32>)` that queries `historical_events` joined with `heritage_eras`, optional `motifs`, optional `urns`, filtered by year range if provided, ordered by `occurred_on ASC`. Return `TimelineEventsResponse` with computed `meta` (min_year, max_year from actual data).
  - [ ] 3.2 Add function `list_motifs_by_era(pool, era_slug: &str)` that queries `motif_eras` joined with motifs and urns, filtered by era slug. Return 404 if era slug not found.
  - [ ] 3.3 Add function `create_era(pool, payload: CreateEraRequest)` that inserts into `heritage_eras` and returns the created row.
  - [ ] 3.4 Add function `create_event(pool, payload: CreateEventRequest)` that inserts into `historical_events` and returns the created row.
  - [ ] 3.5 Add function `get_timeline_stats(pool)` that aggregates from `analytics_events` to produce weekly view counts (event_name = 'timeline_viewed') and top-10 most-compared motif pairs (event_name = 'compare_opened').
  - [ ] 3.6 Create `backend-rust/src/services/compare_service.rs` with function `compare_motifs(pool, ids: Vec<Uuid>, user_id: Option<Uuid>)` that: validates exactly 2 IDs (return INVALID_COMPARE_PAIR error otherwise), fetches both motifs with lesson content and eras, checks content-rating gating via existing `lesson_service::get_motif_detail` logic, returns `CompareResponse` with `comparison_axes: ["category", "rarity", "era", "urn"]`.
  - [ ] 3.7 Register both modules in `backend-rust/src/services/mod.rs`.

- [ ] 4. Backend routes (`routes/timeline.rs` and `routes/compare.rs`)
  Implement Axum route handlers and wire them into the router.
  - [ ] 4.1 Create `backend-rust/src/routes/timeline.rs` with handler `get_timeline_events` (public, adds `Cache-Control: public, max-age=300` header), handler `get_timeline_motifs` (public, returns 400 if `era` query param missing), handler `post_heritage_era` (admin-only, returns 201), handler `post_historical_event` (admin-only, returns 201), handler `get_timeline_stats` (admin-only).
  - [ ] 4.2 Create `backend-rust/src/routes/compare.rs` with handler `get_compare_motifs` (authenticated, parses `ids` query param as comma-separated UUIDs).
  - [ ] 4.3 Register both modules in `backend-rust/src/routes/mod.rs`.
  - [ ] 4.4 Wire routes into the main router: `GET /api/v1/timeline/events`, `GET /api/v1/timeline/motifs`, `POST /api/v1/admin/heritage-eras`, `POST /api/v1/admin/historical-events`, `GET /api/v1/admin/timeline/stats`, `GET /api/v1/motifs/compare`.

- [ ] 5. Add `proptest` dev-dependency
  Pin `proptest` to exact version in Cargo.toml for property-based testing.
  - [ ] 5.1 Add `proptest = "=1.4.0"` to `[dev-dependencies]` in `backend-rust/Cargo.toml`.
  - [ ] 5.2 Verify the project compiles with `cargo check` in `backend-rust/`.

- [ ] 6. Property-based tests — Era and Event creation round-trips (Properties 1–2)
  Implement property tests for Properties 1 and 2 from the design document.
  - [ ] 6.1 Create test file `backend-rust/tests/timeline_properties.rs` with proptest configuration (minimum 100 cases). Write Property 1: for any valid era creation payload (valid slug pattern, name_vi, name_en, start_year ≤ end_year, valid color_hex matching `^#[0-9A-Fa-f]{6}$`, sort_order ≥ 0), the `create_era` function returns a result whose fields match the input. **Validates: Requirements 1.2**
  - [ ] 6.2 Write Property 2: for any valid event creation payload (valid era_id reference, slug, names, occurred_on date, descriptions, optional motif_id/urn_id, importance 1–5), the `create_event` function returns a result whose fields match the input. **Validates: Requirements 1.3**

- [ ] 7. Property-based tests — Timeline ordering and filtering (Properties 3–4)
  Implement property tests for Properties 3 and 4 from the design document.
  - [ ] 7.1 Write Property 3: for any set of historical events in the database, `list_events` returns events sorted by `occurred_on` ASC, and `meta.min_year` equals the earliest event year and `meta.max_year` equals the latest event year. **Validates: Requirements 2.1, 2.2**
  - [ ] 7.2 Write Property 4: for any year range [from, to] and any set of historical events, `list_events(from, to)` returns only events whose `occurred_on` year is within [from, to] inclusive, and does not omit any event in that range. **Validates: Requirements 2.3**

- [ ] 8. Property-based tests — Motif era filter and Compare endpoint (Properties 5–8)
  Implement property tests for Properties 5, 6, 7, and 8 from the design document.
  - [ ] 8.1 Write Property 5: for any era slug that exists in the database, `list_motifs_by_era(slug)` returns exactly the set of motifs tagged with that era in `motif_eras`, and no motifs not tagged with that era. **Validates: Requirements 3.2**
  - [ ] 8.2 Write Property 6: for any two valid, accessible motif IDs, `compare_motifs([A, B])` returns a response containing both motifs with lesson content, eras, and a non-empty `comparison_axes` array. **Validates: Requirements 4.1**
  - [ ] 8.3 Write Property 7: for any list of motif IDs where count ≠ 2 (0, 1, 3, 4, ...), `compare_motifs(ids)` returns error with code `INVALID_COMPARE_PAIR`. **Validates: Requirements 4.2**
  - [ ] 8.4 Write Property 8: for any motif with restricted content rating and any user without access to that rating, `compare_motifs` with that motif's ID returns HTTP 403. **Validates: Requirements 4.3**

- [ ] 9. Property-based test — Timeline stats aggregation (Property 9)
  Implement property test for Property 9 from the design document.
  - [ ] 9.1 Write Property 9: for any set of `analytics_events` with `event_name = 'timeline_viewed'` distributed across multiple weeks, `get_timeline_stats` returns `weekly_views` where each week's count equals the actual number of matching events in that ISO week, and `top_compared_pairs` is ordered by descending frequency with at most 10 entries. **Validates: Requirements 6.3**

- [ ] 10. Frontend — Timeline page and components
  Create the `/timeline` route with horizontal scrollable timeline, event panel, and compare modal.
  - [ ] 10.1 Create `frontend/src/app/timeline/page.jsx` as a server component that fetches initial timeline data from `GET /api/v1/timeline/events` and renders the timeline layout with era-colored background segments.
  - [ ] 10.2 Create `frontend/src/components/timeline/TimelineTrack.jsx` as a client component with horizontal scrollable track, era-colored segments, and event markers. Implement keyboard navigation (ArrowLeft/ArrowRight moves focus between markers) and ARIA roles (`role="listbox"` on track, `role="option"` on markers, `aria-label` with event name and date).
  - [ ] 10.3 Create `frontend/src/components/timeline/EventPanel.jsx` as a client component side panel that opens when a marker is clicked, showing event description (vi/en), linked motif thumbnail (if any), and linked urn name (if any). Include close button with `aria-label="Close panel"`.
  - [ ] 10.4 Create `frontend/src/components/timeline/CompareModal.jsx` as a client component modal for side-by-side motif comparison. Fetches from `GET /api/v1/motifs/compare?ids=A,B`. Displays comparison axes and motif details. Includes focus trap and Escape key to close.
  - [ ] 10.5 Add API functions in `frontend/src/lib/api.js`: `fetchTimelineEvents(from?, to?)`, `fetchTimelineMotifs(eraSlug)`, `compareMotifs(idA, idB)`. Include analytics event calls for `timeline_viewed` and `compare_opened`.

- [ ] 11. Frontend — Accessibility and WCAG 2.1 AA compliance
  Ensure the timeline page meets WCAG 2.1 AA requirements.
  - [ ] 11.1 Verify all interactive elements in TimelineTrack have visible focus indicators (minimum 3:1 contrast ratio against adjacent colors), keyboard operability (Enter/Space to activate markers), and screen-reader announcements.
  - [ ] 11.2 Ensure color contrast of era segments and text labels meets 4.5:1 ratio for normal text. Add `aria-live="polite"` region for dynamic content updates (panel open/close).
  - [ ] 11.3 Add skip-navigation link at the top of the timeline page to jump past the timeline track to main content.

## Task Dependency Graph

```json
{
  "waves": [
    [1],
    [2, 5],
    [3],
    [4, 6, 7, 8, 9],
    [10],
    [11]
  ]
}
```

## Notes

- All Rust dependencies must be pinned to exact versions (e.g., `"=1.4.0"`) per project convention.
- Migrations use Alembic (Python) — not Rust migration tools.
- The existing `AuthState` pattern (pool + settings) is reused for new route handlers.
- Property-based tests use `proptest` with minimum 100 iterations per property.
- Frontend uses the existing `lib/api.js` fetch pattern and Zustand stores.
- WCAG 2.1 AA compliance requires manual testing with assistive technologies for full validation.
