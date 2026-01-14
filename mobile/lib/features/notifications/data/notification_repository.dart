import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';

/// Repository for managing FCM tokens with backend
class NotificationRepository {
  final Dio _dio;

  NotificationRepository(this._dio);

  /// Register FCM token with backend
  Future<bool> registerToken(String token, String userId) async {
    try {
      final response = await _dio.post(
        '/api/notifications/register-token',
        data: {
          'fcm_token': token,
          'user_id': userId,
          'platform': defaultTargetPlatform.name,
          'timestamp': DateTime.now().toIso8601String(),
        },
      );

      debugPrint('NotificationRepository: Token registered successfully');
      return response.statusCode == 200 || response.statusCode == 201;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error registering token: ${e.message}');
      // Don't throw - fail silently for notifications
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Unregister FCM token from backend
  Future<bool> unregisterToken(String token) async {
    try {
      final response = await _dio.post(
        '/api/notifications/unregister-token',
        data: {
          'fcm_token': token,
        },
      );

      debugPrint('NotificationRepository: Token unregistered successfully');
      return response.statusCode == 200;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error unregistering token: ${e.message}');
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Update notification preferences
  Future<bool> updatePreferences(Map<String, bool> preferences) async {
    try {
      final response = await _dio.put(
        '/api/notifications/preferences',
        data: {'preferences': preferences},
      );

      debugPrint('NotificationRepository: Preferences updated successfully');
      return response.statusCode == 200;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error updating preferences: ${e.message}');
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Get notification preferences
  Future<Map<String, bool>?> getPreferences() async {
    try {
      final response = await _dio.get('/api/notifications/preferences');

      if (response.statusCode == 200 && response.data != null) {
        return Map<String, bool>.from(response.data['preferences'] as Map);
      }
      return null;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error getting preferences: ${e.message}');
      return null;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return null;
    }
  }

  /// Mark notification as read
  Future<bool> markAsRead(String notificationId) async {
    try {
      final response = await _dio.post(
        '/api/notifications/$notificationId/read',
      );

      return response.statusCode == 200;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error marking as read: ${e.message}');
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Get notification history
  Future<List<Map<String, dynamic>>> getNotificationHistory({
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await _dio.get(
        '/api/notifications/history',
        queryParameters: {
          'page': page,
          'limit': limit,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final items = response.data['items'] as List<dynamic>;
        return items.map((item) => item as Map<String, dynamic>).toList();
      }
      return [];
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error getting history: ${e.message}');
      return [];
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return [];
    }
  }
}

/// Provider for notification repository
final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return NotificationRepository(dio);
});

