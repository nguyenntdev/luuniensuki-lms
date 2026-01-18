import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/sound_service.dart';
import '../widgets/xp_celebration_overlay.dart';

/// Celebration level based on XP amount
enum CelebrationLevel {
  small, // 25 XP - Quick badge popup
  medium, // 50-75 XP - Badge + subtle particles
  large, // 300+ XP - Full confetti blast
}

/// Service for managing XP gain celebrations
class XpCelebrationService {
  final Ref? _ref;

  XpCelebrationService._([this._ref]);

  static final instance = XpCelebrationService._();

  OverlayEntry? _currentOverlay;

  /// Show XP celebration overlay
  void showCelebration({
    required BuildContext context,
    required int xpGained,
    required int oldTotalXp,
    required int newTotalXp,
    List<String>? badges,
    VoidCallback? onComplete,
  }) {
    // Dismiss any existing celebration
    dismiss();

    final celebrationLevel = _getCelebrationLevel(xpGained);
    final didLevelUp = AppConstants.didLevelUp(oldTotalXp, newTotalXp);
    final newRank = didLevelUp ? AppConstants.getRankForXp(newTotalXp) : null;

    // Play appropriate sound effect
    _playCelebrationSound(context, xpGained, didLevelUp);

    _currentOverlay = OverlayEntry(
      builder: (context) => XpCelebrationOverlay(
        xpGained: xpGained,
        celebrationLevel: celebrationLevel,
        didLevelUp: didLevelUp,
        newRank: newRank,
        badges: badges ?? [],
        onComplete: () {
          dismiss();
          onComplete?.call();
        },
      ),
    );

    Overlay.of(context).insert(_currentOverlay!);
  }

  /// Play celebration sound based on XP amount and level up
  void _playCelebrationSound(BuildContext context, int xpGained, bool didLevelUp) {
    // Try to get sound service from context
    try {
      // Find ProviderScope and get sound service
      final container = ProviderScope.containerOf(context);
      final soundService = container.read(soundServiceProvider);

      if (didLevelUp) {
        soundService.playLevelUp();
      } else if (xpGained >= AppConstants.largeXpThreshold) {
        soundService.playLevelUp();
      } else {
        soundService.playXpGain();
      }
    } catch (e) {
      if (kDebugMode) {
        print('Could not play celebration sound: $e');
      }
    }
  }

  /// Dismiss current celebration
  void dismiss() {
    _currentOverlay?.remove();
    _currentOverlay?.dispose();
    _currentOverlay = null;
  }

  /// Determine celebration level based on XP amount
  CelebrationLevel _getCelebrationLevel(int xpGained) {
    if (xpGained >= AppConstants.largeXpThreshold) {
      return CelebrationLevel.large;
    } else if (xpGained >= AppConstants.mediumXpThreshold) {
      return CelebrationLevel.medium;
    } else {
      return CelebrationLevel.small;
    }
  }
}

/// Provider for XP celebration service
final xpCelebrationServiceProvider = Provider<XpCelebrationService>((ref) {
  return XpCelebrationService.instance;
});

/// Extension to easily show celebrations
extension XpCelebrationContext on BuildContext {
  void showXpCelebration({
    required int xpGained,
    required int oldTotalXp,
    required int newTotalXp,
    List<String>? badges,
    VoidCallback? onComplete,
  }) {
    XpCelebrationService.instance.showCelebration(
      context: this,
      xpGained: xpGained,
      oldTotalXp: oldTotalXp,
      newTotalXp: newTotalXp,
      badges: badges,
      onComplete: onComplete,
    );
  }
}

