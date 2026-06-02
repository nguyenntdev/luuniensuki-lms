//! Janus VideoRoom admin client (Task 6).
//!
//! Maps the LiveKit `RoomService` operations onto Janus VideoRoom admin
//! requests, mirroring the Python `_livekit_room_service_request` behavior:
//!
//! | LiveKit RoomService          | Janus VideoRoom request                                                           |
//! |------------------------------|-----------------------------------------------------------------------------------|
//! | `CreateRoom`                 | `{"request":"create","room":<id>,"secret":...,"publishers":N,"bitrate":...,...}`   |
//! | `DeleteRoom`                 | `{"request":"destroy","room":<id>,"secret":...}`                                  |
//! | `ListParticipants`           | `{"request":"listparticipants","room":<id>}`                                      |
//! | `RemoveParticipant` (kick)   | `{"request":"kick","room":<id>,"secret":...,"id":<feed_id>}`                       |
//! | `MutePublishedTrack` (mute)  | `{"request":"moderate","room":<id>,"secret":...,"id":<feed_id>,"mute_audio":...}`  |
//! | (room existence)             | `{"request":"exists","room":<id>}`                                                |
//!
//! ## Wire-format assumptions
//!
//! Talking to a live Janus instance over its raw HTTP/WS API requires a
//! create-session → attach-handle → message dance. We deliberately *simplify*
//! and encapsulate that behind a single private helper, [`JanusAdminClient::videoroom_request`],
//! which POSTs a Janus message envelope of the shape:
//!
//! ```json
//! { "janus": "message", "transaction": "<random>", "admin_secret": "<redacted>", "body": { ...videoroom request... } }
//! ```
//!
//! to `base_url`, and reads the VideoRoom plugin reply out of
//! `response["plugindata"]["data"]`. A VideoRoom error reply carries an
//! `error_code` (i64) and `error` (string); a success reply carries the
//! `videoroom` discriminator (e.g. `"created"`, `"destroyed"`, `"success"`)
//! plus operation-specific fields (`participants`, `exists`, ...). These
//! assumptions are documented here so the signaling broker (Task 14) and a real
//! Janus deployment can adjust the envelope in one place without touching the
//! operation methods.
//!
//! ## Trait boundary
//!
//! The design refers to this component as `JanusAdmin`. To let property/unit
//! tests fake the media plane without a live SFU, the surface is split into:
//!   * [`JanusAdminClient`] — the concrete `reqwest`-backed client holding the
//!     admin secret, with inherent `async` methods carrying the real logic, and
//!   * [`JanusAdminApi`] — a trait declaring the same operations via
//!     return-position `impl Future` (RPITIT, stable since Rust 1.75), so a
//!     downstream service can be generic over a real or in-memory impl.
//!
//! This module owns its own [`JanusError`] (it does NOT depend on `AppError`);
//! callers map `JanusError` into their own error envelope.
//!
//! Validates: Requirements 9.1, 9.2, 9.4, 9.5

use std::future::Future;
use std::time::Duration;

use serde_json::{json, Value};

/// Janus VideoRoom error code for "No such room" (`JANUS_VIDEOROOM_ERROR_NO_SUCH_ROOM`).
const ERR_NO_SUCH_ROOM: i64 = 426;
/// Janus VideoRoom error code for "Room already exists" (`JANUS_VIDEOROOM_ERROR_ROOM_EXISTS`).
const ERR_ROOM_EXISTS: i64 = 427;

/// Errors raised by the Janus admin client.
///
/// Intentionally self-contained (no `AppError` dependency). `Transport` is the
/// only retryable variant.
#[derive(Debug, thiserror::Error)]
pub enum JanusError {
    /// A network / HTTP-level failure (connect error, timeout, 5xx, body decode
    /// failure). Retried with exponential backoff up to `max_retries`.
    #[error("janus transport error: {0}")]
    Transport(String),

    /// The VideoRoom plugin returned an error reply (`error_code` + `error`).
    #[error("janus plugin error {code}: {reason}")]
    Plugin { code: i64, reason: String },

    /// The response was well-formed HTTP/JSON but did not match the expected
    /// VideoRoom envelope shape.
    #[error("unexpected janus response: {0}")]
    Unexpected(String),
}

/// Options for provisioning a VideoRoom (mirrors the LiveKit `CreateRoom` knobs
/// the live stack cares about).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RoomOpts {
    /// Maximum simultaneous publishers allowed in the room.
    pub publishers: i64,
    /// Per-publisher target bitrate in bits/sec.
    pub bitrate: i64,
    /// Whether to emit audio-level events (used for active-speaker UI).
    pub audiolevel_event: bool,
}

/// A single participant as reported by VideoRoom `listparticipants`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JanusParticipant {
    /// The VideoRoom feed id of this participant.
    pub id: i64,
    /// Optional display name bound at join time.
    pub display: Option<String>,
    /// Whether this participant is currently publishing media.
    pub publisher: bool,
}

/// `reqwest`-backed Janus VideoRoom admin client.
///
/// Holds the Janus admin secret server-side; it is never serialized into a
/// client-facing response and is redacted from `Debug` output.
#[derive(Clone)]
pub struct JanusAdminClient {
    http: reqwest::Client,
    base_url: String,
    admin_secret: String,
    max_retries: u32,
}

impl std::fmt::Debug for JanusAdminClient {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Redact the admin secret so it never leaks via logs/Debug.
        f.debug_struct("JanusAdminClient")
            .field("base_url", &self.base_url)
            .field("admin_secret", &"<redacted>")
            .field("max_retries", &self.max_retries)
            .finish()
    }
}

impl JanusAdminClient {
    /// Default number of retries for transient transport failures.
    const DEFAULT_MAX_RETRIES: u32 = 3;

    /// Construct a client pointing at the Janus admin/HTTP `base_url`, holding
    /// the `admin_secret` server-side.
    pub fn new(base_url: impl Into<String>, admin_secret: impl Into<String>) -> Self {
        Self {
            http: reqwest::Client::new(),
            base_url: base_url.into(),
            admin_secret: admin_secret.into(),
            max_retries: Self::DEFAULT_MAX_RETRIES,
        }
    }

    /// Override the retry budget (primarily for tests / tuning).
    pub fn with_max_retries(mut self, max_retries: u32) -> Self {
        self.max_retries = max_retries;
        self
    }

    // ---- Operations ----------------------------------------------------

    /// Create a VideoRoom. Treats "already exists" as success (`allow_not_found`).
    ///
    /// Validates: Requirements 9.1, 9.4
    pub async fn create_room(
        &self,
        room: i64,
        opts: &RoomOpts,
        secret: &str,
    ) -> Result<(), JanusError> {
        let resp = self.videoroom_request(build_create_body(room, opts, secret)).await?;
        let data = extract_plugin_data(&resp)?;
        // allow_benign = true: "already exists" is success-equivalent for create.
        interpret_plugin_result(data, true)
    }

    /// Destroy a VideoRoom. Treats "no such room" as success (`allow_not_found`).
    ///
    /// Validates: Requirements 9.2, 9.4
    pub async fn destroy_room(&self, room: i64, secret: &str) -> Result<(), JanusError> {
        let resp = self.videoroom_request(build_destroy_body(room, secret)).await?;
        let data = extract_plugin_data(&resp)?;
        // allow_benign = true: "no such room" is success-equivalent for destroy.
        interpret_plugin_result(data, true)
    }

    /// List the participants currently in a VideoRoom.
    pub async fn list_participants(&self, room: i64) -> Result<Vec<JanusParticipant>, JanusError> {
        let resp = self.videoroom_request(build_list_body(room)).await?;
        let data = extract_plugin_data(&resp)?;
        if let Some((code, reason)) = plugin_error(data) {
            return Err(JanusError::Plugin { code, reason });
        }
        parse_participants(data)
    }

    /// Kick (remove) a publisher feed from a room. Requires the per-room secret.
    ///
    /// Validates: Requirements 9.5
    pub async fn kick(&self, room: i64, secret: &str, feed_id: i64) -> Result<(), JanusError> {
        let resp = self.videoroom_request(build_kick_body(room, secret, feed_id)).await?;
        let data = extract_plugin_data(&resp)?;
        interpret_plugin_result(data, false)
    }

    /// Moderate a publisher feed (mute/unmute its audio). Requires the per-room
    /// secret.
    ///
    /// Validates: Requirements 9.5
    pub async fn moderate_mute(
        &self,
        room: i64,
        secret: &str,
        feed_id: i64,
        mute_audio: bool,
    ) -> Result<(), JanusError> {
        let resp = self
            .videoroom_request(build_moderate_body(room, secret, feed_id, mute_audio))
            .await?;
        let data = extract_plugin_data(&resp)?;
        interpret_plugin_result(data, false)
    }

    /// Check whether a VideoRoom currently exists. A "no such room" plugin error
    /// is normalized to `Ok(false)`.
    pub async fn room_exists(&self, room: i64) -> Result<bool, JanusError> {
        let resp = self.videoroom_request(build_exists_body(room)).await?;
        let data = extract_plugin_data(&resp)?;
        if let Some((code, reason)) = plugin_error(data) {
            if is_benign_plugin_error(code, &reason) {
                return Ok(false);
            }
            return Err(JanusError::Plugin { code, reason });
        }
        Ok(parse_exists(data))
    }

    // ---- Transport ------------------------------------------------------

    /// POST a VideoRoom request `body` wrapped in a Janus message envelope and
    /// return the full parsed response JSON. Retries transient transport
    /// failures with exponential backoff (`100ms * 2^n`).
    async fn videoroom_request(&self, body: Value) -> Result<Value, JanusError> {
        let mut attempt: u32 = 0;
        loop {
            // A fresh transaction id per attempt (Janus de-dupes on transaction).
            let envelope = json!({
                "janus": "message",
                "transaction": new_transaction_id(),
                "admin_secret": self.admin_secret,
                "body": body,
            });

            match self.send_once(&envelope).await {
                Ok(value) => return Ok(value),
                Err(JanusError::Transport(msg)) if attempt < self.max_retries => {
                    let backoff = Duration::from_millis(100u64 * 2u64.pow(attempt));
                    tokio::time::sleep(backoff).await;
                    attempt += 1;
                    let _ = msg; // last error context is folded into the next retry
                    continue;
                }
                Err(e) => return Err(e),
            }
        }
    }

    /// Perform a single (non-retrying) POST and decode the JSON body. Network
    /// errors, 5xx statuses, and body-decode failures map to
    /// [`JanusError::Transport`] (retryable).
    async fn send_once(&self, envelope: &Value) -> Result<Value, JanusError> {
        let resp = self
            .http
            .post(&self.base_url)
            .json(envelope)
            .send()
            .await
            .map_err(|e| JanusError::Transport(e.to_string()))?;

        if resp.status().is_server_error() {
            return Err(JanusError::Transport(format!(
                "janus returned status {}",
                resp.status()
            )));
        }

        resp.json::<Value>()
            .await
            .map_err(|e| JanusError::Transport(e.to_string()))
    }
}

/// Trait mirror of [`JanusAdminClient`] using return-position `impl Future`
/// (RPITIT). Lets services be generic over the real client or an in-memory fake
/// in tests. Not object-safe by design — use a generic bound, not `dyn`.
pub trait JanusAdminApi: Send + Sync {
    /// See [`JanusAdminClient::create_room`].
    fn create_room(
        &self,
        room: i64,
        opts: &RoomOpts,
        secret: &str,
    ) -> impl Future<Output = Result<(), JanusError>> + Send;

    /// See [`JanusAdminClient::destroy_room`].
    fn destroy_room(
        &self,
        room: i64,
        secret: &str,
    ) -> impl Future<Output = Result<(), JanusError>> + Send;

    /// See [`JanusAdminClient::list_participants`].
    fn list_participants(
        &self,
        room: i64,
    ) -> impl Future<Output = Result<Vec<JanusParticipant>, JanusError>> + Send;

    /// See [`JanusAdminClient::kick`].
    fn kick(
        &self,
        room: i64,
        secret: &str,
        feed_id: i64,
    ) -> impl Future<Output = Result<(), JanusError>> + Send;

    /// See [`JanusAdminClient::moderate_mute`].
    fn moderate_mute(
        &self,
        room: i64,
        secret: &str,
        feed_id: i64,
        mute_audio: bool,
    ) -> impl Future<Output = Result<(), JanusError>> + Send;

    /// See [`JanusAdminClient::room_exists`].
    fn room_exists(&self, room: i64) -> impl Future<Output = Result<bool, JanusError>> + Send;
}

/// The trait impl delegates to the inherent methods, which hold the real logic.
/// Inherent methods take precedence in resolution, so these calls do not recurse.
impl JanusAdminApi for JanusAdminClient {
    fn create_room(
        &self,
        room: i64,
        opts: &RoomOpts,
        secret: &str,
    ) -> impl Future<Output = Result<(), JanusError>> + Send {
        JanusAdminClient::create_room(self, room, opts, secret)
    }

    fn destroy_room(
        &self,
        room: i64,
        secret: &str,
    ) -> impl Future<Output = Result<(), JanusError>> + Send {
        JanusAdminClient::destroy_room(self, room, secret)
    }

    fn list_participants(
        &self,
        room: i64,
    ) -> impl Future<Output = Result<Vec<JanusParticipant>, JanusError>> + Send {
        JanusAdminClient::list_participants(self, room)
    }

    fn kick(
        &self,
        room: i64,
        secret: &str,
        feed_id: i64,
    ) -> impl Future<Output = Result<(), JanusError>> + Send {
        JanusAdminClient::kick(self, room, secret, feed_id)
    }

    fn moderate_mute(
        &self,
        room: i64,
        secret: &str,
        feed_id: i64,
        mute_audio: bool,
    ) -> impl Future<Output = Result<(), JanusError>> + Send {
        JanusAdminClient::moderate_mute(self, room, secret, feed_id, mute_audio)
    }

    fn room_exists(&self, room: i64) -> impl Future<Output = Result<bool, JanusError>> + Send {
        JanusAdminClient::room_exists(self, room)
    }
}

// ---- Pure helpers (testable without HTTP) -------------------------------

/// Generate a random transaction id for a Janus message envelope.
fn new_transaction_id() -> String {
    uuid::Uuid::new_v4().simple().to_string()
}

/// Build the VideoRoom `create` request body.
fn build_create_body(room: i64, opts: &RoomOpts, secret: &str) -> Value {
    json!({
        "request": "create",
        "room": room,
        "secret": secret,
        "publishers": opts.publishers,
        "bitrate": opts.bitrate,
        "audiolevel_event": opts.audiolevel_event,
        "notify_joining": true,
    })
}

/// Build the VideoRoom `destroy` request body.
fn build_destroy_body(room: i64, secret: &str) -> Value {
    json!({
        "request": "destroy",
        "room": room,
        "secret": secret,
    })
}

/// Build the VideoRoom `listparticipants` request body.
fn build_list_body(room: i64) -> Value {
    json!({
        "request": "listparticipants",
        "room": room,
    })
}

/// Build the VideoRoom `kick` request body.
fn build_kick_body(room: i64, secret: &str, feed_id: i64) -> Value {
    json!({
        "request": "kick",
        "room": room,
        "secret": secret,
        "id": feed_id,
    })
}

/// Build the VideoRoom `moderate` request body.
fn build_moderate_body(room: i64, secret: &str, feed_id: i64, mute_audio: bool) -> Value {
    json!({
        "request": "moderate",
        "room": room,
        "secret": secret,
        "id": feed_id,
        "mute_audio": mute_audio,
    })
}

/// Build the VideoRoom `exists` request body.
fn build_exists_body(room: i64) -> Value {
    json!({
        "request": "exists",
        "room": room,
    })
}

/// Pull the VideoRoom plugin payload out of a Janus response
/// (`response["plugindata"]["data"]`).
fn extract_plugin_data(resp: &Value) -> Result<&Value, JanusError> {
    resp.get("plugindata")
        .and_then(|p| p.get("data"))
        .ok_or_else(|| {
            JanusError::Unexpected(format!("missing plugindata.data in response: {resp}"))
        })
}

/// Extract a `(error_code, error)` pair from a VideoRoom payload, if present.
fn plugin_error(data: &Value) -> Option<(i64, String)> {
    let code = data.get("error_code").and_then(Value::as_i64)?;
    let reason = data
        .get("error")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();
    Some((code, reason))
}

/// Classify a VideoRoom plugin error as benign (`allow_not_found`): a
/// "no such room" or "already exists" condition that create/destroy treat as
/// success-equivalent.
///
/// Validates: Requirements 9.4
pub fn is_benign_plugin_error(code: i64, reason: &str) -> bool {
    if code == ERR_NO_SUCH_ROOM || code == ERR_ROOM_EXISTS {
        return true;
    }
    let r = reason.to_ascii_lowercase();
    r.contains("no such room") || r.contains("already exists") || r.contains("room exists")
}

/// Turn a VideoRoom payload into `Ok(())` or a [`JanusError::Plugin`]. When
/// `allow_benign` is set, a benign error (see [`is_benign_plugin_error`]) is
/// treated as success.
fn interpret_plugin_result(data: &Value, allow_benign: bool) -> Result<(), JanusError> {
    if let Some((code, reason)) = plugin_error(data) {
        if allow_benign && is_benign_plugin_error(code, &reason) {
            return Ok(());
        }
        return Err(JanusError::Plugin { code, reason });
    }
    Ok(())
}

/// Parse the `participants` array from a `listparticipants` payload.
fn parse_participants(data: &Value) -> Result<Vec<JanusParticipant>, JanusError> {
    let arr = data
        .get("participants")
        .and_then(Value::as_array)
        .ok_or_else(|| {
            JanusError::Unexpected(format!("listparticipants missing participants array: {data}"))
        })?;

    arr.iter()
        .map(|p| {
            let id = p.get("id").and_then(Value::as_i64).ok_or_else(|| {
                JanusError::Unexpected(format!("participant missing numeric id: {p}"))
            })?;
            let display = p
                .get("display")
                .and_then(Value::as_str)
                .map(str::to_string);
            let publisher = p.get("publisher").and_then(Value::as_bool).unwrap_or(false);
            Ok(JanusParticipant {
                id,
                display,
                publisher,
            })
        })
        .collect()
}

/// Read the `exists` boolean from an `exists` payload (absent → `false`).
fn parse_exists(data: &Value) -> bool {
    data.get("exists").and_then(Value::as_bool).unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---- Request-body construction -------------------------------------

    #[test]
    fn create_body_has_expected_keys() {
        let opts = RoomOpts {
            publishers: 12,
            bitrate: 256_000,
            audiolevel_event: true,
        };
        let body = build_create_body(42, &opts, "room-secret");

        assert_eq!(body["request"], "create");
        assert_eq!(body["room"], 42);
        assert_eq!(body["secret"], "room-secret");
        assert_eq!(body["publishers"], 12);
        assert_eq!(body["bitrate"], 256_000);
        assert_eq!(body["audiolevel_event"], true);
        assert_eq!(body["notify_joining"], true);
    }

    #[test]
    fn destroy_body_has_expected_keys() {
        let body = build_destroy_body(7, "s3cret");
        assert_eq!(body["request"], "destroy");
        assert_eq!(body["room"], 7);
        assert_eq!(body["secret"], "s3cret");
    }

    #[test]
    fn list_body_has_expected_keys() {
        let body = build_list_body(99);
        assert_eq!(body["request"], "listparticipants");
        assert_eq!(body["room"], 99);
    }

    #[test]
    fn kick_body_has_expected_keys() {
        let body = build_kick_body(3, "sek", 555);
        assert_eq!(body["request"], "kick");
        assert_eq!(body["room"], 3);
        assert_eq!(body["secret"], "sek");
        assert_eq!(body["id"], 555);
    }

    #[test]
    fn moderate_body_has_expected_keys() {
        let body = build_moderate_body(3, "sek", 555, true);
        assert_eq!(body["request"], "moderate");
        assert_eq!(body["room"], 3);
        assert_eq!(body["secret"], "sek");
        assert_eq!(body["id"], 555);
        assert_eq!(body["mute_audio"], true);

        let unmute = build_moderate_body(3, "sek", 555, false);
        assert_eq!(unmute["mute_audio"], false);
    }

    #[test]
    fn exists_body_has_expected_keys() {
        let body = build_exists_body(1234);
        assert_eq!(body["request"], "exists");
        assert_eq!(body["room"], 1234);
    }

    // ---- allow_not_found classification --------------------------------

    #[test]
    fn benign_by_error_code() {
        assert!(is_benign_plugin_error(ERR_NO_SUCH_ROOM, ""));
        assert!(is_benign_plugin_error(ERR_ROOM_EXISTS, ""));
    }

    #[test]
    fn benign_by_reason_text_case_insensitive() {
        assert!(is_benign_plugin_error(0, "No such room"));
        assert!(is_benign_plugin_error(0, "Room already exists"));
        assert!(is_benign_plugin_error(0, "ROOM EXISTS"));
    }

    #[test]
    fn non_benign_errors_are_not_swallowed() {
        assert!(!is_benign_plugin_error(499, "Unauthorized (wrong secret)"));
        assert!(!is_benign_plugin_error(0, "some other failure"));
    }

    // ---- response interpretation ---------------------------------------

    #[test]
    fn interpret_swallows_benign_when_allowed() {
        let data = json!({ "videoroom": "event", "error_code": ERR_ROOM_EXISTS, "error": "Room already exists" });
        assert!(interpret_plugin_result(&data, true).is_ok());
    }

    #[test]
    fn interpret_surfaces_benign_when_not_allowed() {
        let data = json!({ "videoroom": "event", "error_code": ERR_NO_SUCH_ROOM, "error": "No such room" });
        match interpret_plugin_result(&data, false) {
            Err(JanusError::Plugin { code, .. }) => assert_eq!(code, ERR_NO_SUCH_ROOM),
            other => panic!("expected plugin error, got {other:?}"),
        }
    }

    #[test]
    fn interpret_surfaces_non_benign_even_when_allowed() {
        let data = json!({ "videoroom": "event", "error_code": 499, "error": "Unauthorized" });
        assert!(matches!(
            interpret_plugin_result(&data, true),
            Err(JanusError::Plugin { code: 499, .. })
        ));
    }

    #[test]
    fn interpret_ok_on_success_payload() {
        let data = json!({ "videoroom": "created", "room": 42 });
        assert!(interpret_plugin_result(&data, false).is_ok());
    }

    #[test]
    fn extract_plugin_data_missing_is_unexpected() {
        let resp = json!({ "janus": "ack" });
        assert!(matches!(
            extract_plugin_data(&resp),
            Err(JanusError::Unexpected(_))
        ));
    }

    #[test]
    fn parse_participants_reads_rows() {
        let data = json!({
            "videoroom": "participants",
            "room": 5,
            "participants": [
                { "id": 1, "display": "Alice", "publisher": true },
                { "id": 2, "publisher": false },
            ],
        });
        let parsed = parse_participants(&data).unwrap();
        assert_eq!(
            parsed,
            vec![
                JanusParticipant { id: 1, display: Some("Alice".to_string()), publisher: true },
                JanusParticipant { id: 2, display: None, publisher: false },
            ]
        );
    }

    #[test]
    fn parse_exists_defaults_false() {
        assert!(parse_exists(&json!({ "videoroom": "success", "exists": true })));
        assert!(!parse_exists(&json!({ "videoroom": "success", "exists": false })));
        assert!(!parse_exists(&json!({ "videoroom": "success" })));
    }

    #[test]
    fn debug_redacts_admin_secret() {
        let client = JanusAdminClient::new("http://janus.internal:8088/janus", "super-secret");
        let rendered = format!("{client:?}");
        assert!(rendered.contains("<redacted>"));
        assert!(!rendered.contains("super-secret"));
    }
}
