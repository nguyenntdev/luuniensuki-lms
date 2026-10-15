//! Leaderboard & League DTOs.
//!
//! Phase 9 (Tasks 10.1–10.2): Leaderboards & Leagues migration.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Leaderboard DTOs
// ---------------------------------------------------------------------------

/// A single entry on the leaderboard.
#[derive(Debug, Serialize)]
pub struct LeaderboardEntry {
    pub rank: i32,
    pub user_id: Uuid,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub total_xp: i32,
    pub level: i32,
}

/// Query params for GET /api/v1/leaderboard.
#[derive(Debug, Deserialize)]
pub struct LeaderboardQuery {
    pub limit: Option<i32>,
    pub offset: Option<i32>,
    pub timeframe: Option<String>, // "all", "weekly", "monthly"
}

/// Response for GET /api/v1/leaderboard.
#[derive(Debug, Serialize)]
pub struct LeaderboardResponse {
    pub entries: Vec<LeaderboardEntry>,
    pub total: i32,
    pub user_rank: Option<i32>,
}

// ---------------------------------------------------------------------------
// League DTOs
// ---------------------------------------------------------------------------

/// A league in list responses.
#[derive(Debug, Serialize)]
pub struct LeagueOut {
    pub id: Uuid,
    pub name: String,
    pub tier: i32,
    pub min_xp: i32,
    pub max_xp: Option<i32>,
    pub icon_url: Option<String>,
    pub member_count: i32,
}

/// User's current league info.
#[derive(Debug, Serialize)]
pub struct UserLeagueOut {
    pub league: Option<LeagueOut>,
    pub rank_in_league: i32,
    pub xp_to_next_league: Option<i32>,
    pub promotion_zone: bool,
    pub demotion_zone: bool,
}

/// League detail with members.
#[derive(Debug, Serialize)]
pub struct LeagueDetailOut {
    pub id: Uuid,
    pub name: String,
    pub tier: i32,
    pub min_xp: i32,
    pub max_xp: Option<i32>,
    pub icon_url: Option<String>,
    pub members: Vec<LeaderboardEntry>,
    pub total_members: i32,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct LeaderboardRow {
    pub user_id: Uuid,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub total_xp: i32,
}

#[derive(Debug, sqlx::FromRow)]
pub struct RankedLeaderboardRow {
    pub user_id: Uuid,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub total_xp: i32,
    pub rank: i64,
}

#[allow(dead_code)]
#[derive(Debug, sqlx::FromRow)]
pub struct LeagueRow {
    pub id: Uuid,
    pub name: String,
    pub tier: i32,
    pub min_xp: i32,
    pub max_xp: Option<i32>,
    pub icon_url: Option<String>,
    pub member_count: i32,
}

#[allow(dead_code)]
#[derive(Debug, sqlx::FromRow)]
pub struct UserLeagueRow {
    pub league_id: Option<Uuid>,
    pub league_name: Option<String>,
    pub tier: Option<i32>,
    pub min_xp: Option<i32>,
    pub max_xp: Option<i32>,
    pub icon_url: Option<String>,
    pub rank_in_league: i32,
}
