import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';

/// Repository for managing push notification consent and tokens with backend
class NotificationRepository {
  final Dio _dio;

  NotificationRepository(this._dio);

  /// Register FCM device token with backend with explicit opt-in consent
  Future<bool> registerToken(
    String token,
    String userId, {
    String? platform,
  }) async {
    try {
      final plat = (platform ?? defaultTargetPlatform.name).toLowerCase();
      final normalizedPlatform = (plat.contains('ios') || plat.contains('darwin'))
          ? 'ios'
          : (plat.contains('android') ? 'android' : 'web');

      final response = await _dio.post(
        '/api/v1/notifications/register-push',
        data: {
          'token': token,
          'platform': normalizedPlatform,
        },
      );

      debugPrint('NotificationRepository: Token registered successfully');
      return response.statusCode == 200 || response.statusCode == 201;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error registering token: ${e.message}');
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Unregister FCM token from backend upon opt-out or logout
  Future<bool> unregisterToken([String? token]) async {
    try {
      final response = await _dio.delete(
        '/api/v1/notifications/unregister-push',
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

  /// Explicitly grant or revoke push notification consent
  Future<bool> updateConsent({
    required bool granted,
    String? token,
    String? platform,
  }) async {
    try {
      final plat = (platform ?? defaultTargetPlatform.name).toLowerCase();
      final normalizedPlatform = (plat.contains('ios') || plat.contains('darwin'))
          ? 'ios'
          : (plat.contains('android') ? 'android' : 'web');

      final response = await _dio.post(
        '/api/v1/notifications/consent',
        data: {
          'granted': granted,
          if (token != null) 'token': token,
          'platform': normalizedPlatform,
          'consent_version': 'v1.0',
        },
      );

      debugPrint('NotificationRepository: Push consent updated: granted=$granted');
      return response.statusCode == 200;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error updating consent: ${e.message}');
      return false;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return false;
    }
  }

  /// Get current push notification consent status from server
  Future<Map<String, dynamic>?> getConsentStatus() async {
    try {
      final response = await _dio.get('/api/v1/notifications/consent');
      if (response.statusCode == 200 && response.data != null) {
        return Map<String, dynamic>.from(response.data as Map);
      }
      return null;
    } on DioException catch (e) {
      debugPrint('NotificationRepository: Error getting consent status: ${e.message}');
      return null;
    } catch (e) {
      debugPrint('NotificationRepository: Unexpected error: $e');
      return null;
    }
  }

  /// Update notification preferences
  Future<bool> updatePreferences(Map<String, dynamic> preferences) async {
    try {
      final response = await _dio.put(
        '/api/v1/notifications/settings',
        data: preferences,
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
  Future<Map<String, dynamic>?> getPreferences() async {
    try {
      final response = await _dio.get('/api/v1/notifications/settings');

      if (response.statusCode == 200 && response.data != null) {
        return Map<String, dynamic>.from(response.data as Map);
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
        '/api/v1/notifications/$notificationId/read',
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
        '/api/v1/notifications/history',
        queryParameters: {
          'limit': limit,
          'offset': (page - 1) * limit,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final notifications = response.data['notifications'] as List<dynamic>?;
        if (notifications != null) {
          return notifications.map((item) => item as Map<String, dynamic>).toList();
        }
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

