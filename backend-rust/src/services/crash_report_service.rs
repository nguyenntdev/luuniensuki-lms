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

/// POST /api/v1/crash-reports — submit crash report.
pub async fn submit_crash_report(
    pool: &PgPool,
    user_id: Uuid,
    req: SubmitCrashReportRequest,
) -> Result<SubmitCrashReportResponse, AppError> {
    let id = Uuid::new_v4();
    let now = Utc::now();

    sqlx::query(
        r#"
        INSERT INTO crash_reports (id, user_id, session_id, error_type, error_message, stack_trace, platform, app_version, device_model, os_version, additional_data, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        "#,
    )
    .bind(id)
    .bind(user_id)
    .bind(req.session_id)
    .bind(&req.error_type)
    .bind(&req.error_message)
    .bind(&req.stack_trace)
    .bind(&req.platform)
    .bind(&req.app_version)
    .bind(&req.device_model)
    .bind(&req.os_version)
    .bind(&req.additional_data)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(SubmitCrashReportResponse { id, created_at: now })
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
pub async fn get_crash_report(
    pool: &PgPool,
    report_id: Uuid,
) -> Result<CrashReportOut, AppError> {
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

    let today: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM crash_reports WHERE created_at::date = CURRENT_DATE",
    )
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
