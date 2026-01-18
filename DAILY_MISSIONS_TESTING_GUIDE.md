# Daily Missions Testing Guide

## Prerequisites

1. Database migration applied:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. Daily mission templates seeded:
   ```bash
   cd backend
   python3 seed_daily_missions.py
   ```

3. Test user account created and authenticated

## Test Cases

### 1. GET /api/v1/daily-missions - Get Today's Missions

#### Test 1.1: First Time User
**Expected**: Creates missions for user automatically

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/daily-missions
```

**Expected Response**:
```json
{
  "missions": [
    {
      "id": "...",
      "mission": {
        "id": "...",
        "slug": "complete-1-lesson",
        "name": "Học 1 Bài",
        "description": "Hoàn thành 1 bài học hôm nay",
        "mission_type": "lesson",
        "target_count": 1,
        "xp_reward": 50,
        "is_active": true
      },
      "mission_date": "2025-01-20T00:00:00",
      "current_count": 0,
      "is_completed": false,
      "completed_at": null,
      "xp_awarded": 0,
      "progress_percentage": 0
    },
    ...
  ],
  "total_xp_today": 0,
  "completed_count": 0,
  "total_count": 4
}
```

#### Test 1.2: Existing User with Progress
**Expected**: Returns current progress

```bash
# After completing a mission
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/daily-missions
```

**Expected**: 
- `progress_percentage` > 0 for missions with progress
- `is_completed: true` for completed missions
- `total_xp_today` > 0 if missions completed

### 2. POST /api/v1/daily-missions/{mission_id}/progress - Update Progress

#### Test 2.1: Increment Progress
**Expected**: Updates current_count

```bash
# Get mission ID from GET endpoint
MISSION_ID="your-mission-id"

curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  http://localhost:8000/api/v1/daily-missions/$MISSION_ID/progress
```

**Expected Response**:
```json
{
  "mission": {
    ...
    "current_count": 1,
    "is_completed": true,
    "xp_awarded": 50,
    "progress_percentage": 100
  },
  "xp_gained": 50,
  "just_completed": true
}
```

#### Test 2.2: Increment Beyond Target
**Expected**: Caps at target_count

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 999}' \
  http://localhost:8000/api/v1/daily-missions/$MISSION_ID/progress
```

**Expected**: 
- `current_count` equals `target_count` (not 999)
- `progress_percentage: 100`

#### Test 2.3: Update Already Completed Mission
**Expected**: No changes, xp_gained = 0

```bash
# Send again to already completed mission
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  http://localhost:8000/api/v1/daily-missions/$MISSION_ID/progress
```

**Expected**:
- `just_completed: false`
- `xp_gained: 0`
- State unchanged

#### Test 2.4: Invalid Mission ID
**Expected**: 404 error

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  http://localhost:8000/api/v1/daily-missions/00000000-0000-0000-0000-000000000000/progress
```

**Expected**: 404 "Mission not found for today"

### 3. GET /api/v1/daily-missions/history - Get History

#### Test 3.1: Default (30 days)
**Expected**: Returns last 30 days

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/daily-missions/history
```

**Expected Response**:
```json
{
  "history": [
    {
      "mission_date": "2025-01-20T00:00:00",
      "mission_name": "Học 1 Bài",
      "mission_type": "lesson",
      "target_count": 1,
      "current_count": 1,
      "is_completed": true,
      "completed_at": "2025-01-20T10:30:00Z",
      "xp_awarded": 50
    },
    ...
  ],
  "total_completed": 4,
  "total_xp_earned": 250,
  "current_streak": 1
}
```

#### Test 3.2: Custom Date Range
**Expected**: Returns specified days

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/daily-missions/history?days=7"
```

**Expected**: History for last 7 days only

#### Test 3.3: Streak Calculation
**Setup**: Complete all missions for 3 consecutive days

**Expected**: `current_streak: 3`

### 4. Integration Tests

#### Test 4.1: Complete Mission Flow
1. Get today's missions
2. Complete a lesson (via existing lesson endpoint)
3. Update mission progress
4. Verify XP awarded
5. Check history

#### Test 4.2: User XP Update
Verify user's `total_xp` increases when mission completes:

```bash
# 1. Get user XP before
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/auth/me

# 2. Complete a mission
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  http://localhost:8000/api/v1/daily-missions/$MISSION_ID/progress

# 3. Get user XP after
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/auth/me

# Verify: total_xp increased by mission.xp_reward
```

### 5. Edge Cases

#### Test 5.1: Midnight Reset
**Expected**: New missions appear next day

```bash
# Test at 11:59 PM - get today's missions
# Test at 12:01 AM - should see new missions for new day
```

#### Test 5.2: Multiple Users
**Expected**: Each user has independent missions

```bash
# User A completes mission
# User B's mission should be unaffected
```

#### Test 5.3: Inactive Missions
**Setup**: Set a mission to `is_active: false` in database

**Expected**: Mission not assigned to users

## Python Test Script

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. Get missions
resp = requests.get(f"{BASE_URL}/daily-missions", headers=headers)
missions = resp.json()
print(f"✓ Got {missions['total_count']} missions")

# 2. Update first mission
mission_id = missions['missions'][0]['id']
resp = requests.post(
    f"{BASE_URL}/daily-missions/{mission_id}/progress",
    headers=headers,
    json={"increment": 1}
)
result = resp.json()
print(f"✓ Mission {'completed' if result['just_completed'] else 'updated'}")
print(f"  XP gained: {result['xp_gained']}")

# 3. Get history
resp = requests.get(f"{BASE_URL}/daily-missions/history", headers=headers)
history = resp.json()
print(f"✓ History: {history['total_completed']} completed, streak: {history['current_streak']}")
```

## Database Verification

```sql
-- Check missions created
SELECT * FROM daily_missions;

-- Check user missions
SELECT * FROM user_daily_missions WHERE user_id = 'your_user_id';

-- Check XP awards
SELECT 
  u.email,
  u.total_xp,
  SUM(udm.xp_awarded) as mission_xp
FROM users u
LEFT JOIN user_daily_missions udm ON u.id = udm.user_id
WHERE u.id = 'your_user_id'
GROUP BY u.id;
```

## Expected Results Summary

| Test | Expected Result |
|------|----------------|
| First access | Auto-creates 4 missions for user |
| Update progress | Increments current_count |
| Complete mission | Awards XP, sets is_completed |
| Duplicate complete | No effect, xp_gained = 0 |
| Get history | Shows past missions |
| Streak calculation | Consecutive days with all completed |
| Invalid mission | 404 error |
| Midnight reset | New missions next day |

## Success Criteria

✅ All endpoints return correct HTTP status codes
✅ Missions auto-created for new users
✅ Progress updates correctly
✅ XP awarded only once per mission
✅ History shows accurate data
✅ Streak calculated correctly
✅ No duplicate missions per user per day
✅ Database constraints enforced

