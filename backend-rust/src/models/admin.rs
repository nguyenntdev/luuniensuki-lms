//! Admin DTOs.
//!
//! Phase 13 (Tasks 14.1–14.8): Admin migration.
//! Fixed to match actual production schema:
//! - Push notifications: `push_notifications` table with `user_id`, `title`, `body`,
//!   `notification_type`, `data_payload`, `status`, `scheduled_for`, `sent_at`, etc.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Push Notification Admin DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/admin/push-notifications/send.
#[derive(Debug, Deserialize)]
pub struct SendPushRequest {
    pub user_id: Uuid,
    pub title: String,
    pub body: String,
    pub notification_type: Option<String>,
    pub data_payload: Option<serde_json::Value>,
}

/// Request body for POST /api/v1/admin/push-notifications/broadcast.
#[derive(Debug, Deserialize)]
pub struct BroadcastPushRequest {
    pub title: String,
    pub body: String,
    pub notification_type: Option<String>,
    pub data_payload: Option<serde_json::Value>,
}

/// Response for push notification send/broadcast.
#[derive(Debug, Serialize)]
pub struct PushNotificationResponse {
    pub id: Uuid,
    pub status: String,
    pub created_at: DateTime<Utc>,
}

/// A push notification in admin list.
#[derive(Debug, Serialize)]
pub struct PushNotificationOut {
    pub id: Uuid,
    pub user_id: Uuid,
    pub title: String,
    pub body: String,
    pub notification_type: String,
    pub data_payload: Option<serde_json::Value>,
    pub status: String,
    pub sent_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

/// Response for GET /api/v1/admin/push-notifications.
#[derive(Debug, Serialize)]
pub struct PushNotificationsListResponse {
    pub notifications: Vec<PushNotificationOut>,
    pub total: i64,
    pub page: i32,
    pub per_page: i32,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct PushNotificationRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub title: String,
    pub body: String,
    pub notification_type: String,
    pub data_payload: Option<serde_json::Value>,
    pub status: String,
    pub sent_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}
