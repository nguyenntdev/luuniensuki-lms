//! Lesson, Motif, and Urn route handlers.
//!
//! Phase 4 (Tasks 5.1–5.5): Lessons & Content migration.

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
use crate::models::lesson::LessonCacheIn;
use crate::routes::auth::AuthState;
use crate::services::lesson_service;

// ---------------------------------------------------------------------------
// Auth helpers (same pattern as routes/users.rs)
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
pub struct UrnIdQuery {
    pub urn_id: Option<Uuid>,
}

// ---------------------------------------------------------------------------
// Urn handlers (Task 5.2)
// ---------------------------------------------------------------------------

/// GET /api/v1/urns — list all urns with user progress.
pub async fn list_urns(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let urns = lesson_service::list_urns(pool, user_id).await?;
    Ok(Json(urns))
}

/// GET /api/v1/urns/{urn_slug} — urn detail with motifs.
pub async fn get_urn_detail(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(urn_slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let detail = lesson_service::get_urn_detail(pool, &urn_slug, user_id).await?;
    Ok(Json(detail))
}

/// GET /api/v1/urns/{urn_slug}/progress — urn progress for user.
pub async fn get_urn_progress(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(urn_slug): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let progress = lesson_service::get_urn_progress(pool, &urn_slug, user_id).await?;
    Ok(Json(progress))
}

// ---------------------------------------------------------------------------
// Motif handlers (Task 5.3)
// ---------------------------------------------------------------------------

/// GET /motifs/{urn_name} — list motifs by urn name/slug.
pub async fn get_motifs_by_urn(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(urn_name): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = lesson_service::list_motifs_by_urn(pool, &urn_name, user_id).await?;
    Ok(Json(result))
}

/// GET /api/v1/motifs/{motif_id} — motif detail.
pub async fn get_motif_detail(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(motif_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let detail = lesson_service::get_motif_detail(pool, motif_id, user_id).await?;
    Ok(Json(detail))
}

// ---------------------------------------------------------------------------
// Complete lesson handler (Task 5.5)
// ---------------------------------------------------------------------------

/// POST /api/v1/motifs/{motif_id}/complete-lesson — complete a lesson.
pub async fn complete_lesson(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(motif_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = lesson_service::complete_lesson(pool, motif_id, user_id).await?;
    Ok(Json(result))
}

// ---------------------------------------------------------------------------
// Lesson cache & sequence handlers (Task 5.4)
// ---------------------------------------------------------------------------

/// GET /api/v1/lessons/cache-manifest — get cache manifest.
pub async fn get_cache_manifest(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let manifest = lesson_service::get_cache_manifest(pool, user_id).await?;
    Ok(Json(manifest))
}

/// GET /api/v1/lessons/next — get next recommended lesson.
pub async fn get_next_lesson(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<UrnIdQuery>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let next = lesson_service::get_next_lesson(pool, user_id, params.urn_id).await?;
    Ok(Json(next))
}

/// GET /api/v1/lessons/{lesson_id}/prerequisites — get lesson prerequisites.
pub async fn get_lesson_prerequisites(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(lesson_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let prereqs = lesson_service::get_lesson_prerequisites(pool, lesson_id, user_id).await?;
    Ok(Json(prereqs))
}

/// GET /api/v1/lessons/{lesson_id}/is-unlocked — check if lesson is unlocked.
pub async fn check_lesson_is_unlocked(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(lesson_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let status = lesson_service::is_lesson_unlocked(pool, lesson_id, user_id).await?;
    Ok(Json(status))
}

/// GET /api/v1/lessons/sequence — get full learning sequence.
pub async fn get_lesson_sequence(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(params): Query<UrnIdQuery>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let seq = lesson_service::get_lesson_sequence(pool, user_id, params.urn_id).await?;
    Ok(Json(seq))
}

/// POST /api/v1/lessons/{lesson_id}/cache — mark lesson as cached.
pub async fn mark_lesson_cached(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(lesson_id): Path<Uuid>,
    Json(payload): Json<LessonCacheIn>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let cache = lesson_service::mark_lesson_cached(pool, lesson_id, user_id, &payload).await?;
    Ok(Json(cache))
}

/// DELETE /api/v1/lessons/{lesson_id}/cache — remove cached lesson.
pub async fn remove_cached_lesson(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(lesson_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    lesson_service::remove_cached_lesson(pool, lesson_id, user_id).await?;
    Ok(StatusCode::NO_CONTENT)
}

/// GET /api/v1/lessons/cached — get all cached lessons.
pub async fn get_cached_lessons(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let cached = lesson_service::get_cached_lessons(pool, user_id).await?;
    Ok(Json(cached))
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
        routing::{delete, get, post},
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
            .route("/api/v1/urns", get(list_urns))
            .route("/api/v1/urns/:urn_slug", get(get_urn_detail))
            .route("/api/v1/urns/:urn_slug/progress", get(get_urn_progress))
            .route("/motifs/:urn_name", get(get_motifs_by_urn))
            .route("/api/v1/motifs/:motif_id", get(get_motif_detail))
            .route(
                "/api/v1/motifs/:motif_id/complete-lesson",
                post(complete_lesson),
            )
            .route("/api/v1/lessons/cache-manifest", get(get_cache_manifest))
            .route("/api/v1/lessons/next", get(get_next_lesson))
            .route(
                "/api/v1/lessons/:lesson_id/prerequisites",
                get(get_lesson_prerequisites),
            )
            .route(
                "/api/v1/lessons/:lesson_id/is-unlocked",
                get(check_lesson_is_unlocked),
            )
            .route("/api/v1/lessons/sequence", get(get_lesson_sequence))
            .route(
                "/api/v1/lessons/:lesson_id/cache",
                post(mark_lesson_cached).delete(remove_cached_lesson),
            )
            .route("/api/v1/lessons/cached", get(get_cached_lessons))
            .with_state(state)
    }

    #[tokio::test]
    async fn list_urns_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/urns")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_urns_returns_503_without_pool() {
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
                    .uri("/api/v1/urns")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn urn_detail_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/urns/test-urn")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn motifs_by_urn_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/motifs/test-urn")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn motif_detail_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/motifs/00000000-0000-0000-0000-000000000001")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn complete_lesson_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/motifs/00000000-0000-0000-0000-000000000001/complete-lesson")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn cache_manifest_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/cache-manifest")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn next_lesson_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/next")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn lesson_prerequisites_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/00000000-0000-0000-0000-000000000001/prerequisites")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn lesson_is_unlocked_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/00000000-0000-0000-0000-000000000001/is-unlocked")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn lesson_sequence_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/sequence")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn cached_lessons_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/lessons/cached")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn complete_lesson_returns_503_without_pool() {
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
                    .method("POST")
                    .uri("/api/v1/motifs/00000000-0000-0000-0000-000000000001/complete-lesson")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}
