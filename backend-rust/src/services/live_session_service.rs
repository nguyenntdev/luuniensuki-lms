//! Live session lifecycle service (Task 11).
//!
//! Ports the Python `create_live_session`, `end_live_session`,
//! `get_live_session`, `list_live_sessions_for_classroom`, and
//! `update_live_session_settings` from `backend/services/live_sessions.py`, and
//! owns the scheduled → live → ended state machine plus Janus VideoRoom
//! provisioning/teardown.
//!
//! Uses sqlx runtime queries (`query`, `query_as`) — NOT the compile-time
//! `query!` macro — matching the other service modules in this crate. sqlx
//! errors map to `AppError::Internal`.
//!
//! `live_sessions` columns (struct order — used verbatim in SELECT/RETURNING so
//! `query_as::<_, LiveSession>` lines up):
//!   id, classroom_id, created_by_id, room_name, title, status,
//!   starts_at, ended_at, idempotency_key, session_metadata,
//!   created_at, updated_at
//!
//! Validates: Requirements 2.1, 2.2, 2.4, 7.1, 7.2, 7.3, 9.1, 9.2, 9.3, 11.3

use std::sync::Arc;

use axum::http::StatusCode;
use chrono::Utc;
use serde_json::{json, Map, Value};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::{CreateSessionRequest, LiveSession, UpdateSettingsRequest};
use crate::services::ai_hook_client::{AiHookClient, AiSessionPayload};
use crate::services::janus_admin::{JanusAdminApi, RoomOpts};
use crate::services::{live_auth, live_event_service, live_participant_service};

/// Full `live_sessions` column list (struct order) reused by SELECT/RETURNING.
const SESSION_COLUMNS: &str = "\
    id, classroom_id, created_by_id, room_name, title, status, \
    starts_at, ended_at, idempotency_key, session_metadata, \
    created_at, updated_at";

/// VideoRoom provisioning knobs (Req 9.1).
const DEFAULT_PUBLISHERS: i64 = 12;
const DEFAULT_BITRATE: i64 = 256_000;

/// `session_metadata` key under which the active media backend is recorded so
/// in-flight sessions stay on their original backend across a flag flip (Req 11.3).
const META_MEDIA_BACKEND: &str = "media_backend";

// ---------------------------------------------------------------------------
// Pure helpers (unit-testable without a DB)
// ---------------------------------------------------------------------------

/// Whether `end_session` should short-circuit as a no-op for the given status.
/// The state machine only moves forward; a session already `ended` is terminal
/// and ending it again is a harmless no-op (Req 7.1).
pub fn should_skip_end(status: &str) -> bool {
    status == "ended"
}

/// Generate a fresh, collision-resistant room name (`lms-live-<uuid32>`).
pub fn generate_room_name() -> String {
    format!("lms-live-{}", Uuid::new_v4().simple())
}

/// Derive a positive numeric Janus VideoRoom id from a fresh UUID. Janus
/// VideoRoom ids are signed 64-bit; we keep them strictly positive.
pub fn generate_janus_room_id() -> i64 {
    // Take the low 63 bits of a v4 UUID and force non-zero.
    let raw = (Uuid::new_v4().as_u128() as u64) & 0x7fff_ffff_ffff_ffff;
    (raw as i64).max(1)
}

/// Merge the active media backend into a caller-supplied `session_metadata`
/// object, preserving every existing key (lock_room, ai_enabled, grade_level,
/// ai_cost_ceiling_usd, ...). Non-object inputs are treated as an empty object.
pub fn metadata_with_backend(base: Option<&Value>, media_backend: &str) -> Value {
    let mut map: Map<String, Value> = base
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();
    map.insert(META_MEDIA_BACKEND.to_string(), json!(media_backend));
    Value::Object(map)
}

/// Apply an `UpdateSettingsRequest` patch onto an existing `session_metadata`
/// object, returning the merged object. Only `Some` fields are written; absent
/// fields are left untouched (mirrors the Python partial-update semantics).
pub fn merge_settings_metadata(existing: &Value, patch: &UpdateSettingsRequest) -> Value {
    let mut map: Map<String, Value> = existing.as_object().cloned().unwrap_or_default();
    if let Some(v) = patch.lock_room {
        map.insert("lock_room".to_string(), json!(v));
    }
    if let Some(v) = patch.ai_enabled {
        map.insert("ai_enabled".to_string(), json!(v));
    }
    if let Some(ref v) = patch.grade_level {
        map.insert("grade_level".to_string(), json!(v));
    }
    if let Some(v) = patch.ai_cost_ceiling_usd {
        map.insert("ai_cost_ceiling_usd".to_string(), json!(v));
    }
    Value::Object(map)
}

/// Clamp a list limit into `1..=200`.
fn clamp_limit(n: i64) -> i64 {
    n.clamp(1, 200)
}

/// Read a string-valued metadata key.
fn meta_str(metadata: &Value, key: &str) -> Option<String> {
    metadata.get(key).and_then(Value::as_str).map(str::to_string)
}

/// Read an f64-valued metadata key.
fn meta_f64(metadata: &Value, key: &str) -> Option<f64> {
    metadata.get(key).and_then(Value::as_f64)
}

// ---------------------------------------------------------------------------
// Session lifecycle
// ---------------------------------------------------------------------------

/// Create a live session idempotently and provision its Janus VideoRoom.
///
/// When `req.idempotency_key` matches an existing session for the same
/// classroom, that session is returned unchanged — no new row, room, or event
/// is created (Req 2.1). Otherwise a new session row is inserted, exactly one
/// VideoRoom is provisioned, the `live_janus_rooms` binding is persisted, and a
/// single `session_created` event is recorded (Req 2.2). If Janus provisioning
/// fails, the session insert is rolled back and a 503 is returned (Req 2.4).
///
/// The active `media_backend` is recorded in `session_metadata` so in-flight
/// sessions stay on their original backend across a flag flip (Req 11.3).
#[allow(clippy::too_many_arguments)]
pub async fn create_session<J: JanusAdminApi>(
    pool: &PgPool,
    janus: &J,
    ai: Option<&Arc<AiHookClient>>,
    actor_id: Uuid,
    req: &CreateSessionRequest,
    media_backend: &str,
    janus_public_ws_url: &str,
) -> Result<LiveSession, AppError> {
    // --- Idempotent fast path -------------------------------------------
    if let Some(ref key) = req.idempotency_key {
        let existing = sqlx::query_as::<_, LiveSession>(&format!(
            "SELECT {SESSION_COLUMNS} FROM live_sessions \
             WHERE classroom_id = $1 AND idempotency_key = $2"
        ))
        .bind(req.classroom_id)
        .bind(key)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        if let Some(session) = existing {
            return Ok(session);
        }
    }

    // --- Provision identifiers ------------------------------------------
    let room_name = generate_room_name();
    let janus_room_id = generate_janus_room_id();
    let room_secret = Uuid::new_v4().simple().to_string();
    let starts_at = req.starts_at.unwrap_or_else(Utc::now);
    let metadata = metadata_with_backend(req.session_metadata.as_ref(), media_backend);

    // Insert the session row first (status `scheduled`). If Janus provisioning
    // fails we delete this row so no orphan session remains (Req 2.4).
    let session = sqlx::query_as::<_, LiveSession>(&format!(
        "INSERT INTO live_sessions \
           (id, classroom_id, created_by_id, room_name, title, status, \
            starts_at, ended_at, idempotency_key, session_metadata, \
            created_at, updated_at) \
         VALUES ($1, $2, $3, $4, $5, 'scheduled', $6, NULL, $7, $8, now(), now()) \
         RETURNING {SESSION_COLUMNS}"
    ))
    .bind(Uuid::new_v4())
    .bind(req.classroom_id)
    .bind(actor_id)
    .bind(&room_name)
    .bind(&req.title)
    .bind(starts_at)
    .bind(&req.idempotency_key)
    .bind(&metadata)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Provision exactly one Janus VideoRoom (Req 9.1).
    let opts = RoomOpts {
        publishers: DEFAULT_PUBLISHERS,
        bitrate: DEFAULT_BITRATE,
        audiolevel_event: true,
    };
    if let Err(e) = janus.create_room(janus_room_id, &opts, &room_secret).await {
        // Roll back the session insert; ending must not leave an orphan (Req 2.4).
        let _ = sqlx::query("DELETE FROM live_sessions WHERE id = $1")
            .bind(session.id)
            .execute(pool)
            .await;
        tracing::error!(error = %e, "janus room provisioning failed; rolled back session");
        return Err(AppError::Http {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: "Failed to provision media room".to_string(),
        });
    }

    // Persist the session → VideoRoom binding. The room secret is stored as a
    // reference value (here, the secret itself) used server-side for moderation.
    sqlx::query(
        "INSERT INTO live_janus_rooms \
           (id, live_session_id, janus_room_id, room_secret_ref, pin_ref, media_state, created_at, updated_at) \
         VALUES ($1, $2, $3, $4, NULL, 'provisioned', now(), now())",
    )
    .bind(Uuid::new_v4())
    .bind(session.id)
    .bind(janus_room_id)
    .bind(&room_secret)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Record exactly one session_created event (Req 2.2, 6.1).
    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(session.id, "session_created", "system")
            .with_user_id(actor_id)
            .with_payload(json!({
                "room_name": room_name,
                "janus_room_id": janus_room_id,
                "media_backend": media_backend,
            })),
    )
    .await?;

    // Fire the AI lifecycle hook when AI is enabled (Req 10.1). Fire-and-forget.
    if live_auth::is_ai_enabled(&session) {
        if let Some(ai) = ai {
            let payload = AiSessionPayload {
                live_session_id: session.id,
                classroom_id: session.classroom_id,
                janus_ws_url: janus_public_ws_url.to_string(),
                janus_room_id,
                ai_teacher_identity: live_participant_service::ai_teacher_identity(session.id),
                grade_level: meta_str(&session.session_metadata, "grade_level"),
                ai_cost_ceiling_usd: meta_f64(&session.session_metadata, "ai_cost_ceiling_usd"),
            };
            ai.clone().spawn_session_created(payload);
        }
    }

    Ok(session)
}

/// List sessions for a classroom, most recent first. `limit` is clamped 1..=200.
pub async fn list_sessions(
    pool: &PgPool,
    classroom_id: Uuid,
    limit: i64,
) -> Result<Vec<LiveSession>, AppError> {
    let bounded = clamp_limit(limit);
    let sessions = sqlx::query_as::<_, LiveSession>(&format!(
        "SELECT {SESSION_COLUMNS} FROM live_sessions \
         WHERE classroom_id = $1 ORDER BY created_at DESC LIMIT $2"
    ))
    .bind(classroom_id)
    .bind(bounded)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(sessions)
}

/// Fetch a single session by id.
pub async fn get_session(pool: &PgPool, id: Uuid) -> Result<Option<LiveSession>, AppError> {
    let session = sqlx::query_as::<_, LiveSession>(&format!(
        "SELECT {SESSION_COLUMNS} FROM live_sessions WHERE id = $1"
    ))
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(session)
}

/// Update session settings (`session_metadata` fields) and record a
/// `settings_updated` event.
pub async fn update_settings(
    pool: &PgPool,
    session: &LiveSession,
    patch: &UpdateSettingsRequest,
    actor_id: Uuid,
) -> Result<LiveSession, AppError> {
    let merged = merge_settings_metadata(&session.session_metadata, patch);

    let updated = sqlx::query_as::<_, LiveSession>(&format!(
        "UPDATE live_sessions SET session_metadata = $2, updated_at = now() \
         WHERE id = $1 RETURNING {SESSION_COLUMNS}"
    ))
    .bind(session.id)
    .bind(&merged)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(session.id, "settings_updated", "user")
            .with_user_id(actor_id)
            .with_payload(json!({
                "lock_room": patch.lock_room,
                "ai_enabled": patch.ai_enabled,
                "grade_level": patch.grade_level,
                "ai_cost_ceiling_usd": patch.ai_cost_ceiling_usd,
            })),
    )
    .await?;

    Ok(updated)
}

/// End a session and tear down its Janus VideoRoom.
///
/// Idempotent (Req 7.1): a second call on an already-ended session is a no-op
/// that returns the ended session without re-setting `ended_at` or recording a
/// duplicate event. Ending never blocks on a media-plane failure — if the room
/// destroy fails the session is still marked ended and a `room_close_failed`
/// event is recorded (Req 9.3).
pub async fn end_session<J: JanusAdminApi>(
    pool: &PgPool,
    janus: &J,
    ai: Option<&Arc<AiHookClient>>,
    session: &LiveSession,
    ended_by: Option<Uuid>,
) -> Result<LiveSession, AppError> {
    // Idempotent no-op for an already-ended session.
    if should_skip_end(&session.status) {
        return get_session(pool, session.id)
            .await?
            .ok_or_else(|| AppError::Http {
                status: StatusCode::NOT_FOUND,
                message: "Live session not found".to_string(),
            });
    }

    // Advance to ended, setting ended_at exactly once (guarded by IS NULL).
    let ended = sqlx::query_as::<_, LiveSession>(&format!(
        "UPDATE live_sessions \
         SET status = 'ended', \
             ended_at = COALESCE(ended_at, now()), \
             updated_at = now() \
         WHERE id = $1 RETURNING {SESSION_COLUMNS}"
    ))
    .bind(session.id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Record exactly one session_ended event (Req 7.2, 6.1).
    let mut ev = live_event_service::EventInsert::new(session.id, "session_ended", "system");
    if let Some(uid) = ended_by {
        ev = ev.with_user_id(uid);
    }
    let _ = live_event_service::record(pool, ev).await?;

    // Look up the Janus room binding and destroy the room. A destroy failure is
    // recorded but never blocks ending (Req 9.3).
    let room: Option<(i64, String)> = sqlx::query_as(
        "SELECT janus_room_id, room_secret_ref FROM live_janus_rooms WHERE live_session_id = $1",
    )
    .bind(session.id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some((janus_room_id, room_secret)) = room {
        match janus.destroy_room(janus_room_id, &room_secret).await {
            Ok(()) => {
                let _ = sqlx::query(
                    "UPDATE live_janus_rooms SET media_state = 'destroyed', updated_at = now() \
                     WHERE live_session_id = $1",
                )
                .bind(session.id)
                .execute(pool)
                .await;
            }
            Err(e) => {
                let _ = live_event_service::record(
                    pool,
                    live_event_service::EventInsert::new(session.id, "room_close_failed", "system")
                        .with_payload(json!({ "error": e.to_string() })),
                )
                .await;
            }
        }
    }

    // Notify the AI worker (fire-and-forget).
    if let Some(ai) = ai {
        ai.clone().spawn_session_ended(session.id);
    }

    Ok(ended)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_skip_end_only_for_ended() {
        assert!(should_skip_end("ended"));
        assert!(!should_skip_end("scheduled"));
        assert!(!should_skip_end("live"));
    }

    #[test]
    fn room_name_has_prefix_and_is_unique() {
        let a = generate_room_name();
        let b = generate_room_name();
        assert!(a.starts_with("lms-live-"));
        assert_ne!(a, b);
    }

    #[test]
    fn janus_room_id_is_positive() {
        for _ in 0..1000 {
            assert!(generate_janus_room_id() > 0);
        }
    }

    #[test]
    fn metadata_with_backend_preserves_existing_keys() {
        let base = json!({ "lock_room": true, "ai_enabled": false, "grade_level": "g5" });
        let merged = metadata_with_backend(Some(&base), "janus");
        assert_eq!(merged["lock_room"], json!(true));
        assert_eq!(merged["ai_enabled"], json!(false));
        assert_eq!(merged["grade_level"], json!("g5"));
        assert_eq!(merged["media_backend"], json!("janus"));
    }

    #[test]
    fn metadata_with_backend_handles_none_and_non_object() {
        let from_none = metadata_with_backend(None, "livekit");
        assert_eq!(from_none["media_backend"], json!("livekit"));
        let from_scalar = metadata_with_backend(Some(&json!("oops")), "janus");
        assert_eq!(from_scalar["media_backend"], json!("janus"));
    }

    #[test]
    fn merge_settings_only_writes_some_fields() {
        let existing = json!({ "lock_room": false, "ai_enabled": true, "grade_level": "g3" });
        let patch = UpdateSettingsRequest {
            lock_room: Some(true),
            ai_enabled: None,
            grade_level: None,
            ai_cost_ceiling_usd: Some(2.5),
        };
        let merged = merge_settings_metadata(&existing, &patch);
        assert_eq!(merged["lock_room"], json!(true)); // overwritten
        assert_eq!(merged["ai_enabled"], json!(true)); // preserved
        assert_eq!(merged["grade_level"], json!("g3")); // preserved
        assert_eq!(merged["ai_cost_ceiling_usd"], json!(2.5)); // added
    }

    #[test]
    fn clamp_limit_bounds() {
        assert_eq!(clamp_limit(0), 1);
        assert_eq!(clamp_limit(10), 10);
        assert_eq!(clamp_limit(9999), 200);
    }
}
