//! Admin operations for the streak repair economy.
//!
//! - Big Red Button (BRB): rate-limited to 5/24h per actor; freezes streaks
//!   for affected users and writes one `streak_protection_events` row per user.
//! - Manual repair grant (`payment_method = 'admin_grant'`).
//! - Manual insurance grant (creates an `active` `streak_insurance_subscriptions`
//!   row).
//! - Repair-event audit listing.
//! - BRB event listing.
//! - Aggregate stats (KPI buckets).
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use axum::http::StatusCode;
use chrono::{DateTime, Duration, Utc};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::streak_economy::{
    BrbEventSummary, BrbEventsResponse, BrbResponse, GrantInsuranceRequest,
    KpiBuckets, RepairEventsQuery, RepairEventsResponse, StreakEconomyStats,
    StreakInsuranceRow, StreakRepairEventRow,
};

const BRB_RATE_LIMIT_PER_24H: i64 = 5;

// ---------------------------------------------------------------------------
// Big Red Button
// ---------------------------------------------------------------------------

pub async fn big_red_button(
    pool: &PgPool,
    actor_user_id: Uuid,
    reason: &str,
    duration_minutes: i32,
    effective_from: DateTime<Utc>,
) -> Result<BrbResponse, AppError> {
    if duration_minutes <= 0 {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_DURATION".to_string(),
            message: "duration_minutes must be > 0".to_string(),
            details: json!({"received": duration_minutes}),
        });
    }

    // 1. Rate limit: count BRB events from this actor in the last 24h.
    //    Each press inserts many rows but they share `event_id`, so we count
    //    distinct event_ids.
    let recent: i64 = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(DISTINCT event_id)::bigint
        FROM streak_protection_events
        WHERE actor_user_id = $1
          AND created_at > NOW() - INTERVAL '24 hours'
        "#,
    )
    .bind(actor_user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if recent >= BRB_RATE_LIMIT_PER_24H {
        return Err(AppError::Domain {
            status: StatusCode::TOO_MANY_REQUESTS,
            code: "BRB_RATE_LIMIT".to_string(),
            message:
                "Big Red Button has been pressed 5 times in the last 24 hours; further presses require database-level approval"
                    .to_string(),
            details: json!({}),
        });
    }

    let event_id = Uuid::new_v4();
    let effective_to = effective_from + Duration::minutes(duration_minutes as i64);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Insert one protection-event row per user with current_streak > 0 whose
    // last activity is close to the affected window.
    let inserted: i64 = sqlx::query_scalar::<_, i64>(
        r#"
        WITH affected AS (
            SELECT id AS user_id
            FROM users
            WHERE current_streak > 0
              AND last_active_at IS NOT NULL
              AND last_active_at >= $5 - INTERVAL '24 hours'
              AND last_active_at <= $6
        ),
        ins AS (
            INSERT INTO streak_protection_events
                (event_id, user_id, actor_user_id, reason,
                 effective_from, effective_to)
            SELECT $1, user_id, $2, $3, $5, $6
            FROM affected
            RETURNING user_id
        ),
        bumped AS (
            UPDATE users SET streak_freezes = streak_freezes + 1
            WHERE id IN (SELECT user_id FROM ins)
            RETURNING id
        )
        SELECT COUNT(*)::bigint FROM bumped
        "#,
    )
    .bind(event_id)
    .bind(actor_user_id)
    .bind(reason)
    .bind(duration_minutes)
    .bind(effective_from)
    .bind(effective_to)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "brb",
        actor_user_id = %actor_user_id,
        reason = %reason,
        duration_minutes = duration_minutes,
        affected_users = inserted,
        event_id = %event_id,
        "big red button pressed"
    );

    Ok(BrbResponse {
        affected_users: inserted,
        event_id,
    })
}

// ---------------------------------------------------------------------------
// Admin grant repair
// ---------------------------------------------------------------------------

pub async fn grant_repair(
    pool: &PgPool,
    target_user_id: Uuid,
    actor_user_id: Uuid,
    reason: &str,
) -> Result<StreakRepairEventRow, AppError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Per-user lock to align with the user-facing repair path.
    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text, 0))")
        .bind(target_user_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Find the most recent lost streak — admin grants ignore the 48h window
    // but still need *something* to restore.
    let history: Option<(Uuid, i32, DateTime<Utc>)> = sqlx::query_as(
        r#"
        SELECT id, streak_value, streak_ended_at
        FROM user_streak_history
        WHERE user_id = $1
        ORDER BY streak_ended_at DESC
        LIMIT 1
        "#,
    )
    .bind(target_user_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (_history_id, streak_before_loss, lost_at) = history.ok_or_else(|| AppError::Domain {
        status: StatusCode::NOT_FOUND,
        code: "NO_STREAK_TO_REPAIR".to_string(),
        message: "User has no recorded lost streak".to_string(),
        details: json!({}),
    })?;

    sqlx::query(
        r#"
        UPDATE users
        SET current_streak = $2,
            longest_streak = GREATEST(longest_streak, $2),
            last_active_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        "#,
    )
    .bind(target_user_id)
    .bind(streak_before_loss)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let row: StreakRepairEventRow = sqlx::query_as(
        r#"
        INSERT INTO streak_repair_events
            (user_id, payment_method, payment_amount,
             streak_before_loss, streak_restored_to,
             lost_at, notes, actor_user_id)
        VALUES ($1, 'admin_grant', 0, $2, $2, $3, $4, $5)
        RETURNING id, user_id, payment_method, payment_amount,
                  streak_before_loss, streak_restored_to,
                  lost_at, repaired_at, idempotency_key, notes,
                  actor_user_id, created_at
        "#,
    )
    .bind(target_user_id)
    .bind(streak_before_loss)
    .bind(lost_at)
    .bind(reason)
    .bind(actor_user_id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "streak_repair",
        actor_user_id = %actor_user_id,
        target_user_id = %target_user_id,
        payment = "admin_grant",
        restored_to = streak_before_loss,
        "admin granted streak repair"
    );

    Ok(row)
}

// ---------------------------------------------------------------------------
// Insurance grant
// ---------------------------------------------------------------------------

pub async fn grant_insurance(
    pool: &PgPool,
    target_user_id: Uuid,
    actor_user_id: Uuid,
    request: &GrantInsuranceRequest,
) -> Result<StreakInsuranceRow, AppError> {
    if request.duration_days <= 0 {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_DURATION".to_string(),
            message: "duration_days must be > 0".to_string(),
            details: json!({"received": request.duration_days}),
        });
    }

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Reject if the user already has an active subscription — the unique
    // index on (user_id) where status='active' would do this for us, but a
    // typed error message is friendlier.
    let already: Option<(Uuid,)> = sqlx::query_as(
        r#"
        SELECT id
        FROM streak_insurance_subscriptions
        WHERE user_id = $1 AND status = 'active' AND expires_at > NOW()
        LIMIT 1
        "#,
    )
    .bind(target_user_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if already.is_some() {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "INSURANCE_ALREADY_ACTIVE".to_string(),
            message: "User already has an active streak insurance subscription".to_string(),
            details: json!({}),
        });
    }

    let row: StreakInsuranceRow = sqlx::query_as(
        r#"
        INSERT INTO streak_insurance_subscriptions
            (user_id, status, started_at, expires_at, provider,
             auto_brb_enabled, granted_by_user_id, grant_reason)
        VALUES ($1, 'active', NOW(), NOW() + ($2 || ' days')::INTERVAL,
                'admin_grant', true, $3, $4)
        RETURNING id, user_id, status, started_at, expires_at, provider,
                  provider_subscription_id, auto_brb_enabled,
                  granted_by_user_id, grant_reason, created_at, updated_at
        "#,
    )
    .bind(target_user_id)
    .bind(request.duration_days.to_string())
    .bind(actor_user_id)
    .bind(&request.reason)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "streak_insurance_grant",
        actor_user_id = %actor_user_id,
        target_user_id = %target_user_id,
        duration_days = request.duration_days,
        "insurance granted"
    );

    Ok(row)
}

// ---------------------------------------------------------------------------
// Audit listings
// ---------------------------------------------------------------------------

pub async fn list_repair_events(
    pool: &PgPool,
    query: &RepairEventsQuery,
) -> Result<RepairEventsResponse, AppError> {
    let page = query.page.unwrap_or(1).max(1);
    let per_page = query.per_page.unwrap_or(50).clamp(1, 200);
    let offset = (page - 1) * per_page;

    // We accept three optional filters: user_id, from, to.
    // Bound positions: $1 user, $2 from, $3 to, $4 limit, $5 offset
    let events = sqlx::query_as::<_, StreakRepairEventRow>(
        r#"
        SELECT id, user_id, payment_method, payment_amount,
               streak_before_loss, streak_restored_to,
               lost_at, repaired_at, idempotency_key, notes,
               actor_user_id, created_at
        FROM streak_repair_events
        WHERE ($1::uuid IS NULL OR user_id = $1)
          AND ($2::timestamptz IS NULL OR repaired_at >= $2)
          AND ($3::timestamptz IS NULL OR repaired_at <= $3)
        ORDER BY repaired_at DESC
        LIMIT $4 OFFSET $5
        "#,
    )
    .bind(query.user_id)
    .bind(query.from)
    .bind(query.to)
    .bind(per_page)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total: i64 = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(*)::bigint
        FROM streak_repair_events
        WHERE ($1::uuid IS NULL OR user_id = $1)
          AND ($2::timestamptz IS NULL OR repaired_at >= $2)
          AND ($3::timestamptz IS NULL OR repaired_at <= $3)
        "#,
    )
    .bind(query.user_id)
    .bind(query.from)
    .bind(query.to)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(RepairEventsResponse {
        events,
        page,
        per_page,
        total,
    })
}

pub async fn list_brb_events(
    pool: &PgPool,
    page: i64,
    per_page: i64,
) -> Result<BrbEventsResponse, AppError> {
    let page = page.max(1);
    let per_page = per_page.clamp(1, 200);
    let offset = (page - 1) * per_page;

    // PostgreSQL `MIN()` is not defined for `uuid`, so we pick a representative
    // row per `event_id` using DISTINCT ON and join to a per-event count.
    let events = sqlx::query_as::<_, BrbEventSummary>(
        r#"
        SELECT
            r.event_id,
            r.actor_user_id,
            r.reason,
            r.effective_from,
            r.effective_to,
            r.applied_at,
            c.affected_users
        FROM (
            SELECT DISTINCT ON (event_id)
                event_id,
                actor_user_id,
                reason,
                effective_from,
                effective_to,
                applied_at
            FROM streak_protection_events
            ORDER BY event_id, applied_at ASC
        ) r
        JOIN (
            SELECT event_id, COUNT(*)::bigint AS affected_users
            FROM streak_protection_events
            GROUP BY event_id
        ) c USING (event_id)
        ORDER BY r.applied_at DESC
        LIMIT $1 OFFSET $2
        "#,
    )
    .bind(per_page)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(DISTINCT event_id)::bigint FROM streak_protection_events",
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(BrbEventsResponse {
        events,
        page,
        per_page,
        total,
    })
}

// ---------------------------------------------------------------------------
// Aggregate stats
// ---------------------------------------------------------------------------

pub async fn streak_economy_stats(pool: &PgPool) -> Result<StreakEconomyStats, AppError> {
    let repairs = count_buckets(
        pool,
        "SELECT COUNT(*)::bigint FROM streak_repair_events WHERE repaired_at >= $1",
        "SELECT COUNT(*)::bigint FROM streak_repair_events",
    )
    .await?;

    let brb_invocations = brb_invocation_buckets(pool).await?;

    let friend_streak_increments = count_buckets(
        pool,
        "SELECT COUNT(*)::bigint FROM friend_streaks WHERE updated_at >= $1",
        "SELECT COALESCE(SUM(longest_count),0)::bigint FROM friend_streaks",
    )
    .await?;

    let phoenix_awards = count_buckets(
        pool,
        "SELECT COUNT(*)::bigint FROM user_streak_history WHERE phoenix_awarded = true AND streak_ended_at >= $1",
        "SELECT COUNT(*)::bigint FROM user_streak_history WHERE phoenix_awarded = true",
    )
    .await?;

    Ok(StreakEconomyStats {
        repairs,
        brb_invocations,
        friend_streak_increments,
        phoenix_awards,
    })
}

async fn count_buckets(
    pool: &PgPool,
    bucketed_sql: &str,
    all_time_sql: &str,
) -> Result<KpiBuckets, AppError> {
    let now = Utc::now();
    let last_7 = now - Duration::days(7);
    let last_30 = now - Duration::days(30);

    let last_7_days: i64 = sqlx::query_scalar::<_, i64>(bucketed_sql)
        .bind(last_7)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let last_30_days: i64 = sqlx::query_scalar::<_, i64>(bucketed_sql)
        .bind(last_30)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let all_time: i64 = sqlx::query_scalar::<_, i64>(all_time_sql)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(KpiBuckets {
        last_7_days,
        last_30_days,
        all_time,
    })
}

async fn brb_invocation_buckets(pool: &PgPool) -> Result<KpiBuckets, AppError> {
    let now = Utc::now();
    let last_7 = now - Duration::days(7);
    let last_30 = now - Duration::days(30);

    let last_7_days: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(DISTINCT event_id)::bigint FROM streak_protection_events WHERE applied_at >= $1",
    )
    .bind(last_7)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let last_30_days: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(DISTINCT event_id)::bigint FROM streak_protection_events WHERE applied_at >= $1",
    )
    .bind(last_30)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let all_time: i64 = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(DISTINCT event_id)::bigint FROM streak_protection_events",
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(KpiBuckets {
        last_7_days,
        last_30_days,
        all_time,
    })
}
