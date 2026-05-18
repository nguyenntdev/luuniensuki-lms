import 'package:flutter/material.dart';
import '../../../../routing/route_names.dart';

/// Types of notifications
enum NotificationType {
  achievement,
  streak,
  lesson,
  social,
  system,
}

/// A notification item entity
class NotificationItem {
  final String id;
  final NotificationType type;
  final String title;
  final String message;
  final DateTime timestamp;
  final bool isRead;
  final String? actionUrl;
  final Map<String, dynamic>? metadata;

  const NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.timestamp,
    this.isRead = false,
    this.actionUrl,
    this.metadata,
  });

  /// Get icon for notification type
  IconData get icon {
    switch (type) {
      case NotificationType.achievement:
        return Icons.emoji_events;
      case NotificationType.streak:
        return Icons.local_fire_department;
      case NotificationType.lesson:
        return Icons.school;
      case NotificationType.social:
        return Icons.people;
      case NotificationType.system:
        return Icons.info_outline;
    }
  }

  /// Get color for notification type
  Color get color {
    switch (type) {
      case NotificationType.achievement:
        return const Color(0xFF9C27B0); // Purple
      case NotificationType.streak:
        return const Color(0xFFFF6B35); // Orange
      case NotificationType.lesson:
        return const Color(0xFF60A5FA); // Blue
      case NotificationType.social:
        return const Color(0xFF34D399); // Green
      case NotificationType.system:
        return const Color(0xFFE8B44C); // Gold
    }
  }

  /// Copy with method for updating notification
  NotificationItem copyWith({
    String? id,
    NotificationType? type,
    String? title,
    String? message,
    DateTime? timestamp,
    bool? isRead,
    String? actionUrl,
    Map<String, dynamic>? metadata,
  }) {
    return NotificationItem(
      id: id ?? this.id,
      type: type ?? this.type,
      title: title ?? this.title,
      message: message ?? this.message,
      timestamp: timestamp ?? this.timestamp,
      isRead: isRead ?? this.isRead,
      actionUrl: actionUrl ?? this.actionUrl,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Format time ago
  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays > 7) {
      return '${timestamp.day}/${timestamp.month}/${timestamp.year}';
    } else if (difference.inDays > 0) {
      return '${difference.inDays} ngày trước';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} giờ trước';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} phút trước';
    } else {
      return 'Vừa xong';
    }
  }
}

/// Mock notification data for testing
class MockNotifications {
  static final List<NotificationItem> items = [
    NotificationItem(
      id: '1',
      type: NotificationType.achievement,
      title: 'Huy hiệu mới!',
      message: 'Bạn đã mở khóa huy hiệu "Người khám phá"',
      timestamp: DateTime.now().subtract(const Duration(minutes: 30)),
      isRead: false,
      actionUrl: RoutePaths.achievements,
    ),
    NotificationItem(
      id: '2',
      type: NotificationType.streak,
      title: 'Chuỗi học tập 7 ngày!',
      message: 'Tuyệt vời! Bạn đã duy trì chuỗi học tập 7 ngày liên tiếp.',
      timestamp: DateTime.now().subtract(const Duration(hours: 2)),
      isRead: false,
    ),
    NotificationItem(
      id: '3',
      type: NotificationType.lesson,
      title: 'Bài học mới',
      message: 'Bài học về "Hoa văn rồng" đã sẵn sàng để học.',
      timestamp: DateTime.now().subtract(const Duration(hours: 5)),
      isRead: true,
      actionUrl: RoutePaths.motif('dragon-pattern'),
    ),
    NotificationItem(
      id: '4',
      type: NotificationType.system,
      title: 'Cập nhật ứng dụng',
      message: 'Phiên bản mới với nhiều tính năng thú vị đã có sẵn.',
      timestamp: DateTime.now().subtract(const Duration(days: 1)),
      isRead: true,
    ),
    NotificationItem(
      id: '5',
      type: NotificationType.achievement,
      title: 'Lên cấp!',
      message: 'Bạn đã đạt cấp độ "Học giả". Chúc mừng!',
      timestamp: DateTime.now().subtract(const Duration(days: 2)),
      isRead: true,
      actionUrl: RoutePaths.profile,
    ),
  ];
}
