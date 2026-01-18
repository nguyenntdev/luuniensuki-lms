# P1-AI-02: Quiz Hints - Quick Reference

## API Endpoints

### Request Hint
```
POST /api/v1/quiz/questions/{question_id}/hint
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "hint_type": "explain" | "clue" | "elimination"
}

Response: QuizHintOut
```

### Get Hint History
```
GET /api/v1/quiz/questions/{question_id}/hints
Authorization: Bearer <token>

Response: QuizHintsListOut
```

## Hint Types & Costs

| Type        | Cost (Hearts) | Description                          | Example                                      |
|-------------|---------------|--------------------------------------|----------------------------------------------|
| explain     | 0 (FREE)      | Explains concept without answer      | "Họa tiết Rồng biểu thị quyền lực..."       |
| clue        | 1             | Subtle hint towards correct answer   | "Nghĩ về vị trí của họa tiết trên đỉnh..."  |
| elimination | 2             | Removes one wrong answer             | "Đáp án 'X' đã được loại bỏ"                |

## Business Rules

1. **One Hint Per Type**: User can only request each hint type once per question
2. **Heart Deduction**: Hearts deducted before hint generation
3. **RAG Context**: All hints use RAG sources for accuracy
4. **Unlimited Hearts**: Users with unlimited hearts can request hints freely
5. **Fallback**: If AI fails, provides basic fallback hints

## Integration Points

### Hearts Service
```python
from backend.services.hearts import use_heart, HeartTransactionReason

success, user_hearts = use_heart(
    db, user, now,
    reason=HeartTransactionReason.quiz_hint,
    metadata={"question_id": str(question_id), "hint_type": hint_type.value}
)
```

### RAG Sources
```python
rag_sources = _collect_ai_sources(
    db,
    motif_id=question.motif_id,
    query=question.question_text,
    limit=6,
)
```

### AI Generation
```python
hint_text = generate_hint_with_ai(
    db, question, hint_type, rag_sources, _call_deepseek_chat
)
```

## Database Schema

### Table: quiz_hint_requests
```sql
CREATE TABLE quiz_hint_requests (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES quiz_questions(id) ON DELETE CASCADE,
    hint_type VARCHAR(20) NOT NULL,
    hint_text TEXT NOT NULL,
    heart_cost INTEGER DEFAULT 0,
    rag_sources JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_quiz_hints_user ON quiz_hint_requests(user_id);
CREATE INDEX idx_quiz_hints_question ON quiz_hint_requests(question_id);
CREATE INDEX idx_quiz_hints_created ON quiz_hint_requests(created_at);
```

## Error Codes

| Code | Message                                           | Reason                              |
|------|---------------------------------------------------|-------------------------------------|
| 400  | Invalid hint_type                                 | Unknown hint type                   |
| 400  | You have already used this hint type              | Duplicate hint type for question    |
| 400  | Not enough hearts. Need X, have Y                 | Insufficient hearts                 |
| 404  | Question not found                                | Invalid question_id                 |
| 500  | Failed to deduct hearts                           | Hearts service error                |

## Example Requests

### Python
```python
import requests

# Request clue hint
response = requests.post(
    f"https://api.example.com/api/v1/quiz/questions/{question_id}/hint",
    headers={"Authorization": f"Bearer {token}"},
    json={"hint_type": "clue"}
)
hint = response.json()
print(f"Hint: {hint['hint_text']}")
print(f"Cost: {hint['heart_cost']} hearts")

# Get all hints for question
response = requests.get(
    f"https://api.example.com/api/v1/quiz/questions/{question_id}/hints",
    headers={"Authorization": f"Bearer {token}"}
)
hints = response.json()
print(f"Total hints used: {hints['total']}")
```

### cURL
```bash
# Request explain hint (free)
curl -X POST "https://api.example.com/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}'

# Get hints
curl "https://api.example.com/api/v1/quiz/questions/$QUESTION_ID/hints" \
  -H "Authorization: Bearer $TOKEN"
```

## Migration

Run migration:
```bash
cd /path/to/luuniensuki-lms
alembic upgrade head
```

Verify migration:
```bash
alembic current
# Should show: 0027_quiz_hints (head)
```

Rollback if needed:
```bash
alembic downgrade -1
```

## Monitoring Queries

### Recent hint usage
```sql
SELECT 
    h.hint_type,
    COUNT(*) as count,
    AVG(h.heart_cost) as avg_cost
FROM quiz_hint_requests h
WHERE h.created_at > NOW() - INTERVAL '24 hours'
GROUP BY h.hint_type;
```

### Top users by hint usage
```sql
SELECT 
    u.display_name,
    COUNT(*) as hints_used,
    SUM(h.heart_cost) as hearts_spent
FROM quiz_hint_requests h
JOIN users u ON h.user_id = u.id
GROUP BY u.id, u.display_name
ORDER BY hints_used DESC
LIMIT 10;
```

### Hints per question
```sql
SELECT 
    q.question_text,
    COUNT(*) as hint_requests,
    ARRAY_AGG(DISTINCT h.hint_type) as hint_types_used
FROM quiz_hint_requests h
JOIN quiz_questions q ON h.question_id = q.id
GROUP BY q.id, q.question_text
ORDER BY hint_requests DESC
LIMIT 10;
```

## Service Functions

### Core Functions
- `get_hint_cost(hint_type)` - Get heart cost for hint type
- `can_request_hint(db, user, question_id, hint_type)` - Validate hint request
- `get_question_hints(db, user, question_id)` - Get user's hints for question
- `create_hint_request(...)` - Main function to create hint
- `generate_hint_with_ai(...)` - Generate AI hint
- `eliminate_wrong_answer(...)` - Handle elimination logic

## File Locations

- **Model**: `backend/models.py` (line ~880, ~138)
- **Service**: `backend/services/quiz_hints.py`
- **Schemas**: `backend/schemas.py` (line ~335)
- **Endpoints**: `backend/main.py` (line ~6900)
- **Migration**: `migrations/versions/0027_quiz_hints.py`

