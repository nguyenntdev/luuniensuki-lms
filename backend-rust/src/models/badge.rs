//! Badge, Quest, and Achievement DTOs.
//!
//! Phase 7 (Tasks 8.1–8.3): Badges, Quests, Achievements migration.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Badge DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/badges/{badge_id}/award.
#[derive(Debug, Deserialize)]
pub struct AwardBadgeRequest {
    pub reason: Option<String>,
}

/// Response for POST /api/v1/badges/{badge_id}/award.
#[derive(Debug, Serialize)]
pub struct AwardBadgeResponse {
    pub badge_id: Uuid,
    pub user_id: Uuid,
    pub awarded: bool,
    pub already_owned: bool,
    pub awarded_at: Option<DateTime<Utc>>,
}

// ---------------------------------------------------------------------------
// Quest DTOs
// ---------------------------------------------------------------------------

/// A quest in list responses.
#[derive(Debug, Serialize)]
pub struct QuestOut {
    pub id: Uuid,
    pub slug: String,
    pub title: String,
    pub description: Option<String>,
    pub quest_type: String,
    pub xp_reward: i32,
    pub requirements: Option<serde_json::Value>,
    pub is_active: bool,
}

/// Quest detail response.
#[derive(Debug, Serialize)]
pub struct QuestDetailOut {
    pub id: Uuid,
    pub slug: String,
    pub title: String,
    pub description: Option<String>,
    pub quest_type: String,
    pub xp_reward: i32,
    pub requirements: Option<serde_json::Value>,
    pub steps: Vec<QuestStepOut>,
    pub user_progress: Option<QuestUserProgress>,
}

/// A step in a quest.
#[derive(Debug, Serialize)]
pub struct QuestStepOut {
    pub step_number: i32,
    pub description: String,
    pub target_count: i32,
}

/// User's progress on a quest.
#[derive(Debug, Serialize)]
pub struct QuestUserProgress {
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub current_step: i32,
    pub is_completed: bool,
}

/// Response for POST /api/v1/quests/{quest_slug}/start.
#[derive(Debug, Serialize)]
pub struct QuestStartResponse {
    pub quest_id: Uuid,
    pub quest_slug: String,
    pub started: bool,
    pub already_started: bool,
    pub started_at: Option<DateTime<Utc>>,
}

/// Quest summary for GET /api/v1/users/me/quest-summary.
#[derive(Debug, Serialize)]
pub struct QuestSummaryResponse {
    pub active_quests: i32,
    pub completed_quests: i32,
    pub total_quest_xp: i32,
}

/// A daily mission.
#[derive(Debug, Serialize)]
pub struct DailyMissionOut {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub mission_type: String,
    pub target_count: i32,
    pub current_count: i32,
    pub xp_reward: i32,
    pub is_completed: bool,
    pub expires_at: Option<DateTime<Utc>>,
}

/// Response for GET /api/v1/missions/daily.
#[derive(Debug, Serialize)]
pub struct DailyMissionsResponse {
    pub missions: Vec<DailyMissionOut>,
    pub completed_count: i32,
    pub total_count: i32,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct QuestRow {
    pub id: Uuid,
    pub slug: String,
    pub title: String,
    pub description: Option<String>,
    pub quest_type: String,
    pub xp_reward: i32,
    pub requirements: Option<serde_json::Value>,
    pub is_active: bool,
}

#[derive(Debug, sqlx::FromRow)]
pub struct QuestStepRow {
    pub step_number: i32,
    pub description: String,
    pub target_count: i32,
}

#[derive(Debug, sqlx::FromRow)]
pub struct QuestProgressRow {
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub current_step: i32,
}

#[derive(Debug, sqlx::FromRow)]
pub struct UserBadgeRow {
    pub badge_id: Uuid,
    pub awarded_at: DateTime<Utc>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct DailyMissionRow {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub mission_type: String,
    pub target_count: i32,
    pub current_count: i32,
    pub xp_reward: i32,
    pub is_completed: bool,
    pub expires_at: Option<DateTime<Utc>>,
}
