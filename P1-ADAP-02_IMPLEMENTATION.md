# P1-ADAP-02: Adaptive Quiz System Implementation

## Overview

This document describes the implementation of adaptive difficulty adjustment for quizzes based on user skill levels. The system uses an ELO-like rating algorithm to track user proficiency across different skill types and dynamically adjust quiz difficulty.

## Architecture

### Components

1. **UserSkillLevel Model** - Tracks user proficiency across skill types
2. **Adaptive Quiz Service** - Core logic for skill calculation and question selection
3. **API Endpoints** - RESTful endpoints for adaptive quiz functionality
4. **Database Migration** - Schema changes to support adaptive learning

## Database Schema

### New Enum: SkillType

```python
class SkillType(str, Enum):
    motif_recognition = "motif_recognition"
    history_knowledge = "history_knowledge"
    cultural_understanding = "cultural_understanding"
```

### New Model: UserSkillLevel

Tracks user skill level for each skill type.

**Fields:**
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `skill_type`: Skill type (from SkillType enum)
- `skill_level`: Float (0.0 to 1.0, starts at 0.5)
- `total_questions`: Total questions answered for this skill
- `correct_answers`: Number of correct answers
- `last_updated_at`: Last update timestamp
- `created_at`: Creation timestamp

**Constraints:**
- Unique constraint on (user_id, skill_type)
- Cascading delete on user deletion

**Indexes:**
- `idx_user_skill_user` on user_id
- `idx_user_skill_type` on skill_type

### Modified Model: QuizQuestion

**New Field:**
- `skill_type`: Optional string field to categorize questions by skill type

## Adaptive Learning Algorithm

### ELO-like Rating System

The skill level adjustment uses an ELO-like algorithm:

**Constants:**
- `K_FACTOR = 0.1`: Learning rate for skill updates
- `MIN_SKILL_LEVEL = 0.0`: Minimum skill level
- `MAX_SKILL_LEVEL = 1.0`: Maximum skill level
- `DEFAULT_SKILL_LEVEL = 0.5`: Starting skill level
- `DIFFICULTY_TOLERANCE = 0.15`: Range for question selection

**Algorithm:**
1. Normalize question difficulty (1-5 integer) to float (0.0-1.0)
2. Calculate expected performance based on skill level vs question difficulty
3. Update skill level: `new_skill = old_skill + K_FACTOR * (actual - expected)`
4. Clamp result to [0.0, 1.0] range

### Question Selection

Questions are selected within a tolerance range of the user's skill level:
- `min_difficulty = skill_level - 0.15`
- `max_difficulty = skill_level + 0.15`

This ensures questions are neither too easy nor too hard, promoting optimal learning.

## API Endpoints

### 1. GET /api/v1/quiz/adaptive

Get adaptive quiz questions based on user's skill level.

**Query Parameters:**
- `motif_id` (optional): UUID - Filter questions by motif
- `skill_type` (optional): string - Filter by skill type (motif_recognition, history_knowledge, cultural_understanding)
- `limit` (optional): int (1-50, default 10) - Number of questions to return

**Response:**
```json
{
  "motif_id": "uuid or null",
  "skill_type": "string or null",
  "recommended_difficulty": 0.65,
  "questions": [
    {
      "id": "uuid",
      "question_text": "string",
      "question_type": "multiple_choice",
      "options": [...],
      "target_mesh_name": "string or null",
      "explanation": "string or null"
    }
  ]
}
```

### 2. GET /api/v1/skills

Get user's skill levels across all skill types.

**Response:**
```json
{
  "skills": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "skill_type": "motif_recognition",
      "skill_level": 0.65,
      "total_questions": 45,
      "correct_answers": 38,
      "accuracy": 84.4,
      "last_updated_at": "2025-01-20T10:00:00Z",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "overall_level": 0.62
}
```

### 3. POST /api/v1/skills/recalculate

Recalculate user's skill levels from quiz attempt history.

**Response:** Same as GET /api/v1/skills

## Service Functions

### backend/services/adaptive_quiz.py

**Functions:**

1. `normalize_difficulty(difficulty: int) -> float`
   - Converts integer difficulty (1-5) to normalized float (0.0-1.0)

2. `get_user_skill_level(db, user_id, skill_type) -> UserSkillLevel`
   - Get or create user skill level for a skill type
   - Creates new entry with default 0.5 if not exists

3. `update_skill_level(db, user_id, skill_type, question_difficulty, is_correct) -> UserSkillLevel`
   - Updates skill level using ELO-like algorithm
   - Increments statistics (total_questions, correct_answers)

4. `get_recommended_difficulty(db, user_id, skill_type) -> float`
   - Returns recommended difficulty for user

5. `get_adaptive_questions(db, user_id, motif_id, skill_type, limit) -> list[QuizQuestion]`
   - Selects questions matching user's skill level
   - Applies filters and randomizes results

6. `recalculate_user_skills(db, user_id) -> list[UserSkillLevel]`
   - Replays all quiz attempts to recalculate skill levels
   - Useful for backfilling or recalibration

## Integration with Quiz Submission

The quiz submission endpoint (`POST /api/v1/quizzes/submit`) has been enhanced to automatically update skill levels when a quiz is submitted. For each question answered:

1. Check if the question has a `skill_type` assigned
2. Call `update_skill_level()` with the result
3. Log warnings if skill update fails (non-blocking)

This ensures skill levels are continuously updated as users practice.

## Migration

Run the migration to create the necessary database schema:

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

## Testing

### Manual Testing

1. **Get adaptive quiz questions:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/quiz/adaptive?skill_type=motif_recognition&limit=5"
```

2. **Get user skills:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/skills"
```

3. **Recalculate skills:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/skills/recalculate"
```

### Expected Behavior

- New users start with skill_level=0.5 for all skills
- Correct answers on hard questions increase skill level more
- Incorrect answers on easy questions decrease skill level more
- Skill level converges to user's true ability over time
- Questions are selected within ±0.15 of current skill level

## Files Created/Modified

### Created:
- `backend/services/adaptive_quiz.py` - Adaptive quiz service
- `backend/schemas.py` - Added UserSkillLevelOut, UserSkillsOut, AdaptiveQuizOut
- `migrations/versions/0025_adaptive_quiz.py` - Database migration

### Modified:
- `backend/models.py`:
  - Added SkillType enum
  - Added UserSkillLevel model
  - Added skill_type field to QuizQuestion
  - Added skill_levels relationship to User
- `backend/main.py`:
  - Added imports for SkillType and UserSkillLevel
  - Added GET /api/v1/quiz/adaptive endpoint
  - Added GET /api/v1/skills endpoint
  - Added POST /api/v1/skills/recalculate endpoint
  - Modified quiz submission to update skill levels

## Future Enhancements

1. **Difficulty Calibration**: Automatically assign skill_type to questions based on content analysis
2. **Learning Curve Analytics**: Track skill progression over time
3. **Personalized Recommendations**: Suggest content based on skill gaps
4. **Adaptive Practice Mode**: Generate practice sessions focused on weak skills
5. **Multi-dimensional Skills**: Track more granular skill categories
6. **Confidence Intervals**: Track uncertainty in skill estimates
7. **Decay Function**: Gradually decrease skill level over time without practice

## Conclusion

The adaptive quiz system is now implemented and ready for use. It provides a foundation for personalized learning experiences by tracking user proficiency and adjusting difficulty accordingly.


