//! Notification route handlers.
//!
//! Phase 10 (Tasks 11.1–11.3): Notifications migration.

use axum::{
    extract::{Query, State},
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
use crate::models::notification::*;
use crate::routes::auth::AuthState;
use crate::services::notification_service;

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

fn authenticate(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(
        &token,
        &settings.jwt_secret_key,
        settings.jwt_validate_new_claims,
        &settings.jwt_issuer,
        &settings.jwt_audience,
    )
    .map_err(|_| AppError::Unauthorized)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
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
// Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/notifications/settings
pub async fn get_settings(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let settings = notification_service::get_settings(pool, user_id).await?;
    Ok(Json(settings))
}

/// PUT /api/v1/notifications/settings
pub async fn update_settings(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<UpdateNotificationSettingsRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let settings = notification_service::update_settings(pool, user_id, body).await?;
    Ok(Json(settings))
}

/// POST /api/v1/notifications/register-push
pub async fn register_push(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<RegisterPushRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = notification_service::register_push(pool, user_id, body).await?;
    Ok(Json(result))
}

/// DELETE /api/v1/notifications/unregister-push
pub async fn unregister_push(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(body): Json<UnregisterPushRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = notification_service::unregister_push(pool, user_id, body).await?;
    Ok(Json(result))
}

/// GET /api/v1/notifications/history
pub async fn get_history(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<PaginationParams>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let page = params.page.unwrap_or(1);
    let per_page = params.per_page.unwrap_or(20);
    let history = notification_service::get_history(pool, user_id, page, per_page).await?;
    Ok(Json(history))
}

/// GET /api/v1/notifications/should-prompt-permission
pub async fn should_prompt_permission(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = notification_service::should_prompt_permission(pool, user_id).await?;
    Ok(Json(result))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::Request,
        routing::{delete, get, post, put},
        Router,
    };
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState {
            pool: None,
            settings,
        }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route(
                "/api/v1/notifications/settings",
                get(get_settings).put(update_settings),
            )
            .route("/api/v1/notifications/register-push", post(register_push))
            .route(
                "/api/v1/notifications/unregister-push",
                delete(unregister_push),
            )
            .route("/api/v1/notifications/history", get(get_history))
            .route(
                "/api/v1/notifications/should-prompt-permission",
                get(should_prompt_permission),
            )
            .with_state(state)
    }

    #[tokio::test]
    async fn get_settings_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/notifications/settings")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_settings_returns_503_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/notifications/settings")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn register_push_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/notifications/register-push")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"token":"abc","platform":"ios"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn history_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/notifications/history")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn should_prompt_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/notifications/should-prompt-permission")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
