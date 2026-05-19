//! Notification DTOs.
//!
//! Phase 10 (Tasks 11.1–11.3): Notifications migration.
//! Fixed to match actual production schema:
//! - Settings: `user_notification_settings` table
//! - Push token: stored in `user_notification_settings.push_token` + `push_platform`
//! - History: `push_notifications` table

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Notification Settings DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/notifications/settings.
#[derive(Debug, Serialize)]
pub struct NotificationSettingsOut {
    pub user_id: Uuid,
    pub push_enabled: bool,
    pub email_enabled: bool,
    pub streak_reminders: bool,
    pub daily_mission_reminders: bool,
    pub weekly_digest: bool,
    pub marketing_enabled: bool,
    pub quiet_hours_start: Option<i32>,
    pub quiet_hours_end: Option<i32>,
}

/// Request body for PUT /api/v1/notifications/settings.
#[derive(Debug, Deserialize)]
pub struct UpdateNotificationSettingsRequest {
    pub push_enabled: Option<bool>,
    pub email_enabled: Option<bool>,
    pub streak_reminders: Option<bool>,
    pub daily_mission_reminders: Option<bool>,
    pub weekly_digest: Option<bool>,
    pub marketing_enabled: Option<bool>,
    pub quiet_hours_start: Option<i32>,
    pub quiet_hours_end: Option<i32>,
}

// ---------------------------------------------------------------------------
// Push Token DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/notifications/register-push.
#[derive(Debug, Deserialize)]
pub struct RegisterPushRequest {
    pub token: String,
    pub platform: String,
}

/// Request body for DELETE /api/v1/notifications/unregister-push.
#[derive(Debug, Deserialize)]
pub struct UnregisterPushRequest {
    pub token: String,
}

/// Response for push token operations.
#[derive(Debug, Serialize)]
pub struct PushTokenResponse {
    pub success: bool,
    pub message: String,
}

// ---------------------------------------------------------------------------
// Notification History DTOs
// ---------------------------------------------------------------------------

/// A notification in history.
#[derive(Debug, Serialize)]
pub struct NotificationHistoryItem {
    pub id: Uuid,
    pub notification_type: String,
    pub title: String,
    pub body: String,
    pub data_payload: Option<serde_json::Value>,
    pub status: String,
    pub sent_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

/// Response for GET /api/v1/notifications/history.
#[derive(Debug, Serialize)]
pub struct NotificationHistoryResponse {
    pub notifications: Vec<NotificationHistoryItem>,
    pub total: i64,
    pub page: i32,
    pub per_page: i32,
}

/// Response for GET /api/v1/notifications/should-prompt-permission.
#[derive(Debug, Serialize)]
pub struct ShouldPromptPermissionResponse {
    pub should_prompt: bool,
    pub reason: Option<String>,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct NotificationSettingsRow {
    pub user_id: Uuid,
    pub push_enabled: bool,
    pub email_enabled: bool,
    pub streak_reminders: bool,
    pub daily_mission_reminders: bool,
    pub weekly_digest: bool,
    pub marketing_enabled: bool,
    pub quiet_hours_start: Option<i32>,
    pub quiet_hours_end: Option<i32>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct NotificationHistoryRow {
    pub id: Uuid,
    pub notification_type: String,
    pub title: String,
    pub body: String,
    pub data_payload: Option<serde_json::Value>,
    pub status: String,
    pub sent_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}
