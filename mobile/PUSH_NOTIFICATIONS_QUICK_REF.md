# Push Notifications - Quick Reference

## 🚀 Quick Start

### 1. Get Dependencies
```bash
cd mobile
flutter pub get
```

### 2. Firebase Setup (One-time)

**Android:**
1. Get `google-services.json` from Firebase Console
2. Place in `android/app/google-services.json`

**iOS:**
1. Get `GoogleService-Info.plist` from Firebase Console  
2. Add to `ios/Runner/` in Xcode
3. Enable Push Notifications capability

### 3. Initialize in main.dart

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'features/notifications/data/notification_service.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  await firebaseMessagingBackgroundHandler(message);
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(ProviderScope(child: MyApp()));
}

class MyApp extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.read(fcmIntegrationProvider); // Initialize FCM
    return MaterialApp(/* ... */);
  }
}
```

### 4. Test

Run app and check logs for FCM token:
```
NotificationService: FCM Token: xxx
```

---

## 📱 Notification Types

| Type | Vietnamese | Icon | Color |
|------|-----------|------|-------|
| Streak Reminder | Nhắc nhở chuỗi học | 🔥 | Orange |
| Daily Goal | Mục tiêu hàng ngày | 🚩 | Blue |
| Achievement | Thành tựu | 🏆 | Gold |
| Badge | Huy hiệu | 🎖️ | Amber |
| Level Up | Lên cấp | ⬆️ | Violet |
| Leaderboard | Bảng xếp hạng | 📊 | Purple |
| New Content | Nội dung mới | ✨ | Green |
| Quest | Nhiệm vụ | ✅ | Success |
| Social | Bạn bè | 👥 | Cyan |
| System | Hệ thống | 📢 | Indigo |

---

## 🎯 Usage Examples

### Access Notification Service

```dart
final service = ref.watch(notificationServiceProvider);

// Get FCM token
final token = service.fcmToken;

// Subscribe to topic
await service.subscribeToTopic('achievements');

// Unsubscribe from topic
await service.unsubscribeFromTopic('achievements');
```

### Manage Preferences

```dart
final prefs = ref.watch(notificationPreferencesProvider);

// Toggle preference
await ref
    .read(notificationPreferencesProvider.notifier)
    .toggleStreakReminders(true);

// Enable all
await ref
    .read(notificationPreferencesProvider.notifier)
    .enableAll();
```

### Handle Notifications

```dart
// Listen for messages
final service = NotificationService();
service.messageStream.listen((message) {
  print('Notification: ${message.notification?.title}');
  print('Data: ${message.data}');
});
```

---

## 🔔 Send Notification (Backend)

### Python (Firebase Admin SDK)

```python
from firebase_admin import messaging

# Send to specific device
message = messaging.Message(
    notification=messaging.Notification(
        title='Huy hiệu mới!',
        body='Bạn đã mở khóa huy hiệu "Người khám phá"',
    ),
    data={
        'type': 'achievement_unlocked',
        'action': 'open_achievement',
        'target_id': 'first-discovery',
    },
    token='USER_FCM_TOKEN',
)
messaging.send(message)

# Send to topic
message = messaging.Message(
    notification=messaging.Notification(
        title='Đừng quên học hôm nay!',
        body='Duy trì chuỗi học tập của bạn 🔥',
    ),
    data={'type': 'streak_reminder'},
    topic='streak_reminders',
)
messaging.send(message)
```

### REST API

```bash
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: key=YOUR_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "DEVICE_TOKEN",
    "notification": {
      "title": "Test",
      "body": "This is a test"
    },
    "data": {
      "type": "system_announcement"
    }
  }'
```

---

## 🐛 Common Issues

### No Token Generated

**Solution:**
- Wait a few seconds after app start
- Check Firebase is initialized
- For iOS: Ensure APNs token is generated first
- Check internet connection

### Notifications Not Received (iOS)

**Solution:**
- Enable Push Notifications in Xcode
- Configure APNs in Firebase Console
- Verify `GoogleService-Info.plist` is added
- Check notification permissions

### Notifications Not Received (Android)

**Solution:**
- Verify `google-services.json` is in `android/app/`
- Check minSdkVersion >= 21
- Apply Google Services plugin in gradle
- Check notification permissions

### Background Handler Not Working

**Solution:**
- Ensure handler is top-level function
- Add `@pragma('vm:entry-point')` annotation
- Register with `FirebaseMessaging.onBackgroundMessage()`

---

## 📋 Checklist

### Mobile Setup
- [ ] Add Firebase dependencies to pubspec.yaml
- [ ] Add `google-services.json` (Android)
- [ ] Add `GoogleService-Info.plist` (iOS)
- [ ] Update gradle files (Android)
- [ ] Update AppDelegate.swift (iOS)
- [ ] Enable Push Notifications capability (iOS)
- [ ] Initialize Firebase in main.dart
- [ ] Initialize FCM integration provider
- [ ] Test token generation

### Backend Setup
- [ ] Install firebase-admin package
- [ ] Add Firebase service account key
- [ ] Create FCMToken database model
- [ ] Create NotificationPreferences model
- [ ] Implement register-token endpoint
- [ ] Implement unregister-token endpoint
- [ ] Implement preferences endpoints
- [ ] Implement notification history endpoint
- [ ] Test sending notifications

### Testing
- [ ] Test foreground notifications
- [ ] Test background notifications
- [ ] Test terminated state
- [ ] Test notification tap handling
- [ ] Test preferences persistence
- [ ] Test topic subscriptions
- [ ] Test on real Android device
- [ ] Test on real iOS device

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `notification_service.dart` | FCM integration & token management |
| `notification_repository.dart` | Backend API calls |
| `notification_type_enum.dart` | Notification type definitions |
| `fcm_integration_provider.dart` | Coordinates service & repository |
| `notification_preferences_provider.dart` | Manages user preferences |
| `notification_preferences_widget.dart` | Settings UI |
| `notifications_screen.dart` | Main notifications screen |

---

## 🔗 Resources

- [Firebase Console](https://console.firebase.google.com)
- [FCM Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Flutter Firebase Messaging](https://pub.dev/packages/firebase_messaging)
- [Local Notifications](https://pub.dev/packages/flutter_local_notifications)

---

## 💡 Tips

1. **Test on Real Devices**: Notifications don't work reliably on simulators/emulators
2. **Check Logs**: Enable debug logging to see token generation and message receipt
3. **Use Topics**: For broadcast notifications to multiple users
4. **Respect Preferences**: Always check user preferences before sending
5. **Test All States**: Foreground, background, and terminated
6. **Handle Actions**: Use `data` payload to navigate to relevant screens
7. **Keep It Short**: Notification title/body should be concise
8. **Be Meaningful**: Every notification should provide value to the user

