# Requirements Document

## Introduction

This feature migrates the live virtual-classroom **control plane and signaling**
from the current Python (FastAPI + SQLAlchemy) live service to a native **Rust**
service (Axum/Tokio, sqlx runtime queries), and replaces the **media plane** with
a self-hosted **Janus WebRTC Gateway** running the **VideoRoom** plugin in place of
LiveKit. The Rust service owns WebSocket signaling, Janus room/session lifecycle,
the participant roster, moderation, join-credential/ICE issuance, and the
`live_events` audit log.

The **AI Teacher stays in Python**. The existing `ai_teacher_agent` worker keeps
running unchanged: it joins each room as a participant (`ai-teacher-<sessionid16>`),
consumes/publishes media through Janus, and exchanges lifecycle and event data with
Rust over an internal HTTP boundary. The LLM/STT/TTS routes remain gateway-pinned to
Python.

The migration is **behavior-preserving**: authorization rules, idempotent session
creation, room-lock semantics, the role model (host/cohost/learner/ai_teacher), the
state machine (scheduled → live → ended), and the audit log are mirrored exactly from
the Python implementation. Database changes are **additive only** (new nullable
columns plus one new table via migration `0046`). LiveKit and Janus **coexist behind
the `LIVE_MEDIA_BACKEND` feature flag** during a phased, reversible cutover so that
rollback is a configuration flip rather than a redeploy. The deployment target is a
disk- and memory-constrained production host, so resource usage is explicitly bounded.

These requirements are derived from the approved design document and are numbered so
that the design's `Validates: Requirements X.Y` forward references (1.1, 2.1, 3.1,
4.1, 4.2, 5.1, 6.1, 7.1, 11.4) resolve correctly.

## Glossary

- **Live_Control_Plane**: The native Rust REST surface (`/api/v1/live-sessions/*`)
  that handles create/list/get/end, join/leave, participants, events, settings, and
  moderation requests and maps failures to the `AppError` envelope.
- **Live_Authorization**: The Rust authorization layer that ports the Python access /
  manage / moderate / room-lock-bypass predicates.
- **Session_Service**: The Rust service owning session lifecycle and the
  scheduled→live→ended state machine.
- **Participant_Service**: The Rust service owning the participant roster, identity
  derivation, feed/handle binding, and reconciliation with Janus.
- **Event_Service**: The Rust service that appends and lists the append-only
  `live_events` audit log.
- **Moderation_Service**: The Rust service that performs `mute_all` and
  `remove_participant`, delegating media actions to the Janus_Admin_Client.
- **Credential_Service**: The Rust service that issues scoped join credentials and
  time-limited ICE/TURN credentials.
- **Signaling_Broker**: The per-connection Rust WebSocket task that brokers Janus
  attach/join/offer/answer/trickle between a browser and Janus and records signaling
  events.
- **Janus_Admin_Client**: The single Rust component that talks to the Janus management
  surface (create/destroy/list/kick/moderate), holding the admin and per-room secrets.
- **AI_Hook_Client**: The Rust client that notifies the Python AI worker of session
  lifecycle changes over the internal HTTP boundary.
- **Route_Modes**: The `route-modes.toml`-driven routing layer that selects `gateway`
  (Python) vs `native` (Rust) handling per route, hot-reloaded at runtime.
- **Build_System**: The Rust/Cargo build configuration and dependency manifest,
  including pinned versions recorded in `docs/build-budget.md`.
- **Schema_Migration**: The shared Alembic migration chain (additive migration `0046`).
- **Live_Rate_Limit_Service**: The Rust service enforcing token/join rate-limit buckets
  over the existing rate-limit tables.
- **Deployment_System**: The docker-compose + configuration surface used to deploy,
  flag, and roll back the live stack.
- **Janus VideoRoom**: The `janus.plugin.videoroom` plugin of the Janus WebRTC Gateway
  that forwards media as an SFU; one VideoRoom is created per live session.
- **SFU (Selective Forwarding Unit)**: A media server that forwards each publisher's
  RTP streams to subscribers without transcoding; here, Janus.
- **Signaling broker**: See Signaling_Broker; the Rust intermediary so browsers never
  talk to Janus directly.
- **Join credential**: A short-lived HS256 JWT scoped to one `(session_id, identity)`
  pair, returned to a client to authorize a single signaling session; it never carries
  Janus secrets.
- **Feed id / Handle id**: Janus VideoRoom identifiers — the `feed_id` of a publisher
  and the Janus plugin `handle_id` — persisted as `janus_feed_id` / `janus_handle_id`
  to bind a roster row to its media plane state.
- **Room secret**: The per-room Janus secret (and the admin secret) required for
  privileged VideoRoom operations; held server-side only and never sent to clients.
- **ICE/TURN**: Connectivity-establishment infrastructure; the system issues
  time-limited TURN credentials (coturn REST API HMAC) reusing the existing TURN
  deployment.
- **AI teacher participant**: The Python AI worker's presence in a room under identity
  `ai-teacher-<sessionid16>`, created idempotently with `event_source = "ai_agent"`.
- **Route mode `native` / `gateway`**: `native` routes are handled by Rust; `gateway`
  routes are proxied to the Python service.
- **LIVE_MEDIA_BACKEND**: The feature flag selecting the media backend (`janus` or
  `livekit`) for new sessions during the phased cutover.

## Requirements

### Requirement 1: Authorization Parity

**User Story:** As a platform security owner, I want the Rust live service to make
exactly the same authorization decisions as the Python live service, so that
migrating the control plane does not change who may access, manage, moderate, or
bypass the lock on a live session.

#### Acceptance Criteria

1. WHEN an access, manage, moderate, or room-lock-bypass decision is evaluated for a given user and live session, THE Live_Authorization SHALL return the same allow/deny result that the corresponding Python predicate (`can_access_classroom`, `can_manage_classroom`, `can_user_moderate_live_session`, `_can_user_bypass_room_lock`, `ensure_user_can_join_live_session`) returns for identical inputs.
2. THE Live_Authorization SHALL classify a user as administrative WHERE the user role is in {admin, super_admin}, and as staff WHERE the user role is in {admin, super_admin, teacher}.
3. WHEN evaluating manage permission, THE Live_Authorization SHALL grant management WHERE the user is administrative OR the user is a teacher who owns the classroom.
4. WHEN evaluating access permission, THE Live_Authorization SHALL grant access WHERE the user can manage the classroom OR the user is a member of the classroom.
5. WHEN evaluating moderation permission, THE Live_Authorization SHALL grant moderation WHERE the user can manage the classroom OR the user is an active participant whose role is host (or cohost when cohost moderation is permitted).
6. IF an authorization decision denies a request, THEN THE Live_Control_Plane SHALL return an `AppError` with HTTP status 403 and the matching error code.

### Requirement 2: Idempotent Session Creation

**User Story:** As a classroom teacher, I want creating a live session with a repeated
idempotency key to be safe to retry, so that network retries never produce duplicate
sessions, duplicate Janus rooms, or duplicate audit events.

#### Acceptance Criteria

1. WHEN a create-session request carries a `(classroom_id, idempotency_key)` pair that matches an existing session, THE Session_Service SHALL return the existing session, such that exactly one `live_sessions` row, exactly one Janus VideoRoom, and exactly one `session_created` event exist for that pair.
2. WHEN a create-session request carries a `(classroom_id, idempotency_key)` pair that does not yet exist, THE Session_Service SHALL create one `live_sessions` row with status `scheduled`, provision exactly one Janus VideoRoom, persist one `live_janus_rooms` binding, and record exactly one `session_created` event.
3. IF a user lacking manage permission for the target classroom submits a create-session request, THEN THE Live_Control_Plane SHALL reject the request with HTTP status 403 and create no session.
4. IF Janus room provisioning fails during session creation, THEN THE Session_Service SHALL roll back the `live_sessions` insert and return HTTP status 503.

### Requirement 3: Participant Roster Consistency with Janus

**User Story:** As a host, I want the participant roster to stay consistent with the
feeds actually present in Janus, so that the displayed roster reflects who is really
connected and publishing media.

#### Acceptance Criteria

1. WHEN a non-AI participant successfully publishes media, THE Participant_Service SHALL persist that participant's `janus_feed_id` and `janus_handle_id`, and WHEN `reconcile_with_janus` runs while the broker roster and the Janus participant list agree, THE Participant_Service SHALL produce an empty diff.
2. WHEN `reconcile_with_janus` detects a divergence between the broker roster and the Janus participant list, THE Participant_Service SHALL record a reconciliation event describing the divergence.
3. WHEN the AI worker requests `ensure_ai_teacher` for a session, THE Participant_Service SHALL return a single `ai_teacher` participant with identity `ai-teacher-<sessionid16>`, create it at most once per session, and record it with `event_source = "ai_agent"`.
4. THE Participant_Service SHALL derive a human participant identity as `user-<uuid>` and an AI teacher identity as `ai-teacher-<sessionid16>`.
5. THE Participant_Service SHALL maintain at most one roster row per `(live_session_id, participant_identity)` and at most one per `(live_session_id, user_id)`.
6. WHEN a participant leaves a session, THE Participant_Service SHALL set that participant's `left_at` timestamp.

### Requirement 4: Room-Lock Enforcement and Moderation Invariants

**User Story:** As a host, I want to lock the room and to mute or remove participants,
so that I can control who joins and maintain order without ever affecting hosts or the
AI teacher.

#### Acceptance Criteria

1. WHILE a session is room-locked (`session_metadata.lock_room` is true), WHEN a user who has no host/cohost role history in the session and lacks manage permission attempts to join, THE Live_Authorization SHALL reject the join with error code `ROOM_LOCKED` and HTTP status 403.
2. WHEN a `mute_all` action is processed, THE Moderation_Service SHALL target only participants that are neither host nor AI participants (cohosts targeted only when `include_cohosts` is true), and SHALL report a `processed` plus `failed` count equal to the number of targeted participants.
3. WHILE a session is room-locked, WHEN a user who is a manager or who has host/cohost role history in the session attempts to join, THE Live_Authorization SHALL permit the join.
4. WHEN a moderator removes a participant, THE Moderation_Service SHALL issue a Janus VideoRoom `kick` for that participant's feed and SHALL set that participant's `left_at` timestamp.
5. IF a user without moderation permission submits a `mute_all` or remove-participant request, THEN THE Live_Control_Plane SHALL reject the request with HTTP status 403 and perform no moderation action.

### Requirement 5: Credential Scoping and Secret Isolation

**User Story:** As a security engineer, I want join credentials tightly scoped and Janus
secrets kept server-side, so that a leaked client credential cannot be replayed against
another session and clients never receive admin or room secrets.

#### Acceptance Criteria

1. WHEN a join credential is issued, THE Credential_Service SHALL encode exactly one `(session_id, identity)` pair and an `expires_at`, such that the credential is rejected after `expires_at`, cannot authorize any other session, and contains no Janus admin secret or room secret.
2. WHEN issuing a join credential, THE Credential_Service SHALL also issue time-limited ICE/TURN credentials using the coturn REST API HMAC scheme with the configured TTL.
3. THE Live_Control_Plane SHALL exclude the Janus admin secret and every per-room secret from all client-facing responses.
4. WHILE handling a request to `/internal/ai/*` or the AI-teacher credential endpoint, THE Live_Control_Plane SHALL require a valid `LIVE_INTERNAL_TOKEN` that is distinct from user JWTs.
5. WHEN a signaling WebSocket upgrade presents an invalid or expired credential, THE Signaling_Broker SHALL close the connection with code 4401 and send an error signal.

### Requirement 6: Event-Log Completeness

**User Story:** As a compliance reviewer, I want every session lifecycle transition to
produce exactly the expected audit events, so that the `live_events` log is a complete
and non-duplicated record of what happened.

#### Acceptance Criteria

1. WHEN a lifecycle transition occurs (session creation, join, publish, leave, settings update, `mute_all`, remove participant, or session end), THE Event_Service SHALL append exactly the expected `live_events` row(s) with the correct `event_type` and `event_source`, with no missing rows and no duplicate rows for a single transition.
2. THE Event_Service SHALL store `live_events` as append-only rows ordered by `(live_session_id, created_at)`.
3. WHEN listing events, THE Event_Service SHALL apply the `since` filter and clamp `limit` to the range 1..200.
4. WHEN a participant publishes media and Janus reports `webrtcup`, THE Signaling_Broker SHALL record exactly one `participant_published` event.

### Requirement 7: Session State-Machine Validity

**User Story:** As a host, I want session status to move only forward through
scheduled→live→ended and ending to be safely repeatable, so that the lifecycle is
predictable and end retries are harmless.

#### Acceptance Criteria

1. WHEN a session status transition is requested, THE Session_Service SHALL advance status only along scheduled→live→ended (never backward), SHALL treat a second `end_session` call as a no-op that returns the already-ended session, and SHALL set `ended_at` exactly once.
2. WHEN `end_session` is invoked on a non-ended session, THE Session_Service SHALL set status to `ended`, set `ended_at`, and record exactly one `session_ended` event.
3. IF a join or credential request targets a session whose status is `ended`, THEN THE Live_Control_Plane SHALL reject the request with HTTP status 400 and message "Live session has ended".

### Requirement 8: WebRTC Signaling

**User Story:** As a learner, I want to negotiate WebRTC media through the Rust signaling
broker, so that I can publish and subscribe to audio/video without ever talking to Janus
directly.

#### Acceptance Criteria

1. WHEN a client opens the signaling WebSocket, THE Signaling_Broker SHALL authenticate the upgrade with a valid scoped join credential before creating any Janus session.
2. WHEN a client sends `join_publisher`, THE Signaling_Broker SHALL create a Janus session, attach a VideoRoom publisher handle, bind it to the participant identity, and respond with a `joined` message containing the `feed_id` and the current publishers.
3. WHEN a client sends a `publish` offer, THE Signaling_Broker SHALL forward a `configure` request with the JSEP offer to Janus and return the Janus JSEP answer to the client.
4. WHEN a client or Janus emits an ICE candidate, THE Signaling_Broker SHALL forward the candidate to the other party, and SHALL forward an end-of-candidates marker when trickle completes.
5. WHILE a signaling session is active, THE Signaling_Broker SHALL send a Janus keepalive ping every 25 seconds on the broker↔Janus session.
6. WHEN a client WebSocket closes, THE Signaling_Broker SHALL retain the participant roster row for `LIVE_RECONNECT_GRACE_SECONDS`, reuse that row if the client reconnects within the window, and otherwise mark the participant left and record a `participant_left` event.
7. WHEN a client sends `leave`, THE Signaling_Broker SHALL issue a VideoRoom `leave`, destroy the Janus session, and mark the participant left.

### Requirement 9: Janus Room Lifecycle and Admin Operations

**User Story:** As an operator, I want Janus rooms created and destroyed in step with the
session lifecycle and ending to never block on media-plane failures, so that the control
plane stays available even when the SFU misbehaves.

#### Acceptance Criteria

1. WHEN a session is created, THE Janus_Admin_Client SHALL create exactly one Janus VideoRoom configured with the `publishers`, `bitrate`, and `audiolevel_event` options.
2. WHEN a session ends, THE Janus_Admin_Client SHALL destroy the associated Janus VideoRoom.
3. IF Janus room destroy fails during `end_session`, THEN THE Session_Service SHALL still mark the session ended and record a `room_close_failed` event.
4. WHEN a create or destroy admin request returns a "no such room" or "already exists" condition, THE Janus_Admin_Client SHALL treat the result as success-equivalent (`allow_not_found`) and SHALL retry transient failures with exponential backoff.
5. WHEN a moderation mute or kick is performed, THE Janus_Admin_Client SHALL supply the per-room secret from `live_janus_rooms` and issue the corresponding VideoRoom `moderate` or `kick` request.
6. WHERE the optional Janus webhook is enabled, WHEN an authenticated webhook event arrives, THE Live_Control_Plane SHALL look up the session by `janus_room_id`/`room_name` and record a `webhook.<event>` event.

### Requirement 10: AI Teacher Integration Boundary

**User Story:** As an AI platform engineer, I want a clear Rust→Python boundary for the AI
teacher, so that the Python worker can join rooms and provide tutoring while the LLM, STT,
and TTS endpoints stay in Python.

#### Acceptance Criteria

1. WHEN a session is created with `session_metadata.ai_enabled` true, THE AI_Hook_Client SHALL POST a `session.created` lifecycle hook to the Python AI worker including `live_session_id`, `classroom_id`, `janus_ws_url`, `janus_room_id`, `ai_teacher_identity`, `grade_level`, and `ai_cost_ceiling_usd`.
2. WHEN a session ends or AI is toggled, THE AI_Hook_Client SHALL POST the corresponding `session.ended` or `ai_toggled` lifecycle hook to the Python AI worker.
3. IF an AI lifecycle hook delivery fails, THEN THE AI_Hook_Client SHALL record an `ai_hook_failed` event, continue without blocking the control plane, and retry delivery in the background.
4. WHEN the Python AI worker requests an AI-teacher credential, THE Credential_Service SHALL validate the `LIVE_INTERNAL_TOKEN` and then issue a scoped join credential for identity `ai-teacher-<sessionid16>`.
5. THE Route_Modes SHALL keep the LLM/STT/TTS routes (`/api/v1/live/chat`, `/api/v1/ai-tutor/*`, `.../ai-teacher/stt|tts|reply`) pinned to `gateway` (Python).

### Requirement 11: Native Route Migration and Coexistence

**User Story:** As a release engineer, I want the live control routes to switch from
gateway to native incrementally behind flags, so that I can cut over and roll back without
redeploying.

#### Acceptance Criteria

1. WHEN a live control route's `route-modes.toml` entry changes from `gateway` to `native`, THE Route_Modes SHALL hot-reload the change (via SIGHUP or the 30-second poll) without a process restart.
2. WHERE `LIVE_MEDIA_BACKEND` is set, THE Live_Control_Plane SHALL select the Janus media path WHEN it equals `janus` and the LiveKit media path WHEN it equals `livekit`.
3. WHEN a session is created, THE Session_Service SHALL record the active media backend in `session_metadata` so that in-flight sessions remain on their original backend across a flag flip.
4. WHERE this migration introduces new Rust dependencies, THE Build_System SHALL pin each dependency to an exact version and record its measured footprint in `docs/build-budget.md`.
5. IF a native route or the Janus backend must be rolled back, THEN THE Deployment_System SHALL restore the prior behavior by reverting the `route-modes.toml` entry to `gateway` or setting `LIVE_MEDIA_BACKEND` to `livekit`, without requiring a schema rollback.

### Requirement 12: Deployment and Non-Functional Constraints

**User Story:** As an operator of a disk- and memory-constrained production host, I want the
migration to be additive and bounded in resource usage, so that deploying Janus alongside
LiveKit does not destabilize the host.

#### Acceptance Criteria

1. THE Schema_Migration SHALL apply migration `0046` additively — adding the nullable columns `janus_feed_id` and `janus_handle_id` to `live_participants` and the new `live_janus_rooms` table — without altering or dropping existing columns.
2. THE Live_Control_Plane SHALL persist only durable bindings (feed, handle, and room ids) to Postgres and keep transient SDP/ICE signaling state in memory only.
3. THE Deployment_System SHALL run the `janus-gateway` container with a 512 MiB memory limit and capped container logs.
4. THE Deployment_System SHALL bind the Janus admin port (`:7088`) and the Janus signaling port (`:8188`) to the internal network only, exposing externally only the media UDP range and the reverse-proxied public WS path.
5. WHEN a client exceeds a `token` or `join` rate-limit bucket, THE Live_Rate_Limit_Service SHALL reject the request with error code `RATE_LIMITED` and HTTP status 429.
