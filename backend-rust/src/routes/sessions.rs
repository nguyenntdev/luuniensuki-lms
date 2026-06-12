//! Session and Analytics route handlers.
//!
//! Phase 11 (Tasks 12.1–12.2): Sessions, Heartbeat, Analytics Events migration.

use axum::{
    extract::State,
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::session::*;
use crate::routes::auth::AuthState;
use crate::services::session_service;

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

fn authenticate(headers: &HeaderMap, settings: &Settings) -> Result<auth::Claims, AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key, settings.jwt_validate_new_claims, &settings.jwt_issuer, &settings.jwt_audience)
        .map_err(|_| AppError::Unauthorized)?;
    Ok(claims)
}

fn require_admin(claims: &auth::Claims) -> Result<(), AppError> {
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// POST /api/v1/sessions/heartbeat
pub async fn heartbeat(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<HeartbeatRequest>,
) -> Result<impl IntoResponse, AppError> {
    let claims = authenticate(&headers, &state.settings)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    let pool = require_pool(&state.pool)?;
    let result = session_service::heartbeat(pool, user_id, body).await?;
    Ok(Json(result))
}

/// POST /api/v1/sessions/end
pub async fn end_session(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<EndSessionRequest>,
) -> Result<impl IntoResponse, AppError> {
    let claims = authenticate(&headers, &state.settings)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    let pool = require_pool(&state.pool)?;
    let result = session_service::end_session(pool, user_id, body).await?;
    Ok(Json(result))
}

/// POST /api/v1/analytics/events
pub async fn ingest_events(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<IngestEventsRequest>,
) -> Result<impl IntoResponse, AppError> {
    let claims = authenticate(&headers, &state.settings)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    let pool = require_pool(&state.pool)?;
    let result = session_service::ingest_events(pool, user_id, body).await?;
    Ok(Json(result))
}

/// GET /api/v1/admin/analytics/sessions/active
pub async fn get_active_sessions(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let claims = authenticate(&headers, &state.settings)?;
    require_admin(&claims)?;
    let pool = require_pool(&state.pool)?;
    let result = session_service::get_active_sessions(pool).await?;
    Ok(Json(result))
}

/// GET /api/v1/admin/analytics/sessions/stats
pub async fn get_session_stats(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let claims = authenticate(&headers, &state.settings)?;
    require_admin(&claims)?;
    let pool = require_pool(&state.pool)?;
    let result = session_service::get_session_stats(pool).await?;
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
            .route("/api/v1/sessions/heartbeat", post(heartbeat))
            .route("/api/v1/sessions/end", post(end_session))
            .route("/api/v1/analytics/events", post(ingest_events))
            .route("/api/v1/admin/analytics/sessions/active", get(get_active_sessions))
            .route("/api/v1/admin/analytics/sessions/stats", get(get_session_stats))
            .with_state(state)
    }

    #[tokio::test]
    async fn heartbeat_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/sessions/heartbeat")
                .header("content-type", "application/json")
                .body(Body::from(r#"{}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn end_session_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/sessions/end")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"session_id":"00000000-0000-0000-0000-000000000001"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn ingest_events_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/analytics/events")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"events":[]}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn heartbeat_returns_503_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/sessions/heartbeat")
                .header("Authorization", format!("Bearer {}", token))
                .header("content-type", "application/json")
                .body(Body::from(r#"{}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn admin_active_sessions_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/analytics/sessions/active")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn admin_active_sessions_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/analytics/sessions/active")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn admin_session_stats_returns_403_for_non_admin() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/analytics/sessions/stats")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn admin_session_stats_returns_503_for_admin_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "admin",
            &state.settings.jwt_secret_key, 60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/admin/analytics/sessions/stats")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}
