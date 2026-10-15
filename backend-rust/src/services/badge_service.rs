//! Badge, Quest, and Achievement business logic.
//!
//! Phase 7 (Tasks 8.1–8.3): Badges, Quests, Achievements migration.

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::badge::*;

/// POST /api/v1/badges/{badge_id}/award — award badge (idempotent).
pub async fn award_badge(
    pool: &PgPool,
    badge_id: Uuid,
    user_id: Uuid,
) -> Result<AwardBadgeResponse, AppError> {
    // Verify badge exists
    let _badge: (Uuid,) = sqlx::query_as("SELECT id FROM badges WHERE id = $1")
        .bind(badge_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or_else(|| AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Badge not found".to_string(),
        })?;

    // Check if already awarded
    let existing = sqlx::query_as::<_, UserBadgeRow>(
        "SELECT badge_id, awarded_at FROM user_badges WHERE user_id = $1 AND badge_id = $2",
    )
    .bind(user_id)
    .bind(badge_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some(existing_badge) = existing {
        return Ok(AwardBadgeResponse {
            badge_id,
            user_id,
            awarded: false,
            already_owned: true,
            awarded_at: Some(existing_badge.awarded_at),
        });
    }

    let now = Utc::now();
    sqlx::query(
        "INSERT INTO user_badges (id, user_id, badge_id, awarded_at) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(badge_id)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(AwardBadgeResponse {
        badge_id,
        user_id,
        awarded: true,
        already_owned: false,
        awarded_at: Some(now),
    })
}

/// GET /api/v1/quests — list quests.
pub async fn list_quests(pool: &PgPool, _user_id: Uuid) -> Result<Vec<QuestOut>, AppError> {
    let rows = sqlx::query_as::<_, QuestRow>(
        r#"
        SELECT id, slug, name AS title, description,
               COALESCE(category, 'general') AS quest_type,
               COALESCE((SELECT SUM(qr.amount)::int FROM quest_rewards qr
                         WHERE qr.quest_id = quests.id AND qr.reward_type = 'xp'), 0) AS xp_reward,
               NULL::jsonb AS requirements, is_active
        FROM quests
        WHERE is_active = true
        ORDER BY display_order NULLS LAST, name
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| QuestOut {
            id: r.id,
            slug: r.slug,
            title: r.title,
            description: r.description,
            quest_type: r.quest_type,
            xp_reward: r.xp_reward,
            requirements: r.requirements,
            is_active: r.is_active,
        })
        .collect())
}

/// GET /api/v1/quests/{quest_slug} — quest detail.
pub async fn get_quest_detail(
    pool: &PgPool,
    quest_slug: &str,
    user_id: Uuid,
) -> Result<QuestDetailOut, AppError> {
    let quest = sqlx::query_as::<_, QuestRow>(
        "SELECT id, slug, name AS title, description, COALESCE(category, 'general') AS quest_type, COALESCE((SELECT SUM(qr.amount)::int FROM quest_rewards qr WHERE qr.quest_id = quests.id AND qr.reward_type = 'xp'), 0) AS xp_reward, NULL::jsonb AS requirements, is_active FROM quests WHERE slug = $1",
    )
    .bind(quest_slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Quest not found".to_string(),
    })?;

    // Get steps
    let steps = sqlx::query_as::<_, QuestStepRow>(
        "SELECT display_order AS step_number, description, 1 AS target_count FROM quest_steps WHERE quest_id = $1 ORDER BY display_order",
    )
    .bind(quest.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Get user progress
    let progress = sqlx::query_as::<_, QuestProgressRow>(
        "SELECT started_at, completed_at, 1 AS current_step FROM quest_progress WHERE user_id = $1 AND quest_id = $2",
    )
    .bind(user_id)
    .bind(quest.id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(QuestDetailOut {
        id: quest.id,
        slug: quest.slug,
        title: quest.title,
        description: quest.description,
        quest_type: quest.quest_type,
        xp_reward: quest.xp_reward,
        requirements: quest.requirements,
        steps: steps
            .into_iter()
            .map(|s| QuestStepOut {
                step_number: s.step_number,
                description: s.description,
                target_count: s.target_count,
            })
            .collect(),
        user_progress: progress.map(|p| QuestUserProgress {
            started_at: p.started_at,
            completed_at: p.completed_at,
            current_step: p.current_step,
            is_completed: p.completed_at.is_some(),
        }),
    })
}

/// POST /api/v1/quests/{quest_slug}/start — start a quest.
pub async fn start_quest(
    pool: &PgPool,
    quest_slug: &str,
    user_id: Uuid,
) -> Result<QuestStartResponse, AppError> {
    let quest = sqlx::query_as::<_, QuestRow>(
        "SELECT id, slug, name AS title, description, COALESCE(category, 'general') AS quest_type, COALESCE((SELECT SUM(qr.amount)::int FROM quest_rewards qr WHERE qr.quest_id = quests.id AND qr.reward_type = 'xp'), 0) AS xp_reward, NULL::jsonb AS requirements, is_active FROM quests WHERE slug = $1",
    )
    .bind(quest_slug)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Quest not found".to_string(),
    })?;

    // Check if already started
    let existing = sqlx::query_as::<_, QuestProgressRow>(
        "SELECT started_at, completed_at, 1 AS current_step FROM quest_progress WHERE user_id = $1 AND quest_id = $2",
    )
    .bind(user_id)
    .bind(quest.id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some(p) = existing {
        return Ok(QuestStartResponse {
            quest_id: quest.id,
            quest_slug: quest.slug,
            started: false,
            already_started: true,
            started_at: p.started_at,
        });
    }

    let now = Utc::now();
    sqlx::query(
        "INSERT INTO quest_progress (id, user_id, quest_id, started_at, status) VALUES ($1, $2, $3, $4, 'in_progress')",
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(quest.id)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(QuestStartResponse {
        quest_id: quest.id,
        quest_slug: quest.slug,
        started: true,
        already_started: false,
        started_at: Some(now),
    })
}

/// GET /api/v1/users/me/quest-summary — quest summary.
pub async fn get_quest_summary(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<QuestSummaryResponse, AppError> {
    let stats: Option<(i64, i64, i64)> = sqlx::query_as(
        r#"
        SELECT
            COUNT(CASE WHEN qp.completed_at IS NULL THEN 1 END) AS active,
            COUNT(CASE WHEN qp.completed_at IS NOT NULL THEN 1 END) AS completed,
            COALESCE(SUM(CASE WHEN qp.completed_at IS NOT NULL THEN COALESCE(qr.xp, 0) ELSE 0 END), 0)::bigint AS total_xp
        FROM quest_progress qp
        LEFT JOIN (
            SELECT quest_id, SUM(amount) AS xp
            FROM quest_rewards
            WHERE reward_type = 'xp'
            GROUP BY quest_id
        ) qr ON qr.quest_id = qp.quest_id
        WHERE qp.user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (active, completed, total_xp) = stats.unwrap_or((0, 0, 0));

    Ok(QuestSummaryResponse {
        active_quests: active as i32,
        completed_quests: completed as i32,
        total_quest_xp: total_xp as i32,
    })
}

/// GET /api/v1/quests/weekly — weekly quests.
pub async fn get_weekly_quests(pool: &PgPool, _user_id: Uuid) -> Result<Vec<QuestOut>, AppError> {
    let rows = sqlx::query_as::<_, QuestRow>(
        r#"
        SELECT id, slug, name AS title, description,
               COALESCE(category, 'general') AS quest_type,
               COALESCE((SELECT SUM(qr.amount)::int FROM quest_rewards qr
                         WHERE qr.quest_id = quests.id AND qr.reward_type = 'xp'), 0) AS xp_reward,
               NULL::jsonb AS requirements, is_active
        FROM quests
        WHERE is_active = true AND category = 'weekly'
        ORDER BY display_order NULLS LAST, name
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| QuestOut {
            id: r.id,
            slug: r.slug,
            title: r.title,
            description: r.description,
            quest_type: r.quest_type,
            xp_reward: r.xp_reward,
            requirements: r.requirements,
            is_active: r.is_active,
        })
        .collect())
}

/// GET /api/v1/missions/daily — daily missions.
pub async fn get_daily_missions(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<DailyMissionsResponse, AppError> {
    let rows = sqlx::query_as::<_, DailyMissionRow>(
        r#"
        SELECT dm.id, dm.name AS title, dm.description, dm.mission_type::text AS mission_type,
               dm.target_count, COALESCE(udm.current_count, 0) AS current_count,
               dm.xp_reward,
               COALESCE(udm.is_completed, false) AS is_completed,
               NULL::timestamptz AS expires_at
        FROM daily_missions dm
        LEFT JOIN user_daily_missions udm ON udm.mission_id = dm.id AND udm.user_id = $1
        WHERE dm.is_active = true
        ORDER BY dm.name
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let completed_count = rows.iter().filter(|r| r.is_completed).count() as i32;
    let total_count = rows.len() as i32;

    let missions: Vec<DailyMissionOut> = rows
        .into_iter()
        .map(|r| DailyMissionOut {
            id: r.id,
            title: r.title,
            description: r.description,
            mission_type: r.mission_type,
            target_count: r.target_count,
            current_count: r.current_count,
            xp_reward: r.xp_reward,
            is_completed: r.is_completed,
            expires_at: r.expires_at,
        })
        .collect();

    Ok(DailyMissionsResponse {
        missions,
        completed_count,
        total_count,
    })
}
