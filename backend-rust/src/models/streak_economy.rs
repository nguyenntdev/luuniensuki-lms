//! DTOs and database row types for the streak repair economy feature.
//!
//! Covers four mechanics:
//! - Streak Repair (Requirement 1, 2)
//! - Big Red Button (Requirement 3)
//! - Friend Streak (Requirement 4)
//! - Streak Comeback (Requirement 5)

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Payment method
// ---------------------------------------------------------------------------

/// Payment method for streak repair. Serialized as lowercase string.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
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
}

// ---------------------------------------------------------------------------
// Repair DTOs (Requirement 1)
// ---------------------------------------------------------------------------

/// POST /api/v1/users/me/streak/repair request body.
#[derive(Debug, Deserialize)]
pub struct RepairRequest {
    pub payment: PaymentMethod,
}

/// POST /api/v1/users/me/streak/repair response body.
#[derive(Debug, Serialize)]
pub struct RepairResponse {
    pub current_streak: i32,
    pub payment: String,
    pub repaired_at: DateTime<Utc>,
}

/// GET /api/v1/users/me/streak/repair-options response body.
#[derive(Debug, Serialize)]
pub struct RepairOptions {
    pub repair_available: bool,
    pub lost_at: Option<DateTime<Utc>>,
    pub expires_at: Option<DateTime<Utc>>,
    pub monthly_repairs_used: i32,
    pub monthly_repairs_limit: i32,
    pub hearts_required: i32,
    pub xp_required: i32,
    pub payment_options_available: Vec<String>,
}

// ---------------------------------------------------------------------------
// Friend Streak DTOs (Requirement 4)
// ---------------------------------------------------------------------------

/// Output row for a single friend streak.
#[derive(Debug, Serialize)]
pub struct FriendStreakOut {
    pub friend_id: Uuid,
    pub friend_display_name: String,
    pub friend_avatar_url: Option<String>,
    pub current_count: i32,
    pub longest_count: i32,
    pub is_alive: bool,
    pub last_increment_date: Option<NaiveDate>,
}

// ---------------------------------------------------------------------------
// BRB DTOs (Requirement 3)
// ---------------------------------------------------------------------------

/// POST /api/v1/admin/streak/big-red-button request body.
#[derive(Debug, Deserialize)]
pub struct BrbRequest {
    pub reason: String,
    pub duration_minutes: i32,
    pub effective_from: DateTime<Utc>,
}

/// POST /api/v1/admin/streak/big-red-button response body.
#[derive(Debug, Serialize)]
pub struct BrbResult {
    pub affected_users: i64,
    pub event_id: Uuid,
}

// ---------------------------------------------------------------------------
// Comeback DTOs (Requirement 5)
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize)]
pub struct ActiveComebackBonus {
    pub multiplier: f64,
    pub started_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct ComebackStatus {
    pub phoenix_eligible: bool,
    pub consecutive_days_active: i32,
    pub days_required: i32,
    pub active_bonus: Option<ActiveComebackBonus>,
}

// ---------------------------------------------------------------------------
// Admin grant request DTO
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct AdminGrantRepairRequest {
    pub reason: String,
}

// ---------------------------------------------------------------------------
// Database row types
// ---------------------------------------------------------------------------

/// Row from `user_streak_history`.
#[derive(Debug, sqlx::FromRow)]
pub struct StreakHistoryRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub streak_value: i32,
    pub streak_started_at: DateTime<Utc>,
    pub streak_ended_at: DateTime<Utc>,
    pub phoenix_awarded: bool,
}

/// Row from `streak_repair_events`.
#[derive(Debug, sqlx::FromRow)]
pub struct StreakRepairEventRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub payment_method: String,
    pub payment_amount: i32,
    pub streak_before_loss: i32,
    pub streak_restored_to: i32,
    pub lost_at: DateTime<Utc>,
    pub repaired_at: DateTime<Utc>,
    pub idempotency_key: Option<String>,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
}

/// Row from `friend_streaks` joined with the friend's user row.
#[derive(Debug, sqlx::FromRow)]
pub struct FriendStreakJoinRow {
    pub friend_id: Uuid,
    pub friend_display_name: String,
    pub friend_avatar_url: Option<String>,
    pub current_count: i32,
    pub longest_count: i32,
    pub last_increment_date: Option<NaiveDate>,
}

/// Row from `streak_protection_events` (BRB events).
#[derive(Debug, sqlx::FromRow)]
pub struct StreakProtectionEventRow {
    pub event_id: Uuid,
    pub reason: String,
    pub effective_from: DateTime<Utc>,
    pub effective_to: DateTime<Utc>,
    pub applied_at: DateTime<Utc>,
    pub affected_users: i64,
}

/// Paginated wrapper for admin event listings.
#[derive(Debug, Serialize)]
pub struct PaginatedRepairEvents {
    pub items: Vec<RepairEventOut>,
    pub page: i32,
    pub per_page: i32,
    pub total: i64,
}

#[derive(Debug, Serialize)]
pub struct RepairEventOut {
    pub id: Uuid,
    pub user_id: Uuid,
    pub payment_method: String,
    pub payment_amount: i32,
    pub streak_before_loss: i32,
    pub streak_restored_to: i32,
    pub lost_at: DateTime<Utc>,
    pub repaired_at: DateTime<Utc>,
    pub notes: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct PaginatedBrbEvents {
    pub items: Vec<BrbEventOut>,
    pub page: i32,
    pub per_page: i32,
    pub total: i64,
}

#[derive(Debug, Serialize)]
pub struct BrbEventOut {
    pub event_id: Uuid,
    pub reason: String,
    pub effective_from: DateTime<Utc>,
    pub effective_to: DateTime<Utc>,
    pub applied_at: DateTime<Utc>,
    pub affected_users: i64,
}
