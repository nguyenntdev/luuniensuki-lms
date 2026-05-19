# Requirements Document — FSRS Spaced Repetition

## Introduction

This feature replaces the existing legacy spaced-repetition algorithm (SM-2 family) in `services/spaced_repetition.py` with the modern **Free Spaced Repetition Scheduler (FSRS)** algorithm, implemented natively in Rust. FSRS uses the DSR model (Difficulty, Stability, Retrievability) and has been benchmarked on 700M+ reviews to achieve ~30% lower log-loss than SM-2 (rephrased from the FSRS Algorithm wiki at `github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm`).

The migration is gradual: 50% of users use FSRS, 50% keep SM-2, with primary metric being 7-day quiz retention. After 14 days of A/B running with statistically significant improvement (p < 0.05), ramp FSRS to 100%.

## Glossary

- **Card**: A reviewable item, currently represented in `quiz_questions` rows scheduled per-user via `user_quiz_review_state` (existing table).
- **Rating**: One of `Again | Hard | Good | Easy` — user feedback after attempting a card.
- **Stability (S)**: Memory stability in days; how long the card remains memorable.
- **Difficulty (D)**: Card difficulty on a 1–10 scale.
- **Retrievability (R)**: Probability the user recalls the card right now (0..1).
- **Optimal Retention**: Target R% the user wants to maintain (default 90%).
- **w0..w20**: 21 FSRS algorithm parameters tuned per user or per cohort.

## Requirements

### Requirement 1: FSRS scheduler in Rust

#### Acceptance Criteria

1. THE Rust_Service SHALL include a vendored or pinned `rs-fsrs = "=1.5.0"` (or equivalent) crate in `Cargo.toml`.
2. WHEN a user submits a quiz answer, THE Rust_Service SHALL compute the next review date using FSRS, persisting `fsrs_state`, `fsrs_difficulty`, `fsrs_stability`, `fsrs_due_date`, and `fsrs_last_review` in `user_quiz_review_state`.
3. THE Rust_Service SHALL map quiz outcomes to FSRS ratings: `score >= 0.9` → Good, `0.6..0.9` → Hard, `< 0.6` → Again, an explicit "easy" flag → Easy.
4. WHEN a user calls `GET /api/v1/reviews/due`, THE Rust_Service SHALL return all cards where `fsrs_due_date <= NOW()`, ordered by `fsrs_due_date ASC`, paginated.
5. WHEN a user calls `POST /api/v1/reviews/:card_id/rate` with body `{"rating": "Again|Hard|Good|Easy"}`, THE Rust_Service SHALL apply FSRS, update the review state, and return the new `fsrs_due_date`.

### Requirement 2: Per-user parameter optimization

#### Acceptance Criteria

1. THE Rust_Service SHALL store per-user FSRS parameters in `user_fsrs_params` table with columns `user_id`, `w0..w20` (numeric array), `optimal_retention` (numeric default 0.9), `last_optimized_at`, `review_count_at_last_optimize`.
2. WHEN a user accumulates ≥ 50 new reviews since `last_optimized_at`, THE Rust_Service SHALL queue an optimization job that retrains `w0..w20` from the user's review history.
3. IF a user has fewer than 50 total reviews, THE Rust_Service SHALL fall back to cohort-level default parameters cached in `fsrs_cohort_params`.
4. THE optimization job SHALL run as a background task using `tokio::spawn`, not block the request path, and complete within 60 seconds for users with up to 5000 reviews.

### Requirement 3: Optimal retention slider

#### Acceptance Criteria

1. WHEN a user calls `GET /api/v1/users/me/fsrs-settings`, THE Rust_Service SHALL return current `optimal_retention` and a recommended range (0.75 to 0.97).
2. WHEN a user calls `PUT /api/v1/users/me/fsrs-settings` with body `{"optimal_retention": 0.85}`, THE Rust_Service SHALL validate the value is in `[0.70, 0.97]` and update the row.
3. IF the value is out of range, THE Rust_Service SHALL respond with HTTP 400 and `{"error":{"code":"INVALID_RETENTION","message":"Optimal retention must be between 0.70 and 0.97","details":{}}}`.

### Requirement 4: A/B test cohort assignment

#### Acceptance Criteria

1. THE Rust_Service SHALL use the existing `Experiment` infrastructure to assign users to `fsrs_v1_treatment` or `fsrs_v1_control` cohorts based on a hash of user_id; assignment is sticky.
2. WHEN a user is in `fsrs_v1_control`, THE Rust_Service SHALL route quiz scheduling to the legacy SM-2 service (proxied to Python or kept native if SM-2 has been ported).
3. WHEN a user is in `fsrs_v1_treatment`, THE Rust_Service SHALL use FSRS for all quiz scheduling.
4. THE Rust_Service SHALL log every review event to `analytics_events` with `event_name = 'review_completed'` and a `cohort` field set to the assigned cohort.

### Requirement 5: One-time migration from SM-2 state

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL provide a one-time SQL migration that initializes FSRS state for every existing row in `user_quiz_review_state`: `fsrs_difficulty = 5.0` (mid-scale), `fsrs_stability` derived from existing `interval_days`, `fsrs_due_date` derived from existing `next_review_at`, `fsrs_state = 'review'`.
2. THE migration SHALL be reversible: a corresponding down-migration drops the new columns.
3. THE migration SHALL not modify any existing column, only add new ones (additive).

### Requirement 6: KPI tracking

#### Acceptance Criteria

1. THE Rust_Service SHALL expose `GET /api/v1/admin/fsrs/stats` returning per-cohort metrics: avg reviews/day, avg retention rate (computed from `correct/total` over last 30 days), and review time (avg `fsrs_due_date - fsrs_last_review`).
2. THE Rust_Service SHALL emit Prometheus counters `fsrs_reviews_total{cohort, rating}` and a histogram `fsrs_due_date_lag_seconds`.

### Requirement 7: Performance and resource constraints

#### Acceptance Criteria

1. THE FSRS computation per review SHALL complete in less than 5 ms p99 on the production host.
2. THE optimization job SHALL not exceed 200 MB peak RSS and SHALL be cancellable via SIGTERM.
3. THE Rust_Service SHALL not require any new external dependency beyond `rs-fsrs` and existing crates.
