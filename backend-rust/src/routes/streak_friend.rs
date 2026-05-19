//! Friend streak user-facing routes.
//!
//! - `GET /api/v1/users/me/friend-streaks`
//! - `GET /api/v1/users/:other_id/friend-streak`
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use axum::{
    extract::{Path, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::streak_economy::FriendStreaksResponse;
use crate::routes::auth::AuthState;
use crate::services::streak_friend_service;

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

/// `GET /api/v1/users/me/friend-streaks`.
pub async fn list_my_friend_streaks(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let rows = streak_friend_service::list_my_friend_streaks(pool, user_id).await?;
    Ok(Json(FriendStreaksResponse {
        friend_streaks: rows,
    }))
}

/// `GET /api/v1/users/:other_id/friend-streak`.
pub async fn get_friend_streak(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(other_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let row = streak_friend_service::get_friend_streak(pool, user_id, other_id).await?;
    Ok(Json(row))
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
            .route("/api/v1/users/me/friend-streaks", get(list_my_friend_streaks))
            .route("/api/v1/users/:other_id/friend-streak", get(get_friend_streak))
            .with_state(s)
    }

    #[tokio::test]
    async fn list_my_friend_streaks_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/users/me/friend-streaks")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
