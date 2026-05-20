# Implementation Plan: Heritage Trail Mode

## Overview

This plan implements the Heritage Trail Mode feature: a narrative-driven learning experience with curated motif sequences, story checkpoints, adjustable pacing, completion certificates, teacher-curated trails, and KPI analytics. The implementation spans an Alembic migration (6 tables), Rust model DTOs, a service module, 3 route modules (public, admin, teacher), router wiring, and 14 property-based tests.

## Tasks

- [ ] 1. Database migration — create trail tables
  - [ ] 1.1 Create migration file `migrations/versions/0043_heritage_trails.py` with tables: `trails`, `trail_steps`, `trail_checkpoints`, `user_trail_progress`, `user_trail_checkpoint_responses`, `trail_certificates`, plus all indexes and constraints as specified in the design document.
  - [ ] 1.2 Add downgrade function that drops all 6 tables and indexes in reverse dependency order.
- [ ] 2. Rust model DTOs — `models/trail.rs`
  - [ ] 2.1 Create `backend-rust/src/models/trail.rs` with enums (`TrailStatus`, `TrailVisibility`, `Pace`), request structs (`CreateTrailRequest`, `UpdateTrailRequest`, `TrailStepInput`, `TrailCheckpointInput`, `SetPaceRequest`, `CreateTeacherTrailRequest`, `CheckpointSubmitRequest`), and response structs (`TrailOut`, `TrailDetailOut`, `UserTrailProgressOut`, `TrailStartResponse`, `StepCompleteResponse`, `CheckpointResponse`, `CertificateVerifyOut`, `TrailAnalyticsOut`, `SkippedCheckpointOut`, `TrailListResponse`).
  - [ ] 2.2 Register the module in `backend-rust/src/models/mod.rs` by adding `pub mod trail;`.
- [ ] 3. Trail service — core business logic
  - [ ] 3.1 Create `backend-rust/src/services/trail_service.rs` with admin functions: `create_trail`, `update_trail`, `publish_trail` (validates 5–15 steps + non-empty intro/outro), `promote_trail`, `get_trail_analytics`.
  - [ ] 3.2 Add public functions: `list_trails` (paginated, published+public only, ordered by `published_at DESC`), `get_trail_detail` (returns step_count/checkpoint_count but hides motif sequence if user hasn't started).
  - [ ] 3.3 Add progression functions: `start_trail` (idempotent — creates or returns existing progress row with first motif), `complete_step` (validates motif lesson completion, advances position, returns next motif/checkpoint/completed), `submit_checkpoint` (persists response, advances past checkpoint).
  - [ ] 3.4 Add pace function: `set_pace` (validates enum, computes `next_reminder_at` based on pace: daily→+24h, 2x_week→+84h, weekly→+168h).
  - [ ] 3.5 Add teacher functions: `create_teacher_trail` (validates classroom ownership, sets `visibility = 'classroom'`), `submit_for_promotion` (validates draft status, transitions to `pending_review`).
  - [ ] 3.6 Add certificate functions: `generate_certificate_hash` (deterministic SHA-256 from `user_id:trail_id:completed_at_unix`), `render_certificate_pdf` (best-effort, returns `None` on failure), `verify_certificate` (returns user display_name, trail title, issued_at or 404).
  - [ ] 3.7 Add analytics event emission: emit `trail_started`, `trail_step_completed`, `trail_checkpoint_responded`, `trail_completed` events via the existing analytics event system.
  - [ ] 3.8 Register the module in `backend-rust/src/services/mod.rs` by adding `pub mod trail_service;`.
- [ ] 4. Route module — public & user endpoints (`routes/trails.rs`)
  - [ ] 4.1 Create `backend-rust/src/routes/trails.rs` with handlers: `list_trails` (GET `/api/v1/trails`), `get_trail_detail` (GET `/api/v1/trails/:slug`), `start_trail` (POST `/api/v1/trails/:slug/start`), `complete_step` (POST `/api/v1/trails/:slug/step/:position/complete`), `submit_checkpoint` (POST `/api/v1/trails/:slug/checkpoint/:idx`), `set_pace` (PUT `/api/v1/users/me/trails/:trail_id/pace`), `verify_certificate` (GET `/api/v1/certificates/:hash/verify`). All handlers delegate to `trail_service`. Certificate verify requires no auth; all others require JWT.
  - [ ] 4.2 Register the module in `backend-rust/src/routes/mod.rs` by adding `pub mod trails;`.
- [ ] 5. Route module — admin endpoints (`routes/trail_admin.rs`)
  - [ ] 5.1 Create `backend-rust/src/routes/trail_admin.rs` with handlers: `create_trail` (POST `/api/v1/admin/trails`), `update_trail` (PATCH `/api/v1/admin/trails/:id`), `promote_trail` (POST `/api/v1/admin/trails/:id/promote`), `get_trail_analytics` (GET `/api/v1/admin/trails/:id/analytics`). All require JWT with admin role.
  - [ ] 5.2 Register the module in `backend-rust/src/routes/mod.rs` by adding `pub mod trail_admin;`.
- [ ] 6. Route module — teacher endpoints (`routes/trail_teacher.rs`)
  - [ ] 6.1 Create `backend-rust/src/routes/trail_teacher.rs` with handlers: `create_teacher_trail` (POST `/api/v1/teacher/trails`), `submit_for_promotion` (POST `/api/v1/teacher/trails/:id/submit-for-promotion`). Both require JWT with teacher role.
  - [ ] 6.2 Register the module in `backend-rust/src/routes/mod.rs` by adding `pub mod trail_teacher;`.
- [ ] 7. Wire routes into the application router
  - [ ] 7.1 Add a `trail_routes` group in `build_router` that mounts all public/user endpoints from `routes::trails`, admin endpoints from `routes::trail_admin`, and teacher endpoints from `routes::trail_teacher` with `auth_state`. Merge into the final router.
- [ ] 8. Add dev dependency — `proptest`
  - [ ] 8.1 Add `proptest = "=1.4.0"` to `[dev-dependencies]` in `backend-rust/Cargo.toml`.
- [ ] 9. Property-based tests — trail creation and validation (Properties 1–2)
  - [ ] 9.1 Write property test for Property 1 (trail creation produces a draft): For any valid trail creation payload, `create_trail` returns a trail with `status = 'draft'` and fields matching input. **Validates: Requirements 1.2**
  - [ ] 9.2 Write property test for Property 2 (publish validation enforces step count boundaries): For any trail with N steps, publish succeeds iff 5 ≤ N ≤ 15 AND narrator_intro is non-empty AND narrator_outro is non-empty. **Validates: Requirements 1.3, 1.4**
- [ ] 10. Property-based tests — listing and detail (Properties 3–4)
  - [ ] 10.1 Write property test for Property 3 (trail listing returns only published public trails in order): For any set of trails with mixed statuses/visibilities, list returns only published+public, ordered by `published_at` DESC. **Validates: Requirements 2.1**
  - [ ] 10.2 Write property test for Property 4 (trail detail hides motif sequence before start): For any trail and user who hasn't started, detail contains step_count but no motif IDs/content. **Validates: Requirements 2.2, 2.3**
- [ ] 11. Property-based tests — progression (Properties 5–6)
  - [ ] 11.1 Write property test for Property 5 (start trail is idempotent): For any user and published trail, calling start_trail multiple times returns the same progress row with unchanged position. **Validates: Requirements 3.1**
  - [ ] 11.2 Write property test for Property 6 (trail advancement state machine): For any trail with steps/checkpoints and user at position P, completing step P advances correctly based on whether a checkpoint follows, or trail is complete. **Validates: Requirements 3.2, 3.3, 3.4**
- [ ] 12. Property-based tests — pace and certificates (Properties 7–9)
  - [ ] 12.1 Write property test for Property 7 (pace setting accepts only valid enum values): Setting pace succeeds iff value is one of `{daily, 2x_week, weekly}`. **Validates: Requirements 4.1**
  - [ ] 12.2 Write property test for Property 8 (notification schedule computation): For any pace and reference timestamp, `next_reminder_at` is computed correctly (daily→+24h, 2x_week→+84h, weekly→+168h). **Validates: Requirements 4.2**
  - [ ] 12.3 Write property test for Property 9 (certificate hash determinism): For any `(user_id, trail_id, completed_at_unix)`, `generate_certificate_hash` always produces the same SHA-256 hex string; distinct tuples produce distinct hashes. **Validates: Requirements 5.1**
- [ ] 13. Property-based tests — certificate verification and teacher (Properties 10–12)
  - [ ] 13.1 Write property test for Property 10 (certificate verification returns correct data): For any valid hash in DB, verify returns correct user_display_name, trail_title, issued_at; unknown hash returns 404. **Validates: Requirements 5.3**
  - [ ] 13.2 Write property test for Property 11 (teacher trail creation requires classroom ownership): Creating a classroom trail succeeds iff teacher is classroom owner; non-owners get 403. **Validates: Requirements 6.1**
  - [ ] 13.3 Write property test for Property 12 (submit-for-promotion state transition): `submit_for_promotion` succeeds iff trail status is `'draft'`; on success status becomes `'pending_review'`. **Validates: Requirements 6.2**
- [ ] 14. Property-based tests — promotion and analytics (Properties 13–14)
  - [ ] 14.1 Write property test for Property 13 (admin promote state transition): Promoting a `pending_review` trail sets `status = 'published'`, `visibility = 'public'`, preserves `created_by_user_id`. **Validates: Requirements 6.3**
  - [ ] 14.2 Write property test for Property 14 (analytics aggregation correctness): For any set of progress rows, analytics returns correct unique_starts, completion_rate, average_days_to_complete, and top_skipped_checkpoints. **Validates: Requirements 7.2**

## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": [1, 8]},
    {"tasks": [2]},
    {"tasks": [3]},
    {"tasks": [4, 5, 6]},
    {"tasks": [7]},
    {"tasks": [9, 10, 11, 12, 13, 14]}
  ]
}
```

## Notes

- Migration number is `0043` (next after existing `0042_streak_repair_economy.py`).
- All Cargo.toml dependencies must be pinned to exact versions per project convention.
- Property-based tests use `proptest = "=1.4.0"` with minimum 100 iterations per property.
- The service module follows the existing pattern: thin route handlers delegate to service functions that accept `&PgPool` and return `Result<T, AppError>`.
- Certificate PDF rendering is best-effort; the certificate row is always inserted even if PDF fails.
- The `verify_certificate` endpoint is the only unauthenticated endpoint in this feature.
