//! Classroom & Membership route handlers.
//!
//! Phase 8 (Tasks 9.1–9.4): Classrooms & Memberships migration.

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
use crate::models::classroom::*;
use crate::routes::auth::AuthState;
use crate::services::classroom_service;

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

/// POST /api/v1/classrooms — create classroom.
pub async fn create_classroom(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<CreateClassroomRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let classroom = classroom_service::create_classroom(pool, user_id, &payload).await?;
    Ok((StatusCode::CREATED, Json(classroom)))
}

/// GET /api/v1/classrooms — list classrooms.
pub async fn list_classrooms(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let classrooms = classroom_service::list_classrooms(pool, user_id).await?;
    Ok(Json(classrooms))
}

/// GET /api/v1/classrooms/{id} — classroom detail.
pub async fn get_classroom(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let classroom = classroom_service::get_classroom(pool, id, user_id).await?;
    Ok(Json(classroom))
}

/// PATCH /api/v1/classrooms/{id} — update classroom.
pub async fn update_classroom(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Json(payload): Json<UpdateClassroomRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let classroom = classroom_service::update_classroom(pool, id, user_id, &payload).await?;
    Ok(Json(classroom))
}

/// DELETE /api/v1/classrooms/{id} — archive classroom.
pub async fn archive_classroom(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    classroom_service::archive_classroom(pool, id, user_id).await?;
    Ok(StatusCode::NO_CONTENT)
}

/// GET /api/v1/classrooms/{id}/members — list members.
pub async fn list_members(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let members = classroom_service::list_members(pool, id, user_id).await?;
    Ok(Json(members))
}

/// POST /api/v1/classrooms/{id}/members — add member.
pub async fn add_member(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Json(payload): Json<AddMemberRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let member = classroom_service::add_member(pool, id, user_id, &payload).await?;
    Ok((StatusCode::CREATED, Json(member)))
}

/// DELETE /api/v1/classrooms/{id}/members/{user_id} — remove member.
pub async fn remove_member(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path((id, target_user_id)): Path<(Uuid, Uuid)>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    classroom_service::remove_member(pool, id, user_id, target_user_id).await?;
    Ok(StatusCode::NO_CONTENT)
}

/// GET /api/v1/classrooms/{id}/lessons — classroom lessons.
pub async fn list_classroom_lessons(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let lessons = classroom_service::list_classroom_lessons(pool, id, user_id).await?;
    Ok(Json(lessons))
}

/// POST /api/v1/classrooms/{id}/lessons — assign lesson.
pub async fn assign_lesson(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Json(payload): Json<AssignLessonRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let lesson = classroom_service::assign_lesson(pool, id, user_id, &payload).await?;
    Ok((StatusCode::CREATED, Json(lesson)))
}

/// GET /api/v1/classrooms/{id}/analytics — classroom analytics.
pub async fn get_classroom_analytics(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let analytics = classroom_service::get_classroom_analytics(pool, id, user_id).await?;
    Ok(Json(analytics))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{body::Body, http::Request, routing::{delete, get, patch, post}, Router};
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/classrooms", post(create_classroom).get(list_classrooms))
            .route("/api/v1/classrooms/:id", get(get_classroom).patch(update_classroom).delete(archive_classroom))
            .route("/api/v1/classrooms/:id/members", get(list_members).post(add_member))
            .route("/api/v1/classrooms/:id/members/:user_id", delete(remove_member))
            .route("/api/v1/classrooms/:id/lessons", get(list_classroom_lessons).post(assign_lesson))
            .route("/api/v1/classrooms/:id/analytics", get(get_classroom_analytics))
            .with_state(state)
    }

    #[tokio::test]
    async fn create_classroom_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/classrooms")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"name":"Test"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_classrooms_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/classrooms")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_classrooms_returns_503_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001", "user",
            &state.settings.jwt_secret_key, 60,
        ).unwrap();
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/classrooms")
                .header("Authorization", format!("Bearer {}", token))
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn get_classroom_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/classrooms/00000000-0000-0000-0000-000000000001")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn archive_classroom_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("DELETE")
                .uri("/api/v1/classrooms/00000000-0000-0000-0000-000000000001")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn list_members_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/classrooms/00000000-0000-0000-0000-000000000001/members")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn classroom_analytics_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .uri("/api/v1/classrooms/00000000-0000-0000-0000-000000000001/analytics")
                .body(Body::empty()).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }
}
