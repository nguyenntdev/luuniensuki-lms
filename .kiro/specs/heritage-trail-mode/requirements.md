# Requirements Document — Heritage Trail Mode

## Introduction

A **trail** is a curated sequence of 5–15 motifs sharing a theme (e.g., "Linh vật Cao Đỉnh", "Hình tượng vua Minh Mạng qua 9 đỉnh"). Trails introduce a narrative arc to learning, with **story checkpoints** for reflection, an **adjustable pace**, **completion certificates**, and **curator-built trails** for teachers.

Research evidence (rephrased): heritage-based games with narrative-driven gameplay and task-driven learning increase meaningfulness compared to non-narrative formats (`researchgate.net/publication/379750538`).

## Glossary

- **Trail**: An ordered set of motifs with an introduction, conclusion, and optional checkpoints. Stored in `trails` table.
- **Trail Step**: One motif's position within a trail. Stored in `trail_steps`.
- **Checkpoint**: A reflection prompt every 2–3 steps. Stored in `trail_checkpoints`.
- **Pace**: A user-selected cadence (`daily`, `2x_week`, `weekly`) determining notification frequency.
- **Trail Certificate**: A signed PDF generated on completion, verifiable via hash.

## Requirements

### Requirement 1: Trail data model and admin CRUD

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL create tables: `trails (id, slug, title_vi, title_en, description_vi, description_en, narrator_intro, narrator_outro, difficulty, estimated_minutes, created_by_user_id, status text 'draft|published|archived', visibility text 'public|classroom|private', created_at, updated_at)`, `trail_steps (id, trail_id, motif_id, position int, created_at)`, `trail_checkpoints (id, trail_id, after_position int, prompt_vi, prompt_en, created_at)`, `user_trail_progress (id, user_id, trail_id, current_position int, started_at, completed_at, last_activity_at)`, `user_trail_checkpoint_responses (id, user_id, checkpoint_id, response_text, created_at)`, `trail_certificates (id, user_id, trail_id, hash text unique, issued_at, pdf_url)`.
2. WHEN an admin calls `POST /api/v1/admin/trails` with full payload, THE Rust_Service SHALL create a draft trail and return HTTP 201.
3. WHEN an admin calls `PATCH /api/v1/admin/trails/:id` with `{"status": "published"}`, THE Rust_Service SHALL publish the trail (validating that it has at least 5 steps and at most 15) and return HTTP 200.
4. IF the validation fails (steps out of range, missing intro/outro), THE Rust_Service SHALL respond with HTTP 422 and `{"error":{"code":"TRAIL_VALIDATION","message":"...","details":{...}}}`.

### Requirement 2: Public trail browse and detail

#### Acceptance Criteria

1. WHEN any authenticated user calls `GET /api/v1/trails`, THE Rust_Service SHALL return all `published` trails with `visibility = 'public'`, ordered by `published_at DESC`, paginated.
2. WHEN a user calls `GET /api/v1/trails/:slug`, THE Rust_Service SHALL return the trail's intro, outro, total step count, total checkpoints, estimated minutes, and the user's `user_trail_progress` if any.
3. THE endpoint SHALL not return the actual motif sequence until the user starts the trail; only step count is exposed before start (preserves narrative reveal).

### Requirement 3: Start, advance, and complete a trail

#### Acceptance Criteria

1. WHEN a user calls `POST /api/v1/trails/:slug/start`, THE Rust_Service SHALL create a `user_trail_progress` row with `current_position = 1` and return the first motif's full content. If a row already exists, return the existing one.
2. WHEN a user calls `POST /api/v1/trails/:slug/step/:position/complete` for the current position, THE Rust_Service SHALL: (a) verify the user has completed the linked motif's lesson via `user_progress.status IN ('learned','mastered')`, (b) advance `current_position += 1`, (c) return the next motif or, if a checkpoint follows, the checkpoint prompt.
3. WHEN a user calls `POST /api/v1/trails/:slug/checkpoint/:idx` with body `{"response": "<text>"}`, THE Rust_Service SHALL persist the response and advance past the checkpoint.
4. WHEN the user completes the final step, THE Rust_Service SHALL set `completed_at = NOW()`, generate a certificate (Requirement 5), and return HTTP 200 with the trail's outro and certificate URL.

### Requirement 4: Pace and reminders

#### Acceptance Criteria

1. THE Rust_Service SHALL allow a user to select a pace via `PUT /api/v1/users/me/trails/:trail_id/pace` with body `{"pace": "daily|2x_week|weekly"}`; valid values stored in `user_trail_progress.pace`.
2. THE Rust_Service SHALL queue notifications via the existing notification system on the schedule defined by `pace`, but only for users with `notification_settings.streak_reminders = true`.
3. The notification dispatch is a background job; this requirement only mandates the data model and queue insertion, not the actual delivery (which is handled by the existing notification worker).

### Requirement 5: Completion certificate

#### Acceptance Criteria

1. WHEN a trail is completed, THE Rust_Service SHALL generate a deterministic SHA-256 hash from `(user_id, trail_id, completed_at_unix)` and persist it in `trail_certificates.hash`.
2. THE Rust_Service SHALL render a PDF via an internal templating helper, store it under `uploads/certificates/<hash>.pdf`, and set `pdf_url`.
3. WHEN any party calls `GET /api/v1/certificates/:hash/verify`, THE Rust_Service SHALL return the certificate's user display_name, trail title, and issued_at without authentication.
4. THE PDF generation SHALL fail gracefully: if the rendering library throws, the certificate row is still inserted with `pdf_url = NULL` and a background retry attempts re-rendering.

### Requirement 6: Curator-built trails (teacher role)

#### Acceptance Criteria

1. WHEN a user with `role = 'teacher'` calls `POST /api/v1/teacher/trails` with full payload AND `visibility = 'classroom'` AND a `classroom_id`, THE Rust_Service SHALL create a draft trail bound to that classroom; the teacher must be the classroom owner.
2. WHEN a teacher calls `POST /api/v1/teacher/trails/:id/submit-for-promotion`, THE Rust_Service SHALL change `status` from `draft` to `pending_review` and notify admins.
3. WHEN an admin calls `POST /api/v1/admin/trails/:id/promote`, THE Rust_Service SHALL change `visibility` from `classroom` to `public` and `status` to `published`, attributing original authorship to the teacher.

### Requirement 7: KPI tracking

#### Acceptance Criteria

1. THE Rust_Service SHALL emit `analytics_events` with event names `trail_started`, `trail_step_completed`, `trail_checkpoint_responded`, `trail_completed`.
2. THE Rust_Service SHALL expose `GET /api/v1/admin/trails/:id/analytics` returning unique starts, average days-to-complete, completion rate, and the top 5 most-skipped checkpoints (ordered by null-response count).
