import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/presentation/providers/auth_provider.dart';
import '../services/xp_celebration_service.dart';

/// Helper widget to show XP celebrations when XP changes
/// Can be used anywhere in the app where XP is gained
class XpGainHandler extends ConsumerStatefulWidget {
  final Widget child;

  const XpGainHandler({
    super.key,
    required this.child,
  });

  @override
  ConsumerState<XpGainHandler> createState() => _XpGainHandlerState();
}

class _XpGainHandlerState extends ConsumerState<XpGainHandler> {
  int? _previousXp;

  @override
  Widget build(BuildContext context) {
    // Watch for user XP changes
    final user = ref.watch(currentUserProvider);
    
    // If user exists and XP changed, show celebration
    if (user != null) {
      if (_previousXp != null && user.totalXp > _previousXp!) {
        // XP increased - show celebration
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            context.showXpCelebration(
              xpGained: user.totalXp - _previousXp!,
              oldTotalXp: _previousXp!,
              newTotalXp: user.totalXp,
            );
          }
        });
      }
      _previousXp = user.totalXp;
    }

    return widget.child;
  }
}

/// Extension methods for showing XP celebrations programmatically
extension XpCelebrationHelpers on BuildContext {
  /// Show celebration for a specific XP gain result
  void celebrateXpGain({
    required int xpGained,
    required int oldTotalXp,
    required int newTotalXp,
    List<String>? badges,
    VoidCallback? onComplete,
  }) {
    if (xpGained > 0) {
      showXpCelebration(
        xpGained: xpGained,
        oldTotalXp: oldTotalXp,
        newTotalXp: newTotalXp,
        badges: badges,
        onComplete: onComplete,
      );
    }
  }
}

