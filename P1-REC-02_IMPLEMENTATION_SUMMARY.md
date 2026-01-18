# P1-REC-02: Lesson Prerequisites and Next Lesson Implementation

## Overview

This document describes the implementation of P1-REC-02, which adds prerequisite logic and "next lesson" recommendations to the LMS.

## Implementation Summary

### 1. Database Models

#### New Model: `LessonPrerequisite`
- **Table**: `lesson_prerequisites`
- **Purpose**: Define prerequisite relationships between lessons
- **Fields**:
  - `id`: UUID primary key
  - `lesson_id`: FK to lesson_content (the lesson that requires prerequisites)
  - `prerequisite_lesson_id`: FK to lesson_content (the lesson that must be completed first)
  - `is_strict`: Boolean (true = must complete, false = recommended)
  - `created_at`: Timestamp
- **Constraints**:
  - UniqueConstraint on (lesson_id, prerequisite_lesson_id)
  - Indexes on both lesson_id and prerequisite_lesson_id

#### Updated Model: `LessonContent`
Added new fields:
- `difficulty_level`: Integer (1-5, nullable) - For ordering lessons by difficulty
- `estimated_time_minutes`: Integer (nullable) - Estimated completion time

### 2. Database Migration

**File**: `migrations/versions/0026_lesson_prerequisites.py`

The migration:
1. Adds `difficulty_level` and `estimated_time_minutes` columns to `lesson_content`
2. Creates `lesson_prerequisites` table with proper indexes and constraints
3. Includes downgrade logic to reverse changes

### 3. Service Layer

**File**: `backend/services/lesson_sequence.py`

#### Functions:

##### `check_lesson_unlocked(db, user, lesson_id)`
Checks if a lesson is unlocked for a user based on prerequisites.

**Returns**: `(is_unlocked, missing_strict_prerequisites, missing_recommended_prerequisites)`
- `is_unlocked`: Boolean - True if all strict prerequisites are met
- `missing_strict_prerequisites`: List of LessonContent objects that must be completed
- `missing_recommended_prerequisites`: List of LessonContent objects that are recommended

##### `get_next_lesson(db, user, urn_id=None)`
Gets the next recommended lesson for a user.

**Strategy**:
1. **Priority 1**: Continue in-progress lessons (status: discovered or learned)
2. **Priority 2**: Find next unlocked lesson, ordered by difficulty

**Filtering**:
- Excludes already mastered lessons
- Filters by urn if urn_id provided
- Only returns unlocked lessons

**Returns**: Dictionary with lesson info or None

##### `get_lesson_prerequisites(db, user, lesson_id)`
Gets all prerequisites for a lesson with completion status.

**Returns**: Dictionary containing:
- `lesson_id`: The lesson ID
- `prerequisites`: List of prerequisite info with completion status
- `all_prerequisites_met`: Boolean

##### `get_lesson_sequence(db, user, urn_id=None)`
Gets the full learning sequence for a user.

**Returns**: Dictionary containing:
- `urn_id`, `urn_name`: Urn context (if filtered)
- `total_lessons`: Total number of lessons
- `completed_lessons`: Number completed by user
- `current_position`: Furthest position reached
- `sequence`: Ordered list of lessons with unlock/completion status

### 4. API Endpoints

All endpoints require authentication.

#### GET `/api/v1/lessons/next`
Get next recommended lesson.

**Query Parameters**:
- `urn_id` (optional): Filter lessons from specific urn

**Response**: `NextLessonOut`
```json
{
  "lesson_id": "uuid",
  "motif_id": "uuid",
  "motif_name": "string",
  "motif_slug": "string",
  "urn_id": "uuid",
  "urn_name": "string",
  "difficulty_level": 1-5,
  "estimated_time_minutes": 30,
  "reason": "continue_learning | next_in_sequence | no_lessons_available",
  "has_prerequisites": false,
  "progress_status": "discovered | learned | mastered"
}
```

#### GET `/api/v1/lessons/{lesson_id}/prerequisites`
Get prerequisites for a specific lesson.

**Response**: `LessonPrerequisitesOut`
```json
{
  "lesson_id": "uuid",
  "prerequisites": [
    {
      "id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "difficulty_level": 1-5,
      "estimated_time_minutes": 30,
      "is_strict": true,
      "is_completed": false
    }
  ],
  "all_prerequisites_met": false
}
```

#### GET `/api/v1/lessons/{lesson_id}/is-unlocked`
Check if a lesson is unlocked for the user.

**Response**: `LessonUnlockStatusOut`
```json
{
  "lesson_id": "uuid",
  "is_unlocked": true,
  "missing_prerequisites": [],
  "recommended_prerequisites": []
}
```

#### GET `/api/v1/lessons/sequence`
Get the full learning sequence.

**Query Parameters**:
- `urn_id` (optional): Filter lessons from specific urn

**Response**: `LessonSequenceOut`
```json
{
  "urn_id": "uuid",
  "urn_name": "string",
  "total_lessons": 10,
  "completed_lessons": 3,
  "current_position": 3,
  "sequence": [
    {
      "lesson_id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "urn_id": "uuid",
      "urn_name": "string",
      "difficulty_level": 1,
      "estimated_time_minutes": 30,
      "is_unlocked": true,
      "is_completed": true,
      "progress_status": "mastered",
      "position": 1
    }
  ]
}
```

### 5. Schemas

**File**: `backend/schemas.py`

New schemas added:
- `LessonPrerequisiteOut`
- `PrerequisiteLessonInfo`
- `LessonPrerequisitesOut`
- `LessonUnlockStatusOut`
- `NextLessonOut`
- `LessonSequenceItem`
- `LessonSequenceOut`

## Use Cases

### 1. Mobile App: Continue Learning
```python
# Get next lesson for user
response = requests.get(
    "/api/v1/lessons/next",
    headers={"Authorization": f"Bearer {token}"}
)
next_lesson = response.json()
if next_lesson["lesson_id"]:
    # Navigate to lesson
    navigate_to_lesson(next_lesson["lesson_id"])
```

### 2. Show Learning Path Progress
```python
# Get full sequence
response = requests.get(
    "/api/v1/lessons/sequence",
    headers={"Authorization": f"Bearer {token}"}
)
sequence = response.json()
# Display progress: 3/10 lessons completed
print(f"{sequence['completed_lessons']}/{sequence['total_lessons']} lessons")
```

### 3. Check Prerequisites Before Starting
```python
# Before starting a lesson, check if unlocked
response = requests.get(
    f"/api/v1/lessons/{lesson_id}/is-unlocked",
    headers={"Authorization": f"Bearer {token}"}
)
unlock_status = response.json()
if not unlock_status["is_unlocked"]:
    # Show locked state with missing prerequisites
    show_locked_ui(unlock_status["missing_prerequisites"])
```

## Files Modified

1. **backend/models.py**: Added LessonPrerequisite model and fields to LessonContent
2. **backend/schemas.py**: Added prerequisite-related schemas
3. **backend/main.py**: Added 4 new API endpoints
4. **backend/services/lesson_sequence.py**: New service file (created)
5. **migrations/versions/0026_lesson_prerequisites.py**: Database migration (created)

## Testing

Run the test script:
```bash
chmod +x test_lesson_prerequisites.sh
./test_lesson_prerequisites.sh
```

The script tests:
- Getting next lesson (with and without urn filter)
- Getting full lesson sequence
- Checking lesson prerequisites
- Checking lesson unlock status

## Future Enhancements

1. **Admin UI**: Add interface to manage prerequisites
2. **Adaptive Difficulty**: Adjust difficulty based on user performance
3. **Skill Trees**: Visual representation of prerequisite chains
4. **Alternative Paths**: Allow multiple prerequisite options (A OR B)
5. **Time-Based Unlocks**: Unlock lessons after certain time periods

