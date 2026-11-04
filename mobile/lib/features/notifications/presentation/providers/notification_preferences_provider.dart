import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/storage/hive_storage.dart';
import '../../data/notification_repository.dart';

/// Notification preferences model with explicit push consent state
class NotificationPreferences {
  final bool pushConsentGranted;
  final bool pushEnabled;
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
  final bool teacherAlerts;
  final bool partnerAlerts;

  const NotificationPreferences({
    this.pushConsentGranted = false,
    this.pushEnabled = false,
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
    this.teacherAlerts = true,
    this.partnerAlerts = true,
  });

  NotificationPreferences copyWith({
    bool? pushConsentGranted,
    bool? pushEnabled,
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
    bool? teacherAlerts,
    bool? partnerAlerts,
  }) {
    return NotificationPreferences(
      pushConsentGranted: pushConsentGranted ?? this.pushConsentGranted,
      pushEnabled: pushEnabled ?? this.pushEnabled,
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
      teacherAlerts: teacherAlerts ?? this.teacherAlerts,
      partnerAlerts: partnerAlerts ?? this.partnerAlerts,
    );
  }
}

/// Provider for notification preferences
class NotificationPreferencesNotifier
    extends StateNotifier<NotificationPreferences> {
  final HiveStorage _storage;
  final NotificationRepository? _repository;
  static const String _prefsKey = 'notification_preferences';

  NotificationPreferencesNotifier(this._storage, [this._repository])
      : super(const NotificationPreferences()) {
    _loadPreferences();
  }

  /// Load preferences from storage
  Future<void> _loadPreferences() async {
    final prefs = _storage.getSetting<Map<dynamic, dynamic>>(_prefsKey);
    if (prefs != null) {
      state = NotificationPreferences(
        pushConsentGranted: prefs['pushConsentGranted'] as bool? ?? false,
        pushEnabled: prefs['pushEnabled'] as bool? ?? false,
        streakReminders: prefs['streakReminders'] as bool? ?? true,
        dailyGoalReminders: prefs['dailyGoalReminders'] as bool? ?? true,
        achievementNotifications:
            prefs['achievementNotifications'] as bool? ?? true,
        leaderboardUpdates: prefs['leaderboardUpdates'] as bool? ?? true,
        newContentNotifications:
            prefs['newContentNotifications'] as bool? ?? true,
        questNotifications: prefs['questNotifications'] as bool? ?? true,
        badgeNotifications: prefs['badgeNotifications'] as bool? ?? true,
        levelUpNotifications: prefs['levelUpNotifications'] as bool? ?? true,
        friendActivityNotifications:
            prefs['friendActivityNotifications'] as bool? ?? true,
        systemAnnouncements: prefs['systemAnnouncements'] as bool? ?? true,
        teacherAlerts: prefs['teacherAlerts'] as bool? ?? true,
        partnerAlerts: prefs['partnerAlerts'] as bool? ?? true,
      );
    }
  }

  /// Save preferences to storage
  Future<void> _savePreferences() async {
    await _storage.setSetting(_prefsKey, {
      'pushConsentGranted': state.pushConsentGranted,
      'pushEnabled': state.pushEnabled,
      'streakReminders': state.streakReminders,
      'dailyGoalReminders': state.dailyGoalReminders,
      'achievementNotifications': state.achievementNotifications,
      'leaderboardUpdates': state.leaderboardUpdates,
      'newContentNotifications': state.newContentNotifications,
      'questNotifications': state.questNotifications,
      'badgeNotifications': state.badgeNotifications,
      'levelUpNotifications': state.levelUpNotifications,
      'friendActivityNotifications': state.friendActivityNotifications,
      'systemAnnouncements': state.systemAnnouncements,
      'teacherAlerts': state.teacherAlerts,
      'partnerAlerts': state.partnerAlerts,
    });
  }

  /// Explicit Opt-In / Opt-Out Push Consent Toggle
  Future<void> togglePushConsent(
    bool granted, {
    String? token,
    String? platform,
  }) async {
    state = state.copyWith(
      pushConsentGranted: granted,
      pushEnabled: granted,
    );
    await _savePreferences();

    // Notify backend of consent state change
    if (_repository != null) {
      await _repository.updateConsent(
        granted: granted,
        token: token,
        platform: platform,
      );
      if (!granted) {
        // Opt-out promptly unregisters device token on backend
        await _repository.unregisterToken(token);
      }
    }
  }

  /// Toggle streak reminders
  Future<void> toggleStreakReminders(bool value) async {
    state = state.copyWith(streakReminders: value);
    await _savePreferences();
    if (_repository != null) {
      await _repository.updatePreferences({'streak_reminders': value});
    }
  }

  /// Toggle daily goal reminders
  Future<void> toggleDailyGoalReminders(bool value) async {
    state = state.copyWith(dailyGoalReminders: value);
    await _savePreferences();
    if (_repository != null) {
      await _repository.updatePreferences({'daily_mission_reminders': value});
    }
  }

  /// Toggle achievement notifications
  Future<void> toggleAchievementNotifications(bool value) async {
    state = state.copyWith(achievementNotifications: value);
    await _savePreferences();
  }

  /// Toggle leaderboard updates
  Future<void> toggleLeaderboardUpdates(bool value) async {
    state = state.copyWith(leaderboardUpdates: value);
    await _savePreferences();
  }

  /// Toggle new content notifications
  Future<void> toggleNewContentNotifications(bool value) async {
    state = state.copyWith(newContentNotifications: value);
    await _savePreferences();
  }

  /// Toggle quest notifications
  Future<void> toggleQuestNotifications(bool value) async {
    state = state.copyWith(questNotifications: value);
    await _savePreferences();
  }

  /// Toggle badge notifications
  Future<void> toggleBadgeNotifications(bool value) async {
    state = state.copyWith(badgeNotifications: value);
    await _savePreferences();
  }

  /// Toggle level up notifications
  Future<void> toggleLevelUpNotifications(bool value) async {
    state = state.copyWith(levelUpNotifications: value);
    await _savePreferences();
  }

  /// Toggle friend activity notifications
  Future<void> toggleFriendActivityNotifications(bool value) async {
    state = state.copyWith(friendActivityNotifications: value);
    await _savePreferences();
  }

  /// Toggle system announcements
  Future<void> toggleSystemAnnouncements(bool value) async {
    state = state.copyWith(systemAnnouncements: value);
    await _savePreferences();
  }

  /// Toggle teacher alerts
  Future<void> toggleTeacherAlerts(bool value) async {
    state = state.copyWith(teacherAlerts: value);
    await _savePreferences();
  }

  /// Toggle partner alerts
  Future<void> togglePartnerAlerts(bool value) async {
    state = state.copyWith(partnerAlerts: value);
    await _savePreferences();
  }

  /// Enable all notifications
  Future<void> enableAll() async {
    state = const NotificationPreferences(
      pushConsentGranted: true,
      pushEnabled: true,
      streakReminders: true,
      dailyGoalReminders: true,
      achievementNotifications: true,
      leaderboardUpdates: true,
      newContentNotifications: true,
      questNotifications: true,
      badgeNotifications: true,
      levelUpNotifications: true,
      friendActivityNotifications: true,
      systemAnnouncements: true,
      teacherAlerts: true,
      partnerAlerts: true,
    );
    await _savePreferences();
  }

  /// Disable all notifications (opt-out)
  Future<void> disableAll() async {
    state = const NotificationPreferences(
      pushConsentGranted: false,
      pushEnabled: false,
      streakReminders: false,
      dailyGoalReminders: false,
      achievementNotifications: false,
      leaderboardUpdates: false,
      newContentNotifications: false,
      questNotifications: false,
      badgeNotifications: false,
      levelUpNotifications: false,
      friendActivityNotifications: false,
      systemAnnouncements: false,
      teacherAlerts: false,
      partnerAlerts: false,
    );
    await _savePreferences();
    if (_repository != null) {
      await _repository.updateConsent(granted: false);
      await _repository.unregisterToken();
    }
  }
}

/// Provider for notification preferences
final notificationPreferencesProvider = StateNotifierProvider<
    NotificationPreferencesNotifier, NotificationPreferences>((ref) {
  final storage = ref.watch(hiveStorageProvider);
  final repository = ref.watch(notificationRepositoryProvider);
  return NotificationPreferencesNotifier(storage, repository);
});

