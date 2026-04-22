import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../widgets/daily_goal_celebration.dart';

/// Service for showing daily goal celebration
class DailyGoalCelebrationService {
  DailyGoalCelebrationService._();
  
  static final instance = DailyGoalCelebrationService._();

  OverlayEntry? _currentOverlay;

  /// Show celebration when goal is completed
  void showCelebration(BuildContext context) {
    // Dismiss any existing celebration
    dismiss();

    _currentOverlay = OverlayEntry(
      builder: (context) => DailyGoalCelebration(
        onDismiss: dismiss,
      ),
    );

    Overlay.of(context).insert(_currentOverlay!);
  }

  /// Dismiss current celebration
  void dismiss() {
    _currentOverlay?.remove();
    _currentOverlay?.dispose();
    _currentOverlay = null;
  }
}

/// Provider for daily goal celebration service
final dailyGoalCelebrationServiceProvider = Provider<DailyGoalCelebrationService>((ref) {
  return DailyGoalCelebrationService.instance;
});

/// Extension to easily show celebrations
extension DailyGoalCelebrationContext on BuildContext {
  void showDailyGoalCelebration() {
    DailyGoalCelebrationService.instance.showCelebration(this);
  }
}

