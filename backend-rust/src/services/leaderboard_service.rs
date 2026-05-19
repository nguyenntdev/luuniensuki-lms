//! Leaderboard & League business logic.
//!
//! Phase 9 (Tasks 10.1–10.2): Leaderboards & Leagues migration.

use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::leaderboard::*;

/// Calculate level from XP (simple formula matching Python).
fn xp_to_level(xp: i32) -> i32 {
    // Each level requires 100 XP more than the previous
    // Level 1: 0-99, Level 2: 100-299, Level 3: 300-599, etc.
    let mut level = 1;
    let mut threshold = 100;
    let mut total = 0;
    loop {
        total += threshold;
        if xp < total {
            break;
        }
        level += 1;
        threshold += 100;
    }
    level
}

/// GET /api/v1/leaderboard — global leaderboard.
pub async fn get_leaderboard(
    pool: &PgPool,
    user_id: Uuid,
    params: &LeaderboardQuery,
) -> Result<LeaderboardResponse, AppError> {
    let limit = params.limit.unwrap_or(50).min(100);
    let offset = params.offset.unwrap_or(0).max(0);

    let rows = sqlx::query_as::<_, LeaderboardRow>(
        r#"
        SELECT id AS user_id, display_name, avatar_url, total_xp
        FROM users
        WHERE total_xp > 0
        ORDER BY total_xp DESC, display_name ASC
        LIMIT $1 OFFSET $2
        "#,
    )
    .bind(limit as i64)
    .bind(offset as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users WHERE total_xp > 0")
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // Get user's rank
    let user_rank: Option<(i64,)> = sqlx::query_as(
        r#"
        SELECT COUNT(*) + 1
        FROM users
        WHERE total_xp > (SELECT total_xp FROM users WHERE id = $1)
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let entries: Vec<LeaderboardEntry> = rows
        .into_iter()
        .enumerate()
        .map(|(i, r)| LeaderboardEntry {
            rank: (offset + i as i32 + 1),
            user_id: r.user_id,
            display_name: r.display_name,
            avatar_url: r.avatar_url,
            total_xp: r.total_xp,
            level: xp_to_level(r.total_xp),
        })
        .collect();

    Ok(LeaderboardResponse {
        entries,
        total: total.0 as i32,
        user_rank: user_rank.map(|r| r.0 as i32),
    })
}

/// GET /api/v1/leaderboard/friends — friends leaderboard.
pub async fn get_friends_leaderboard(
    pool: &PgPool,
    user_id: Uuid,
    params: &LeaderboardQuery,
) -> Result<LeaderboardResponse, AppError> {
    let limit = params.limit.unwrap_or(50).min(100);

    // Get friends + self
    let rows = sqlx::query_as::<_, LeaderboardRow>(
        r#"
        SELECT u.id AS user_id, u.display_name, u.avatar_url, u.total_xp
        FROM users u
        WHERE u.id = $1
           OR u.id IN (SELECT friend_id FROM friendships WHERE user_id = $1 AND status = 'accepted')
           OR u.id IN (SELECT user_id FROM friendships WHERE friend_id = $1 AND status = 'accepted')
        ORDER BY u.total_xp DESC, u.display_name ASC
        LIMIT $2
        "#,
    )
    .bind(user_id)
    .bind(limit as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total = rows.len() as i32;
    let user_rank = rows.iter().position(|r| r.user_id == user_id).map(|i| i as i32 + 1);

    let entries: Vec<LeaderboardEntry> = rows
        .into_iter()
        .enumerate()
        .map(|(i, r)| LeaderboardEntry {
            rank: (i as i32 + 1),
            user_id: r.user_id,
            display_name: r.display_name,
            avatar_url: r.avatar_url,
            total_xp: r.total_xp,
            level: xp_to_level(r.total_xp),
        })
        .collect();

    Ok(LeaderboardResponse {
        entries,
        total,
        user_rank,
    })
}

/// GET /api/v1/leagues — list leagues.
pub async fn list_leagues(pool: &PgPool) -> Result<Vec<LeagueOut>, AppError> {
    let rows = sqlx::query_as::<_, LeagueRow>(
        r#"
        SELECT id, name, tier, min_xp, max_xp, icon_url,
               (SELECT COUNT(*)::int FROM users WHERE total_xp >= l.min_xp AND (l.max_xp IS NULL OR total_xp < l.max_xp)) AS member_count
        FROM leagues l
        ORDER BY tier ASC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows
        .into_iter()
        .map(|r| LeagueOut {
            id: r.id,
            name: r.name,
            tier: r.tier,
            min_xp: r.min_xp,
            max_xp: r.max_xp,
            icon_url: r.icon_url,
            member_count: r.member_count,
        })
        .collect())
}

/// GET /api/v1/leagues/me — user's current league.
pub async fn get_user_league(pool: &PgPool, user_id: Uuid) -> Result<UserLeagueOut, AppError> {
    // Get user's XP
    let user_xp: (i32,) = sqlx::query_as("SELECT total_xp FROM users WHERE id = $1")
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .unwrap_or((0,));

    // Find user's league
    let league = sqlx::query_as::<_, LeagueRow>(
        r#"
        SELECT id, name, tier, min_xp, max_xp, icon_url, 0 AS member_count
        FROM leagues
        WHERE min_xp <= $1 AND (max_xp IS NULL OR max_xp > $1)
        ORDER BY tier DESC
        LIMIT 1
        "#,
    )
    .bind(user_xp.0)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match league {
        Some(l) => {
            // Rank within league
            let rank: (i64,) = sqlx::query_as(
                r#"
                SELECT COUNT(*) + 1
                FROM users
                WHERE total_xp >= $1 AND total_xp > $2
                  AND (($3::int IS NULL) OR total_xp < $3)
                "#,
            )
            .bind(l.min_xp)
            .bind(user_xp.0)
            .bind(l.max_xp)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            // Next league
            let next_league_min: Option<(i32,)> = sqlx::query_as(
                "SELECT min_xp FROM leagues WHERE tier = $1 + 1 LIMIT 1",
            )
            .bind(l.tier)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            let xp_to_next = next_league_min.map(|n| (n.0 - user_xp.0).max(0));

            // Member count for this league
            let member_count: (i64,) = sqlx::query_as(
                r#"
                SELECT COUNT(*)
                FROM users
                WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)
                "#,
            )
            .bind(l.min_xp)
            .bind(l.max_xp)
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

            Ok(UserLeagueOut {
                league: Some(LeagueOut {
                    id: l.id,
                    name: l.name,
                    tier: l.tier,
                    min_xp: l.min_xp,
                    max_xp: l.max_xp,
                    icon_url: l.icon_url,
                    member_count: member_count.0 as i32,
                }),
                rank_in_league: rank.0 as i32,
                xp_to_next_league: xp_to_next,
                promotion_zone: rank.0 <= 3,
                demotion_zone: false, // Simplified
            })
        }
        None => Ok(UserLeagueOut {
            league: None,
            rank_in_league: 0,
            xp_to_next_league: None,
            promotion_zone: false,
            demotion_zone: false,
        }),
    }
}

/// GET /api/v1/leagues/{league_id} — league detail.
pub async fn get_league_detail(pool: &PgPool, league_id: Uuid) -> Result<LeagueDetailOut, AppError> {
    let league = sqlx::query_as::<_, LeagueRow>(
        "SELECT id, name, tier, min_xp, max_xp, icon_url, 0 AS member_count FROM leagues WHERE id = $1",
    )
    .bind(league_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "League not found".to_string(),
    })?;

    // Get members in this league
    let members = sqlx::query_as::<_, LeaderboardRow>(
        r#"
        SELECT id AS user_id, display_name, avatar_url, total_xp
        FROM users
        WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)
        ORDER BY total_xp DESC
        LIMIT 50
        "#,
    )
    .bind(league.min_xp)
    .bind(league.max_xp)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total_members: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM users WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)",
    )
    .bind(league.min_xp)
    .bind(league.max_xp)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let member_entries: Vec<LeaderboardEntry> = members
        .into_iter()
        .enumerate()
        .map(|(i, r)| LeaderboardEntry {
            rank: (i as i32 + 1),
            user_id: r.user_id,
            display_name: r.display_name,
            avatar_url: r.avatar_url,
            total_xp: r.total_xp,
            level: xp_to_level(r.total_xp),
        })
        .collect();

    Ok(LeagueDetailOut {
        id: league.id,
        name: league.name,
        tier: league.tier,
        min_xp: league.min_xp,
        max_xp: league.max_xp,
        icon_url: league.icon_url,
        members: member_entries,
        total_members: total_members.0 as i32,
    })
}
