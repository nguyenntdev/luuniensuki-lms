//! Crash Report DTOs.
//!
//! Phase 12 (Task 13.1): Crash Reports migration.
//! Phase 13 (Task 14.7): Admin crash report routes.
//! Fixed to match actual production schema:
//! - `crash_reports` table with `error_type`, `error_message`, `stack_trace`,
//!   `platform`, `app_version`, `device_model`, `os_version`, `additional_data`
//! - NO `resolved_at` or `resolved_by` columns

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Crash Report DTOs
// ---------------------------------------------------------------------------

/// Request body for POST /api/v1/crash-reports.
#[derive(Debug, Deserialize)]
pub struct SubmitCrashReportRequest {
    pub error_type: String,
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub platform: String,
    pub app_version: String,
    pub device_model: Option<String>,
    pub os_version: Option<String>,
    pub additional_data: Option<serde_json::Value>,
    pub session_id: Option<Uuid>,
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
    pub session_id: Option<Uuid>,
    pub error_type: String,
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub platform: String,
    pub app_version: String,
    pub device_model: Option<String>,
    pub os_version: Option<String>,
    pub additional_data: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
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
    pub today: i64,
    pub by_error_type: Vec<ErrorTypeCount>,
}

/// Count per error_type for stats.
#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct ErrorTypeCount {
    pub error_type: String,
    pub count: i64,
}

// ---------------------------------------------------------------------------
// DB Row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
pub struct CrashReportRow {
    pub id: Uuid,
    pub user_id: Option<Uuid>,
    pub session_id: Option<Uuid>,
    pub error_type: String,
    pub error_message: String,
    pub stack_trace: Option<String>,
    pub platform: String,
    pub app_version: String,
    pub device_model: Option<String>,
    pub os_version: Option<String>,
    pub additional_data: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
}
