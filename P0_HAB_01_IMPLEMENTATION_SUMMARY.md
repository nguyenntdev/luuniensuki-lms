# P0-HAB-01 Implementation Summary: Daily Mission Schema and Progress Tracking

## Date: 2025-01-20

## Overview
Successfully implemented the Daily Mission schema and progress tracking feature for the Luuniensuki LMS platform.

## 1. Database Models (backend/models.py)

### New Enum
- **MissionType**: Enum with values: `lesson`, `quiz`, `discovery`, `streak`

### New Tables

#### DailyMission
Template table for daily missions with the following fields:
- `id`: UUID primary key
- `slug`: str unique (e.g., "complete-1-lesson", "pass-1-quiz")
- `name`: str
- `description`: str (mission description text)
- `mission_type`: MissionType enum
- `target_count`: int (how many to complete, default: 1)
- `xp_reward`: int (XP award on completion, default: 50)
- `is_active`: bool (default: true)
- `created_at`: datetime

Indexes:
- `idx_daily_missions_slug`
- `idx_daily_missions_type`
- `idx_daily_missions_active`

#### UserDailyMission
User's progress tracking for daily missions:
- `id`: UUID primary key
- `user_id`: FK to users (CASCADE on delete)
- `mission_id`: FK to daily_missions (CASCADE on delete)
- `mission_date`: date (the day this mission was assigned - no timezone)
- `current_count`: int (progress towards target, default: 0)
- `is_completed`: bool (default: false)
- `completed_at`: datetime (nullable, timezone-aware)
- `xp_awarded`: int (0 initially, filled when completed)
- `created_at`: datetime (timezone-aware)

Unique constraint: `(user_id, mission_id, mission_date)` - prevents duplicate missions per day

Indexes:
- `idx_user_daily_missions_user`
- `idx_user_daily_missions_mission`
- `idx_user_daily_missions_date`
- `idx_user_daily_missions_completed`

## 2. Database Migration (migrations/versions/0012_daily_missions.py)

Created Alembic migration with:
- Creates `mission_type` ENUM type
- Creates `daily_missions` table with all indexes
- Creates `user_daily_missions` table with all indexes and foreign keys
- Includes downgrade function for rollback
- Uses helper functions to check existence before creating:
  - `_table_exists()`
  - `_index_exists()`
  - `_enum_exists()`

Revision ID: `0012_daily_missions`
Revises: `0011_rag_embeddings`

## 3. API Schemas (backend/schemas.py)

Added comprehensive schemas for API request/response:

### Response Schemas
- **DailyMissionOut**: Template mission details
- **UserDailyMissionOut**: User's mission progress with calculated `progress_percentage`
- **DailyMissionsResponse**: Today's missions summary
- **UpdateMissionProgressResponse**: Response after progress update
- **DailyMissionHistoryItem**: Single historical mission entry
- **DailyMissionHistoryResponse**: Historical missions with streak calculation

### Request Schemas
- **UpdateMissionProgressRequest**: Request to increment mission progress

## 4. API Endpoints (backend/main.py)

### GET /api/v1/daily-missions
**Purpose**: Get today's daily missions with user progress
**Authentication**: Required (current_user)
**Response**: `DailyMissionsResponse`
- Returns all active missions for today
- Auto-creates user missions if they don't exist
- Includes progress percentage calculation
- Returns total XP earned today and completion count

**Logic**:
1. Ensures user has missions assigned for today via `_ensure_daily_missions_for_user()`
2. Fetches all user missions for the current date
3. Calculates progress percentage for each mission
4. Returns summary with total XP and completed count

### POST /api/v1/daily-missions/{mission_id}/progress
**Purpose**: Update progress on a specific daily mission
**Authentication**: Required (current_user)
**Request Body**: `UpdateMissionProgressRequest` with `increment` field
**Response**: `UpdateMissionProgressResponse`
- Increments mission progress
- Awards XP when mission is completed
- Returns whether mission was just completed

**Logic**:
1. Finds user's mission for today
2. If already completed, returns current state without changes
3. Increments `current_count` by `increment` (capped at `target_count`)
4. Checks if mission is now complete
5. If complete:
   - Sets `is_completed = true`
   - Sets `completed_at` timestamp
   - Awards XP to user's `total_xp`
   - Sets `xp_awarded` on the mission record
6. Returns updated mission state with `xp_gained` and `just_completed` flags

### GET /api/v1/daily-missions/history
**Purpose**: Get past mission history
**Authentication**: Required (current_user)
**Query Parameters**: `days` (default: 30, range: 1-90)
**Response**: `DailyMissionHistoryResponse`
- Returns mission history for the specified date range
- Calculates total completed missions and XP earned
- Calculates current completion streak (consecutive days with all missions completed)

**Logic**:
1. Fetches user missions from the last N days
2. Builds history items for each mission
3. Calculates streak by checking consecutive days where all missions were completed
4. Returns aggregated statistics

## 5. Helper Functions

### _ensure_daily_missions_for_user(db, user_id, mission_date)
**Purpose**: Ensures user has all active missions assigned for a given date
**Logic**:
1. Gets all active `DailyMission` templates
2. For each mission, checks if user already has it for the date
3. If not, creates a new `UserDailyMission` record
4. Returns list of user missions

## 6. Model Updates

Updated `backend/main.py` imports to include:
- `DailyMission`
- `UserDailyMission`
- `MissionType`

## 7. Code Patterns Followed

✅ **SQLAlchemy 2.0 Style**
- Used `Mapped[]` type hints
- Used `mapped_column()` for column definitions
- Used `select()` queries
- Used `selectinload()` for eager loading relationships

✅ **Existing Patterns**
- Enum types for mission_type
- UUID primary keys
- Proper timezone handling (timezone-aware for timestamps, naive for dates)
- Index creation for performance
- Cascade deletion for related records
- Unique constraints to prevent duplicates
- Server defaults for boolean and integer fields

✅ **API Patterns**
- FastAPI route decorators
- Pydantic models for request/response
- Dependency injection for auth and database
- Proper HTTP status codes
- Comprehensive error handling

## 8. Migration Strategy

To apply the migration:
```bash
# From the project root
cd backend
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```

## 9. Example Mission Data

To seed initial missions, admins can insert into `daily_missions`:

```sql
INSERT INTO daily_missions (id, slug, name, description, mission_type, target_count, xp_reward, is_active)
VALUES 
  (gen_random_uuid(), 'complete-1-lesson', 'Học 1 bài', 'Hoàn thành 1 bài học hôm nay', 'lesson', 1, 50, true),
  (gen_random_uuid(), 'pass-1-quiz', 'Đạt 1 bài kiểm tra', 'Vượt qua 1 bài kiểm tra hôm nay', 'quiz', 1, 75, true),
  (gen_random_uuid(), 'discover-2-motifs', 'Khám phá 2 họa tiết', 'Khám phá 2 họa tiết mới hôm nay', 'discovery', 2, 100, true),
  (gen_random_uuid(), 'maintain-streak', 'Duy trì chuỗi', 'Duy trì chuỗi học tập', 'streak', 1, 25, true);
```

## 10. Frontend Integration Points

The mobile/web frontend can now:

1. **Display Daily Missions Dashboard**
   - Call `GET /api/v1/daily-missions` on app open
   - Show progress bars for each mission
   - Display total XP earned today

2. **Update Mission Progress**
   - After completing a lesson: `POST /api/v1/daily-missions/{lesson_mission_id}/progress`
   - After passing a quiz: `POST /api/v1/daily-missions/{quiz_mission_id}/progress`
   - After discovering motifs: `POST /api/v1/daily-missions/{discovery_mission_id}/progress`

3. **Show Mission History**
   - Call `GET /api/v1/daily-missions/history?days=30` for analytics
   - Display streak calendar
   - Show XP earnings over time

## 11. Testing Recommendations

1. **Unit Tests**
   - Test mission assignment logic
   - Test progress increment boundaries
   - Test XP awarding
   - Test streak calculation

2. **Integration Tests**
   - Test full mission lifecycle (create -> progress -> complete)
   - Test concurrent mission updates
   - Test edge cases (completing already-completed mission, etc.)

3. **Manual Testing**
   - Create test missions
   - Complete missions and verify XP awards
   - Check mission reset at midnight
   - Verify history and streak calculations

## 12. Next Steps

For full Daily Missions feature:
- [ ] Create admin endpoints to manage mission templates
- [ ] Add automatic mission reset/rotation logic
- [ ] Implement mission notifications
- [ ] Add mission completion animations in UI
- [ ] Create analytics dashboard for mission completion rates
- [ ] Add mission rewards beyond XP (badges, items, etc.)
- [ ] Implement special event missions

## Files Modified

1. `backend/models.py` - Added DailyMission and UserDailyMission models
2. `backend/schemas.py` - Added Daily Mission schemas
3. `backend/main.py` - Added imports and 3 API endpoints
4. `migrations/versions/0012_daily_missions.py` - New migration file

## Status

✅ **COMPLETE** - All requirements from P0-HAB-01 have been implemented:
- ✅ New models defined with proper fields
- ✅ Database migration created
- ✅ API endpoints implemented:
  - ✅ GET /api/v1/daily-missions
  - ✅ POST /api/v1/daily-missions/{mission_id}/progress
  - ✅ GET /api/v1/daily-missions/history
- ✅ Following SQLAlchemy 2.0 style
- ✅ Following existing code patterns

