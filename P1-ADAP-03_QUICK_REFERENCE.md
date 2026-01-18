# P1-ADAP-03: Daily Learning Path - Quick Reference

## 📋 API Endpoints

### 1. Get Today's Learning Path
```http
GET /api/v1/learning-path/today
Authorization: Bearer {token}
```

**Response Fields:**
- `lessons[]` - Recommended lessons to complete
- `reviews[]` - Due spaced repetition reviews  
- `quizzes[]` - Practice quizzes
- `estimated_time_minutes` - Total time needed
- `progress` - Completion stats

### 2. Force Regenerate Path
```http
POST /api/v1/learning-path/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "force_regenerate": true,
  "target_date": "2025-01-16T00:00:00Z"  // optional
}
```

### 3. Mark Item Complete
```http
POST /api/v1/learning-path/complete-item
Authorization: Bearer {token}
Content-Type: application/json

{
  "item_type": "lesson",  // or "review" or "quiz"
  "item_id": "uuid"
}
```

### 4. Get Path History
```http
GET /api/v1/learning-path/history?days=30
Authorization: Bearer {token}
```

### 5. Get Path Statistics
```http
GET /api/v1/learning-path/stats?days=30
Authorization: Bearer {token}
```

## 🧮 Algorithm Constants

```python
# Maximum items per day
MAX_LESSONS_PER_DAY = 3
MAX_REVIEWS_PER_DAY = 10
MAX_QUIZZES_PER_DAY = 5

# Time estimates (minutes)
LESSON_TIME_MINUTES = 10
REVIEW_TIME_MINUTES = 3
QUIZ_TIME_MINUTES = 5

# Review intervals based on quiz score
90%+ score → 14 days
80-89% score → 7 days  
60-79% score → 3 days
<60% score → 1 day
```

## 📊 Database Schema

```sql
CREATE TABLE user_learning_paths (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    path_date TIMESTAMP WITH TIME ZONE NOT NULL,
    recommended_lessons JSONB DEFAULT '[]',
    recommended_reviews JSONB DEFAULT '[]',
    recommended_quizzes JSONB DEFAULT '[]',
    estimated_time_minutes INTEGER DEFAULT 0,
    completed_items JSONB DEFAULT '[]',
    is_completed BOOLEAN DEFAULT false,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, path_date)
);

CREATE INDEX idx_learning_path_user ON user_learning_paths(user_id);
CREATE INDEX idx_learning_path_date ON user_learning_paths(path_date);
CREATE INDEX idx_learning_path_completed ON user_learning_paths(is_completed);
```

## 🎯 Service Functions

```python
from backend.services import learning_path as lp_service

# Get or create today's path
path = lp_service.get_todays_learning_path(db, user, now)

# Force generate new path
path = lp_service.generate_learning_path(db, user, path_date, now)

# Mark item complete
result = lp_service.complete_path_item(db, path, "lesson", lesson_id, now)

# Get history
paths = lp_service.get_path_history(db, user, limit=30)

# Get stats
stats = lp_service.get_path_statistics(db, user, days=30)
```

## 🔄 Typical User Flow

1. **Morning**: User opens app
   - GET `/api/v1/learning-path/today`
   - Receives personalized daily path

2. **During Learning**: User completes items
   - POST `/api/v1/learning-path/complete-item` after each lesson/quiz/review
   - Progress updates in real-time

3. **Evening**: Check progress
   - GET `/api/v1/learning-path/stats?days=7`
   - See weekly completion rates

4. **Weekly Review**: Analyze trends
   - GET `/api/v1/learning-path/history?days=30`
   - Review past month's paths

## 📈 Recommendation Logic

### Lessons
1. Discovered but not learned motifs (oldest first)
2. New undiscovered motifs
3. Aligned with user's onboarding goal

### Reviews  
1. Calculate days since last review
2. Determine if overdue based on performance
3. Prioritize: high → medium → low
4. Limit to MAX_REVIEWS_PER_DAY

### Quizzes
1. Learned motifs with score < 90%
2. Prioritize lowest scores first
3. Adaptive difficulty based on best score
4. Limit to MAX_QUIZZES_PER_DAY

## ⚡ Performance Tips

- Paths are cached per (user_id, date)
- Regeneration only on explicit request
- Indexes on all query fields
- JSONB for flexible item storage

## 🐛 Common Issues

**Path not generating?**
- Check user has progress data
- Verify lessons exist for motifs
- Ensure onboarding completed

**Reviews not appearing?**
- User needs learned/mastered motifs
- Check quiz attempt history
- Verify review intervals

**Completion not tracking?**
- Verify item_id matches recommendation
- Check item_type is correct
- Ensure path exists for today

## 🧪 Test Commands

```bash
# Get today's path
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/learning-path/today

# Complete a lesson  
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item_type":"lesson","item_id":"'$LESSON_ID'"}' \
  http://localhost:8000/api/v1/learning-path/complete-item

# Force regenerate
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_regenerate":true}' \
  http://localhost:8000/api/v1/learning-path/generate

# Get stats  
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/learning-path/stats?days=30
```

## 📁 File Locations

- **Model**: `backend/models.py` (line 2518)
- **Service**: `backend/services/learning_path.py`
- **Schemas**: `backend/schemas.py` (line 2276)
- **Endpoints**: `backend/main.py` (line 12646)
- **Migration**: `migrations/versions/0024_user_learning_paths.py`

