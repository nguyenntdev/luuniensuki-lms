//! Streak repair business logic.
//!
//! Implements:
//! - `POST /api/v1/users/me/streak/repair`
//! - `GET  /api/v1/users/me/streak/repair-options`
//!
//! Spec: `.kiro/specs/streak-repair-economy/`
//!
//! Algorithm summary (see design.md for the full sequence):
//! 1. Open transaction with a per-user advisory lock.
//! 2. Honour `Idempotency-Key` by returning a cached response when a row with
//!    the same `(user_id, idempotency_key)` exists in the last 24h.
//! 3. Find the most recent `user_streak_history` row inside the 48h window.
//! 4. Enforce monthly limit (1, or 3 with active insurance).
//! 5. Validate payment funds, deduct, restore the streak, insert event row.

use axum::http::StatusCode;
use chrono::{DateTime, Duration, Utc};
use serde_json::json;
use sqlx::{PgPool, Postgres, Transaction};
use uuid::Uuid;

use crate::error::AppError;
use crate::models::streak_economy::{RepairOptions, RepairResponse, StreakRepairEventRow};

pub const REPAIR_HEARTS_COST: i32 = 50;
pub const REPAIR_XP_COST: i32 = 200;
pub const REPAIR_WINDOW_HOURS: i64 = 48;
pub const DEFAULT_MONTHLY_LIMIT: i32 = 1;
pub const INSURED_MONTHLY_LIMIT: i32 = 3;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PaymentMethod {
    Hearts,
    Xp,
}

impl PaymentMethod {
    pub fn as_db_str(&self) -> &'static str {
        match self {
            PaymentMethod::Hearts => "hearts",
            PaymentMethod::Xp => "xp",
        }
    }

    pub fn cost(&self) -> i32 {
        match self {
            PaymentMethod::Hearts => REPAIR_HEARTS_COST,
            PaymentMethod::Xp => REPAIR_XP_COST,
        }
    }

    pub fn parse(input: &str) -> Result<Self, AppError> {
        match input {
            "hearts" => Ok(PaymentMethod::Hearts),
            "xp" => Ok(PaymentMethod::Xp),
            _ => Err(AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "INVALID_PAYMENT_METHOD".to_string(),
                message: "payment must be 'hearts' or 'xp'".to_string(),
                details: json!({"received": input}),
            }),
        }
    }
}

/// Repair the user's streak. Idempotency-Key is optional; if present, a prior
/// row inside the last 24h short-circuits the deduction and returns the same
/// response.
pub async fn repair(
    pool: &PgPool,
    user_id: Uuid,
    payment: PaymentMethod,
    idempotency_key: Option<&str>,
) -> Result<RepairResponse, AppError> {
    let mut tx = pool
        .begin()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // 1. Per-user advisory lock — serializes all repair attempts for this user.
    sqlx::query("SELECT pg_advisory_xact_lock(hashtextextended($1::text, 0))")
        .bind(user_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // 2. Idempotency replay (only when a key is provided).
    if let Some(key) = idempotency_key {
        if let Some(existing) = sqlx::query_as::<_, StreakRepairEventRow>(
            r#"
            SELECT id, user_id, payment_method, payment_amount,
                   streak_before_loss, streak_restored_to,
                   lost_at, repaired_at, idempotency_key, notes,
                   actor_user_id, created_at
            FROM streak_repair_events
            WHERE user_id = $1
              AND idempotency_key = $2
              AND repaired_at > NOW() - INTERVAL '24 hours'
            ORDER BY repaired_at DESC
            LIMIT 1
            "#,
        )
        .bind(user_id)
        .bind(key)
        .fetch_optional(&mut *tx)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        {
            tx.commit()
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
            return Ok(RepairResponse {
                current_streak: existing.streak_restored_to,
                payment: existing.payment_method,
                repaired_at: existing.repaired_at,
            });
        }
    }

    // 3. Locate the most recent loss inside the 48h window.
    let history: Option<(Uuid, i32, DateTime<Utc>)> = sqlx::query_as(
        r#"
        SELECT id, streak_value, streak_ended_at
        FROM user_streak_history
        WHERE user_id = $1
          AND streak_ended_at > NOW() - ($2 || ' hours')::INTERVAL
        ORDER BY streak_ended_at DESC
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .bind(REPAIR_WINDOW_HOURS.to_string())
    .fetch_optional(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (_history_id, streak_before_loss, lost_at) = history.ok_or_else(|| AppError::Domain {
        status: StatusCode::GONE,
        code: "REPAIR_WINDOW_EXPIRED".to_string(),
        message: "Streak can only be repaired within 48 hours of loss".to_string(),
        details: json!({}),
    })?;

    // 4. Enforce monthly limit (3 with active insurance, 1 otherwise).
    let monthly_used: (i64,) = sqlx::query_as(
        r#"
        SELECT COUNT(*)::bigint
        FROM streak_repair_events
        WHERE user_id = $1
          AND date_trunc('month', repaired_at) = date_trunc('month', NOW())
          AND payment_method <> 'admin_grant'
        "#,
    )
    .bind(user_id)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let limit = if has_active_insurance_tx(&mut tx, user_id).await? {
        INSURED_MONTHLY_LIMIT
    } else {
        DEFAULT_MONTHLY_LIMIT
    };

    if monthly_used.0 >= limit as i64 {
        return Err(AppError::Domain {
            status: StatusCode::TOO_MANY_REQUESTS,
            code: "REPAIR_LIMIT_REACHED".to_string(),
            message: "Streak repair already used this month".to_string(),
            details: json!({
                "reset_at": next_month_start(Utc::now()),
                "monthly_limit": limit,
            }),
        });
    }

    // 5. Validate payment, deduct, restore.
    match payment {
        PaymentMethod::Hearts => {
            // Read current hearts (defaulting to 0 if no row).
            let current: i32 = sqlx::query_scalar::<_, i32>(
                "SELECT current_hearts FROM user_hearts WHERE user_id = $1",
            )
            .bind(user_id)
            .fetch_optional(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
            .unwrap_or(0);

            if current < REPAIR_HEARTS_COST {
                return Err(AppError::Domain {
                    status: StatusCode::PAYMENT_REQUIRED,
                    code: "INSUFFICIENT_HEARTS".to_string(),
                    message: format!("Need {} hearts to repair", REPAIR_HEARTS_COST),
                    details: json!({"current": current, "required": REPAIR_HEARTS_COST}),
                });
            }

            sqlx::query(
                r#"
                UPDATE user_hearts
                SET current_hearts = current_hearts - $2,
                    last_heart_lost_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = $1
                "#,
            )
            .bind(user_id)
            .bind(REPAIR_HEARTS_COST)
            .execute(&mut *tx)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        }
        PaymentMethod::Xp => {
            let current: i32 =
                sqlx::query_scalar::<_, i32>("SELECT total_xp FROM users WHERE id = $1")
                    .bind(user_id)
                    .fetch_optional(&mut *tx)
                    .await
                    .map_err(|e| AppError::Internal(e.into()))?
                    .unwrap_or(0);

            if current < REPAIR_XP_COST {
                return Err(AppError::Domain {
                    status: StatusCode::PAYMENT_REQUIRED,
                    code: "INSUFFICIENT_XP".to_string(),
                    message: format!("Need {} XP to repair", REPAIR_XP_COST),
                    details: json!({"current": current, "required": REPAIR_XP_COST}),
                });
            }

            sqlx::query("UPDATE users SET total_xp = total_xp - $2 WHERE id = $1")
                .bind(user_id)
                .bind(REPAIR_XP_COST)
                .execute(&mut *tx)
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
        }
    }

    // Restore the streak on the users row.
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
    .bind(user_id)
    .bind(streak_before_loss)
    .execute(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Insert the audit row.
    let event_id = Uuid::new_v4();
    let repaired_at: DateTime<Utc> = sqlx::query_scalar::<_, DateTime<Utc>>(
        r#"
        INSERT INTO streak_repair_events
            (id, user_id, payment_method, payment_amount,
             streak_before_loss, streak_restored_to,
             lost_at, idempotency_key)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING repaired_at
        "#,
    )
    .bind(event_id)
    .bind(user_id)
    .bind(payment.as_db_str())
    .bind(payment.cost())
    .bind(streak_before_loss)
    .bind(streak_before_loss)
    .bind(lost_at)
    .bind(idempotency_key)
    .fetch_one(&mut *tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tx.commit()
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "streak_repair",
        user_id = %user_id,
        payment = payment.as_db_str(),
        restored_to = streak_before_loss,
        "streak repair succeeded"
    );

    crate::routes::metrics::STREAK_REPAIR_TOTAL.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

    Ok(RepairResponse {
        current_streak: streak_before_loss,
        payment: payment.as_db_str().to_string(),
        repaired_at,
    })
}

/// `GET /api/v1/users/me/streak/repair-options`.
pub async fn get_repair_options(pool: &PgPool, user_id: Uuid) -> Result<RepairOptions, AppError> {
    // Latest streak loss in the last 48h.
    let last_loss: Option<DateTime<Utc>> = sqlx::query_scalar::<_, DateTime<Utc>>(
        r#"
        SELECT streak_ended_at
        FROM user_streak_history
        WHERE user_id = $1
          AND streak_ended_at > NOW() - INTERVAL '48 hours'
        ORDER BY streak_ended_at DESC
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let monthly_used: i64 = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(*)::bigint
        FROM streak_repair_events
        WHERE user_id = $1
          AND date_trunc('month', repaired_at) = date_trunc('month', NOW())
          AND payment_method <> 'admin_grant'
        "#,
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let limit = if has_active_insurance(pool, user_id).await? {
        INSURED_MONTHLY_LIMIT
    } else {
        DEFAULT_MONTHLY_LIMIT
    };

    let hearts: i32 =
        sqlx::query_scalar::<_, i32>("SELECT current_hearts FROM user_hearts WHERE user_id = $1")
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
            .unwrap_or(0);

    let xp: i32 = sqlx::query_scalar::<_, i32>("SELECT total_xp FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .unwrap_or(0);

    let mut payment_options = Vec::new();
    if hearts >= REPAIR_HEARTS_COST {
        payment_options.push("hearts".to_string());
    }
    if xp >= REPAIR_XP_COST {
        payment_options.push("xp".to_string());
    }

    let repair_available = last_loss.is_some() && monthly_used < limit as i64;

    Ok(RepairOptions {
        repair_available,
        lost_at: last_loss,
        expires_at: last_loss.map(|t| t + Duration::hours(REPAIR_WINDOW_HOURS)),
        monthly_repairs_used: monthly_used as i32,
        monthly_repairs_limit: limit,
        hearts_required: REPAIR_HEARTS_COST,
        xp_required: REPAIR_XP_COST,
        payment_options_available: payment_options,
    })
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async fn has_active_insurance(pool: &PgPool, user_id: Uuid) -> Result<bool, AppError> {
    let row: Option<(Uuid,)> = sqlx::query_as(
        r#"
        SELECT id
        FROM streak_insurance_subscriptions
        WHERE user_id = $1 AND status = 'active' AND expires_at > NOW()
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row.is_some())
}

async fn has_active_insurance_tx(
    tx: &mut Transaction<'_, Postgres>,
    user_id: Uuid,
) -> Result<bool, AppError> {
    let row: Option<(Uuid,)> = sqlx::query_as(
        r#"
        SELECT id
        FROM streak_insurance_subscriptions
        WHERE user_id = $1 AND status = 'active' AND expires_at > NOW()
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .fetch_optional(&mut **tx)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    Ok(row.is_some())
}

fn next_month_start(now: DateTime<Utc>) -> DateTime<Utc> {
    use chrono::Datelike;
    let (y, m) = if now.month() == 12 {
        (now.year() + 1, 1)
    } else {
        (now.year(), now.month() + 1)
    };
    chrono::TimeZone::with_ymd_and_hms(&Utc, y, m, 1, 0, 0, 0)
        .single()
        .unwrap_or(now)
}
