# P0-ANA-03: Session Tracking API Reference

## Base URL
```
Production: https://api.luuniensuki.com
Development: http://localhost:8000
```

## Authentication
All endpoints require JWT authentication via Bearer token in Authorization header:
```
Authorization: Bearer <access_token>
```

Admin endpoints additionally require admin or super_admin role.

---

## User Endpoints

### POST /api/v1/sessions/heartbeat

**Description**: Create or update a user session with a heartbeat signal.

**Authentication**: Required (any authenticated user)

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_type": "mobile",
  "platform": "ios",
  "app_version": "1.5.0"
}
```

**Request Schema**:
| Field | Type | Required | Pattern | Description |
|-------|------|----------|---------|-------------|
| session_id | UUID | Yes | - | Unique session identifier |
| device_type | string | Yes | `^(mobile\|web\|tablet)$` | Type of device |
| platform | string | Yes | `^(ios\|android\|web)$` | Platform/OS |
| app_version | string | No | - | Application version |

**Response (200 OK)**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| session_id | UUID | Session identifier |
| is_active | boolean | Whether session is currently active |

**Behavior**:
- If session_id doesn't exist: Creates new session
- If session_id exists: Updates last_active_at timestamp
- Sets is_active to true
- Updates device_type, platform, and app_version

**Error Responses**:
- `401 Unauthorized`: Invalid or missing authentication token
- `422 Unprocessable Entity`: Invalid request body

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_type": "mobile",
    "platform": "ios",
    "app_version": "1.5.0"
  }'
```

**Client Recommendations**:
- Call every 30 seconds while app is active
- Generate session_id once per app session (login to logout)
- Store session_id locally for the duration of the session
- Handle offline scenarios with request queuing

---

### POST /api/v1/sessions/end

**Description**: End a user session and record the end time.

**Authentication**: Required (any authenticated user)

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | UUID | Yes | Session to end |

**Response (200 OK)**:
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_seconds": 1847
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| session_id | UUID | Session identifier |
| duration_seconds | integer \| null | Session duration in seconds |

**Behavior**:
- Sets ended_at to current timestamp
- Sets is_active to false
- Calculates duration from started_at to ended_at
- Session must belong to authenticated user

**Error Responses**:
- `401 Unauthorized`: Invalid or missing authentication token
- `404 Not Found`: Session not found or doesn't belong to user
- `422 Unprocessable Entity`: Invalid request body

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/end \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Client Recommendations**:
- Call when user logs out
- Call on app termination/backgrounding (best effort)
- Use beforeunload handler on web
- Don't retry on failure (session will auto-expire)

---

## Admin Endpoints

### GET /api/v1/admin/analytics/sessions/active

**Description**: Get count of currently active sessions.

**Authentication**: Required (admin or super_admin role)

**Query Parameters**: None

**Response (200 OK)**:
```json
{
  "active_sessions": 42,
  "last_5_minutes": 42,
  "last_30_minutes": 67,
  "timestamp": "2025-01-17T14:32:15.123456Z"
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| active_sessions | integer | Sessions active in last 5 minutes |
| last_5_minutes | integer | Same as active_sessions |
| last_30_minutes | integer | Sessions active in last 30 minutes |
| timestamp | datetime | Response generation timestamp (UTC) |

**Behavior**:
- Counts sessions with last_active_at within last 5 minutes
- Counts sessions with last_active_at within last 30 minutes
- Auto-expires sessions inactive for 30+ minutes
- Sets ended_at for expired sessions

**Performance**:
- Uses indexed queries
- Typical response time: <200ms
- Can be cached for 10-30 seconds

**Error Responses**:
- `401 Unauthorized`: Invalid or missing authentication token
- `403 Forbidden`: User doesn't have admin role

**Example cURL**:
```bash
curl -X GET http://localhost:8000/api/v1/admin/analytics/sessions/active \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Use Cases**:
- Real-time dashboard display
- Monitoring active user count
- System load assessment
- Auto-scaling triggers

---

### GET /api/v1/admin/analytics/sessions/stats

**Description**: Get detailed session statistics and analytics.

**Authentication**: Required (admin or super_admin role)

**Query Parameters**: None

**Response (200 OK)**:
```json
{
  "total_sessions_today": 156,
  "total_sessions_week": 892,
  "total_sessions_month": 3521,
  "avg_session_duration_minutes": 23.47,
  "unique_users_today": 124,
  "unique_users_week": 451,
  "unique_users_month": 1203,
  "current_active_sessions": 42,
  "peak_concurrent_today": 87,
  "by_platform": {
    "ios": 1205,
    "android": 1518,
    "web": 798
  },
  "by_device_type": {
    "mobile": 2723,
    "tablet": 312,
    "web": 486
  }
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| total_sessions_today | integer | Sessions started today |
| total_sessions_week | integer | Sessions started in last 7 days |
| total_sessions_month | integer | Sessions started in last 30 days |
| avg_session_duration_minutes | float | Average duration (ended sessions only) |
| unique_users_today | integer | Unique users today |
| unique_users_week | integer | Unique users in last 7 days |
| unique_users_month | integer | Unique users in last 30 days |
| current_active_sessions | integer | Currently active sessions |
| peak_concurrent_today | integer | Maximum concurrent sessions today |
| by_platform | object | Session count by platform |
| by_device_type | object | Session count by device type |

**Behavior**:
- Aggregates session data across time periods
- Calculates average duration from ended sessions
- Counts unique users (excludes anonymous sessions)
- Peak concurrent is approximation (active sessions count)

**Performance**:
- Uses indexed queries with aggregations
- Typical response time: <500ms
- Can be cached for 60 seconds
- Consider read replica for heavy usage

**Error Responses**:
- `401 Unauthorized`: Invalid or missing authentication token
- `403 Forbidden`: User doesn't have admin role

**Example cURL**:
```bash
curl -X GET http://localhost:8000/api/v1/admin/analytics/sessions/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Use Cases**:
- Analytics dashboards
- Growth tracking
- Platform distribution analysis
- Engagement metrics
- Business reporting

---

## Common Patterns

### Session Lifecycle

```
1. User Login/App Start
   ↓
2. Generate session_id (UUID)
   ↓
3. POST /sessions/heartbeat (create session)
   ↓
4. Every 30s: POST /sessions/heartbeat (update)
   ↓
5. User Logout/App Close
   ↓
6. POST /sessions/end
```

### Error Handling

```javascript
try {
  await sendHeartbeat();
} catch (error) {
  if (error.status === 401) {
    // Token expired, re-authenticate
  } else if (error.status === 422) {
    // Invalid request, check parameters
  } else {
    // Network error, retry with exponential backoff
  }
}
```

### Offline Handling

```javascript
// Queue heartbeats when offline
const heartbeatQueue = [];

async function sendHeartbeat() {
  if (!navigator.onLine) {
    heartbeatQueue.push({ session_id, timestamp: Date.now() });
    return;
  }
  
  // Send current heartbeat
  await api.post('/sessions/heartbeat', data);
  
  // Flush queue if exists
  while (heartbeatQueue.length > 0) {
    const queued = heartbeatQueue.shift();
    await api.post('/sessions/heartbeat', queued);
  }
}
```

## Rate Limits

- Heartbeat: No rate limit (30s interval expected)
- End session: No rate limit
- Admin active: 10 requests/second per admin
- Admin stats: 2 requests/second per admin

## Data Retention

- Active sessions: Kept indefinitely
- Ended sessions: Retained for analytics
- Recommendation: Archive sessions older than 90 days

## Changelog

### Version 1.0 (2025-01-17)
- Initial release
- 4 endpoints implemented
- Real-time active session tracking
- Detailed analytics for admins

