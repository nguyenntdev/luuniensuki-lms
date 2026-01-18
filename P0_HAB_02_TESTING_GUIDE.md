# P0-HAB-02: Weekly Quests Testing Guide

## Prerequisites

1. Backend running with database access
2. User account with authentication token
3. Migration applied
4. Quests seeded

## Step-by-Step Testing

### 1. Run Migration

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
docker-compose exec backend alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 0012_daily_missions -> 0013_weekly_quests, Add weekly quests
```

**Verify:**
```sql
-- Check tables exist
SELECT COUNT(*) FROM weekly_quests;
SELECT COUNT(*) FROM user_weekly_quests;
```

### 2. Seed Weekly Quests

```bash
docker-compose exec backend python -m backend.seed_weekly_quests
```

**Expected Output:**
```
🌱 Seeding weekly quests...
✓ Added weekly quest: Weekly Explorer
✓ Added weekly quest: Weekly Collector
✓ Added weekly quest: Weekly Master
✓ Added weekly quest: Weekly Lesson Champion
✓ Added weekly quest: Weekly Quiz Master
✓ Added weekly quest: Weekly Perfect Score
✓ Added weekly quest: Weekly Dedication

✅ Seeded 7 new weekly quests
📊 Total weekly quests: 7
```

**Verify:**
```sql
SELECT slug, name, category, target_count, xp_reward 
FROM weekly_quests 
WHERE is_active = true;
```

### 3. Test GET /api/v1/weekly-quests

```bash
# Get authentication token first
TOKEN="your_jwt_token_here"

# Get current week's quests
curl -X GET http://localhost:8000/api/v1/weekly-quests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

**Expected Response:**
```json
{
  "quests": [
    {
      "id": "uuid",
      "quest": {
        "id": "uuid",
        "slug": "weekly-explorer",
        "name": "Weekly Explorer",
        "description": "Discover 10 new motifs this week",
        "category": "exploration",
        "week_number": null,
        "year": null,
        "target_count": 10,
        "xp_reward": 150,
        "badge_slug": null,
        "is_recurring": true,
        "is_active": true
      },
      "week_start_date": "2025-01-20T00:00:00",
      "current_count": 0,
      "is_completed": false,
      "completed_at": null,
      "xp_awarded": 0,
      "progress_percentage": 0
    }
    // ... 6 more quests
  ],
  "week_start_date": "2025-01-20T00:00:00",
  "week_end_date": "2025-01-26T23:59:59",
  "total_xp_this_week": 0,
  "completed_count": 0,
  "total_count": 7
}
```

**Verify:**
- ✅ All 7 quests returned
- ✅ `week_start_date` is Monday of current week
- ✅ `week_end_date` is Sunday of current week
- ✅ All `current_count` is 0
- ✅ All `is_completed` is false
- ✅ `progress_percentage` is 0

### 4. Test POST /api/v1/weekly-quests/{quest_id}/progress

```bash
# Get a quest ID from previous response
QUEST_ID="uuid-from-weekly-explorer"

# Update progress
curl -X POST http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 3}' | jq
```

**Expected Response:**
```json
{
  "quest": {
    "id": "uuid",
    "quest": {
      "slug": "weekly-explorer",
      // ... quest details
    },
    "current_count": 3,
    "is_completed": false,
    "progress_percentage": 30
  },
  "xp_gained": 0,
  "just_completed": false,
  "badge_earned": null
}
```

**Verify:**
- ✅ `current_count` increased by 3
- ✅ `progress_percentage` is 30 (3/10 * 100)
- ✅ `xp_gained` is 0 (not completed yet)
- ✅ `just_completed` is false

### 5. Test Quest Completion

```bash
# Complete the quest (need 7 more)
curl -X POST http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 7}' | jq
```

**Expected Response:**
```json
{
  "quest": {
    "current_count": 10,
    "is_completed": true,
    "completed_at": "2025-01-20T15:30:00Z",
    "xp_awarded": 150,
    "progress_percentage": 100
  },
  "xp_gained": 150,
  "just_completed": true,
  "badge_earned": null
}
```

**Verify:**
- ✅ `current_count` is 10 (target reached)
- ✅ `is_completed` is true
- ✅ `completed_at` is set
- ✅ `xp_awarded` is 150
- ✅ `xp_gained` is 150
- ✅ `just_completed` is true
- ✅ User's total_xp increased by 150

### 6. Test Quest with Badge

```bash
# Get the "Weekly Perfect Score" quest (has badge)
PERFECT_SCORE_QUEST_ID="uuid-from-weekly-perfect-score"

# Complete it
curl -X POST http://localhost:8000/api/v1/weekly-quests/$PERFECT_SCORE_QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 3}' | jq
```

**Expected Response:**
```json
{
  "quest": {
    "quest": {
      "badge_slug": "quiz-perfectionist"
    },
    "is_completed": true,
    "xp_awarded": 350
  },
  "xp_gained": 350,
  "just_completed": true,
  "badge_earned": "quiz-perfectionist"
}
```

**Verify:**
- ✅ `badge_earned` is "quiz-perfectionist"
- ✅ User has new badge in user_badges table
- ✅ XP is 350

### 7. Test Already Completed Quest

```bash
# Try to update the already completed quest
curl -X POST http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' | jq
```

**Expected Response:**
```json
{
  "quest": {
    "current_count": 10,
    "is_completed": true
  },
  "xp_gained": 0,
  "just_completed": false
}
```

**Verify:**
- ✅ No additional XP awarded
- ✅ `just_completed` is false
- ✅ Count doesn't increase beyond target

### 8. Test GET /api/v1/weekly-quests/history

```bash
# Get quest history
curl -X GET "http://localhost:8000/api/v1/weekly-quests/history?weeks=4" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

**Expected Response:**
```json
{
  "history": [
    {
      "week_start_date": "2025-01-20T00:00:00",
      "quest_name": "Weekly Explorer",
      "quest_category": "exploration",
      "target_count": 10,
      "current_count": 10,
      "is_completed": true,
      "completed_at": "2025-01-20T15:30:00Z",
      "xp_awarded": 150
    },
    {
      "week_start_date": "2025-01-20T00:00:00",
      "quest_name": "Weekly Perfect Score",
      "quest_category": "quiz_champion",
      "target_count": 3,
      "current_count": 3,
      "is_completed": true,
      "completed_at": "2025-01-20T15:35:00Z",
      "xp_awarded": 350
    }
    // ... more entries
  ],
  "total_completed": 2,
  "total_xp_earned": 500
}
```

**Verify:**
- ✅ Completed quests appear in history
- ✅ Incomplete quests also appear
- ✅ Sorted by week_start_date descending (newest first)
- ✅ `total_completed` matches completed count
- ✅ `total_xp_earned` is sum of xp_awarded

### 9. Test Week Boundary

```bash
# Check what happens on Sunday night vs Monday morning
# Manually adjust system time or wait for actual week transition

# On Sunday (last day of week)
curl -X GET http://localhost:8000/api/v1/weekly-quests \
  -H "Authorization: Bearer $TOKEN" | jq '.week_start_date, .week_end_date'

# Should show current week

# On Monday (new week)
curl -X GET http://localhost:8000/api/v1/weekly-quests \
  -H "Authorization: Bearer $TOKEN" | jq '.week_start_date, .week_end_date'

# Should show new week with fresh quests
```

**Verify:**
- ✅ Week dates change correctly
- ✅ New quest instances created for new week
- ✅ Previous week's progress preserved in history
- ✅ All progress counters reset to 0

### 10. Test Auto-Assignment

```bash
# Create a new user or use existing user who hasn't accessed quests yet

# First access triggers auto-assignment
curl -X GET http://localhost:8000/api/v1/weekly-quests \
  -H "Authorization: Bearer $NEW_USER_TOKEN" | jq '.total_count'

# Should return 7 (all active recurring quests)
```

**Verify:**
- ✅ User gets all 7 active quests on first access
- ✅ All quests start at 0 progress
- ✅ Duplicate calls don't create duplicates

### 11. Database Integrity Tests

```sql
-- Check unique constraint
INSERT INTO user_weekly_quests
  (id, user_id, quest_id, week_start_date, current_count)
VALUES
  (gen_random_uuid(), 'user-uuid', 'quest-uuid', '2025-01-20', 0);
-- Should fail with unique constraint violation

-- Check cascade delete (user)
DELETE FROM users WHERE id = 'test-user-uuid';
-- Should delete all associated user_weekly_quests

-- Check cascade delete (quest)
DELETE FROM weekly_quests WHERE id = 'test-quest-uuid';
-- Should delete all associated user_weekly_quests

-- Check week_start_date is always Monday
SELECT DISTINCT EXTRACT(DOW FROM week_start_date) as day_of_week
FROM user_weekly_quests;
-- Should only return 1 (Monday)
```

## Edge Cases

### Test Overflow Protection
```bash
# Try to increment beyond target
curl -X POST http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"increment": 999}' | jq '.quest.current_count'

# Should cap at target_count, not exceed it
```

### Test Invalid Quest ID
```bash
curl -X POST http://localhost:8000/api/v1/weekly-quests/invalid-uuid/progress \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"increment": 1}'

# Should return 404
```

### Test Negative Increment
```bash
curl -X POST http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"increment": -5}'

# Should fail validation (increment must be >= 0)
```

## Performance Tests

### Test Batch Assignment
```python
# Run in Django/Flask shell or script
from backend.services.weekly_quests import assign_weekly_quests_to_all_users

import time
start = time.time()
count = assign_weekly_quests_to_all_users(db)
elapsed = time.time() - start

print(f"Assigned {count} quests to all users in {elapsed:.2f}s")
# Should complete in reasonable time even with many users
```

## Checklist

- [ ] Migration runs without errors
- [ ] Seed creates 7 quests
- [ ] GET /weekly-quests returns quests
- [ ] POST /progress increments count
- [ ] Quest completion awards XP
- [ ] Quest completion awards badge (when specified)
- [ ] Already completed quest doesn't award XP again
- [ ] GET /history returns past weeks
- [ ] Week boundary creates new instances
- [ ] Auto-assignment works on first access
- [ ] Unique constraint prevents duplicates
- [ ] Cascade deletes work
- [ ] Overflow protection works
- [ ] Invalid quest returns 404
- [ ] Negative increment rejected
- [ ] Progress percentage calculated correctly
- [ ] Week dates are correct (Monday-Sunday)


