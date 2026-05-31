# Implementation Plan: Streak Repair Economy

## Overview

This plan implements the remaining pieces of the streak repair economy feature. The migration (0042), models (`streak_economy.rs`), route handlers, and core service logic are already in place. What remains is:

1. **Streak rollover service** — capturing streak losses into `user_streak_history` and integrating with the existing `update_streak` logic.
2. **Background jobs** — nightly streak rollover (00:10 UTC) and friend streak maintenance (00:05 UTC).
3. **Phoenix badge awarding** — the actual award + comeback bonus creation (currently only eligibility is checked).
4. **XP multiplier** — applying the 2x comeback bonus during lesson completion.
5. **Prometheus counters** — exposing streak economy metrics in the existing `/metrics` endpoint.
6. **Tests** — unit tests, route-level tests, and property-based tests for core invariants.

All existing route handlers, services, and the Alembic migration are already landed and functional. This plan fills the gaps to make the feature production-ready.

## Tasks

- [x] 1. Streak rollover service and history capture
  - [x] 1.1 Create `backend-rust/src/services/streak_rollover_service.rs` with `capture_streak_loss_to_history` function
    - Accept `tx: &mut Transaction<'_, Postgres>`, `user_id: Uuid`, `streak_value: i32`, `streak_started_at: DateTime<Utc>`.
    - Insert a row into `user_streak_history` with the provided values and `streak_ended_at = NOW()`.
    - Return `sqlx::Result<()>`.
    - **Validates:** Requirement 7.1, 7.3

  - [x] 1.2 Register `streak_rollover_service` in `backend-rust/src/services/mod.rs`
    - Add `pub mod streak_rollover_service;` to the module declarations.
    - **Validates:** Requirement 7.1

  - [x] 1.3 Integrate history capture into `lesson_service.rs` `update_streak`
    - When `diff > 1` (streak would reset) and `streak_freezes = 0`, call `capture_streak_loss_to_history` before resetting the streak.
    - Query `streak_freezes` from the user row (already locked with `FOR UPDATE`).
    - If `streak_freezes > 0`, decrement freezes and preserve the streak instead of resetting.
    - **Validates:** Requirement 7.2, 7.3

  - [x] 1.4 Add per-user advisory lock to `update_streak` in `lesson_service.rs`
    - Add `SELECT pg_advisory_xact_lock(hashtextextended($1::text, 0))` at the start of the streak update to prevent concurrent double-increment or double-reset.
    - **Validates:** Requirement 7.4

- [x] 2. Nightly streak rollover background job
  - [x] 2.1 Create `backend-rust/src/jobs/mod.rs` with module declarations
    - Declare `pub mod streak_rollover_job;` and `pub mod friend_streak_job;`.
    - **Validates:** Requirement 7.1

  - [x] 2.2 Create `backend-rust/src/jobs/streak_rollover_job.rs`
    - Implement `pub async fn run(pool: PgPool)` that calculates the delay until 00:10 UTC, then loops with `tokio::time::interval` (24h period) and `MissedTickBehavior::Skip`.
    - **Validates:** Requirement 7.1

  - [x] 2.3 Implement `nightly_streak_rollover` logic inside the job
    - SELECT users with `current_streak > 0` and `(last_active_at IS NULL OR last_active_at::date < CURRENT_DATE - 1)` using `FOR UPDATE SKIP LOCKED`.
    - For each user: acquire advisory lock, check `streak_freezes`. If > 0, decrement and preserve. Otherwise, call `capture_streak_loss_to_history` and reset `current_streak = 0`.
    - Return a stats struct with counts of frozen/reset users.
    - **Validates:** Requirement 7.1, 7.2, 7.3, 7.4

  - [x] 2.4 Add `mod jobs;` to `backend-rust/src/main.rs` and spawn the rollover job
    - After the pool is created (and is `Some`), spawn with `tokio::spawn(jobs::streak_rollover_job::run(pool.clone()))`.
    - **Validates:** Requirement 7.1

  - [x] 2.5 Add structured logging with `feature = "streak_rollover"` for batch results
    - Log at `info` level: number of users processed, frozen, and reset.
    - **Validates:** Requirement 8.1

- [x] 3. Friend streak nightly job
  - [x] 3.1 Create `backend-rust/src/jobs/friend_streak_job.rs`
    - Implement `pub async fn run(pool: PgPool)` targeting 00:05 UTC with the same interval pattern.
    - **Validates:** Requirement 4.6

  - [x] 3.2 Implement friend streak reset logic
    - For all `friend_streaks` rows where `last_increment_date IS NOT NULL AND last_increment_date < CURRENT_DATE - 1`, set `current_count = 0` (preserve `longest_count`).
    - **Validates:** Requirement 4.3

  - [x] 3.3 Implement friend streak increment logic
    - Find all canonical pairs where both users have `last_active_at::date = CURRENT_DATE - 1` and a mutual friendship exists (both directions accepted in `friend_requests`).
    - Call `increment_for_pair` for each qualifying pair.
    - **Validates:** Requirement 4.2, 4.6

  - [x] 3.4 Spawn the friend streak job in `main.rs`
    - After the pool is created, spawn with `tokio::spawn(jobs::friend_streak_job::run(pool.clone()))`.
    - **Validates:** Requirement 4.6

  - [x] 3.5 Add structured logging with `feature = "friend_streak_increment"` for batch results
    - Log at `info` level: pairs reset, pairs incremented.
    - **Validates:** Requirement 8.1

- [x] 4. Phoenix badge awarding and comeback bonus
  - [x] 4.1 Add `award_phoenix_if_eligible` function to `streak_comeback_service.rs`
    - Check eligibility: find `user_streak_history` row with `streak_value >= 30` and `phoenix_awarded = false`.
    - Verify user has been active 3 consecutive days since that loss (using `current_streak >= 3` and `last_active_at > streak_ended_at`).
    - Insert into `user_badges` (the existing badges table join), set `phoenix_awarded = true` on the history row, insert `user_comeback_bonuses` with `multiplier = 2.0` and `expires_at = NOW() + 7 days`.
    - Emit structured log with `feature = "phoenix_award"`.
    - **Validates:** Requirement 5.2, 5.5

  - [x] 4.2 Integrate Phoenix check into streak update flow
    - After `update_streak` in `lesson_service.rs` increments the streak (not resets), call `award_phoenix_if_eligible` if `new_streak >= 3`.
    - This fires on every lesson completion where the streak grows, but the function is idempotent (guarded by `phoenix_awarded`).
    - **Validates:** Requirement 5.2

  - [x] 4.3 Implement XP multiplier application in lesson completion
    - In the XP-granting code path of `lesson_service.rs` (where `total_xp` is incremented), query `user_comeback_bonuses` for an active row (`expires_at > NOW()`).
    - If found, multiply the XP delta by the bonus multiplier before persisting.
    - **Validates:** Requirement 5.3

  - [x] 4.4 Ensure Phoenix badge is awarded at most once per history row
    - The `phoenix_awarded = false` guard in the SELECT ensures no double-award. Add a test verifying this invariant.
    - **Validates:** Requirement 5.5

- [x] 5. Prometheus counters for streak economy
  - [x] 5.1 Add four new `AtomicU64` counters in `backend-rust/src/routes/metrics.rs`
    - `STREAK_REPAIR_TOTAL`, `STREAK_BRB_TOTAL`, `FRIEND_STREAK_INCREMENT_TOTAL`, `PHOENIX_BADGE_TOTAL`.
    - **Validates:** Requirement 8.2

  - [x] 5.2 Extend the `metrics()` handler to output the new counters
    - Add Prometheus text exposition lines: `streak_repair_total`, `streak_brb_invocations_total`, `friend_streak_increments_total`, `phoenix_badges_awarded_total`.
    - **Validates:** Requirement 8.2

  - [x] 5.3 Increment counters in the respective service functions
    - `STREAK_REPAIR_TOTAL` in `streak_repair_service::repair` on success.
    - `STREAK_BRB_TOTAL` in `streak_admin_service::big_red_button` on success.
    - `FRIEND_STREAK_INCREMENT_TOTAL` in `streak_friend_service::increment_for_pair` on success.
    - `PHOENIX_BADGE_TOTAL` in `streak_comeback_service::award_phoenix_if_eligible` on success.
    - **Validates:** Requirement 8.2

  - [x] 5.4 Update the metrics test in `main.rs` to assert new counter names appear
    - Add assertions for `streak_repair_total`, `streak_brb_invocations_total`, `friend_streak_increments_total`, `phoenix_badges_awarded_total` in the existing `metrics_returns_prometheus_text_format` test.
    - **Validates:** Requirement 8.2

- [x] 6. Unit and route-level tests
  - [x] 6.1 Add route-level tests in `routes/streak_repair.rs`
    - Test: invalid payment method in body returns 400.
    - Test: missing JSON body returns 422 (deserialization failure).
    - **Validates:** Requirement 1.1, 1.2

  - [x] 6.2 Add unit tests in `streak_repair_service.rs`
    - Test `PaymentMethod::parse` for "hearts", "xp", and invalid strings.
    - Test `next_month_start` across year boundary (Dec 31 → Jan 1).
    - Test `next_month_start` for Feb → Mar.
    - **Validates:** Requirement 1.4

  - [x] 6.3 Add unit tests in `streak_rollover_service.rs`
    - Test that `capture_streak_loss_to_history` rejects `streak_value <= 0` with an error.
    - **Validates:** Requirement 7.3

  - [x] 6.4 Add route-level tests in `routes/streak_admin.rs`
    - Test: grant-insurance with learner token returns 403.
    - Test: BRB with invalid duration (0 or negative) returns 400.
    - **Validates:** Requirement 3.1, 6.5

- [x] 7. Property-based tests for core invariants
  - [x] 7.1 Add `proptest = "=1.5.0"` as a dev-dependency in `Cargo.toml`
    - Pin to exact version per project convention.
    - **Validates:** Design testing strategy

  - [x] 7.2 Write property test: canonical pair invariant
    - For any two distinct UUIDs `a` and `b`, `canonical_pair(a, b)` always returns `(min, max)` satisfying the CHECK constraint `user_a_id < user_b_id`.
    - Also verify `canonical_pair(a, b) == canonical_pair(b, a)` (commutativity).
    - **Validates: Requirements 4.1**

  - [x] 7.3 Write property test: PaymentMethod::parse correctness
    - For any arbitrary string, `parse` returns `Ok(Hearts)` iff input == "hearts", `Ok(Xp)` iff input == "xp", and `Err` otherwise.
    - **Validates: Requirements 1.1, 1.2**

  - [x] 7.4 Write property test: next_month_start always advances
    - For any `DateTime<Utc>`, `next_month_start(dt)` returns a timestamp strictly after `dt`, on day 1, at 00:00:00 UTC.
    - **Validates: Requirements 1.4**

## Task Dependency Graph

```json
{
  "waves": [
    ["1"],
    ["2", "4"],
    ["3", "5"],
    ["6"],
    ["7"]
  ]
}
```

## Notes

- Tasks 1–4 are the core logic tasks and must be completed in order since each builds on the previous.
- Task 5 (Prometheus) depends on Task 4 because it needs the Phoenix award path to exist.
- Tasks 6 and 7 (tests) can be started after the code they test is in place.
- The existing migration, models, routes, and service implementations are already landed — these tasks fill the remaining gaps (background jobs, streak history integration, Phoenix awarding, XP multiplier, observability, and tests).
- All new dependencies must be pinned to exact versions per project convention (Requirement 11.4).
