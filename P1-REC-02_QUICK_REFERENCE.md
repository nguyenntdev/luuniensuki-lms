# P1-REC-02: Quick Reference

## API Endpoints

### 1. Get Next Lesson
```
GET /api/v1/lessons/next?urn_id={optional}
```
Returns the next recommended lesson for the user.

### 2. Get Lesson Prerequisites
```
GET /api/v1/lessons/{lesson_id}/prerequisites
```
Returns all prerequisites for a lesson with completion status.

### 3. Check Lesson Unlocked
```
GET /api/v1/lessons/{lesson_id}/is-unlocked
```
Returns whether the lesson is unlocked and lists missing prerequisites.

### 4. Get Lesson Sequence
```
GET /api/v1/lessons/sequence?urn_id={optional}
```
Returns the full ordered learning sequence with progress.

## Database Schema

### lesson_prerequisites
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

### lesson_content (new fields)
```sql
ALTER TABLE lesson_content 
    ADD COLUMN difficulty_level INTEGER,
    ADD COLUMN estimated_time_minutes INTEGER;
```

## Service Functions

### lesson_sequence.check_lesson_unlocked()
```python
is_unlocked, missing_strict, missing_recommended = check_lesson_unlocked(
    db, user, lesson_id
)
```

### lesson_sequence.get_next_lesson()
```python
next_lesson_dict = get_next_lesson(db, user, urn_id=None)
```

### lesson_sequence.get_lesson_prerequisites()
```python
prereqs_dict = get_lesson_prerequisites(db, user, lesson_id)
```

### lesson_sequence.get_lesson_sequence()
```python
sequence_dict = get_lesson_sequence(db, user, urn_id=None)
```

## Example Usage

### cURL: Get next lesson
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/next" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### cURL: Check if lesson unlocked
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/{LESSON_ID}/is-unlocked" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python: Get learning sequence
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/lessons/sequence",
    headers={"Authorization": f"Bearer {token}"},
    params={"urn_id": urn_id}  # optional
)
sequence = response.json()
print(f"Progress: {sequence['completed_lessons']}/{sequence['total_lessons']}")
```

## Migration

Apply migration:
```bash
alembic upgrade head
```

Or using Docker:
```bash
docker-compose exec backend alembic upgrade head
```

## Testing

Run test script:
```bash
chmod +x test_lesson_prerequisites.sh
./test_lesson_prerequisites.sh
```

