import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../presentation/providers/streak_provider.dart';
import '../presentation/widgets/streak_reminder_dialog.dart';
import '../presentation/widgets/streak_milestone_animation.dart';
import '../domain/entities/streak_milestone.dart';

/// Service to handle streak-related UI events like reminders and celebrations
class StreakEventService {
  final Ref _ref;
  bool _hasShownReminderThisSession = false;
  bool _hasShownMilestoneThisSession = false;

  StreakEventService(this._ref);

  /// Check if streak is at risk and show reminder
  Future<void> checkAndShowStreakReminder(BuildContext context) async {
    // Only show once per session
    if (_hasShownReminderThisSession) return;

    try {
      // Load streak data
      await _ref.read(streakNotifierProvider.notifier).loadStreak();
      final streakState = _ref.read(streakNotifierProvider);
      final data = streakState.data;

      // Check if streak is at risk and user has a streak to lose
      if (data.isAtRisk && data.currentStreak > 0) {
        _hasShownReminderThisSession = true;

        // Wait a bit for the app to fully render
        await Future.delayed(const Duration(milliseconds: 500));

        if (context.mounted) {
          await StreakReminderDialog.show(
            context,
            onStartLearning: () {
              // Navigate to explore/learning screen
              // This will be handled by the caller
            },
          );
        }
      }
    } catch (e) {
      debugPrint('Error checking streak reminder: $e');
    }
  }

  /// Check and show milestone celebration if reached
  Future<void> checkAndShowMilestoneCelebration(
    BuildContext context,
    int previousStreak,
    int currentStreak,
  ) async {
    if (_hasShownMilestoneThisSession) return;

    // Check if user crossed a milestone boundary
    final previousMilestone = StreakMilestone.forStreak(previousStreak);
    final currentMilestone = StreakMilestone.forStreak(currentStreak);

    // Only celebrate if they reached a new milestone
    if (currentMilestone != null &&
        (previousMilestone == null ||
            currentMilestone.days > previousMilestone.days)) {
      _hasShownMilestoneThisSession = true;

      if (context.mounted) {
        await StreakMilestoneAnimation.show(
          context,
          milestone: currentMilestone,
          currentStreak: currentStreak,
        );
      }
    }
  }

  /// Reset session flags (call when user logs out or app restarts)
  void resetSession() {
    _hasShownReminderThisSession = false;
    _hasShownMilestoneThisSession = false;
  }
}

/// Provider for streak event service
final streakEventServiceProvider = Provider<StreakEventService>((ref) {
  return StreakEventService(ref);
});

/// Provider to trigger streak check on app start
/// Watch this provider in your main navigation wrapper to trigger streak check
final streakStartupCheckProvider = FutureProvider.family<void, BuildContext>(
  (ref, context) async {
    final service = ref.read(streakEventServiceProvider);
    await service.checkAndShowStreakReminder(context);
  },
);

