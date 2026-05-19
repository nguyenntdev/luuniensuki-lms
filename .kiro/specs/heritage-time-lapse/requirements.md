# Requirements Document — Heritage Time-Lapse

## Introduction

This feature adds a temporal dimension to the existing heritage content. Currently, the 9 Cửu Đỉnh urns and their motifs are presented spatially (3D viewer) without explicit historical context. This feature introduces a **timeline view** spanning 1802 (Gia Long) through 1945 (Bảo Đại) with the casting of the 9 dingsi in 1835–1837 as anchor events, an **era filter** for motifs, a **compare panel** for side-by-side analysis of two motifs, and **historical events overlay**.

Research evidence (rephrased): MDPI Heritage 2025 (`mdpi.com/2571-9408/8/7/280`) reports that timeline + contextual narrative increase comprehension scores in digital heritage education compared to spatial-only views.

## Glossary

- **Era**: A named historical period (e.g., "Đầu Nguyễn", "Pháp thuộc", "Hiện đại"). Stored in `heritage_eras` table.
- **Historical Event**: A dated milestone (e.g., "Đúc Cửu Đỉnh hoàn thành — 1837") with optional `motif_id`/`urn_id` reference. Stored in `historical_events` table.
- **Motif Era Tag**: A many-to-many link between motifs and eras via `motif_eras`.
- **Compare Pair**: An ad-hoc client-requested pair of motif IDs for side-by-side rendering.

## Requirements

### Requirement 1: Heritage eras and historical events

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL create tables `heritage_eras (id, slug, name_vi, name_en, start_year, end_year, color_hex, sort_order)` and `historical_events (id, era_id, slug, name_vi, name_en, occurred_on (date), description_vi, description_en, motif_id nullable, urn_id nullable, importance int default 1)`.
2. WHEN an admin calls `POST /api/v1/admin/heritage-eras`, THE Rust_Service SHALL create a new era with the supplied fields and return HTTP 201.
3. WHEN an admin calls `POST /api/v1/admin/historical-events`, THE Rust_Service SHALL create a new event linked to an era (and optionally a motif/urn) and return HTTP 201.
4. THE seed migration SHALL insert at least the following eras: `gia-long-minh-mang` (1802–1841), `thieu-tri-tu-duc` (1841–1883), `phap-thuoc-bao-dai` (1883–1945) and at least 12 historical events covering the casting of the 9 dingsi.

### Requirement 2: Public timeline endpoint

#### Acceptance Criteria

1. WHEN any user calls `GET /api/v1/timeline/events`, THE Rust_Service SHALL return all historical events ordered by `occurred_on ASC` with their associated era, motif (if any), urn (if any).
2. THE response SHALL include a `meta` block with `min_year` and `max_year` to support frontend zooming.
3. WHEN the user supplies query params `from=1830&to=1840`, THE Rust_Service SHALL filter events to that year range.
4. THE endpoint SHALL be cached at the HTTP layer with `Cache-Control: public, max-age=300`.

### Requirement 3: Motif filtering by era

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL create a `motif_eras` (motif_id, era_id) many-to-many table with primary key on the pair.
2. WHEN any user calls `GET /api/v1/timeline/motifs?era=<slug>`, THE Rust_Service SHALL return all motifs tagged with that era, joined with their urn metadata.
3. WHEN no era query param is supplied, THE endpoint SHALL return an HTTP 400 error.
4. The seed migration SHALL backfill `motif_eras` so that every existing motif is linked to at least one era.

### Requirement 4: Side-by-side compare endpoint

#### Acceptance Criteria

1. WHEN a user calls `GET /api/v1/motifs/compare?ids=<uuid>,<uuid>` with exactly two motif IDs, THE Rust_Service SHALL return a single object containing both motifs with full lesson content, eras, and shared `comparison_axes` (a curated list of categorical fields like `category`, `rarity`, `era`).
2. IF more than 2 IDs are supplied, THE Rust_Service SHALL respond with HTTP 400 and `{"error":{"code":"INVALID_COMPARE_PAIR","message":"Exactly 2 motif IDs are required"}}`.
3. THE endpoint SHALL respect content-rating gating from the existing `lesson_service::get_motif_detail` logic.

### Requirement 5: Frontend timeline route

#### Acceptance Criteria

1. The Next.js frontend SHALL render `/timeline` with a horizontal scrollable timeline where each historical event is a clickable marker.
2. Clicking a marker SHALL open a side panel with the event's description and any linked motif/urn.
3. The page SHALL be accessible (WCAG 2.1 AA): keyboard arrow keys move focus along markers, screen-reader labels announce each event.

### Requirement 6: KPI tracking

#### Acceptance Criteria

1. THE Rust_Service SHALL log timeline page views to `analytics_events` with `event_name = 'timeline_viewed'`.
2. THE Rust_Service SHALL log compare-modal opens to `analytics_events` with `event_name = 'compare_opened'` and `payload = {"motif_ids": [...]}`.
3. WHEN an admin calls `GET /api/v1/admin/timeline/stats`, THE Rust_Service SHALL return weekly view counts and the top-10 most-compared motif pairs.
