//! Live virtual-classroom route handlers (Task 15).
//!
//! Native Axum handlers for the `/api/v1/live-sessions/*` control plane plus the
//! `/signal` WebSocket upgrade, replacing the gateway-pinned Python live routes.
//! All handlers reuse the existing `AuthState` + `route_helpers` auth pattern and
//! map failures to the `AppError` envelope.
//!
//! Media-plane operations are delegated to `JanusAdminClient` (built per-request
//! from `Settings`); session/participant/event/moderation logic lives in the
//! `live_*` services. The AI lifecycle hook is fire-and-forget and optional.
//!
//! Validates: Requirements 1.6, 5.3, 5.4, 5.5, 7.3, 9.6, 10.4, 10.5
//! (and exercises live_session/participant/event/moderation/credential services)

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Path, Query, State,
    },
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::live::{
    AppendEventRequest, CreateSessionRequest, EventsQuery, ListSessionsQuery, LiveCredentialOut,
    LiveEventOut, LiveParticipantOut, LiveSessionJoinOut, LiveSessionOut, MuteAllRequest,
    RemoveParticipantRequest, ServerSignal, SignalQuery, UpdateRoleRequest, UpdateSettingsRequest,
};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{authenticate, require_pool};
use crate::services::janus_admin::JanusAdminClient;
use crate::services::{
    live_auth, live_credential_service, live_event_service, live_moderation_service,
    live_participant_service, live_session_service,
};

/// ICE/TURN credential TTL in seconds (short-lived per design; 10 min).
const ICE_TTL_SECONDS: i64 = 600;

/// Build a Janus admin client from settings (admin URL + admin secret).
fn janus_client(state: &AuthState) -> JanusAdminClient {
    JanusAdminClient::new(
        state.settings.janus_admin_url.clone(),
        state.settings.janus_admin_secret.clone(),
    )
}

/// Resolve the JWT `role` claim for a user (auth + role) from the request.
fn authenticate_with_role(
    headers: &HeaderMap,
    settings: &crate::config::Settings,
) -> Result<(Uuid, String), AppError> {
    let token = crate::routes::route_helpers::extract_access_token(headers)
        .ok_or(AppError::Unauthorized)?;
    let claims = crate::auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    let uid: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok((uid, claims.role))
}

/// Load a session or return 404.
async fn load_session(
    pool: &sqlx::PgPool,
    id: Uuid,
) -> Result<crate::models::live::LiveSession, AppError> {
    live_session_service::get_session(pool, id)
        .await?
        .ok_or_else(|| AppError::Http {
            status: StatusCode::NOT_FOUND,
            message: "Live session not found".to_string(),
        })
}

/// Reject join/credential requests targeting an ended session (Req 7.3).
fn reject_if_ended(session: &crate::models::live::LiveSession) -> Result<(), AppError> {
    if session.status == "ended" {
        return Err(AppError::Http {
            status: StatusCode::BAD_REQUEST,
            message: "Live session has ended".to_string(),
        });
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// REST handlers
// ---------------------------------------------------------------------------

/// POST /api/v1/live-sessions — create (manage classroom).
pub async fn create_session(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(req): Json<CreateSessionRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;

    if !live_auth::can_manage_classroom(pool, actor_id, &role, req.classroom_id).await? {
        return Err(AppError::Domain {
            status: StatusCode::FORBIDDEN,
            code: "FORBIDDEN".to_string(),
            message: "Not authorized to create a live session for this classroom".to_string(),
            details: json!({}),
        });
    }

    let janus = janus_client(&state);
    let session = live_session_service::create_session(
        pool,
        &janus,
        None,
        actor_id,
        &req,
        &state.settings.live_media_backend,
        &state.settings.janus_public_ws_url,
    )
    .await?;

    let count = live_participant_service::count_active(pool, session.id).await?;
    Ok((StatusCode::CREATED, Json(session.to_out(count))))
}

/// GET /api/v1/live-sessions?classroom_id=&limit= — list (access classroom).
pub async fn list_sessions(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Query(q): Query<ListSessionsQuery>,
) -> Result<Json<Vec<LiveSessionOut>>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;

    if !live_auth::can_access_classroom(pool, actor_id, &role, q.classroom_id).await? {
        return Err(AppError::Domain {
            status: StatusCode::FORBIDDEN,
            code: "FORBIDDEN".to_string(),
            message: "Not authorized to access this classroom".to_string(),
            details: json!({}),
        });
    }

    let sessions = live_session_service::list_sessions(pool, q.classroom_id, q.limit.unwrap_or(20))
        .await?;
    let mut out = Vec::with_capacity(sessions.len());
    for s in sessions {
        let count = live_participant_service::count_active(pool, s.id).await?;
        out.push(s.to_out(count));
    }
    Ok(Json(out))
}

/// GET /api/v1/live-sessions/:id — detail (access).
pub async fn get_session(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<LiveSessionOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    live_auth::ensure_can_access(pool, actor_id, &role, &session).await?;
    let count = live_participant_service::count_active(pool, session.id).await?;
    Ok(Json(session.to_out(count)))
}

/// POST /api/v1/live-sessions/:id/end — end (manage).
pub async fn end_session(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<LiveSessionOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;

    if !live_auth::can_manage_classroom(pool, actor_id, &role, session.classroom_id).await? {
        return Err(AppError::Domain {
            status: StatusCode::FORBIDDEN,
            code: "FORBIDDEN".to_string(),
            message: "Not authorized to end this session".to_string(),
            details: json!({}),
        });
    }

    let janus = janus_client(&state);
    let ended = live_session_service::end_session(pool, &janus, None, &session, Some(actor_id))
        .await?;
    let count = live_participant_service::count_active(pool, ended.id).await?;
    Ok(Json(ended.to_out(count)))
}

/// POST /api/v1/live-sessions/:id/join — join (access + room-lock).
pub async fn join_session(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<LiveSessionJoinOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    reject_if_ended(&session)?;
    live_auth::ensure_can_join(pool, actor_id, &role, &session).await?;

    let identity = live_participant_service::identity_for_user(actor_id);
    let part_role =
        if live_auth::can_manage_classroom(pool, actor_id, &role, session.classroom_id).await? {
            "host"
        } else {
            "learner"
        };
    let participant =
        live_participant_service::upsert_join(pool, session.id, Some(actor_id), &identity, None, part_role)
            .await?;

    let _ = live_event_service::record(
        pool,
        live_event_service::EventInsert::new(session.id, "participant_joined", "user")
            .with_identity(&identity)
            .with_user_id(actor_id),
    )
    .await;

    let janus = build_credential(&state, pool, &session, &identity, part_role).await?;
    let count = live_participant_service::count_active(pool, session.id).await?;

    Ok(Json(LiveSessionJoinOut {
        session: session.to_out(count),
        participant: LiveParticipantOut::from(participant),
        janus,
    }))
}

/// POST /api/v1/live-sessions/:id/token — issue a join credential (access + lock).
pub async fn issue_credential(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<LiveCredentialOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    reject_if_ended(&session)?;
    live_auth::ensure_can_join(pool, actor_id, &role, &session).await?;

    let identity = live_participant_service::identity_for_user(actor_id);
    let part_role =
        if live_auth::can_manage_classroom(pool, actor_id, &role, session.classroom_id).await? {
            "host"
        } else {
            "learner"
        };
    let cred = build_credential(&state, pool, &session, &identity, part_role).await?;
    Ok(Json(cred))
}

/// Build a join credential + ICE servers + the session's Janus room id.
async fn build_credential(
    state: &AuthState,
    pool: &sqlx::PgPool,
    session: &crate::models::live::LiveSession,
    identity: &str,
    role: &str,
) -> Result<LiveCredentialOut, AppError> {
    let janus_room_id: i64 =
        sqlx::query_scalar("SELECT janus_room_id FROM live_janus_rooms WHERE live_session_id = $1")
            .bind(session.id)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?
            .unwrap_or(0);

    let (token, expires_at) = live_credential_service::issue_join_credential(
        session.id,
        identity,
        role,
        state.settings.live_join_credential_ttl_minutes,
        &state.settings.jwt_secret_key,
    )?;

    let ice_servers = live_credential_service::issue_ice_credentials(
        &state.settings.turn_static_auth_secret,
        &[], // TURN URLs are configured at the edge; empty = host/srflx only in dev
        ICE_TTL_SECONDS,
        identity,
    );

    Ok(LiveCredentialOut {
        janus_ws_url: state.settings.janus_public_ws_url.clone(),
        janus_room_id,
        identity: identity.to_string(),
        credential: token,
        expires_at,
        ice_servers,
    })
}

/// POST /api/v1/live-sessions/:id/leave — leave (access). 204.
pub async fn leave_session(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    live_auth::ensure_can_access(pool, actor_id, &role, &session).await?;

    let identity = live_participant_service::identity_for_user(actor_id);
    let left = live_participant_service::mark_left(pool, session.id, Some(actor_id), Some(&identity))
        .await?;
    if left.is_some() {
        let _ = live_event_service::record(
            pool,
            live_event_service::EventInsert::new(session.id, "participant_left", "user")
                .with_identity(&identity)
                .with_user_id(actor_id),
        )
        .await;
    }
    Ok(StatusCode::NO_CONTENT)
}

/// GET /api/v1/live-sessions/:id/participants — roster (access).
pub async fn list_participants(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<Vec<LiveParticipantOut>>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    live_auth::ensure_can_access(pool, actor_id, &role, &session).await?;

    let rows = sqlx::query_as::<_, crate::models::live::LiveParticipant>(
        "SELECT id, live_session_id, user_id, participant_identity, display_name, role, is_ai, \
                joined_at, left_at, connection_metadata, janus_feed_id, janus_handle_id \
         FROM live_participants WHERE live_session_id = $1 AND left_at IS NULL \
         ORDER BY joined_at ASC",
    )
    .bind(session.id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(Json(rows.into_iter().map(LiveParticipantOut::from).collect()))
}

/// GET /api/v1/live-sessions/:id/events — events feed (access).
pub async fn list_events(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
    Query(q): Query<EventsQuery>,
) -> Result<Json<Vec<LiveEventOut>>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    live_auth::ensure_can_access(pool, actor_id, &role, &session).await?;

    let events = live_event_service::list(pool, session.id, q.limit.unwrap_or(50), q.since).await?;
    Ok(Json(events.into_iter().map(LiveEventOut::from).collect()))
}

/// POST /api/v1/live-sessions/:id/events — append event (access). 201.
pub async fn append_event(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
    Json(req): Json<AppendEventRequest>,
) -> Result<(StatusCode, Json<LiveEventOut>), AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    live_auth::ensure_can_access(pool, actor_id, &role, &session).await?;

    let mut ev = live_event_service::EventInsert::new(
        session.id,
        req.event_type,
        req.event_source.unwrap_or_else(|| "user".to_string()),
    )
    .with_user_id(actor_id);
    if let Some(identity) = req.participant_identity {
        ev = ev.with_identity(identity);
    }
    if let Some(payload) = req.payload {
        ev = ev.with_payload(payload);
    }
    let recorded = live_event_service::record(pool, ev).await?;
    Ok((StatusCode::CREATED, Json(LiveEventOut::from(recorded))))
}

/// PATCH /api/v1/live-sessions/:id/participants/:pid/role — (moderate).
pub async fn update_participant_role(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path((id, pid)): Path<(Uuid, Uuid)>,
    Json(req): Json<UpdateRoleRequest>,
) -> Result<Json<LiveParticipantOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    if !live_auth::can_moderate(pool, actor_id, &role, &session, true).await? {
        return Err(forbidden("Not authorized to moderate this session"));
    }

    // Resolve the target participant's identity from its id.
    let identity: Option<String> = sqlx::query_scalar(
        "SELECT participant_identity FROM live_participants WHERE id = $1 AND live_session_id = $2",
    )
    .bind(pid)
    .bind(session.id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let identity = identity.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "Participant not found".to_string(),
    })?;

    let updated =
        live_participant_service::update_role(pool, session.id, &identity, &req.role).await?;
    Ok(Json(LiveParticipantOut::from(updated)))
}

/// POST /api/v1/live-sessions/:id/host/settings — update settings (manage).
pub async fn update_settings(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
    Json(req): Json<UpdateSettingsRequest>,
) -> Result<Json<LiveSessionOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    if !live_auth::can_manage_classroom(pool, actor_id, &role, session.classroom_id).await? {
        return Err(forbidden("Not authorized to update settings"));
    }
    let updated = live_session_service::update_settings(pool, &session, &req, actor_id).await?;
    let count = live_participant_service::count_active(pool, updated.id).await?;
    Ok(Json(updated.to_out(count)))
}

/// POST /api/v1/live-sessions/:id/host/mute-all — (moderate).
pub async fn mute_all(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
    Json(req): Json<MuteAllRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    if !live_auth::can_moderate(pool, actor_id, &role, &session, true).await? {
        return Err(forbidden("Not authorized to moderate this session"));
    }
    let janus = janus_client(&state);
    let result = live_moderation_service::mute_all(
        pool,
        &janus,
        session.id,
        req.include_cohosts.unwrap_or(false),
        actor_id,
    )
    .await?;
    Ok(Json(result))
}

/// POST /api/v1/live-sessions/:id/host/remove-participant — (moderate).
pub async fn remove_participant(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
    Json(req): Json<RemoveParticipantRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let (actor_id, role) = authenticate_with_role(&headers, &state.settings)?;
    let session = load_session(pool, id).await?;
    if !live_auth::can_moderate(pool, actor_id, &role, &session, true).await? {
        return Err(forbidden("Not authorized to moderate this session"));
    }
    let janus = janus_client(&state);
    let result = live_moderation_service::remove_participant(
        pool,
        &janus,
        session.id,
        &req.participant_identity,
        actor_id,
    )
    .await?;
    Ok(Json(result))
}

/// POST /api/v1/live-sessions/:id/ai-teacher/credential — internal-token gated (Req 10.4).
pub async fn ai_teacher_credential(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Path(id): Path<Uuid>,
) -> Result<Json<LiveCredentialOut>, AppError> {
    let pool = require_pool(&state.pool)?;
    // Validate the internal service token (distinct from user JWTs).
    let provided = headers
        .get("x-live-internal-token")
        .and_then(|h| h.to_str().ok())
        .unwrap_or("");
    if provided.is_empty() || provided != state.settings.live_internal_token {
        return Err(AppError::Unauthorized);
    }
    let session = load_session(pool, id).await?;
    reject_if_ended(&session)?;

    let identity = live_participant_service::ai_teacher_identity(session.id);
    // Ensure the AI-teacher roster row exists (idempotent).
    let _ = live_participant_service::ensure_ai_teacher(pool, session.id, None).await?;
    let cred = build_credential(&state, pool, &session, &identity, "ai_teacher").await?;
    Ok(Json(cred))
}

/// Helper for a 403 domain error.
fn forbidden(msg: &str) -> AppError {
    AppError::Domain {
        status: StatusCode::FORBIDDEN,
        code: "FORBIDDEN".to_string(),
        message: msg.to_string(),
        details: json!({}),
    }
}

// ---------------------------------------------------------------------------
// WebSocket signaling (Req 5.5, 8.1)
// ---------------------------------------------------------------------------

/// GET (WS) /api/v1/live-sessions/:id/signal?credential= — signaling broker.
///
/// Verifies the scoped join credential on the upgrade before accepting the
/// socket. An invalid/expired/wrong-session credential closes the connection
/// with code 4401 and an error signal (Req 5.5). On success the socket is
/// accepted; the per-connection broker loop (Task 14 `janus_signaling`) runs
/// against the configured Janus instance.
pub async fn signal_ws(
    ws: WebSocketUpgrade,
    State(state): State<AuthState>,
    Path(id): Path<Uuid>,
    Query(q): Query<SignalQuery>,
) -> Result<Response, AppError> {
    // Verify the credential BEFORE upgrading (Req 8.1).
    let claims = match live_credential_service::verify_join_credential(
        &q.credential,
        &state.settings.jwt_secret_key,
    ) {
        Ok(c) if live_credential_service::credential_is_for_session(&c, id) => c,
        _ => {
            // Bad credential: accept then immediately close 4401 with an error.
            return Ok(ws.on_upgrade(move |socket| close_unauthorized(socket)));
        }
    };

    let identity = claims.sub.clone();
    Ok(ws.on_upgrade(move |socket| run_signaling(socket, identity)))
}

/// Close a freshly-upgraded socket with code 4401 + an error signal (Req 5.5).
async fn close_unauthorized(mut socket: WebSocket) {
    let err = ServerSignal::Error {
        code: "UNAUTHORIZED".to_string(),
        message: "Invalid or expired join credential".to_string(),
    };
    let _ = socket
        .send(Message::Text(
            crate::services::janus_signaling::server_signal_text(&err),
        ))
        .await;
    let _ = socket
        .send(Message::Close(Some(axum::extract::ws::CloseFrame {
            code: 4401,
            reason: "unauthorized".into(),
        })))
        .await;
}

/// Minimal authenticated signaling loop. Parses client signals and acknowledges
/// them; the full Janus relay (attach/join/configure/trickle) is driven by the
/// `janus_signaling` broker once a Janus WS connection is established for the
/// deployment. Until then, this keeps the socket alive and reports a clear
/// not-ready error for media operations rather than silently dropping frames.
async fn run_signaling(mut socket: WebSocket, identity: String) {
    use crate::models::live::ClientSignal;
    use crate::services::janus_signaling::{parse_client_signal, server_signal_text};

    tracing::info!(%identity, "live signaling connection established");

    while let Some(Ok(msg)) = socket.recv().await {
        let text = match msg {
            Message::Text(t) => t,
            Message::Close(_) => break,
            _ => continue,
        };

        match parse_client_signal(&text) {
            Ok(ClientSignal::Leave) => break,
            Ok(_) => {
                // Media relay requires the Janus WS connection (configured at
                // deploy time). Acknowledge with a structured not-ready error so
                // the client can surface it rather than hang.
                let sig = ServerSignal::Error {
                    code: "MEDIA_BACKEND_NOT_READY".to_string(),
                    message: "Janus media relay is not yet active for this deployment".to_string(),
                };
                if socket.send(Message::Text(server_signal_text(&sig))).await.is_err() {
                    break;
                }
            }
            Err(e) => {
                let sig = ServerSignal::Error {
                    code: "BAD_SIGNAL".to_string(),
                    message: format!("Could not parse signal: {e}"),
                };
                if socket.send(Message::Text(server_signal_text(&sig))).await.is_err() {
                    break;
                }
            }
        }
    }

    tracing::info!(%identity, "live signaling connection closed");
}
