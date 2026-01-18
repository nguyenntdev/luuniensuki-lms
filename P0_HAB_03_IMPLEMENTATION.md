# P0-HAB-03: Streak System Implementation

**Status**: ✅ Implemented  
**Version**: 1.0  
**Date**: 2025-01-20

## Overview

The Streak System is a gamification feature that rewards users for maintaining daily learning streaks. Users earn XP for consistent activity, unlock milestone rewards at 7, 30, and 100-day streaks, and can use streak freezes to protect their progress.

## Features

### Core Functionality

- **Daily Streak Tracking**: Automatically tracks consecutive days of learning activity
- **Streak Calculation**: Calculates current and longest streaks based on `last_active_at`
- **Milestone Rewards**: Award badges, XP, and streak freezes at key milestones
- **Streak Freezes**: Protect your streak when you miss a day
- **At-Risk Detection**: Identifies when a streak is about to break

### Reward Structure

#### Daily Completion
- **10 XP** for maintaining your streak each day

#### Milestone Rewards

| Milestone | XP Bonus | Badge | Streak Freeze |
|-----------|----------|-------|---------------|
| 7 Days    | 100 XP   | 🔥 Thất Nhật Liên Tiếp | 0 |
| 30 Days   | 500 XP   | 🔥🔥 Tam Thập Nhật Liên Tiếp | 0 |
| 100 Days  | 2000 XP  | 🔥🔥🔥 Bách Nhật Liên Tiếp | 1 |

## Backend Implementation

### 1. Database Model

**StreakReward** (`backend/models.py`)
```python
class StreakReward(Base):
    __tablename__ = "streak_rewards"
    
    id: UUID
    user_id: UUID  # FK to users
    streak_day: int  # Milestone day (7, 30, 100)
    reward_type: str  # "xp", "badge", or "streak_freeze"
    reward_amount: int
    awarded_at: datetime
    created_at: datetime
```

**Indexes**:
- `idx_streak_rewards_user` on `user_id`
- `idx_streak_rewards_streak_day` on `streak_day`
- Unique constraint on `(user_id, streak_day)`

### 2. Streak Service

**Location**: `backend/services/streak.py`

**Functions**:

```python
def calculate_current_streak(user: User, now: datetime) -> int
    """Calculate current streak based on last_active_at."""

def is_streak_maintained_today(user: User, now: datetime) -> bool
    """Check if user has been active today."""

def is_streak_at_risk(user: User, now: datetime) -> bool
    """Check if streak is at risk (no activity today)."""

def use_streak_freeze(db: Session, user: User, now: datetime) -> bool
    """Use a streak freeze to protect the streak."""

def award_daily_streak_reward(db: Session, user: User, now: datetime) -> int
    """Award 10 XP for daily streak completion."""

def award_milestone_rewards(db: Session, user: User, now: datetime) -> dict
    """Award milestone rewards (badges, XP, freezes)."""

def get_next_milestone(current_streak: int) -> Optional[dict]
    """Get information about the next milestone."""
```

### 3. API Endpoints

#### GET /api/v1/streak
Get current streak status with milestones.

**Response**:
```json
{
  "current_streak": 7,
  "longest_streak": 10,
  "streak_freezes": 1,
  "is_maintained_today": true,
  "is_at_risk": false,
  "next_milestone": {
    "day": 30,
    "days_remaining": 23,
    "rewards": {
      "xp": 500,
      "badge_slug": "streak-30-days",
      "freeze": 0
    }
  },
  "milestones": [
    {
      "day": 7,
      "xp_reward": 100,
      "badge_slug": "streak-7",
      "freeze_reward": 0,
      "is_completed": true
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

#### POST /api/v1/streak/claim-daily
Claim daily streak reward (10 XP).

**Requirements**:
- User must be active today (`is_maintained_today` = true)

**Response**:
```json
{
  "xp_awarded": 10,
  "current_streak": 7,
  "total_xp": 1850,
  "message": "Earned 10 XP for maintaining your streak!"
}
```

If milestone rewards are triggered:
```json
{
  "xp_awarded": 110,
  "current_streak": 7,
  "total_xp": 1950,
  "message": "Earned 10 XP for maintaining your streak! Plus 100 XP from milestone rewards!"
}
```

#### POST /api/v1/streak/use-freeze
Use a streak freeze to protect the streak.

**Requirements**:
- User must have at least 1 streak freeze available
- Streak must be at risk (no activity today)

**Response** (Success):
```json
{
  "success": true,
  "remaining_freezes": 0,
  "message": "Streak freeze used successfully! Your streak is protected."
}
```

**Response** (Failure):
```json
{
  "success": false,
  "remaining_freezes": 0,
  "message": "You don't have any streak freezes available"
}
```

### 4. Database Migration

**File**: `migrations/versions/0014_streak_rewards.py`

Creates the `streak_rewards` table with proper indexes and constraints.

**Run migration**:
```bash
docker compose exec api alembic upgrade head
```

### 5. Badge Seeding

Three new badges added to `backend/seed.py`:

- **streak-7**: Thất Nhật Liên Tiếp (7-Day Streak) - 150 XP bonus
- **streak-30-days**: Tam Thập Nhật Liên Tiếp (30-Day Streak) - 500 XP bonus  
- **streak-100-days**: Bách Nhật Liên Tiếp (100-Day Streak) - 2000 XP bonus

**Seed badges**:
```bash
docker compose exec api python -m backend.seed
```

## Integration with Existing Systems

### Streak Updates
The existing `_update_streak()` function in `main.py` is called on:
- Lesson completion
- Quiz submission
- Motif discovery
- Urn exam submission

This automatically maintains the streak counter.

### User Model Fields
Uses existing fields on the `User` model:
- `current_streak`: Current consecutive days
- `longest_streak`: All-time best streak
- `streak_freezes`: Available freeze count
- `last_active_at`: Last activity timestamp

## Testing

### Manual Testing

1. **Check initial status**:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/streak
   ```

2. **Complete learning activity** (lesson, quiz, etc.) to increment streak

3. **Claim daily reward**:
   ```bash
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/streak/claim-daily
   ```

4. **Use streak freeze**:
   ```bash
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/streak/use-freeze
   ```

### Test Scenarios

- [ ] New user starts with 0 streak
- [ ] Streak increments after daily activity
- [ ] Streak resets after missing a day
- [ ] 7-day milestone awards badge and XP
- [ ] 30-day milestone awards badge and XP
- [ ] 100-day milestone awards badge, XP, and streak freeze
- [ ] Streak freeze protects streak when used
- [ ] Cannot use freeze if none available
- [ ] Cannot claim daily reward if not active today
- [ ] Milestones are only awarded once

## Files Changed

### New Files
- `backend/services/streak.py` - Streak service logic
- `migrations/versions/0014_streak_rewards.py` - Database migration
- `P0_HAB_03_IMPLEMENTATION.md` - This documentation

### Modified Files
- `backend/models.py` - Added StreakReward model
- `backend/main.py` - Added streak endpoints and badge constants
- `backend/seed.py` - Added 30-day and 100-day streak badges
- `backend/schemas.py` - Added streak response schemas

## Future Enhancements

- [ ] Mobile UI for streak visualization
- [ ] Push notifications for streak at risk
- [ ] Streak leaderboard
- [ ] Weekly/monthly streak challenges
- [ ] Custom streak freeze purchase with gems
- [ ] Streak recovery grace period

## References

- **Existing Streak Logic**: `backend/main.py:_update_streak()`
- **Badge System**: `backend/models.py:Badge` and `backend/seed.py:DEFAULT_BADGES`
- **Daily Missions**: Similar pattern in `backend/models.py:DailyMission`

