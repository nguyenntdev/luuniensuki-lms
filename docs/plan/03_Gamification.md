# 03_Gamification.md (Badges • Streak • Leaderboard)

## Goal

Make progression feel meaningful beyond “unlock once” by adding:

- **Badges/Achievements** (collectible goals)
- **Daily streak** (retention loop)
- **Leaderboard** (social proof / competition)

## Current State

- XP and rank exist (based on `User.total_xp`).
- DB models exist:
  - `Badge`, `UserBadge`
  - `User` has `current_streak`, `longest_streak`, `streak_freezes`, `last_active_at`
- No APIs for badges/streak/leaderboard.
- No badge seed data.

## Design Notes (Keep It Simple First)

1. Start with **server-authoritative** awarding (no client-side awarding).
2. Evaluate badge unlocks on a few key events:
   - motif discovered
   - lesson completed
   - quiz passed / mastery
   - daily activity update
3. Store badge criteria in JSON (already in model) and implement a small “rule engine”.

---

## A) Badge System

### Badge Criteria Schema (Proposed)

In `Badge.unlock_criteria` JSON, use:

```json
{
  "type": "motif_discovered_count",
  "count": 10,
  "category": "thao_moc"
}
```

Supported `type` values for MVP:

- `first_discovery`
- `first_mastery`
- `motif_discovered_count` (optionally filtered by `category` or `urn_slug`)
- `motif_mastered_count` (optional filters)
- `urn_complete` (all motifs in urn discovered/mastered)
- `streak_reached` (`days`)

### Badge Seed Set (MVP)

Create ~10 badges:

- “Tân Thủ Khai Bút” (first discovery)
- “Đệ Nhất Tàng Thư” (10 discoveries)
- “Ngự Uyển Ký Sự” (quest completion for one category)
- “Sử Quan Nhập Môn” (first mastery)
- “Thất Nhật Hành Trình” (7-day streak)
- … (expand later)

### Badge Awarding Rules

- Award within the same DB transaction as the event (when possible).
- Enforce uniqueness via `uq_user_badges_user_badge` (already exists).
- If a badge has `xp_bonus`, add to `User.total_xp` once when earned.

### Badge APIs

- **BE-BADGE-01**: `GET /api/v1/users/me/badges`
  - Returns earned badges + progress towards next badges (optional).

### Tasks

- [ ] **BE-BADGE-00**: Define `unlock_criteria` schema + validator (service-level)
- [ ] **BE-BADGE-01**: Implement `GET /api/v1/users/me/badges`
- [ ] **BE-BADGE-02**: Add “badge evaluation” service + integrate into:
  - discovery unlock
  - lesson completion
  - quiz mastery
- [ ] **DATA-BADGE-01**: Seed initial badge set (JSON file + seed script support)
- [ ] **FE-BADGE-01**: Show badges in dashboard (`UserProfile`)

---

## B) Streak System

### Streak Update Event

Define a single helper:

`touch_user_activity(user, now)` called on:
- unlock discovery
- complete lesson
- quiz submit

### Streak Algorithm (MVP)

Use a configured timezone (default: `Asia/Ho_Chi_Minh`) and compare local **calendar day**:

- If last_active_at is `None` → set `current_streak=1`
- If same day → no change
- If next day → `current_streak += 1`, update `longest_streak`
- If gap > 1 day:
  - if `streak_freezes > 0`: consume 1 freeze and treat as next day (optional MVP+)
  - else reset `current_streak=1`

### Streak APIs

- **BE-STREAK-01**: `GET /api/v1/users/me/streak`
  - `{ current, longest, freezes, last_active_at, next_reset_at }`

### Tasks

- [ ] **BE-STREAK-00**: Implement `touch_user_activity` + unit tests
- [ ] **BE-STREAK-01**: Implement `GET /api/v1/users/me/streak`
- [ ] **FE-STREAK-01**: Dashboard streak widget

---

## C) Leaderboard

### Leaderboard Query (MVP)

- Rank by `User.total_xp DESC`, tie-break by `created_at ASC`.
- Return top `limit` (default 50).
- If authenticated, compute `me_rank` with a window function (or a separate query).

### Leaderboard APIs

- **BE-LB-01**: `GET /api/v1/leaderboard?limit=50`
  - Response: `{ top: [...], me: { rank, user } | null }`

### Caching (Later)

- Add Redis caching for leaderboard results (60–120s TTL).
- Cache key includes `limit`.

### Tasks

- [ ] **BE-LB-01**: Implement leaderboard endpoint (no cache)
- [ ] **BE-LB-02**: Add `me_rank` calculation (tested)
- [ ] **FE-LB-01**: `/leaderboard` page
- [ ] **OPS-LB-01**: Optional Redis in prod compose (phase 2)

---

## Definition of Done (Gamification MVP)

- User can view:
  - streak status
  - badges earned
  - leaderboard
- Badge awarding happens automatically on discovery/lesson/quiz events.
- No duplicate badge XP / no duplicate badge rows.

