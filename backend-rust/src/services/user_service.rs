//! User service: business logic for profile, password, onboarding, public profile.
//!
//! Phase 3 (Tasks 4.1–4.5): mirrors the Python handlers' DB interactions.

use axum::http::StatusCode;
use chrono::Utc;
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::error::AppError;
use crate::models::user::{UserPublicRow, UserRow};

// ---------------------------------------------------------------------------
// Display name validation (mirrors Python's _is_valid_display_name)
// ---------------------------------------------------------------------------

/// Validate display name: only Latin letters, digits, and spaces allowed.
/// Mirrors Python's `_is_valid_display_name` which checks NFC-normalized chars.
pub fn is_valid_display_name(display_name: &str) -> bool {
    for ch in display_name.chars() {
        if ch == ' ' {
            continue;
        }
        if ch.is_ascii_digit() {
            continue;
        }
        // Latin letters (Basic Latin + Latin Extended)
        if ch.is_alphabetic() && is_latin_char(ch) {
            continue;
        }
        return false;
    }
    true
}

/// Check if a character is a Latin script character.
/// This approximates Python's `unicodedata.name(ch).contains("LATIN")`.
fn is_latin_char(ch: char) -> bool {
    // Basic Latin letters
    if ch.is_ascii_alphabetic() {
        return true;
    }
    // Latin Extended characters (U+00C0–U+024F covers Latin-1 Supplement
    // and Latin Extended-A/B which have "LATIN" in their Unicode name)
    let code = ch as u32;
    (0x00C0..=0x024F).contains(&code)
        || (0x1E00..=0x1EFF).contains(&code) // Latin Extended Additional
        || (0x2C60..=0x2C7F).contains(&code) // Latin Extended-C
        || (0xA720..=0xA7FF).contains(&code) // Latin Extended-D
}

/// Username regex: 3-20 chars, only [a-zA-Z0-9_].
pub fn is_valid_username(username: &str) -> bool {
    let len = username.len();
    if !(3..=20).contains(&len) {
        return false;
    }
    username
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '_')
}

// ---------------------------------------------------------------------------
// Profile update
// ---------------------------------------------------------------------------

/// Update user profile fields. Returns the updated user row.
pub async fn update_profile(
    pool: &PgPool,
    user_id: Uuid,
    display_name: Option<&str>,
    username: Option<&str>,
    bio: Option<&str>,
    is_profile_public: Option<bool>,
    ai_personalization_enabled: Option<bool>,
) -> Result<UserRow, AppError> {
    // Validate display_name if provided
    if let Some(dn) = display_name {
        if !is_valid_display_name(dn) {
            return Err(AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "INVALID_DISPLAY_NAME".to_string(),
                message: "Display name must contain only letters, numbers, and spaces"
                    .to_string(),
                details: json!({}),
            });
        }
    }

    // Validate username if provided
    if let Some(uname) = username {
        if !is_valid_username(uname) {
            return Err(AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "INVALID_USERNAME".to_string(),
                message:
                    "Username must be 3-20 characters and contain only letters, numbers, and underscores"
                        .to_string(),
                details: json!({}),
            });
        }

        // Check uniqueness
        let existing: Option<(Uuid,)> = sqlx::query_as(
            "SELECT id FROM users WHERE username = $1 AND id != $2",
        )
        .bind(uname)
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        if existing.is_some() {
            return Err(AppError::Domain {
                status: StatusCode::CONFLICT,
                code: "USERNAME_TAKEN".to_string(),
                message: "Username already taken".to_string(),
                details: json!({}),
            });
        }
    }

    // Build dynamic UPDATE query
    let mut set_clauses: Vec<String> = Vec::new();
    let mut param_idx: usize = 2; // $1 is user_id

    if display_name.is_some() {
        param_idx += 1;
        set_clauses.push(format!("display_name = ${}", param_idx));
    }
    if username.is_some() {
        param_idx += 1;
        set_clauses.push(format!("username = ${}", param_idx));
    }
    if bio.is_some() {
        param_idx += 1;
        set_clauses.push(format!("bio = ${}", param_idx));
    }
    if is_profile_public.is_some() {
        param_idx += 1;
        set_clauses.push(format!("is_profile_public = ${}", param_idx));
    }
    if ai_personalization_enabled.is_some() {
        param_idx += 1;
        set_clauses.push(format!("ai_personalization_enabled = ${}", param_idx));
    }

    if set_clauses.is_empty() {
        // Nothing to update, just fetch current state
        let row = sqlx::query_as::<_, UserRow>(
            "SELECT id, email, display_name, avatar_url, username, bio, role, \
             total_xp, starting_urn_id, is_profile_public, ai_personalization_enabled, \
             password_hash, onboarding_goal, onboarding_completed, onboarding_completed_at, \
             created_at FROM users WHERE id = $1",
        )
        .bind(user_id)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?
        .ok_or(AppError::Unauthorized)?;
        return Ok(row);
    }

    set_clauses.push("updated_at = NOW()".to_string());

    // We need to use a raw query approach since we have dynamic params.
    // Build the full SQL and use a manual approach with sqlx::query.
    let sql = format!(
        "UPDATE users SET {} WHERE id = $1 RETURNING \
         id, email, display_name, avatar_url, username, bio, role, \
         total_xp, starting_urn_id, is_profile_public, ai_personalization_enabled, \
         password_hash, onboarding_goal, onboarding_completed, onboarding_completed_at, \
         created_at",
        set_clauses.join(", ")
    );

    // Since sqlx doesn't support truly dynamic bind params easily with query_as,
    // we'll use a simpler approach: always update all fields (using COALESCE pattern).
    // This is cleaner and avoids the dynamic SQL complexity.

    let row = sqlx::query_as::<_, UserRow>(
        "UPDATE users SET \
         display_name = COALESCE($2, display_name), \
         username = COALESCE($3, username), \
         bio = COALESCE($4, bio), \
         is_profile_public = COALESCE($5, is_profile_public), \
         ai_personalization_enabled = COALESCE($6, ai_personalization_enabled), \
         updated_at = NOW() \
         WHERE id = $1 \
         RETURNING id, email, display_name, avatar_url, username, bio, role, \
         total_xp, starting_urn_id, is_profile_public, ai_personalization_enabled, \
         password_hash, onboarding_goal, onboarding_completed, onboarding_completed_at, \
         created_at",
    )
    .bind(user_id)
    .bind(display_name)
    .bind(username)
    .bind(bio)
    .bind(is_profile_public)
    .bind(ai_personalization_enabled)
    .fetch_optional(pool)
    .await
    .map_err(|e| {
        // Handle unique constraint violation (race condition on username)
        if let Some(db_err) = e.as_database_error() {
            if db_err.code().as_deref() == Some("23505") {
                return AppError::Domain {
                    status: StatusCode::CONFLICT,
                    code: "USERNAME_TAKEN".to_string(),
                    message: "Username already taken".to_string(),
                    details: json!({}),
                };
            }
        }
        AppError::Internal(e.into())
    })?
    .ok_or(AppError::Unauthorized)?;

    // Drop the unused `sql` binding (we used COALESCE approach instead)
    let _ = sql;

    Ok(row)
}

// ---------------------------------------------------------------------------
// Change password
// ---------------------------------------------------------------------------

/// Change user password: verify old, hash new, update DB.
pub async fn change_password(
    pool: &PgPool,
    user_id: Uuid,
    current_password: &str,
    new_password: &str,
) -> Result<(), AppError> {
    // Fetch current hash
    let row: Option<(String,)> =
        sqlx::query_as("SELECT password_hash FROM users WHERE id = $1")
            .bind(user_id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    let (hash,) = row.ok_or(AppError::Unauthorized)?;

    // Verify current password
    let valid = auth::verify_password(current_password, &hash).map_err(|_| {
        AppError::Http {
            status: StatusCode::BAD_REQUEST,
            message: "Current password is incorrect".to_string(),
        }
    })?;

    if !valid {
        return Err(AppError::Http {
            status: StatusCode::BAD_REQUEST,
            message: "Current password is incorrect".to_string(),
        });
    }

    // Hash new password
    let new_hash = auth::hash_password(new_password).map_err(|e| {
        if matches!(e, auth::AuthError::PasswordTooLong) {
            AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "PASSWORD_TOO_LONG".to_string(),
                message: "Password too long".to_string(),
                details: json!({}),
            }
        } else {
            AppError::Internal(anyhow::anyhow!("{}", e))
        }
    })?;

    // Update
    sqlx::query("UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2")
        .bind(&new_hash)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(())
}

// ---------------------------------------------------------------------------
// Starting path
// ---------------------------------------------------------------------------

/// URN row for starting path lookup.
#[derive(Debug, sqlx::FromRow)]
struct UrnRow {
    pub id: Uuid,
    pub slug: String,
}

/// Set user's starting path (by urn_id or urn_slug).
pub async fn set_starting_path(
    pool: &PgPool,
    user_id: Uuid,
    urn_id: Option<Uuid>,
    urn_slug: Option<&str>,
) -> Result<(Uuid, String), AppError> {
    // Resolve URN
    let urn = if let Some(id) = urn_id {
        sqlx::query_as::<_, UrnRow>("SELECT id, slug FROM urns WHERE id = $1")
            .bind(id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
    } else if let Some(slug) = urn_slug {
        sqlx::query_as::<_, UrnRow>("SELECT id, slug FROM urns WHERE slug = $1")
            .bind(slug)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
    } else {
        None
    };

    // If urn_id lookup failed, try slug as fallback (matching Python behavior)
    let urn = match urn {
        Some(u) => u,
        None => {
            if let Some(slug) = urn_slug {
                sqlx::query_as::<_, UrnRow>("SELECT id, slug FROM urns WHERE slug = $1")
                    .bind(slug)
                    .fetch_optional(pool)
                    .await
                    .map_err(|e| AppError::Internal(e.into()))?
                    .ok_or_else(|| AppError::Http {
                        status: StatusCode::NOT_FOUND,
                        message: "Urn not found".to_string(),
                    })?
            } else {
                return Err(AppError::Http {
                    status: StatusCode::NOT_FOUND,
                    message: "Urn not found".to_string(),
                });
            }
        }
    };

    // Update user
    sqlx::query("UPDATE users SET starting_urn_id = $1, updated_at = NOW() WHERE id = $2")
        .bind(urn.id)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok((urn.id, urn.slug))
}

// ---------------------------------------------------------------------------
// Onboarding
// ---------------------------------------------------------------------------

/// Valid onboarding goals (matches Python's valid_goals list).
const VALID_GOALS: &[&str] = &[
    "learn_culture",
    "pass_exam",
    "curiosity",
    "professional",
    "hobby",
];

/// Save onboarding goal.
pub async fn set_onboarding_goal(
    pool: &PgPool,
    user_id: Uuid,
    goal: &str,
) -> Result<String, AppError> {
    if !VALID_GOALS.contains(&goal) {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_GOAL".to_string(),
            message: format!(
                "Invalid goal. Must be one of: {}",
                VALID_GOALS.join(", ")
            ),
            details: json!({}),
        });
    }

    sqlx::query(
        "UPDATE users SET onboarding_goal = $1, updated_at = NOW() WHERE id = $2",
    )
    .bind(goal)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(goal.to_string())
}

/// Get onboarding status.
pub async fn get_onboarding(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<(bool, Option<String>, Option<DateTime<Utc>>), AppError> {
    let row: Option<(bool, Option<String>, Option<DateTime<Utc>>)> = sqlx::query_as(
        "SELECT onboarding_completed, onboarding_goal, onboarding_completed_at \
         FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (completed, goal, completed_at) = row.ok_or(AppError::Unauthorized)?;
    Ok((completed, goal, completed_at))
}

/// Complete onboarding.
pub async fn complete_onboarding(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<(bool, Option<DateTime<Utc>>), AppError> {
    // Check if already completed
    let row: Option<(bool, Option<DateTime<Utc>>)> = sqlx::query_as(
        "SELECT onboarding_completed, onboarding_completed_at FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let (completed, completed_at) = row.ok_or(AppError::Unauthorized)?;

    if completed {
        return Ok((true, completed_at));
    }

    let now = Utc::now();
    sqlx::query(
        "UPDATE users SET onboarding_completed = true, onboarding_completed_at = $1, \
         updated_at = NOW() WHERE id = $2",
    )
    .bind(now)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok((true, Some(now)))
}

// ---------------------------------------------------------------------------
// Public profile
// ---------------------------------------------------------------------------

/// Get public profile by user ID.
pub async fn get_public_profile(
    pool: &PgPool,
    user_id: Uuid,
    requester_id: Uuid,
) -> Result<UserPublicRow, AppError> {
    let row = sqlx::query_as::<_, UserPublicRow>(
        "SELECT id, email, display_name, avatar_url, username, bio, role, \
         total_xp, is_profile_public, created_at \
         FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "User not found".to_string(),
    })?;

    // Check privacy (owner can always see their own profile)
    if !row.is_profile_public && row.id != requester_id {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Profile is private".to_string(),
        });
    }

    Ok(row)
}

/// Resolve a user by UUID or username (for GET /u/{username_or_id}).
pub async fn resolve_user_by_id_or_username(
    pool: &PgPool,
    identifier: &str,
    requester_id: Uuid,
) -> Result<UserPublicRow, AppError> {
    // Try UUID first
    if let Ok(uuid) = identifier.parse::<Uuid>() {
        return get_public_profile(pool, uuid, requester_id).await;
    }

    // Fall back to username lookup
    let row = sqlx::query_as::<_, UserPublicRow>(
        "SELECT id, email, display_name, avatar_url, username, bio, role, \
         total_xp, is_profile_public, created_at \
         FROM users WHERE username = $1",
    )
    .bind(identifier)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "User not found".to_string(),
    })?;

    if !row.is_profile_public && row.id != requester_id {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Profile is private".to_string(),
        });
    }

    Ok(row)
}
