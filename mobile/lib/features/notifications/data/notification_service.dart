import 'dart:async';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models/notification_type_enum.dart';

/// FCM Notification Service
/// Handles Firebase Cloud Messaging integration for push notifications
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  final StreamController<RemoteMessage> _messageStreamController =
      StreamController<RemoteMessage>.broadcast();
  final StreamController<String?> _tokenStreamController =
      StreamController<String?>.broadcast();

  Stream<RemoteMessage> get messageStream => _messageStreamController.stream;
  Stream<String?> get tokenStream => _tokenStreamController.stream;

  String? _fcmToken;
  String? get fcmToken => _fcmToken;

  bool _initialized = false;

  /// Initialize Firebase Cloud Messaging
  Future<void> initialize() async {
    if (_initialized) {
      debugPrint('NotificationService: Already initialized');
      return;
    }

    try {
      // Initialize Firebase
      await Firebase.initializeApp();
      debugPrint('NotificationService: Firebase initialized');

      // Initialize local notifications
      await _initializeLocalNotifications();

      // Request permission
      final permission = await requestPermission();
      if (!permission) {
        debugPrint('NotificationService: Notifications permission denied');
        _initialized = true;
        return;
      }

      // Get FCM token
      await _getFCMToken();

      // Setup message handlers
      _setupMessageHandlers();

      // Listen for token refresh
      _firebaseMessaging.onTokenRefresh.listen((token) {
        debugPrint('NotificationService: FCM Token refreshed: $token');
        _fcmToken = token;
        _tokenStreamController.add(token);
      });

      _initialized = true;
      debugPrint('NotificationService: Initialization complete');
    } catch (e, stackTrace) {
      debugPrint('NotificationService: Initialization error: $e');
      debugPrint('Stack trace: $stackTrace');
      _initialized = true; // Mark as initialized to prevent retry loops
    }
  }

  /// Initialize local notifications plugin
  Future<void> _initializeLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    debugPrint('NotificationService: Local notifications initialized');
  }

  /// Request notification permission
  Future<bool> requestPermission() async {
    final settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    final isGranted = settings.authorizationStatus == AuthorizationStatus.authorized;
    debugPrint('NotificationService: Permission granted: $isGranted');
    return isGranted;
  }

  /// Get FCM token
  Future<String?> _getFCMToken() async {
    try {
      // For iOS, get APNs token first
      if (Platform.isIOS) {
        final apnsToken = await _firebaseMessaging.getAPNSToken();
        debugPrint('NotificationService: APNs Token: $apnsToken');
        if (apnsToken == null) {
          // Wait a bit and try again
          await Future.delayed(const Duration(seconds: 3));
        }
      }

      _fcmToken = await _firebaseMessaging.getToken();
      debugPrint('NotificationService: FCM Token: $_fcmToken');
      _tokenStreamController.add(_fcmToken);
      return _fcmToken;
    } catch (e) {
      debugPrint('NotificationService: Error getting FCM token: $e');
      return null;
    }
  }

  /// Setup message handlers for different states
  void _setupMessageHandlers() {
    // Handle foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('NotificationService: Foreground message received');
      debugPrint('Title: ${message.notification?.title}');
      debugPrint('Body: ${message.notification?.body}');
      debugPrint('Data: ${message.data}');

      _messageStreamController.add(message);
      _showLocalNotification(message);
    });

    // Handle background messages (when app is in background but not terminated)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('NotificationService: Background message opened app');
      debugPrint('Data: ${message.data}');
      _messageStreamController.add(message);
    });

    // Handle notification tap from terminated state
    _firebaseMessaging.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        debugPrint('NotificationService: Terminated state message opened app');
        debugPrint('Data: ${message.data}');
        _messageStreamController.add(message);
      }
    });
  }

  /// Show local notification for foreground messages
  Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    // Parse notification type from data
    final typeString = message.data['type'] as String?;
    final notificationType = typeString != null
        ? PushNotificationType.fromString(typeString)
        : PushNotificationType.systemAnnouncement;

    // Get color code for the notification type
    final colorValue = notificationType.color.value;

    final androidDetails = AndroidNotificationDetails(
      'default_channel',
      'Default Notifications',
      channelDescription: 'Default notification channel for the app',
      importance: Importance.high,
      priority: Priority.high,
      color: Color(colorValue),
      playSound: true,
      enableVibration: true,
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      message.hashCode,
      notification.title,
      notification.body,
      details,
      payload: message.data.toString(),
    );
  }

  /// Handle notification tap
  void _onNotificationTapped(NotificationResponse response) {
    debugPrint('NotificationService: Notification tapped');
    debugPrint('Payload: ${response.payload}');
    // The navigation will be handled by the messageStream listeners
  }

  /// Subscribe to a topic
  Future<void> subscribeToTopic(String topic) async {
    try {
      await _firebaseMessaging.subscribeToTopic(topic);
      debugPrint('NotificationService: Subscribed to topic: $topic');
    } catch (e) {
      debugPrint('NotificationService: Error subscribing to topic: $e');
    }
  }

  /// Unsubscribe from a topic
  Future<void> unsubscribeFromTopic(String topic) async {
    try {
      await _firebaseMessaging.unsubscribeFromTopic(topic);
      debugPrint('NotificationService: Unsubscribed from topic: $topic');
    } catch (e) {
      debugPrint('NotificationService: Error unsubscribing from topic: $e');
    }
  }

  /// Delete FCM token
  Future<void> deleteToken() async {
    try {
      await _firebaseMessaging.deleteToken();
      _fcmToken = null;
      _tokenStreamController.add(null);
      debugPrint('NotificationService: FCM token deleted');
    } catch (e) {
      debugPrint('NotificationService: Error deleting token: $e');
    }
  }

  void dispose() {
    _messageStreamController.close();
    _tokenStreamController.close();
  }
}

/// Background message handler (must be top-level function)
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('NotificationService: Background message handler');
  debugPrint('Title: ${message.notification?.title}');
  debugPrint('Body: ${message.notification?.body}');
  debugPrint('Data: ${message.data}');
}

/// Provider for notification service
final notificationServiceProvider = Provider<NotificationService>((ref) {
  return NotificationService();
});

