//! Crash Report DTOs.
//!
//! Phase 12 (Task 13.1): Crash Reports migration.
//! Phase 13 (Task 14.7): Admin crash report routes.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Crash Report DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/crash-reports.
#[derive(Debug, Deserialize)]
pub struct SubmitCrashReportRequest {
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub device_info: Option<serde_json::Value>,
    pub app_version: Option<String>,
    pub platform: Option<String>,
}

/// Response for POST /api/v1/crash-reports.
#[derive(Debug, Serialize)]
pub struct SubmitCrashReportResponse {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Admin Crash Report DTOs
// ---------------------------------------------------------------------------

/// A crash report in admin list.
#[derive(Debug, Serialize)]
pub struct CrashReportOut {
    pub id: Uuid,
    pub user_id: Option<Uuid>,
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub device_info: Option<serde_json::Value>,
    pub app_version: Option<String>,
    pub platform: Option<String>,
    pub created_at: DateTime<Utc>,
    pub resolved_at: Option<DateTime<Utc>>,
    pub resolved_by: Option<Uuid>,
}

/// Response for GET /api/v1/admin/crash-reports.
#[derive(Debug, Serialize)]
pub struct CrashReportsListResponse {
    pub crash_reports: Vec<CrashReportOut>,
    pub total: i64,
    pub page: i32,
    pub per_page: i32,
}

/// Response for GET /api/v1/admin/crash-reports/stats.
#[derive(Debug, Serialize)]
pub struct CrashReportStatsResponse {
    pub total: i64,
    pub unresolved: i64,
    pub resolved: i64,
    pub today: i64,
}

/// Response for POST /api/v1/admin/crash-reports/{id}/resolve.
#[derive(Debug, Serialize)]
pub struct ResolveCrashReportResponse {
    pub id: Uuid,
    pub resolved_at: DateTime<Utc>,
    pub resolved_by: Uuid,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct CrashReportRow {
    pub id: Uuid,
    pub user_id: Option<Uuid>,
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub device_info: Option<serde_json::Value>,
    pub app_version: Option<String>,
    pub platform: Option<String>,
    pub created_at: DateTime<Utc>,
    pub resolved_at: Option<DateTime<Utc>>,
    pub resolved_by: Option<Uuid>,
}

#[derive(Debug, sqlx::FromRow)]
pub struct CrashReportStatsRow {
    pub total: i64,
    pub unresolved: i64,
    pub resolved: i64,
    pub today: i64,
}
