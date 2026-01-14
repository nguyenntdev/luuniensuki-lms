# Push Notifications Implementation Guide

## Overview

This document describes the push notifications implementation for the LMS mobile app using Firebase Cloud Messaging (FCM).

## Features

✅ **FCM Integration**
- Firebase Cloud Messaging setup
- Token management
- Background & foreground message handling
- Local notifications for foreground messages

✅ **Notification Types**
- Streak reminders ("Đừng quên học hôm nay!")
- Daily goal reminders
- Achievement unlocked notifications
- Badge earned notifications
- Level up notifications
- Leaderboard updates
- New content available
- Quest completed
- Friend activity
- System announcements

✅ **User Preferences**
- Granular control over notification types
- Enable/disable individual notification categories
- Persisted preferences (Hive storage)
- Sync with backend

✅ **Notification Management**
- Mark as read/unread
- Delete individual notifications
- Clear all notifications
- Pull to refresh

## Architecture

### File Structure

```
lib/features/notifications/
├── data/
│   ├── models/
│   │   └── notification_type_enum.dart       # Notification type definitions
│   ├── notification_service.dart              # FCM service
│   └── notification_repository.dart           # Backend API integration
├── domain/
│   └── entities/
│       └── notification_item.dart             # Notification entity
└── presentation/
    ├── providers/
    │   ├── notifications_provider.dart        # Notifications state management
    │   ├── notification_preferences_provider.dart  # Preferences state
    │   └── fcm_integration_provider.dart      # FCM integration logic
    ├── screens/
    │   └── notifications_screen.dart          # Main notifications screen
    └── widgets/
        ├── notification_item_widget.dart      # Notification list item
        └── notification_preferences_widget.dart  # Preferences UI
```

## Setup Instructions

### 1. Firebase Setup

#### Android

1. Create a Firebase project at https://console.firebase.google.com
2. Add an Android app to your Firebase project
3. Download `google-services.json`
4. Place it in `android/app/google-services.json`
5. Update `android/build.gradle`:

```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

6. Update `android/app/build.gradle`:

```gradle
apply plugin: 'com.google.gms.google-services'

android {
    defaultConfig {
        minSdkVersion 21  // FCM requires min SDK 21
    }
}
```

#### iOS

1. Add an iOS app to your Firebase project
2. Download `GoogleService-Info.plist`
3. Add it to `ios/Runner/` in Xcode
4. Update `ios/Runner/Info.plist`:

```xml
<key>FirebaseAppDelegateProxyEnabled</key>
<false/>
```

5. Update `ios/Runner/AppDelegate.swift`:

```swift
import UIKit
import Flutter
import Firebase
import FirebaseMessaging

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    FirebaseApp.configure()
    
    if #available(iOS 10.0, *) {
      UNUserNotificationCenter.current().delegate = self
    }
    
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
  
  override func application(_ application: UIApplication,
                           didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    Messaging.messaging().apnsToken = deviceToken
  }
}
```

6. Enable Push Notifications capability in Xcode

### 2. Dependencies

Already added to `pubspec.yaml`:

```yaml
dependencies:
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.10
  flutter_local_notifications: ^16.3.0
```

### 3. Initialize in App

Update `lib/main.dart`:

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'features/notifications/data/notification_service.dart';

// Top-level background handler
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  await firebaseMessagingBackgroundHandler(message);
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  // Setup background handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(
    ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Initialize FCM integration
    ref.read(fcmIntegrationProvider);
    
    return MaterialApp(
      // ... rest of app
    );
  }
}
```

## Usage

### Sending Notifications from Backend

See `PUSH_NOTIFICATIONS_BACKEND_API.md` for backend implementation details.

### Handling Notifications in App

Notifications are automatically handled by the `FCMIntegrationProvider`. When a notification arrives:

1. **Foreground**: Shows as local notification
2. **Background**: Handled by Firebase
3. **Terminated**: Opens app when tapped

### User Preferences

Users can control which notifications they receive:

```dart
// Access preferences
final prefs = ref.watch(notificationPreferencesProvider);

// Toggle a preference
await ref
    .read(notificationPreferencesProvider.notifier)
    .toggleStreakReminders(true);

// Enable all
await ref
    .read(notificationPreferencesProvider.notifier)
    .enableAll();

// Disable all
await ref
    .read(notificationPreferencesProvider.notifier)
    .disableAll();
```

### Notification Actions

Users can perform actions on notifications:

- **Tap**: Navigate to related content
- **Mark as read**: Mark notification as read
- **Delete**: Remove notification
- **Clear all**: Remove all notifications

## Notification Types & Examples

### 1. Streak Reminder
```json
{
  "notification": {
    "title": "Đừng quên học hôm nay!",
    "body": "Duy trì chuỗi học tập của bạn 🔥"
  },
  "data": {
    "type": "streak_reminder",
    "action": "open_home"
  }
}
```

### 2. Achievement Unlocked
```json
{
  "notification": {
    "title": "Huy hiệu mới!",
    "body": "Bạn đã mở khóa huy hiệu 'Người khám phá'"
  },
  "data": {
    "type": "achievement_unlocked",
    "action": "open_achievement",
    "target_id": "first-discovery"
  }
}
```

### 3. Daily Goal Reminder
```json
{
  "notification": {
    "title": "Hoàn thành mục tiêu!",
    "body": "Chỉ còn 2 bài học nữa để đạt mục tiêu hôm nay"
  },
  "data": {
    "type": "daily_goal_reminder",
    "action": "open_home"
  }
}
```

### 4. Level Up
```json
{
  "notification": {
    "title": "Lên cấp! 🎉",
    "body": "Chúc mừng! Bạn đã đạt cấp độ Học giả"
  },
  "data": {
    "type": "level_up",
    "action": "open_profile",
    "level": "5"
  }
}
```

### 5. New Content Available
```json
{
  "notification": {
    "title": "Nội dung mới",
    "body": "Bài học về 'Hoa văn rồng' đã sẵn sàng"
  },
  "data": {
    "type": "new_content_available",
    "action": "open_lesson",
    "target_id": "lesson-123"
  }
}
```

## Testing

### 1. Test FCM Token Registration

```dart
// Get FCM token
final service = NotificationService();
await service.initialize();
final token = service.fcmToken;
print('FCM Token: $token');
```

### 2. Test Local Notifications

```dart
// Send a test notification
final service = NotificationService();
await service.initialize();

// This will show a local notification
await service._showLocalNotification(
  RemoteMessage(
    notification: RemoteNotification(
      title: 'Test',
      body: 'This is a test notification',
    ),
    data: {'type': 'system_announcement'},
  ),
);
```

### 3. Test from Firebase Console

1. Go to Firebase Console > Cloud Messaging
2. Click "Send your first message"
3. Enter title and body
4. Click "Send test message"
5. Enter your FCM token
6. Click "Test"

## Troubleshooting

### iOS: Not Receiving Notifications

1. Check APNs certificate in Firebase Console
2. Verify `GoogleService-Info.plist` is in the project
3. Enable Push Notifications capability in Xcode
4. Check device has internet connection
5. Verify app has notification permission

### Android: Not Receiving Notifications

1. Check `google-services.json` is in `android/app/`
2. Verify Google Services plugin is applied
3. Check minSdkVersion is at least 21
4. Verify app has notification permission
5. Check Firebase project has correct package name

### Token Not Generated

1. Wait a few seconds after initialization
2. Check internet connection
3. Verify Firebase is initialized
4. Check console for errors
5. For iOS, ensure APNs token is generated first

## Next Steps

1. ✅ Mobile implementation complete
2. ⏳ Backend API endpoints (see PUSH_NOTIFICATIONS_BACKEND_API.md)
3. ⏳ Firebase Admin SDK setup on backend
4. ⏳ Scheduled notifications (daily reminders)
5. ⏳ Analytics for notification engagement

