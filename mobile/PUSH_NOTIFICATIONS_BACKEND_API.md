# Backend FCM Token Endpoints

The mobile app requires the following backend endpoints to support push notifications:

## 1. Register FCM Token

**Endpoint:** `POST /api/notifications/register-token`

**Description:** Register a user's FCM token for push notifications

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "fcm_token": "string",
  "user_id": "string (UUID)",
  "platform": "string (android/ios)",
  "timestamp": "string (ISO 8601)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Token registered successfully"
}
```

**Database Schema Addition Needed:**
```python
# Add to models.py
class FCMToken(Base):
    __tablename__ = 'fcm_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String, nullable=False, unique=True)
    platform = Column(String, nullable=False)  # 'android' or 'ios'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="fcm_tokens")
```

---

## 2. Unregister FCM Token

**Endpoint:** `POST /api/notifications/unregister-token`

**Description:** Remove a user's FCM token (e.g., on logout)

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "fcm_token": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Token unregistered successfully"
}
```

---

## 3. Update Notification Preferences

**Endpoint:** `PUT /api/notifications/preferences`

**Description:** Update user's notification preferences

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "preferences": {
    "streakReminders": true,
    "dailyGoalReminders": true,
    "achievementNotifications": true,
    "leaderboardUpdates": true,
    "newContentNotifications": true,
    "questNotifications": true,
    "badgeNotifications": true,
    "levelUpNotifications": true,
    "friendActivityNotifications": true,
    "systemAnnouncements": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "preferences": { /* updated preferences */ }
}
```

**Database Schema Addition Needed:**
```python
# Add to models.py
class NotificationPreferences(Base):
    __tablename__ = 'notification_preferences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False)
    
    # Preference flags
    streak_reminders = Column(Boolean, default=True)
    daily_goal_reminders = Column(Boolean, default=True)
    achievement_notifications = Column(Boolean, default=True)
    leaderboard_updates = Column(Boolean, default=True)
    new_content_notifications = Column(Boolean, default=True)
    quest_notifications = Column(Boolean, default=True)
    badge_notifications = Column(Boolean, default=True)
    level_up_notifications = Column(Boolean, default=True)
    friend_activity_notifications = Column(Boolean, default=True)
    system_announcements = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
```

---

## 4. Get Notification Preferences

**Endpoint:** `GET /api/notifications/preferences`

**Description:** Get user's current notification preferences

**Authentication:** Required (JWT)

**Response:**
```json
{
  "preferences": {
    "streakReminders": true,
    "dailyGoalReminders": true,
    "achievementNotifications": true,
    "leaderboardUpdates": true,
    "newContentNotifications": true,
    "questNotifications": true,
    "badgeNotifications": true,
    "levelUpNotifications": true,
    "friendActivityNotifications": true,
    "systemAnnouncements": true
  }
}
```

---

## 5. Mark Notification as Read

**Endpoint:** `POST /api/notifications/{notification_id}/read`

**Description:** Mark a specific notification as read

**Authentication:** Required (JWT)

**Response:**
```json
{
  "success": true
}
```

---

## 6. Get Notification History

**Endpoint:** `GET /api/notifications/history`

**Description:** Get user's notification history

**Authentication:** Required (JWT)

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "items": [
    {
      "id": "string (UUID)",
      "type": "string (notification type)",
      "title": "string",
      "message": "string",
      "timestamp": "string (ISO 8601)",
      "is_read": "boolean",
      "action_url": "string (optional)",
      "metadata": { /* optional metadata */ }
    }
  ],
  "total": "number",
  "page": "number",
  "limit": "number"
}
```

---

## Implementation Notes

### 1. Firebase Admin SDK Setup

You'll need to install Firebase Admin SDK in the backend:

```bash
pip install firebase-admin
```

### 2. Initialize Firebase Admin

```python
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
```

### 3. Send Push Notification Function

```python
def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict = None,
    notification_type: str = "system_announcement"
):
    """Send a push notification to a specific device"""
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            "type": notification_type,
            **(data or {})
        },
        token=token,
    )
    
    try:
        response = messaging.send(message)
        print(f'Successfully sent message: {response}')
        return True
    except Exception as e:
        print(f'Error sending message: {e}')
        return False
```

### 4. Topic-based Notifications

```python
def send_topic_notification(
    topic: str,
    title: str,
    body: str,
    data: dict = None,
):
    """Send notification to all users subscribed to a topic"""
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        topic=topic,
    )
    
    messaging.send(message)
```

### 5. Usage Examples

```python
# When user achieves something
send_push_notification(
    token=user.fcm_token,
    title="Huy hiệu mới!",
    body="Bạn đã mở khóa huy hiệu 'Người khám phá'",
    notification_type="achievement_unlocked",
    data={
        "action": "open_achievement",
        "achievement_id": "first-discovery"
    }
)

# Daily streak reminder (topic-based)
send_topic_notification(
    topic="streak_reminders",
    title="Đừng quên học hôm nay!",
    body="Duy trì chuỗi học tập của bạn 🔥",
    data={
        "type": "streak_reminder",
        "action": "open_home"
    }
)
```

---

## Required Environment Variables

Add to `.env`:

```bash
# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
```

---

## Testing

You can test FCM notifications using:

1. **Firebase Console**: Send test notifications from the Firebase Console
2. **Postman**: Use FCM REST API to send test notifications
3. **Backend Admin Panel**: Create admin endpoint to send test notifications

Example test curl:

```bash
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: key=YOUR_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "DEVICE_FCM_TOKEN",
    "notification": {
      "title": "Test Notification",
      "body": "This is a test notification"
    },
    "data": {
      "type": "system_announcement"
    }
  }'
```

