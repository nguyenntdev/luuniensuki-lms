# P1-ADAP-02 Quick Reference

## API Endpoints

### Get Adaptive Quiz
```
GET /api/v1/quiz/adaptive
Query Params: ?motif_id=<uuid>&skill_type=<type>&limit=<int>
Auth: Required
```

### Get User Skills
```
GET /api/v1/skills
Auth: Required
```

### Recalculate Skills
```
POST /api/v1/skills/recalculate
Auth: Required
```

## Skill Types

- `motif_recognition` - Visual pattern recognition
- `history_knowledge` - Historical facts and context
- `cultural_understanding` - Cultural significance and symbolism

## Key Constants

- **Default Skill Level:** 0.5
- **Skill Range:** 0.0 to 1.0
- **K-Factor (Learning Rate):** 0.1
- **Difficulty Tolerance:** ±0.15

## Skill Level Interpretation

| Skill Level | Description |
|-------------|-------------|
| 0.0 - 0.3   | Beginner    |
| 0.3 - 0.5   | Novice      |
| 0.5 - 0.7   | Intermediate|
| 0.7 - 0.9   | Advanced    |
| 0.9 - 1.0   | Expert      |

## Database Tables

### user_skill_levels
- Tracks skill progression per user per skill type
- Unique constraint on (user_id, skill_type)

### quiz_questions (modified)
- Added optional `skill_type` field
- Links questions to skill categories

## Example Responses

### Adaptive Quiz Response
```json
{
  "motif_id": null,
  "skill_type": "motif_recognition",
  "recommended_difficulty": 0.65,
  "questions": [...]
}
```

### User Skills Response
```json
{
  "skills": [
    {
      "skill_type": "motif_recognition",
      "skill_level": 0.65,
      "total_questions": 45,
      "correct_answers": 38,
      "accuracy": 84.4
    }
  ],
  "overall_level": 0.62
}
```

## Workflow

1. User requests adaptive quiz
2. System retrieves user's skill level (creates if new)
3. Questions are selected within difficulty range
4. User submits quiz
5. System updates skill levels based on performance
6. Repeat for continuous learning

## Files

- **Model:** `backend/models.py` (UserSkillLevel, SkillType)
- **Service:** `backend/services/adaptive_quiz.py`
- **Schemas:** `backend/schemas.py`
- **Endpoints:** `backend/main.py`
- **Migration:** `migrations/versions/0025_adaptive_quiz.py`

