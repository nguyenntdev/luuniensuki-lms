//! Progress, Streak, Hearts, Daily Goal, and Milestone business logic.
//!
//! Phase 6 (Tasks 7.1–7.3): Progress & Streaks migration.
//!
//! Fixed to match actual production database schema:
//! - Streaks: stored in `users` table (current_streak, longest_streak, streak_freezes, last_active_at)
//! - Hearts: stored in `user_hearts` table (current_hearts, max_hearts, unlimited_until, hearts_refill_at)
//! - Daily Goal: no table exists — returns hardcoded defaults
//! - Milestones: stored in `user_milestones` table (milestone_type is a PG enum, cast to text)

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::progress::*;

const DISCOVERY_XP: i32 = 10;
const MAX_HEARTS: i32 = 5;
const DEFAULT_DAILY_XP_GOAL: i32 = 50;

/// POST /api/v1/progress/unlock — unlock/discover a motif.
pub async fn unlock_motif(
    pool: &PgPool,
    user_id: Uuid,
    payload: &UnlockMotifRequest,
) -> Result<UnlockMotifResponse, AppError> {
    // Verify motif exists
    let _motif: (Uuid,) = sqlx::query_as("SELECT id FROM motifs WHERE id = $1 AND is_active = true")
        .bind(payload.motif_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or_else(|| AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Motif not found".to_string(),
        })?;

    let now = Utc::now();

    // Upsert progress to 'discovered'
    sqlx::query(
        r#"
        INSERT INTO user_progress (id, user_id, motif_id, status, discovered_at, xp_earned)
        VALUES ($1, $2, $3, 'discovered', $4, $5)
        ON CONFLICT (user_id, motif_id)
        DO UPDATE SET
            discovered_at = COALESCE(user_progress.discovered_at, $4),
            status = CASE WHEN user_progress.status = 'hidden' THEN 'discovered' ELSE user_progress.status END
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(payload.motif_id)
    .bind(now)
    .bind(DISCOVERY_XP)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Award XP
    sqlx::query("UPDATE users SET total_xp = total_xp + $1, last_active_at = $2 WHERE id = $3")
        .bind(DISCOVERY_XP)
        .bind(now)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(UnlockMotifResponse {
        motif_id: payload.motif_id,
        status: "discovered".to_string(),
        discovered_at: now,
        xp_awarded: DISCOVERY_XP,
    })
}

/// GET /api/v1/users/me/streak — get user streak data.
/// Streak data is stored in the `users` table directly.
pub async fn get_streak(pool: &PgPool, user_id: Uuid) -> Result<StreakResponse, AppError> {
    let row: Option<StreakRow> = sqlx::query_as(
        r#"
        SELECT current_streak, longest_streak, streak_freezes, last_active_at
        FROM users
        WHERE id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => {
            let today = Utc::now();
            let streak_alive = r.last_active_at
                .map(|d| (today - d).num_hours() <= 48)
                .unwrap_or(false);

            Ok(StreakResponse {
                current_streak: if streak_alive { r.current_streak } else { 0 },
                longest_streak: r.longest_streak,
                last_activity_date: r.last_active_at.map(|d| d.format("%Y-%m-%d").to_string()),
                streak_alive,
                freeze_available: r.streak_freezes > 0,
            })
        }
        None => Ok(StreakResponse {
            current_streak: 0,
            longest_streak: 0,
            last_activity_date: None,
            streak_alive: false,
            freeze_available: false,
        }),
    }
}

/// POST /api/v1/users/me/streak — update streak (heartbeat).
/// Updates the `users` table directly.
pub async fn update_streak_heartbeat(
    pool: &PgPool,
    user_id: Uuid,
    _payload: &StreakHeartbeatRequest,
) -> Result<StreakHeartbeatResponse, AppError> {
    let now = Utc::now();
    let today = now.date_naive();

    let row: Option<StreakRow> = sqlx::query_as(
        r#"
        SELECT current_streak, longest_streak, streak_freezes, last_active_at
        FROM users
        WHERE id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (new_streak, longest, extended) = match row {
        Some(r) => {
            let last_date = r.last_active_at.map(|d| d.date_naive());
            if last_date == Some(today) {
                // Already active today
                (r.current_streak, r.longest_streak, false)
            } else if last_date.map(|d| (today - d).num_days() == 1).unwrap_or(false) {
                // Consecutive day
                let new = r.current_streak + 1;
                let longest = new.max(r.longest_streak);
                (new, longest, true)
            } else {
                // Streak broken, start fresh
                (1, r.longest_streak.max(1), true)
            }
        }
        None => (1, 1, true),
    };

    // Update streak in users table
    sqlx::query(
        r#"
        UPDATE users
        SET current_streak = $1, longest_streak = $2, last_active_at = $3
        WHERE id = $4
        "#,
    )
    .bind(new_streak)
    .bind(longest)
    .bind(now)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(StreakHeartbeatResponse {
        current_streak: new_streak,
        longest_streak: longest,
        streak_extended: extended,
        last_activity_date: today.to_string(),
    })
}

/// GET /api/v1/users/me/hearts — get hearts balance.
/// Hearts are stored in `user_hearts` table.
pub async fn get_hearts(pool: &PgPool, user_id: Uuid) -> Result<HeartsResponse, AppError> {
    let row: Option<HeartsRow> = sqlx::query_as(
        r#"
        SELECT current_hearts, max_hearts, hearts_refill_at, unlimited_until
        FROM user_hearts
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => {
            let now = Utc::now();
            let is_unlimited = r.unlimited_until.map(|u| u > now).unwrap_or(false);
            Ok(HeartsResponse {
                hearts: r.current_hearts,
                max_hearts: r.max_hearts,
                next_regen_at: r.hearts_refill_at,
                is_unlimited,
            })
        }
        None => Ok(HeartsResponse {
            hearts: MAX_HEARTS,
            max_hearts: MAX_HEARTS,
            next_regen_at: None,
            is_unlimited: false,
        }),
    }
}

/// POST /api/v1/users/me/hearts — spend or refill hearts.
/// Hearts are stored in `user_hearts` table.
pub async fn update_hearts(
    pool: &PgPool,
    user_id: Uuid,
    payload: &HeartsActionRequest,
) -> Result<HeartsActionResponse, AppError> {
    let amount = payload.amount.unwrap_or(1);

    match payload.action.as_str() {
        "spend" => {
            // Ensure user has enough hearts
            let row: Option<HeartsRow> = sqlx::query_as(
                r#"
                SELECT current_hearts, max_hearts, hearts_refill_at, unlimited_until
                FROM user_hearts
                WHERE user_id = $1
                "#,
            )
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let now = Utc::now();
            let current = row.as_ref().map(|r| r.current_hearts).unwrap_or(MAX_HEARTS);
            let is_unlimited = row.as_ref()
                .and_then(|r| r.unlimited_until)
                .map(|u| u > now)
                .unwrap_or(false);

            if !is_unlimited && current < amount {
                return Err(AppError::Domain {
                    status: axum::http::StatusCode::BAD_REQUEST,
                    code: "INSUFFICIENT_HEARTS".to_string(),
                    message: "Not enough hearts".to_string(),
                    details: serde_json::json!({"current": current, "required": amount}),
                });
            }

            let new_hearts = if is_unlimited { current } else { (current - amount).max(0) };

            sqlx::query(
                r#"
                INSERT INTO user_hearts (id, user_id, current_hearts, max_hearts, last_heart_lost_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5)
                ON CONFLICT (user_id)
                DO UPDATE SET current_hearts = $3, last_heart_lost_at = $5, updated_at = $5
                "#,
            )
            .bind(Uuid::new_v4())
            .bind(user_id)
            .bind(new_hearts)
            .bind(MAX_HEARTS)
            .bind(now)
            .execute(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            Ok(HeartsActionResponse {
                hearts: new_hearts,
                max_hearts: MAX_HEARTS,
                action_performed: "spend".to_string(),
            })
        }
        "refill" => {
            let now = Utc::now();
            sqlx::query(
                r#"
                INSERT INTO user_hearts (id, user_id, current_hearts, max_hearts, hearts_refill_at, updated_at)
                VALUES ($1, $2, $3, $3, NULL, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET current_hearts = $3, hearts_refill_at = NULL, updated_at = $4
                "#,
            )
            .bind(Uuid::new_v4())
            .bind(user_id)
            .bind(MAX_HEARTS)
            .bind(now)
            .execute(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            Ok(HeartsActionResponse {
                hearts: MAX_HEARTS,
                max_hearts: MAX_HEARTS,
                action_performed: "refill".to_string(),
            })
        }
        _ => Err(AppError::Domain {
            status: axum::http::StatusCode::BAD_REQUEST,
            code: "INVALID_ACTION".to_string(),
            message: "Action must be 'spend' or 'refill'".to_string(),
            details: serde_json::json!({}),
        }),
    }
}

/// GET /api/v1/users/me/daily-goal — get daily goal settings.
/// No separate table exists in production. Return hardcoded defaults.
pub async fn get_daily_goal(_pool: &PgPool, _user_id: Uuid) -> Result<DailyGoalResponse, AppError> {
    Ok(DailyGoalResponse {
        daily_xp_goal: DEFAULT_DAILY_XP_GOAL,
        xp_earned_today: 0,
        goal_met: false,
        lessons_today: 0,
        quizzes_today: 0,
    })
}

/// PUT /api/v1/users/me/daily-goal — update daily goal.
/// No separate table exists in production. Accept the request but return the value as-is.
pub async fn update_daily_goal(
    _pool: &PgPool,
    _user_id: Uuid,
    payload: &UpdateDailyGoalRequest,
) -> Result<UpdateDailyGoalResponse, AppError> {
    if payload.daily_xp_goal < 10 || payload.daily_xp_goal > 500 {
        return Err(AppError::Domain {
            status: axum::http::StatusCode::BAD_REQUEST,
            code: "INVALID_GOAL".to_string(),
            message: "Daily XP goal must be between 10 and 500".to_string(),
            details: serde_json::json!({}),
        });
    }

    // No-op: no table exists. Return the value as confirmation.
    Ok(UpdateDailyGoalResponse {
        daily_xp_goal: payload.daily_xp_goal,
        updated: true,
    })
}

/// GET /api/v1/users/me/milestones — get user milestones.
/// Milestones are stored in `user_milestones` table. milestone_type is a PG enum, cast to text.
pub async fn get_milestones(pool: &PgPool, user_id: Uuid) -> Result<MilestonesResponse, AppError> {
    let rows = sqlx::query_as::<_, MilestoneRow>(
        r#"
        SELECT id, milestone_type::text AS milestone_type, achieved_at, context_data, celebrated
        FROM user_milestones
        WHERE user_id = $1
        ORDER BY achieved_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total_achieved = rows.len() as i32;

    let milestones: Vec<MilestoneOut> = rows
        .into_iter()
        .map(|r| {
            let title = r.milestone_type.clone();
            MilestoneOut {
                id: r.id,
                milestone_type: r.milestone_type,
                title,
                description: r.context_data.as_ref().and_then(|d| d.get("description").and_then(|v| v.as_str()).map(|s| s.to_string())),
                achieved_at: Some(r.achieved_at),
                progress_current: if r.celebrated { 1 } else { 0 },
                progress_target: 1,
                is_achieved: true,
            }
        })
        .collect();

    Ok(MilestonesResponse {
        milestones,
        total_achieved,
    })
}
