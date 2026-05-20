//! Admin route handlers.
//!
//! Phase 13 (Tasks 14.1–14.8): Admin migration.
//! Fixed: removed resolve_crash_report (no DB support), updated to match actual schema.

use axum::{
    extract::{Path, Query, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::admin::*;
use crate::routes::auth::AuthState;
use crate::services::admin_service;
use crate::services::crash_report_service;

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_access=") {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

fn authenticate_admin(headers: &HeaderMap, settings: &Settings) -> Result<(Uuid, auth::Claims), AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok((user_id, claims))
}

// ---------------------------------------------------------------------------
// Query params
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct PaginationParams {
    pub page: Option<i32>,
    pub per_page: Option<i32>,
}

// ---------------------------------------------------------------------------
// Push Notification Admin Handlers
// ---------------------------------------------------------------------------

/// POST /api/v1/admin/push-notifications/send
pub async fn send_push_notification(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<SendPushRequest>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = admin_service::send_push_notification(pool, body).await?;
    Ok(Json(result))
}

/// POST /api/v1/admin/push-notifications/broadcast
pub async fn broadcast_push_notification(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<BroadcastPushRequest>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = admin_service::broadcast_push_notification(pool, body).await?;
    Ok(Json(result))
}

/// GET /api/v1/admin/push-notifications
pub async fn list_push_notifications(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<PaginationParams>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20);
    let result = admin_service::list_push_notifications(pool, page, per_page).await?;
    Ok(Json(result))
}

// ---------------------------------------------------------------------------
// Crash Report Admin Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/admin/crash-reports
pub async fn list_crash_reports(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<PaginationParams>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20);
    let result = crash_report_service::list_crash_reports(pool, page, per_page).await?;
    Ok(Json(result))
}

/// GET /api/v1/admin/crash-reports/stats
pub async fn get_crash_report_stats(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = crash_report_service::get_crash_report_stats(pool).await?;
    Ok(Json(result))
}

/// GET /api/v1/admin/crash-reports/{report_id}
pub async fn get_crash_report(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(report_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = crash_report_service::get_crash_report(pool, report_id).await?;
    Ok(Json(result))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::{get, post}, Router};
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/admin/push-notifications/send", post(send_push_notification))
            .route("/api/v1/admin/push-notifications/broadcast", post(broadcast_push_notification))
            .route("/api/v1/admin/push-notifications", get(list_push_notifications))
            .route("/api/v1/admin/crash-reports", get(list_crash_reports))
            .route("/api/v1/admin/crash-reports/stats", get(get_crash_report_stats))
            .route("/api/v1/admin/crash-reports/:report_id", get(get_crash_report))
            .with_state(state)
    }

    #[tokio::test]
    async fn send_push_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/admin/push-notifications/send")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"user_id":"00000000-0000-0000-0000-000000000001","title":"t","body":"b"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn send_push_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/admin/push-notifications/send")
                .header("Authorization", format!("Bearer {}", token))
                .header("content-type", "application/json")
                .body(Body::from(r#"{"user_id":"00000000-0000-0000-0000-000000000001","title":"t","body":"b"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn broadcast_push_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/admin/push-notifications/broadcast")
                .header("Authorization", format!("Bearer {}", token))
                .header("content-type", "application/json")
                .body(Body::from(r#"{"title":"t","body":"b"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn list_push_notifications_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/push-notifications")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn list_crash_reports_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/crash-reports")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn crash_report_stats_returns_503_for_admin_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "admin",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/crash-reports/stats")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}


// ---------------------------------------------------------------------------
// Phase 13 leftover admin endpoints (Tasks 14.3–14.6)
// ---------------------------------------------------------------------------

use crate::services::admin_extras_service;

pub async fn list_audit(
    State(state): State<AuthState>,
    Query(params): Query<PaginationParams>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _ = authenticate_admin(&headers, &state.settings)?;
    let resp = admin_extras_service::list_audit_logs(
        pool,
        params.page.unwrap_or(1) as i64,
        params.per_page.unwrap_or(50) as i64,
    )
    .await?;
    Ok(Json(resp))
}

pub async fn list_feature_flags(
    State(state): State<AuthState>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _ = authenticate_admin(&headers, &state.settings)?;
    let resp = admin_extras_service::list_feature_flags(pool).await?;
    Ok(Json(serde_json::json!({ "feature_flags": resp })))
}

pub async fn list_experiments(
    State(state): State<AuthState>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _ = authenticate_admin(&headers, &state.settings)?;
    let resp = admin_extras_service::list_experiments(pool).await?;
    Ok(Json(serde_json::json!({ "experiments": resp })))
}
