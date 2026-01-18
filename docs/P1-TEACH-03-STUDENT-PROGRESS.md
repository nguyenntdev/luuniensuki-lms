# P1-TEACH-03: View Student Progress for Each Classroom Member

## Overview

This feature provides comprehensive progress tracking and analytics for students in a classroom. Teachers can view detailed metrics for individual students, class-wide averages, leaderboards, and export progress data.

## Features Implemented

### 1. Student Progress Service (`backend/services/student_progress.py`)

The service provides the following functionality:

- **Individual Student Progress**: Calculate comprehensive progress metrics for a single student
- **Class-Wide Summary**: Aggregate and average metrics across all students in a classroom
- **Leaderboard**: Rank students by various performance metrics
- **Time Tracking**: Calculate total time spent learning from user sessions

### 2. Database Model (`StudentProgressSnapshot`)

Added a new model for caching daily progress snapshots:

```python
class StudentProgressSnapshot(Base):
    """Cached progress snapshots for classroom students."""
    - student_id: UUID (FK to users)
    - classroom_id: UUID (FK to classes)
    - snapshot_date: date
    - lessons_completed: int
    - quizzes_passed: int
    - average_quiz_score: float
    - motifs_discovered: int
    - current_streak: int
    - xp_earned: int
    - time_spent_minutes: int
    - created_at: datetime
```

**Indexes**:
- `idx_progress_snapshots_student` on `student_id`
- `idx_progress_snapshots_classroom` on `classroom_id`
- `idx_progress_snapshots_date` on `snapshot_date`
- Unique constraint on `(student_id, classroom_id, snapshot_date)`

### 3. API Endpoints

#### GET `/api/v1/classrooms/{classroom_id}/students/{student_id}/progress`

Get detailed progress for a specific student.

**Response**:
```json
{
  "student_id": "uuid",
  "classroom_id": "uuid",
  "joined_at": "2024-01-01T00:00:00Z",
  "overall_completion_percent": 65.5,
  "lessons": {
    "total_motifs": 100,
    "discovered": 65,
    "learned": 40,
    "mastered": 20
  },
  "quizzes": {
    "total_attempts": 150,
    "passed": 120,
    "average_score": 85.5
  },
  "engagement": {
    "current_streak": 7,
    "longest_streak": 15,
    "total_xp": 5000,
    "time_spent_minutes": 1200
  }
}
```

#### GET `/api/v1/classrooms/{classroom_id}/progress`

Get class-wide progress summary with averages.

**Response**:
```json
{
  "classroom_id": "uuid",
  "student_count": 25,
  "averages": {
    "completion_percent": 55.2,
    "discovered_motifs": 55.2,
    "learned_motifs": 32.5,
    "mastered_motifs": 15.3,
    "quiz_attempts": 120.5,
    "quizzes_passed": 95.2,
    "average_quiz_score": 78.5,
    "current_streak": 5.5,
    "total_xp": 3500.0
  }
}
```

#### GET `/api/v1/classrooms/{classroom_id}/leaderboard`

Get class leaderboard sorted by various metrics.

**Query Parameters**:
- `order_by`: `xp` | `streak` | `motifs` | `quizzes` (default: `xp`)
- `limit`: 1-100 (default: 50)

**Response**:
```json
{
  "classroom_id": "uuid",
  "order_by": "xp",
  "entries": [
    {
      "rank": 1,
      "student_id": "uuid",
      "display_name": "John Doe",
      "total_xp": 8500,
      "current_streak": 15,
      "discovered_motifs": 80,
      "mastered_motifs": 45,
      "quizzes_passed": 200
    }
  ]
}
```

#### GET `/api/v1/classrooms/{classroom_id}/export`

Export class progress data as CSV.

**Returns**: CSV file with headers:
- Student ID
- Display Name
- Email
- Joined At
- Completion %
- Discovered Motifs
- Learned Motifs
- Mastered Motifs
- Quiz Attempts
- Quizzes Passed
- Avg Quiz Score
- Current Streak
- Longest Streak
- Total XP
- Time Spent (min)

### 4. Schemas

Added the following Pydantic schemas in `backend/schemas.py`:

- `LessonStatsOut`: Lesson/motif completion statistics
- `QuizStatsOut`: Quiz performance statistics
- `EngagementStatsOut`: Student engagement statistics
- `StudentProgressOut`: Complete student progress response
- `ClassProgressAveragesOut`: Class-wide average metrics
- `ClassProgressSummaryOut`: Class-wide progress summary
- `LeaderboardEntryOut`: Single leaderboard entry
- `LeaderboardOut`: Complete leaderboard response

### 5. Database Migration

Created migration `0030_student_progress_snapshots.py` to add the `StudentProgressSnapshot` table.

**To apply migration**:
```bash
cd backend
alembic upgrade head
```

## Authorization

All endpoints require the user to be:
- The teacher of the classroom, OR
- An admin/super_admin user

This is enforced via the `_ensure_class_access()` function.

## Usage Examples

### Get Individual Student Progress

```bash
curl -X GET \
  "http://localhost:8000/api/v1/classrooms/{classroom_id}/students/{student_id}/progress" \
  -H "Authorization: Bearer {token}"
```

### Get Class Summary

```bash
curl -X GET \
  "http://localhost:8000/api/v1/classrooms/{classroom_id}/progress" \
  -H "Authorization: Bearer {token}"
```

### Get Leaderboard

```bash
# Sort by XP (default)
curl -X GET \
  "http://localhost:8000/api/v1/classrooms/{classroom_id}/leaderboard" \
  -H "Authorization: Bearer {token}"

# Sort by streak
curl -X GET \
  "http://localhost:8000/api/v1/classrooms/{classroom_id}/leaderboard?order_by=streak" \
  -H "Authorization: Bearer {token}"
```

### Export Progress Data

```bash
curl -X GET \
  "http://localhost:8000/api/v1/classrooms/{classroom_id}/export" \
  -H "Authorization: Bearer {token}" \
  -o progress_export.csv
```

## Performance Considerations

1. **Caching**: The `StudentProgressSnapshot` model can be used for daily caching to reduce real-time calculation load. This is optional and can be implemented as a background task.

2. **Batch Queries**: The class summary and leaderboard endpoints may perform multiple queries. Consider implementing query optimization or using the snapshot cache for large classrooms.

3. **Time Calculation**: Time spent is calculated from `UserSession` records. Ensure sessions are properly ended for accurate tracking.

## Future Enhancements

1. **Snapshot Generation**: Implement a daily cron job to populate `StudentProgressSnapshot` for faster queries
2. **Comparison Views**: Add endpoints to compare student progress over time
3. **Custom Date Ranges**: Allow filtering progress by date ranges
4. **Advanced Analytics**: Add trend analysis and prediction features
5. **Email Reports**: Allow teachers to schedule automated progress reports
6. **Student View**: Allow students to view their own progress in a classroom

## Files Changed

- `backend/models.py`: Added `StudentProgressSnapshot` model and `Date` import
- `backend/services/student_progress.py`: New service with progress calculation logic
- `backend/schemas.py`: Added student progress schemas
- `backend/main.py`: Added 4 new API endpoints
- `migrations/versions/0030_student_progress_snapshots.py`: Database migration

## Testing Checklist

- [ ] Verify individual student progress endpoint returns correct data
- [ ] Verify class summary calculates averages correctly
- [ ] Verify leaderboard sorting works for all sort options
- [ ] Verify CSV export includes all students and columns
- [ ] Verify authorization prevents unauthorized access
- [ ] Test with empty classrooms (no students)
- [ ] Test with students who have no progress
- [ ] Verify migration applies successfully
- [ ] Performance test with large classrooms (100+ students)


