//! Progress, Streak, Hearts, Daily Goal, and Milestone route handlers.
//!
//! Phase 6 (Tasks 7.1–7.3): Progress & Streaks migration.

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
use crate::models::progress::*;
use crate::routes::auth::AuthState;
use crate::services::progress_service;

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

/// POST /api/v1/progress/unlock — unlock/discover a motif.
pub async fn unlock_motif(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<UnlockMotifRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = progress_service::unlock_motif(pool, user_id, &payload).await?;
    Ok(Json(result))
}

/// GET /api/v1/users/me/streak — get user streak data.
pub async fn get_streak(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let streak = progress_service::get_streak(pool, user_id).await?;
    Ok(Json(streak))
}

/// POST /api/v1/users/me/streak — update streak (heartbeat).
pub async fn update_streak(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<StreakHeartbeatRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = progress_service::update_streak_heartbeat(pool, user_id, &payload).await?;
    Ok(Json(result))
}

/// GET /api/v1/users/me/hearts — get hearts balance.
pub async fn get_hearts(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let hearts = progress_service::get_hearts(pool, user_id).await?;
    Ok(Json(hearts))
}

/// POST /api/v1/users/me/hearts — spend/refill hearts.
pub async fn update_hearts(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<HeartsActionRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = progress_service::update_hearts(pool, user_id, &payload).await?;
    Ok(Json(result))
}

/// GET /api/v1/users/me/daily-goal — get daily goal settings.
pub async fn get_daily_goal(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let goal = progress_service::get_daily_goal(pool, user_id).await?;
    Ok(Json(goal))
}

/// PUT /api/v1/users/me/daily-goal — update daily goal.
pub async fn update_daily_goal(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<UpdateDailyGoalRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = progress_service::update_daily_goal(pool, user_id, &payload).await?;
    Ok(Json(result))
}

/// GET /api/v1/users/me/milestones — get user milestones.
pub async fn get_milestones(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let milestones = progress_service::get_milestones(pool, user_id).await?;
    Ok(Json(milestones))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::{get, post, put}, Router};
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/progress/unlock", post(unlock_motif))
            .route("/api/v1/users/me/streak", get(get_streak).post(update_streak))
            .route("/api/v1/users/me/hearts", get(get_hearts).post(update_hearts))
            .route("/api/v1/users/me/daily-goal", get(get_daily_goal).put(update_daily_goal))
            .route("/api/v1/users/me/milestones", get(get_milestones))
            .with_state(state)
    }

    #[tokio::test]
    async fn unlock_motif_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/progress/unlock")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"motif_id":"00000000-0000-0000-0000-000000000001"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_streak_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/users/me/streak")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_streak_returns_503_without_pool() {
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
                .uri("/api/v1/users/me/streak")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn get_hearts_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/users/me/hearts")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_daily_goal_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/users/me/daily-goal")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_milestones_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/users/me/milestones")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn update_streak_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/users/me/streak")
                .header("content-type", "application/json")
                .body(Body::from(r#"{}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
