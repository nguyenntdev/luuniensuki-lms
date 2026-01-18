# P0-ACT-03: Notification API Reference

## Overview

Complete API reference for push notification permission prompt and notification settings management.

**Base URL:** `/api/v1/notifications`

**Authentication:** All endpoints require JWT bearer token authentication.

## Endpoints

### 1. Get Notification Settings

Retrieve the current user's notification settings. Creates default settings if they don't exist.

**Endpoint:** `GET /api/v1/notifications/settings`

**Authentication:** Required

**Parameters:** None

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
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

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token

---

### 2. Update Notification Settings

Update the current user's notification preferences.

**Endpoint:** `PUT /api/v1/notifications/settings`

**Authentication:** Required

**Request Body:**

```json
{
  "push_enabled": true,
  "email_enabled": true,
  "streak_reminders": false,
  "daily_mission_reminders": true,
  "weekly_digest": true,
  "marketing_enabled": false,
  "quiet_hours_start": 22,
  "quiet_hours_end": 8
}
```

All fields are optional. Only provided fields will be updated.

**Field Constraints:**
- `quiet_hours_start`: Integer 0-23 (hour of day)
- `quiet_hours_end`: Integer 0-23 (hour of day)

**Response:** `200 OK`

Returns the updated notification settings (same format as GET).

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token
- `422 Unprocessable Entity` - Validation error (e.g., quiet_hours out of range)

---

### 3. Register Push Notification Token

Register or update the user's push notification device token.

**Endpoint:** `POST /api/v1/notifications/register-push`

**Authentication:** Required

**Request Body:**

```json
{
  "token": "fcm-or-apns-device-token-string",
  "platform": "ios"
}
```

**Fields:**
- `token` (required): FCM or APNS device token string
- `platform` (required): Must be one of: `ios`, `android`, `web`

**Side Effects:**
- Sets `push_enabled` to `true`
- Sets `push_permission_prompted` to `true` on the user record
- Stores the token and platform

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Push notification token registered successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token
- `422 Unprocessable Entity` - Invalid platform or missing required fields

---

### 4. Unregister Push Notification Token

Remove the user's push notification token and disable push notifications.

**Endpoint:** `DELETE /api/v1/notifications/unregister-push`

**Authentication:** Required

**Parameters:** None

**Side Effects:**
- Clears `push_token` and `push_platform`
- Sets `push_enabled` to `false`

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Push notification token unregistered successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token

---

### 5. Check If Should Prompt for Permission

Check if the app should display the push notification permission prompt to the user.

**Endpoint:** `GET /api/v1/notifications/should-prompt-permission`

**Authentication:** Required

**Parameters:** None

**Logic:**

Returns `should_prompt: true` when:
1. User has NOT been prompted before (`push_permission_prompted` is `false`)
2. User has completed at least 1 lesson (`lesson_viewed_at IS NOT NULL` in `user_progress`)

**Response:** `200 OK`

When user should be prompted:
```json
{
  "should_prompt": true,
  "reason": "User is eligible for push notification prompt"
}
```

When user should NOT be prompted (already prompted):
```json
{
  "should_prompt": false,
  "reason": "User has already been prompted for push notifications"
}
```

When user should NOT be prompted (no lessons completed):
```json
{
  "should_prompt": false,
  "reason": "User has not completed any lessons yet"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token

---

## Data Models

### NotificationSettingsOut

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Settings record ID |
| user_id | UUID | User ID |
| push_enabled | boolean | Whether push notifications are enabled |
| push_token | string \| null | FCM/APNS device token |
| push_platform | string \| null | Platform: ios, android, or web |
| email_enabled | boolean | Whether email notifications are enabled |
| streak_reminders | boolean | Send streak reminder notifications |
| daily_mission_reminders | boolean | Send daily mission reminders |
| weekly_digest | boolean | Send weekly digest emails |
| marketing_enabled | boolean | Receive marketing communications |
| quiet_hours_start | integer \| null | Quiet hours start (0-23) |
| quiet_hours_end | integer \| null | Quiet hours end (0-23) |
| created_at | datetime | When settings were created |
| updated_at | datetime | When settings were last updated |

### NotificationSettingsUpdateIn

All fields optional for partial updates:

| Field | Type | Constraints |
|-------|------|-------------|
| push_enabled | boolean | - |
| email_enabled | boolean | - |
| streak_reminders | boolean | - |
| daily_mission_reminders | boolean | - |
| weekly_digest | boolean | - |
| marketing_enabled | boolean | - |
| quiet_hours_start | integer | 0-23 |
| quiet_hours_end | integer | 0-23 |

### PushTokenRegisterIn

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| token | string | Yes | Min length: 1 |
| platform | string | Yes | Must be: ios, android, or web |

### PushTokenRegisterOut

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| message | string | Human-readable message |

### ShouldPromptPermissionOut

| Field | Type | Description |
|-------|------|-------------|
| should_prompt | boolean | Whether to show permission prompt |
| reason | string \| null | Explanation of the decision |

## Usage Examples

### cURL

```bash
# Get settings
curl -X GET "https://api.example.com/api/v1/notifications/settings" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update settings
curl -X PUT "https://api.example.com/api/v1/notifications/settings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"streak_reminders": true, "quiet_hours_start": 22}'

# Register token
curl -X POST "https://api.example.com/api/v1/notifications/register-push" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "fcm-token-123", "platform": "ios"}'

# Check should prompt
curl -X GET "https://api.example.com/api/v1/notifications/should-prompt-permission" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### JavaScript / TypeScript (Axios)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.example.com',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Get settings
const settings = await api.get('/api/v1/notifications/settings');
console.log(settings.data);

// Update settings
await api.put('/api/v1/notifications/settings', {
  streak_reminders: true,
  quiet_hours_start: 22,
  quiet_hours_end: 8
});

// Register push token
await api.post('/api/v1/notifications/register-push', {
  token: fcmToken,
  platform: 'web'
});

// Check should prompt
const { data } = await api.get('/api/v1/notifications/should-prompt-permission');
if (data.should_prompt) {
  // Show permission dialog
}
```

### Dart / Flutter (Dio)

```dart
import 'package:dio/dio.dart';

final dio = Dio(BaseOptions(
  baseUrl: 'https://api.example.com',
  headers: {'Authorization': 'Bearer $token'},
));

// Get settings
final settings = await dio.get('/api/v1/notifications/settings');
print(settings.data);

// Update settings
await dio.put('/api/v1/notifications/settings', data: {
  'streak_reminders': true,
  'quiet_hours_start': 22,
  'quiet_hours_end': 8,
});

// Register push token
await dio.post('/api/v1/notifications/register-push', data: {
  'token': fcmToken,
  'platform': 'ios',
});

// Check should prompt
final response = await dio.get('/api/v1/notifications/should-prompt-permission');
if (response.data['should_prompt'] == true) {
  // Show permission dialog
}
```

### Python (requests)

```python
import requests

headers = {'Authorization': f'Bearer {token}'}
base_url = 'https://api.example.com'

# Get settings
response = requests.get(f'{base_url}/api/v1/notifications/settings', headers=headers)
settings = response.json()

# Update settings
requests.put(
    f'{base_url}/api/v1/notifications/settings',
    headers=headers,
    json={
        'streak_reminders': True,
        'quiet_hours_start': 22,
        'quiet_hours_end': 8
    }
)

# Register push token
requests.post(
    f'{base_url}/api/v1/notifications/register-push',
    headers=headers,
    json={'token': fcm_token, 'platform': 'android'}
)

# Check should prompt
response = requests.get(
    f'{base_url}/api/v1/notifications/should-prompt-permission',
    headers=headers
)
should_prompt = response.json()['should_prompt']
```

## Integration Guide

### Mobile App Flow

#### Step 1: After First Lesson Completion

After the user completes their first lesson, check if you should show the permission prompt:

```dart
Future<void> onLessonCompleted() async {
  // Mark lesson as completed via your normal API
  await completeLesson(lessonId);

  // Check if should prompt for notifications
  final response = await dio.get('/api/v1/notifications/should-prompt-permission');

  if (response.data['should_prompt'] == true) {
    // Show your permission prompt UI
    showNotificationPermissionDialog();
  }
}
```

#### Step 2: Handle Permission Grant

When the user grants permission:

```dart
Future<void> onPermissionGranted() async {
  // Request native permission
  final permission = await FirebaseMessaging.instance.requestPermission();

  if (permission.authorizationStatus == AuthorizationStatus.authorized) {
    // Get FCM token
    final token = await FirebaseMessaging.instance.getToken();

    // Register with backend
    await dio.post('/api/v1/notifications/register-push', data: {
      'token': token,
      'platform': Platform.isIOS ? 'ios' : 'android',
    });
  }
}
```

#### Step 3: Handle Permission Denial

When the user denies permission:

```dart
Future<void> onPermissionDenied() async {
  // Update settings to reflect user's choice
  await dio.put('/api/v1/notifications/settings', data: {
    'push_enabled': false,
  });
}
```

### Settings Screen Integration

```dart
class NotificationSettingsScreen extends StatefulWidget {
  @override
  State<NotificationSettingsScreen> createState() => _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState extends State<NotificationSettingsScreen> {
  NotificationSettings? _settings;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final response = await dio.get('/api/v1/notifications/settings');
    setState(() {
      _settings = NotificationSettings.fromJson(response.data);
    });
  }

  Future<void> _updateSetting(String key, bool value) async {
    await dio.put('/api/v1/notifications/settings', data: {key: value});
    await _loadSettings(); // Refresh
  }

  @override
  Widget build(BuildContext context) {
    if (_settings == null) return CircularProgressIndicator();

    return ListView(
      children: [
        SwitchListTile(
          title: Text('Streak Reminders'),
          value: _settings!.streakReminders,
          onChanged: (value) => _updateSetting('streak_reminders', value),
        ),
        SwitchListTile(
          title: Text('Daily Mission Reminders'),
          value: _settings!.dailyMissionReminders,
          onChanged: (value) => _updateSetting('daily_mission_reminders', value),
        ),
        // Add more settings...
      ],
    );
  }
}
```

## Error Handling

### Common Error Scenarios

#### 1. Invalid Platform

**Request:**
```json
{
  "token": "some-token",
  "platform": "invalid"
}
```

**Response:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "platform"],
      "msg": "Platform must be one of: ios, android, web",
      "type": "value_error"
    }
  ]
}
```

#### 2. Missing Authentication

**Response:** `401 Unauthorized`
```json
{
  "detail": "Not authenticated"
}
```

#### 3. Invalid Quiet Hours

**Request:**
```json
{
  "quiet_hours_start": 25
}
```

**Response:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "quiet_hours_start"],
      "msg": "ensure this value is less than or equal to 23",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## Best Practices

1. **Check permission status before showing prompt**
   - Always call `should-prompt-permission` endpoint first
   - Don't prompt users who have already been asked

2. **Handle token refresh**
   - FCM tokens can change - re-register when they do
   - Call `register-push` with the new token

3. **Respect user preferences**
   - Check notification settings before sending
   - Honor quiet hours
   - Don't send if category is disabled

4. **Graceful degradation**
   - If push notifications fail, fall back to email
   - Don't break app if notification service is down

5. **Privacy**
   - Only send notifications user has opted into
   - Allow granular control over notification types
   - Make it easy to disable notifications

## Rate Limiting

Currently no rate limiting on notification endpoints. Consider implementing if needed:

- Registration: 10 requests per minute
- Settings updates: 30 requests per minute
- Settings read: 100 requests per minute

## Changelog

- **2025-01-17**: Initial implementation of P0-ACT-03
  - Added all 5 notification endpoints
  - Created notification settings model
  - Added push permission tracking


