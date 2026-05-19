//! Session and Analytics DTOs.
//!
//! Phase 11 (Tasks 12.1–12.2): Sessions, Heartbeat, Analytics Events migration.
//! Fixed to match actual production schema:
//! - Sessions: `user_sessions` table with `session_id`, `device_type`, `platform`, `app_version`, `is_active`
//! - Analytics: `analytics_events` table with `event_name`, `path`, `payload`, `session_id`, `cohort`, `event_category`, `device_info`

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Session DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/sessions/heartbeat.
#[derive(Debug, Deserialize)]
pub struct HeartbeatRequest {
    pub session_id: Option<Uuid>,
    pub device_type: Option<String>,
    pub platform: Option<String>,
    pub app_version: Option<String>,
}

/// Response for POST /api/v1/sessions/heartbeat.
#[derive(Debug, Serialize)]
pub struct HeartbeatResponse {
    pub session_id: Uuid,
    pub last_active_at: DateTime<Utc>,
}

/// Request body for POST /api/v1/sessions/end.
#[derive(Debug, Deserialize)]
pub struct EndSessionRequest {
    pub session_id: Uuid,
}

/// Response for POST /api/v1/sessions/end.
#[derive(Debug, Serialize)]
pub struct EndSessionResponse {
    pub session_id: Uuid,
    pub ended_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Analytics DTOs
// ---------------------------------------------------------------------------

/// A single analytics event in the batch.
#[derive(Debug, Deserialize)]
pub struct AnalyticsEventInput {
    pub event_name: String,
    pub path: Option<String>,
    pub payload: Option<serde_json::Value>,
    pub session_id: Option<Uuid>,
    pub cohort: Option<String>,
    pub event_category: Option<String>,
    pub device_info: Option<serde_json::Value>,
    pub timestamp: Option<DateTime<Utc>>,
}

/// Request body for POST /api/v1/analytics/events.
#[derive(Debug, Deserialize)]
pub struct IngestEventsRequest {
    pub events: Vec<AnalyticsEventInput>,
}

/// Response for POST /api/v1/analytics/events.
#[derive(Debug, Serialize)]
pub struct IngestEventsResponse {
    pub ingested: i32,
}

// ---------------------------------------------------------------------------
// Admin Analytics DTOs
// ---------------------------------------------------------------------------

/// An active session for admin view.
#[derive(Debug, Serialize)]
pub struct ActiveSessionOut {
    pub session_id: Uuid,
    pub user_id: Option<Uuid>,
    pub started_at: DateTime<Utc>,
    pub last_active_at: DateTime<Utc>,
    pub device_type: String,
    pub platform: String,
}

/// Response for GET /api/v1/admin/analytics/sessions/active.
#[derive(Debug, Serialize)]
pub struct ActiveSessionsResponse {
    pub sessions: Vec<ActiveSessionOut>,
    pub total: i64,
}

/// Response for GET /api/v1/admin/analytics/sessions/stats.
#[derive(Debug, Serialize)]
pub struct SessionStatsResponse {
    pub active_sessions: i64,
    pub total_sessions_today: i64,
    pub avg_session_minutes: f64,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct UserSessionRow {
    pub id: Uuid,
    pub session_id: Uuid,
    pub user_id: Option<Uuid>,
    pub started_at: DateTime<Utc>,
    pub last_active_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub device_type: String,
    pub platform: String,
    pub app_version: Option<String>,
    pub is_active: bool,
}

#[derive(Debug, sqlx::FromRow)]
pub struct ActiveSessionRow {
    pub id: Uuid,
    pub session_id: Uuid,
    pub user_id: Option<Uuid>,
    pub started_at: DateTime<Utc>,
    pub last_active_at: DateTime<Utc>,
    pub device_type: String,
    pub platform: String,
}

#[derive(Debug, sqlx::FromRow)]
pub struct SessionStatsRow {
    pub active_sessions: i64,
    pub total_sessions_today: i64,
    pub avg_session_minutes: Option<f64>,
}
