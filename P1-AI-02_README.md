# P1-AI-02: Context-Aware Quiz Hints (RAG-Powered)

## 🎯 Feature Overview

The Quiz Hints feature provides AI-powered, context-aware hints to help users understand quiz questions better. Using Retrieval-Augmented Generation (RAG), the system generates educational hints based on actual content from the LMS, ensuring accuracy and relevance.

## 🌟 Key Features

### Three Hint Types

1. **Explain (FREE - 0 hearts)**
   - Explains the underlying concept without revealing the answer
   - Educational focus - helps users learn
   - Example: _"Họa tiết Rồng thường xuất hiện trên các đỉnh Cửu Đỉnh vì biểu thị sức mạnh và quyền lực của vua chúa..."_

2. **Clue (1 heart)**
   - Provides a subtle hint pointing toward the correct answer
   - Helps users think critically
   - Example: _"Hãy nghĩ về vị trí đặc biệt của họa tiết này trên đỉnh và ý nghĩa biểu tượng của nó..."_

3. **Elimination (2 hearts)**
   - Removes one incorrect answer from the options
   - Reduces complexity for struggling users
   - Example: _"Đáp án 'Lá Sen' đã được loại bỏ vì không đúng"_

### RAG Integration

- **Smart Context**: Uses RAG to collect relevant information from:
  - Motif descriptions
  - Lesson content (historical context, symbolism, fun facts)
  - Urn information
  - Custom RAG documents
  
- **Semantic Search**: When enabled, uses embeddings to find most relevant context

- **Source Tracking**: Stores which RAG sources were used for each hint (audit trail)

### Hearts Economy

- Integrated with existing hearts system
- Free educational content (explain hints)
- Premium features cost hearts (clue, elimination)
- Transactions logged with metadata
- Respects unlimited hearts mode

### Smart Validation

- **One per type**: Users can only request each hint type once per question
- **Heart check**: Validates sufficient hearts before generation
- **Progress tracking**: Prevents hint spam

## 📁 Files Modified/Created

### New Files
- `backend/services/quiz_hints.py` - Core hint generation service
- `migrations/versions/0027_quiz_hints.py` - Database migration
- `test_quiz_hints.sh` - API testing script
- `P1-AI-02_IMPLEMENTATION.md` - Detailed implementation docs
- `P1-AI-02_QUICK_REFERENCE.md` - Quick reference guide
- `P1-AI-02_README.md` - This file

### Modified Files
- `backend/models.py` - Added HintType enum, QuizHintRequest model, updated HeartTransactionReason
- `backend/schemas.py` - Added QuizHintRequestIn, QuizHintOut, QuizHintsListOut
- `backend/main.py` - Added two new API endpoints

## 🚀 Getting Started

### 1. Run Migration

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

Verify:
```bash
alembic current
# Should show: 0027_quiz_hints (head)
```

### 2. Test the API

```bash
# Get a quiz question ID first
QUESTION_ID="<your-quiz-question-uuid>"
TOKEN="<your-access-token>"

# Test the endpoints
./test_quiz_hints.sh http://localhost:8000 $TOKEN $QUESTION_ID
```

### 3. Try it manually

```bash
# Request a free explain hint
curl -X POST "http://localhost:8000/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}'
```

## 📚 API Documentation

### POST /api/v1/quiz/questions/{question_id}/hint

Request a hint for a quiz question.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Body:**
```json
{
    "hint_type": "explain" | "clue" | "elimination"
}
```

**Response (200):**
```json
{
    "id": "uuid",
    "question_id": "uuid",
    "hint_type": "clue",
    "hint_text": "Hãy nghĩ về ý nghĩa biểu tượng...",
    "heart_cost": 1,
    "created_at": "2025-01-20T12:00:00Z",
    "rag_sources": [...]
}
```

**Errors:**
- `400`: Invalid hint type or already used
- `400`: Not enough hearts
- `404`: Question not found
- `500`: System error

### GET /api/v1/quiz/questions/{question_id}/hints

Get all hints requested for a question.

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "hints": [
        {
            "id": "uuid",
            "question_id": "uuid",
            "hint_type": "explain",
            "hint_text": "...",
            "heart_cost": 0,
            "created_at": "2025-01-20T11:00:00Z",
            "rag_sources": null
        }
    ],
    "total": 1
}
```

## 🎓 Usage Examples

### Python Client

```python
import requests

class QuizHintsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def request_hint(self, question_id: str, hint_type: str):
        """Request a hint for a question."""
        response = requests.post(
            f"{self.base_url}/api/v1/quiz/questions/{question_id}/hint",
            headers=self.headers,
            json={"hint_type": hint_type}
        )
        response.raise_for_status()
        return response.json()

    def get_hints(self, question_id: str):
        """Get all hints for a question."""
        response = requests.get(
            f"{self.base_url}/api/v1/quiz/questions/{question_id}/hints",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = QuizHintsClient("http://localhost:8000", "your-token")

# Get free explanation
explain_hint = client.request_hint(question_id, "explain")
print(f"Explanation: {explain_hint['hint_text']}")
print(f"Cost: {explain_hint['heart_cost']} hearts")

# Get subtle clue (costs 1 heart)
clue_hint = client.request_hint(question_id, "clue")
print(f"Clue: {clue_hint['hint_text']}")

# View all hints used
hints = client.get_hints(question_id)
print(f"Total hints used: {hints['total']}")
for hint in hints['hints']:
    print(f"- {hint['hint_type']}: {hint['hint_text'][:50]}...")
```

### Mobile Integration (Flutter/Dart)

```dart
class QuizHintsService {
  final ApiClient apiClient;

  Future<QuizHint> requestHint(String questionId, String hintType) async {
    final response = await apiClient.post(
      '/api/v1/quiz/questions/$questionId/hint',
      data: {'hint_type': hintType},
    );
    return QuizHint.fromJson(response.data);
  }

  Future<List<QuizHint>> getHints(String questionId) async {
    final response = await apiClient.get(
      '/api/v1/quiz/questions/$questionId/hints',
    );
    final data = response.data as Map<String, dynamic>;
    return (data['hints'] as List)
        .map((h) => QuizHint.fromJson(h))
        .toList();
  }
}
```

## 🔍 Monitoring & Analytics

### Track Hint Usage

```sql
-- Daily hint usage by type
SELECT
    DATE(created_at) as date,
    hint_type,
    COUNT(*) as requests,
    SUM(heart_cost) as hearts_spent
FROM quiz_hint_requests
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), hint_type
ORDER BY date DESC, requests DESC;

-- Questions that need most hints
SELECT
    q.question_text,
    COUNT(h.id) as hint_requests,
    ARRAY_AGG(DISTINCT h.hint_type) as hint_types
FROM quiz_hint_requests h
JOIN quiz_questions q ON h.question_id = q.id
GROUP BY q.id, q.question_text
HAVING COUNT(h.id) > 5
ORDER BY hint_requests DESC;

-- User engagement with hints
SELECT
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as total_hints,
    AVG(heart_cost) as avg_cost,
    SUM(CASE WHEN hint_type = 'explain' THEN 1 ELSE 0 END) as free_hints,
    SUM(CASE WHEN hint_type != 'explain' THEN 1 ELSE 0 END) as paid_hints
FROM quiz_hint_requests
WHERE created_at > NOW() - INTERVAL '7 days';
```

## 🧪 Testing Checklist

- [ ] Migration runs successfully
- [ ] Can request explain hint (0 hearts)
- [ ] Can request clue hint (1 heart deducted)
- [ ] Can request elimination hint (2 hearts deducted)
- [ ] Prevented from requesting same hint type twice
- [ ] Hearts properly deducted from balance
- [ ] Can view hint history for question
- [ ] Invalid hint type returns 400 error
- [ ] Invalid question ID returns 404 error
- [ ] Insufficient hearts returns 400 error
- [ ] Unlimited hearts mode works correctly
- [ ] RAG sources included in response
- [ ] Elimination correctly removes wrong answer
- [ ] AI fallback works when API fails

## 🐛 Troubleshooting

### Hint generation fails
- **Check**: DeepSeek API key configured (`DEEPSEEK_API_KEY`)
- **Check**: RAG documents exist in database
- **Fallback**: System provides basic hints if AI fails

### Hearts not deducting
- **Check**: User has UserHearts record (created automatically)
- **Check**: Heart transaction logged in database
- **Debug**: Check `heart_transactions` table

### Duplicate hint error
- **Expected**: Users can only use each hint type once per question
- **Check**: Existing hints in `quiz_hint_requests` table

## 📊 Performance Considerations

- **RAG Retrieval**: ~100-200ms for source collection
- **AI Generation**: ~1-3 seconds for hint generation
- **Database**: Indexed queries for fast lookup
- **Caching**: Consider caching RAG sources per motif

## 🔐 Security

- **Authentication**: All endpoints require valid JWT token
- **Authorization**: Users can only access their own hints
- **Validation**: Input validation prevents injection
- **Rate Limiting**: Consider adding rate limits for hint requests

## 🚧 Future Enhancements

1. **Adaptive Difficulty**: Adjust hint quality based on user skill level
2. **Effectiveness Tracking**: Track if hints lead to correct answers
3. **Community Hints**: Allow highly-rated hints to be shared
4. **Smart Elimination**: Use AI to eliminate most confusing option
5. **Hint Bundles**: Purchase multiple hints at discount
6. **Hint Achievements**: Badges for answering without hints

## 📞 Support

For issues or questions:
1. Check implementation docs: `P1-AI-02_IMPLEMENTATION.md`
2. Check quick reference: `P1-AI-02_QUICK_REFERENCE.md`
3. Run test script: `./test_quiz_hints.sh`
4. Check database migrations: `alembic current`

## ✅ Deployment Checklist

- [ ] Code reviewed and tested locally
- [ ] Migration tested on development database
- [ ] API endpoints tested with test script
- [ ] Documentation reviewed
- [ ] Hearts integration verified
- [ ] RAG sources validated
- [ ] Error handling tested
- [ ] Performance tested with multiple users
- [ ] Backup database before migration
- [ ] Run migration on production
- [ ] Monitor error logs after deployment
- [ ] Test all three hint types in production
- [ ] Verify hearts deduction working correctly

