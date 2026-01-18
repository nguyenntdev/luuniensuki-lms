# P0-ANA-03: Real-Time Session Counter Implementation

## Overview
This implementation adds a real-time session tracking system using a database-backed `UserSession` model. It enables tracking of active users, concurrent sessions, and detailed session analytics.

## Components Added

### 1. Database Model: `UserSession`
**File**: `backend/models.py`

```python
class UserSession(Base):
    """User session tracking for real-time analytics."""
    __tablename__ = "user_sessions"
```

**Fields**:
- `id`: UUID primary key
- `user_id`: Foreign key to users table (nullable for anonymous sessions)
- `session_id`: UUID unique identifier for each session
- `started_at`: Timestamp when session began
- `last_active_at`: Timestamp of last heartbeat
- `ended_at`: Timestamp when session ended (nullable)
- `device_type`: Type of device (mobile, web, tablet)
- `platform`: Platform (ios, android, web)
- `app_version`: App version string (nullable)
- `is_active`: Boolean flag for active sessions

**Indexes**:
- `idx_user_sessions_user_id`: For user lookups
- `idx_user_sessions_session_id`: For session lookups
- `idx_user_sessions_is_active`: For active session queries
- `idx_user_sessions_last_active`: For activity-based queries
- `idx_user_sessions_started_at`: For time-based analytics

### 2. Database Migration
**File**: `migrations/versions/0017_user_sessions.py`

Creates the `user_sessions` table with all indexes.

**To apply migration**:
```bash
# Using docker:
docker compose exec api alembic upgrade head

# Or locally with Python:
python3 -m alembic upgrade head
```

### 3. Schemas
**File**: `backend/schemas.py`

#### Request Schemas:
- `SessionHeartbeatIn`: For heartbeat requests
- `SessionEndIn`: For ending sessions

#### Response Schemas:
- `SessionHeartbeatOut`: Heartbeat response
- `SessionEndOut`: Session end response with duration
- `ActiveSessionsOut`: Active session counts
- `SessionStatsOut`: Detailed session statistics

### 4. API Endpoints

#### User Endpoints:

##### POST `/api/v1/sessions/heartbeat`
**Description**: Update session activity (called every 30s from client)

**Request Body**:
```json
{
  "session_id": "uuid",
  "device_type": "mobile|web|tablet",
  "platform": "ios|android|web",
  "app_version": "1.0.0" // optional
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "uuid",
  "is_active": true
}
```

**Authentication**: Required (JWT token)

**Behavior**:
- Creates new session if session_id doesn't exist
- Updates `last_active_at` timestamp
- Marks session as active
- Updates device info

##### POST `/api/v1/sessions/end`
**Description**: End current session (called on logout/app close)

**Request Body**:
```json
{
  "session_id": "uuid"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "uuid",
  "duration_seconds": 1234
}
```

**Authentication**: Required (JWT token)

**Behavior**:
- Marks session as inactive
- Sets `ended_at` timestamp
- Calculates and returns session duration

#### Admin Endpoints:

##### GET `/api/v1/admin/analytics/sessions/active`
**Description**: Get count of currently active sessions

**Response**:
```json
{
  "active_sessions": 42,
  "last_5_minutes": 42,
  "last_30_minutes": 67,
  "timestamp": "2025-01-17T12:00:00Z"
}
```

**Authentication**: Admin role required

**Behavior**:
- Counts sessions active in last 5 minutes
- Counts sessions active in last 30 minutes
- Auto-expires sessions older than 30 minutes without heartbeat
- Returns current timestamp

##### GET `/api/v1/admin/analytics/sessions/stats`
**Description**: Get detailed session statistics

**Response**:
```json
{
  "total_sessions_today": 150,
  "total_sessions_week": 890,
  "total_sessions_month": 3500,
  "avg_session_duration_minutes": 23.5,
  "unique_users_today": 120,
  "unique_users_week": 450,
  "unique_users_month": 1200,
  "current_active_sessions": 42,
  "peak_concurrent_today": 87,
  "by_platform": {
    "ios": 1200,
    "android": 1500,
    "web": 800
  },
  "by_device_type": {
    "mobile": 2700,
    "tablet": 300,
    "web": 500
  }
}
```

**Authentication**: Admin role required

**Metrics Provided**:
- Session counts by period (day/week/month)
- Average session duration (only ended sessions)
- Unique user counts by period
- Current active sessions count
- Peak concurrent sessions today
- Breakdown by platform (ios/android/web)
- Breakdown by device type (mobile/tablet/web)

## Session Logic

### Active Session Definition
A session is considered **active** if:
1. `is_active = true`
2. `last_active_at` is within the last 5 minutes

### Auto-Expiration
Sessions are automatically expired when:
- No heartbeat received for 30 minutes
- `ended_at` is set to `last_active_at`
- `is_active` is set to `false`

This happens automatically when calling the active sessions endpoint.

### Client Implementation Requirements

#### Mobile/Web Client Behavior:

1. **On App Start/Login**:
   - Generate new `session_id` (UUID)
   - Call heartbeat endpoint immediately

2. **During Active Use**:
   - Call heartbeat every 30 seconds
   - Include current device type, platform, and app version

3. **On App Close/Logout**:
   - Call end session endpoint
   - Clear session_id from local storage

#### Example Client Code (React Native):
```javascript
import { v4 as uuidv4 } from 'uuid';

let sessionId = null;
let heartbeatInterval = null;

// Start session
async function startSession() {
  sessionId = uuidv4();
  await sendHeartbeat();
  
  // Send heartbeat every 30 seconds
  heartbeatInterval = setInterval(sendHeartbeat, 30000);
}

// Send heartbeat
async function sendHeartbeat() {
  try {
    await fetch('/api/v1/sessions/heartbeat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        device_type: 'mobile',
        platform: Platform.OS, // 'ios' or 'android'
        app_version: '1.5.0',
      }),
    });
  } catch (error) {
    console.error('Heartbeat failed:', error);
  }
}

// End session
async function endSession() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
  }
  
  if (sessionId) {
    try {
      await fetch('/api/v1/sessions/end', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      });
    } catch (error) {
      console.error('End session failed:', error);
    }
  }
  
  sessionId = null;
}

// Register app lifecycle listeners
AppState.addEventListener('change', (nextAppState) => {
  if (nextAppState === 'active') {
    startSession();
  } else if (nextAppState === 'background' || nextAppState === 'inactive') {
    endSession();
  }
});
```

## Testing

### 1. Test Migration
```bash
# Check current migration
docker compose exec api alembic current

# Run migration
docker compose exec api alembic upgrade head

# Verify table created
docker compose exec db psql -U postgres -d luuniensuki -c "\d user_sessions"
```

### 2. Test Heartbeat Endpoint
```bash
# Login first to get token
TOKEN=$(curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r .access_token)

# Generate session ID
SESSION_ID=$(uuidgen)

# Send heartbeat
curl -X POST http://localhost/api/v1/sessions/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"device_type\": \"web\",
    \"platform\": \"web\",
    \"app_version\": \"1.0.0\"
  }" | jq
```

### 3. Test End Session
```bash
curl -X POST http://localhost/api/v1/sessions/end \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" | jq
```

### 4. Test Admin Endpoints
```bash
# Login as admin
ADMIN_TOKEN=$(curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | jq -r .access_token)

# Get active sessions
curl -X GET http://localhost/api/v1/admin/analytics/sessions/active \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Get session stats
curl -X GET http://localhost/api/v1/admin/analytics/sessions/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

## Database Queries

### Check Active Sessions
```sql
SELECT 
  COUNT(*) as active_count,
  COUNT(DISTINCT user_id) as unique_users
FROM user_sessions
WHERE is_active = true
  AND last_active_at > NOW() - INTERVAL '5 minutes';
```

### Session Duration Analysis
```sql
SELECT 
  platform,
  AVG(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60) as avg_duration_minutes,
  COUNT(*) as session_count
FROM user_sessions
WHERE ended_at IS NOT NULL
GROUP BY platform
ORDER BY avg_duration_minutes DESC;
```

### Peak Concurrent Users by Hour
```sql
SELECT 
  DATE_TRUNC('hour', started_at) as hour,
  COUNT(*) as sessions_started
FROM user_sessions
WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

## Performance Considerations

1. **Indexes**: All frequently queried columns are indexed
2. **Auto-Expiration**: Happens only when admin checks active sessions
3. **Heartbeat Frequency**: 30 seconds balances accuracy vs. database load
4. **Anonymous Sessions**: Supported for pre-login analytics

## Security

1. **User Sessions**: Users can only update their own sessions
2. **Admin Endpoints**: Protected by admin role requirement
3. **Session Validation**: Session ID must match user ID

## Future Enhancements

1. **Background Job**: Auto-expire old sessions periodically
2. **Real-time Dashboard**: WebSocket updates for live session counts
3. **Geolocation**: Add IP-based location tracking
4. **Device Fingerprinting**: Enhanced device tracking
5. **Session History**: Archive old sessions for long-term analytics
6. **Anomaly Detection**: Alert on unusual session patterns

## Files Modified

1. ✅ `backend/models.py` - Added UserSession model
2. ✅ `backend/schemas.py` - Added session schemas
3. ✅ `backend/main.py` - Added session endpoints
4. ✅ `migrations/versions/0017_user_sessions.py` - Database migration

## Summary

This implementation provides a robust real-time session tracking system that:
- ✅ Tracks active sessions with 5-minute accuracy
- ✅ Auto-expires stale sessions after 30 minutes
- ✅ Provides detailed analytics for admins
- ✅ Supports multiple platforms and device types
- ✅ Follows existing code patterns and best practices
- ✅ Includes comprehensive documentation and testing guides

