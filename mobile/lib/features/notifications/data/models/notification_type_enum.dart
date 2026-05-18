import 'package:flutter/material.dart';

/// Types of push notifications
enum PushNotificationType {
  streakReminder('streak_reminder'),
  dailyGoalReminder('daily_goal_reminder'),
  achievementUnlocked('achievement_unlocked'),
  leaderboardUpdate('leaderboard_update'),
  newContentAvailable('new_content_available'),
  questCompleted('quest_completed'),
  badgeEarned('badge_earned'),
  levelUp('level_up'),
  friendActivity('friend_activity'),
  systemAnnouncement('system_announcement');

  const PushNotificationType(this.value);
  final String value;

  static PushNotificationType fromString(String value) {
    return PushNotificationType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => PushNotificationType.systemAnnouncement,
    );
  }

  /// Get icon for notification type
  IconData get icon {
    switch (this) {
      case PushNotificationType.streakReminder:
        return Icons.local_fire_department;
      case PushNotificationType.dailyGoalReminder:
        return Icons.flag;
      case PushNotificationType.achievementUnlocked:
        return Icons.emoji_events;
      case PushNotificationType.leaderboardUpdate:
        return Icons.leaderboard;
      case PushNotificationType.newContentAvailable:
        return Icons.auto_awesome;
      case PushNotificationType.questCompleted:
        return Icons.check_circle;
      case PushNotificationType.badgeEarned:
        return Icons.military_tech;
      case PushNotificationType.levelUp:
        return Icons.arrow_upward;
      case PushNotificationType.friendActivity:
        return Icons.people;
      case PushNotificationType.systemAnnouncement:
        return Icons.campaign;
    }
  }

  /// Get color for notification type
  Color get color {
    switch (this) {
      case PushNotificationType.streakReminder:
        return const Color(0xFFFF6B35); // Orange/Red for fire
      case PushNotificationType.dailyGoalReminder:
        return const Color(0xFF60A5FA); // Blue
      case PushNotificationType.achievementUnlocked:
        return const Color(0xFFE8B44C); // Gold
      case PushNotificationType.leaderboardUpdate:
        return const Color(0xFF9C27B0); // Purple
      case PushNotificationType.newContentAvailable:
        return const Color(0xFF34D399); // Green
      case PushNotificationType.questCompleted:
        return const Color(0xFF10B981); // Success green
      case PushNotificationType.badgeEarned:
        return const Color(0xFFF59E0B); // Amber
      case PushNotificationType.levelUp:
        return const Color(0xFF8B5CF6); // Violet
      case PushNotificationType.friendActivity:
        return const Color(0xFF06B6D4); // Cyan
      case PushNotificationType.systemAnnouncement:
        return const Color(0xFF6366F1); // Indigo
    }
  }

  /// Get priority (1-5, 5 being highest)
  int get priority {
    switch (this) {
      case PushNotificationType.streakReminder:
        return 4;
      case PushNotificationType.dailyGoalReminder:
        return 3;
      case PushNotificationType.achievementUnlocked:
        return 5;
      case PushNotificationType.leaderboardUpdate:
        return 2;
      case PushNotificationType.newContentAvailable:
        return 3;
      case PushNotificationType.questCompleted:
        return 4;
      case PushNotificationType.badgeEarned:
        return 5;
      case PushNotificationType.levelUp:
        return 5;
      case PushNotificationType.friendActivity:
        return 2;
      case PushNotificationType.systemAnnouncement:
        return 3;
    }
  }
}

/// Notification preferences model
class NotificationPreferences {
  final bool streakReminders;
  final bool dailyGoalReminders;
  final bool achievementNotifications;
  final bool leaderboardUpdates;
  final bool newContentNotifications;
  final bool questNotifications;
  final bool badgeNotifications;
  final bool levelUpNotifications;
  final bool friendActivityNotifications;
  final bool systemAnnouncements;

  const NotificationPreferences({
    this.streakReminders = true,
    this.dailyGoalReminders = true,
    this.achievementNotifications = true,
    this.leaderboardUpdates = true,
    this.newContentNotifications = true,
    this.questNotifications = true,
    this.badgeNotifications = true,
    this.levelUpNotifications = true,
    this.friendActivityNotifications = true,
    this.systemAnnouncements = true,
  });

  NotificationPreferences copyWith({
    bool? streakReminders,
    bool? dailyGoalReminders,
    bool? achievementNotifications,
    bool? leaderboardUpdates,
    bool? newContentNotifications,
    bool? questNotifications,
    bool? badgeNotifications,
    bool? levelUpNotifications,
    bool? friendActivityNotifications,
    bool? systemAnnouncements,
  }) {
    return NotificationPreferences(
      streakReminders: streakReminders ?? this.streakReminders,
      dailyGoalReminders: dailyGoalReminders ?? this.dailyGoalReminders,
      achievementNotifications: achievementNotifications ?? this.achievementNotifications,
      leaderboardUpdates: leaderboardUpdates ?? this.leaderboardUpdates,
      newContentNotifications: newContentNotifications ?? this.newContentNotifications,
      questNotifications: questNotifications ?? this.questNotifications,
      badgeNotifications: badgeNotifications ?? this.badgeNotifications,
      levelUpNotifications: levelUpNotifications ?? this.levelUpNotifications,
      friendActivityNotifications: friendActivityNotifications ?? this.friendActivityNotifications,
      systemAnnouncements: systemAnnouncements ?? this.systemAnnouncements,
    );
  }
}

