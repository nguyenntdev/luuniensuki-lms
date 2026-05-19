//! Progress, Streak, Hearts, Daily Goal, and Milestone business logic.
//!
//! Phase 6 (Tasks 7.1–7.3): Progress & Streaks migration.

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
pub async fn get_streak(pool: &PgPool, user_id: Uuid) -> Result<StreakResponse, AppError> {
    let row = sqlx::query_as::<_, StreakRow>(
        "SELECT current_streak, longest_streak, last_activity_date FROM user_streaks WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => {
            let today = Utc::now().date_naive();
            let streak_alive = r.last_activity_date
                .map(|d| (today - d).num_days() <= 1)
                .unwrap_or(false);

            Ok(StreakResponse {
                current_streak: if streak_alive { r.current_streak } else { 0 },
                longest_streak: r.longest_streak,
                last_activity_date: r.last_activity_date.map(|d| d.to_string()),
                streak_alive,
                freeze_available: false,
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
pub async fn update_streak_heartbeat(
    pool: &PgPool,
    user_id: Uuid,
    _payload: &StreakHeartbeatRequest,
) -> Result<StreakHeartbeatResponse, AppError> {
    let today = Utc::now().date_naive();

    let row = sqlx::query_as::<_, StreakRow>(
        "SELECT current_streak, longest_streak, last_activity_date FROM user_streaks WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (new_streak, longest, extended) = match row {
        Some(r) => {
            if r.last_activity_date == Some(today) {
                // Already active today
                (r.current_streak, r.longest_streak, false)
            } else if r.last_activity_date.map(|d| (today - d).num_days() == 1).unwrap_or(false) {
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

    // Upsert streak
    sqlx::query(
        r#"
        INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_activity_date)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id)
        DO UPDATE SET current_streak = $2, longest_streak = $3, last_activity_date = $4
        "#,
    )
    .bind(user_id)
    .bind(new_streak)
    .bind(longest)
    .bind(today)
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
pub async fn get_hearts(pool: &PgPool, user_id: Uuid) -> Result<HeartsResponse, AppError> {
    let row = sqlx::query_as::<_, HeartsRow>(
        "SELECT hearts, max_hearts, next_regen_at, is_unlimited FROM user_hearts WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => Ok(HeartsResponse {
            hearts: r.hearts,
            max_hearts: r.max_hearts,
            next_regen_at: r.next_regen_at,
            is_unlimited: r.is_unlimited,
        }),
        None => Ok(HeartsResponse {
            hearts: MAX_HEARTS,
            max_hearts: MAX_HEARTS,
            next_regen_at: None,
            is_unlimited: false,
        }),
    }
}

/// POST /api/v1/users/me/hearts — spend or refill hearts.
pub async fn update_hearts(
    pool: &PgPool,
    user_id: Uuid,
    payload: &HeartsActionRequest,
) -> Result<HeartsActionResponse, AppError> {
    let amount = payload.amount.unwrap_or(1);

    match payload.action.as_str() {
        "spend" => {
            // Ensure user has enough hearts
            let row = sqlx::query_as::<_, HeartsRow>(
                "SELECT hearts, max_hearts, next_regen_at, is_unlimited FROM user_hearts WHERE user_id = $1",
            )
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let current = row.as_ref().map(|r| r.hearts).unwrap_or(MAX_HEARTS);
            let is_unlimited = row.as_ref().map(|r| r.is_unlimited).unwrap_or(false);

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
                INSERT INTO user_hearts (user_id, hearts, max_hearts, is_unlimited)
                VALUES ($1, $2, $3, false)
                ON CONFLICT (user_id)
                DO UPDATE SET hearts = $2
                "#,
            )
            .bind(user_id)
            .bind(new_hearts)
            .bind(MAX_HEARTS)
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
            sqlx::query(
                r#"
                INSERT INTO user_hearts (user_id, hearts, max_hearts, is_unlimited)
                VALUES ($1, $2, $2, false)
                ON CONFLICT (user_id)
                DO UPDATE SET hearts = $2, next_regen_at = NULL
                "#,
            )
            .bind(user_id)
            .bind(MAX_HEARTS)
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
pub async fn get_daily_goal(pool: &PgPool, user_id: Uuid) -> Result<DailyGoalResponse, AppError> {
    let goal_row = sqlx::query_as::<_, DailyGoalRow>(
        "SELECT daily_xp_goal FROM user_settings WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let daily_xp_goal = goal_row.map(|r| r.daily_xp_goal).unwrap_or(DEFAULT_DAILY_XP_GOAL);

    // Calculate today's XP from activity
    let today_start = Utc::now().date_naive().and_hms_opt(0, 0, 0).unwrap();
    let today_stats: Option<(i64, i64, i64)> = sqlx::query_as(
        r#"
        SELECT
            COALESCE(SUM(xp_earned), 0) AS xp_today,
            COUNT(CASE WHEN learned_at >= $2 THEN 1 END) AS lessons_today,
            COUNT(CASE WHEN mastered_at >= $2 THEN 1 END) AS quizzes_today
        FROM user_progress
        WHERE user_id = $1 AND (learned_at >= $2 OR mastered_at >= $2 OR discovered_at >= $2)
        "#,
    )
    .bind(user_id)
    .bind(today_start)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (xp_today, lessons, quizzes) = today_stats.unwrap_or((0, 0, 0));

    Ok(DailyGoalResponse {
        daily_xp_goal,
        xp_earned_today: xp_today as i32,
        goal_met: xp_today as i32 >= daily_xp_goal,
        lessons_today: lessons as i32,
        quizzes_today: quizzes as i32,
    })
}

/// PUT /api/v1/users/me/daily-goal — update daily goal.
pub async fn update_daily_goal(
    pool: &PgPool,
    user_id: Uuid,
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

    sqlx::query(
        r#"
        INSERT INTO user_settings (user_id, daily_xp_goal)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET daily_xp_goal = $2
        "#,
    )
    .bind(user_id)
    .bind(payload.daily_xp_goal)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(UpdateDailyGoalResponse {
        daily_xp_goal: payload.daily_xp_goal,
        updated: true,
    })
}

/// GET /api/v1/users/me/milestones — get user milestones.
pub async fn get_milestones(pool: &PgPool, user_id: Uuid) -> Result<MilestonesResponse, AppError> {
    let rows = sqlx::query_as::<_, MilestoneRow>(
        r#"
        SELECT m.id, m.milestone_type, m.title, m.description,
               um.achieved_at, COALESCE(um.progress_current, 0) AS progress_current,
               m.progress_target
        FROM milestones m
        LEFT JOIN user_milestones um ON um.milestone_id = m.id AND um.user_id = $1
        ORDER BY m.display_order NULLS LAST, m.title
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total_achieved = rows.iter().filter(|r| r.achieved_at.is_some()).count() as i32;

    let milestones: Vec<MilestoneOut> = rows
        .into_iter()
        .map(|r| MilestoneOut {
            id: r.id,
            milestone_type: r.milestone_type,
            title: r.title,
            description: r.description,
            achieved_at: r.achieved_at,
            progress_current: r.progress_current,
            progress_target: r.progress_target,
            is_achieved: r.achieved_at.is_some(),
        })
        .collect();

    Ok(MilestonesResponse {
        milestones,
        total_achieved,
    })
}
