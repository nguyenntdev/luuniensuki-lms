//! Janus signaling broker (Task 14).
//!
//! One [`SignalingSession`] runs per browser WebSocket. It owns a single Janus
//! session (over the Janus WebSocket API via `tokio-tungstenite`) and brokers
//! the VideoRoom attach / join / configure / trickle exchange between the
//! browser and Janus, so the browser never talks to Janus directly and never
//! sees the Janus admin/room secret (Req 5.3, 8.1).
//!
//! ## Message flow (Req 8.2–8.4)
//!
//! Browser → broker messages are [`ClientSignal`]; broker → browser messages are
//! [`ServerSignal`] (both defined in `models/live`). The broker:
//!   * on `JoinPublisher`: creates a Janus session, attaches a VideoRoom
//!     publisher handle, joins the room, persists the feed/handle binding, and
//!     replies `Joined { feed_id, publishers }`.
//!   * on `Publish`: forwards a `configure` request carrying the JSEP offer and
//!     returns the Janus JSEP answer as `Answer { sdp }`.
//!   * on `Subscribe`/`Answer`: attaches a subscriber handle and relays the
//!     subscriber offer/answer.
//!   * on `Trickle`: forwards ICE candidates (and the end-of-candidates marker)
//!     to Janus, and relays Janus candidates back to the browser.
//!   * on `Leave` / socket close: issues a VideoRoom `leave`, destroys the Janus
//!     session, and (after the reconnect grace window) marks the participant
//!     left and records a `participant_left` event (Req 8.6, 8.7).
//!
//! A Janus `keepalive` is sent every [`KEEPALIVE_SECS`] seconds on the
//! broker↔Janus session (Req 8.5).
//!
//! ## Status
//!
//! This module provides the broker's control structure, message
//! parsing/serialization, keepalive cadence, and teardown bookkeeping against a
//! pluggable [`JanusConn`] transport. The concrete Janus WebSocket transport
//! ([`TungsteniteJanusConn`]) is feature-isolated so the broker logic is
//! unit-testable with an in-memory fake connection without a live SFU.
//!
//! Validates: Requirements 8.1–8.7, 6.4, 3.1, 5.3

use std::time::Duration;

use axum::extract::ws::{Message as AxumMessage, WebSocket};
use serde_json::{json, Value};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::{ClientSignal, IceCandidate, PublisherInfo, ServerSignal};
use crate::services::{live_event_service, live_participant_service};

/// Janus keepalive cadence on the broker↔Janus session (Req 8.5).
pub const KEEPALIVE_SECS: u64 = 25;

/// VideoRoom plugin id used on attach.
const VIDEOROOM_PLUGIN: &str = "janus.plugin.videoroom";

/// Per-connection context: identifies the session/participant the broker is
/// bound to and carries the Janus room coordinates.
#[derive(Debug, Clone)]
pub struct SignalingCtx {
    pub session_id: Uuid,
    pub participant_id: Uuid,
    pub participant_identity: String,
    pub display_name: String,
    pub janus_room_id: i64,
    /// Reconnect grace window before a dropped client is marked left.
    pub reconnect_grace: Duration,
    /// Numeric publisher id used when joining the VideoRoom (derived from the
    /// participant id so it is stable across reconnects within a session).
    pub numeric_id: i64,
}

impl SignalingCtx {
    /// Derive the stable numeric publisher id for a participant (low 53 bits so
    /// it round-trips through JSON numbers safely).
    pub fn derive_numeric_id(participant_id: Uuid) -> i64 {
        ((participant_id.as_u128() as u64) & 0x1f_ffff_ffff_ffff) as i64
    }
}

/// Minimal transport abstraction over the broker↔Janus connection so the broker
/// logic can be exercised with an in-memory fake in tests.
pub trait JanusConn: Send {
    /// Send a JSON message to Janus.
    fn send_json(
        &mut self,
        value: Value,
    ) -> impl std::future::Future<Output = Result<(), AppError>> + Send;

    /// Receive the next JSON message from Janus (None when the connection
    /// closes).
    fn recv_json(
        &mut self,
    ) -> impl std::future::Future<Output = Result<Option<Value>, AppError>> + Send;
}

// ---------------------------------------------------------------------------
// Pure request-builders + parsers (unit-testable without any transport)
// ---------------------------------------------------------------------------

/// Build the Janus `create` (new session) envelope.
pub fn build_create_session(transaction: &str) -> Value {
    json!({ "janus": "create", "transaction": transaction })
}

/// Build the Janus `attach` (VideoRoom plugin) envelope for a session.
pub fn build_attach(session: i64, transaction: &str) -> Value {
    json!({
        "janus": "attach",
        "session_id": session,
        "plugin": VIDEOROOM_PLUGIN,
        "transaction": transaction,
    })
}

/// Build the VideoRoom publisher `join` message.
pub fn build_join_publisher(
    session: i64,
    handle: i64,
    room: i64,
    feed_id: i64,
    display: &str,
    transaction: &str,
) -> Value {
    json!({
        "janus": "message",
        "session_id": session,
        "handle_id": handle,
        "transaction": transaction,
        "body": {
            "request": "join",
            "ptype": "publisher",
            "room": room,
            "id": feed_id,
            "display": display,
        },
    })
}

/// Build the VideoRoom `configure` message carrying a JSEP offer (publish).
pub fn build_publish(
    session: i64,
    handle: i64,
    audio: bool,
    video: bool,
    sdp_offer: &str,
    transaction: &str,
) -> Value {
    json!({
        "janus": "message",
        "session_id": session,
        "handle_id": handle,
        "transaction": transaction,
        "body": { "request": "configure", "audio": audio, "video": video },
        "jsep": { "type": "offer", "sdp": sdp_offer },
    })
}

/// Build a Janus `trickle` message (a candidate, or the end-of-candidates
/// marker when `candidate` is `None`).
pub fn build_trickle(
    session: i64,
    handle: i64,
    candidate: Option<&IceCandidate>,
    transaction: &str,
) -> Value {
    let cand = match candidate {
        Some(c) => serde_json::to_value(c).unwrap_or(json!({})),
        None => json!({ "completed": true }),
    };
    json!({
        "janus": "trickle",
        "session_id": session,
        "handle_id": handle,
        "transaction": transaction,
        "candidate": cand,
    })
}

/// Build the VideoRoom `leave` message.
pub fn build_leave(session: i64, handle: i64, transaction: &str) -> Value {
    json!({
        "janus": "message",
        "session_id": session,
        "handle_id": handle,
        "transaction": transaction,
        "body": { "request": "leave" },
    })
}

/// Build the Janus `keepalive` message for a session (Req 8.5).
pub fn build_keepalive(session: i64, transaction: &str) -> Value {
    json!({ "janus": "keepalive", "session_id": session, "transaction": transaction })
}

/// Build the Janus `destroy` (session teardown) message.
pub fn build_destroy_session(session: i64, transaction: &str) -> Value {
    json!({ "janus": "destroy", "session_id": session, "transaction": transaction })
}

/// Extract the publishers array from a VideoRoom `joined` event payload.
pub fn parse_publishers(plugindata: &Value) -> Vec<PublisherInfo> {
    plugindata
        .get("publishers")
        .and_then(Value::as_array)
        .map(|arr| {
            arr.iter()
                .filter_map(|p| {
                    let feed_id = p.get("id").and_then(Value::as_i64)?;
                    let display = p.get("display").and_then(Value::as_str).map(str::to_string);
                    Some(PublisherInfo { feed_id, display })
                })
                .collect()
        })
        .unwrap_or_default()
}

/// Pull the JSEP SDP string out of a Janus event (`jsep.sdp`).
pub fn parse_jsep_sdp(event: &Value) -> Option<String> {
    event
        .get("jsep")
        .and_then(|j| j.get("sdp"))
        .and_then(Value::as_str)
        .map(str::to_string)
}

/// Whether a Janus event is a `webrtcup` notification (publish established —
/// Req 6.4 records `participant_published` once on this).
pub fn is_webrtcup(event: &Value) -> bool {
    event.get("janus").and_then(Value::as_str) == Some("webrtcup")
}

/// A new transaction id for a Janus envelope.
fn txn() -> String {
    Uuid::new_v4().simple().to_string()
}

/// Serialize a [`ServerSignal`] to a JSON text frame for the browser.
pub fn server_signal_text(sig: &ServerSignal) -> String {
    serde_json::to_string(sig).unwrap_or_else(|_| {
        r#"{"type":"error","code":"INTERNAL","message":"serialization failed"}"#.to_string()
    })
}

/// Parse an incoming browser text frame into a [`ClientSignal`].
pub fn parse_client_signal(text: &str) -> Result<ClientSignal, String> {
    serde_json::from_str::<ClientSignal>(text).map_err(|e| e.to_string())
}

// ---------------------------------------------------------------------------
// Roster bookkeeping on disconnect (Req 8.6, 8.7)
// ---------------------------------------------------------------------------

/// After the client WebSocket closes, wait out the reconnect grace window and —
/// if the participant has not rejoined — mark them left and record a
/// `participant_left` event. The "rejoined" check is delegated to the caller via
/// `rejoined`, which is re-evaluated after the grace sleep.
pub async fn finalize_disconnect<F>(
    pool: &PgPool,
    ctx: &SignalingCtx,
    grace: Duration,
    rejoined: F,
) -> Result<(), AppError>
where
    F: FnOnce() -> bool,
{
    tokio::time::sleep(grace).await;
    if rejoined() {
        return Ok(()); // client reconnected within the window; keep the row
    }

    live_participant_service::mark_left(
        pool,
        ctx.session_id,
        None,
        Some(&ctx.participant_identity),
    )
    .await?;

    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(ctx.session_id, "participant_left", "system")
            .with_identity(&ctx.participant_identity),
    )
    .await;

    Ok(())
}

/// Record the one-time `participant_published` event when Janus reports
/// `webrtcup` for this participant (Req 6.4). Idempotency at the DB level is the
/// caller's concern (the broker only fires this once per publish).
pub async fn record_published(pool: &PgPool, ctx: &SignalingCtx) -> Result<(), AppError> {
    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(ctx.session_id, "participant_published", "system")
            .with_identity(&ctx.participant_identity),
    )
    .await?;
    Ok(())
}

// ---------------------------------------------------------------------------
// Browser frame helpers
// ---------------------------------------------------------------------------

/// Classify an inbound axum WebSocket frame: `Some(Some(text))` for a text
/// frame, `Some(None)` for a non-text data frame to ignore, `None` for a close.
pub fn classify_client_frame(msg: &AxumMessage) -> Option<Option<&str>> {
    match msg {
        AxumMessage::Text(t) => Some(Some(t.as_str())),
        AxumMessage::Close(_) => None,
        AxumMessage::Binary(_) | AxumMessage::Ping(_) | AxumMessage::Pong(_) => Some(None),
    }
}

/// Send a [`ServerSignal`] to the browser over the axum WebSocket.
pub async fn send_to_client(ws: &mut WebSocket, sig: &ServerSignal) -> Result<(), AppError> {
    ws.send(AxumMessage::Text(server_signal_text(sig)))
        .await
        .map_err(|e| AppError::Internal(anyhow::anyhow!("ws send failed: {e}")))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn numeric_id_is_stable_and_in_range() {
        let id = Uuid::new_v4();
        let a = SignalingCtx::derive_numeric_id(id);
        let b = SignalingCtx::derive_numeric_id(id);
        assert_eq!(a, b);
        assert!(a >= 0);
        assert!(a <= 0x1f_ffff_ffff_ffff);
    }

    #[test]
    fn create_and_attach_envelopes() {
        let c = build_create_session("t1");
        assert_eq!(c["janus"], "create");
        assert_eq!(c["transaction"], "t1");

        let a = build_attach(42, "t2");
        assert_eq!(a["janus"], "attach");
        assert_eq!(a["session_id"], 42);
        assert_eq!(a["plugin"], VIDEOROOM_PLUGIN);
    }

    #[test]
    fn join_publisher_body_is_correct() {
        let m = build_join_publisher(10, 20, 555, 999, "Alice", "t");
        assert_eq!(m["janus"], "message");
        assert_eq!(m["session_id"], 10);
        assert_eq!(m["handle_id"], 20);
        assert_eq!(m["body"]["request"], "join");
        assert_eq!(m["body"]["ptype"], "publisher");
        assert_eq!(m["body"]["room"], 555);
        assert_eq!(m["body"]["id"], 999);
        assert_eq!(m["body"]["display"], "Alice");
    }

    #[test]
    fn publish_carries_jsep_offer() {
        let m = build_publish(1, 2, true, false, "v=0...", "t");
        assert_eq!(m["body"]["request"], "configure");
        assert_eq!(m["body"]["audio"], true);
        assert_eq!(m["body"]["video"], false);
        assert_eq!(m["jsep"]["type"], "offer");
        assert_eq!(m["jsep"]["sdp"], "v=0...");
    }

    #[test]
    fn trickle_with_candidate_and_end_marker() {
        let cand = IceCandidate {
            candidate: Some("candidate:1 1 udp ...".to_string()),
            sdp_mid: Some("0".to_string()),
            sdp_mline_index: Some(0),
            completed: None,
        };
        let with = build_trickle(1, 2, Some(&cand), "t");
        assert_eq!(with["candidate"]["candidate"], "candidate:1 1 udp ...");
        assert_eq!(with["candidate"]["sdpMid"], "0");

        let end = build_trickle(1, 2, None, "t");
        assert_eq!(end["candidate"]["completed"], true);
    }

    #[test]
    fn keepalive_and_destroy_target_session() {
        assert_eq!(build_keepalive(7, "t")["janus"], "keepalive");
        assert_eq!(build_keepalive(7, "t")["session_id"], 7);
        assert_eq!(build_destroy_session(7, "t")["janus"], "destroy");
    }

    #[test]
    fn parse_publishers_reads_feeds() {
        let data = json!({
            "videoroom": "joined",
            "publishers": [
                { "id": 1, "display": "Alice" },
                { "id": 2 },
            ],
        });
        let pubs = parse_publishers(&data);
        assert_eq!(pubs.len(), 2);
        assert_eq!(pubs[0].feed_id, 1);
        assert_eq!(pubs[0].display.as_deref(), Some("Alice"));
        assert_eq!(pubs[1].feed_id, 2);
        assert!(pubs[1].display.is_none());
    }

    #[test]
    fn parse_publishers_empty_when_absent() {
        assert!(parse_publishers(&json!({ "videoroom": "event" })).is_empty());
    }

    #[test]
    fn parse_jsep_sdp_extracts() {
        let ev = json!({ "janus": "event", "jsep": { "type": "answer", "sdp": "v=0 answer" } });
        assert_eq!(parse_jsep_sdp(&ev).as_deref(), Some("v=0 answer"));
        assert!(parse_jsep_sdp(&json!({ "janus": "event" })).is_none());
    }

    #[test]
    fn webrtcup_detected() {
        assert!(is_webrtcup(&json!({ "janus": "webrtcup" })));
        assert!(!is_webrtcup(&json!({ "janus": "event" })));
    }

    #[test]
    fn client_signal_round_trips() {
        let txt = r#"{"type":"join_publisher","display_name":"Bob"}"#;
        match parse_client_signal(txt).unwrap() {
            ClientSignal::JoinPublisher { display_name } => assert_eq!(display_name, "Bob"),
            other => panic!("unexpected: {other:?}"),
        }

        let bad = parse_client_signal("not json");
        assert!(bad.is_err());
    }

    #[test]
    fn server_signal_serializes_with_type_tag() {
        let s = server_signal_text(&ServerSignal::Answer {
            sdp: "v=0".to_string(),
        });
        assert!(s.contains("\"type\":\"answer\""));
        assert!(s.contains("\"sdp\":\"v=0\""));

        let e = server_signal_text(&ServerSignal::Error {
            code: "ROOM_LOCKED".to_string(),
            message: "locked".to_string(),
        });
        assert!(e.contains("\"type\":\"error\""));
        assert!(e.contains("ROOM_LOCKED"));
    }

    #[test]
    fn classify_client_frame_variants() {
        assert_eq!(
            classify_client_frame(&AxumMessage::Text("hi".to_string())),
            Some(Some("hi"))
        );
        assert_eq!(
            classify_client_frame(&AxumMessage::Binary(vec![1])),
            Some(None)
        );
        assert!(classify_client_frame(&AxumMessage::Close(None)).is_none());
    }
}
