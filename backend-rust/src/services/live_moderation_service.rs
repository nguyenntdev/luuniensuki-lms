//! Live moderation service (Task 12).
//!
//! Ports `mute_all_participants` and `remove_participant` from
//! `backend/services/live_sessions.py`, delegating media-plane actions to the
//! Janus admin client instead of LiveKit. Mute targets the audio of non-host,
//! non-AI participants (cohosts optional); remove issues a VideoRoom `kick` and
//! marks the participant left.
//!
//! Uses sqlx runtime queries (`query`, `query_as`) — NOT the compile-time
//! `query!` macro. sqlx errors map to `AppError::Internal`.
//!
//! Validates: Requirements 4.2, 4.4, 4.5

use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::ModerationActionOut;
use crate::services::janus_admin::JanusAdminApi;
use crate::services::{live_event_service, live_participant_service};

/// Roles that are never muted/removed by a bulk action.
const ROLE_HOST: &str = "host";
const ROLE_COHOST: &str = "cohost";

// ---------------------------------------------------------------------------
// Pure targeting predicate (backs Property 8 — unit-testable without a DB)
// ---------------------------------------------------------------------------

/// Whether a participant with `(role, is_ai)` is a target of `mute_all` given
/// `include_cohosts`. Hosts and AI participants are NEVER targets; cohosts are
/// targets only when `include_cohosts` is true (Req 4.2, Property 8).
pub fn is_mute_target(role: &str, is_ai: bool, include_cohosts: bool) -> bool {
    if is_ai || role == ROLE_HOST {
        return false;
    }
    if role == ROLE_COHOST {
        return include_cohosts;
    }
    true
}

// ---------------------------------------------------------------------------
// Janus room binding lookup
// ---------------------------------------------------------------------------

/// Fetch `(janus_room_id, room_secret_ref)` for a session, or 404 when the
/// session has no provisioned Janus room.
async fn room_binding(pool: &PgPool, session_id: Uuid) -> Result<(i64, String), AppError> {
    let row: Option<(i64, String)> = sqlx::query_as(
        "SELECT janus_room_id, room_secret_ref FROM live_janus_rooms WHERE live_session_id = $1",
    )
    .bind(session_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    row.ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "No media room for this session".to_string(),
    })
}

// ---------------------------------------------------------------------------
// Moderation actions
// ---------------------------------------------------------------------------

/// Mute the audio of all eligible participants in a session.
///
/// Targets active (`left_at IS NULL`) participants that are neither host nor AI
/// (cohosts only when `include_cohosts`). Each target that has a bound
/// `janus_feed_id` receives a VideoRoom `moderate {mute_audio:true}`; the result
/// is tallied into `processed` (success) and `failed` (error). `processed +
/// failed` equals the number of targeted participants that had a feed id
/// (Property 8). Records one `mute_all` event.
pub async fn mute_all<J: JanusAdminApi>(
    pool: &PgPool,
    janus: &J,
    session_id: Uuid,
    include_cohosts: bool,
    actor_id: Uuid,
) -> Result<ModerationActionOut, AppError> {
    let (janus_room_id, secret) = room_binding(pool, session_id).await?;

    // Pull active participants with their role / is_ai / feed binding.
    let rows: Vec<(String, bool, Option<i64>)> = sqlx::query_as(
        "SELECT role, is_ai, janus_feed_id FROM live_participants \
         WHERE live_session_id = $1 AND left_at IS NULL",
    )
    .bind(session_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let mut processed: i64 = 0;
    let mut failed: i64 = 0;

    for (role, is_ai, feed_id) in rows {
        if !is_mute_target(&role, is_ai, include_cohosts) {
            continue;
        }
        // Only participants actually publishing (bound feed id) can be muted.
        let Some(feed_id) = feed_id else { continue };

        match janus.moderate_mute(janus_room_id, &secret, feed_id, true).await {
            Ok(()) => processed += 1,
            Err(e) => {
                failed += 1;
                tracing::warn!(error = %e, feed_id, "mute_all: moderate failed for feed");
            }
        }
    }

    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(session_id, "mute_all", "user")
            .with_user_id(actor_id)
            .with_payload(json!({
                "processed": processed,
                "failed": failed,
                "include_cohosts": include_cohosts,
            })),
    )
    .await?;

    Ok(ModerationActionOut {
        action: "mute_all".to_string(),
        processed,
        failed,
        detail: None,
    })
}

/// Remove a participant from the session: issue a VideoRoom `kick` for their
/// feed (when bound) and mark them left (Req 4.4). Records a
/// `participant_removed` event. Returns `processed = 1` when a participant was
/// found and marked left, else `processed = 0`.
pub async fn remove_participant<J: JanusAdminApi>(
    pool: &PgPool,
    janus: &J,
    session_id: Uuid,
    participant_identity: &str,
    actor_id: Uuid,
) -> Result<ModerationActionOut, AppError> {
    let (janus_room_id, secret) = room_binding(pool, session_id).await?;

    // Find the active participant's feed id (if any).
    let feed_id: Option<i64> = sqlx::query_scalar(
        "SELECT janus_feed_id FROM live_participants \
         WHERE live_session_id = $1 AND participant_identity = $2 AND left_at IS NULL",
    )
    .bind(session_id)
    .bind(participant_identity)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .flatten();

    let mut failed: i64 = 0;
    if let Some(feed_id) = feed_id {
        if let Err(e) = janus.kick(janus_room_id, &secret, feed_id).await {
            failed += 1;
            tracing::warn!(error = %e, feed_id, "remove_participant: kick failed");
        }
    }

    // Mark the participant left regardless of the media-plane outcome.
    let marked = live_participant_service::mark_left(
        pool,
        session_id,
        None,
        Some(participant_identity),
    )
    .await?;

    let processed = if marked.is_some() { 1 } else { 0 };

    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(session_id, "participant_removed", "user")
            .with_identity(participant_identity)
            .with_user_id(actor_id)
            .with_payload(json!({ "participant_identity": participant_identity })),
    )
    .await?;

    Ok(ModerationActionOut {
        action: "remove_participant".to_string(),
        processed,
        failed,
        detail: None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn host_is_never_a_mute_target() {
        assert!(!is_mute_target("host", false, true));
        assert!(!is_mute_target("host", false, false));
    }

    #[test]
    fn ai_is_never_a_mute_target() {
        assert!(!is_mute_target("learner", true, true));
        assert!(!is_mute_target("ai_teacher", true, false));
    }

    #[test]
    fn learner_is_always_a_mute_target() {
        assert!(is_mute_target("learner", false, false));
        assert!(is_mute_target("learner", false, true));
    }

    #[test]
    fn cohost_depends_on_include_cohosts() {
        assert!(!is_mute_target("cohost", false, false));
        assert!(is_mute_target("cohost", false, true));
    }
}
