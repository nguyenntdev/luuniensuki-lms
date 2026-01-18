# P1-REC-01: Content Recommendation Engine - Quick Reference

## TL;DR

Content recommendation engine with collaborative filtering, content-based filtering, and personalized recommendations. Track user interactions and get smart content suggestions.

## API Endpoints

### 1. GET /api/v1/recommendations
Get personalized recommendations (4 types).

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Query Parameters:**
- `recommendation_type` (optional): continue_learning | discover_new | review_needed | popular
- `limit` (default: 10, max: 50)

### 2. GET /api/v1/recommendations/similar/{content_type}/{content_id}
Get similar content based on tags.

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/similar/motif/$MOTIF_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. POST /api/v1/recommendations/interaction
Record user interaction with content.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "motif",
    "content_id": "uuid",
    "interaction_type": "view",
    "duration_seconds": 120
  }'
```

**Interaction Types:** `view`, `complete`, `like`, `save`

### 4. POST /api/v1/recommendations/feedback
Submit recommendation feedback.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "uuid",
    "content_type": "motif",
    "feedback_type": "helpful"
  }'
```

**Feedback Types:** `helpful`, `not_helpful`, `irrelevant`, `already_seen`

## Recommendation Types

### 1. Continue Learning
Lessons user started but hasn't completed.
- Status: discovered or learned (not mastered)
- Score: 1.0 (highest priority)

### 2. Discover New
New content based on user's interests and tags.
- Analyzes liked/completed content tags
- Finds similar unviewed content
- Score: 0.8

### 3. Review Needed
Content completed >7 days ago.
- Spaced repetition learning
- Score: 0.6

### 4. Popular
Trending content (last 30 days).
- Most interacted with
- Excludes user's own content
- Score: 0.7

## Database Schema

### UserContentInteraction Table
```sql
CREATE TABLE user_content_interactions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  content_type VARCHAR(50) NOT NULL,  -- lesson, motif, quest
  content_id UUID NOT NULL,
  interaction_type interaction_type NOT NULL,  -- view, complete, like, save
  duration_seconds INTEGER,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Usage Examples

### Auto-track Lesson View
```python
from .services.recommendations import record_interaction
from .models import InteractionType

record_interaction(
    db=db,
    user=current_user,
    content_type="lesson",
    content_id=lesson_id,
    interaction_type=InteractionType.view,
    duration_seconds=None
)
```

### Get Recommendations in Frontend
```javascript
const response = await fetch('/api/v1/recommendations?limit=5', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// data.continue_learning - lessons to continue
// data.discover_new - new content suggestions
// data.review_needed - review recommendations
// data.popular - trending content
```

## Migration

```bash
# Apply migration
docker-compose exec backend python -m alembic upgrade head

# Or locally
python -m alembic upgrade head
```

Migration: `0024_user_content_interactions.py`

## Files Changed

**Created:**
- `backend/services/recommendations.py`
- `migrations/versions/0024_user_content_interactions.py`

**Modified:**
- `backend/models.py` - Added UserContentInteraction model
- `backend/schemas.py` - Added recommendation schemas
- `backend/main.py` - Added 4 API endpoints

## Key Features

✅ Collaborative filtering (users who liked X also liked Y)
✅ Content-based filtering (similar tags)
✅ Personalized recommendations (4 types)
✅ Interaction tracking (view, complete, like, save)
✅ Feedback system
✅ Efficient database indexes

## Performance

**Indexes:**
- `user_id` - Fast user lookups
- `content_type, content_id` - Fast content lookups
- `created_at` - Time-based queries
- `user_id, content_type` - Composite queries

**Query Limits:**
- Max 50 recommendations per request
- Default 10 recommendations
- 30-day window for popular content
- 7-day threshold for review recommendations

## Testing Checklist

- [ ] Get all recommendations
- [ ] Filter by recommendation_type
- [ ] Get similar content for motif
- [ ] Record view interaction
- [ ] Record complete interaction
- [ ] Submit helpful feedback
- [ ] Test with empty interaction history
- [ ] Test with rich interaction history

## Integration Checklist

- [ ] Auto-track lesson views
- [ ] Auto-track lesson completions
- [ ] Auto-track quiz completions
- [ ] Add like/save buttons to UI
- [ ] Display recommendations in UI
- [ ] Show "continue learning" section
- [ ] Show "discover new" section
- [ ] Add feedback buttons to recommendations

