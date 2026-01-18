# P0-ACT-02: Guest Preview API Reference

## Overview

The Guest Preview API enables first-time visitors to experience a demo lesson before signing up. All endpoints (except `/convert`) are public and don't require authentication.

## Endpoints

### 1. Get Preview Lesson

Retrieve the demo lesson content for guest users.

**Endpoint:** `GET /api/v1/preview/lesson`  
**Authentication:** None  
**Rate Limit:** Recommended 100 requests/hour per IP

#### Request

No request body required.

#### Response 200 OK

```json
{
  "lesson_id": "123e4567-e89b-12d3-a456-426614174000",
  "motif_id": "123e4567-e89b-12d3-a456-426614174001",
  "motif_name": "Dragon",
  "motif_description": "The dragon is a symbol of power and wisdom...",
  "urn_id": "123e4567-e89b-12d3-a456-426614174002",
  "urn_name": "Cao Dinh",
  "urn_thumbnail_url": "https://example.com/thumbnails/cao-dinh.jpg",
  "intro_text": "Welcome to this lesson about the dragon motif...",
  "description": "In Vietnamese culture, the dragon represents...",
  "historical_context": "Dragons have appeared in Vietnamese art since...",
  "symbolism": "The dragon symbolizes imperial power...",
  "fun_fact": "Did you know that Vietnamese dragons have 117 scales?",
  "additional_images": [
    "https://example.com/images/dragon-1.jpg",
    "https://example.com/images/dragon-2.jpg"
  ]
}
```

#### Error Responses

**404 Not Found** - No preview lesson available

```json
{
  "detail": {
    "code": "NO_PREVIEW_AVAILABLE",
    "message": "No preview lesson available at this time"
  }
}
```

---

### 2. Start Preview Session

Create a tracking record when a guest starts viewing the preview lesson.

**Endpoint:** `POST /api/v1/preview/start`  
**Authentication:** None  
**Rate Limit:** Recommended 20 requests/hour per session_id

#### Request Body

```json
{
  "session_id": "session-1642089600-abc123",
  "device_info": {
    "platform": "web",
    "browser": "Chrome",
    "browser_version": "121.0",
    "os": "macOS",
    "screen_width": 1920,
    "screen_height": 1080
  }
}
```

**Fields:**
- `session_id` (required, string): Client-generated unique session identifier
- `device_info` (optional, object): Device/browser metadata for analytics

#### Response 200 OK

```json
{
  "preview_id": "123e4567-e89b-12d3-a456-426614174003",
  "lesson_id": "123e4567-e89b-12d3-a456-426614174000",
  "lesson_title": "Dragon",
  "lesson_description": "In Vietnamese culture, the dragon represents...",
  "motif_name": "Dragon",
  "urn_name": "Cao Dinh",
  "started_at": "2025-01-16T14:30:00.000Z"
}
```

#### Error Responses

**404 Not Found** - No preview lesson available

```json
{
  "detail": {
    "code": "NO_PREVIEW_AVAILABLE",
    "message": "No preview lesson available at this time"
  }
}
```

---

### 3. Complete Preview Session

Mark a preview session as complete when the guest finishes viewing.

**Endpoint:** `POST /api/v1/preview/complete`  
**Authentication:** None  
**Rate Limit:** Recommended 10 requests/hour per session_id

#### Request Body

```json
{
  "session_id": "session-1642089600-abc123"
}
```

**Fields:**
- `session_id` (required, string): The same session ID used in `/start`

#### Response 200 OK

```json
{
  "success": true,
  "message": "Preview session marked as complete",
  "completed_at": "2025-01-16T14:35:00.000Z",
  "preview_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

#### Error Responses

**404 Not Found** - Preview session not found

```json
{
  "detail": {
    "code": "PREVIEW_SESSION_NOT_FOUND",
    "message": "No active preview session found for this session ID"
  }
}
```

---

### 4. Convert Preview to User

Link previous guest preview sessions to a newly registered user account.

**Endpoint:** `POST /api/v1/preview/convert`  
**Authentication:** Required (Bearer token)  
**Rate Limit:** Recommended 5 requests/hour per user

#### Request Headers

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

#### Request Body

```json
{
  "session_id": "session-1642089600-abc123"
}
```

**Fields:**
- `session_id` (required, string): The session ID from previous guest preview

#### Response 200 OK

```json
{
  "success": true,
  "message": "Successfully linked 2 preview session(s) to your account",
  "preview_sessions_converted": 2
}
```

**Note:** If no preview sessions exist for the session_id, returns success with 0 converted.

#### Error Responses

**401 Unauthorized** - Missing or invalid authentication token

```json
{
  "detail": "Not authenticated"
}
```

---

## Data Models

### GuestPreviewLessonOut

| Field | Type | Description |
|-------|------|-------------|
| lesson_id | UUID | Lesson content identifier |
| motif_id | UUID | Related motif identifier |
| motif_name | string | Name of the motif |
| motif_description | string | Description of the motif |
| urn_id | UUID | Related urn identifier |
| urn_name | string | Name of the urn |
| urn_thumbnail_url | string? | URL to urn thumbnail image |
| intro_text | string? | Introduction text for the lesson |
| description | string | Main lesson description |
| historical_context | string? | Historical background |
| symbolism | string? | Symbolic meanings |
| fun_fact | string? | Interesting fact about the motif |
| additional_images | string[]? | Array of additional image URLs |

### GuestPreviewStartIn

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | Client-generated session identifier |
| device_info | object | No | Device/browser metadata |

### GuestPreviewStartOut

| Field | Type | Description |
|-------|------|-------------|
| preview_id | UUID | Created preview session identifier |
| lesson_id | UUID | Lesson being previewed |
| lesson_title | string | Title of the lesson |
| lesson_description | string | Lesson description |
| motif_name | string | Name of the motif |
| urn_name | string | Name of the urn |
| started_at | datetime | When preview session started |

### GuestPreviewCompleteIn

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | Session identifier from /start |

### GuestPreviewCompleteOut

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| message | string | Human-readable message |
| completed_at | datetime | When preview was completed |
| preview_id | UUID | Preview session identifier |

### GuestPreviewConvertIn

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | Session identifier to link |

### GuestPreviewConvertOut

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| message | string | Human-readable message |
| preview_sessions_converted | integer | Number of sessions linked |

---

## Usage Examples

### JavaScript/TypeScript (Frontend)

```typescript
// 1. Generate and persist session ID
function getSessionId(): string {
  let sessionId = localStorage.getItem('guest_session_id');
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('guest_session_id', sessionId);
  }
  return sessionId;
}

// 2. Get preview lesson
async function getPreviewLesson() {
  const response = await fetch('/api/v1/preview/lesson');
  return await response.json();
}

// 3. Start preview session
async function startPreview() {
  const sessionId = getSessionId();
  const deviceInfo = {
    platform: 'web',
    browser: navigator.userAgent,
    screen_width: window.screen.width,
    screen_height: window.screen.height
  };

  const response = await fetch('/api/v1/preview/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, device_info: deviceInfo })
  });

  return await response.json();
}

// 4. Complete preview
async function completePreview() {
  const sessionId = getSessionId();
  const response = await fetch('/api/v1/preview/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });

  return await response.json();
}

// 5. Convert after signup (requires auth token)
async function convertPreview(authToken: string) {
  const sessionId = getSessionId();
  const response = await fetch('/api/v1/preview/convert', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ session_id: sessionId })
  });

  return await response.json();
}
```

### Python (Backend/Testing)

```python
import requests

BASE_URL = "http://localhost:8000"
session_id = f"session-{int(time.time())}"

# 1. Get preview lesson
response = requests.get(f"{BASE_URL}/api/v1/preview/lesson")
lesson = response.json()

# 2. Start preview
response = requests.post(
    f"{BASE_URL}/api/v1/preview/start",
    json={
        "session_id": session_id,
        "device_info": {"platform": "web", "browser": "python-requests"}
    }
)
preview = response.json()

# 3. Complete preview
response = requests.post(
    f"{BASE_URL}/api/v1/preview/complete",
    json={"session_id": session_id}
)
completion = response.json()

# 4. Convert (after user registration)
headers = {"Authorization": f"Bearer {auth_token}"}
response = requests.post(
    f"{BASE_URL}/api/v1/preview/convert",
    json={"session_id": session_id},
    headers=headers
)
conversion = response.json()
```

### cURL

```bash
# 1. Get preview lesson
curl http://localhost:8000/api/v1/preview/lesson

# 2. Start preview
curl -X POST http://localhost:8000/api/v1/preview/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-123", "device_info": {"platform": "web"}}'

# 3. Complete preview
curl -X POST http://localhost:8000/api/v1/preview/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-123"}'

# 4. Convert (with auth)
curl -X POST http://localhost:8000/api/v1/preview/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"session_id": "session-123"}'
```

---

## Best Practices

### Session ID Generation

- **Use UUIDs or timestamp-based IDs**: `session-${timestamp}-${random}`
- **Persist in localStorage**: Don't regenerate on every page load
- **Include randomness**: Prevent collisions
- **Clear on logout**: Optional, for privacy

### Device Info Collection

Only collect non-PII data:
- Platform (web, ios, android)
- Browser name and version
- Screen dimensions
- OS name (not version for privacy)
- Language preference

**Do NOT collect:**
- IP addresses
- Geolocation
- Personal identifiers
- Tracking cookies

### Error Handling

Always handle these cases:
1. No preview lesson available (mark at least one lesson as preview_eligible)
2. Network failures (retry logic)
3. Invalid session_id (regenerate if needed)
4. Authentication failures (for /convert endpoint)

### Performance

- Cache GET `/lesson` response for 5 minutes
- Debounce completion calls
- Use async/await for all API calls
- Show loading states

---

## Analytics Integration

Track these events:

```typescript
// Example analytics tracking
analytics.track('Preview Lesson Viewed', {
  lesson_id: lesson.lesson_id,
  motif_name: lesson.motif_name
});

analytics.track('Preview Session Started', {
  preview_id: preview.preview_id,
  session_id: sessionId
});

analytics.track('Preview Session Completed', {
  preview_id: completion.preview_id,
  duration_seconds: calculateDuration()
});

analytics.track('Preview Converted to Signup', {
  sessions_converted: conversion.preview_sessions_converted,
  user_id: currentUser.id
});
```

---

## Rate Limiting Recommendations

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| GET /lesson | 100 | 1 hour | IP address |
| POST /start | 20 | 1 hour | session_id |
| POST /complete | 10 | 1 hour | session_id |
| POST /convert | 5 | 1 hour | user_id |

---

## Related Documentation

- [Implementation Guide](P0-ACT-02_GUEST_PREVIEW_IMPLEMENTATION.md)
- [Quick Reference](P0-ACT-02_QUICK_REFERENCE.md)
- [Testing Script](test_guest_preview.sh)

---

**Version:** 1.0.0
**Last Updated:** 2025-01-16

