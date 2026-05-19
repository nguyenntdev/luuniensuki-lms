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

use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::streak_economy::{
    ActiveComebackBonus, ComebackStatusResponse, StreakInsuranceRow,
};

const DAYS_REQUIRED: i32 = 3;
const QUALIFYING_STREAK_VALUE: i32 = 30;

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
