/// Onboarding Test Helper
/// Use this in Flutter DevTools console or in debug builds to test onboarding
///
/// Example usage:
/// ```dart
/// // In your app (debug build only):
/// if (kDebugMode) {
///   OnboardingTestHelper.showTestControls(context, ref);
/// }
/// ```

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/storage/hive_storage.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/glass/index.dart';

/// Debug helper for testing onboarding
class OnboardingTestHelper {
  /// Show a floating button to control onboarding (debug only)
  static Widget showTestControls(BuildContext context, WidgetRef ref) {
    if (!kDebugMode) return const SizedBox.shrink();

    return Positioned(
      bottom: 100,
      right: 16,
      child: _OnboardingTestWidget(ref: ref),
    );
  }

  /// Quick reset and show onboarding
  static Future<void> resetAndShow(BuildContext context, WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(false);

    if (context.mounted) {
      context.go('/onboarding');
    }
  }

  /// Check current status
  static Future<void> checkStatus(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    final hasSeenOnboarding = storage.hasSeenOnboarding();

    debugPrint('=== Onboarding Status ===');
    debugPrint('Has Seen Onboarding: $hasSeenOnboarding');
    debugPrint('========================');
  }

  /// Complete onboarding (for testing)
  static Future<void> markAsCompleted(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(true);
    debugPrint('Onboarding marked as completed');
  }

  /// Reset onboarding (for testing)
  static Future<void> reset(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(false);
    debugPrint('Onboarding reset');
  }
}

class _OnboardingTestWidget extends ConsumerStatefulWidget {
  final WidgetRef ref;

  const _OnboardingTestWidget({required this.ref});

  @override
  ConsumerState<_OnboardingTestWidget> createState() =>
      _OnboardingTestWidgetState();
}

class _OnboardingTestWidgetState extends ConsumerState<_OnboardingTestWidget> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final storage = ref.watch(hiveStorageProvider);
    final hasSeenOnboarding = storage.hasSeenOnboarding();

    return GlassContainer(
      opacity: 0.15,
      padding: const EdgeInsets.all(AppSpacing.sm),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Toggle button
          GestureDetector(
            onTap: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            child: Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(AppSpacing.radiusRound),
              ),
              child: Icon(
                _isExpanded ? Icons.close : Icons.bug_report,
                color: AppColors.onPrimary,
                size: 24,
              ),
            ),
          ),

          if (_isExpanded) ...[
            AppSpacing.verticalSpaceSM,
            
            // Status
            Text(
              hasSeenOnboarding ? '✓ Completed' : '○ Not completed',
              style: TextStyle(
                color: hasSeenOnboarding
                    ? AppColors.success
                    : AppColors.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),

            AppSpacing.verticalSpaceSM,

            // Show button
            SizedBox(
              width: 120,
              child: GlassButton(
                text: 'Show',
                isPrimary: true,
                height: 36,
                onPressed: () {
                  context.push('/onboarding');
                },
              ),
            ),

            AppSpacing.verticalSpaceXS,

            // Reset button
            SizedBox(
              width: 120,
              child: GlassButton(
                text: 'Reset',
                isPrimary: false,
                height: 36,
                onPressed: () async {
                  await OnboardingTestHelper.reset(ref);
                  setState(() {});
                },
              ),
            ),

            AppSpacing.verticalSpaceXS,

            // Complete button
            SizedBox(
              width: 120,
              child: GlassButton(
                text: 'Complete',
                isPrimary: false,
                height: 36,
                onPressed: () async {
                  await OnboardingTestHelper.markAsCompleted(ref);
                  setState(() {});
                },
              ),
            ),
          ],
        ],
      ),
    );
  }
}

