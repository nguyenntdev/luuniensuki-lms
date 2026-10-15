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
    let offset = params.offset.unwrap_or(0).max(0);

    // Get user rank and total count within friends scope (friends + self) using window functions
    let meta = sqlx::query_as::<_, (i64, i64)>(
        r#"
        WITH friends_scope AS (
            SELECT u.id AS user_id,
                   RANK() OVER (ORDER BY u.total_xp DESC, u.display_name ASC)::bigint AS rank,
                   COUNT(*) OVER ()::bigint AS total_count
            FROM users u
            WHERE u.id = $1
               OR u.id IN (SELECT to_user_id FROM friend_requests WHERE from_user_id = $1 AND status = 'accepted')
               OR u.id IN (SELECT from_user_id FROM friend_requests WHERE to_user_id = $1 AND status = 'accepted')
        )
        SELECT rank, total_count
        FROM friends_scope
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (user_rank, total) = match meta {
        Some((r, c)) => (Some(r as i32), c as i32),
        None => (None, 0),
    };

    // Get paginated ranked friends entries
    let rows = sqlx::query_as::<_, RankedLeaderboardRow>(
        r#"
        WITH friends_scope AS (
            SELECT u.id AS user_id, u.display_name, u.avatar_url, u.total_xp,
                   RANK() OVER (ORDER BY u.total_xp DESC, u.display_name ASC)::bigint AS rank
            FROM users u
            WHERE u.id = $1
               OR u.id IN (SELECT to_user_id FROM friend_requests WHERE from_user_id = $1 AND status = 'accepted')
               OR u.id IN (SELECT from_user_id FROM friend_requests WHERE to_user_id = $1 AND status = 'accepted')
        )
        SELECT user_id, display_name, avatar_url, total_xp, rank
        FROM friends_scope
        ORDER BY rank ASC, display_name ASC
        LIMIT $2 OFFSET $3
        "#,
    )
    .bind(user_id)
    .bind(limit as i64)
    .bind(offset as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let entries: Vec<LeaderboardEntry> = rows
        .into_iter()
        .map(|r| LeaderboardEntry {
            rank: r.rank as i32,
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

/// In-memory league tier definition.
#[derive(Debug, Clone, Copy)]
pub struct LeagueTierDef {
    pub id: Uuid,
    pub name: &'static str,
    pub tier: i32,
    pub min_xp: i32,
    pub max_xp: Option<i32>,
    pub icon_url: Option<&'static str>,
}

/// Constant in-memory domain definitions for league tiers.
pub const LEAGUE_TIERS: &[LeagueTierDef] = &[
    LeagueTierDef {
        id: Uuid::from_u128(1),
        name: "Bronze",
        tier: 1,
        min_xp: 0,
        max_xp: Some(500),
        icon_url: Some("/assets/leagues/bronze.svg"),
    },
    LeagueTierDef {
        id: Uuid::from_u128(2),
        name: "Silver",
        tier: 2,
        min_xp: 500,
        max_xp: Some(1500),
        icon_url: Some("/assets/leagues/silver.svg"),
    },
    LeagueTierDef {
        id: Uuid::from_u128(3),
        name: "Gold",
        tier: 3,
        min_xp: 1500,
        max_xp: Some(3000),
        icon_url: Some("/assets/leagues/gold.svg"),
    },
    LeagueTierDef {
        id: Uuid::from_u128(4),
        name: "Platinum",
        tier: 4,
        min_xp: 3000,
        max_xp: Some(6000),
        icon_url: Some("/assets/leagues/platinum.svg"),
    },
    LeagueTierDef {
        id: Uuid::from_u128(5),
        name: "Diamond",
        tier: 5,
        min_xp: 6000,
        max_xp: Some(10000),
        icon_url: Some("/assets/leagues/diamond.svg"),
    },
    LeagueTierDef {
        id: Uuid::from_u128(6),
        name: "Obsidian",
        tier: 6,
        min_xp: 10000,
        max_xp: None,
        icon_url: Some("/assets/leagues/obsidian.svg"),
    },
];

/// Helper to resolve a user's league tier definition based on total XP.
pub fn resolve_league_tier(total_xp: i32) -> &'static LeagueTierDef {
    LEAGUE_TIERS
        .iter()
        .rev()
        .find(|t| total_xp >= t.min_xp && t.max_xp.map_or(true, |max| total_xp < max))
        .unwrap_or(&LEAGUE_TIERS[0])
}

/// GET /api/v1/leagues — list leagues.
pub async fn list_leagues(pool: &PgPool) -> Result<Vec<LeagueOut>, AppError> {
    let mut leagues = Vec::with_capacity(LEAGUE_TIERS.len());
    for t in LEAGUE_TIERS {
        let count: (i64,) = sqlx::query_as(
            "SELECT COUNT(*) FROM users WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)",
        )
        .bind(t.min_xp)
        .bind(t.max_xp)
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        leagues.push(LeagueOut {
            id: t.id,
            name: t.name.to_string(),
            tier: t.tier,
            min_xp: t.min_xp,
            max_xp: t.max_xp,
            icon_url: t.icon_url.map(|s| s.to_string()),
            member_count: count.0 as i32,
        });
    }

    Ok(leagues)
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

    let tier_def = resolve_league_tier(user_xp.0);

    // Rank within league
    let rank: (i64,) = sqlx::query_as(
        r#"
        SELECT COUNT(*) + 1
        FROM users
        WHERE total_xp >= $1 AND total_xp > $2
          AND (($3::int IS NULL) OR total_xp < $3)
        "#,
    )
    .bind(tier_def.min_xp)
    .bind(user_xp.0)
    .bind(tier_def.max_xp)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Next league
    let next_tier = LEAGUE_TIERS.iter().find(|t| t.tier == tier_def.tier + 1);
    let xp_to_next = next_tier.map(|n| (n.min_xp - user_xp.0).max(0));

    // Member count for this league
    let member_count: (i64,) = sqlx::query_as(
        r#"
        SELECT COUNT(*)
        FROM users
        WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)
        "#,
    )
    .bind(tier_def.min_xp)
    .bind(tier_def.max_xp)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(UserLeagueOut {
        league: Some(LeagueOut {
            id: tier_def.id,
            name: tier_def.name.to_string(),
            tier: tier_def.tier,
            min_xp: tier_def.min_xp,
            max_xp: tier_def.max_xp,
            icon_url: tier_def.icon_url.map(|s| s.to_string()),
            member_count: member_count.0 as i32,
        }),
        rank_in_league: rank.0 as i32,
        xp_to_next_league: xp_to_next,
        promotion_zone: rank.0 <= 3,
        demotion_zone: false,
    })
}

/// GET /api/v1/leagues/{league_id} — league detail.
pub async fn get_league_detail(
    pool: &PgPool,
    league_id: Uuid,
) -> Result<LeagueDetailOut, AppError> {
    let tier_def = LEAGUE_TIERS
        .iter()
        .find(|t| t.id == league_id)
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
        ORDER BY total_xp DESC, display_name ASC
        LIMIT 50
        "#,
    )
    .bind(tier_def.min_xp)
    .bind(tier_def.max_xp)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total_members: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM users WHERE total_xp >= $1 AND ($2::int IS NULL OR total_xp < $2)",
    )
    .bind(tier_def.min_xp)
    .bind(tier_def.max_xp)
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
        id: tier_def.id,
        name: tier_def.name.to_string(),
        tier: tier_def.tier,
        min_xp: tier_def.min_xp,
        max_xp: tier_def.max_xp,
        icon_url: tier_def.icon_url.map(|s| s.to_string()),
        members: member_entries,
        total_members: total_members.0 as i32,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xp_to_level_progression() {
        assert_eq!(xp_to_level(0), 1);
        assert_eq!(xp_to_level(50), 1);
        assert_eq!(xp_to_level(99), 1);
        assert_eq!(xp_to_level(100), 2);
        assert_eq!(xp_to_level(299), 2);
        assert_eq!(xp_to_level(300), 3);
        assert_eq!(xp_to_level(599), 3);
        assert_eq!(xp_to_level(600), 4);
    }

    #[test]
    fn test_league_tiers_constant_definitions() {
        assert_eq!(LEAGUE_TIERS.len(), 6);
        assert_eq!(LEAGUE_TIERS[0].name, "Bronze");
        assert_eq!(LEAGUE_TIERS[1].name, "Silver");
        assert_eq!(LEAGUE_TIERS[2].name, "Gold");
        assert_eq!(LEAGUE_TIERS[3].name, "Platinum");
        assert_eq!(LEAGUE_TIERS[4].name, "Diamond");
        assert_eq!(LEAGUE_TIERS[5].name, "Obsidian");

        assert_eq!(resolve_league_tier(0).name, "Bronze");
        assert_eq!(resolve_league_tier(499).name, "Bronze");
        assert_eq!(resolve_league_tier(500).name, "Silver");
        assert_eq!(resolve_league_tier(1500).name, "Gold");
        assert_eq!(resolve_league_tier(3000).name, "Platinum");
        assert_eq!(resolve_league_tier(6000).name, "Diamond");
        assert_eq!(resolve_league_tier(10000).name, "Obsidian");
        assert_eq!(resolve_league_tier(999999).name, "Obsidian");
    }
}
