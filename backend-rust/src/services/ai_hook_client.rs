//! AI lifecycle hook client (Task 10).
//!
//! The Rust → Python integration boundary. Notifies the Python AI worker of
//! live-session lifecycle changes (`session.created`, `session.ended`,
//! `ai_toggled`) over an internal HTTP endpoint so the worker can attach or
//! detach its AI-teacher participant.
//!
//! ## Fire-and-forget, never blocks the control plane
//!
//! Per Requirement 10.3 a hook delivery failure MUST NOT block the control
//! plane. This client therefore:
//!   * retries transient delivery failures with exponential backoff (up to
//!     [`AiHookClient::MAX_RETRIES`] attempts) inside [`AiHookClient::post_json`],
//!     and
//!   * returns `Err(AiHookError::Delivery(_))` only after the retry budget is
//!     exhausted, so the **caller** can record the failure and move on.
//!
//! The actual `ai_hook_failed` event recording is performed by the *caller*
//! (`live_session_service`, Task 11), which owns the `PgPool` +
//! `live_event_service`. This module is deliberately self-contained: it owns
//! its own [`AiHookError`] (NOT `AppError`) and has no DB dependency. The
//! intended caller shape is:
//!
//! ```ignore
//! // Inside live_session_service, after creating the session (gated on
//! // session_metadata.ai_enabled). Spawned so it never blocks the response:
//! let ai = ai_hook.clone();
//! let pool = pool.clone();
//! tokio::spawn(async move {
//!     if let Err(e) = ai.session_created(&payload).await {
//!         // Delivery failed after retries — record the audit event and carry on.
//!         let _ = live_event_service::record(&pool, EventInsert {
//!             live_session_id: payload.live_session_id,
//!             event_type: "ai_hook_failed".into(),
//!             payload: serde_json::json!({ "hook": "session.created", "error": e.to_string() }),
//!             ..Default::default()
//!         }).await;
//!     }
//! });
//! ```
//!
//! For convenience this module also exposes `spawn_*` helpers (see
//! [`AiHookClient::spawn_session_created`] etc.) that wrap the async methods in
//! a detached `tokio::spawn`, logging on failure. The session service may use
//! those directly when it does not need to record an `ai_hook_failed` event
//! itself, or use the awaitable methods when it does.
//!
//! Validates: Requirements 10.1, 10.2, 10.3

use std::sync::Arc;
use std::time::Duration;

use serde::Serialize;
use serde_json::{json, Value};
use uuid::Uuid;

/// Errors raised by the AI lifecycle hook client.
///
/// Intentionally self-contained (no `AppError` dependency). The only variant,
/// [`AiHookError::Delivery`], is returned after the retry budget is exhausted so
/// the caller can record an `ai_hook_failed` event without blocking.
#[derive(Debug, thiserror::Error)]
pub enum AiHookError {
    /// Hook delivery failed after exhausting retries (network error, non-2xx
    /// status, etc.). The string carries the last error context for logging /
    /// the `ai_hook_failed` event payload.
    #[error("ai hook delivery failed: {0}")]
    Delivery(String),
}

/// Payload for the `session.created` lifecycle hook.
///
/// Mirrors Requirement 10.1: includes `live_session_id`, `classroom_id`,
/// `janus_ws_url`, `janus_room_id`, `ai_teacher_identity`, `grade_level`, and
/// `ai_cost_ceiling_usd`. Optional fields are emitted as JSON `null` when absent
/// (default serde behavior) so the Python worker sees a stable key set.
#[derive(Debug, Clone, Serialize)]
pub struct AiSessionPayload {
    /// The live session this AI teacher should attach to.
    pub live_session_id: Uuid,
    /// The classroom that owns the session.
    pub classroom_id: Uuid,
    /// The Janus WebSocket URL the worker should connect to as a publisher.
    pub janus_ws_url: String,
    /// The Janus VideoRoom id the AI teacher should join.
    pub janus_room_id: i64,
    /// The identity the AI teacher publishes under (`ai-teacher-<id16>`).
    pub ai_teacher_identity: String,
    /// Optional grade level used to tune the AI teacher's behavior.
    pub grade_level: Option<String>,
    /// Optional per-session AI spend ceiling in USD.
    pub ai_cost_ceiling_usd: Option<f64>,
}

/// `reqwest`-backed client that POSTs lifecycle hooks to the Python AI worker.
///
/// Holds the shared `LIVE_INTERNAL_TOKEN` server-side; it is sent as the
/// `X-Live-Internal-Token` header on every request and is redacted from `Debug`
/// output so it never leaks via logs.
#[derive(Clone)]
pub struct AiHookClient {
    http: reqwest::Client,
    worker_base_url: String,
    internal_token: String,
}

impl std::fmt::Debug for AiHookClient {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Redact the internal token so it never leaks via logs/Debug.
        f.debug_struct("AiHookClient")
            .field("worker_base_url", &self.worker_base_url)
            .field("internal_token", &"<redacted>")
            .finish()
    }
}

impl AiHookClient {
    /// HTTP header carrying the shared internal service token. The Python worker
    /// validates this on `/internal/ai/*` (distinct from user JWTs).
    pub const INTERNAL_TOKEN_HEADER: &'static str = "X-Live-Internal-Token";

    /// Total number of delivery attempts (1 initial + retries) before giving up.
    const MAX_RETRIES: u32 = 3;

    /// Construct a client pointing at the Python AI worker `worker_base_url`,
    /// authenticating with the shared `internal_token`.
    pub fn new(worker_base_url: String, internal_token: String) -> Self {
        Self {
            http: reqwest::Client::new(),
            worker_base_url,
            internal_token,
        }
    }

    // ---- Lifecycle hooks ------------------------------------------------

    /// POST a `session.created` hook to the worker.
    ///
    /// Validates: Requirements 10.1
    pub async fn session_created(&self, payload: &AiSessionPayload) -> Result<(), AiHookError> {
        // Serialize to a Value so post_json owns a single delivery path. Payload
        // is plain data (no non-finite floats) so serialization cannot fail in
        // practice; surface any failure as a delivery error rather than panic.
        let body = serde_json::to_value(payload)
            .map_err(|e| AiHookError::Delivery(format!("payload serialization failed: {e}")))?;
        self.post_json("/internal/ai/session.created", body).await
    }

    /// POST a `session.ended` hook to the worker.
    ///
    /// Validates: Requirements 10.2
    pub async fn session_ended(&self, session_id: Uuid) -> Result<(), AiHookError> {
        self.post_json(
            "/internal/ai/session.ended",
            json!({ "live_session_id": session_id }),
        )
        .await
    }

    /// POST an `ai_toggled` hook to the worker.
    ///
    /// Validates: Requirements 10.2
    pub async fn ai_toggled(&self, session_id: Uuid, enabled: bool) -> Result<(), AiHookError> {
        self.post_json(
            "/internal/ai/ai_toggled",
            json!({ "live_session_id": session_id, "enabled": enabled }),
        )
        .await
    }

    // ---- Fire-and-forget helpers ---------------------------------------
    //
    // These detach the delivery onto a background task so the control plane is
    // never blocked. They log on final failure. Callers that need to record an
    // `ai_hook_failed` audit event (with DB access) should instead `await` the
    // methods above inside their own spawned task — see the module docs.

    /// Spawn a detached `session.created` delivery; logs on final failure.
    pub fn spawn_session_created(self: Arc<Self>, payload: AiSessionPayload) {
        tokio::spawn(async move {
            if let Err(e) = self.session_created(&payload).await {
                tracing::warn!(
                    live_session_id = %payload.live_session_id,
                    error = %e,
                    "ai session.created hook delivery failed after retries"
                );
            }
        });
    }

    /// Spawn a detached `session.ended` delivery; logs on final failure.
    pub fn spawn_session_ended(self: Arc<Self>, session_id: Uuid) {
        tokio::spawn(async move {
            if let Err(e) = self.session_ended(session_id).await {
                tracing::warn!(
                    live_session_id = %session_id,
                    error = %e,
                    "ai session.ended hook delivery failed after retries"
                );
            }
        });
    }

    /// Spawn a detached `ai_toggled` delivery; logs on final failure.
    pub fn spawn_ai_toggled(self: Arc<Self>, session_id: Uuid, enabled: bool) {
        tokio::spawn(async move {
            if let Err(e) = self.ai_toggled(session_id, enabled).await {
                tracing::warn!(
                    live_session_id = %session_id,
                    enabled,
                    error = %e,
                    "ai ai_toggled hook delivery failed after retries"
                );
            }
        });
    }

    // ---- Transport ------------------------------------------------------

    /// POST `body` as JSON to `{worker_base_url}{path}` with the internal-token
    /// header. Retries transient delivery failures with exponential backoff
    /// (`100ms * 2^n`) up to [`Self::MAX_RETRIES`] attempts, returning the last
    /// error as [`AiHookError::Delivery`] once the budget is exhausted.
    ///
    /// A non-2xx response is treated as a (retryable) delivery failure: the AI
    /// worker may be momentarily unavailable or restarting.
    async fn post_json(&self, path: &str, body: Value) -> Result<(), AiHookError> {
        let url = self.build_url(path);
        let mut attempt: u32 = 0;
        loop {
            match self.send_once(&url, &body).await {
                Ok(()) => return Ok(()),
                Err(msg) => {
                    attempt += 1;
                    if attempt >= Self::MAX_RETRIES {
                        return Err(AiHookError::Delivery(msg));
                    }
                    // Backoff: 100ms, 200ms, 400ms, ... before the next attempt.
                    let backoff = Duration::from_millis(100u64 * 2u64.pow(attempt - 1));
                    tokio::time::sleep(backoff).await;
                }
            }
        }
    }

    /// Perform a single (non-retrying) POST. Network errors and non-2xx statuses
    /// map to an `Err(String)` describing the failure (retryable upstream).
    async fn send_once(&self, url: &str, body: &Value) -> Result<(), String> {
        let resp = self
            .http
            .post(url)
            .header(Self::INTERNAL_TOKEN_HEADER, &self.internal_token)
            .json(body)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let status = resp.status();
        if status.is_success() {
            Ok(())
        } else {
            Err(format!("ai worker returned status {status}"))
        }
    }

    /// Join the configured base URL with a hook `path`, tolerating a trailing
    /// slash on the base so callers need not normalize it.
    fn build_url(&self, path: &str) -> String {
        format!("{}{}", self.worker_base_url.trim_end_matches('/'), path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn session_payload_serializes_with_expected_keys() {
        let live_session_id = Uuid::nil();
        let classroom_id = Uuid::from_u128(1);
        let payload = AiSessionPayload {
            live_session_id,
            classroom_id,
            janus_ws_url: "ws://janus.internal:8188".to_string(),
            janus_room_id: 4242,
            ai_teacher_identity: "ai-teacher-0123456789abcdef".to_string(),
            grade_level: Some("grade-5".to_string()),
            ai_cost_ceiling_usd: Some(1.50),
        };

        let value = serde_json::to_value(&payload).expect("payload serializes");
        let obj = value.as_object().expect("payload is a JSON object");

        // Exactly the seven keys mandated by Requirement 10.1, no more.
        let mut keys: Vec<&str> = obj.keys().map(String::as_str).collect();
        keys.sort_unstable();
        assert_eq!(
            keys,
            vec![
                "ai_cost_ceiling_usd",
                "ai_teacher_identity",
                "classroom_id",
                "grade_level",
                "janus_room_id",
                "janus_ws_url",
                "live_session_id",
            ]
        );

        assert_eq!(value["live_session_id"], live_session_id.to_string());
        assert_eq!(value["classroom_id"], classroom_id.to_string());
        assert_eq!(value["janus_ws_url"], "ws://janus.internal:8188");
        assert_eq!(value["janus_room_id"], 4242);
        assert_eq!(value["ai_teacher_identity"], "ai-teacher-0123456789abcdef");
        assert_eq!(value["grade_level"], "grade-5");
        assert_eq!(value["ai_cost_ceiling_usd"], 1.50);
    }

    #[test]
    fn optional_fields_serialize_as_null_when_absent() {
        let payload = AiSessionPayload {
            live_session_id: Uuid::nil(),
            classroom_id: Uuid::nil(),
            janus_ws_url: "ws://janus".to_string(),
            janus_room_id: 1,
            ai_teacher_identity: "ai-teacher-x".to_string(),
            grade_level: None,
            ai_cost_ceiling_usd: None,
        };

        let value = serde_json::to_value(&payload).expect("payload serializes");
        // Keys are present but null, giving the worker a stable key set.
        assert!(value.get("grade_level").is_some());
        assert!(value["grade_level"].is_null());
        assert!(value.get("ai_cost_ceiling_usd").is_some());
        assert!(value["ai_cost_ceiling_usd"].is_null());
    }

    #[test]
    fn client_construction_and_debug_redacts_token() {
        let client = AiHookClient::new(
            "http://ai-worker.internal:9000".to_string(),
            "super-secret-token".to_string(),
        );
        assert_eq!(client.worker_base_url, "http://ai-worker.internal:9000");
        assert_eq!(client.internal_token, "super-secret-token");

        let rendered = format!("{client:?}");
        assert!(rendered.contains("<redacted>"));
        assert!(!rendered.contains("super-secret-token"));
        assert!(rendered.contains("ai-worker.internal"));
    }

    #[test]
    fn build_url_trims_trailing_slash_on_base() {
        let with_slash = AiHookClient::new(
            "http://ai-worker.internal:9000/".to_string(),
            "tok".to_string(),
        );
        assert_eq!(
            with_slash.build_url("/internal/ai/session.created"),
            "http://ai-worker.internal:9000/internal/ai/session.created"
        );

        let without_slash =
            AiHookClient::new("http://ai-worker.internal:9000".to_string(), "tok".to_string());
        assert_eq!(
            without_slash.build_url("/internal/ai/session.ended"),
            "http://ai-worker.internal:9000/internal/ai/session.ended"
        );
    }

    #[test]
    fn ai_hook_error_displays_delivery_context() {
        let err = AiHookError::Delivery("connection refused".to_string());
        assert_eq!(err.to_string(), "ai hook delivery failed: connection refused");
    }
}
