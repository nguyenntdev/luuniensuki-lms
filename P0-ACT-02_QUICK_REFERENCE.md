# P0-ACT-02: Guest Preview - Quick Reference

## TL;DR

Guest preview allows visitors to try a demo lesson before signing up. Track engagement, completion, and conversion rates.

## API Endpoints

### 1. GET /api/v1/preview/lesson
Get the demo lesson (no auth)

```bash
curl http://localhost:8000/api/v1/preview/lesson
```

### 2. POST /api/v1/preview/start
Start preview session (no auth)

```bash
curl -X POST http://localhost:8000/api/v1/preview/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "device_info": {"platform": "web"}
  }'
```

### 3. POST /api/v1/preview/complete
Mark preview complete (no auth)

```bash
curl -X POST http://localhost:8000/api/v1/preview/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-123"}'
```

### 4. POST /api/v1/preview/convert
Link preview to user (auth required)

```bash
curl -X POST http://localhost:8000/api/v1/preview/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"session_id": "session-123"}'
```

## Database

### Tables

**guest_previews**
- `id` - UUID primary key
- `session_id` - Client-generated session identifier
- `preview_lesson_id` - FK to lesson_content
- `started_at` - When preview started
- `completed_at` - When preview completed (nullable)
- `converted_to_user_id` - FK to users (nullable)
- `device_info` - JSONB metadata
- `created_at` - Record creation time

**lesson_content**
- Added: `preview_eligible` - Boolean flag

### Mark Lesson as Preview-Eligible

```sql
UPDATE lesson_content 
SET preview_eligible = true 
WHERE id = 'lesson-uuid';
```

## Analytics Queries

### Conversion Rate
```sql
SELECT 
  COUNT(*) as total,
  COUNT(converted_to_user_id) as converted,
  ROUND(COUNT(converted_to_user_id)::numeric / COUNT(*)::numeric * 100, 2) as rate_pct
FROM guest_previews;
```

### Completion Rate
```sql
SELECT 
  COUNT(*) as total,
  COUNT(completed_at) as completed,
  ROUND(COUNT(completed_at)::numeric / COUNT(*)::numeric * 100, 2) as rate_pct
FROM guest_previews;
```

## Frontend Integration

### Session ID
```javascript
let sessionId = localStorage.getItem('guest_session_id');
if (!sessionId) {
  sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('guest_session_id', sessionId);
}
```

### User Flow
1. Guest visits → Show "Try Demo" CTA
2. Click demo → Call `GET /api/v1/preview/lesson`
3. View lesson → Call `POST /api/v1/preview/start`
4. Complete → Call `POST /api/v1/preview/complete`
5. Sign up → User registers
6. After login → Call `POST /api/v1/preview/convert`

## Migration

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

## Key Files

- **Model**: `backend/models.py` (GuestPreview class)
- **Schemas**: `backend/schemas.py` (GuestPreview* schemas)
- **Endpoints**: `backend/main.py` (lines ~1230-1430)
- **Migration**: `migrations/versions/0022_guest_preview.py`
- **Docs**: `P0-ACT-02_GUEST_PREVIEW_IMPLEMENTATION.md`

## Testing

```bash
# Get lesson
curl http://localhost:8000/api/v1/preview/lesson

# Start session
curl -X POST http://localhost:8000/api/v1/preview/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123"}'

# Complete
curl -X POST http://localhost:8000/api/v1/preview/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123"}'
```

## Metrics to Track

- Preview start rate
- Preview completion rate  
- Preview-to-signup conversion rate
- Time to complete preview
- Time from preview to signup
- Device/platform breakdown

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-16

