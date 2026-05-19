//! Streak comeback / Phoenix routes + insurance read.
//!
//! - `GET /api/v1/users/me/streak/comeback-status`
//! - `GET /api/v1/users/me/streak-insurance`
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use axum::{
    extract::State,
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde_json::Value;
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::routes::auth::AuthState;
use crate::services::streak_comeback_service;

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
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
}

/// `GET /api/v1/users/me/streak/comeback-status`.
pub async fn comeback_status(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = streak_comeback_service::comeback_status(pool, user_id).await?;
    Ok(Json(result))
}

/// `GET /api/v1/users/me/streak-insurance`.
pub async fn my_insurance(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let row = streak_comeback_service::get_my_insurance(pool, user_id).await?;
    // Spec returns either the subscription record or `null`.
    let body: Value = match row {
        Some(r) => serde_json::to_value(r).unwrap_or(Value::Null),
        None => Value::Null,
    };
    Ok(Json(body))
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::get, Router};
    use tower::ServiceExt;

    fn test_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let s = test_state();
        Router::new()
            .route("/api/v1/users/me/streak/comeback-status", get(comeback_status))
            .route("/api/v1/users/me/streak-insurance", get(my_insurance))
            .with_state(s)
    }

    #[tokio::test]
    async fn comeback_status_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/users/me/streak/comeback-status")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn my_insurance_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/users/me/streak-insurance")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
