//! Badge, Quest, and Achievement route handlers.
//!
//! Phase 7 (Tasks 8.1–8.3): Badges, Quests, Achievements migration.

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
use crate::routes::auth::AuthState;
use crate::services::badge_service;

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
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// POST /api/v1/badges/{badge_id}/award — award badge (idempotent).
pub async fn award_badge(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(badge_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = badge_service::award_badge(pool, badge_id, user_id).await?;
    Ok(Json(result))
}

/// GET /api/v1/quests — list quests.
pub async fn list_quests(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let quests = badge_service::list_quests(pool, user_id).await?;
    Ok(Json(quests))
}

/// GET /api/v1/quests/{quest_slug} — quest detail.
pub async fn get_quest_detail(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(quest_slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let quest = badge_service::get_quest_detail(pool, &quest_slug, user_id).await?;
    Ok(Json(quest))
}

/// POST /api/v1/quests/{quest_slug}/start — start a quest.
pub async fn start_quest(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(quest_slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = badge_service::start_quest(pool, &quest_slug, user_id).await?;
    Ok(Json(result))
}

/// GET /api/v1/users/me/quest-summary — quest summary.
pub async fn get_quest_summary(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let summary = badge_service::get_quest_summary(pool, user_id).await?;
    Ok(Json(summary))
}

/// GET /api/v1/quests/weekly — weekly quests.
pub async fn get_weekly_quests(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let quests = badge_service::get_weekly_quests(pool, user_id).await?;
    Ok(Json(quests))
}

/// GET /api/v1/missions/daily — daily missions.
pub async fn get_daily_missions(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let missions = badge_service::get_daily_missions(pool, user_id).await?;
    Ok(Json(missions))
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
            .route("/api/v1/badges/:badge_id/award", post(award_badge))
            .route("/api/v1/quests", get(list_quests))
            .route("/api/v1/quests/weekly", get(get_weekly_quests))
            .route("/api/v1/quests/:quest_slug", get(get_quest_detail))
            .route("/api/v1/quests/:quest_slug/start", post(start_quest))
            .route("/api/v1/users/me/quest-summary", get(get_quest_summary))
            .route("/api/v1/missions/daily", get(get_daily_missions))
            .with_state(state)
    }

    #[tokio::test]
    async fn award_badge_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/badges/00000000-0000-0000-0000-000000000001/award")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_quests_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/quests")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_quests_returns_503_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/quests")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn quest_detail_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/quests/test-quest")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn start_quest_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/quests/test-quest/start")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn quest_summary_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/users/me/quest-summary")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn daily_missions_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/missions/daily")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
