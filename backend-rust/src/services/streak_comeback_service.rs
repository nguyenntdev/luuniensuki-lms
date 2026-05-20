//! Streak comeback / Phoenix Badge progress.
//!
//! Implements `GET /api/v1/users/me/streak/comeback-status` and
//! `GET /api/v1/users/me/streak-insurance`.
//!
//! Phoenix eligibility:
//! - The user must have a `user_streak_history` row with `streak_value >= 30`
//!   AND `phoenix_awarded = false`.
//! - After that streak ended, the user must have been active on 3 consecutive
//!   UTC days (using `users.last_active_at`).
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use chrono::{DateTime, Duration, Utc};
use sqlx::{PgPool, Postgres, Transaction};
use uuid::Uuid;

use crate::error::AppError;
use crate::models::streak_economy::{
    ActiveComebackBonus, ComebackStatusResponse, StreakInsuranceRow,
};

const DAYS_REQUIRED: i32 = 3;
const QUALIFYING_STREAK_VALUE: i32 = 30;
const COMEBACK_BONUS_DAYS: i64 = 7;
const COMEBACK_MULTIPLIER: f64 = 2.0;

/// `GET /api/v1/users/me/streak/comeback-status`.
pub async fn comeback_status(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<ComebackStatusResponse, AppError> {
    // Find the latest qualifying lost-streak that has not been redeemed yet.
    let candidate: Option<(Uuid, DateTime<Utc>)> = sqlx::query_as(
        r#"
        SELECT id, streak_ended_at
        FROM user_streak_history
        WHERE user_id = $1
          AND streak_value >= $2
          AND phoenix_awarded = false
        ORDER BY streak_ended_at DESC
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .bind(QUALIFYING_STREAK_VALUE)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let consecutive_days_active = match candidate {
        Some((_history_id, ended_at)) => {
            // After a streak loss, `users.current_streak` is reset to 0 and
            // grows again with daily activity. We treat the rebuilt
            // `current_streak` (capped at any post-loss value) as the count
            // of consecutive comeback days, and additionally check that the
            // user's `last_active_at` falls strictly after the loss.
            let row: Option<(i32, Option<DateTime<Utc>>)> = sqlx::query_as(
                "SELECT current_streak, last_active_at FROM users WHERE id = $1",
            )
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            match row {
                Some((streak, Some(last_active))) if last_active > ended_at => streak,
                _ => 0,
            }
        }
        None => 0,
    };

    let phoenix_eligible = consecutive_days_active >= DAYS_REQUIRED;

    // Look up an active comeback bonus, if any.
    let active_bonus = active_comeback_bonus(pool, user_id).await?;

    Ok(ComebackStatusResponse {
        phoenix_eligible,
        consecutive_days_active,
        days_required: DAYS_REQUIRED,
        active_bonus,
    })
}

/// `GET /api/v1/users/me/streak-insurance`.
pub async fn get_my_insurance(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<Option<StreakInsuranceRow>, AppError> {
    let row = sqlx::query_as::<_, StreakInsuranceRow>(
        r#"
        SELECT id, user_id, status, started_at, expires_at, provider,
               provider_subscription_id, auto_brb_enabled,
               granted_by_user_id, grant_reason, created_at, updated_at
        FROM streak_insurance_subscriptions
        WHERE user_id = $1 AND status = 'active' AND expires_at > NOW()
        ORDER BY started_at DESC
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row)
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async fn active_comeback_bonus(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<Option<ActiveComebackBonus>, AppError> {
    let row: Option<(String, DateTime<Utc>, DateTime<Utc>)> = sqlx::query_as(
        r#"
        SELECT multiplier::text, started_at, expires_at
        FROM user_comeback_bonuses
        WHERE user_id = $1 AND expires_at > NOW()
        ORDER BY expires_at DESC
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(row.map(|(mult_text, started_at, expires_at)| {
        let multiplier = mult_text.parse::<f64>().unwrap_or(1.0);
        ActiveComebackBonus {
            multiplier,
            started_at,
            expires_at,
        }
    }))
}


/// Award the Phoenix badge if the user is eligible.
///
/// Eligibility:
///   - There exists a `user_streak_history` row with `streak_value >= 30` and
///     `phoenix_awarded = false`.
///   - The user's `current_streak >= 3` and `last_active_at` is strictly
///     after the loss timestamp.
///
/// On success: marks the history row as awarded, inserts a `user_badges` row,
/// and creates a 7-day 2.0x comeback bonus.
///
/// Returns `Ok(true)` if the badge was awarded in this call, `Ok(false)`
/// otherwise. Idempotent under concurrent calls (guarded by the
/// `phoenix_awarded` boolean).
pub async fn award_phoenix_if_eligible(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<bool, AppError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Per-user advisory lock: prevents two concurrent requests from awarding
    // twice for the same history row.
    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text, 0))")
        .bind(user_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Find the most recent unredeemed qualifying loss.
    let candidate: Option<(Uuid, DateTime<Utc>)> = sqlx::query_as(
        r#"
        SELECT id, streak_ended_at
        FROM user_streak_history
        WHERE user_id = $1
          AND streak_value >= $2
          AND phoenix_awarded = false
        ORDER BY streak_ended_at DESC
        LIMIT 1
        FOR UPDATE
        "#,
    )
    .bind(user_id)
    .bind(QUALIFYING_STREAK_VALUE)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (history_id, ended_at) = match candidate {
        Some(c) => c,
        None => {
            tx.rollback()
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(false);
        }
    };

    // Check the user's current streak and last activity.
    let row: Option<(i32, Option<DateTime<Utc>>)> = sqlx::query_as(
        "SELECT current_streak, last_active_at FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let eligible = match row {
        Some((streak, Some(last_active))) => {
            streak >= DAYS_REQUIRED && last_active > ended_at
        }
        _ => false,
    };

    if !eligible {
        tx.rollback()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        return Ok(false);
    }

    // Look up the Phoenix badge id (badge slug = 'phoenix').
    let badge_id: Option<Uuid> =
        sqlx::query_scalar("SELECT id FROM badges WHERE slug = 'phoenix' LIMIT 1")
            .fetch_optional(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    let badge_id = match badge_id {
        Some(id) => id,
        None => {
            // Badge missing — log and bail out without making changes.
            tracing::warn!(
                feature = "phoenix_award",
                user_id = %user_id,
                "phoenix badge slug missing from badges table",
            );
            tx.rollback()
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(false);
        }
    };

    // Award the badge (idempotent).
    sqlx::query(
        "INSERT INTO user_badges (id, user_id, badge_id, awarded_at) \
         VALUES ($1, $2, $3, NOW()) \
         ON CONFLICT DO NOTHING",
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(badge_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Mark the history row as redeemed.
    sqlx::query(
        "UPDATE user_streak_history SET phoenix_awarded = true WHERE id = $1",
    )
    .bind(history_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Insert the comeback bonus row.
    sqlx::query(
        r#"
        INSERT INTO user_comeback_bonuses
            (id, user_id, multiplier, started_at, expires_at, history_row_id)
        VALUES ($1, $2, $3, NOW(), $4, $5)
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(COMEBACK_MULTIPLIER)
    .bind(Utc::now() + Duration::days(COMEBACK_BONUS_DAYS))
    .bind(history_id)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tx.commit().await.map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "phoenix_award",
        user_id = %user_id,
        history_id = %history_id,
        "phoenix badge awarded with comeback bonus",
    );

    crate::routes::metrics::PHOENIX_BADGE_TOTAL
        .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

    Ok(true)
}

/// Apply the active comeback multiplier to an XP delta. Returns the multiplied
/// value rounded down to the nearest integer.
///
/// If no active bonus exists, returns the input unchanged.
pub async fn apply_xp_multiplier(
    tx: &mut Transaction<'_, Postgres>,
    user_id: Uuid,
    base_xp: i32,
) -> Result<i32, AppError> {
    if base_xp <= 0 {
        return Ok(base_xp);
    }
    let row: Option<(String,)> = sqlx::query_as(
        "SELECT multiplier::text FROM user_comeback_bonuses \
         WHERE user_id = $1 AND expires_at > NOW() \
         ORDER BY expires_at DESC LIMIT 1",
    )
    .bind(user_id)
    .fetch_optional(&mut **tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let multiplier = row
        .and_then(|r| r.0.parse::<f64>().ok())
        .unwrap_or(1.0);
    let multiplied = ((base_xp as f64) * multiplier).floor() as i32;
    Ok(multiplied)
}
