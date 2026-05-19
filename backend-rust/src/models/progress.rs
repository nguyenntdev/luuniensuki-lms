//! Progress, Streak, Hearts, Daily Goal, and Milestone DTOs.
//!
//! Phase 6 (Tasks 7.1–7.3): Progress & Streaks migration.
//!
//! Fixed to match actual production database schema.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Progress DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/progress/unlock.
#[derive(Debug, Deserialize)]
pub struct UnlockMotifRequest {
    pub motif_id: Uuid,
}

/// Response for POST /api/v1/progress/unlock.
#[derive(Debug, Serialize)]
pub struct UnlockMotifResponse {
    pub motif_id: Uuid,
    pub status: String,
    pub discovered_at: DateTime<Utc>,
    pub xp_awarded: i32,
}

// ---------------------------------------------------------------------------
// Streak DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/users/me/streak.
#[derive(Debug, Serialize)]
pub struct StreakResponse {
    pub current_streak: i32,
    pub longest_streak: i32,
    pub last_activity_date: Option<String>,
    pub streak_alive: bool,
    pub freeze_available: bool,
}

/// Request body for POST /api/v1/users/me/streak.
#[derive(Debug, Deserialize)]
pub struct StreakHeartbeatRequest {
    pub activity_type: Option<String>,
}

/// Response for POST /api/v1/users/me/streak (heartbeat).
#[derive(Debug, Serialize)]
pub struct StreakHeartbeatResponse {
    pub current_streak: i32,
    pub longest_streak: i32,
    pub streak_extended: bool,
    pub last_activity_date: String,
}

// ---------------------------------------------------------------------------
// Hearts DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/users/me/hearts.
#[derive(Debug, Serialize)]
pub struct HeartsResponse {
    pub hearts: i32,
    pub max_hearts: i32,
    pub next_regen_at: Option<DateTime<Utc>>,
    pub is_unlimited: bool,
}

/// Request body for POST /api/v1/users/me/hearts.
#[derive(Debug, Deserialize)]
pub struct HeartsActionRequest {
    pub action: String, // "spend" or "refill"
    pub amount: Option<i32>,
}

/// Response for POST /api/v1/users/me/hearts.
#[derive(Debug, Serialize)]
pub struct HeartsActionResponse {
    pub hearts: i32,
    pub max_hearts: i32,
    pub action_performed: String,
}

// ---------------------------------------------------------------------------
// Daily Goal DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/users/me/daily-goal.
#[derive(Debug, Serialize)]
pub struct DailyGoalResponse {
    pub daily_xp_goal: i32,
    pub xp_earned_today: i32,
    pub goal_met: bool,
    pub lessons_today: i32,
    pub quizzes_today: i32,
}

/// Request body for PUT /api/v1/users/me/daily-goal.
#[derive(Debug, Deserialize)]
pub struct UpdateDailyGoalRequest {
    pub daily_xp_goal: i32,
}

/// Response for PUT /api/v1/users/me/daily-goal.
#[derive(Debug, Serialize)]
pub struct UpdateDailyGoalResponse {
    pub daily_xp_goal: i32,
    pub updated: bool,
}

// ---------------------------------------------------------------------------
// Milestone DTOs
// ---------------------------------------------------------------------------

/// A single milestone.
#[derive(Debug, Serialize)]
pub struct MilestoneOut {
    pub id: Uuid,
    pub milestone_type: String,
    pub title: String,
    pub description: Option<String>,
    pub achieved_at: Option<DateTime<Utc>>,
    pub progress_current: i32,
    pub progress_target: i32,
    pub is_achieved: bool,
}

/// Response for GET /api/v1/users/me/milestones.
#[derive(Debug, Serialize)]
pub struct MilestonesResponse {
    pub milestones: Vec<MilestoneOut>,
    pub total_achieved: i32,
}

// ---------------------------------------------------------------------------
// DB Row types — match actual production schema
// ---------------------------------------------------------------------------

/// Streak data from `users` table.
#[derive(Debug, sqlx::FromRow)]
pub struct StreakRow {
    pub current_streak: i32,
    pub longest_streak: i32,
    pub streak_freezes: i32,
    pub last_active_at: Option<DateTime<Utc>>,
}

/// Hearts data from `user_hearts` table.
#[derive(Debug, sqlx::FromRow)]
pub struct HeartsRow {
    pub current_hearts: i32,
    pub max_hearts: i32,
    pub hearts_refill_at: Option<DateTime<Utc>>,
    pub unlimited_until: Option<DateTime<Utc>>,
}

/// Milestone data from `user_milestones` table.
#[derive(Debug, sqlx::FromRow)]
pub struct MilestoneRow {
    pub id: Uuid,
    pub milestone_type: String,
    pub achieved_at: DateTime<Utc>,
    pub context_data: Option<serde_json::Value>,
    pub celebrated: bool,
}
