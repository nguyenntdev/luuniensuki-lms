# P0-HAB-02: Weekly Quests - Quick Reference

## API Endpoints

### Get Current Week's Quests
```
GET /api/v1/weekly-quests
Authorization: Bearer {token}

Response: WeeklyQuestsResponse
- quests: List of user's quests for this week
- week_start_date: Monday of current week
- week_end_date: Sunday of current week
- total_xp_this_week: XP earned this week
- completed_count: Number completed
- total_count: Total quests this week
```

### Update Quest Progress
```
POST /api/v1/weekly-quests/{quest_id}/progress
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "increment": 1
}

Response: UpdateWeeklyQuestProgressResponse
- quest: Updated quest data
- xp_gained: XP just earned (0 if already complete)
- just_completed: true if just completed this request
- badge_earned: Badge slug if awarded (null otherwise)
```

### Get Quest History
```
GET /api/v1/weekly-quests/history?weeks=4
Authorization: Bearer {token}

Query Params:
- weeks: 1-12 (default: 4)

Response: WeeklyQuestHistoryResponse
- history: List of past quest attempts
- total_completed: Total completed in range
- total_xp_earned: Total XP earned in range
```

## Quest Categories

| Category | Description | Example Quests |
|----------|-------------|----------------|
| `exploration` | Discover new content | Discover 10 motifs, Explore 3 urns |
| `mastery` | Master lessons/motifs | Master 5 motifs, Complete 20 lessons |
| `quiz_champion` | Excel at quizzes | Pass 10 quizzes, 3 perfect scores |
| `streak_master` | Maintain streaks | 7-day streak |

## Database Schema

### weekly_quests
```sql
CREATE TABLE weekly_quests (
  id UUID PRIMARY KEY,
  slug VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  category quest_category NOT NULL,
  week_number INT NULL,        -- 1-52, null for recurring
  year INT NULL,                -- null for recurring
  target_count INT NOT NULL DEFAULT 1,
  xp_reward INT NOT NULL DEFAULT 100,
  badge_slug VARCHAR(100) NULL,
  is_recurring BOOLEAN NOT NULL DEFAULT true,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### user_weekly_quests
```sql
CREATE TABLE user_weekly_quests (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  quest_id UUID NOT NULL REFERENCES weekly_quests(id) ON DELETE CASCADE,
  week_start_date TIMESTAMP NOT NULL,  -- Monday 00:00:00
  current_count INT NOT NULL DEFAULT 0,
  is_completed BOOLEAN NOT NULL DEFAULT false,
  completed_at TIMESTAMPTZ NULL,
  xp_awarded INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, quest_id, week_start_date)
);
```

## Service Functions

```python
from backend.services.weekly_quests import (
    get_week_start_date,
    get_week_end_date,
    ensure_weekly_quests_for_user,
    assign_weekly_quests_to_all_users,
)

# Get current week's Monday
week_start = get_week_start_date()  # datetime(2025, 1, 20, 0, 0, 0)

# Get week's Sunday
week_end = get_week_end_date(week_start)  # datetime(2025, 1, 26, 23, 59, 59)

# Assign quests to a user
user_quests = ensure_weekly_quests_for_user(db, user_id)

# Assign quests to all users (for scheduled job)
count = assign_weekly_quests_to_all_users(db)
```

## Default Weekly Quests

| Slug | Name | Category | Target | XP | Badge |
|------|------|----------|--------|-----|-------|
| `weekly-explorer` | Weekly Explorer | exploration | 10 | 150 | - |
| `weekly-collector` | Weekly Collector | exploration | 3 | 200 | - |
| `weekly-master` | Weekly Master | mastery | 5 | 250 | - |
| `weekly-lesson-champion` | Weekly Lesson Champion | mastery | 20 | 300 | - |
| `weekly-quiz-master` | Weekly Quiz Master | quiz_champion | 10 | 200 | - |
| `weekly-perfect-score` | Weekly Perfect Score | quiz_champion | 3 | 350 | quiz-perfectionist |
| `weekly-dedication` | Weekly Dedication | streak_master | 7 | 400 | dedicated-learner |

## Setup Commands

```bash
# Run migration
docker-compose exec backend alembic upgrade head

# Seed default quests
docker-compose exec backend python -m backend.seed_weekly_quests

# Test endpoint
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/v1/weekly-quests
```

## Integration Examples

### Track Motif Discovery
```python
# When user discovers a motif, update exploration quests
from backend.services.weekly_quests import get_week_start_date

week_start = get_week_start_date()
quests = db.execute(
    select(UserWeeklyQuest)
    .join(WeeklyQuest)
    .where(
        UserWeeklyQuest.user_id == user.id,
        UserWeeklyQuest.week_start_date == week_start,
        WeeklyQuest.category == QuestCategory.exploration,
        UserWeeklyQuest.is_completed == False,
    )
).scalars().all()

for quest in quests:
    # Update via API or directly
    quest.current_count += 1
```

### Track Quiz Completion
```python
# When user passes a quiz
quests = db.execute(
    select(UserWeeklyQuest)
    .join(WeeklyQuest)
    .where(
        UserWeeklyQuest.user_id == user.id,
        UserWeeklyQuest.week_start_date == week_start,
        WeeklyQuest.category == QuestCategory.quiz_champion,
        UserWeeklyQuest.is_completed == False,
    )
).scalars().all()

for quest in quests:
    quest.current_count += 1
```

## File Locations

| File | Purpose |
|------|---------|
| `backend/models.py` | QuestCategory, WeeklyQuest, UserWeeklyQuest models |
| `backend/schemas.py` | API request/response schemas |
| `backend/main.py` | API endpoints (lines ~8300-8600) |
| `backend/services/weekly_quests.py` | Business logic service |
| `migrations/versions/0013_weekly_quests.py` | Database migration |
| `backend/seed_weekly_quests.py` | Seed script |
| `P0_HAB_02_IMPLEMENTATION_SUMMARY.md` | Full documentation |

## Key Features

✅ Auto-assignment of recurring quests
✅ Week boundary handling (Monday-Sunday)
✅ XP rewards on completion
✅ Optional badge awards
✅ Progress tracking and history
✅ Idempotent operations
✅ Unique constraint prevents duplicates
✅ Cascade delete on user/quest deletion

## Testing Quick Checklist

- [ ] Migration runs without errors
- [ ] Seed creates 7 default quests
- [ ] GET /weekly-quests returns current week quests
- [ ] POST /weekly-quests/{id}/progress increments count
- [ ] Quest completion awards XP
- [ ] Quest completion awards badge (if specified)
- [ ] GET /weekly-quests/history returns past weeks
- [ ] New week creates new quest instances
- [ ] Duplicate assignments prevented

