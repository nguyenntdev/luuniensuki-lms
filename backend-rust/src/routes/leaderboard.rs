//! Leaderboard & League route handlers.
//!
//! Phase 9 (Tasks 10.1–10.2): Leaderboards & Leagues migration.

use axum::{
    extract::{Path, Query, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::leaderboard::LeaderboardQuery;
use crate::routes::auth::AuthState;
use crate::services::leaderboard_service;

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
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key, settings.jwt_validate_new_claims, &settings.jwt_issuer, &settings.jwt_audience)
        .map_err(|_| AppError::Unauthorized)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/leaderboard — global leaderboard.
pub async fn get_leaderboard(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<LeaderboardQuery>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let leaderboard = leaderboard_service::get_leaderboard(pool, user_id, &params).await?;
    Ok(Json(leaderboard))
}

/// GET /api/v1/leaderboard/friends — friends leaderboard.
pub async fn get_friends_leaderboard(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<LeaderboardQuery>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let leaderboard = leaderboard_service::get_friends_leaderboard(pool, user_id, &params).await?;
    Ok(Json(leaderboard))
}

/// GET /api/v1/leagues — list leagues.
pub async fn list_leagues(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let _user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let leagues = leaderboard_service::list_leagues(pool).await?;
    Ok(Json(leagues))
}

/// GET /api/v1/leagues/me — user's current league.
pub async fn get_user_league(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let league = leaderboard_service::get_user_league(pool, user_id).await?;
    Ok(Json(league))
}

/// GET /api/v1/leagues/{league_id} — league detail.
pub async fn get_league_detail(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(league_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let _user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let league = leaderboard_service::get_league_detail(pool, league_id).await?;
    Ok(Json(league))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::get, Router};
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/leaderboard", get(get_leaderboard))
            .route("/api/v1/leaderboard/friends", get(get_friends_leaderboard))
            .route("/api/v1/leagues", get(list_leagues))
            .route("/api/v1/leagues/me", get(get_user_league))
            .route("/api/v1/leagues/:league_id", get(get_league_detail))
            .with_state(state)
    }

    #[tokio::test]
    async fn leaderboard_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/leaderboard")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn leaderboard_returns_503_without_pool() {
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
                .uri("/api/v1/leaderboard")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn friends_leaderboard_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/leaderboard/friends")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_leagues_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/leagues")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn user_league_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/leagues/me")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn league_detail_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/leagues/00000000-0000-0000-0000-000000000001")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
