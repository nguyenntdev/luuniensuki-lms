//! Trail pace reminder dispatcher.
//!
//! Polls `user_trail_progress.next_reminder_at` every 60 seconds. For each
//! row whose reminder time has passed and whose user has streak reminders
//! enabled, inserts a `push_notifications` row with
//! `notification_type = 'trail_pace_reminder'` and advances `next_reminder_at`
//! by the row's pace cadence.
//!
//! Idempotency: only one reminder is queued per (user, trail, scheduled_at)
//! tuple — `next_reminder_at` is advanced atomically inside the same query
//! that selects the row, so a re-run of the loop will not double-queue.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/` (Requirement 4).

use chrono::{Duration, Utc};
use serde_json::json;
use sqlx::PgPool;
use tokio::time::{self, MissedTickBehavior};
use uuid::Uuid;

const POLL_INTERVAL_SECONDS: u64 = 60;

pub async fn run(pool: PgPool) {
    let mut ticker = time::interval(time::Duration::from_secs(POLL_INTERVAL_SECONDS));
    ticker.set_missed_tick_behavior(MissedTickBehavior::Skip);

    loop {
        ticker.tick().await;
        match dispatch_pass(&pool).await {
            Ok(n) if n > 0 => {
                tracing::info!(
                    feature = "trail_pace_reminder",
                    reminders_queued = n,
                    "trail reminder pass"
                );
            }
            Ok(_) => {}
            Err(err) => {
                tracing::warn!(
                    feature = "trail_pace_reminder",
                    error = %err,
                    "trail reminder pass failed"
                );
            }
        }
    }
}

async fn dispatch_pass(pool: &PgPool) -> Result<i64, sqlx::Error> {
    let mut tx = pool.begin().await?;

    // Pull rows where the reminder is due, the trail is not completed, and
    // the user opted in to streak reminders. We grab pace + slug + title so
    // the inserted notification has useful copy.
    //
    // notification_settings table is joined defensively — if a user has no
    // row, default-allow streak reminders.
    //
    // We also skip users who have been active within the cadence window —
    // they don't need a reminder, and queueing one would be noise. The
    // cadence is encoded inline as an INTERVAL chosen by pace.
    let due: Vec<(
        Uuid,   // user_id
        Uuid,   // trail_id
        String, // pace
        String, // slug
        String, // title_vi
    )> = sqlx::query_as(
        r#"
        SELECT p.user_id, p.trail_id, COALESCE(p.pace, 'daily'), t.slug, t.title_vi
        FROM user_trail_progress p
        JOIN trails t ON t.id = p.trail_id
        JOIN users u ON u.id = p.user_id
        LEFT JOIN notification_settings ns ON ns.user_id = p.user_id
        WHERE p.completed_at IS NULL
          AND p.next_reminder_at IS NOT NULL
          AND p.next_reminder_at <= NOW()
          AND COALESCE(ns.streak_reminders, true) = true
          AND (
            u.last_active_at IS NULL
            OR u.last_active_at < NOW() - CASE COALESCE(p.pace, 'daily')
                 WHEN 'weekly'  THEN INTERVAL '6 days'
                 WHEN '2x_week' THEN INTERVAL '3 days'
                 ELSE                INTERVAL '20 hours'
               END
          )
        FOR UPDATE OF p SKIP LOCKED
        LIMIT 100
        "#,
    )
    .fetch_all(&mut *tx)
    .await?;

    if due.is_empty() {
        return Ok(0);
    }

    let mut queued: i64 = 0;
    for (user_id, trail_id, pace, slug, title_vi) in due {
        let next = match pace.as_str() {
            "weekly" => Utc::now() + Duration::hours(168),
            "2x_week" => Utc::now() + Duration::hours(84),
            _ => Utc::now() + Duration::hours(24),
        };

        // Insert notification.
        sqlx::query(
            r#"
            INSERT INTO push_notifications
                (id, user_id, title, body, notification_type, data_payload, status, scheduled_for, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3, 'trail_pace_reminder', $4::jsonb, 'pending', NOW(), NOW())
            "#,
        )
        .bind(user_id)
        .bind(format!("Tiếp tục lộ trình «{}»", title_vi))
        .bind("Hôm nay là ngày học tiếp theo của bạn — bước tiếp theo đang chờ.")
        .bind(json!({"trail_slug": slug}).to_string())
        .execute(&mut *tx)
        .await?;

        // Advance the reminder cursor.
        sqlx::query(
            "UPDATE user_trail_progress SET next_reminder_at = $3 \
             WHERE user_id = $1 AND trail_id = $2",
        )
        .bind(user_id)
        .bind(trail_id)
        .bind(next)
        .execute(&mut *tx)
        .await?;

        queued += 1;
    }

    tx.commit().await?;

    Ok(queued)
}
