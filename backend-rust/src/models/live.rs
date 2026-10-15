//! Live virtual-classroom DTOs (row types, request/response DTOs, and signaling
//! message enums) for the Rust + Janus migration.
//!
//! Wave 1 (Task 4). These mirror the reused tables `live_sessions`,
//! `live_participants`, `live_events` (migrations 0038/0039) plus the additive
//! changes from migration `0046_live_janus_signaling` (the two new
//! `live_participants.janus_*` columns and the new `live_janus_rooms` table).
//!
//! Conventions follow `models/session.rs`:
//! - `#[derive(Debug, sqlx::FromRow)]` for DB row types (read via `query_as`)
//! - `#[derive(Debug, Serialize)]` for response DTOs
//! - `#[derive(Debug, Deserialize)]` for request DTOs
//! - JSONB columns map to `serde_json::Value`
//!
//! Consumers (services/routes) arrive in later tasks, so some of these types are
//! not yet referenced — dead-code warnings here are expected for now.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// DB Row types (sqlx::FromRow)
// ---------------------------------------------------------------------------

/// Row of the reused `live_sessions` table.
#[derive(Debug, sqlx::FromRow)]
pub struct LiveSession {
    pub id: Uuid,
    pub classroom_id: Uuid,
    pub created_by_id: Option<Uuid>,
    pub room_name: String,
    pub title: Option<String>,
    /// One of `scheduled` | `live` | `ended`.
    pub status: String,
    pub starts_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub idempotency_key: Option<String>,
    /// JSONB: `{ lock_room, ai_enabled, grade_level, ai_cost_ceiling_usd }`.
    pub session_metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Row of the reused `live_participants` table, including the additive
/// `janus_feed_id` / `janus_handle_id` columns from migration `0046`.
#[derive(Debug, sqlx::FromRow)]
pub struct LiveParticipant {
    pub id: Uuid,
    pub live_session_id: Uuid,
    pub user_id: Option<Uuid>,
    pub participant_identity: String,
    pub display_name: Option<String>,
    /// One of `host` | `cohost` | `learner` | `ai_teacher`.
    pub role: String,
    pub is_ai: bool,
    pub joined_at: DateTime<Utc>,
    pub left_at: Option<DateTime<Utc>>,
    /// JSONB connection metadata (nullable in the DB; legacy/AI rows may be NULL).
    pub connection_metadata: Option<serde_json::Value>,
    /// VideoRoom publisher feed id (nullable; bound during publish).
    pub janus_feed_id: Option<i64>,
    /// Janus plugin handle id (nullable; bound during attach).
    pub janus_handle_id: Option<i64>,
}

/// Row of the reused `live_events` append-only audit table.
#[derive(Debug, sqlx::FromRow)]
pub struct LiveEvent {
    pub id: Uuid,
    pub live_session_id: Uuid,
    pub event_type: String,
    pub event_source: String,
    pub participant_identity: Option<String>,
    pub participant_user_id: Option<Uuid>,
    /// JSONB payload.
    pub payload: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

/// Row of the new `live_janus_rooms` table (migration `0046`). Maps a session to
/// its Janus VideoRoom; secrets are stored as references, never plaintext.
#[derive(Debug, sqlx::FromRow)]
pub struct LiveJanusRoom {
    pub id: Uuid,
    pub live_session_id: Uuid,
    pub janus_room_id: i64,
    pub room_secret_ref: String,
    pub pin_ref: Option<String>,
    /// One of `provisioned` | `active` | `destroyed`.
    pub media_state: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Response DTOs
// ---------------------------------------------------------------------------

/// Public view of a live session plus its current participant count.
#[derive(Debug, Serialize)]
pub struct LiveSessionOut {
    pub id: Uuid,
    pub classroom_id: Uuid,
    pub created_by_id: Option<Uuid>,
    pub room_name: String,
    pub title: Option<String>,
    pub status: String,
    pub starts_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub idempotency_key: Option<String>,
    pub session_metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub participant_count: i64,
}

/// Public view of a single participant.
#[derive(Debug, Serialize)]
pub struct LiveParticipantOut {
    pub id: Uuid,
    pub participant_identity: String,
    pub user_id: Option<Uuid>,
    pub display_name: Option<String>,
    pub role: String,
    pub is_ai: bool,
    pub joined_at: DateTime<Utc>,
    pub left_at: Option<DateTime<Utc>>,
}

/// Public view of an audit event.
#[derive(Debug, Serialize)]
pub struct LiveEventOut {
    pub id: Uuid,
    pub event_type: String,
    pub event_source: String,
    pub participant_identity: Option<String>,
    pub participant_user_id: Option<Uuid>,
    pub payload: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

/// A single ICE server entry handed to the browser.
#[derive(Debug, Serialize)]
pub struct IceServer {
    pub urls: Vec<String>,
    pub username: Option<String>,
    pub credential: Option<String>,
}

/// Join credential payload (scoped HS256 JWT + connection params). Never carries
/// the Janus room/admin secret.
#[derive(Debug, Serialize)]
pub struct LiveCredentialOut {
    /// Public Janus WS URL for the browser.
    pub janus_ws_url: String,
    pub janus_room_id: i64,
    pub identity: String,
    /// Scoped HS256 JWT (NOT the room/admin secret).
    pub credential: String,
    pub expires_at: DateTime<Utc>,
    pub ice_servers: Vec<IceServer>,
}

/// Response for POST `/api/v1/live-sessions/{id}/join`.
#[derive(Debug, Serialize)]
pub struct LiveSessionJoinOut {
    pub session: LiveSessionOut,
    pub participant: LiveParticipantOut,
    pub janus: LiveCredentialOut,
}

/// Result of a moderation action (mute-all, remove-participant, ...).
#[derive(Debug, Serialize)]
pub struct ModerationActionOut {
    pub action: String,
    pub processed: i64,
    pub failed: i64,
    pub detail: Option<String>,
}

// ---------------------------------------------------------------------------
// Request DTOs
// ---------------------------------------------------------------------------

/// Request body for POST `/api/v1/live-sessions`.
#[derive(Debug, Deserialize)]
pub struct CreateSessionRequest {
    pub classroom_id: Uuid,
    pub title: Option<String>,
    pub starts_at: Option<DateTime<Utc>>,
    pub idempotency_key: Option<String>,
    pub session_metadata: Option<serde_json::Value>,
}

/// Query for GET `/api/v1/live-sessions?classroom_id=&limit=`.
#[derive(Debug, Deserialize)]
pub struct ListSessionsQuery {
    pub classroom_id: Uuid,
    pub limit: Option<i64>,
}

/// Query for GET `/api/v1/live-sessions/{id}/events?limit=&since=`.
#[derive(Debug, Deserialize)]
pub struct EventsQuery {
    pub limit: Option<i64>,
    pub since: Option<DateTime<Utc>>,
}

/// Request body for POST `/api/v1/live-sessions/{id}/events`.
#[derive(Debug, Deserialize)]
pub struct AppendEventRequest {
    pub event_type: String,
    pub event_source: Option<String>,
    pub participant_identity: Option<String>,
    pub payload: Option<serde_json::Value>,
}

/// Request body for updating a participant's role.
#[derive(Debug, Deserialize)]
pub struct UpdateRoleRequest {
    pub role: String,
}

/// Request body for updating session settings (`session_metadata` fields).
#[derive(Debug, Deserialize)]
pub struct UpdateSettingsRequest {
    pub lock_room: Option<bool>,
    pub ai_enabled: Option<bool>,
    pub grade_level: Option<String>,
    pub ai_cost_ceiling_usd: Option<f64>,
}

/// Request body for the mute-all moderation action.
#[derive(Debug, Deserialize)]
pub struct MuteAllRequest {
    pub include_cohosts: Option<bool>,
}

/// Request body for removing a participant.
#[derive(Debug, Deserialize)]
pub struct RemoveParticipantRequest {
    pub participant_identity: String,
}

/// Query carrying the scoped join credential on the WS upgrade / signaling routes.
#[derive(Debug, Deserialize)]
pub struct SignalQuery {
    pub credential: String,
}

// ---------------------------------------------------------------------------
// Signaling message enums (JSON over the Rust WebSocket)
// ---------------------------------------------------------------------------

/// A WebRTC ICE candidate, shaped to match the browser `RTCIceCandidate` /
/// Janus trickle wire format (camelCase keys). `None`/absent fields are omitted
/// when serialized so Janus and the browser receive clean payloads.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IceCandidate {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub candidate: Option<String>,
    #[serde(rename = "sdpMid", skip_serializing_if = "Option::is_none")]
    pub sdp_mid: Option<String>,
    #[serde(rename = "sdpMLineIndex", skip_serializing_if = "Option::is_none")]
    pub sdp_mline_index: Option<u32>,
    /// Janus end-of-candidates marker (`{"completed": true}`).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub completed: Option<bool>,
}

/// Summary of a VideoRoom publisher feed advertised to peers.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PublisherInfo {
    pub feed_id: i64,
    pub display: Option<String>,
}

/// Client → Rust signaling messages.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ClientSignal {
    JoinPublisher {
        display_name: String,
    },
    Publish {
        sdp_offer: String,
        audio: bool,
        video: bool,
    },
    Subscribe {
        feed_id: i64,
    },
    /// Answer for a subscriber handle.
    Answer {
        feed_id: i64,
        sdp_answer: String,
    },
    /// `candidate: None` signals end-of-candidates.
    Trickle {
        candidate: Option<IceCandidate>,
    },
    Unpublish,
    Leave,
}

/// Rust → Client signaling messages.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ServerSignal {
    Joined {
        feed_id: i64,
        publishers: Vec<PublisherInfo>,
    },
    /// Publisher answer.
    Answer {
        sdp: String,
    },
    /// Subscriber offer.
    Offer {
        feed_id: i64,
        sdp: String,
    },
    Publishers {
        publishers: Vec<PublisherInfo>,
    },
    Trickle {
        feed_id: Option<i64>,
        candidate: Option<IceCandidate>,
    },
    Leaving {
        feed_id: i64,
    },
    Error {
        code: String,
        message: String,
    },
}

// ---------------------------------------------------------------------------
// Helper conversions (row -> response DTO)
// ---------------------------------------------------------------------------

impl LiveSession {
    /// Build a [`LiveSessionOut`] from this row plus a participant count.
    pub fn to_out(self, participant_count: i64) -> LiveSessionOut {
        LiveSessionOut {
            id: self.id,
            classroom_id: self.classroom_id,
            created_by_id: self.created_by_id,
            room_name: self.room_name,
            title: self.title,
            status: self.status,
            starts_at: self.starts_at,
            ended_at: self.ended_at,
            idempotency_key: self.idempotency_key,
            session_metadata: self.session_metadata,
            created_at: self.created_at,
            updated_at: self.updated_at,
            participant_count,
        }
    }
}

impl From<LiveParticipant> for LiveParticipantOut {
    fn from(p: LiveParticipant) -> Self {
        LiveParticipantOut {
            id: p.id,
            participant_identity: p.participant_identity,
            user_id: p.user_id,
            display_name: p.display_name,
            role: p.role,
            is_ai: p.is_ai,
            joined_at: p.joined_at,
            left_at: p.left_at,
        }
    }
}

impl From<LiveEvent> for LiveEventOut {
    fn from(e: LiveEvent) -> Self {
        LiveEventOut {
            id: e.id,
            event_type: e.event_type,
            event_source: e.event_source,
            participant_identity: e.participant_identity,
            participant_user_id: e.participant_user_id,
            payload: e.payload,
            created_at: e.created_at,
        }
    }
}
