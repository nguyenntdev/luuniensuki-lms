# Implementation Plan: FSRS Spaced Repetition

## Overview

This plan implements the FSRS (Free Spaced Repetition Scheduler) feature for the Rust backend. It covers database migration, the `fsrs` crate integration, cohort assignment, core scheduling service, per-user optimization, new API endpoints, Prometheus metrics, and property-based tests. Tasks are ordered by dependency: schema first, then models, then services, then routes, then integration.

## Tasks

- [ ] 1. Database migration — FSRS schema
  Create Alembic migration `migrations/versions/0043_fsrs_spaced_repetition.py` that:
  - Adds columns to `user_quiz_review_state`: `fsrs_state TEXT DEFAULT 'new'`, `fsrs_difficulty DOUBLE PRECISION`, `fsrs_stability DOUBLE PRECISION`, `fsrs_due_date TIMESTAMP WITH TIME ZONE`, `fsrs_last_review TIMESTAMP WITH TIME ZONE`
  - Creates `user_fsrs_params` table with columns: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `user_id UUID NOT NULL UNIQUE REFERENCES users(id)`, `parameters DOUBLE PRECISION[] NOT NULL DEFAULT '{}'`, `optimal_retention DOUBLE PRECISION NOT NULL DEFAULT 0.9`, `last_optimized_at TIMESTAMP WITH TIME ZONE`, `review_count_at_last_optimize INTEGER NOT NULL DEFAULT 0`, `created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`, `updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`
  - Creates index `idx_user_fsrs_params_user_id` on `user_fsrs_params(user_id)`
  - Creates `fsrs_cohort_params` table with columns: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `cohort_name TEXT NOT NULL UNIQUE DEFAULT 'default'`, `parameters DOUBLE PRECISION[] NOT NULL`, `optimal_retention DOUBLE PRECISION NOT NULL DEFAULT 0.9`, `updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`
  - Seeds `fsrs_cohort_params` with FSRS default parameters `[0.4072,1.1829,3.1262,15.4722,7.2102,0.5316,1.0651,0.0589,1.5747,0.1070,1.0070,1.9523,0.1110,0.3255,2.2698,0.2315,2.9898,0.5163,0.6136,0.0000,0.0000]`
  - Backfills existing rows: `fsrs_difficulty = 5.0`, `fsrs_stability = COALESCE(interval_days, 1.0)`, `fsrs_due_date = COALESCE(next_review_at, NOW())`, `fsrs_state = 'review'`
  - Down migration drops the new columns and tables (reversible)
  **Requirements:** 5.1, 5.2, 5.3

- [ ] 2. Add `fsrs` and `proptest` crate dependencies
  - [ ] 2.1 Add `fsrs = "=5.2.0"` to `[dependencies]` in `backend-rust/Cargo.toml`
  - [ ] 2.2 Add `proptest = "=1.5.0"` to `[dev-dependencies]` in `backend-rust/Cargo.toml`
  - [ ] 2.3 Run `cargo check` in `backend-rust/` to verify dependencies resolve
  **Requirements:** 1.1, 7.3

- [ ] 3. FSRS domain models
  Create `backend-rust/src/models/fsrs.rs` with all FSRS domain types:
  - [ ] 3.1 Define `FsrsRating` enum (Again, Hard, Good, Easy) with Serialize/Deserialize (snake_case)
  - [ ] 3.2 Define `CardState` enum (New, Learning, Review, Relearning) with Serialize/Deserialize (snake_case)
  - [ ] 3.3 Define `ReviewStateRow` struct (sqlx::FromRow): id, user_id, question_id, fsrs_state, fsrs_difficulty, fsrs_stability, fsrs_due_date, fsrs_last_review, interval_days, next_review_at
  - [ ] 3.4 Define `UserFsrsParamsRow` struct (sqlx::FromRow): id, user_id, parameters, optimal_retention, last_optimized_at, review_count_at_last_optimize
  - [ ] 3.5 Define request/response DTOs: DueCardOut, DueReviewsQuery, DueReviewsResponse, RateCardRequest, RateCardResponse, FsrsSettingsResponse, UpdateFsrsSettingsRequest, FsrsStatsResponse, CohortStats
  - [ ] 3.6 Add `pub mod fsrs;` to `backend-rust/src/models/mod.rs`
  - [ ] 3.7 Run `cargo check` to verify models compile
  **Requirements:** 1.2, 1.4, 1.5, 3.1, 6.1

- [ ] 4. Cohort assignment service
  Create `backend-rust/src/services/cohort_service.rs` with deterministic hash-based cohort assignment:
  - [ ] 4.1 Implement `Cohort` enum (Treatment, Control) with Display/FromStr
  - [ ] 4.2 Implement `assign_cohort(user_id: &Uuid) -> Cohort` using SHA-256 of `"fsrs_v1_" + user_id.as_bytes()`, first byte < 128 → Treatment, else Control
  - [ ] 4.3 Implement `cohort_name(cohort: &Cohort) -> &'static str` returning `"fsrs_v1_treatment"` or `"fsrs_v1_control"`
  - [ ] 4.4 Add `pub mod cohort_service;` to `backend-rust/src/services/mod.rs`
  - [ ] 4.5 Write unit tests verifying determinism (same UUID → same cohort) and a known regression case
  - [ ] 4.6 Write property-based test (proptest) verifying Property 6: cohort assignment determinism and approximate 50/50 distribution
  **Requirements:** 4.1

- [ ] 5. FSRS scheduling service — core logic
  Create `backend-rust/src/services/fsrs_service.rs`:
  - [ ] 5.1 Implement `map_score_to_rating(score: f64, easy_flag: bool) -> FsrsRating` with threshold logic: easy_flag → Easy, score >= 0.9 → Good, 0.6 <= score < 0.9 → Hard, score < 0.6 → Again
  - [ ] 5.2 Implement `rate_card(pool: &PgPool, user_id: Uuid, card_id: Uuid, rating: FsrsRating) -> Result<RateCardResponse, AppError>` — fetches state, checks ownership, loads params (personal or cohort fallback), applies FSRS, updates DB, logs analytics event
  - [ ] 5.3 Implement `get_due_cards(pool: &PgPool, user_id: Uuid, page: u32, page_size: u32) -> Result<DueReviewsResponse, AppError>` — queries cards where fsrs_due_date <= NOW(), orders ASC, paginates
  - [ ] 5.4 Add `pub mod fsrs_service;` to `backend-rust/src/services/mod.rs`
  - [ ] 5.5 Write unit tests for `map_score_to_rating` (score=0.95→Good, 0.75→Hard, 0.3→Again, easy_flag=true→Easy)
  - [ ] 5.6 Write property-based test (proptest) verifying Property 2: score-to-rating mapping consistency with thresholds
  **Requirements:** 1.2, 1.3, 1.4, 1.5, 2.3

- [ ] 6. Property-based test — FSRS scheduling validity (Property 1)
  - [ ] 6.1 Write property-based test (proptest) verifying Property 1: for any valid card state with difficulty in [1.0, 10.0] and stability > 0, and for any rating, applying FSRS scheduling produces output where difficulty is in [1.0, 10.0], stability > 0, due_date > last_review, and state is valid
  **Requirements:** 1.2

- [ ] 7. Optimizer service — background parameter optimization
  Create `backend-rust/src/services/optimizer_service.rs`:
  - [ ] 7.1 Implement `should_use_personal_params(total_reviews: i64, has_params: bool) -> bool` returning true only if total_reviews >= 50 and params exist
  - [ ] 7.2 Implement `maybe_trigger_optimization(pool: &PgPool, user_id: Uuid)` — checks if user has ≥ 50 new reviews since last_optimized_at, spawns optimization via tokio::spawn
  - [ ] 7.3 Implement `run_optimization(pool: &PgPool, user_id: Uuid) -> Result<(), AppError>` — fetches review history, retrains w0..w20 via fsrs crate optimizer, updates user_fsrs_params, logs errors via tracing::error!
  - [ ] 7.4 Add `pub mod optimizer_service;` to `backend-rust/src/services/mod.rs`
  - [ ] 7.5 Write unit tests for `should_use_personal_params` (49/true→false, 50/true→true, 50/false→false)
  - [ ] 7.6 Write property-based test (proptest) verifying Property 4: parameter source threshold — personal params used iff total_reviews >= 50 AND params exist
  **Requirements:** 2.1, 2.2, 2.3, 2.4

- [ ] 8. Review route handlers
  Create `backend-rust/src/routes/reviews.rs` and mount routes:
  - [ ] 8.1 Implement `get_due_reviews` handler for GET /api/v1/reviews/due — authenticated, validates pagination (page_size max 100), calls fsrs_service::get_due_cards
  - [ ] 8.2 Implement `rate_card` handler for POST /api/v1/reviews/:card_id/rate — authenticated, validates rating, checks cohort (control → proxy to legacy, treatment → FSRS), calls fsrs_service::rate_card, triggers maybe_trigger_optimization, increments Prometheus counter
  - [ ] 8.3 Add `pub mod reviews;` to `backend-rust/src/routes/mod.rs`
  - [ ] 8.4 Mount review routes in `build_router` in `src/main.rs` with auth_state
  **Requirements:** 1.4, 1.5, 4.2, 4.3

- [ ] 9. FSRS settings endpoints
  Add optimal retention settings to users route:
  - [ ] 9.1 Add `get_fsrs_settings` handler to `backend-rust/src/routes/users.rs` for GET /api/v1/users/me/fsrs-settings — returns optimal_retention, recommended_range [0.75, 0.97], last_optimized_at, review_count, using_personal_params
  - [ ] 9.2 Add `update_fsrs_settings` handler to `backend-rust/src/routes/users.rs` for PUT /api/v1/users/me/fsrs-settings — validates optimal_retention in [0.70, 0.97], returns INVALID_RETENTION (400) if out of range, upserts user_fsrs_params
  - [ ] 9.3 Mount FSRS settings routes in `build_router` in `src/main.rs`
  - [ ] 9.4 Write unit tests for retention validation boundary (0.70→accept, 0.97→accept, 0.69→reject, 0.98→reject)
  - [ ] 9.5 Write property-based test (proptest) verifying Property 5: optimal retention validation — accepts iff value in [0.70, 0.97]
  **Requirements:** 3.1, 3.2, 3.3

- [ ] 10. Admin FSRS stats endpoint
  Add KPI endpoint to admin route:
  - [ ] 10.1 Add `get_fsrs_stats` handler to `backend-rust/src/routes/admin.rs` for GET /api/v1/admin/fsrs/stats — requires admin role, aggregates per-cohort metrics (user_count, avg_reviews_per_day, retention_rate_30d, avg_interval_days)
  - [ ] 10.2 Mount admin FSRS stats route in `build_router` in `src/main.rs`
  - [ ] 10.3 Write property-based test (proptest) verifying Property 7: stats aggregation correctness — for generated review event sets, verify computed retention rate matches expected
  **Requirements:** 6.1

- [ ] 11. Prometheus metrics for FSRS
  Extend metrics module with FSRS-specific counters:
  - [ ] 11.1 Add to `backend-rust/src/routes/metrics.rs`: FSRS_REVIEWS_TOTAL counters (2 cohorts × 4 ratings = 8 AtomicU64), FSRS_DUE_DATE_LAG_SUM and FSRS_DUE_DATE_LAG_COUNT atomics, helper functions `increment_fsrs_review(cohort, rating)` and `observe_due_date_lag(lag_seconds)`
  - [ ] 11.2 Extend the `metrics()` handler to output `fsrs_reviews_total{cohort,rating}` and `fsrs_due_date_lag_seconds` histogram lines
  - [ ] 11.3 Wire `increment_fsrs_review` call in the rate_card handler after successful rating
  **Requirements:** 6.2

- [ ] 12. Property-based test — Due cards ordering (Property 3)
  - [ ] 12.1 Write property-based test (proptest) verifying Property 3: for any generated set of (Uuid, DateTime) pairs, applying due-cards filter (due_date <= now) and sort (ascending) produces only past-due cards in correct order
  **Requirements:** 1.4

- [ ] 13. Analytics event logging
  Ensure review events are logged with cohort information:
  - [ ] 13.1 In `fsrs_service::rate_card`, insert into `analytics_events` with event_name='review_completed', user_id, and properties JSON containing card_id, rating, cohort, fsrs_stability, fsrs_difficulty, fsrs_due_date
  - [ ] 13.2 Verify the analytics insert is within the same transaction as the state update (atomic)
  **Requirements:** 4.4

- [ ] 14. Integration wiring and final verification
  - [ ] 14.1 Verify all module declarations are in place (models/mod.rs, services/mod.rs, routes/mod.rs)
  - [ ] 14.2 Verify all routes are mounted in `build_router` with correct HTTP methods and paths
  - [ ] 14.3 Run `cargo build` in `backend-rust/` to verify full compilation
  - [ ] 14.4 Run `cargo test` in `backend-rust/` to verify all unit and property tests pass
  **Requirements:** 1.1, 7.1, 7.3

## Task Dependency Graph

```json
{
  "waves": [
    ["1", "2"],
    ["3"],
    ["4", "11"],
    ["5"],
    ["6", "7", "10", "12"],
    ["8", "9", "13"],
    ["14"]
  ]
}
```

## Notes

- The migration (Task 1) is independent of Rust code and can be applied to the database at any time.
- Tasks 2-3 must be completed before any service or route tasks.
- Property-based tests (Tasks 4.6, 5.6, 6.1, 7.6, 9.5, 10.3, 12.1) use `proptest = "=1.5.0"` with minimum 100 iterations each.
- The `fsrs` crate (v5.2.0) is the actively maintained Rust implementation by the open-spaced-repetition org (published as `fsrs` on crates.io, not `rs-fsrs`).
- All new endpoints require JWT authentication via the existing `AuthState` pattern.
- Error responses use the existing `AppError::Domain` variant for domain-specific errors.
- The optimization job (Task 7) runs via `tokio::spawn` and must not block request handling.
- Prometheus metrics use the existing atomic counter pattern (no external metrics crate).
