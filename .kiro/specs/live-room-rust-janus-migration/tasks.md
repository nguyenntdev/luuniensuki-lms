# Implementation Plan: Live Room — Rust + Janus Migration

## Overview

This plan implements the migration of the live virtual-classroom **control plane and
signaling** from Python (FastAPI) to native **Rust** (Axum/Tokio, sqlx runtime queries),
and replaces the **media plane** with a self-hosted **Janus WebRTC Gateway** (VideoRoom
plugin) running alongside LiveKit behind the `LIVE_MEDIA_BACKEND` feature flag.

The AI Teacher stays in Python; Rust notifies it over an internal HTTP boundary. All
schema changes are additive (migration `0046`). The migration is behavior-preserving:
authorization, idempotent creation, room-lock, the role model, the
scheduled→live→ended state machine, and the `live_events` audit log are mirrored from
the Python implementation.

Tasks are ordered by dependency wave. Test sub-tasks are marked optional (`*`); core
implementation sub-tasks are never optional. Deployment/cutover tasks (15) are gated
on explicit operator confirmation because they touch production secrets and a
disk/memory-constrained host.

## Tasks

### Wave 0 — Foundations (schema, deps, config)

- [x] 1. Migration `0046_live_janus_signaling` (additive)
  - [x] 1.1 Create `migrations/versions/0046_live_janus_signaling.py` with `revision = "0046_live_janus_signaling"`, `down_revision = "0045_fsrs_spaced_repetition"`.
  - [x] 1.2 In `upgrade()`, add nullable columns to `live_participants`: `janus_feed_id BIGINT NULL`, `janus_handle_id BIGINT NULL` (no alter/drop of existing columns).
  - [x] 1.3 In `upgrade()`, create table `live_janus_rooms` (`id` UUID PK, `live_session_id` UUID NOT NULL FK→live_sessions ON DELETE CASCADE, `janus_room_id` BIGINT NOT NULL, `room_secret_ref` VARCHAR(191) NOT NULL, `pin_ref` VARCHAR(191) NULL, `media_state` VARCHAR(20) NOT NULL DEFAULT 'provisioned', `created_at`/`updated_at` TIMESTAMPTZ DEFAULT now(), `UNIQUE(live_session_id)`, `UNIQUE(janus_room_id)`); add index `idx_live_janus_rooms_session`.
  - [x] 1.4 Implement `downgrade()` dropping `live_janus_rooms` and the two columns in reverse order.
  - **Validates:** Requirements 12.1, 3.1

- [x] 2. Add pinned dependencies and record footprint
  - [x] 2.1 Add to `backend-rust/Cargo.toml` `[dependencies]`: `tokio-tungstenite = "=0.23.1"`, `hmac = "=0.12.1"`, `sha1 = "=0.10.6"`; add the `ws` feature to the `axum` dependency.
  - [x] 2.2 Add `proptest = "=1.5.0"` to `[dev-dependencies]` (if not already present).
  - [x] 2.3 Add a row for each new direct dependency to `backend-rust/docs/build-budget.md` with measured peak release-build RSS.
  - [x] 2.4 Run `cargo check` in `backend-rust/` to confirm resolution.
  - **Validates:** Requirements 11.4

- [x] 3. Extend `config::Settings` with live/Janus env
  - [x] 3.1 Add fields (all defaulted so dev starts without them): `janus_ws_url`, `janus_public_ws_url`, `janus_http_url`, `janus_admin_url`, `janus_admin_secret`, `janus_api_secret`, `live_media_backend` (`livekit|janus`, default `livekit`), `live_reconnect_grace_seconds` (default 20), `live_internal_token`, `live_join_credential_ttl_minutes` (default 30), `turn_static_auth_secret`.
  - [x] 3.2 Wire the env reads in `Settings::from_env` and confirm `cargo check`.
  - **Validates:** Requirements 11.2, 5.4

### Wave 1 — Domain models

- [x] 4. `models/live.rs` row + DTO structs
  - [x] 4.1 Add `LiveSession`, `LiveParticipant`, `LiveEvent`, `LiveJanusRoom` (sqlx::FromRow) mirroring the reused tables plus the new columns/table.
  - [x] 4.2 Add response DTOs `LiveSessionOut`, `LiveParticipantOut`, `LiveEventOut`, `LiveCredentialOut`, `LiveSessionJoinOut`, `ModerationActionOut`, `IceServer`, and request DTOs (`CreateSessionRequest`, `ListSessionsQuery`, `EventsQuery`, `AppendEventRequest`, `UpdateRoleRequest`, `UpdateSettingsRequest`, `MuteAllRequest`, `RemoveParticipantRequest`, `SignalQuery`).
  - [x] 4.3 Add signaling enums `ClientSignal` / `ServerSignal` (serde tag="type", snake_case) and `PublisherInfo`/`IceCandidate`.
  - [x] 4.4 Register `pub mod live;` in `backend-rust/src/models/mod.rs`; `cargo check`.
  - **Validates:** Requirements 1.1, 2.1, 5.1, 8.1

### Wave 2 — Services (control plane)

- [x] 5. Live authorization (`services/live_auth.rs`)
  - [x] 5.1 Port predicates: `is_admin`, `is_staff`, `can_manage_classroom`, `can_access_classroom`, `can_moderate`, `can_bypass_room_lock`, `ensure_can_access`, `ensure_can_join` (room-lock → `ROOM_LOCKED` 403), and `session_metadata` accessors (`is_room_locked`, `is_ai_enabled` default true) — exact parity with the Python predicates.
  - [x] 5.2 Register module; `cargo check`.
  - [ ]* 5.3 Property test — Property 1 (authorization parity) and Property 4 (room-lock enforcement).
  - **Validates:** Requirements 1.1–1.6, 4.1, 4.3

- [x] 6. Janus admin client (`services/janus_admin.rs`)
  - [x] 6.1 Define a `JanusAdmin` trait (create_room, destroy_room, list_participants, kick, moderate_mute, room_exists) so it can be faked in tests; implement the reqwest-backed concrete client holding the admin/room secrets.
  - [x] 6.2 Implement Janus VideoRoom request-body construction and response parsing; `allow_not_found` for create/destroy ("no such room"/"already exists" → success), exponential-backoff retry for transient failures.
  - [x] 6.3 Register module; `cargo check`.
  - [ ]* 6.4 Unit tests for request-body construction and `allow_not_found`/retry behavior.
  - **Validates:** Requirements 9.1, 9.2, 9.4, 9.5

- [x] 7. Credential / ICE issuer (`services/live_credential_service.rs`)
  - [x] 7.1 Implement `issue_join_credential` (HS256 JWT scoped to one `(session_id, identity)` + `expires_at`, signed with shared secret, no Janus secret).
  - [x] 7.2 Implement `verify_join_credential` (rejects expired / wrong-session) and `issue_ice_credentials` (coturn REST API HMAC, configured TTL) using `hmac`+`sha1`.
  - [x] 7.3 Register module; `cargo check`.
  - [ ]* 7.4 Property test — Property 5 (credential scoping & secret isolation).
  - **Validates:** Requirements 5.1, 5.2

- [x] 8. Event service (`services/live_event_service.rs`)
  - [x] 8.1 Implement `record(pool, EventInsert)` (append-only) and `list(pool, session_id, limit clamped 1..200, since)`, plus `find_live_session_by_room_name`.
  - [x] 8.2 Register module; `cargo check`.
  - [ ]* 8.3 Property test — Property 6 (event-log completeness; ordering by `(live_session_id, created_at)`).
  - **Validates:** Requirements 6.1, 6.2, 6.3

- [x] 9. Participant service (`services/live_participant_service.rs`)
  - [x] 9.1 Implement `upsert_join`, `mark_left`, `ensure_ai_teacher` (idempotent, `event_source="ai_agent"`), `update_role`, identity builders `identity_for_user` (`user-<uuid>`) and `ai_teacher_identity` (`ai-teacher-<id16>`), feed/handle persistence.
  - [x] 9.2 Implement `reconcile_with_janus` (empty diff when broker & Janus agree; records a reconciliation event on divergence). Enforce the one-row-per-identity / per-user-id invariants.
  - [x] 9.3 Register module; `cargo check`.
  - [ ]* 9.4 Property test — Property 3 (roster consistency vs Janus).
  - **Validates:** Requirements 3.1–3.6

- [x] 10. AI lifecycle hook client (`services/ai_hook_client.rs`)
  - [x] 10.1 Implement `session_created`/`session_ended`/`ai_toggled` POSTs to the Python worker (gated on `ai_enabled`); fire-and-forget with background retry; on failure record `ai_hook_failed` and never block.
  - [x] 10.2 Register module; `cargo check`.
  - **Validates:** Requirements 10.1, 10.2, 10.3

- [x] 11. Session service (`services/live_session_service.rs`)
  - [x] 11.1 Implement `create_session` (idempotent on `(classroom_id, idempotency_key)`; insert row → provision Janus room → persist `live_janus_rooms` → `session_created` event → optional AI hook; rollback insert + 503 on Janus failure; record active `live_media_backend` in metadata).
  - [x] 11.2 Implement `list_sessions`, `get_session`, `update_settings`.
  - [x] 11.3 Implement `end_session` (scheduled→live→ended only; idempotent no-op when already ended; set `ended_at` once; `session_ended` event; destroy Janus room; on destroy failure still end + record `room_close_failed`; AI `session.ended` hook).
  - [x] 11.4 Register module; `cargo check`.
  - [ ]* 11.5 Property tests — Property 2 (idempotent creation) and Property 7 (state-machine validity).
  - **Validates:** Requirements 2.1–2.4, 7.1–7.3, 9.3, 11.3

- [x] 12. Moderation service (`services/live_moderation_service.rs`)
  - [x] 12.1 Implement `mute_all` (target non-host, non-AI; cohosts only when `include_cohosts`; report processed+failed) and `remove_participant` (Janus `kick` + set `left_at`); delegate media ops to `JanusAdmin` with the per-room secret.
  - [x] 12.2 Register module; `cargo check`.
  - [ ]* 12.3 Property test — Property 8 (moderation invariants).
  - **Validates:** Requirements 4.2, 4.4, 4.5

- [x] 13. Live rate-limit service (`services/live_rate_limit_service.rs`)
  - [x] 13.1 Port `check_and_record` for `token`/`join` buckets over `live_rate_limit_logs`; exceeded → `RATE_LIMITED` 429.
  - [x] 13.2 Register module; `cargo check`.
  - **Validates:** Requirements 12.5

### Wave 3 — Signaling broker

- [x] 14. Janus signaling broker (`services/janus_signaling.rs`)
  - [x] 14.1 Implement the per-connection `SignalingSession` over `tokio-tungstenite` to the Janus WS API: create Janus session, attach VideoRoom handle, bind to identity.
  - [x] 14.2 Implement the `join_publisher` → `publish` (configure + JSEP) → `answer` flow, persisting `janus_feed_id`/`janus_handle_id`; record one `participant_published` on `webrtcup`.
  - [x] 14.3 Implement subscriber attach (`subscribe`/`answer`), bidirectional ICE trickle forwarding (incl. end-of-candidates), and 25s Janus keepalive.
  - [x] 14.4 Implement reconnection grace (`LIVE_RECONNECT_GRACE_SECONDS`): reuse roster row within window, else `mark_left` + `participant_left`. Implement `leave`/disconnect cleanup (VideoRoom leave → destroy Janus session → mark left).
  - [x] 14.5 Register module; `cargo check`.
  - **Validates:** Requirements 8.1–8.7, 6.4, 3.1

### Wave 4 — Routes & wiring

- [x] 15. Live REST handlers (`routes/live.rs`)
  - [x] 15.1 Implement REST handlers for the full `/api/v1/live-sessions/*` surface (create, list, get, end, token, join, leave, participants, events list/append, role, settings, mute-all, remove-participant) delegating to services with auth + `AppError` mapping.
  - [x] 15.2 Implement the WS `signal_ws` handler (verify credential on upgrade → run `SignalingSession`; close 4401 on bad credential).
  - [ ] 15.3 Implement `ai-teacher/credential` (requires `LIVE_INTERNAL_TOKEN`) and the optional `POST /api/v1/janus/webhook` (shared secret → `webhook.<event>`).
  - [x] 15.4 Register `pub mod live;` in `routes/mod.rs`; `cargo check`.
  - **Validates:** Requirements 1.6, 5.3, 5.4, 5.5, 7.3, 9.6, 10.4, 10.5

- [x] 16. Router wiring & route modes
  - [x] 16.1 Mount the live routes in `build_router` (`src/main.rs`) with `auth_state`; mount the WS route with the `ws` extractor.
  - [x] 16.2 Keep `/api/v1/live-sessions/*` and `/api/v1/live/*` entries as `gateway` in `route-modes.toml` for now (cutover is task 17.x); update `docs/ai-tutor-routing.md` so the AI-tutor pinning lint scopes to the LLM/STT/TTS routes only, not the control routes.
  - [x] 16.3 Run `cargo build` to verify full compilation.
  - **Validates:** Requirements 11.1, 10.5

### Wave 5 — Integration & contract tests (optional)

- [ ]* 17. Tests against a Janus instance and DTO contracts
  - [ ]* 17.1 Integration test gated on `JANUS_TEST_URL` exercising attach/join/offer/answer/trickle + room destroy with a headless client.
  - [ ]* 17.2 Extend `backend-rust/tests/contract/` to assert native JSON responses match the existing Python live DTOs.
  - **Validates:** Requirements 8.x, parity

### Wave 6 — Deployment & cutover (operator-gated)

- [ ] 18. Janus compose service + config (no traffic)
  - [ ] 18.1 Add the pinned `janus-gateway` service to `docker-compose.prod.yml` (and dev compose) with `memory: 512m`, capped json-file logs, internal-only `:7088`/`:8188`/`:8088`, media UDP range `20000-20100` (non-overlapping with LiveKit), cert/TURN volumes reused.
  - [ ] 18.2 Add `janus/etc` config files (videoroom plugin, admin/api secrets via env).
  - [ ] 18.3 Document required prod env (`JANUS_ADMIN_SECRET`, `JANUS_API_SECRET`, `LIVE_INTERNAL_TOKEN`, `TURN_STATIC_AUTH_SECRET`, `LIVE_MEDIA_BACKEND`) — values supplied by the operator, never committed.
  - **Validates:** Requirements 12.2, 12.3, 12.4

- [ ] 19. Phased cutover (gated, reversible)
  - [ ] 19.1 Phase A — deploy passive (`LIVE_MEDIA_BACKEND=livekit`), run migration `0046`, verify integration tests.
  - [ ] 19.2 Phase B — flip read-only control routes to `native`; validate parity.
  - [ ] 19.3 Phase C — Janus canary on one classroom; flip `join`/`token`/`signal`; monitor RSS/disk/event-log.
  - [ ] 19.4 Phase D — default `janus`; Phase E — decommission LiveKit after a bake period.
  - **Validates:** Requirements 11.2, 11.5, 12.x

## Task Dependency Graph

```json
{
  "waves": [
    ["1", "2", "3"],
    ["4"],
    ["5", "6", "7", "8", "9", "10", "13"],
    ["11", "12"],
    ["14"],
    ["15"],
    ["16"],
    ["17"],
    ["18"],
    ["19"]
  ]
}
```

## Notes

- All new Rust deps are exact-pinned and recorded in `docs/build-budget.md` (Req 11.4).
- Schema changes are additive only; migration `0046` follows `0045` in the chain.
- Property tests cover correctness Properties 1–8 from the design; Janus is faked at
  the `JanusAdmin` trait boundary so they run without a live SFU.
- The AI Teacher stays in Python; LLM/STT/TTS routes remain `gateway`-pinned.
- Tasks 18–19 (Janus container + phased cutover) require operator confirmation and
  production secrets; they are not auto-dispatched.
