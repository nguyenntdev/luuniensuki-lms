//! Session and Analytics DTOs.
//!
//! Phase 11 (Tasks 12.1–12.2): Sessions, Heartbeat, Analytics Events migration.

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
    pub device_info: Option<serde_json::Value>,
}

/// Response for POST /api/v1/sessions/heartbeat.
#[derive(Debug, Serialize)]
pub struct HeartbeatResponse {
    pub session_id: Uuid,
    pub last_heartbeat_at: DateTime<Utc>,
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
    pub duration_seconds: i64,
}

// ---------------------------------------------------------------------------
// Analytics DTOs
// ---------------------------------------------------------------------------

/// A single analytics event in the batch.
#[derive(Debug, Deserialize)]
pub struct AnalyticsEventInput {
    pub event_type: String,
    pub event_data: Option<serde_json::Value>,
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
    pub user_id: Uuid,
    pub started_at: DateTime<Utc>,
    pub last_heartbeat_at: DateTime<Utc>,
    pub device_info: Option<serde_json::Value>,
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
    pub avg_duration_seconds: f64,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct UserSessionRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub started_at: DateTime<Utc>,
    pub last_heartbeat_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub duration_seconds: Option<i64>,
    pub device_info: Option<serde_json::Value>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct ActiveSessionRow {
    pub id: Uuid,
    pub user_id: Uuid,
    pub started_at: DateTime<Utc>,
    pub last_heartbeat_at: DateTime<Utc>,
    pub device_info: Option<serde_json::Value>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct SessionStatsRow {
    pub active_sessions: i64,
    pub total_sessions_today: i64,
    pub avg_duration_seconds: Option<f64>,
}
