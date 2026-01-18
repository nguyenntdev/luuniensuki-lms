# P0-ANA-03: Session Tracking Quick Reference

## 🎯 Overview
Real-time session tracking system for monitoring active users and collecting session analytics.

## 🔑 Key Metrics

### Active Sessions
- **Last 5 minutes**: Users with heartbeat in last 5 min (truly active)
- **Last 30 minutes**: Users with heartbeat in last 30 min (recently active)
- **Auto-expire**: Sessions without heartbeat for 30+ min are marked inactive

### Session Duration
- Calculated only for ended sessions
- Measured from `started_at` to `ended_at`
- Average displayed in minutes

## 📡 API Endpoints

### User Endpoints

#### POST `/api/v1/sessions/heartbeat`
**Purpose**: Keep session alive, track activity  
**Frequency**: Every 30 seconds  
**Auth**: Required  

**Request**:
```json
{
  "session_id": "uuid",
  "device_type": "mobile|web|tablet",
  "platform": "ios|android|web",
  "app_version": "1.0.0"
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

#### POST `/api/v1/sessions/end`
**Purpose**: Gracefully end session  
**When**: On logout, app close  
**Auth**: Required  

**Request**:
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

### Admin Endpoints

#### GET `/api/v1/admin/analytics/sessions/active`
**Purpose**: Real-time active session count  
**Auth**: Admin role  

**Response**:
```json
{
  "active_sessions": 42,
  "last_5_minutes": 42,
  "last_30_minutes": 67,
  "timestamp": "2025-01-17T12:00:00Z"
}
```

#### GET `/api/v1/admin/analytics/sessions/stats`
**Purpose**: Comprehensive session analytics  
**Auth**: Admin role  

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
  "by_platform": {"ios": 1200, "android": 1500, "web": 800},
  "by_device_type": {"mobile": 2700, "tablet": 300, "web": 500}
}
```

## 🔧 Database Schema

```sql
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),  -- nullable for anonymous
  session_id UUID UNIQUE NOT NULL,
  started_at TIMESTAMP WITH TIME ZONE NOT NULL,
  last_active_at TIMESTAMP WITH TIME ZONE NOT NULL,
  ended_at TIMESTAMP WITH TIME ZONE,
  device_type VARCHAR(20) NOT NULL,  -- mobile, web, tablet
  platform VARCHAR(20) NOT NULL,     -- ios, android, web
  app_version VARCHAR(20),
  is_active BOOLEAN NOT NULL DEFAULT true
);

-- Indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX idx_user_sessions_last_active ON user_sessions(last_active_at);
CREATE INDEX idx_user_sessions_started_at ON user_sessions(started_at);
```

## 🔍 Useful SQL Queries

### Current Active Users
```sql
SELECT COUNT(*) 
FROM user_sessions 
WHERE is_active = true 
  AND last_active_at > NOW() - INTERVAL '5 minutes';
```

### Today's Sessions
```sql
SELECT COUNT(*) 
FROM user_sessions 
WHERE started_at >= CURRENT_DATE;
```

### Average Session Duration by Platform
```sql
SELECT 
  platform,
  AVG(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60) as avg_minutes
FROM user_sessions 
WHERE ended_at IS NOT NULL
GROUP BY platform;
```

### Peak Concurrent Today
```sql
SELECT MAX(concurrent) as peak
FROM (
  SELECT 
    DATE_TRUNC('minute', started_at) as minute,
    COUNT(*) as concurrent
  FROM user_sessions
  WHERE started_at >= CURRENT_DATE
  GROUP BY minute
) subquery;
```

## 🧪 Testing Commands

### Run Full Test Suite
```bash
./test_session_tracking.sh
```

### Manual Testing
```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r .access_token)

# 2. Send Heartbeat
SESSION_ID=$(uuidgen)
curl -X POST http://localhost/api/v1/sessions/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"device_type\": \"web\",
    \"platform\": \"web\"
  }" | jq

# 3. End Session
curl -X POST http://localhost/api/v1/sessions/end \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" | jq
```

## 📱 Client Implementation

### React Native Example
```javascript
import { v4 as uuidv4 } from 'uuid';
import { Platform } from 'react-native';

class SessionManager {
  constructor() {
    this.sessionId = null;
    this.heartbeatInterval = null;
  }

  start() {
    this.sessionId = uuidv4();
    this.sendHeartbeat();
    this.heartbeatInterval = setInterval(() => this.sendHeartbeat(), 30000);
  }

  async sendHeartbeat() {
    await api.post('/sessions/heartbeat', {
      session_id: this.sessionId,
      device_type: 'mobile',
      platform: Platform.OS,
      app_version: '1.5.0',
    });
  }

  async end() {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    if (this.sessionId) {
      await api.post('/sessions/end', { session_id: this.sessionId });
    }
  }
}
```

### Web Example
```javascript
class SessionManager {
  constructor() {
    this.sessionId = crypto.randomUUID();
    this.heartbeatInterval = null;
  }

  start() {
    this.sendHeartbeat();
    this.heartbeatInterval = setInterval(() => this.sendHeartbeat(), 30000);
    
    // End session on page unload
    window.addEventListener('beforeunload', () => this.end());
  }

  async sendHeartbeat() {
    await fetch('/api/v1/sessions/heartbeat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: this.sessionId,
        device_type: 'web',
        platform: 'web',
        app_version: APP_VERSION,
      }),
    });
  }

  async end() {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    await fetch('/api/v1/sessions/end', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: this.sessionId }),
    });
  }
}
```

## 📊 Admin Dashboard Usage

```javascript
// Poll active sessions every 10 seconds
const pollActiveSessions = async () => {
  const response = await fetch('/api/v1/admin/analytics/sessions/active', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  const data = await response.json();
  
  updateDashboard({
    activeUsers: data.last_5_minutes,
    recentUsers: data.last_30_minutes,
  });
};

setInterval(pollActiveSessions, 10000);

// Fetch detailed stats once per minute
const fetchStats = async () => {
  const response = await fetch('/api/v1/admin/analytics/sessions/stats', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  const stats = await response.json();
  
  updateCharts({
    platforms: stats.by_platform,
    devices: stats.by_device_type,
    avgDuration: stats.avg_session_duration_minutes,
  });
};

setInterval(fetchStats, 60000);
```

## ⚡ Performance Tips

1. **Indexes**: All critical queries use indexes
2. **Batch Updates**: Client should batch heartbeats if offline
3. **Cleanup**: Run periodic cleanup of old sessions (optional background job)
4. **Caching**: Admin endpoints can be cached for 10-30 seconds

## 🔒 Security Notes

- Users can only update their own sessions
- Session ID must match user ID
- Admin endpoints require admin role
- Anonymous sessions supported (user_id nullable)

## 📝 Files Modified

- `backend/models.py` - UserSession model
- `backend/schemas.py` - Session schemas  
- `backend/main.py` - Session endpoints
- `migrations/versions/0017_user_sessions.py` - Migration

## 🚀 Deployment

```bash
# Apply migration
docker compose exec api alembic upgrade head

# Restart API
docker compose restart api

# Verify
curl http://localhost/api/v1/admin/analytics/sessions/active \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

