# P0-ACT-02: Guest Preview Implementation

**Status:** ✅ Complete  
**Version:** 1.0.0  
**Date:** 2025-01-16

## Overview

Implementation of guest preview functionality that allows first-time visitors to experience a "value demo" lesson before signing up. This feature addresses the P0-ACT-02 requirement for first-time user activation.

## Features Implemented

### 1. Database Model (`GuestPreview`)

**Location:** `backend/models.py`

A new model to track guest preview sessions:

```python
class GuestPreview(Base):
    """Track guest users' preview lesson sessions before signup."""
    
    # Fields:
    - id: UUID primary key
    - session_id: str (browser/device session identifier)
    - preview_lesson_id: FK to lesson_content (nullable)
    - started_at: datetime
    - completed_at: datetime (nullable)
    - converted_to_user_id: FK to users (nullable, if they signed up)
    - device_info: JSONB (nullable)
    - created_at: datetime
```

**Indexes:**
- `idx_guest_previews_session_id` - Fast lookup by session
- `idx_guest_previews_started_at` - Time-based analytics
- `idx_guest_previews_converted_user` - Conversion tracking

### 2. LessonContent Enhancement

**Location:** `backend/models.py`

Added `preview_eligible` field to `LessonContent` model:

```python
preview_eligible: Mapped[bool] = mapped_column(
    Boolean, nullable=False, server_default=text("false")
)  # True if this lesson can be shown to guest users as a preview
```

This allows content administrators to mark specific lessons as suitable for guest preview.

### 3. API Endpoints

**Location:** `backend/main.py`

All preview endpoints are **authentication-free** (except `/convert`):

#### GET `/api/v1/preview/lesson`

Get the demo lesson for guest users.

**Authentication:** None required  
**Response:** `GuestPreviewLessonOut`

```json
{
  "lesson_id": "uuid",
  "motif_id": "uuid",
  "motif_name": "Dragon",
  "motif_description": "...",
  "urn_id": "uuid",
  "urn_name": "Cao Dinh",
  "urn_thumbnail_url": "https://...",
  "intro_text": "...",
  "description": "...",
  "historical_context": "...",
  "symbolism": "...",
  "fun_fact": "...",
  "additional_images": ["url1", "url2"]
}
```

#### POST `/api/v1/preview/start`

Start a guest preview session.

**Authentication:** None required  
**Request:** `GuestPreviewStartIn`

```json
{
  "session_id": "browser-session-123",
  "device_info": {
    "platform": "web",
    "browser": "Chrome",
    "os": "macOS"
  }
}
```

**Response:** `GuestPreviewStartOut`

```json
{
  "preview_id": "uuid",
  "lesson_id": "uuid",
  "lesson_title": "Dragon",
  "lesson_description": "...",
  "motif_name": "Dragon",
  "urn_name": "Cao Dinh",
  "started_at": "2025-01-16T14:00:00Z"
}
```

#### POST `/api/v1/preview/complete`

Mark a preview session as complete.

**Authentication:** None required  
**Request:** `GuestPreviewCompleteIn`

```json
{
  "session_id": "browser-session-123"
}
```

**Response:** `GuestPreviewCompleteOut`

```json
{
  "success": true,
  "message": "Preview session marked as complete",
  "completed_at": "2025-01-16T14:05:00Z",
  "preview_id": "uuid"
}
```

#### POST `/api/v1/preview/convert`

Link preview session(s) to a newly registered user account.

**Authentication:** Required (Bearer token)
**Request:** `GuestPreviewConvertIn`

```json
{
  "session_id": "browser-session-123"
}
```

**Response:** `GuestPreviewConvertOut`

```json
{
  "success": true,
  "message": "Successfully linked 2 preview session(s) to your account",
  "preview_sessions_converted": 2
}
```

### 4. Pydantic Schemas

**Location:** `backend/schemas.py`

Added comprehensive request/response schemas:

- `GuestPreviewStartIn` - Request to start preview session
- `GuestPreviewStartOut` - Preview session details
- `GuestPreviewLessonOut` - Complete lesson data for guests
- `GuestPreviewCompleteIn` - Request to mark complete
- `GuestPreviewCompleteOut` - Completion confirmation
- `GuestPreviewConvertIn` - Request to link to user
- `GuestPreviewConvertOut` - Conversion result

### 5. Database Migration

**Location:** `migrations/versions/0022_guest_preview.py`

Migration includes:
1. Add `preview_eligible` boolean column to `lesson_content` table
2. Create `guest_previews` table with all relationships
3. Create necessary indexes for performance

**To apply migration:**

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

## User Flow

### Guest Preview Flow

1. **Guest visits app** → Sees "Try Demo Lesson" button
2. **Click demo** → Frontend calls `GET /api/v1/preview/lesson`
3. **View lesson** → Frontend calls `POST /api/v1/preview/start` with session_id
4. **Complete lesson** → Frontend calls `POST /api/v1/preview/complete`
5. **Sign up** → User creates account
6. **Link session** → Frontend calls `POST /api/v1/preview/convert` (authenticated)

### Session ID Generation

Frontend should generate a persistent session ID (e.g., using localStorage):

```javascript
// Example session ID generation
let sessionId = localStorage.getItem('guest_session_id');
if (!sessionId) {
  sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  localStorage.setItem('guest_session_id', sessionId);
}
```

## Analytics & Tracking

The `GuestPreview` model enables tracking:

- **Engagement:** How many guests start the preview
- **Completion Rate:** `completed_at` IS NOT NULL
- **Conversion Rate:** `converted_to_user_id` IS NOT NULL
- **Device Analytics:** Via `device_info` JSONB field
- **Time to Complete:** `completed_at - started_at`
- **Time to Convert:** Join with User.created_at

## Content Management

### Marking Lessons as Preview-Eligible

To mark a lesson as available for preview:

```python
# Via admin panel or script
lesson = db.get(LessonContent, lesson_id)
lesson.preview_eligible = True
db.commit()
```

**Best Practices:**
- Only mark high-quality, engaging lessons
- Choose lessons that showcase unique value
- Ensure content is appropriate for all ages
- Keep preview lesson short (3-5 minutes)
- Update preview lesson periodically for freshness

## Testing

### Manual Testing

```bash
# 1. Get preview lesson (no auth)
curl http://localhost:8000/api/v1/preview/lesson

# 2. Start preview session (no auth)
curl -X POST http://localhost:8000/api/v1/preview/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "device_info": {"platform": "web", "browser": "curl"}
  }'

# 3. Complete preview session (no auth)
curl -X POST http://localhost:8000/api/v1/preview/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-123"}'

# 4. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "display_name": "Test User"
  }'

# 5. Link preview to user (requires auth)
curl -X POST http://localhost:8000/api/v1/preview/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"session_id": "test-session-123"}'
```

### SQL Queries for Analytics

```sql
-- Total preview sessions started
SELECT COUNT(*) FROM guest_previews;

-- Completion rate
SELECT
  COUNT(*) as total_sessions,
  COUNT(completed_at) as completed_sessions,
  ROUND(COUNT(completed_at)::numeric / COUNT(*)::numeric * 100, 2) as completion_rate_pct
FROM guest_previews;

-- Conversion rate (preview to signup)
SELECT
  COUNT(*) as total_sessions,
  COUNT(converted_to_user_id) as converted_sessions,
  ROUND(COUNT(converted_to_user_id)::numeric / COUNT(*)::numeric * 100, 2) as conversion_rate_pct
FROM guest_previews;

-- Most popular preview lessons
SELECT
  lc.id,
  m.name as motif_name,
  COUNT(gp.id) as preview_count,
  COUNT(gp.completed_at) as completion_count
FROM guest_previews gp
JOIN lesson_content lc ON gp.preview_lesson_id = lc.id
JOIN motifs m ON lc.motif_id = m.id
GROUP BY lc.id, m.name
ORDER BY preview_count DESC;

-- Average time to complete preview
SELECT
  AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) / 60 as avg_minutes_to_complete
FROM guest_previews
WHERE completed_at IS NOT NULL;

-- Conversion by device type
SELECT
  device_info->>'platform' as platform,
  COUNT(*) as sessions,
  COUNT(converted_to_user_id) as conversions,
  ROUND(COUNT(converted_to_user_id)::numeric / COUNT(*)::numeric * 100, 2) as conversion_rate_pct
FROM guest_previews
GROUP BY device_info->>'platform';
```

## Security Considerations

1. **No Authentication Required** - Preview endpoints are public (except `/convert`)
2. **Session ID** - Use client-generated UUIDs, not server-side auth tokens
3. **Rate Limiting** - Consider adding rate limiting to prevent abuse
4. **Data Privacy** - Device info is optional and should only collect non-PII
5. **Content Filtering** - Only show `preview_eligible=true` and `is_published=true` lessons

## Error Handling

All endpoints include proper error responses:

- `NO_PREVIEW_AVAILABLE` (404) - No preview-eligible lessons found
- `PREVIEW_SESSION_NOT_FOUND` (404) - Invalid or expired session_id
- Standard authentication errors for `/convert` endpoint

## Future Enhancements

Potential improvements for future iterations:

1. **Multiple Preview Lessons** - Allow guests to try multiple lessons
2. **Progress Tracking** - Track which parts of the lesson guests viewed
3. **A/B Testing** - Test different preview lessons for conversion
4. **Preview Limits** - Limit number of previews per session/IP
5. **Preview Analytics Dashboard** - Admin UI for preview metrics
6. **Email Capture** - Optional email collection before preview
7. **Social Sharing** - Allow guests to share their preview experience

## Files Changed

### Backend

1. **backend/models.py**
   - Added `GuestPreview` model
   - Added `preview_eligible` field to `LessonContent` model

2. **backend/schemas.py**
   - Added `GuestPreviewStartIn`
   - Added `GuestPreviewStartOut`
   - Added `GuestPreviewLessonOut`
   - Added `GuestPreviewCompleteIn`
   - Added `GuestPreviewCompleteOut`
   - Added `GuestPreviewConvertIn`
   - Added `GuestPreviewConvertOut`

3. **backend/main.py**
   - Added `GuestPreview` to model imports
   - Added `GET /api/v1/preview/lesson` endpoint
   - Added `POST /api/v1/preview/start` endpoint
   - Added `POST /api/v1/preview/complete` endpoint
   - Added `POST /api/v1/preview/convert` endpoint

4. **migrations/versions/0022_guest_preview.py**
   - New migration for database schema changes

## Deployment Checklist

- [ ] Review and test all endpoints locally
- [ ] Run database migration: `alembic upgrade head`
- [ ] Mark at least one lesson as `preview_eligible=true`
- [ ] Test complete guest flow (preview → signup → convert)
- [ ] Update API documentation
- [ ] Configure rate limiting for preview endpoints (recommended)
- [ ] Monitor preview analytics after deployment
- [ ] Update mobile app to use preview endpoints
- [ ] Update frontend to use preview endpoints

## API Quick Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/preview/lesson` | GET | No | Get demo lesson for guests |
| `/api/v1/preview/start` | POST | No | Start preview session |
| `/api/v1/preview/complete` | POST | No | Mark preview complete |
| `/api/v1/preview/convert` | POST | Yes | Link preview to user account |

## Success Metrics

Track these KPIs to measure feature success:

1. **Preview Start Rate** - % of visitors who start preview
2. **Preview Completion Rate** - % of previews completed
3. **Conversion Rate** - % of previews that lead to signup
4. **Time to Convert** - How long from preview to signup
5. **Preview Quality** - Which lessons convert best

## Support & Troubleshooting

### Common Issues

**Issue:** "No preview lesson available"
- **Solution:** Ensure at least one lesson has `preview_eligible=true` and `is_published=true`

**Issue:** "Preview session not found"
- **Solution:** Verify session_id is being persisted correctly in frontend

**Issue:** "Conversion not working"
- **Solution:** Ensure user is authenticated when calling `/convert` endpoint

### Database Queries

```sql
-- Check if any lessons are preview-eligible
SELECT id, motif_id, preview_eligible, is_published
FROM lesson_content
WHERE preview_eligible = true;

-- View recent preview sessions
SELECT * FROM guest_previews
ORDER BY started_at DESC
LIMIT 10;
```

## Related Documentation

- [P0-ACT-01: Onboarding Implementation](P0-ACT-01_ONBOARDING_IMPLEMENTATION.md)
- [API Quick Reference](API_QUICK_REFERENCE.md)
- [Analytics Taxonomy](ANALYTICS_TAXONOMY_ARCHITECTURE.md)

---

**Implementation Complete:** 2025-01-16
**Last Updated:** 2025-01-16
**Version:** 1.0.0

