# Requirements Document — Streak Repair Economy

## Introduction

This feature extends the existing streak system in Luuniensuki LMS with five new mechanics designed to reduce churn and increase 30-day retention: **Streak Repair**, **Streak Insurance** (data model only), **Big Red Button** (server outage protection), **Friend Streak**, and **Streak Comeback**. Existing **Streak Freeze** behavior is preserved unchanged.

The feature builds on existing infrastructure in the `users` table (`current_streak`, `longest_streak`, `streak_freezes`, `last_active_at`) and the `user_hearts` table. All new functionality lands as additive migrations — no breaking schema changes.

Research evidence (rephrased for compliance):

- Duolingo's "Big Red Button" pattern reduced streak loss during server outages and is documented in `blog.duolingo.com/protecting-streaks-from-site-issues/`.
- StriveCloud 2025 reports Duolingo's gamification stack (streaks + leaderboards + repair) drove +36% YoY DAU.
- Friend streaks have been correlated with higher 30-day retention in mobile learning apps.

The migration is observable: every state change goes through audited events in `streak_repair_events` or `streak_protection_events`, and KPI dashboards consume these tables.

## Glossary

- **User**: An authenticated account with `users.role IN ('learner','teacher','admin')`.
- **Streak**: The count `users.current_streak` representing consecutive days the user completed at least one learning activity.
- **Lost Streak**: A streak that was reset to 0 because the user did not have a qualifying activity for at least 24 hours since `last_active_at`.
- **Streak Freeze**: An existing mechanic that consumes `users.streak_freezes` to skip a missed day; out of scope to modify.
- **Streak Repair**: A new mechanic that restores a `Lost Streak` to its prior value when invoked within 48 hours of the loss, costing either 50 hearts or 200 XP.
- **Big Red Button (BRB)**: An admin-only operation that auto-freezes all active streaks during a confirmed server incident; records a `streak_protection_event`.
- **Friend Streak**: A counter between two users who mutually follow each other and both completed at least one learning activity in the same UTC day.
- **Phoenix Badge**: A badge awarded when a user returns after losing a streak of 30 or more days and completes activities for 3 consecutive days.
- **Comeback Bonus**: A 2x XP multiplier granted for 7 calendar days after a Phoenix Badge is awarded.
- **Streak Insurance**: A premium tier (data model only in this spec) that grants unlimited freezes + 3 repairs/month + automatic BRB protection.
- **Active Day (UTC)**: A 24-hour UTC day during which the user has at least one record in any of: `user_progress.lesson_viewed_at`, `user_progress.quiz_attempts > 0` increment, or `user_streaks_activity` (existing streak rollover logic).
- **Repair Window**: The 48-hour period starting at the moment a streak was lost.
- **Calendar Month**: A month boundary in UTC, used for the per-month repair limit.

## Requirements

### Requirement 1: Streak Repair endpoint

**User Story:** As a User who just lost a long streak, I want to spend hearts or XP to restore it within a short grace window so that one bad day does not erase my hard work.

#### Acceptance Criteria

1. WHEN a User calls `POST /api/v1/users/me/streak/repair` with body `{"payment": "hearts"}` AND the User has a `Lost Streak` whose loss occurred within the last 48 hours AND the User has at least 50 hearts AND the User has not used a repair in the current Calendar Month, THE Rust_Service SHALL atomically: (a) deduct 50 hearts, (b) restore `users.current_streak` to the value it had immediately before the loss, (c) update `users.last_active_at` to NOW(), (d) insert one row into `streak_repair_events`, (e) return HTTP 200 with `{"current_streak": <restored>, "payment": "hearts", "repaired_at": "<ISO>"}`.
2. WHEN a User calls the same endpoint with `{"payment": "xp"}` AND the User has at least 200 total XP AND all other conditions of AC1 hold, THE Rust_Service SHALL atomically: (a) deduct 200 XP from `users.total_xp`, (b) restore the streak as in AC1, (c) insert the event row, (d) return HTTP 200 with `payment` field set to `"xp"`.
3. IF the User's last lost streak occurred more than 48 hours ago, THEN THE Rust_Service SHALL respond with HTTP 410 Gone and a JSON body `{"error":{"code":"REPAIR_WINDOW_EXPIRED","message":"Streak can only be repaired within 48 hours of loss","details":{}}}`.
4. IF the User has already used a repair in the current Calendar Month (UTC), THEN THE Rust_Service SHALL respond with HTTP 429 Too Many Requests and a JSON body `{"error":{"code":"REPAIR_LIMIT_REACHED","message":"Streak repair already used this month","details":{"reset_at":"<ISO of next month start>"}}}`.
5. IF the User selected `hearts` payment but has fewer than 50 hearts, THEN THE Rust_Service SHALL respond with HTTP 402 Payment Required and a JSON body `{"error":{"code":"INSUFFICIENT_HEARTS","message":"Need 50 hearts to repair","details":{"current":<n>,"required":50}}}`.
6. IF the User selected `xp` payment but has fewer than 200 XP, THEN THE Rust_Service SHALL respond with HTTP 402 Payment Required and a JSON body `{"error":{"code":"INSUFFICIENT_XP","message":"Need 200 XP to repair","details":{"current":<n>,"required":200}}}`.
7. WHEN a User calls `GET /api/v1/users/me/streak/repair-options`, THE Rust_Service SHALL respond with HTTP 200 and a JSON body containing `repair_available` (boolean), `lost_at` (nullable ISO timestamp), `expires_at` (nullable ISO timestamp 48h after lost_at), `monthly_repairs_used` (integer), `monthly_repairs_limit` (integer fixed at 1), `hearts_required` (integer fixed at 50), `xp_required` (integer fixed at 200), `payment_options_available` (array containing only the payment methods the User can currently afford).
8. THE repair operation SHALL be idempotent under client retry by accepting an optional `Idempotency-Key` header; two requests with the same key within 24 hours SHALL produce identical responses without performing the deduction twice.

### Requirement 2: Streak Repair audit and admin override

**User Story:** As an Admin, I want every repair logged with cost paid, prior streak value, and time of repair so that abuse and bugs can be investigated.

#### Acceptance Criteria

1. THE Rust_Service SHALL persist every successful repair as a row in `streak_repair_events` with columns `id (uuid PK)`, `user_id (uuid)`, `payment_method (text 'hearts'|'xp')`, `payment_amount (int)`, `streak_before_loss (int)`, `streak_restored_to (int)`, `lost_at (timestamptz)`, `repaired_at (timestamptz default NOW())`, `idempotency_key (text nullable)`, `created_at (timestamptz default NOW())`.
2. THE Rust_Service SHALL expose `GET /api/v1/admin/streak-repair-events` that requires `role = 'admin'`, accepts query params `user_id`, `from`, `to`, `page`, `per_page`, and returns the events filtered and paginated.
3. WHEN an Admin calls `POST /api/v1/admin/users/:user_id/streak/grant-repair` with body `{"reason": "<string>"}`, THE Rust_Service SHALL bypass the monthly limit and the 48-hour window, restore the user's prior streak, insert an event with `payment_method = 'admin_grant'` and the reason in a `notes` column, and return HTTP 200.
4. THE admin grant operation SHALL fail with HTTP 404 if the user has no recorded `Lost Streak` (the system has no value to restore to).

### Requirement 3: Big Red Button (BRB) — server outage protection

**User Story:** As an Operator dealing with a confirmed incident, I want one click to protect every user's streak from being lost during downtime so that we do not lose user trust during outages.

#### Acceptance Criteria

1. WHEN an Admin calls `POST /api/v1/admin/streak/big-red-button` with body `{"reason":"<string>","duration_minutes":<int>,"effective_from":"<ISO>"}` AND the Admin's role is `admin`, THE Rust_Service SHALL: (a) for every User whose `current_streak > 0` and `last_active_at` falls within the affected window, increment `users.streak_freezes` by 1 marked as `protected_freeze`, (b) insert one row into `streak_protection_events` per affected User, (c) return HTTP 200 with `{"affected_users": <count>, "event_id": "<uuid>"}`.
2. THE `streak_protection_events` table SHALL have columns `id`, `user_id`, `event_id (groups all rows from one BRB invocation)`, `reason (text)`, `effective_from (timestamptz)`, `effective_to (timestamptz)`, `applied_at (timestamptz)`, `created_at`.
3. WHEN an Admin calls `GET /api/v1/admin/streak/big-red-button/events`, THE Rust_Service SHALL return paginated list of past BRB invocations with affected user counts.
4. THE BRB operation SHALL be rate-limited to at most 5 invocations per 24 hours per admin user; the 6th invocation responds with HTTP 429 and `{"error":{"code":"BRB_RATE_LIMIT","message":"Big Red Button has been pressed 5 times in the last 24 hours; further presses require database-level approval","details":{}}}`.
5. WHEN streak rollover logic runs (existing nightly job or per-request check), THE Rust_Service SHALL treat `protected_freeze` units as unconsumed regular freezes, consuming them first before any normal freeze; protected freezes SHALL NOT count against the user's normal `streak_freezes` accumulation cap.
6. THE BRB operation SHALL be auditable: every invocation SHALL produce exactly one log line at `info` level with fields `actor_user_id`, `reason`, `duration_minutes`, `affected_users`, `event_id`.

### Requirement 4: Friend Streak

**User Story:** As a User who follows friends in the app, I want a shared streak counter that grows when both of us are active so that my friends and I motivate each other.

#### Acceptance Criteria

1. THE Rust_Service SHALL persist friend streaks in a `friend_streaks` table with columns `id (uuid PK)`, `user_a_id (uuid)`, `user_b_id (uuid)`, `current_count (int)`, `longest_count (int)`, `last_increment_date (date)`, `created_at`, `updated_at`. The pair `(user_a_id, user_b_id)` SHALL be canonical with `user_a_id < user_b_id` lexicographically and have a unique constraint.
2. WHEN both User X and User Y have `last_active_at` set within the same UTC date AND there is a mutual follow row in `user_friendships` (existing table) where both directions are accepted, THE Rust_Service SHALL atomically increment the `friend_streaks.current_count` for the canonical pair and update `last_increment_date` to today; the increment SHALL happen at most once per UTC day per pair.
3. WHEN any UTC day passes without both users active, THE Rust_Service SHALL reset `current_count` to 0 on the next streak-rollover run and SHALL NOT decrement `longest_count`.
4. WHEN a User calls `GET /api/v1/users/me/friend-streaks`, THE Rust_Service SHALL return all friend streaks for that user with the friend's display_name, avatar_url, current_count, longest_count, and `is_alive` (boolean: `last_increment_date == today_utc`).
5. WHEN a User calls `GET /api/v1/users/:other_id/friend-streak`, THE Rust_Service SHALL return the friend streak for the canonical pair if one exists and the two users have a mutual-follow relationship; otherwise HTTP 404.
6. THE friend streak increment SHALL fire from a single nightly job at 00:05 UTC AND from a synchronous check whenever a User completes a learning activity (debounced per pair to fire at most once per day).

### Requirement 5: Streak Comeback and Phoenix Badge

**User Story:** As a User who has been away for a long time, I want a clear path back into the app with recognition and a temporary boost so that my return feels rewarded rather than punished.

#### Acceptance Criteria

1. THE Rust_Service SHALL maintain a `user_streak_history` table with columns `id`, `user_id`, `streak_value (int)`, `streak_started_at (timestamptz)`, `streak_ended_at (timestamptz)`, `created_at`. A new row SHALL be inserted whenever a User's `current_streak` is reset from a value `>= 1` to `0`.
2. WHEN a User has at least one `user_streak_history` row with `streak_value >= 30` AND the User completes learning activities on 3 consecutive UTC days AND the User has not already been awarded the Phoenix badge for the current comeback, THE Rust_Service SHALL: (a) award the existing Phoenix badge (`badges` table row with slug `phoenix`), (b) insert a row into `user_comeback_bonuses` with `multiplier = 2.0`, `started_at = NOW()`, `expires_at = NOW() + 7 days`, (c) return the badge in the next `/api/v1/users/me/badges` response.
3. WHILE a User has an active row in `user_comeback_bonuses` (where `expires_at > NOW()`), THE Rust_Service SHALL multiply XP earned from any source by the bonus's `multiplier`; the multiplied XP SHALL be persisted as the actual XP delta in `users.total_xp`.
4. WHEN a User calls `GET /api/v1/users/me/streak/comeback-status`, THE Rust_Service SHALL return `{"phoenix_eligible": <bool>, "consecutive_days_active": <int>, "days_required": 3, "active_bonus": <object or null>}` where `active_bonus` includes `multiplier`, `started_at`, `expires_at` if a row exists.
5. THE Phoenix badge SHALL be awardable at most once per `user_streak_history` row to prevent farming the bonus by repeatedly losing and rebuilding short streaks.

### Requirement 6: Streak Insurance data model (no payment integration)

**User Story:** As a Product owner, I want the data model for a future paid Streak Insurance tier ready so that when payment integration lands the feature can ship without schema migration in the hot path.

#### Acceptance Criteria

1. THE Rust_Service maintainer SHALL create a `streak_insurance_subscriptions` table with columns `id`, `user_id`, `status (text 'active'|'cancelled'|'expired'|'pending')`, `started_at (timestamptz)`, `expires_at (timestamptz)`, `provider (text)`, `provider_subscription_id (text nullable)`, `created_at`, `updated_at`. The table SHALL have a unique constraint on `(user_id)` where `status = 'active'`.
2. WHEN a User has an `active` row, THE Rust_Service SHALL: (a) treat them as having unlimited monthly freezes, (b) allow up to 3 repairs per Calendar Month instead of 1, (c) automatically apply BRB protection without requiring an admin event row (deferred — placeholder column `auto_brb_enabled` boolean default true).
3. THE Rust_Service SHALL expose `GET /api/v1/users/me/streak-insurance` returning the User's current subscription record or `null`.
4. THE Rust_Service SHALL NOT expose any endpoint that creates, charges, or activates a subscription in this spec; payment integration is an explicitly deferred feature.
5. WHEN an Admin calls `POST /api/v1/admin/users/:user_id/streak-insurance/grant` with body `{"duration_days":<int>,"reason":"<string>"}`, THE Rust_Service SHALL insert an `active` row, set `expires_at = NOW() + duration_days`, and return HTTP 201; this admin grant path is the only mechanism to create rows in this spec.

### Requirement 7: Streak loss detection and history capture

**User Story:** As the system, I need a reliable way to detect when a streak is lost so that all downstream features (repair, comeback, history) work correctly.

#### Acceptance Criteria

1. THE Rust_Service SHALL run a streak-rollover check whenever any User's request reaches the `request_id_and_logging` middleware AND the User's `last_active_at` is more than 24 hours older than the current UTC date boundary; the check SHALL also run from a nightly job at 00:10 UTC for users who did not make a request that day.
2. WHEN the rollover check determines that User U has not had an Active Day in the previous UTC date AND `users.streak_freezes > 0`, THE Rust_Service SHALL consume one freeze (decrement `streak_freezes`), preserve `current_streak`, and NOT insert into `user_streak_history`.
3. WHEN the rollover check determines that User U has not had an Active Day in the previous UTC date AND `users.streak_freezes = 0` AND `users.current_streak > 0`, THE Rust_Service SHALL: (a) snapshot the prior streak into `user_streak_history`, (b) reset `users.current_streak = 0`, (c) NOT touch `users.longest_streak`.
4. THE rollover check SHALL hold a per-user advisory lock (using `pg_advisory_xact_lock` keyed on `user_id`) for the duration of the streak update to prevent two concurrent requests from double-incrementing or double-resetting the streak.

### Requirement 8: KPI tracking and observability

**User Story:** As an analyst, I want every streak-economy event recorded with a stable schema so that A/B tests can compare cohorts.

#### Acceptance Criteria

1. THE Rust_Service SHALL emit one structured log line per repair, BRB invocation, friend-streak increment, and Phoenix badge award; each line SHALL have a `feature` field set to the feature name (e.g., `streak_repair`, `brb`, `friend_streak_increment`, `phoenix_award`).
2. THE Rust_Service SHALL increment Prometheus counters: `streak_repair_total{payment="hearts"|"xp"|"admin_grant"}`, `streak_brb_invocations_total`, `friend_streak_increments_total`, `phoenix_badges_awarded_total`.
3. WHEN an Admin calls `GET /api/v1/admin/streak-economy/stats`, THE Rust_Service SHALL return summary counts for the last 7 days, 30 days, and all-time across all four KPIs.
