//! User row DTOs and response DTOs.
//!
//! Mirrors `backend/models.py::User` for the fields needed by Phase 3 routes.

use chrono::{DateTime, Utc};
use serde::Serialize;
use sqlx::FromRow;
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Database row DTOs
// ---------------------------------------------------------------------------

/// Full user row for profile operations.
#[derive(Debug, FromRow)]
pub struct UserRow {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub bio: Option<String>,
    pub role: String,
    pub total_xp: i64,
    pub starting_urn_id: Option<Uuid>,
    pub is_profile_public: bool,
    pub ai_personalization_enabled: bool,
    pub password_hash: String,
    pub onboarding_goal: Option<String>,
    pub onboarding_completed: bool,
    pub onboarding_completed_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

/// Minimal user row for public profile lookups.
#[derive(Debug, FromRow)]
pub struct UserPublicRow {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub username: Option<String>,
    pub bio: Option<String>,
    pub role: String,
    pub total_xp: i64,
    pub is_profile_public: bool,
    pub created_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Response DTOs
// ---------------------------------------------------------------------------

/// User profile response (returned from PATCH /users/me).
#[derive(Debug, Serialize, Clone)]
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
pub struct UpdateProfileEnvelope {
    pub user: UserProfileResponse,
    pub message: String,
}

/// Onboarding status response.
#[derive(Debug, Serialize)]
pub struct OnboardingStatusResponse {
    pub onboarding_completed: bool,
    pub onboarding_goal: Option<String>,
    pub onboarding_completed_at: Option<String>,
}

/// Starting path response.
#[derive(Debug, Serialize)]
pub struct StartingPathResponse {
    pub starting_urn_id: String,
    pub starting_urn_slug: String,
}

/// Public profile response (GET /api/v1/users/{id}/public).
#[derive(Debug, Serialize)]
pub struct UserPublicProfileResponse {
    pub id: String,
    pub username: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub total_xp: i64,
    pub is_profile_public: bool,
}

impl UserRow {
    /// Convert to the profile response DTO.
    pub fn into_profile_response(self) -> UserProfileResponse {
        UserProfileResponse {
            id: self.id.to_string(),
            email: self.email,
            display_name: self.display_name,
            avatar_url: self.avatar_url,
            username: self.username,
            role: self.role,
            total_xp: self.total_xp,
            starting_urn_id: self.starting_urn_id.map(|u| u.to_string()),
            is_profile_public: self.is_profile_public,
            ai_personalization_enabled: self.ai_personalization_enabled,
        }
    }
}

impl UserPublicRow {
    /// Convert to the public profile response DTO.
    pub fn into_public_response(self) -> UserPublicProfileResponse {
        let username = self
            .username
            .clone()
            .unwrap_or_else(|| {
                self.email
                    .split('@')
                    .next()
                    .unwrap_or(&self.id.to_string())
                    .to_string()
            });
        UserPublicProfileResponse {
            id: self.id.to_string(),
            username,
            display_name: self.display_name,
            avatar_url: self.avatar_url,
            bio: self.bio,
            total_xp: self.total_xp,
            is_profile_public: self.is_profile_public,
        }
    }
}
