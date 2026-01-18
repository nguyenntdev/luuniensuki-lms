# Weekly Quests System - README

## What is it?

Weekly Quests are recurring challenges that refresh every Monday, giving users goals to complete throughout the week for XP and badge rewards.

## Quick Start

### 1. Setup
```bash
# Apply database migration
docker-compose exec backend alembic upgrade head

# Seed default quests
docker-compose exec backend python -m backend.seed_weekly_quests
```

### 2. Access via API
```bash
# Get current week's quests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/weekly-quests

# Update quest progress
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  http://localhost:8000/api/v1/weekly-quests/QUEST_ID/progress
```

## Features

- 🔄 **Auto-Assignment**: Quests automatically assigned to all users each week
- 📅 **Week Tracking**: Monday-Sunday week boundaries
- 🎯 **4 Categories**: Exploration, Mastery, Quiz Champion, Streak Master
- 🏆 **Rewards**: XP and optional badge awards
- 📊 **History**: View past weeks' performance
- ⚡ **Real-time**: Progress updates instantly

## Default Quests (7 total)

| Quest | Category | Goal | Reward |
|-------|----------|------|--------|
| Weekly Explorer | Exploration | Discover 10 motifs | 150 XP |
| Weekly Collector | Exploration | Explore 3 urns | 200 XP |
| Weekly Master | Mastery | Master 5 motifs | 250 XP |
| Weekly Lesson Champion | Mastery | Complete 20 lessons | 300 XP |
| Weekly Quiz Master | Quiz Champion | Pass 10 quizzes | 200 XP |
| Weekly Perfect Score | Quiz Champion | 100% on 3 quizzes | 350 XP + badge |
| Weekly Dedication | Streak Master | 7-day streak | 400 XP + badge |

## API Endpoints

### GET /api/v1/weekly-quests
Get current week's quests with your progress.

### POST /api/v1/weekly-quests/{quest_id}/progress
Update progress on a quest. Automatically awards XP and badges on completion.

### GET /api/v1/weekly-quests/history?weeks=4
View your quest history for past weeks.

## Integration

Update quest progress when users complete actions:

```python
from backend.services.weekly_quests import get_week_start_date

# When user discovers a motif
week_start = get_week_start_date()
exploration_quests = db.query(UserWeeklyQuest).filter(
    UserWeeklyQuest.user_id == user.id,
    UserWeeklyQuest.week_start_date == week_start,
    UserWeeklyQuest.quest.category == 'exploration',
    UserWeeklyQuest.is_completed == False
).all()

for quest in exploration_quests:
    quest.current_count += 1
```

## How It Works

1. **Monday Morning**: New week begins, quests are assigned
2. **During Week**: Users complete actions, progress updates
3. **Quest Complete**: XP + badge awarded automatically
4. **Sunday Night**: Week ends, progress saved to history
5. **Next Monday**: Fresh quests assigned, cycle repeats

## Documentation

- 📖 [Implementation Summary](./P0_HAB_02_IMPLEMENTATION_SUMMARY.md)
- 📋 [Quick Reference](./P0_HAB_02_QUICK_REFERENCE.md)
- 🧪 [Testing Guide](./P0_HAB_02_TESTING_GUIDE.md)
- 📄 [File Summary](./P0_HAB_02_FILE_SUMMARY.md)

## Technical Details

**Models:**
- `WeeklyQuest` - Quest templates
- `UserWeeklyQuest` - User progress tracking

**Database:**
- `weekly_quests` table
- `user_weekly_quests` table
- Unique constraint on (user_id, quest_id, week_start_date)

**Service Layer:**
- `backend/services/weekly_quests.py`
- Auto-assignment logic
- Week boundary calculations

## Support

For questions or issues, refer to the testing guide or implementation summary.

