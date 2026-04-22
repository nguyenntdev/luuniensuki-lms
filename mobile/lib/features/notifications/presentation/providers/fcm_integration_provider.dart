import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/notification_repository.dart';
import '../../data/notification_service.dart';
import 'notifications_provider.dart';

/// Provider to manage FCM integration
class FCMIntegrationNotifier extends StateNotifier<AsyncValue<void>> {
  final NotificationService _notificationService;
  final NotificationRepository _repository;
  final Ref _ref;

  FCMIntegrationNotifier(
    this._notificationService,
    this._repository,
    this._ref,
  ) : super(const AsyncValue.data(null)) {
    _initialize();
  }

  Future<void> _initialize() async {
    state = const AsyncValue.loading();
    try {
      // Initialize notification service
      await _notificationService.initialize();

      // Listen for new tokens
      _notificationService.tokenStream.listen((token) {
        if (token != null) {
          _registerToken(token);
        }
      });

      // Listen for incoming messages
      _notificationService.messageStream.listen((message) {
        _handleMessage(message);
      });

      state = const AsyncValue.data(null);
    } catch (e, stackTrace) {
      state = AsyncValue.error(e, stackTrace);
      debugPrint('FCMIntegrationNotifier: Initialization error: $e');
    }
  }

  /// Register FCM token with backend
  Future<void> _registerToken(String token) async {
    final authState = _ref.read(authProvider);
    
    authState.whenData((user) async {
      if (user != null) {
        debugPrint('FCMIntegrationNotifier: Registering token for user ${user.id}');
        final success = await _repository.registerToken(token, user.id);
        if (success) {
          debugPrint('FCMIntegrationNotifier: Token registered successfully');
        } else {
          debugPrint('FCMIntegrationNotifier: Failed to register token');
        }
      }
    });
  }

  /// Handle incoming push notification
  void _handleMessage(RemoteMessage message) {
    debugPrint('FCMIntegrationNotifier: Handling message');
    debugPrint('Title: ${message.notification?.title}');
    debugPrint('Body: ${message.notification?.body}');
    debugPrint('Data: ${message.data}');

    // Refresh notifications list
    _ref.read(notificationsNotifierProvider.notifier).refresh();

    // You can add navigation logic here based on message data
    final action = message.data['action'] as String?;
    final targetId = message.data['target_id'] as String?;

    if (action != null) {
      _handleNotificationAction(action, targetId);
    }
  }

  /// Handle notification action
  void _handleNotificationAction(String action, String? targetId) {
    debugPrint('FCMIntegrationNotifier: Action: $action, Target: $targetId');
    
    // TODO: Add navigation based on action type
    // Example actions:
    // - 'open_achievement' -> Navigate to achievements screen
    // - 'open_lesson' -> Navigate to specific lesson
    // - 'open_leaderboard' -> Navigate to leaderboard
    // - 'open_profile' -> Navigate to profile
  }

  /// Subscribe to notification topics based on user preferences
  Future<void> updateTopicSubscriptions({
    required bool streakReminders,
    required bool dailyGoalReminders,
    required bool achievementNotifications,
    required bool leaderboardUpdates,
    required bool newContentNotifications,
  }) async {
    // Subscribe/unsubscribe from topics
    if (streakReminders) {
      await _notificationService.subscribeToTopic('streak_reminders');
    } else {
      await _notificationService.unsubscribeFromTopic('streak_reminders');
    }

    if (dailyGoalReminders) {
      await _notificationService.subscribeToTopic('daily_goal_reminders');
    } else {
      await _notificationService.unsubscribeFromTopic('daily_goal_reminders');
    }

    if (achievementNotifications) {
      await _notificationService.subscribeToTopic('achievements');
    } else {
      await _notificationService.unsubscribeFromTopic('achievements');
    }

    if (leaderboardUpdates) {
      await _notificationService.subscribeToTopic('leaderboard');
    } else {
      await _notificationService.unsubscribeFromTopic('leaderboard');
    }

    if (newContentNotifications) {
      await _notificationService.subscribeToTopic('new_content');
    } else {
      await _notificationService.unsubscribeFromTopic('new_content');
    }
  }

  /// Unregister token on logout
  Future<void> unregisterToken() async {
    final token = _notificationService.fcmToken;
    if (token != null) {
      await _repository.unregisterToken(token);
      await _notificationService.deleteToken();
    }
  }
}

/// Provider for FCM integration
final fcmIntegrationProvider =
    StateNotifierProvider<FCMIntegrationNotifier, AsyncValue<void>>((ref) {
  final service = ref.watch(notificationServiceProvider);
  final repository = ref.watch(notificationRepositoryProvider);
  return FCMIntegrationNotifier(service, repository, ref);
});

