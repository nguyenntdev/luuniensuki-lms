//! Live event audit log service (Task 8).
//!
//! Append-only audit log over the reused `live_events` table plus a lookup
//! helper for resolving a session by its `room_name`. Ports the Python
//! `record_live_event`, `list_live_events`, and `find_live_session_by_room_name`
//! helpers from `backend/services/live_sessions.py`.
//!
//! Uses sqlx runtime queries (`query`, `query_as`) — NOT the compile-time
//! `query!` macro — matching the other service modules in this crate.
//!
//! `live_events` columns:
//!   id UUID, live_session_id UUID, event_type TEXT, event_source TEXT,
//!   participant_identity TEXT NULL, participant_user_id UUID NULL,
//!   payload JSONB, created_at TIMESTAMPTZ
//!
//! Validates: Requirements 6.1, 6.2, 6.3

use chrono::{DateTime, Utc};
use serde_json::Value;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::{LiveEvent, LiveSession};

/// Lower/upper bounds for the `list` limit (Req 6.3).
const MIN_LIMIT: i64 = 1;
const MAX_LIMIT: i64 = 200;

/// Data needed to append one row to the append-only `live_events` log.
///
/// `event_source` is one of e.g. `"system"`, `"user"`, `"ai_agent"` — callers
/// pass the appropriate source for the transition being recorded.
#[derive(Debug, Clone)]
pub struct EventInsert {
    pub live_session_id: Uuid,
    pub event_type: String,
    pub event_source: String,
    pub participant_identity: Option<String>,
    pub participant_user_id: Option<Uuid>,
    pub payload: Value,
}

impl EventInsert {
    /// Construct a new event with no participant binding and an empty JSON
    /// object payload. Use the builder methods to attach optional fields.
    pub fn new(
        live_session_id: Uuid,
        event_type: impl Into<String>,
        event_source: impl Into<String>,
    ) -> Self {
        Self {
            live_session_id,
            event_type: event_type.into(),
            event_source: event_source.into(),
            participant_identity: None,
            participant_user_id: None,
            payload: Value::Object(serde_json::Map::new()),
        }
    }

    /// Attach a participant identity (e.g. `user-<uuid>` or `ai-teacher-<id16>`).
    pub fn with_identity(mut self, identity: impl Into<String>) -> Self {
        self.participant_identity = Some(identity.into());
        self
    }

    /// Attach the acting user's id.
    pub fn with_user_id(mut self, user_id: Uuid) -> Self {
        self.participant_user_id = Some(user_id);
        self
    }

    /// Attach a JSON payload.
    pub fn with_payload(mut self, payload: Value) -> Self {
        self.payload = payload;
        self
    }
}

/// Clamp a requested event-list limit into the supported range `1..=200`
/// (Req 6.3). Non-positive values clamp up to `1`; oversized values clamp down
/// to `200`.
pub fn clamp_limit(n: i64) -> i64 {
    n.clamp(MIN_LIMIT, MAX_LIMIT)
}

/// Append exactly one row to the `live_events` audit log and return it.
///
/// The log is append-only: there is no update or delete path. `id` is generated
/// here via `Uuid::new_v4()` and `created_at` is set to `now()`.
///
/// Validates: Requirements 6.1, 6.2
pub async fn record(pool: &PgPool, ev: EventInsert) -> Result<LiveEvent, AppError> {
    let event = sqlx::query_as::<_, LiveEvent>(
        r#"
        INSERT INTO live_events (
            id, live_session_id, event_type, event_source,
            participant_identity, participant_user_id, payload, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, now())
        RETURNING
            id, live_session_id, event_type, event_source,
            participant_identity, participant_user_id, payload, created_at
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(ev.live_session_id)
    .bind(&ev.event_type)
    .bind(&ev.event_source)
    .bind(&ev.participant_identity)
    .bind(ev.participant_user_id)
    .bind(&ev.payload)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(event)
}

/// List events for a session ordered by `created_at` ascending.
///
/// `limit` is clamped to `1..=200`. When `since` is provided, only events
/// strictly newer than that timestamp are returned.
///
/// Validates: Requirements 6.2, 6.3
pub async fn list(
    pool: &PgPool,
    session_id: Uuid,
    limit: i64,
    since: Option<DateTime<Utc>>,
) -> Result<Vec<LiveEvent>, AppError> {
    let bounded = clamp_limit(limit);

    let events = sqlx::query_as::<_, LiveEvent>(
        r#"
        SELECT
            id, live_session_id, event_type, event_source,
            participant_identity, participant_user_id, payload, created_at
        FROM live_events
        WHERE live_session_id = $1
          AND ($2::timestamptz IS NULL OR created_at > $2)
        ORDER BY created_at ASC
        LIMIT $3
        "#,
    )
    .bind(session_id)
    .bind(since)
    .bind(bounded)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(events)
}

/// Resolve a live session by its unique `room_name`. Returns `None` when no
/// matching session exists. Used by the Janus webhook path to map a room back
/// to its session.
pub async fn find_live_session_by_room_name(
    pool: &PgPool,
    room_name: &str,
) -> Result<Option<LiveSession>, AppError> {
    let session = sqlx::query_as::<_, LiveSession>(
        r#"
        SELECT
            id, classroom_id, created_by_id, room_name, title, status,
            starts_at, ended_at, idempotency_key, session_metadata,
            created_at, updated_at
        FROM live_sessions
        WHERE room_name = $1
        "#,
    )
    .bind(room_name)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(session)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clamp_limit_raises_zero_to_one() {
        assert_eq!(clamp_limit(0), 1);
    }

    #[test]
    fn clamp_limit_caps_large_to_two_hundred() {
        assert_eq!(clamp_limit(500), 200);
    }

    #[test]
    fn clamp_limit_passes_through_in_range() {
        assert_eq!(clamp_limit(50), 50);
    }

    #[test]
    fn clamp_limit_handles_negative() {
        assert_eq!(clamp_limit(-10), 1);
    }

    #[test]
    fn clamp_limit_boundaries() {
        assert_eq!(clamp_limit(1), 1);
        assert_eq!(clamp_limit(200), 200);
    }
}
