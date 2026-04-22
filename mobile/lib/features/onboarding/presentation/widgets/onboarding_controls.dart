import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/storage/hive_storage.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';
import '../../../../shared/widgets/glass/index.dart';

/// Example widget showing how to integrate onboarding controls
/// This can be added to Settings screen
class OnboardingControls extends ConsumerWidget {
  const OnboardingControls({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storage = ref.watch(hiveStorageProvider);
    final hasSeenOnboarding = storage.hasSeenOnboarding();

    return GlassContainer(
      opacity: 0.08,
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.auto_awesome,
                color: AppColors.primary,
                size: 24,
              ),
              AppSpacing.horizontalSpaceMD,
              Text(
                'Onboarding',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          AppSpacing.verticalSpaceMD,

          Text(
            hasSeenOnboarding
                ? 'Bạn đã xem onboarding. Xem lại để tìm hiểu thêm về app.'
                : 'Bạn chưa hoàn thành onboarding.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
            ),
          ),

          AppSpacing.verticalSpaceMD,

          Row(
            children: [
              Expanded(
                child: GlassButton(
                  text: 'Xem Onboarding',
                  isPrimary: true,
                  onPressed: () {
                    context.push(RoutePaths.onboarding);
                  },
                ),
              ),
              if (hasSeenOnboarding) ...[
                AppSpacing.horizontalSpaceMD,
                Expanded(
                  child: GlassButton(
                    text: 'Reset',
                    isPrimary: false,
                    onPressed: () async {
                      await storage.setHasSeenOnboarding(false);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Đã reset onboarding'),
                            backgroundColor: AppColors.success,
                          ),
                        );
                      }
                    },
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

/// Example of how to check and show onboarding programmatically
class OnboardingHelper {
  /// Check if user should see onboarding
  static Future<bool> shouldShowOnboarding(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    return !storage.hasSeenOnboarding();
  }

  /// Mark onboarding as completed
  static Future<void> completeOnboarding(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(true);
  }

  /// Reset onboarding (for testing or user request)
  static Future<void> resetOnboarding(WidgetRef ref) async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(false);
  }

  /// Show onboarding if needed, then navigate to destination
  static Future<void> showOnboardingIfNeeded(
    BuildContext context,
    WidgetRef ref, {
    String destination = RoutePaths.explore,
  }) async {
    final shouldShow = await shouldShowOnboarding(ref);
    if (shouldShow && context.mounted) {
      context.go(RoutePaths.onboarding);
    } else if (context.mounted) {
      context.go(destination);
    }
  }
}
