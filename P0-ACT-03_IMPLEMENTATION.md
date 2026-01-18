# P0-ACT-03: Push Notifications Permission Prompt Implementation

## Overview

This document describes the implementation of the push notifications permission prompt system that shows after the first lesson completion.

## Implementation Date

January 17, 2025

## Feature Summary

The system prompts users for push notification permission after they complete their first lesson. This ensures users understand the value of notifications before being asked to grant permission.

## Components Implemented

### 1. Database Models

#### UserNotificationSettings Model

Located in `backend/models.py`, this model stores user notification preferences and push token information.

**Fields:**
- `id`: UUID primary key
- `user_id`: Foreign key to users table (unique, cascades on delete)
- `push_enabled`: Boolean, default false
- `push_token`: Text, nullable (FCM/APNS token)
- `push_platform`: String(20), nullable (ios/android/web)
- `email_enabled`: Boolean, default true
- `streak_reminders`: Boolean, default true
- `daily_mission_reminders`: Boolean, default true
- `weekly_digest`: Boolean, default true
- `marketing_enabled`: Boolean, default false
- `quiet_hours_start`: Integer, nullable (0-23 hour)
- `quiet_hours_end`: Integer, nullable (0-23 hour)
- `created_at`: DateTime with timezone
- `updated_at`: DateTime with timezone

**Relationships:**
- One-to-one with User model via `notification_settings` relationship

#### User Model Update

Added `push_permission_prompted` field to track whether the user has been shown the permission prompt.

**Field:**
- `push_permission_prompted`: Boolean, default false

### 2. Database Migration

**File:** `migrations/versions/0014_notification_settings.py`

**Changes:**
- Adds `push_permission_prompted` column to `users` table
- Creates `user_notification_settings` table
- Creates index on `user_id` for efficient lookups

**Migration Commands:**
```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 3. API Schemas

Located in `backend/schemas.py`:

#### NotificationSettingsOut
Output schema for notification settings with all fields.

#### NotificationSettingsUpdateIn
Input schema for updating notification preferences with optional fields.

#### PushTokenRegisterIn
Input schema for registering push notification tokens.
- Validates platform is one of: ios, android, web

#### PushTokenRegisterOut
Response schema for token registration operations.

#### ShouldPromptPermissionOut
Response schema for checking if user should be prompted for permission.

### 4. API Endpoints

All endpoints require JWT authentication.

#### GET /api/v1/notifications/settings

Get user's notification settings. Creates default settings if they don't exist.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "push_enabled": false,
  "push_token": null,
  "push_platform": null,
  "email_enabled": true,
  "streak_reminders": true,
  "daily_mission_reminders": true,
  "weekly_digest": true,
  "marketing_enabled": false,
  "quiet_hours_start": null,
  "quiet_hours_end": null,
  "created_at": "2025-01-17T10:00:00Z",
  "updated_at": "2025-01-17T10:00:00Z"
}
```

#### PUT /api/v1/notifications/settings

Update user's notification settings.

**Request:**
```json
{
  "push_enabled": true,
  "streak_reminders": true,
  "daily_mission_reminders": false,
  "quiet_hours_start": 22,
  "quiet_hours_end": 8
}
```

**Response:** Same as GET endpoint

#### POST /api/v1/notifications/register-push

Register or update push notification token.

**Request:**
```json
{
  "token": "fcm-or-apns-device-token",
  "platform": "ios"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Push notification token registered successfully"
}
```

**Side Effects:**
- Sets `push_permission_prompted` to true on the user
- Enables push notifications
- Stores the token and platform

#### DELETE /api/v1/notifications/unregister-push

Remove push notification token.

**Response:**
```json
{
  "success": true,
  "message": "Push notification token unregistered successfully"
}
```

#### GET /api/v1/notifications/should-prompt-permission

Check if the app should prompt the user for push notification permission.

**Logic:**
Returns `true` if:
1. User has NOT been prompted before (`push_permission_prompted` is false)
2. User has completed at least 1 lesson (`lesson_viewed_at` is not null)

**Response:**
```json
{
  "should_prompt": true,
  "reason": "User is eligible for push notification prompt"
}
```

Or if not eligible:
```json
{
  "should_prompt": false,
  "reason": "User has already been prompted for push notifications"
}
```

## Usage Flow

### Mobile App Integration

1. **After Lesson Completion:**
   - Call `GET /api/v1/notifications/should-prompt-permission`
   - If `should_prompt` is true, show permission dialog

2. **User Grants Permission:**
   - Get FCM/APNS token from device
   - Call `POST /api/v1/notifications/register-push` with token and platform
   - Backend automatically sets `push_permission_prompted` to true

3. **User Denies Permission:**
   - Call `PUT /api/v1/notifications/settings` with `push_enabled: false`
   - Optionally mark as prompted (future enhancement)

4. **Settings Screen:**
   - Call `GET /api/v1/notifications/settings` to display current preferences
   - Call `PUT /api/v1/notifications/settings` to update preferences
   - Handle token registration/unregistration separately

### Backend Integration

The system is ready for integration with push notification services:

1. **Sending Notifications:**
   ```python
   # Get users with push enabled
   users_with_push = db.execute(
       select(User, UserNotificationSettings)
       .join(UserNotificationSettings)
       .where(
           UserNotificationSettings.push_enabled == True,
           UserNotificationSettings.push_token.isnot(None)
       )
   ).all()
   
   for user, settings in users_with_push:
       # Check quiet hours
       # Check specific notification preferences
       # Send via FCM/APNS using settings.push_token
   ```

2. **Respecting Preferences:**
   - Check `streak_reminders` before sending streak notifications
   - Check `daily_mission_reminders` before sending mission reminders
   - Respect `quiet_hours_start` and `quiet_hours_end`

## Testing

### API Testing Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
TOKEN="your-jwt-token"

# Get notification settings
curl -X GET "$BASE_URL/api/v1/notifications/settings" \
  -H "Authorization: Bearer $TOKEN"

# Update notification settings
curl -X PUT "$BASE_URL/api/v1/notifications/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "streak_reminders": true,
    "daily_mission_reminders": true,
    "quiet_hours_start": 22,
    "quiet_hours_end": 8
  }'

# Check if should prompt
curl -X GET "$BASE_URL/api/v1/notifications/should-prompt-permission" \
  -H "Authorization: Bearer $TOKEN"

# Register push token
curl -X POST "$BASE_URL/api/v1/notifications/register-push" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "test-fcm-token-123",
    "platform": "ios"
  }'

# Unregister push token
curl -X DELETE "$BASE_URL/api/v1/notifications/unregister-push" \
  -H "Authorization: Bearer $TOKEN"
```

## Files Modified

1. `backend/models.py`
   - Added `UserNotificationSettings` model
   - Added `push_permission_prompted` to User model
   - Added relationship between User and UserNotificationSettings

2. `backend/schemas.py`
   - Added notification-related schemas

3. `backend/main.py`
   - Added UserNotificationSettings to imports
   - Added 5 notification API endpoints

4. `migrations/versions/0014_notification_settings.py`
   - New migration file

## Deployment Checklist

- [ ] Review code changes
- [ ] Run database migration on staging
- [ ] Test all API endpoints
- [ ] Verify permission prompt logic
- [ ] Test with mobile app
- [ ] Run migration on production
- [ ] Monitor error logs
- [ ] Document any issues

## Future Enhancements

1. **Notification Scheduler:**
   - Background job to send scheduled notifications
   - Integration with FCM/APNS
   - Respect user preferences and quiet hours

2. **Analytics:**
   - Track permission grant/deny rates
   - Track notification engagement
   - A/B test permission prompt timing

3. **Rich Notifications:**
   - Support for images, actions
   - Deep linking to specific content

4. **Email Notifications:**
   - Implement email notification system
   - Use `email_enabled` flag

## Notes

- The system creates default notification settings on first access
- Token registration automatically marks user as prompted
- Quiet hours are stored as integers (0-23) representing hours
- All timestamps use UTC with timezone awareness
- The system is platform-agnostic (supports iOS, Android, Web)

## Support

For issues or questions, refer to:
- Backend API code: `backend/main.py` (notification endpoints)
- Models: `backend/models.py` (UserNotificationSettings)
- Schemas: `backend/schemas.py` (notification schemas)
- Migration: `migrations/versions/0014_notification_settings.py`

