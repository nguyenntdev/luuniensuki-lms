# P0-HAB-02: Weekly Quest Implementation

## Overview
Complete implementation of Weekly Quests system for Luuniensuki LMS, including templates, user progress tracking, auto-assignment, and API endpoints.

## Implementation Date
January 2025

## Components Implemented

### 1. Database Models (`backend/models.py`)

#### QuestCategory Enum
```python
class QuestCategory(str, Enum):
    exploration = "exploration"      # Discover new motifs/urns
    mastery = "mastery"              # Master lessons/motifs
    quiz_champion = "quiz_champion"  # Excel at quizzes
    streak_master = "streak_master"  # Maintain streaks
```

#### WeeklyQuest Model
Weekly quest template - can be time-specific or recurring.

**Fields:**
- `id`: UUID primary key
- `slug`: Unique string identifier
- `name`: Quest name
- `description`: Quest description
- `category`: QuestCategory enum
- `week_number`: Optional week number (1-52) for time-specific quests
- `year`: Optional year for time-specific quests
- `target_count`: Number of actions required to complete
- `xp_reward`: XP awarded on completion
- `badge_slug`: Optional badge to award on completion
- `is_recurring`: Auto-assign to all users every week
- `is_active`: Whether quest is currently active
- `created_at`: Creation timestamp

**Indexes:**
- `slug`, `category`, `week_number + year`, `is_active`, `is_recurring`

#### UserWeeklyQuest Model
Tracks user progress on weekly quests.

**Fields:**
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `quest_id`: Foreign key to weekly_quests table
- `week_start_date`: Monday of the week (date)
- `current_count`: Current progress count
- `is_completed`: Completion status
- `completed_at`: Completion timestamp
- `xp_awarded`: XP awarded for this quest
- `created_at`: Creation timestamp

**Constraints:**
- Unique constraint on (user_id, quest_id, week_start_date)

**Indexes:**
- `user_id`, `quest_id`, `week_start_date`, `is_completed`

### 2. API Schemas (`backend/schemas.py`)

#### Request Schemas
- `UpdateWeeklyQuestProgressRequest`: Update quest progress

#### Response Schemas
- `WeeklyQuestOut`: Weekly quest template data
- `UserWeeklyQuestOut`: User's quest progress
- `WeeklyQuestsResponse`: Current week's quests
- `UpdateWeeklyQuestProgressResponse`: Progress update result
- `WeeklyQuestHistoryItem`: Historical quest entry
- `WeeklyQuestHistoryResponse`: Quest history data

### 3. Service Layer (`backend/services/weekly_quests.py`)

#### Functions

**`get_week_start_date(dt: Optional[datetime] = None) -> datetime`**
- Returns Monday (start) of the week for given datetime
- Defaults to current week if no datetime provided
- Returns naive datetime for database storage

**`get_week_end_date(week_start: datetime) -> datetime`**
- Returns Sunday (end) of the week
- Takes Monday datetime as input

**`ensure_weekly_quests_for_user(db: Session, user_id: UUID, current_time: Optional[datetime] = None) -> list[UserWeeklyQuest]`**
- Assigns all active recurring quests to user for current week
- Idempotent - safe to call multiple times
- Returns list of user's quests for the week
- Called automatically when accessing weekly quest endpoints

**`assign_weekly_quests_to_all_users(db: Session) -> int`**
- Assigns quests to ALL users for current week
- For scheduled job use (e.g., Monday morning cron)
- Returns count of new assignments created

### 4. API Endpoints (`backend/main.py`)

#### GET `/api/v1/weekly-quests`
Get current week's quests with progress.

**Response:**
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
      "current_count": 3,
      "is_completed": false,
      "completed_at": null,
      "xp_awarded": 0,
      "progress_percentage": 30
    }
  ],
  "week_start_date": "2025-01-20T00:00:00",
  "week_end_date": "2025-01-26T23:59:59",
  "total_xp_this_week": 0,
  "completed_count": 0,
  "total_count": 7
}
```

#### POST `/api/v1/weekly-quests/{quest_id}/progress`
Update progress on a weekly quest.

**Request:**
```json
{
  "increment": 1
}
```

**Response:**
```json
{
  "quest": { /* UserWeeklyQuestOut */ },
  "xp_gained": 150,
  "just_completed": true,
  "badge_earned": "quiz-perfectionist"
}
```

**Behavior:**
- Increments quest progress by specified amount
- Caps at target_count (won't overflow)
- Awards XP when quest is completed
- Awards badge if specified in quest template
- Returns current state even if already completed

#### GET `/api/v1/weekly-quests/history`
Get past weekly quest history.

**Query Parameters:**
- `weeks`: Number of weeks to retrieve (1-12, default: 4)

**Response:**
```json
{
  "history": [
    {
      "week_start_date": "2025-01-13T00:00:00",
      "quest_name": "Weekly Explorer",
      "quest_category": "exploration",
      "target_count": 10,
      "current_count": 10,
      "is_completed": true,
      "completed_at": "2025-01-15T14:30:00Z",
      "xp_awarded": 150
    }
  ],
  "total_completed": 5,
  "total_xp_earned": 850
}
```

### 5. Database Migration (`migrations/versions/0013_weekly_quests.py`)

**Creates:**
- `quest_category` enum type
- `weekly_quests` table with indexes
- `user_weekly_quests` table with indexes
- Unique constraint on (user_id, quest_id, week_start_date)
- Foreign key constraints with CASCADE delete

**Revises:** 0012_daily_missions

### 6. Seed Data (`backend/seed_weekly_quests.py`)

**Default Weekly Quests:**

1. **Weekly Explorer** (Exploration)
   - Discover 10 new motifs
   - 150 XP

2. **Weekly Collector** (Exploration)
   - Explore 3 different urns
   - 200 XP

3. **Weekly Master** (Mastery)
   - Master 5 motifs
   - 250 XP

4. **Weekly Lesson Champion** (Mastery)
   - Complete 20 lessons
   - 300 XP

5. **Weekly Quiz Master** (Quiz Champion)
   - Pass 10 quizzes
   - 200 XP

6. **Weekly Perfect Score** (Quiz Champion)
   - Get 100% on 3 quizzes
   - 350 XP + "quiz-perfectionist" badge

7. **Weekly Dedication** (Streak Master)
   - Maintain streak for 7 days
   - 400 XP + "dedicated-learner" badge

## Usage

### Running the Migration
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
docker-compose exec backend alembic upgrade head
```

### Seeding Weekly Quests
```bash
docker-compose exec backend python -m backend.seed_weekly_quests
```

### Auto-Assignment

Quests are automatically assigned when:
1. User accesses any weekly quest endpoint
2. User logs in (can be added to login flow)

For batch assignment (e.g., Monday morning):
```python
from backend.services.weekly_quests import assign_weekly_quests_to_all_users

# In a scheduled job
with Session() as db:
    count = assign_weekly_quests_to_all_users(db)
    print(f"Assigned {count} weekly quests")
```

## Integration Points

### Tracking Quest Progress

Update quest progress when users complete actions:

```python
from backend.services.weekly_quests import get_week_start_date

# When user discovers a motif
week_start = get_week_start_date()
user_quests = db.execute(
    select(UserWeeklyQuest)
    .join(WeeklyQuest)
    .where(
        UserWeeklyQuest.user_id == user_id,
        UserWeeklyQuest.week_start_date == week_start,
        WeeklyQuest.category == QuestCategory.exploration,
        WeeklyQuest.is_completed == False,
    )
).scalars().all()

for uq in user_quests:
    # Call the progress endpoint or update directly
    uq.current_count += 1
    if uq.current_count >= uq.quest.target_count:
        uq.is_completed = True
        uq.completed_at = datetime.now(timezone.utc)
        uq.xp_awarded = uq.quest.xp_reward
        user.total_xp += uq.quest.xp_reward
```

## Testing Checklist

- [ ] Run migration successfully
- [ ] Seed weekly quests
- [ ] Test GET /api/v1/weekly-quests
- [ ] Test POST /api/v1/weekly-quests/{quest_id}/progress
- [ ] Test GET /api/v1/weekly-quests/history
- [ ] Verify auto-assignment on first access
- [ ] Verify XP is awarded on completion
- [ ] Verify badges are awarded when specified
- [ ] Test week boundary logic (Sunday → Monday transition)
- [ ] Verify unique constraint prevents duplicates

## Notes

- Week starts on Monday at 00:00:00
- Week ends on Sunday at 23:59:59
- All dates stored as naive datetime in database
- API returns timezone-aware datetimes
- Recurring quests auto-assign every week
- Non-recurring quests must have week_number and year set
- Badge awards are optional
- Progress is capped at target_count
- Completing a quest multiple times doesn't award XP again

## Future Enhancements

- Add admin endpoints to create/edit quests
- Add weekly quest analytics
- Add quest difficulty tiers
- Add seasonal/event-specific quests
- Add quest chains (complete A to unlock B)
- Add multiplayer/collaborative quests


