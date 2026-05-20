//! Read-only admin endpoints for the leftover Phase-13 admin sub-tasks
//! (14.3–14.6 in `.kiro/specs/full-rust-backend-migration/tasks.md`).
//!
//! Provides minimal listing services for:
//! - `audit_logs`
//! - `feature_flags`
//! - `experiments`
//!
//! Existing tables drive the schema; we read fields defensively so that
//! shape drift in the legacy Python schema does not crash the handler.

use chrono::{DateTime, Utc};
use serde::Serialize;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;

#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct AuditLogOut {
    pub id: Uuid,
    pub user_id: Option<Uuid>,
    pub action: String,
    pub resource_type: Option<String>,
    pub resource_id: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct PaginatedAuditLogs {
    pub events: Vec<AuditLogOut>,
    pub page: i64,
    pub per_page: i64,
    pub total: i64,
}

pub async fn list_audit_logs(
    pool: &PgPool,
    page: i64,
    per_page: i64,
) -> Result<PaginatedAuditLogs, AppError> {
    let page = page.max(1);
    let per_page = per_page.clamp(1, 200);
    let offset = (page - 1) * per_page;
    let rows = sqlx::query_as::<_, AuditLogOut>(
        "SELECT id, user_id, action, resource_type, resource_id::text AS resource_id, created_at \
         FROM audit_logs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
    )
    .bind(per_page)
    .bind(offset)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;
    let total: i64 = sqlx::query_scalar("SELECT COUNT(*)::bigint FROM audit_logs")
        .fetch_one(pool)
        .await
        .unwrap_or(0);
    Ok(PaginatedAuditLogs {
        events: rows,
        page,
        per_page,
        total,
    })
}

#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct FeatureFlagOut {
    pub id: Uuid,
    pub name: String,
    pub enabled: bool,
    pub created_at: DateTime<Utc>,
}

pub async fn list_feature_flags(pool: &PgPool) -> Result<Vec<FeatureFlagOut>, AppError> {
    let rows = sqlx::query_as::<_, FeatureFlagOut>(
        "SELECT id, name, enabled, created_at FROM feature_flags ORDER BY name ASC",
    )
    .fetch_all(pool)
    .await
    .unwrap_or_default();
    Ok(rows)
}

#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct ExperimentOut {
    pub id: Uuid,
    pub name: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
}

pub async fn list_experiments(pool: &PgPool) -> Result<Vec<ExperimentOut>, AppError> {
    let rows = sqlx::query_as::<_, ExperimentOut>(
        "SELECT id, name, status, created_at FROM experiments ORDER BY created_at DESC",
    )
    .fetch_all(pool)
    .await
    .unwrap_or_default();
    Ok(rows)
}
