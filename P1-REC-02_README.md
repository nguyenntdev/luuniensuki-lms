# P1-REC-02: Lesson Prerequisites and Next Lesson

## Overview

This feature adds prerequisite logic and intelligent "next lesson" recommendations to the Luuniensuki LMS, enabling structured learning paths and preventing users from skipping essential foundational content.

## Quick Start

### 1. Apply Database Migration
```bash
alembic upgrade head
```

### 2. Test the API
```bash
./test_lesson_prerequisites.sh
```

### 3. Get Your Next Lesson
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## What's New?

### 🎯 Smart Lesson Recommendations
- Get personalized next lesson suggestions
- Prioritizes in-progress lessons
- Respects prerequisites and difficulty levels
- Context-aware (filters by urn when applicable)

### 🔒 Prerequisite Management
- Define required (strict) prerequisites
- Add recommended prerequisites for better learning paths
- Automatic lock/unlock based on completion
- Clear visibility of what's needed to progress

### 📊 Learning Path Visualization
- View full ordered sequence of lessons
- See progress through the curriculum
- Check unlock status at a glance
- Filter by collection (urn)

### ✅ Unlock Status Checking
- Verify if a lesson is accessible
- See missing prerequisites
- Distinguish between required and optional

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/lessons/next` | Get next recommended lesson |
| `GET /api/v1/lessons/{id}/prerequisites` | Get lesson prerequisites |
| `GET /api/v1/lessons/{id}/is-unlocked` | Check unlock status |
| `GET /api/v1/lessons/sequence` | Get learning sequence |

## Documentation

- **[📖 Documentation Index](P1-REC-02_INDEX.md)** - Complete documentation hub
- **[📘 Implementation Summary](P1-REC-02_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[📗 API Reference](P1-REC-02_API_REFERENCE.md)** - Full API documentation
- **[📙 Quick Reference](P1-REC-02_QUICK_REFERENCE.md)** - Quick commands

## Example Usage

### Get Next Lesson
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/lessons/next",
    headers={"Authorization": f"Bearer {token}"}
)
next_lesson = response.json()

if next_lesson["lesson_id"]:
    print(f"Next: {next_lesson['motif_name']}")
    print(f"Reason: {next_lesson['reason']}")
else:
    print("All lessons completed!")
```

### Check Prerequisites
```python
response = requests.get(
    f"http://localhost:8000/api/v1/lessons/{lesson_id}/prerequisites",
    headers={"Authorization": f"Bearer {token}"}
)
prereqs = response.json()

if prereqs["all_prerequisites_met"]:
    print("✓ Ready to start!")
else:
    print("Missing prerequisites:")
    for p in prereqs["prerequisites"]:
        if p["is_strict"] and not p["is_completed"]:
            print(f"  - {p['motif_name']} (required)")
```

### Get Learning Sequence
```python
response = requests.get(
    "http://localhost:8000/api/v1/lessons/sequence",
    headers={"Authorization": f"Bearer {token}"}
)
sequence = response.json()

print(f"Progress: {sequence['completed_lessons']}/{sequence['total_lessons']}")
for lesson in sequence["sequence"]:
    status = "✓" if lesson["is_completed"] else ("○" if lesson["is_unlocked"] else "✕")
    print(f"{status} {lesson['position']}. {lesson['motif_name']}")
```

## Database Schema

### New Table: lesson_prerequisites
```sql
CREATE TABLE lesson_prerequisites (
    id UUID PRIMARY KEY,
    lesson_id UUID REFERENCES lesson_content(id),
    prerequisite_lesson_id UUID REFERENCES lesson_content(id),
    is_strict BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(lesson_id, prerequisite_lesson_id)
);
```

### Updated Table: lesson_content
```sql
ALTER TABLE lesson_content
    ADD COLUMN difficulty_level INTEGER,
    ADD COLUMN estimated_time_minutes INTEGER;
```

## Implementation Details

### Service Layer
**File**: `backend/services/lesson_sequence.py`

Key functions:
- `get_next_lesson()` - Smart recommendation algorithm
- `check_lesson_unlocked()` - Prerequisite validation
- `get_lesson_prerequisites()` - Prerequisite details
- `get_lesson_sequence()` - Full path generation

### Recommendation Strategy

1. **Priority 1**: Continue in-progress lessons
2. **Priority 2**: Next unlocked lesson by difficulty

Filters:
- Excludes mastered lessons
- Respects prerequisites
- Considers urn context
- Orders by difficulty level

## Testing

### Automated Testing
```bash
chmod +x test_lesson_prerequisites.sh
./test_lesson_prerequisites.sh
```

The test script verifies:
- ✓ Next lesson recommendation
- ✓ Urn-filtered recommendations
- ✓ Learning sequence retrieval
- ✓ Prerequisite checking
- ✓ Unlock status validation

### Manual Testing
```bash
# Get next lesson
curl -X GET "http://localhost:8000/api/v1/lessons/next" \
  -H "Authorization: Bearer $TOKEN"

# Check if unlocked
curl -X GET "http://localhost:8000/api/v1/lessons/{LESSON_ID}/is-unlocked" \
  -H "Authorization: Bearer $TOKEN"

# Get sequence
curl -X GET "http://localhost:8000/api/v1/lessons/sequence" \
  -H "Authorization: Bearer $TOKEN"
```

## Integration Guide

### Mobile App Integration

```typescript
// HomeScreen.tsx
const { data: nextLesson } = useQuery('nextLesson', () =>
  api.get('/lessons/next')
);

if (nextLesson?.lesson_id) {
  return (
    <ContinueLearningCard
      lessonId={nextLesson.lesson_id}
      title={nextLesson.motif_name}
      estimatedTime={nextLesson.estimated_time_minutes}
    />
  );
}
```

### Learning Path Screen

```typescript
// LearningPathScreen.tsx
const { data: sequence } = useQuery(['sequence', urnId], () =>
  api.get('/lessons/sequence', { params: { urn_id: urnId } })
);

return (
  <View>
    <ProgressBar
      current={sequence.completed_lessons}
      total={sequence.total_lessons}
    />
    <LessonList lessons={sequence.sequence} />
  </View>
);
```

## Files Modified/Created

### Created
- ✅ `backend/services/lesson_sequence.py`
- ✅ `migrations/versions/0026_lesson_prerequisites.py`
- ✅ `test_lesson_prerequisites.sh`
- ✅ `P1-REC-02_*.md` (Documentation)

### Modified
- ✅ `backend/models.py`
- ✅ `backend/schemas.py`
- ✅ `backend/main.py`

## Version Info

- **Version**: 1.0.0
- **Date**: 2025-01-20
- **Status**: ✅ Complete
- **Tested**: ✅ Yes

## Next Steps

1. **Deploy**: Apply migration to production database
2. **Test**: Run test script on staging environment
3. **Integrate**: Update mobile app to use new endpoints
4. **Monitor**: Track usage and performance
5. **Iterate**: Add admin UI for prerequisite management

## Support

- See [API Reference](P1-REC-02_API_REFERENCE.md) for detailed endpoint docs
- Check [Implementation Summary](P1-REC-02_IMPLEMENTATION_SUMMARY.md) for architecture
- Review test script for usage examples
- Check application logs for debugging

---

**Ready to use! 🚀**

