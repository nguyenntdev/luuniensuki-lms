//! User profile route handlers and DTOs.
//!
//! Phase 3 (Tasks 4.1–4.7): Users & Profile migration.
//! Implements profile update, change-password, starting-path,
//! onboarding, avatar upload, and public profile endpoints.

use axum::{
    extract::{Multipart, Path, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::routes::auth::AuthState;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_AVATAR_SIZE: usize = 5 * 1024 * 1024; // 5 MB
const ALLOWED_IMAGE_TYPES: &[&str] = &["image/jpeg", "image/png", "image/webp"];

// ---------------------------------------------------------------------------
// Request/Response DTOs
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

/// User profile response (returned from PATCH /users/me).
#[derive(Debug, Serialize)]
pub struct UserProfileResponse {
    pub id: String,
    pub email: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub role: String,
    pub total_xp: i64,
    pub starting_urn_id: Option<String>,
    pub is_profile_public: bool,
    pub ai_personalization_enabled: bool,
}

/// PATCH /api/v1/users/me response envelope.
#[derive(Debug, Serialize)]
pub struct UpdateProfileResponse {
    pub user: UserProfileResponse,
    pub message: String,
}
