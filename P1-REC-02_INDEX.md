# P1-REC-02: Lesson Prerequisites and Next Lesson - Documentation Index

## Quick Links

- **[Implementation Summary](P1-REC-02_IMPLEMENTATION_SUMMARY.md)** - Complete overview of the implementation
- **[API Reference](P1-REC-02_API_REFERENCE.md)** - Detailed API documentation
- **[Quick Reference](P1-REC-02_QUICK_REFERENCE.md)** - Quick guide for common operations

## What is P1-REC-02?

P1-REC-02 adds intelligent lesson sequencing and prerequisite management to the Luuniensuki LMS. This feature:

- **Guides learners** through content in the right order
- **Prevents confusion** by ensuring prerequisites are met before advancing
- **Provides recommendations** for what to learn next
- **Shows progress** through visual learning paths

## Key Features

### 1. Lesson Prerequisites
- Define which lessons must be completed before others
- Support for **strict** (required) and **recommended** prerequisites
- Automatic unlock/lock based on completion status

### 2. Next Lesson Recommendations
- Smart algorithm to suggest the best next lesson
- Prioritizes in-progress lessons
- Respects prerequisites and difficulty progression
- Filters by urn when viewing specific collections

### 3. Learning Sequence Visualization
- Shows full ordered path of lessons
- Displays unlock status for each lesson
- Tracks progress through the sequence
- Filterable by urn

### 4. Unlock Status Checking
- Check if user can access a lesson
- Lists missing prerequisites
- Distinguishes between required and recommended

## Getting Started

### 1. Database Setup

Run the migration:
```bash
alembic upgrade head
```

Or with Docker:
```bash
docker-compose exec backend alembic upgrade head
```

### 2. Try the API

Get your next lesson:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Run Tests

```bash
chmod +x test_lesson_prerequisites.sh
./test_lesson_prerequisites.sh
```

## API Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/lessons/next` | GET | Get next recommended lesson |
| `/api/v1/lessons/{id}/prerequisites` | GET | Get lesson prerequisites |
| `/api/v1/lessons/{id}/is-unlocked` | GET | Check if lesson is unlocked |
| `/api/v1/lessons/sequence` | GET | Get full learning sequence |

All endpoints require authentication and return JSON.

## Use Cases

### Mobile App: Home Screen
```typescript
// Show "Continue Learning" button
const nextLesson = await getNextLesson();
if (nextLesson.lesson_id) {
  showContinueLearningButton(nextLesson);
}
```

### Learning Path Screen
```typescript
// Display progress and sequence
const sequence = await getLearningSequence(urnId);
showProgressBar(sequence.completed_lessons, sequence.total_lessons);
renderLessonList(sequence.sequence);
```

### Lesson Detail: Lock/Unlock UI
```typescript
// Before entering lesson
const unlockStatus = await checkLessonUnlocked(lessonId);
if (!unlockStatus.is_unlocked) {
  showLockedScreen(unlockStatus.missing_prerequisites);
} else {
  allowLessonAccess();
}
```

## Data Model

### LessonPrerequisite
```
lesson_id → prerequisite_lesson_id
(Dragon lesson requires Phoenix lesson)
```

### LessonContent (new fields)
- `difficulty_level`: 1-5 (beginner to advanced)
- `estimated_time_minutes`: Completion time estimate

## Architecture

```
┌─────────────────┐
│  Mobile App     │
│  (User)         │
└────────┬────────┘
         │ API Request
         ▼
┌─────────────────┐
│  FastAPI        │
│  (main.py)      │
└────────┬────────┘
         │ Service Call
         ▼
┌─────────────────┐
│  lesson_sequence│
│  Service        │
└────────┬────────┘
         │ DB Query
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  Database       │
└─────────────────┘
```

## Files Changed/Created

### Created
- `backend/services/lesson_sequence.py` - Core logic
- `migrations/versions/0026_lesson_prerequisites.py` - Database schema
- `test_lesson_prerequisites.sh` - Test script
- Documentation files (this and others)

### Modified
- `backend/models.py` - Added LessonPrerequisite model and fields
- `backend/schemas.py` - Added prerequisite schemas
- `backend/main.py` - Added 4 new API endpoints

## Integration Guide

### For Frontend Developers

1. **Import the types** (if using TypeScript):
```typescript
interface NextLessonOut {
  lesson_id: string | null;
  motif_id: string | null;
  motif_name: string | null;
  // ... see API Reference for full schema
}
```

2. **Call the endpoints**:
```typescript
const response = await fetch('/api/v1/lessons/next', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const nextLesson: NextLessonOut = await response.json();
```

3. **Handle the response**:
```typescript
if (nextLesson.lesson_id) {
  // Show lesson
} else {
  // No lessons available
}
```

### For Mobile Developers

See the API Reference for complete request/response examples.

Key considerations:
- Cache the sequence locally for offline viewing
- Update unlock status when lessons are completed
- Show visual indicators for locked vs unlocked lessons

## Future Enhancements

- [ ] Admin UI for managing prerequisites
- [ ] Skill tree visualization
- [ ] Alternative prerequisite paths (A OR B)
- [ ] Time-based unlocks
- [ ] Adaptive difficulty based on performance
- [ ] Prerequisite suggestions based on content similarity

## Support

For questions or issues:
1. Check the API Reference for endpoint details
2. Review the Implementation Summary for architecture
3. Run the test script to verify your setup
4. Check server logs for error details

## Version History

- **v1.0** (2025-01-20): Initial implementation
  - Added LessonPrerequisite model
  - Added 4 API endpoints
  - Added lesson_sequence service
  - Added database migration

