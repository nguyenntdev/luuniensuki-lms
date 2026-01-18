# P0-HAB-02: Weekly Quest Implementation - Complete Summary

## Implementation Status: ✅ COMPLETE

**Date:** January 2025  
**Feature:** Weekly Quest Templates + Assignment Flow  
**Developer:** AI Assistant

---

## 📋 Overview

Successfully implemented a complete Weekly Quest system for Luuniensuki LMS, enabling:
- ✅ Recurring weekly quests that auto-assign to users
- ✅ Progress tracking with XP rewards
- ✅ Optional badge awards on completion
- ✅ Historical quest tracking
- ✅ Week boundary handling (Monday-Sunday)
- ✅ RESTful API endpoints

---

## 📁 Files Modified

### 1. Backend Models
**File:** `backend/models.py`
- Added `QuestCategory` enum (exploration, mastery, quiz_champion, streak_master)
- Added `WeeklyQuest` model (quest templates)
- Added `UserWeeklyQuest` model (user progress tracking)

### 2. Backend Schemas
**File:** `backend/schemas.py`
- Added request/response schemas for all weekly quest endpoints
- Schemas: `WeeklyQuestOut`, `UserWeeklyQuestOut`, `WeeklyQuestsResponse`, etc.

### 3. Backend Main
**File:** `backend/main.py`
- Added imports for new models and schemas
- Added 3 API endpoints:
  - `GET /api/v1/weekly-quests` - Get current week's quests
  - `POST /api/v1/weekly-quests/{quest_id}/progress` - Update progress
  - `GET /api/v1/weekly-quests/history` - Get past weeks

---

## 📁 Files Created

### 1. Service Layer
**File:** `backend/services/weekly_quests.py` (NEW)
- `get_week_start_date()` - Calculate Monday of current week
- `get_week_end_date()` - Calculate Sunday of current week
- `ensure_weekly_quests_for_user()` - Auto-assign quests to user
- `assign_weekly_quests_to_all_users()` - Batch assignment for scheduled jobs

### 2. Database Migration
**File:** `migrations/versions/0013_weekly_quests.py` (NEW)
- Creates `quest_category` enum type
- Creates `weekly_quests` table with indexes
- Creates `user_weekly_quests` table with indexes
- Adds unique constraint and foreign keys
- Revises: 0012_daily_missions

### 3. Seed Script
**File:** `backend/seed_weekly_quests.py` (NEW)
- Seeds 7 default recurring weekly quests
- Categories: exploration, mastery, quiz_champion, streak_master
- XP rewards: 150-400 XP
- Some quests award badges on completion

### 4. Documentation Files

**`P0_HAB_02_IMPLEMENTATION_SUMMARY.md`** (NEW)
- Complete technical documentation
- API endpoints with examples
- Database schema
- Integration guides
- Usage instructions

**`P0_HAB_02_QUICK_REFERENCE.md`** (NEW)
- API endpoint quick reference
- Database schema reference
- Service function examples
- Default quest list
- File locations

**`P0_HAB_02_TESTING_GUIDE.md`** (NEW)
- Step-by-step testing instructions
- Expected responses
- Edge case tests
- Performance tests
- Complete checklist

---

## 🗄️ Database Schema

### weekly_quests Table
```
- id (UUID, PK)
- slug (VARCHAR, UNIQUE)
- name (VARCHAR)
- description (TEXT)
- category (quest_category ENUM)
- week_number (INT, nullable)
- year (INT, nullable)
- target_count (INT)
- xp_reward (INT)
- badge_slug (VARCHAR, nullable)
- is_recurring (BOOLEAN)
- is_active (BOOLEAN)
- created_at (TIMESTAMPTZ)
```

### user_weekly_quests Table
```
- id (UUID, PK)
- user_id (UUID, FK → users.id)
- quest_id (UUID, FK → weekly_quests.id)
- week_start_date (TIMESTAMP)
- current_count (INT)
- is_completed (BOOLEAN)
- completed_at (TIMESTAMPTZ, nullable)
- xp_awarded (INT)
- created_at (TIMESTAMPTZ)

UNIQUE(user_id, quest_id, week_start_date)
```

---

## 🎯 Default Weekly Quests

1. **Weekly Explorer** (Exploration)
   - Discover 10 new motifs → 150 XP

2. **Weekly Collector** (Exploration)
   - Explore 3 different urns → 200 XP

3. **Weekly Master** (Mastery)
   - Master 5 motifs → 250 XP

4. **Weekly Lesson Champion** (Mastery)
   - Complete 20 lessons → 300 XP

5. **Weekly Quiz Master** (Quiz Champion)
   - Pass 10 quizzes → 200 XP

6. **Weekly Perfect Score** (Quiz Champion)
   - Get 100% on 3 quizzes → 350 XP + badge

7. **Weekly Dedication** (Streak Master)
   - Maintain 7-day streak → 400 XP + badge

---

## 🔌 API Endpoints

### GET /api/v1/weekly-quests
Returns current week's quests with user's progress.

**Auth:** Required (Bearer token)

**Response Fields:**
- `quests[]` - List of user's weekly quests
- `week_start_date` - Monday of current week
- `week_end_date` - Sunday of current week
- `total_xp_this_week` - XP earned this week
- `completed_count` - Quests completed this week
- `total_count` - Total quests this week

### POST /api/v1/weekly-quests/{quest_id}/progress
Update progress on a specific quest.

**Auth:** Required (Bearer token)

**Request Body:**
```json
{
  "increment": 1
}
```

**Response Fields:**
- `quest` - Updated quest data
- `xp_gained` - XP just earned
- `just_completed` - Whether quest was just completed
- `badge_earned` - Badge slug if awarded

### GET /api/v1/weekly-quests/history
Get past weekly quest history.

**Auth:** Required (Bearer token)

**Query Parameters:**
- `weeks` - Number of weeks to retrieve (1-12, default: 4)

**Response Fields:**
- `history[]` - List of historical quest entries
- `total_completed` - Total quests completed in range
- `total_xp_earned` - Total XP earned in range

---

## ⚙️ Setup Instructions

### 1. Apply Migration
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
docker-compose exec backend alembic upgrade head
```

### 2. Seed Quests
```bash
docker-compose exec backend python -m backend.seed_weekly_quests
```

### 3. Test Endpoints
```bash
TOKEN="your_jwt_token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/weekly-quests
```

---

## 🔄 Auto-Assignment Logic

Quests are automatically assigned when:
1. ✅ User accesses any weekly quest endpoint
2. ✅ User logs in (can be added to login flow)
3. ✅ Scheduled job runs (batch assignment)

**Week Boundary:**
- Week starts: Monday 00:00:00
- Week ends: Sunday 23:59:59
- New week = fresh quest instances

---

## 🧪 Testing Checklist

- [x] Models created with proper relationships
- [x] Schemas created for all endpoints
- [x] Migration file created
- [x] Service layer functions implemented
- [x] API endpoints added to main.py
- [x] Seed script created
- [x] Documentation written
- [ ] Migration applied to database
- [ ] Quests seeded
- [ ] Endpoints tested
- [ ] Week boundary tested
- [ ] Auto-assignment tested
- [ ] Badge awards tested

---

## 🎓 Usage Example

```python
# User discovers a motif
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
    quest.current_count += 1
    if quest.current_count >= quest.quest.target_count:
        quest.is_completed = True
        quest.completed_at = datetime.now(timezone.utc)
        quest.xp_awarded = quest.quest.xp_reward
        user.total_xp += quest.quest.xp_reward
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `P0_HAB_02_IMPLEMENTATION_SUMMARY.md` | Full technical details |
| `P0_HAB_02_QUICK_REFERENCE.md` | Quick lookup guide |
| `P0_HAB_02_TESTING_GUIDE.md` | Testing instructions |
| `P0_HAB_02_FILE_SUMMARY.md` | This file |

---

## ✨ Key Features

✅ **Auto-Assignment** - Quests automatically assigned to users  
✅ **Week Tracking** - Proper Monday-Sunday week boundaries  
✅ **XP Rewards** - Configurable XP per quest  
✅ **Badge Integration** - Optional badge awards  
✅ **Progress Tracking** - Real-time progress updates  
✅ **Historical Data** - Query past weeks' performance  
✅ **Idempotent** - Safe to call assignment multiple times  
✅ **Type Safety** - Full SQLAlchemy 2.0 + Pydantic types  

---

## 🚀 Next Steps

1. Run migration
2. Seed quests
3. Test endpoints
4. Integrate with existing features:
   - Update exploration quests when motifs discovered
   - Update mastery quests when lessons completed
   - Update quiz quests when quizzes passed
   - Update streak quests when streak maintained
5. Add cron job for Monday morning batch assignment
6. Monitor performance and adjust as needed

---

**Implementation Complete! Ready for Testing & Integration.**

