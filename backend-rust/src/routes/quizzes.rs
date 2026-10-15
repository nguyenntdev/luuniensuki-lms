//! Quiz & Adaptive route handlers.
//!
//! Phase 5 (Tasks 6.1–6.4): Quizzes & Adaptive migration.

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
use crate::models::quiz::{AdaptiveQuizRequest, QuizSubmitRequest};
use crate::routes::auth::AuthState;
use crate::services::quiz_service;

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
// Handlers
// ---------------------------------------------------------------------------

/// GET /api/v1/quizzes/{quiz_id} — fetch quiz with questions.
pub async fn get_quiz(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(quiz_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let quiz = quiz_service::get_quiz(pool, quiz_id, user_id).await?;
    Ok(Json(quiz))
}

/// POST /api/v1/quizzes/{quiz_id}/submit — submit quiz answers.
pub async fn submit_quiz(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(quiz_id): Path<Uuid>,
    Json(payload): Json<QuizSubmitRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = quiz_service::submit_quiz(pool, quiz_id, user_id, &payload).await?;
    Ok(Json(result))
}

/// POST /api/v1/quizzes/adaptive — adaptive quiz generation.
pub async fn adaptive_quiz(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<AdaptiveQuizRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = quiz_service::generate_adaptive_quiz(pool, user_id, &payload).await?;
    Ok(Json(result))
}

/// GET /api/v1/quizzes/{quiz_id}/hints — get hints for a quiz.
pub async fn get_quiz_hints(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(quiz_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let hints = quiz_service::get_quiz_hints(pool, quiz_id, user_id).await?;
    Ok(Json(hints))
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
        routing::{get, post},
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
            .route("/api/v1/quizzes/:quiz_id", get(get_quiz))
            .route("/api/v1/quizzes/:quiz_id/submit", post(submit_quiz))
            .route("/api/v1/quizzes/adaptive", post(adaptive_quiz))
            .route("/api/v1/quizzes/:quiz_id/hints", get(get_quiz_hints))
            .with_state(state)
    }

    #[tokio::test]
    async fn get_quiz_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/quizzes/00000000-0000-0000-0000-000000000001")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_quiz_returns_503_without_pool() {
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
                    .uri("/api/v1/quizzes/00000000-0000-0000-0000-000000000001")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn submit_quiz_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/quizzes/00000000-0000-0000-0000-000000000001/submit")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"answers":[]}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn adaptive_quiz_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/quizzes/adaptive")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn get_hints_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/quizzes/00000000-0000-0000-0000-000000000001/hints")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
