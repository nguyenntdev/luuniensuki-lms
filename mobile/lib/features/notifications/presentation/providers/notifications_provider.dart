import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/notification_item.dart';

part 'notifications_provider.freezed.dart';

/// Notifications state
@freezed
class NotificationsState with _$NotificationsState {
  const factory NotificationsState({
    @Default([]) List<NotificationItem> notifications,
    @Default(false) bool isLoading,
    @Default(false) bool isRefreshing,
    String? error,
  }) = _NotificationsState;
}

extension NotificationsStateX on NotificationsState {
  /// Get unread count
  int get unreadCount => notifications.where((n) => !n.isRead).length;

  /// Check if has unread notifications
  bool get hasUnread => unreadCount > 0;
}

/// Notifications notifier
class NotificationsNotifier extends StateNotifier<NotificationsState> {
  NotificationsNotifier() : super(const NotificationsState()) {
    _loadNotifications();
  }

  /// Load notifications (mock data for now)
  Future<void> _loadNotifications() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      // Simulate API delay
      await Future.delayed(const Duration(milliseconds: 500));

      // Load mock data
      state = state.copyWith(
        notifications: MockNotifications.items,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Không thể tải thông báo',
      );
    }
  }

  /// Refresh notifications
  Future<void> refresh() async {
    state = state.copyWith(isRefreshing: true, error: null);

    try {
      // Simulate API delay
      await Future.delayed(const Duration(milliseconds: 800));

      // Reload mock data
      state = state.copyWith(
        notifications: MockNotifications.items,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isRefreshing: false,
        error: 'Không thể làm mới thông báo',
      );
    }
  }

  /// Mark notification as read
  void markAsRead(String notificationId) {
    final updatedNotifications = state.notifications.map((n) {
      if (n.id == notificationId) {
        return n.copyWith(isRead: true);
      }
      return n;
    }).toList();

    state = state.copyWith(notifications: updatedNotifications);
  }

  /// Mark all notifications as read
  void markAllAsRead() {
    final updatedNotifications = state.notifications.map((n) {
      return n.copyWith(isRead: true);
    }).toList();

    state = state.copyWith(notifications: updatedNotifications);
  }

  /// Delete notification
  void deleteNotification(String notificationId) {
    final updatedNotifications = state.notifications
        .where((n) => n.id != notificationId)
        .toList();

    state = state.copyWith(notifications: updatedNotifications);
  }

  /// Clear all notifications
  void clearAll() {
    state = state.copyWith(notifications: []);
  }
}

/// Provider for notifications
final notificationsNotifierProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>((ref) {
  return NotificationsNotifier();
});

