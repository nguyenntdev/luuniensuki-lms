//! DTOs and SQLx row types for the streak-repair-economy feature.
//!
//! Spec: `.kiro/specs/streak-repair-economy/`
//!
//! Covers six new tables:
//! - `streak_repair_events`
//! - `streak_protection_events`
//! - `friend_streaks`
//! - `user_streak_history`
//! - `user_comeback_bonuses`
//! - `streak_insurance_subscriptions`

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Streak Repair
// ---------------------------------------------------------------------------

/// Request body for `POST /api/v1/users/me/streak/repair`.
#[derive(Debug, Deserialize)]
pub struct RepairRequest {
    pub payment: String, // "hearts" | "xp"
}

/// Response body for `POST /api/v1/users/me/streak/repair`.
#[derive(Debug, Serialize)]
pub struct RepairResponse {
    pub current_streak: i32,
    pub payment: String,
    pub repaired_at: DateTime<Utc>,
}

/// Response body for `GET /api/v1/users/me/streak/repair-options`.
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

/// Row of `streak_repair_events`.
#[derive(Debug, sqlx::FromRow, Serialize)]
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
    pub actor_user_id: Option<Uuid>,
    pub created_at: DateTime<Utc>,
}

/// Request body for `POST /api/v1/admin/users/:user_id/streak/grant-repair`.
#[derive(Debug, Deserialize)]
pub struct GrantRepairRequest {
    pub reason: String,
}

// ---------------------------------------------------------------------------
// Big Red Button (Protection events)
// ---------------------------------------------------------------------------

/// Request body for `POST /api/v1/admin/streak/big-red-button`.
#[derive(Debug, Deserialize)]
pub struct BrbRequest {
    pub reason: String,
    pub duration_minutes: i32,
    pub effective_from: DateTime<Utc>,
}

/// Response body for `POST /api/v1/admin/streak/big-red-button`.
#[derive(Debug, Serialize)]
pub struct BrbResponse {
    pub affected_users: i64,
    pub event_id: Uuid,
}

/// Aggregate row for the BRB events list.
#[derive(Debug, sqlx::FromRow, Serialize)]
pub struct BrbEventSummary {
    pub event_id: Uuid,
    pub actor_user_id: Option<Uuid>,
    pub reason: String,
    pub effective_from: DateTime<Utc>,
    pub effective_to: DateTime<Utc>,
    pub applied_at: DateTime<Utc>,
    pub affected_users: i64,
}

/// Row of `streak_protection_events`.
#[derive(Debug, sqlx::FromRow, Serialize)]
pub struct StreakProtectionEventRow {
    pub id: Uuid,
    pub event_id: Uuid,
    pub user_id: Uuid,
    pub actor_user_id: Option<Uuid>,
    pub reason: String,
    pub effective_from: DateTime<Utc>,
    pub effective_to: DateTime<Utc>,
    pub applied_at: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Friend Streaks
// ---------------------------------------------------------------------------

/// Row of `friend_streaks`.
#[derive(Debug, sqlx::FromRow)]
pub struct FriendStreakRow {
    pub id: Uuid,
    pub user_a_id: Uuid,
    pub user_b_id: Uuid,
    pub current_count: i32,
    pub longest_count: i32,
    pub last_increment_date: Option<NaiveDate>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Outgoing friend streak entry, joined with the friend's profile.
#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct FriendStreakOut {
    pub friend_user_id: Uuid,
    pub friend_display_name: String,
    pub friend_avatar_url: Option<String>,
    pub current_count: i32,
    pub longest_count: i32,
    pub last_increment_date: Option<NaiveDate>,
    pub is_alive: bool,
}

/// Response for `GET /api/v1/users/me/friend-streaks`.
#[derive(Debug, Serialize)]
pub struct FriendStreaksResponse {
    pub friend_streaks: Vec<FriendStreakOut>,
}

// ---------------------------------------------------------------------------
// Comeback / Phoenix
// ---------------------------------------------------------------------------

/// Row of `user_streak_history`.
#[derive(Debug, sqlx::FromRow)]
pub struct UserStreakHistoryRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub streak_value: i32,
    pub streak_started_at: DateTime<Utc>,
    pub streak_ended_at: DateTime<Utc>,
    pub phoenix_awarded: bool,
    pub created_at: DateTime<Utc>,
}

/// Row of `user_comeback_bonuses`. The `multiplier` column is `numeric(4,2)`
/// — we cast it to text in queries (`multiplier::text`) so we can keep the
/// model dependency-free, and parse to `f64` at the response layer.
#[derive(Debug, sqlx::FromRow)]
pub struct UserComebackBonusRow {
    pub id: Uuid,
    pub user_id: Uuid,
    /// Multiplier as text (e.g. "2.00") — parsed to f64 in the service.
    pub multiplier: String,
    pub started_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub history_row_id: Option<Uuid>,
    pub created_at: DateTime<Utc>,
}

/// Public-facing comeback bonus.
#[derive(Debug, Serialize)]
pub struct ActiveComebackBonus {
    pub multiplier: f64,
    pub started_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
}

/// Response for `GET /api/v1/users/me/streak/comeback-status`.
#[derive(Debug, Serialize)]
pub struct ComebackStatusResponse {
    pub phoenix_eligible: bool,
    pub consecutive_days_active: i32,
    pub days_required: i32,
    pub active_bonus: Option<ActiveComebackBonus>,
}

// ---------------------------------------------------------------------------
// Streak Insurance
// ---------------------------------------------------------------------------

/// Row of `streak_insurance_subscriptions`.
#[derive(Debug, sqlx::FromRow, Serialize)]
pub struct StreakInsuranceRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub status: String,
    pub started_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub provider: String,
    pub provider_subscription_id: Option<String>,
    pub auto_brb_enabled: bool,
    pub granted_by_user_id: Option<Uuid>,
    pub grant_reason: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Request body for `POST /api/v1/admin/users/:user_id/streak-insurance/grant`.
#[derive(Debug, Deserialize)]
pub struct GrantInsuranceRequest {
    pub duration_days: i32,
    pub reason: String,
}

// ---------------------------------------------------------------------------
// Admin stats
// ---------------------------------------------------------------------------

/// Response body for `GET /api/v1/admin/streak-economy/stats`.
#[derive(Debug, Serialize)]
pub struct StreakEconomyStats {
    pub repairs: KpiBuckets,
    pub brb_invocations: KpiBuckets,
    pub friend_streak_increments: KpiBuckets,
    pub phoenix_awards: KpiBuckets,
}

#[derive(Debug, Serialize, Default)]
pub struct KpiBuckets {
    pub last_7_days: i64,
    pub last_30_days: i64,
    pub all_time: i64,
}

// ---------------------------------------------------------------------------
// Pagination params shared across admin endpoints
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct RepairEventsQuery {
    pub user_id: Option<Uuid>,
    pub from: Option<DateTime<Utc>>,
    pub to: Option<DateTime<Utc>>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Serialize)]
pub struct RepairEventsResponse {
    pub events: Vec<StreakRepairEventRow>,
    pub page: i64,
    pub per_page: i64,
    pub total: i64,
}

#[derive(Debug, Deserialize)]
pub struct BrbEventsQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Serialize)]
pub struct BrbEventsResponse {
    pub events: Vec<BrbEventSummary>,
    pub page: i64,
    pub per_page: i64,
    pub total: i64,
}
