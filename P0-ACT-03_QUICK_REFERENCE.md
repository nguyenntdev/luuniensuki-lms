# P0-ACT-03: Quick Reference Guide

## Quick Commands

### Database Migration

```bash
# Apply migration
cd /path/to/luuniensuki-lms
alembic upgrade head

# Rollback
alembic downgrade -1
```

### API Endpoints

All endpoints require `Authorization: Bearer <token>` header.

```bash
# Check if should prompt for permission
GET /api/v1/notifications/should-prompt-permission

# Get notification settings
GET /api/v1/notifications/settings

# Update notification settings
PUT /api/v1/notifications/settings

# Register push token
POST /api/v1/notifications/register-push

# Unregister push token
DELETE /api/v1/notifications/unregister-push
```

## Key Concepts

### When to Prompt?

The app should check `GET /api/v1/notifications/should-prompt-permission` after each lesson completion.

**Returns true when:**
- User hasn't been prompted before
- User has completed at least 1 lesson

### Permission Flow

```
User completes first lesson
    ↓
Check should-prompt-permission endpoint
    ↓
If should_prompt = true → Show native permission dialog
    ↓
User accepts → Register token → Backend marks as prompted
    ↓
User declines → Update settings push_enabled=false
```

## Database Schema

### user_notification_settings

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| id | UUID | uuid4() | Primary key |
| user_id | UUID | - | Foreign key to users |
| push_enabled | bool | false | Push notifications enabled |
| push_token | text | null | FCM/APNS token |
| push_platform | varchar(20) | null | ios/android/web |
| email_enabled | bool | true | Email notifications enabled |
| streak_reminders | bool | true | Streak reminder preference |
| daily_mission_reminders | bool | true | Daily mission reminder preference |
| weekly_digest | bool | true | Weekly digest preference |
| marketing_enabled | bool | false | Marketing emails preference |
| quiet_hours_start | int | null | Quiet hours start (0-23) |
| quiet_hours_end | int | null | Quiet hours end (0-23) |
| created_at | timestamp | now() | Creation timestamp |
| updated_at | timestamp | now() | Last update timestamp |

### users (updated)

Added field:
- `push_permission_prompted` (bool, default: false)

## Code Examples

### Check if Should Prompt (Frontend)

```dart
Future<bool> shouldPromptForNotifications() async {
  final response = await dio.get(
    '/api/v1/notifications/should-prompt-permission',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return response.data['should_prompt'] as bool;
}
```

### Register Push Token (Frontend)

```dart
Future<void> registerPushToken(String token, String platform) async {
  await dio.post(
    '/api/v1/notifications/register-push',
    data: {'token': token, 'platform': platform},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
}
```

### Update Settings (Frontend)

```dart
Future<void> updateNotificationSettings({
  bool? streakReminders,
  int? quietHoursStart,
  int? quietHoursEnd,
}) async {
  await dio.put(
    '/api/v1/notifications/settings',
    data: {
      if (streakReminders != null) 'streak_reminders': streakReminders,
      if (quietHoursStart != null) 'quiet_hours_start': quietHoursStart,
      if (quietHoursEnd != null) 'quiet_hours_end': quietHoursEnd,
    },
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
}
```

### Send Notification (Backend - Future)

```python
from sqlalchemy import select

# Get users to notify for streaks
users_to_notify = db.execute(
    select(User, UserNotificationSettings)
    .join(UserNotificationSettings)
    .where(
        UserNotificationSettings.push_enabled == True,
        UserNotificationSettings.streak_reminders == True,
        UserNotificationSettings.push_token.isnot(None),
        # Add your business logic here
    )
).all()

for user, settings in users_to_notify:
    # Check quiet hours before sending
    # Send to FCM/APNS using settings.push_token
    pass
```

## Testing Checklist

- [ ] Migration applies successfully
- [ ] Get settings creates default settings
- [ ] Update settings works with partial updates
- [ ] Register token sets prompted flag
- [ ] Unregister token clears token and platform
- [ ] Should prompt returns false after first lesson
- [ ] Should prompt returns true after being prompted
- [ ] Platform validation works (rejects invalid platforms)
- [ ] Quiet hours validation (0-23 range)

## Common Issues

### "Should prompt always returns false"

Check if:
1. User has completed at least one lesson (lesson_viewed_at is not null in user_progress)
2. push_permission_prompted is false on the user record

### "Settings not persisting"

Verify:
1. Database migration ran successfully
2. user_notification_settings table exists
3. Unique constraint on user_id is present

## Files Changed

- `backend/models.py` - Added UserNotificationSettings, updated User
- `backend/schemas.py` - Added notification schemas
- `backend/main.py` - Added 5 notification endpoints
- `migrations/versions/0014_notification_settings.py` - New migration

## Next Steps

1. Run database migration
2. Test API endpoints
3. Integrate with mobile app
4. Implement FCM/APNS sender service
5. Add notification scheduling system

