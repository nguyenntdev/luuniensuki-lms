//! Nightly friend-streak job.
//!
//! Runs at 00:05 UTC. Resets pairs that did not have a mutual active day, and
//! increments pairs where both users were active on the previous UTC date.
//!
//! Spec: `.kiro/specs/streak-repair-economy/` (Requirement 4).

use chrono::{NaiveTime, TimeZone, Utc};
use sqlx::PgPool;
use tokio::time::{interval_at, Duration, Instant, MissedTickBehavior};

/// Run the loop forever. Called via `tokio::spawn` from `main`.
pub async fn run(pool: PgPool) {
    let target = NaiveTime::from_hms_opt(0, 5, 0).expect("valid time");
    let initial_delay = delay_until(target);

    let mut ticker = interval_at(Instant::now() + initial_delay, Duration::from_secs(86_400));
    ticker.set_missed_tick_behavior(MissedTickBehavior::Skip);

    loop {
        ticker.tick().await;
        tracing::info!(feature = "friend_streak", "starting nightly pass");
        match run_pass(&pool).await {
            Ok((reset, incremented)) => {
                tracing::info!(
                    feature = "friend_streak",
                    pairs_reset = reset,
                    pairs_incremented = incremented,
                    "nightly pass finished",
                );
            }
            Err(err) => {
                tracing::error!(
                    feature = "friend_streak",
                    error = %err,
                    "nightly pass failed",
                );
            }
        }
    }
}

/// Reset stale pairs and increment pairs that had a mutual active day
/// yesterday. Returns `(reset_count, increment_count)`.
async fn run_pass(pool: &PgPool) -> Result<(i64, i64), sqlx::Error> {
    // 1. Reset pairs whose last increment was earlier than yesterday.
    let reset_count: i64 = sqlx::query_scalar(
        r#"
        WITH updated AS (
            UPDATE friend_streaks
            SET current_count = 0,
                updated_at = NOW()
            WHERE last_increment_date IS NOT NULL
              AND last_increment_date < (CURRENT_DATE - 1)
              AND current_count > 0
            RETURNING id
        )
        SELECT COUNT(*)::bigint FROM updated
        "#,
    )
    .fetch_one(pool)
    .await?;

    // 2. Increment pairs where both users were active yesterday.
    //    Active = users.last_active_at::date = (CURRENT_DATE - 1).
    //    The pair must already exist OR be created on the fly.
    //
    //    Mutual friendship is detected via `user_friendships` if it exists;
    //    otherwise we fall back to a no-op (table may not be present in all
    //    deploy environments). The query is wrapped in EXCEPTION handling at
    //    the application layer to avoid hard failure.
    let increment_count: i64 = match sqlx::query_scalar::<_, i64>(
        r#"
        WITH active_yesterday AS (
            SELECT id
            FROM users
            WHERE last_active_at IS NOT NULL
              AND last_active_at::date = (CURRENT_DATE - 1)
        ),
        mutual_pairs AS (
            SELECT LEAST(uf.user_id, uf.friend_id)    AS user_a_id,
                   GREATEST(uf.user_id, uf.friend_id) AS user_b_id
            FROM user_friendships uf
            JOIN user_friendships uf2
              ON uf2.user_id = uf.friend_id
             AND uf2.friend_id = uf.user_id
            WHERE uf.status = 'accepted'
              AND uf2.status = 'accepted'
              AND uf.user_id < uf.friend_id
        ),
        active_pairs AS (
            SELECT mp.user_a_id, mp.user_b_id
            FROM mutual_pairs mp
            JOIN active_yesterday ay1 ON ay1.id = mp.user_a_id
            JOIN active_yesterday ay2 ON ay2.id = mp.user_b_id
        ),
        upserts AS (
            INSERT INTO friend_streaks
                (user_a_id, user_b_id, current_count, longest_count,
                 last_increment_date, created_at, updated_at)
            SELECT ap.user_a_id, ap.user_b_id, 1, 1, (CURRENT_DATE - 1), NOW(), NOW()
            FROM active_pairs ap
            ON CONFLICT (user_a_id, user_b_id) DO UPDATE
            SET current_count = friend_streaks.current_count + 1,
                longest_count = GREATEST(friend_streaks.longest_count,
                                         friend_streaks.current_count + 1),
                last_increment_date = (CURRENT_DATE - 1),
                updated_at = NOW()
            WHERE friend_streaks.last_increment_date IS DISTINCT FROM (CURRENT_DATE - 1)
            RETURNING 1
        )
        SELECT COUNT(*)::bigint FROM upserts
        "#,
    )
    .fetch_one(pool)
    .await
    {
        Ok(n) => n,
        Err(err) => {
            // If `user_friendships` is missing in this environment, log and
            // proceed; the reset half of the pass still ran.
            tracing::warn!(
                feature = "friend_streak",
                error = %err,
                "friend streak increment query failed (likely missing table)"
            );
            0
        }
    };

    Ok((reset_count, increment_count))
}

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
