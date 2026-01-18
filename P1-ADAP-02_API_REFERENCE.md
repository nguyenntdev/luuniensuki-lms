# P1-ADAP-02: Adaptive Quiz System - API Reference

## Overview

The Adaptive Quiz System provides personalized quiz questions based on user skill levels and automatically adjusts difficulty as users practice.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

---

## Endpoints

### 1. Get Adaptive Quiz Questions

Retrieves quiz questions matched to the user's skill level.

**Endpoint:** `GET /quiz/adaptive`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| motif_id | UUID | No | null | Filter questions by specific motif |
| skill_type | string | No | null | Filter by skill type (see Skill Types below) |
| limit | integer | No | 10 | Number of questions (1-50) |

**Skill Types:**
- `motif_recognition` - Visual pattern and motif identification
- `history_knowledge` - Historical facts and context
- `cultural_understanding` - Cultural significance and symbolism

**Success Response: 200 OK**
```json
{
  "motif_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "skill_type": "motif_recognition",
  "recommended_difficulty": 0.65,
  "questions": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "question_text": "Identify the main motif in this image",
      "question_type": "multiple_choice",
      "options": [
        {
          "id": "a",
          "text": "Dragon",
          "image_url": null
        },
        {
          "id": "b",
          "text": "Phoenix",
          "image_url": null
        }
      ],
      "target_mesh_name": null,
      "explanation": "This is a dragon motif commonly found in Cao Dinh urns"
    }
  ]
}
```

**Error Responses:**

400 Bad Request - Invalid skill_type
```json
{
  "detail": "Invalid skill_type. Must be one of: motif_recognition, history_knowledge, cultural_understanding"
}
```

404 Not Found - No questions available
```json
{
  "detail": "No questions found matching your skill level"
}
```

**Example Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/quiz/adaptive?skill_type=motif_recognition&limit=5"
```

---

### 2. Get User Skills

Retrieves the user's skill levels across all skill types.

**Endpoint:** `GET /skills`

**Query Parameters:** None

**Success Response: 200 OK**
```json
{
  "skills": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "skill_type": "motif_recognition",
      "skill_level": 0.65,
      "total_questions": 45,
      "correct_answers": 38,
      "accuracy": 84.4,
      "last_updated_at": "2025-01-20T10:30:00Z",
      "created_at": "2025-01-15T08:00:00Z"
    },
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
      "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "skill_type": "history_knowledge",
      "skill_level": 0.58,
      "total_questions": 32,
      "correct_answers": 25,
      "accuracy": 78.1,
      "last_updated_at": "2025-01-19T14:20:00Z",
      "created_at": "2025-01-15T08:00:00Z"
    },
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
      "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "skill_type": "cultural_understanding",
      "skill_level": 0.62,
      "total_questions": 28,
      "correct_answers": 22,
      "accuracy": 78.6,
      "last_updated_at": "2025-01-18T11:15:00Z",
      "created_at": "2025-01-15T08:00:00Z"
    }
  ],
  "overall_level": 0.62
}
```

**Example Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/skills"
```

---

### 3. Recalculate User Skills

Recalculates all skill levels from quiz attempt history. Useful for backfilling data or recalibrating skills.

**Endpoint:** `POST /skills/recalculate`

**Request Body:** None

**Success Response: 200 OK**

Same response format as GET /skills

**Example Request:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/skills/recalculate"
```

---

## Automatic Skill Updates

When a user submits a quiz via `POST /quizzes/submit`, skill levels are automatically updated for each question that has a `skill_type` assigned. This happens transparently in the background.

**Process:**
1. User submits quiz with answers
2. Each answer is checked for correctness
3. If question has a skill_type, skill level is updated using ELO-like algorithm
4. Skill statistics (total_questions, correct_answers) are incremented
5. Quiz submission completes normally

---

## Skill Level Interpretation

| Range | Level | Description |
|-------|-------|-------------|
| 0.0 - 0.3 | Beginner | Just starting, needs easy questions |
| 0.3 - 0.5 | Novice | Basic understanding, moderate difficulty |
| 0.5 - 0.7 | Intermediate | Solid grasp, can handle harder questions |
| 0.7 - 0.9 | Advanced | Strong proficiency, prefers challenges |
| 0.9 - 1.0 | Expert | Master level, seeks hardest questions |

---

## Adaptive Algorithm Details

### Question Selection

Questions are selected within a difficulty range based on skill level:

- **Min Difficulty:** skill_level - 0.15
- **Max Difficulty:** skill_level + 0.15

Integer difficulty (1-5) is normalized to float (0.0-1.0):
- Difficulty 1 → 0.0
- Difficulty 2 → 0.25
- Difficulty 3 → 0.5
- Difficulty 4 → 0.75
- Difficulty 5 → 1.0

### Skill Update Algorithm

Uses an ELO-like rating system:

1. **Expected Performance** = 1.0 - |skill_level - question_difficulty|
2. **Actual Performance** = 1.0 (correct) or 0.0 (incorrect)
3. **Skill Delta** = K_FACTOR × (actual - expected)
4. **New Skill Level** = old_skill + delta (clamped to [0.0, 1.0])

Where K_FACTOR = 0.1 (learning rate)

**Examples:**
- Beginner (0.3) answers hard question (0.8) correctly → skill increases significantly
- Expert (0.9) answers easy question (0.2) incorrectly → skill decreases significantly
- Intermediate (0.5) answers medium question (0.5) correctly → small increase

---

## Usage Patterns

### Pattern 1: General Practice
```bash
# Get adaptive questions for general practice
GET /quiz/adaptive?limit=10
```

### Pattern 2: Skill-Specific Practice
```bash
# Focus on motif recognition
GET /quiz/adaptive?skill_type=motif_recognition&limit=5
```

### Pattern 3: Motif-Specific Study
```bash
# Study specific motif at appropriate difficulty
GET /quiz/adaptive?motif_id=<uuid>&limit=5
```

### Pattern 4: Monitor Progress
```bash
# Check skill levels regularly
GET /skills
```

### Pattern 5: Reset/Recalibrate
```bash
# Recalculate skills from history
POST /skills/recalculate
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | No questions found |
| 500 | Server error |

---

## Notes

- New users start with skill_level = 0.5 for all skills
- Skills are created on-demand when first accessed
- Skill levels update automatically during quiz submission
- Questions without skill_type assignment don't affect skill levels
- Recalculation replays all quiz attempts chronologically

---

## Implementation Files

- **Models:** `backend/models.py`
- **Service:** `backend/services/adaptive_quiz.py`
- **Schemas:** `backend/schemas.py`
- **Endpoints:** `backend/main.py`
- **Migration:** `migrations/versions/0025_adaptive_quiz.py`


