# Daily Missions Feature

**Status**: ✅ Implemented
**Version**: 1.0
**Date**: 2025-01-20

## Overview

Daily Missions is a gamification feature that provides users with daily goals to complete, encouraging regular engagement with the Luuniensuki LMS platform. Users can earn XP by completing missions such as finishing lessons, passing quizzes, and discovering new cultural motifs.

## Features

### ✨ Core Functionality

- **4 Daily Mission Types**:
  1. **Lesson** - Complete lessons about cultural artifacts
  2. **Quiz** - Pass quiz assessments
  3. **Discovery** - Discover new motifs on the urns
  4. **Streak** - Maintain learning streaks

- **Progress Tracking**: Real-time progress updates for each mission
- **XP Rewards**: Earn experience points upon mission completion
- **History & Streaks**: View past performance and maintain learning streaks
- **Auto-Assignment**: Missions automatically assigned to users each day

### 📊 Mission Details

| Mission | Target | XP Reward |
|---------|--------|-----------|
| Học 1 Bài (Complete 1 Lesson) | 1 | 50 |
| Đạt 1 Bài Kiểm Tra (Pass 1 Quiz) | 1 | 75 |
| Khám Phá 2 Họa Tiết (Discover 2 Motifs) | 2 | 100 |
| Duy Trì Chuỗi (Maintain Streak) | 1 | 25 |

**Total Possible Daily XP**: 250 XP

## API Endpoints

### GET /api/v1/daily-missions
Get today's missions with current progress.

**Authentication**: Required

**Response**:
```json
{
  "missions": [...],
  "total_xp_today": 125,
  "completed_count": 2,
  "total_count": 4
}
```

### POST /api/v1/daily-missions/{mission_id}/progress
Update progress on a specific mission.

**Authentication**: Required

**Request Body**:
```json
{
  "increment": 1
}
```

**Response**:
```json
{
  "mission": {...},
  "xp_gained": 50,
  "just_completed": true
}
```

### GET /api/v1/daily-missions/history
Get past mission history and streaks.

**Authentication**: Required

**Query Parameters**:
- `days` (optional): Number of days to fetch (default: 30, max: 90)

**Response**:
```json
{
  "history": [...],
  "total_completed": 24,
  "total_xp_earned": 1200,
  "current_streak": 3
}
```

## Database Schema

### Table: daily_missions
Mission templates that define available missions.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| slug | String | Unique identifier (e.g., "complete-1-lesson") |
| name | String | Display name |
| description | String | Mission description |
| mission_type | Enum | Type: lesson, quiz, discovery, streak |
| target_count | Integer | Number to complete (default: 1) |
| xp_reward | Integer | XP awarded on completion (default: 50) |
| is_active | Boolean | Whether mission is currently active |
| created_at | DateTime | Creation timestamp |

### Table: user_daily_missions
User's daily mission progress.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| mission_id | UUID | Foreign key to daily_missions |
| mission_date | Date | The date this mission was assigned |
| current_count | Integer | Current progress (default: 0) |
| is_completed | Boolean | Completion status |
| completed_at | DateTime | When mission was completed (nullable) |
| xp_awarded | Integer | XP given (0 until completion) |
| created_at | DateTime | Creation timestamp |

**Unique Constraint**: (user_id, mission_id, mission_date)

## Setup Instructions

### 1. Apply Database Migration

```bash
cd backend
alembic upgrade head
```

### 2. Seed Initial Missions

```bash
cd backend
python3 seed_daily_missions.py
```

### 3. Verify Setup

```bash
# Check missions created
psql luuniensuki -c "SELECT slug, name, xp_reward FROM daily_missions;"
```

## Usage Examples

### Frontend Integration

```typescript
// Get today's missions
const response = await fetch('/api/v1/daily-missions', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Display missions
data.missions.forEach(mission => {
  console.log(`${mission.mission.name}: ${mission.current_count}/${mission.mission.target_count}`);
  console.log(`Progress: ${mission.progress_percentage}%`);
});

// Update mission progress (after completing a lesson)
await fetch(`/api/v1/daily-missions/${missionId}/progress`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ increment: 1 })
});
```

### Mobile Integration

```dart
// DailyMissionsScreen in Flutter
class DailyMissionsScreen extends StatefulWidget {
  // Fetch missions on load
  // Display progress bars
  // Show XP earned today
  // Celebrate mission completion with animation
}
```

## How It Works

1. **Mission Assignment**
   - When a user accesses `/daily-missions` for the first time each day
   - All active `DailyMission` templates are fetched
   - `UserDailyMission` records created for that user + date combination

2. **Progress Tracking**
   - Other parts of the app (lesson completion, quiz pass, etc.) call the progress endpoint
   - `current_count` incremented up to `target_count`
   - When `current_count >= target_count`, mission marked complete

3. **XP Awarding**
   - On first completion: `xp_awarded` set to `xp_reward` value
   - User's `total_xp` increased by `xp_reward`
   - Subsequent progress updates don't award additional XP

4. **Streak Calculation**
   - Looks backwards from today
   - For each day, checks if ALL missions were completed
   - Streak breaks when a day is found with incomplete missions

## Future Enhancements

- [ ] **Variable Missions**: Rotate different missions each day
- [ ] **Difficulty Scaling**: Harder missions for advanced users
- [ ] **Bonus Missions**: Special weekend or event missions
- [ ] **Mission Notifications**: Push notifications for incomplete missions
- [ ] **Social Sharing**: Share mission completions with friends
- [ ] **Leaderboards**: Daily/weekly mission completion rankings
- [ ] **Rewards Beyond XP**: Unlock badges, cosmetics, or special content
- [ ] **Admin Dashboard**: Manage missions, view completion rates
- [ ] **A/B Testing**: Test different mission configurations

## Technical Details

### Code Locations

- **Models**: `backend/models.py` (lines 1170-1319)
- **Schemas**: `backend/schemas.py` (lines 731-820)
- **Endpoints**: `backend/main.py` (lines 7890-8206)
- **Migration**: `migrations/versions/0012_daily_missions.py`
- **Seed Script**: `backend/seed_daily_missions.py`

### Dependencies

- SQLAlchemy 2.0
- FastAPI
- PostgreSQL

### Performance Considerations

- Indexes on frequently queried fields (user_id, mission_date, is_completed)
- Eager loading with `selectinload()` to avoid N+1 queries
- Unique constraints prevent duplicate missions
- Cascade deletes handle cleanup

## Testing

See [DAILY_MISSIONS_TESTING_GUIDE.md](./DAILY_MISSIONS_TESTING_GUIDE.md) for comprehensive test cases.

## Support

For issues or questions:
1. Check the implementation summary: [P0_HAB_01_IMPLEMENTATION_SUMMARY.md](./P0_HAB_01_IMPLEMENTATION_SUMMARY.md)
2. Review the testing guide
3. Examine the database migration file
4. Contact the development team

---

**Implemented by**: Development Team
**Feature ID**: P0-HAB-01
**Related Docs**: 
- [Implementation Summary](./P0_HAB_01_IMPLEMENTATION_SUMMARY.md)
- [Testing Guide](./DAILY_MISSIONS_TESTING_GUIDE.md)

