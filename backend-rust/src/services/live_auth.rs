//! Live authorization predicates (Task 5).
//!
//! Native Rust port of the Python authorization layer in
//! `backend/services/live_sessions.py` — exact behavior parity with
//! `can_access_classroom`, `can_manage_classroom`,
//! `can_user_moderate_live_session`, `_can_user_bypass_room_lock`,
//! `ensure_user_can_access_live_session`, `ensure_user_can_join_live_session`,
//! plus the `session_metadata` accessors `is_room_locked` / `is_ai_enabled`.
//!
//! The caller passes the JWT `role` claim as `&str` (matching the
//! `route_helpers` pattern where the access token carries the role), so these
//! predicates never need to re-fetch `users.role`.
//!
//! Uses sqlx runtime queries (`query_scalar`) — NOT the compile-time `query!`
//! macro — matching the other service modules in this crate. sqlx errors map to
//! `AppError::Internal`.
//!
//! Validates: Requirements 1.1–1.6, 4.1, 4.3

use axum::http::StatusCode;
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::LiveSession;

/// `session_metadata` JSON keys (parity with the Python constants).
const META_LOCK_ROOM: &str = "lock_room";
const META_AI_ENABLED: &str = "ai_enabled";

/// Live participant roles that may moderate / bypass a room lock.
const ROLE_HOST: &str = "host";
const ROLE_COHOST: &str = "cohost";

// ---------------------------------------------------------------------------
// Pure role predicates (mirror ADMIN_ROLES / STAFF_ROLES)
// ---------------------------------------------------------------------------

/// `true` when the role is administrative — `ADMIN_ROLES = {admin, super_admin}`.
pub fn is_admin(role: &str) -> bool {
    matches!(role, "admin" | "super_admin")
}

/// `true` when the role is staff — `STAFF_ROLES = {teacher, admin, super_admin}`
/// (the admin set plus `teacher`).
pub fn is_staff(role: &str) -> bool {
    is_admin(role) || role == "teacher"
}

// ---------------------------------------------------------------------------
// session_metadata accessors (mirror is_room_locked / is_ai_enabled)
// ---------------------------------------------------------------------------

/// Whether the room is locked. Reads `session_metadata.lock_room`, defaulting to
/// `false` when the key is missing or not a boolean (parity with the Python
/// `metadata.get(LOCK_ROOM_KEY, False)`).
pub fn is_room_locked(session: &LiveSession) -> bool {
    session
        .session_metadata
        .get(META_LOCK_ROOM)
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
}

/// Whether the AI teacher is enabled. Reads `session_metadata.ai_enabled`,
/// defaulting to `true` when the key is missing or not a boolean (parity with
/// the Python `metadata.get(AI_ENABLED_KEY, True)`).
pub fn is_ai_enabled(session: &LiveSession) -> bool {
    session
        .session_metadata
        .get(META_AI_ENABLED)
        .and_then(|v| v.as_bool())
        .unwrap_or(true)
}

// ---------------------------------------------------------------------------
// Classroom-scoped predicates
// ---------------------------------------------------------------------------

/// Manage permission for a classroom (port of `can_manage_classroom`).
///
/// Granted when the user is administrative OR is a teacher who owns the
/// classroom (`classrooms.owner_id = user_id`).
pub async fn can_manage_classroom(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    classroom_id: Uuid,
) -> Result<bool, AppError> {
    if is_admin(role) {
        return Ok(true);
    }
    if role != "teacher" {
        return Ok(false);
    }

    let owns: bool = sqlx::query_scalar(
        "SELECT EXISTS(SELECT 1 FROM classrooms WHERE id = $1 AND owner_id = $2)",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(owns)
}

/// Access permission for a classroom (port of `can_access_classroom`).
///
/// Granted when the user can manage the classroom OR is a member of it
/// (`classroom_members`).
pub async fn can_access_classroom(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    classroom_id: Uuid,
) -> Result<bool, AppError> {
    if can_manage_classroom(pool, user_id, role, classroom_id).await? {
        return Ok(true);
    }

    let is_member: bool = sqlx::query_scalar(
        "SELECT EXISTS(SELECT 1 FROM classroom_members WHERE classroom_id = $1 AND user_id = $2)",
    )
    .bind(classroom_id)
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(is_member)
}

// ---------------------------------------------------------------------------
// Session-scoped predicates
// ---------------------------------------------------------------------------

/// Moderation permission for a live session (port of
/// `can_user_moderate_live_session`).
///
/// Granted when the user can manage the session's classroom OR is an *active*
/// participant (`left_at IS NULL`) whose role is `host` (or `cohost` when
/// `allow_cohost` is true). `allow_cohost` mirrors the Python keyword argument
/// of the same name (default `true` at the Python call sites).
pub async fn can_moderate(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    session: &LiveSession,
    allow_cohost: bool,
) -> Result<bool, AppError> {
    if can_manage_classroom(pool, user_id, role, session.classroom_id).await? {
        return Ok(true);
    }

    let active_role: Option<String> = sqlx::query_scalar(
        r#"
        SELECT role
        FROM live_participants
        WHERE live_session_id = $1
          AND user_id = $2
          AND left_at IS NULL
        LIMIT 1
        "#,
    )
    .bind(session.id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let allowed = match active_role.as_deref() {
        Some(ROLE_HOST) => true,
        Some(ROLE_COHOST) => allow_cohost,
        _ => false,
    };
    Ok(allowed)
}

/// Room-lock bypass permission (port of `_can_user_bypass_room_lock`).
///
/// Granted when the user can moderate (with cohost allowed) OR has any host /
/// cohost role *history* in the session (an existing `live_participants` row
/// with role `host` or `cohost`, regardless of `left_at`).
pub async fn can_bypass_room_lock(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    session: &LiveSession,
) -> Result<bool, AppError> {
    if can_moderate(pool, user_id, role, session, true).await? {
        return Ok(true);
    }

    let has_role_history: bool = sqlx::query_scalar(
        r#"
        SELECT EXISTS(
            SELECT 1
            FROM live_participants
            WHERE live_session_id = $1
              AND user_id = $2
              AND role IN ('host', 'cohost')
        )
        "#,
    )
    .bind(session.id)
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(has_role_history)
}

// ---------------------------------------------------------------------------
// Guards (port of ensure_user_can_access / ensure_user_can_join)
// ---------------------------------------------------------------------------

/// Ensure the user may access the live session, else 403 (port of
/// `ensure_user_can_access_live_session`).
pub async fn ensure_can_access(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    session: &LiveSession,
) -> Result<(), AppError> {
    if can_access_classroom(pool, user_id, role, session.classroom_id).await? {
        return Ok(());
    }
    Err(AppError::Domain {
        status: StatusCode::FORBIDDEN,
        code: "FORBIDDEN".to_string(),
        message: "Not authorized to access this live session".to_string(),
        details: json!({}),
    })
}

/// Ensure the user may join the live session (port of
/// `ensure_user_can_join_live_session`).
///
/// First enforces access; then, when the room is locked, requires the user to
/// be able to bypass the lock or rejects with `ROOM_LOCKED` (403).
pub async fn ensure_can_join(
    pool: &PgPool,
    user_id: Uuid,
    role: &str,
    session: &LiveSession,
) -> Result<(), AppError> {
    ensure_can_access(pool, user_id, role, session).await?;

    if is_room_locked(session) && !can_bypass_room_lock(pool, user_id, role, session).await? {
        return Err(AppError::Domain {
            status: StatusCode::FORBIDDEN,
            code: "ROOM_LOCKED".to_string(),
            message: "This live room is currently locked by host".to_string(),
            details: json!({}),
        });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    /// Build a minimal `LiveSession` with the given `session_metadata` for the
    /// pure-accessor tests.
    fn session_with_metadata(metadata: serde_json::Value) -> LiveSession {
        LiveSession {
            id: Uuid::new_v4(),
            classroom_id: Uuid::new_v4(),
            created_by_id: None,
            room_name: "room".to_string(),
            title: None,
            status: "live".to_string(),
            starts_at: Utc::now(),
            ended_at: None,
            idempotency_key: None,
            session_metadata: metadata,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }

    #[test]
    fn is_admin_recognizes_admin_roles() {
        assert!(is_admin("admin"));
        assert!(is_admin("super_admin"));
    }

    #[test]
    fn is_admin_rejects_non_admin_roles() {
        assert!(!is_admin("teacher"));
        assert!(!is_admin("student"));
        assert!(!is_admin("guest"));
        assert!(!is_admin(""));
    }

    #[test]
    fn is_staff_includes_admins_and_teacher() {
        assert!(is_staff("admin"));
        assert!(is_staff("super_admin"));
        assert!(is_staff("teacher"));
    }

    #[test]
    fn is_staff_rejects_learners() {
        assert!(!is_staff("student"));
        assert!(!is_staff("guest"));
        assert!(!is_staff(""));
    }

    #[test]
    fn is_room_locked_true_when_flag_set() {
        let s = session_with_metadata(json!({ "lock_room": true }));
        assert!(is_room_locked(&s));
    }

    #[test]
    fn is_room_locked_false_when_flag_unset_or_missing() {
        assert!(!is_room_locked(&session_with_metadata(json!({ "lock_room": false }))));
        assert!(!is_room_locked(&session_with_metadata(json!({}))));
        // Non-boolean / wrong type falls back to the default (false).
        assert!(!is_room_locked(&session_with_metadata(json!({ "lock_room": "yes" }))));
    }

    #[test]
    fn is_ai_enabled_defaults_to_true_when_missing() {
        assert!(is_ai_enabled(&session_with_metadata(json!({}))));
        // Non-boolean / wrong type falls back to the default (true).
        assert!(is_ai_enabled(&session_with_metadata(json!({ "ai_enabled": "no" }))));
    }

    #[test]
    fn is_ai_enabled_respects_explicit_flag() {
        assert!(is_ai_enabled(&session_with_metadata(json!({ "ai_enabled": true }))));
        assert!(!is_ai_enabled(&session_with_metadata(json!({ "ai_enabled": false }))));
    }
}
