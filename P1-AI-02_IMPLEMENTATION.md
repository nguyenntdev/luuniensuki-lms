# P1-AI-02: Context-Aware Quiz Hints Implementation

## Overview

Implementation of context-aware quiz hints using AI + RAG to help users understand quiz questions better. The system provides three types of hints with different heart costs and uses RAG to provide contextually relevant educational content.

## Components Implemented

### 1. Database Models (backend/models.py)

#### New Enum: HintType
```python
class HintType(str, Enum):
    explain = "explain"      # Explain concept (0 hearts)
    clue = "clue"           # Subtle hint (1 heart)
    elimination = "elimination"  # Remove wrong answer (2 hearts)
```

#### New Model: QuizHintRequest
```python
class QuizHintRequest(Base):
    __tablename__ = "quiz_hint_requests"
    
    # Core fields
    id: UUID (primary key)
    user_id: UUID (FK to users)
    question_id: UUID (FK to quiz_questions)
    hint_type: str (explain, clue, elimination)
    hint_text: str (AI-generated hint)
    heart_cost: int (hearts spent)
    rag_sources: JSONB (RAG documents used)
    created_at: datetime
    
    # Indexes
    - idx_quiz_hints_user
    - idx_quiz_hints_question
    - idx_quiz_hints_created
```

#### Updated HeartTransactionReason
Added `quiz_hint` to track heart deductions for hints.

### 2. Service Layer (backend/services/quiz_hints.py)

#### Core Functions

**`get_hint_cost(hint_type)`**
- Returns heart cost for each hint type
- explain: 0 hearts (free educational content)
- clue: 1 heart
- elimination: 2 hearts

**`can_request_hint(db, user, question_id, hint_type)`**
- Validates if user can request a hint
- Checks:
  - Question exists
  - User has enough hearts
  - Hint type not already used for this question
- Returns: (can_request: bool, reason: str)

**`get_question_hints(db, user, question_id)`**
- Retrieves all hints user has requested for a question
- Returns list ordered by creation time

**`generate_hint_with_ai(db, question, hint_type, rag_sources, call_deepseek_fn)`**
- Generates AI-powered hints based on type
- Uses RAG sources for context
- Prompts tailored to each hint type:
  - **explain**: Explains concept without revealing answer
  - **clue**: Provides subtle guidance
  - **elimination**: Not AI-based (handled separately)

**`eliminate_wrong_answer(question, previous_hints)`**
- Removes one wrong answer from options
- Tracks previously eliminated options
- Returns hint text and eliminated options list

**`create_hint_request(db, user, question_id, hint_type, collect_ai_sources_fn, call_deepseek_fn)`**
- Main function to create a hint request
- Steps:
  1. Validate hint request
  2. Collect RAG sources
  3. Generate hint (AI or elimination)
  4. Deduct hearts if needed
  5. Store hint request
- Returns: QuizHintRequest object

### 3. API Schemas (backend/schemas.py)

**QuizHintRequestIn**
```python
{
    "hint_type": str  # "explain" | "clue" | "elimination"
}
```

**QuizHintOut**
```python
{
    "id": UUID,
    "question_id": UUID,
    "hint_type": str,
    "hint_text": str,
    "heart_cost": int,
    "created_at": datetime,
    "rag_sources": Optional[Any]  # RAG metadata
}
```

**QuizHintsListOut**
```python
{
    "hints": List[QuizHintOut],
    "total": int
}
```

### 4. API Endpoints (backend/main.py)

#### POST /api/v1/quiz/questions/{question_id}/hint
Request a context-aware hint for a quiz question.

**Request:**
```json
{
    "hint_type": "clue"
}
```

**Response:**
```json
{
    "id": "uuid",
    "question_id": "uuid",
    "hint_type": "clue",
    "hint_text": "Hãy nghĩ về ý nghĩa biểu tượng của họa tiết...",
    "heart_cost": 1,
    "created_at": "2025-01-20T12:00:00Z",
    "rag_sources": [...]
}
```

**Status Codes:**
- 200: Success
- 400: Invalid hint type or already used
- 404: Question not found
- 500: Heart deduction failed

#### GET /api/v1/quiz/questions/{question_id}/hints
Get all hints user has requested for a question.

**Response:**
```json
{
    "hints": [
        {
            "id": "uuid",
            "question_id": "uuid",
            "hint_type": "explain",
            "hint_text": "...",
            "heart_cost": 0,
            "created_at": "2025-01-20T11:00:00Z"
        }
    ],
    "total": 1
}
```

### 5. Database Migration (migrations/versions/0027_quiz_hints.py)

**Upgrade:**
- Creates HintType enum
- Adds 'quiz_hint' to HeartTransactionReason enum
- Creates quiz_hint_requests table
- Creates indexes for performance

**Downgrade:**
- Drops indexes
- Drops quiz_hint_requests table
- Note: Enum values cannot be easily removed

## Hint Generation Strategy

### Explain Hints (0 hearts)
- **Purpose**: Educational, helps understanding
- **AI Prompt**: "Explain the concept WITHOUT giving the answer"
- **Context**: Uses RAG sources about the motif
- **Example**: "Họa tiết Rồng thường xuất hiện trên các đỉnh Cửu Đỉnh vì..."

### Clue Hints (1 heart)
- **Purpose**: Subtle guidance
- **AI Prompt**: "Give subtle clue pointing to correct answer"
- **Context**: Uses RAG + correct answer
- **Example**: "Hãy nghĩ về vị trí của họa tiết trên đỉnh..."

### Elimination Hints (2 hearts)
- **Purpose**: Reduce options
- **Logic**: Removes one wrong answer
- **Tracking**: Stores eliminated options in rag_sources
- **Example**: "Đáp án 'X' đã được loại bỏ vì không đúng"

## RAG Integration

### Source Collection
- Uses `_collect_ai_sources` function
- Collects from:
  1. Motif information
  2. Lesson content
  3. Urn descriptions
  4. RAG documents (with semantic search if enabled)
- Top 5-6 sources used for context

### Source Storage
Hint requests store RAG source metadata:
```json
{
    "rag_sources": [
        {
            "type": "motif",
            "id": "uuid",
            "title": "Rồng",
            "content": "..."
        },
        {
            "type": "lesson",
            "id": "uuid",
            "title": "Bài học: Rồng",
            "content": "..."
        }
    ]
}
```

For elimination hints:
```json
{
    "rag_sources": {
        "eliminated_options": ["option1", "option2"],
        "sources": [...]
    }
}
```

## Hearts System Integration

### Heart Costs
- Integrated with existing hearts service
- Uses `use_heart()` function with reason `quiz_hint`
- Transaction metadata includes:
  - question_id
  - hint_type

### Validation
- Checks unlimited hearts mode
- Verifies sufficient hearts before generating hint
- Prevents duplicate hint types per question

## Usage Flow

### User Requests Hint
1. User clicks "Get Hint" on quiz question
2. Selects hint type (explain/clue/elimination)
3. System checks:
   - Question exists and is accessible
   - User has enough hearts
   - Haven't used this hint type before
4. If valid:
   - Collects RAG sources about the topic
   - Generates AI hint (or eliminates answer)
   - Deducts hearts (if applicable)
   - Returns hint to user
5. User sees hint and can request other types

### View Previous Hints
1. User can view all hints for a question
2. Shows hint type, text, cost, and timestamp
3. Can reference hints when answering

## Error Handling

### Validation Errors (400)
- "Invalid hint_type. Must be one of: explain, clue, elimination"
- "You have already used this hint type for this question"
- "Not enough hearts. Need X, have Y"

### Not Found Errors (404)
- "Question not found"

### System Errors (500)
- "Failed to deduct hearts"
- AI API failures (with fallback)

## AI Fallbacks

If DeepSeek API fails:
- **explain**: "Hãy xem lại bài học về chủ đề này để hiểu rõ hơn."
- **clue**: "Hãy suy nghĩ kỹ về ý nghĩa và bối cảnh của câu hỏi."
- **elimination**: Returns system message (not AI-based)

## Testing Checklist

### Manual Testing
- [ ] Request explain hint (0 hearts)
- [ ] Request clue hint (1 heart)
- [ ] Request elimination hint (2 hearts)
- [ ] Verify hearts deducted correctly
- [ ] Try requesting same hint type twice (should fail)
- [ ] View hint history for question
- [ ] Test with insufficient hearts
- [ ] Test with unlimited hearts
- [ ] Verify RAG sources included in response
- [ ] Check eliminated options stored correctly

### API Testing
```bash
# Get access token first
TOKEN="your_token"
QUESTION_ID="quiz_question_uuid"

# Request explain hint (free)
curl -X POST "http://localhost:8000/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}'

# Request clue hint (1 heart)
curl -X POST "http://localhost:8000/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "clue"}'

# Request elimination hint (2 hearts)
curl -X POST "http://localhost:8000/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "elimination"}'

# Get hint history
curl -X GET "http://localhost:8000/api/v1/quiz/questions/$QUESTION_ID/hints" \
  -H "Authorization: Bearer $TOKEN"
```

## Database Queries

### Check hint usage
```sql
SELECT
    h.hint_type,
    h.hint_text,
    h.heart_cost,
    h.created_at,
    u.display_name,
    q.question_text
FROM quiz_hint_requests h
JOIN users u ON h.user_id = u.id
JOIN quiz_questions q ON h.question_id = q.id
ORDER BY h.created_at DESC
LIMIT 10;
```

### Count hints by type
```sql
SELECT
    hint_type,
    COUNT(*) as count,
    SUM(heart_cost) as total_hearts_spent
FROM quiz_hint_requests
GROUP BY hint_type;
```

### User hint statistics
```sql
SELECT
    u.display_name,
    COUNT(DISTINCT h.question_id) as questions_with_hints,
    COUNT(*) as total_hints,
    SUM(h.heart_cost) as total_hearts_spent
FROM quiz_hint_requests h
JOIN users u ON h.user_id = u.id
GROUP BY u.id, u.display_name
ORDER BY total_hints DESC;
```

## Future Enhancements

1. **Adaptive Hint Quality**
   - Adjust hint difficulty based on user skill level
   - More detailed hints for beginners

2. **Hint Effectiveness Tracking**
   - Track if user answered correctly after hint
   - Improve hint generation based on effectiveness

3. **Multiple Clues**
   - Allow multiple clue hints with increasing cost
   - First clue: 1 heart, second clue: 2 hearts

4. **Hint Sharing**
   - Allow users to rate helpful hints
   - Show community-rated hints

5. **Smart Elimination**
   - Use AI to eliminate most confusing wrong answer
   - Prioritize elimination based on common mistakes

## Implementation Notes

- All hint generation is async-safe
- RAG sources cached in hint record for audit
- Heart transactions logged for transparency
- Hints immutable once created
- Supports guest mode (if implemented)

