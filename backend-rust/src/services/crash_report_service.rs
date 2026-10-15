//! Crash Report business logic.
//!
//! Phase 12 (Task 13.1): Crash Reports migration.
//! Phase 13 (Task 14.7): Admin crash report routes.
//! Fixed to match actual production schema:
//! - `crash_reports` table with `error_type`, `error_message`, `stack_trace`,
//!   `platform`, `app_version`, `device_model`, `os_version`, `additional_data`
//! - NO `resolved_at` or `resolved_by` columns
//! - `resolve_crash_report` function REMOVED (no DB support)

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::crash_report::*;

pub const MAX_ERROR_TYPE_CHARS: usize = 20;
pub const MAX_ERROR_MESSAGE_CHARS: usize = 2000;
pub const MAX_STACK_TRACE_CHARS: usize = 10000;
pub const MAX_PLATFORM_CHARS: usize = 20;
pub const MAX_APP_VERSION_CHARS: usize = 20;
pub const MAX_DEVICE_MODEL_CHARS: usize = 100;
pub const MAX_OS_VERSION_CHARS: usize = 50;

/// Truncate a string slice to at most `max_chars` Unicode characters without splitting code points.
pub fn truncate_chars(s: &str, max_chars: usize) -> &str {
    match s.char_indices().nth(max_chars) {
        None => s,
        Some((idx, _)) => &s[..idx],
    }
}

/// POST /api/v1/crash-reports — submit crash report.
pub async fn submit_crash_report(
    pool: &PgPool,
    user_id: Uuid,
    req: SubmitCrashReportRequest,
) -> Result<SubmitCrashReportResponse, AppError> {
    let id = Uuid::new_v4();
    let now = Utc::now();

    let error_type = truncate_chars(&req.error_type, MAX_ERROR_TYPE_CHARS);
    let error_message = truncate_chars(&req.error_message, MAX_ERROR_MESSAGE_CHARS);
    let stack_trace = req
        .stack_trace
        .as_deref()
        .map(|st| truncate_chars(st, MAX_STACK_TRACE_CHARS));
    let platform = truncate_chars(&req.platform, MAX_PLATFORM_CHARS);
    let app_version = truncate_chars(&req.app_version, MAX_APP_VERSION_CHARS);
    let device_model = req
        .device_model
        .as_deref()
        .map(|dm| truncate_chars(dm, MAX_DEVICE_MODEL_CHARS));
    let os_version = req
        .os_version
        .as_deref()
        .map(|os| truncate_chars(os, MAX_OS_VERSION_CHARS));

    sqlx::query(
        r#"
        INSERT INTO crash_reports (id, user_id, session_id, error_type, error_message, stack_trace, platform, app_version, device_model, os_version, additional_data, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        "#,
    )
    .bind(id)
    .bind(user_id)
    .bind(req.session_id)
    .bind(error_type)
    .bind(error_message)
    .bind(stack_trace)
    .bind(platform)
    .bind(app_version)
    .bind(device_model)
    .bind(os_version)
    .bind(&req.additional_data)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(SubmitCrashReportResponse {
        id,
        created_at: now,
    })
}

/// GET /api/v1/admin/crash-reports — list crash reports (admin).
pub async fn list_crash_reports(
    pool: &PgPool,
    page: i32,
    per_page: i32,
) -> Result<CrashReportsListResponse, AppError> {
    let offset = (page - 1).max(0) * per_page;

    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM crash_reports")
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, CrashReportRow>(
        r#"
        SELECT id, user_id, session_id, error_type, error_message, stack_trace, platform, app_version, device_model, os_version, additional_data, created_at
        FROM crash_reports
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        "#,
    )
    .bind(per_page as i64)
    .bind(offset as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let crash_reports = rows
        .into_iter()
        .map(|r| CrashReportOut {
            id: r.id,
            user_id: r.user_id,
            session_id: r.session_id,
            error_type: r.error_type,
            error_message: r.error_message,
            stack_trace: r.stack_trace,
            platform: r.platform,
            app_version: r.app_version,
            device_model: r.device_model,
            os_version: r.os_version,
            additional_data: r.additional_data,
            created_at: r.created_at,
        })
        .collect();

    Ok(CrashReportsListResponse {
        crash_reports,
        total: total.0,
        page,
        per_page,
    })
}

/// GET /api/v1/admin/crash-reports/{report_id} — crash report detail (admin).
pub async fn get_crash_report(pool: &PgPool, report_id: Uuid) -> Result<CrashReportOut, AppError> {
    let row = sqlx::query_as::<_, CrashReportRow>(
        r#"
        SELECT id, user_id, session_id, error_type, error_message, stack_trace, platform, app_version, device_model, os_version, additional_data, created_at
        FROM crash_reports
        WHERE id = $1
        "#,
    )
    .bind(report_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Crash report not found".to_string(),
    })?;

    Ok(CrashReportOut {
        id: row.id,
        user_id: row.user_id,
        session_id: row.session_id,
        error_type: row.error_type,
        error_message: row.error_message,
        stack_trace: row.stack_trace,
        platform: row.platform,
        app_version: row.app_version,
        device_model: row.device_model,
        os_version: row.os_version,
        additional_data: row.additional_data,
        created_at: row.created_at,
    })
}

/// GET /api/v1/admin/crash-reports/stats — crash report stats (admin).
/// Groups by error_type since there's no resolved_at column.
pub async fn get_crash_report_stats(pool: &PgPool) -> Result<CrashReportStatsResponse, AppError> {
    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM crash_reports")
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let today: (i64,) =
        sqlx::query_as("SELECT COUNT(*) FROM crash_reports WHERE created_at::date = CURRENT_DATE")
            .fetch_one(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    let by_error_type = sqlx::query_as::<_, ErrorTypeCount>(
        r#"
        SELECT error_type, COUNT(*) AS count
        FROM crash_reports
        GROUP BY error_type
        ORDER BY count DESC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(CrashReportStatsResponse {
        total: total.0,
        today: today.0,
        by_error_type,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_truncate_chars_short() {
        assert_eq!(truncate_chars("hello", 10), "hello");
        assert_eq!(truncate_chars("", 5), "");
    }

    #[test]
    fn test_truncate_chars_exact() {
        assert_eq!(truncate_chars("hello", 5), "hello");
    }

    #[test]
    fn test_truncate_chars_long() {
        assert_eq!(truncate_chars("hello world", 5), "hello");
    }

    #[test]
    fn test_truncate_chars_multibyte() {
        let text = "Cửu Đỉnh Huế";
        assert_eq!(truncate_chars(text, 3), "Cửu");
        assert_eq!(truncate_chars(text, 8), "Cửu Đỉnh");
    }

    #[test]
    fn test_crash_report_bounds_constants() {
        assert_eq!(MAX_ERROR_MESSAGE_CHARS, 2000);
        assert_eq!(MAX_STACK_TRACE_CHARS, 10000);
        assert_eq!(MAX_PLATFORM_CHARS, 20);
        assert_eq!(MAX_APP_VERSION_CHARS, 20);
        assert_eq!(MAX_ERROR_TYPE_CHARS, 20);
        assert_eq!(MAX_DEVICE_MODEL_CHARS, 100);
        assert_eq!(MAX_OS_VERSION_CHARS, 50);
    }
}
