//! User profile route handlers and DTOs.
//!
//! Phase 3 (Tasks 4.1–4.7): Users & Profile migration.
//! Implements profile update, change-password, starting-path,
//! onboarding, avatar upload, and public profile endpoints.

use axum::{
    extract::{Multipart, Path, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde::Deserialize;
use serde_json::json;
use sqlx::PgPool;
use std::path::PathBuf;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::user::{
    OnboardingStatusResponse, StartingPathResponse, UpdateProfileEnvelope,
    UserPublicProfileResponse,
};
use crate::routes::auth::AuthState;
use crate::services::user_service;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_AVATAR_SIZE: usize = 5 * 1024 * 1024; // 5 MB
const ALLOWED_IMAGE_TYPES: &[&str] = &["image/jpeg", "image/png", "image/webp"];

// ---------------------------------------------------------------------------
// Request DTOs
// ---------------------------------------------------------------------------

/// PATCH /api/v1/users/me request body.
#[derive(Debug, Deserialize)]
pub struct UpdateProfileRequest {
    pub display_name: Option<String>,
    pub username: Option<String>,
    pub bio: Option<String>,
    pub is_profile_public: Option<bool>,
    pub ai_personalization_enabled: Option<bool>,
}

/// POST /api/v1/users/me/change-password request body.
#[derive(Debug, Deserialize)]
pub struct ChangePasswordRequest {
    pub current_password: String,
    pub new_password: String,
}

/// POST /api/v1/users/me/starting-path request body.
#[derive(Debug, Deserialize)]
pub struct StartingPathRequest {
    pub urn_id: Option<Uuid>,
    pub urn_slug: Option<String>,
}

/// POST /api/v1/onboarding/goals request body.
#[derive(Debug, Deserialize)]
pub struct OnboardingGoalRequest {
    pub goal: String,
}

// ---------------------------------------------------------------------------
// Auth helper (reuses pattern from routes/auth.rs)
// ---------------------------------------------------------------------------

/// Extract JWT claims from the request headers.
/// Checks Authorization: Bearer header first, then the access cookie.
fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    // 1. Try Authorization: Bearer <token>
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }

    // 2. Try luuniensuki_access cookie
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

/// Require a valid DB pool or return 503.
fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

/// Extract and verify the authenticated user ID from headers.
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

/// PATCH /api/v1/users/me — update current user's profile.
pub async fn update_profile(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<UpdateProfileRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let row = user_service::update_profile(
        pool,
        user_id,
        payload.display_name.as_deref(),
        payload.username.as_deref(),
        payload.bio.as_deref(),
        payload.is_profile_public,
        payload.ai_personalization_enabled,
    )
    .await?;

    Ok(Json(UpdateProfileEnvelope {
        user: row.into_profile_response(),
        message: "Profile updated successfully".to_string(),
    }))
}

/// POST /api/v1/users/me/change-password — change current user's password.
pub async fn change_password(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<ChangePasswordRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    // Validate new password length (min 8, matching Python's Field(..., min_length=8))
    if payload.new_password.len() < 8 {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "VALIDATION_ERROR".to_string(),
            message: "New password must be at least 8 characters".to_string(),
            details: json!({}),
        });
    }

    user_service::change_password(
        pool,
        user_id,
        &payload.current_password,
        &payload.new_password,
    )
    .await?;

    Ok(Json(json!({"message": "Password changed successfully"})))
}

/// POST /api/v1/users/me/starting-path — set user's starting learning path.
pub async fn set_starting_path(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<StartingPathRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let (urn_id, urn_slug) = user_service::set_starting_path(
        pool,
        user_id,
        payload.urn_id,
        payload.urn_slug.as_deref(),
    )
    .await?;

    Ok(Json(StartingPathResponse {
        starting_urn_id: urn_id.to_string(),
        starting_urn_slug: urn_slug,
    }))
}

/// POST /api/v1/onboarding/goals — save user's onboarding goal.
pub async fn save_onboarding_goal(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<OnboardingGoalRequest>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let goal = user_service::set_onboarding_goal(pool, user_id, &payload.goal).await?;

    Ok(Json(json!({
        "success": true,
        "message": "Onboarding goal saved successfully",
        "goal": goal,
    })))
}

/// GET /api/v1/onboarding/status — get user's onboarding status.
pub async fn get_onboarding_status(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let (completed, goal, completed_at) =
        user_service::get_onboarding(pool, user_id).await?;

    Ok(Json(OnboardingStatusResponse {
        onboarding_completed: completed,
        onboarding_goal: goal,
        onboarding_completed_at: completed_at.map(|dt| dt.to_rfc3339()),
    }))
}

/// POST /api/v1/onboarding/complete — mark onboarding as complete.
pub async fn complete_onboarding(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let (completed, completed_at) =
        user_service::complete_onboarding(pool, user_id).await?;

    let message = if completed_at.is_some() {
        "Onboarding completed successfully"
    } else {
        "Onboarding already completed"
    };

    Ok(Json(json!({
        "success": true,
        "message": message,
        "onboarding_completed": completed,
        "onboarding_completed_at": completed_at.map(|dt| dt.to_rfc3339()),
    })))
}

/// POST /api/v1/users/me/avatar — upload user avatar (multipart).
pub async fn upload_avatar(
    headers: HeaderMap,
    State(state): State<AuthState>,
    mut multipart: Multipart,
) -> Result<impl IntoResponse, AppError> {
    let user_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    // Extract the file field from multipart
    let mut file_data: Option<(String, Vec<u8>)> = None;

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| AppError::Http {
            status: StatusCode::BAD_REQUEST,
            message: format!("Invalid multipart data: {}", e),
        })?
    {
        let name = field.name().unwrap_or("").to_string();
        if name == "file" {
            let content_type = field
                .content_type()
                .unwrap_or("application/octet-stream")
                .to_string();

            // Validate MIME type
            if !ALLOWED_IMAGE_TYPES.contains(&content_type.as_str()) {
                return Err(AppError::Domain {
                    status: StatusCode::BAD_REQUEST,
                    code: "INVALID_IMAGE_TYPE".to_string(),
                    message: "Unsupported image type".to_string(),
                    details: json!({"content_type": content_type}),
                });
            }

            // Read file data with size limit
            let data = field
                .bytes()
                .await
                .map_err(|e| AppError::Http {
                    status: StatusCode::BAD_REQUEST,
                    message: format!("Failed to read file: {}", e),
                })?;

            if data.len() > MAX_AVATAR_SIZE {
                return Err(AppError::Domain {
                    status: StatusCode::BAD_REQUEST,
                    code: "AVATAR_TOO_LARGE".to_string(),
                    message: "Avatar file too large".to_string(),
                    details: json!({"max_bytes": MAX_AVATAR_SIZE}),
                });
            }

            file_data = Some((content_type, data.to_vec()));
            break;
        }
    }

    let (content_type, data) = file_data.ok_or_else(|| AppError::Http {
        status: StatusCode::BAD_REQUEST,
        message: "No file field in multipart data".to_string(),
    })?;

    // Determine extension from MIME type
    let extension = match content_type.as_str() {
        "image/jpeg" => "jpg",
        "image/png" => "png",
        "image/webp" => "webp",
        _ => "bin",
    };

    // Generate filename: {user_id}_{uuid}.{ext}
    let filename = format!("{}_{}.{}", user_id, Uuid::new_v4(), extension);

    // Write to uploads directory
    let upload_dir = PathBuf::from(&state.settings.uploads_dir).join("avatars");
    tokio::fs::create_dir_all(&upload_dir)
        .await
        .map_err(|e| AppError::Internal(anyhow::anyhow!("Failed to create upload dir: {}", e)))?;

    let destination = upload_dir.join(&filename);
    tokio::fs::write(&destination, &data)
        .await
        .map_err(|e| AppError::Internal(anyhow::anyhow!("Failed to write avatar: {}", e)))?;

    // Update user's avatar_url in DB (matches Python's URL pattern)
    let avatar_url = format!("/assets/avatars/{}", filename);
    sqlx::query("UPDATE users SET avatar_url = $1, updated_at = NOW() WHERE id = $2")
        .bind(&avatar_url)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(Json(json!({"avatar_url": avatar_url})))
}

/// GET /api/v1/users/{user_id}/public — get a user's public profile.
pub async fn get_user_public_profile(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(target_user_id): Path<Uuid>,
) -> Result<impl IntoResponse, AppError> {
    let requester_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let row =
        user_service::get_public_profile(pool, target_user_id, requester_id).await?;

    Ok(Json(row.into_public_response()))
}

/// GET /api/v1/u/{username_or_id} — resolve user by username or UUID.
pub async fn get_user_by_identifier(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(identifier): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let requester_id = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let row = user_service::resolve_user_by_id_or_username(
        pool,
        &identifier,
        requester_id,
    )
    .await?;

    Ok(Json(row.into_public_response()))
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::{to_bytes, Body},
        http::Request,
        routing::{get, patch, post},
        Router,
    };
    use serde_json::Value;
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
            .route("/api/v1/users/me", patch(update_profile))
            .route(
                "/api/v1/users/me/change-password",
                post(change_password),
            )
            .route(
                "/api/v1/users/me/starting-path",
                post(set_starting_path),
            )
            .route("/api/v1/onboarding/goals", post(save_onboarding_goal))
            .route(
                "/api/v1/onboarding/status",
                get(get_onboarding_status),
            )
            .route(
                "/api/v1/onboarding/complete",
                post(complete_onboarding),
            )
            .route("/api/v1/users/me/avatar", post(upload_avatar))
            .route(
                "/api/v1/users/:user_id/public",
                get(get_user_public_profile),
            )
            .route("/api/v1/u/:identifier", get(get_user_by_identifier))
            .with_state(state)
    }

    #[tokio::test]
    async fn update_profile_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("PATCH")
                    .uri("/api/v1/users/me")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"display_name":"Test"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn change_password_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/users/me/change-password")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"current_password":"old","new_password":"newpass123"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn starting_path_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/users/me/starting-path")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"urn_slug":"test"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn onboarding_goals_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/onboarding/goals")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"goal":"learn_culture"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn onboarding_status_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/onboarding/status")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn avatar_upload_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/users/me/avatar")
                    .header(
                        "content-type",
                        "multipart/form-data; boundary=boundary123",
                    )
                    .body(Body::from(
                        "--boundary123\r\n\
                         Content-Disposition: form-data; name=\"file\"; filename=\"test.png\"\r\n\
                         Content-Type: image/png\r\n\r\n\
                         fake-png-data\r\n\
                         --boundary123--\r\n",
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn update_profile_returns_503_when_pool_is_none() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();

        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("PATCH")
                    .uri("/api/v1/users/me")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{"display_name":"Test"}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn change_password_validates_min_length() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
        )
        .unwrap();

        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/users/me/change-password")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"current_password":"oldpass","new_password":"short"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        // Should fail validation before hitting DB (which is None → 503)
        assert_eq!(resp.status(), StatusCode::BAD_REQUEST);

        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "VALIDATION_ERROR");
    }

    // Unit tests for validation helpers
    #[test]
    fn test_is_valid_display_name() {
        assert!(user_service::is_valid_display_name("John Doe"));
        assert!(user_service::is_valid_display_name("Test123"));
        assert!(user_service::is_valid_display_name("Nguyễn"));
        assert!(!user_service::is_valid_display_name("Test@Name"));
        assert!(!user_service::is_valid_display_name("Test#Name"));
        assert!(!user_service::is_valid_display_name("日本語")); // Non-Latin
    }

    #[test]
    fn test_is_valid_username() {
        assert!(user_service::is_valid_username("abc"));
        assert!(user_service::is_valid_username("user_123"));
        assert!(user_service::is_valid_username("A_very_long_name_12"));
        assert!(!user_service::is_valid_username("ab")); // too short
        assert!(!user_service::is_valid_username("a".repeat(21).as_str())); // too long
        assert!(!user_service::is_valid_username("user name")); // space
        assert!(!user_service::is_valid_username("user@name")); // special char
    }
}
