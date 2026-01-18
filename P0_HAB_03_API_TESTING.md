# P0-HAB-03: Streak API Testing Guide

## Prerequisites

1. **Run database migration**:
   ```bash
   docker compose exec api alembic upgrade head
   ```

2. **Seed badges**:
   ```bash
   docker compose exec api python -m backend.seed
   ```

3. **Get authentication token**:
   ```bash
   # Register or login to get token
   TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password123"}' \
     | jq -r '.access_token')
   ```

## API Testing

### 1. Get Streak Status

**Endpoint**: `GET /api/v1/streak`

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/streak | jq
```

**Expected Response**:
```json
{
  "current_streak": 0,
  "longest_streak": 0,
  "streak_freezes": 0,
  "is_maintained_today": false,
  "is_at_risk": false,
  "next_milestone": {
    "day": 7,
    "days_remaining": 7,
    "rewards": {
      "xp": 100,
      "badge_slug": "streak-7",
      "freeze": 0
    }
  },
  "milestones": [
    {
      "day": 7,
      "xp_reward": 100,
      "badge_slug": "streak-7",
      "freeze_reward": 0,
      "is_completed": false
    },
    {
      "day": 30,
      "xp_reward": 500,
      "badge_slug": "streak-30-days",
      "freeze_reward": 0,
      "is_completed": false
    },
    {
      "day": 100,
      "xp_reward": 2000,
      "badge_slug": "streak-100-days",
      "freeze_reward": 1,
      "is_completed": false
    }
  ]
}
```

### 2. Complete Learning Activity

Do any learning activity to increment streak (choose one):

**Discover a motif**:
```bash
curl -X POST "http://localhost:8000/api/v1/motifs/{MOTIF_ID}/discover" \
  -H "Authorization: Bearer $TOKEN"
```

**Complete a lesson**:
```bash
curl -X POST "http://localhost:8000/api/v1/lessons/{LESSON_ID}/complete" \
  -H "Authorization: Bearer $TOKEN"
```

**Submit a quiz**:
```bash
curl -X POST "http://localhost:8000/api/v1/quizzes/{MOTIF_ID}/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"answers":[...]}'
```

### 3. Claim Daily Streak Reward

**Endpoint**: `POST /api/v1/streak/claim-daily`

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/streak/claim-daily | jq
```

**Expected Response** (first claim):
```json
{
  "xp_awarded": 10,
  "current_streak": 1,
  "total_xp": 10,
  "message": "Earned 10 XP for maintaining your streak!"
}
```

**Expected Response** (7-day milestone):
```json
{
  "xp_awarded": 110,
  "current_streak": 7,
  "total_xp": 370,
  "message": "Earned 10 XP for maintaining your streak! Plus 100 XP from milestone rewards!"
}
```

**Error Response** (not active today):
```json
{
  "detail": "You must be active today to claim daily streak reward"
}
```

### 4. Use Streak Freeze

**Endpoint**: `POST /api/v1/streak/use-freeze`

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/streak/use-freeze | jq
```

**Expected Response** (success):
```json
{
  "success": true,
  "remaining_freezes": 0,
  "message": "Streak freeze used successfully! Your streak is protected."
}
```

**Expected Response** (no freezes available):
```json
{
  "success": false,
  "remaining_freezes": 0,
  "message": "You don't have any streak freezes available"
}
```

**Expected Response** (streak not at risk):
```json
{
  "success": false,
  "remaining_freezes": 1,
  "message": "Streak freeze can only be used when your streak is at risk"
}
```

## Testing Scenarios

### Scenario 1: New User Streak Journey

1. Check initial status (0 streak)
2. Complete learning activity
3. Claim daily reward (+10 XP, streak = 1)
4. Repeat for 7 days
5. On day 7, claim reward to get milestone (+100 XP bonus + badge)
6. Verify badge was awarded in user profile

### Scenario 2: Streak Freeze Usage

1. Build a 10-day streak
2. Reach 100-day milestone to earn a freeze
3. Skip a day (don't complete any learning)
4. Use streak freeze to protect streak
5. Verify freeze was consumed and streak maintained

### Scenario 3: Streak Break

1. Build a 5-day streak
2. Skip 2 days without using freeze
3. Complete learning activity
4. Verify streak reset to 1

## Database Queries

Check streak rewards in database:

```sql
-- View all streak rewards for a user
SELECT * FROM streak_rewards 
WHERE user_id = 'USER_UUID' 
ORDER BY awarded_at DESC;

-- View user's streak stats
SELECT 
  display_name,
  current_streak, 
  longest_streak,
  streak_freezes,
  last_active_at
FROM users 
WHERE email = 'user@example.com';

-- View awarded badges
SELECT 
  b.slug,
  b.name,
  b.xp_bonus,
  ub.earned_at
FROM user_badges ub
JOIN badges b ON b.id = ub.badge_id
WHERE ub.user_id = 'USER_UUID'
ORDER BY ub.earned_at DESC;
```

## Troubleshooting

### Issue: "You must be active today"
**Solution**: Complete any learning activity (lesson, quiz, discovery) before claiming

### Issue: Badge not awarded
**Solution**: Check badges were seeded with `python -m backend.seed`

### Issue: Milestone not triggering
**Solution**: Verify `current_streak` matches milestone day exactly (7, 30, or 100)

### Issue: Database errors
**Solution**: Run migration with `alembic upgrade head`

