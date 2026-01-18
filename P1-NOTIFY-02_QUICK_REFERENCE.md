# P1-NOTIFY-02: Push Notifications - Quick Reference

## API Endpoints

### Admin Endpoints

**POST /api/v1/admin/push-notifications/send**
Send to specific users
```json
{
  "user_ids": ["uuid1", "uuid2"],
  "title": "Title",
  "body": "Message",
  "notification_type": "system",
  "data_payload": {},
  "scheduled_for": "2025-01-20T10:00:00Z"  // Optional
}
```

**POST /api/v1/admin/push-notifications/broadcast**
Broadcast to all eligible users
```json
{
  "title": "Announcement",
  "body": "Message",
  "notification_type": "system",
  "user_role": "teacher"  // Optional filter
}
```

**GET /api/v1/admin/push-notifications**
List all notifications
- Query params: `user_id`, `status`, `notification_type`, `limit`, `offset`

### User Endpoints

**GET /api/v1/notifications/history**
Get user's notification history
- Query params: `limit`, `offset`

## Notification Types

1. **streak_reminder** - Streak at risk
2. **daily_mission** - New missions available
3. **achievement** - Badge/achievement unlocked
4. **social** - Social interactions (follows, likes)
5. **system** - System announcements

## Service Functions

```python
from backend.services import push_notifications

# Quick helpers
push_notifications.send_streak_reminder(db, user_id, current_streak)
push_notifications.send_daily_mission_notification(db, user_id)
push_notifications.send_achievement_notification(db, user_id, name, id)
push_notifications.send_social_notification(db, user_id, message, data)
push_notifications.send_system_notification(db, user_id, title, body, data)

# Manual creation
notification = push_notifications.create_notification(
    db=db,
    user_id=user_id,
    title="Title",
    body="Body",
    notification_type=NotificationType.system,
    data_payload={"key": "value"},
    scheduled_for=None  # or datetime for scheduling
)

# Send immediately
success = push_notifications.send_notification(db, notification)

# Broadcast
results = push_notifications.broadcast_notification(
    db=db,
    title="Title",
    body="Body",
    notification_type=NotificationType.system,
    user_role="learner"  # Optional
)
```

## Environment Variables

```bash
FCM_CREDENTIALS_PATH=/path/to/firebase-credentials.json
PUSH_NOTIFICATION_BATCH_SIZE=500
PUSH_NOTIFICATION_MAX_RETRIES=3
```

## Database Migration

```bash
alembic upgrade head
```

## Files

- **Model**: `backend/models.py` → `PushNotification`
- **Service**: `backend/services/push_notifications.py`
- **Schemas**: `backend/schemas.py` → Push notification schemas
- **Migration**: `migrations/versions/0032_push_notifications.py`
- **Config**: `backend/config.py` → FCM settings

## Status Flow

```
pending → sent → delivered
   ↓
 failed (with retry logic)
```

## Permission Checks

Before sending, the service verifies:
- ✓ User has `push_enabled=true`
- ✓ User has `push_token` registered
- ✓ Not in quiet hours
- ✓ Type-specific preferences (streak_reminders, daily_mission_reminders)

