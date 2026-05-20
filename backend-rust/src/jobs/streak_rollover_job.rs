//! Nightly streak rollover job.
//!
//! Runs at 00:10 UTC. For users who did not record activity for the previous
//! UTC day, either consumes a streak freeze or captures the loss into
//! `user_streak_history` and resets `current_streak`.
//!
//! Spec: `.kiro/specs/streak-repair-economy/` (Requirement 7).

use chrono::{NaiveTime, TimeZone, Timelike, Utc};
use sqlx::PgPool;
use tokio::time::{interval_at, Duration, Instant, MissedTickBehavior};

use crate::services::streak_rollover_service;

/// Run the rollover loop forever. Called via `tokio::spawn` from `main`.
pub async fn run(pool: PgPool) {
    let target = NaiveTime::from_hms_opt(0, 10, 0).expect("valid time");
    let initial_delay = delay_until(target);

    let mut ticker = interval_at(Instant::now() + initial_delay, Duration::from_secs(86_400));
    ticker.set_missed_tick_behavior(MissedTickBehavior::Skip);

    loop {
        ticker.tick().await;
        tracing::info!(feature = "streak_rollover", "starting nightly pass");
        match streak_rollover_service::nightly_streak_rollover(&pool).await {
            Ok(stats) => {
                tracing::info!(
                    feature = "streak_rollover",
                    processed = stats.processed,
                    frozen = stats.frozen,
                    reset = stats.reset,
                    "nightly pass finished",
                );
            }
            Err(err) => {
                tracing::error!(
                    feature = "streak_rollover",
                    error = %err,
                    "nightly pass failed",
                );
            }
        }
    }
}

/// Compute the duration from now until the next occurrence of the given UTC
/// time.
fn delay_until(target: NaiveTime) -> Duration {
    let now = Utc::now();
    let today = now.date_naive();
    let candidate = Utc
        .from_utc_datetime(&today.and_time(target))
        .signed_duration_since(now);

    let secs = if candidate.num_seconds() <= 0 {
        candidate.num_seconds() + 86_400
    } else {
        candidate.num_seconds()
    };

    Duration::from_secs(secs as u64)
}

// silence unused-import lint when `Timelike` is only used transitively
#[allow(dead_code)]
fn _force_use(_: chrono::DateTime<Utc>) -> u32 {
    Utc::now().hour()
}
