//! Crash Report business logic.
//!
//! Phase 12 (Task 13.1): Crash Reports migration.
//! Phase 13 (Task 14.7): Admin crash report routes.

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
        INSERT INTO crash_reports (id, user_id, error_message, stack_trace, device_info, app_version, platform, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        "#,
    )
    .bind(id)
    .bind(user_id)
    .bind(&req.error_message)
    .bind(&req.stack_trace)
    .bind(&req.device_info)
    .bind(&req.app_version)
    .bind(&req.platform)
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
        SELECT id, user_id, error_message, stack_trace, device_info, app_version, platform, created_at, resolved_at, resolved_by
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
            error_message: r.error_message,
            stack_trace: r.stack_trace,
            device_info: r.device_info,
            app_version: r.app_version,
            platform: r.platform,
            created_at: r.created_at,
            resolved_at: r.resolved_at,
            resolved_by: r.resolved_by,
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
        SELECT id, user_id, error_message, stack_trace, device_info, app_version, platform, created_at, resolved_at, resolved_by
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
        error_message: row.error_message,
        stack_trace: row.stack_trace,
        device_info: row.device_info,
        app_version: row.app_version,
        platform: row.platform,
        created_at: row.created_at,
        resolved_at: row.resolved_at,
        resolved_by: row.resolved_by,
    })
}

/// POST /api/v1/admin/crash-reports/{report_id}/resolve — resolve crash report (admin).
pub async fn resolve_crash_report(
    pool: &PgPool,
    report_id: Uuid,
    admin_id: Uuid,
) -> Result<ResolveCrashReportResponse, AppError> {
    let now = Utc::now();

    let result = sqlx::query(
        "UPDATE crash_reports SET resolved_at = $1, resolved_by = $2 WHERE id = $3 AND resolved_at IS NULL",
    )
    .bind(now)
    .bind(admin_id)
    .bind(report_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Crash report not found or already resolved".to_string(),
        });
    }

    Ok(ResolveCrashReportResponse {
        id: report_id,
        resolved_at: now,
        resolved_by: admin_id,
    })
}

/// GET /api/v1/admin/crash-reports/stats — crash report stats (admin).
pub async fn get_crash_report_stats(pool: &PgPool) -> Result<CrashReportStatsResponse, AppError> {
    let stats = sqlx::query_as::<_, CrashReportStatsRow>(
        r#"
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE resolved_at IS NULL) AS unresolved,
            COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) AS resolved,
            COUNT(*) FILTER (WHERE created_at::date = CURRENT_DATE) AS today
        FROM crash_reports
        "#,
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(CrashReportStatsResponse {
        total: stats.total,
        unresolved: stats.unresolved,
        resolved: stats.resolved,
        today: stats.today,
    })
}
