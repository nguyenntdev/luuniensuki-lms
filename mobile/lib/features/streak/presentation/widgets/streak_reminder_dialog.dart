import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/icons/index.dart';
import '../providers/streak_provider.dart';

/// Streak reminder dialog shown when app opens and streak is at risk
/// Encourages users to complete a lesson to maintain their streak
class StreakReminderDialog extends ConsumerWidget {
  final VoidCallback onDismiss;
  final VoidCallback onStartLearning;

  const StreakReminderDialog({
    super.key,
    required this.onDismiss,
    required this.onStartLearning,
  });

  /// Show the streak reminder dialog
  static Future<void> show(
    BuildContext context, {
    required VoidCallback onStartLearning,
  }) {
    return showDialog(
      context: context,
      barrierDismissible: true,
      builder: (context) => StreakReminderDialog(
        onDismiss: () => Navigator.of(context).pop(),
        onStartLearning: () {
          Navigator.of(context).pop();
          onStartLearning();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streakState = ref.watch(streakNotifierProvider);
    final data = streakState.data;
    final hasFreeze = data.streakFreezes > 0;

    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 360),
        padding: const EdgeInsets.all(AppSpacing.xl),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.surface,
              AppColors.surfaceVariant,
            ],
          ),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: AppColors.streakOrange.withOpacity(0.3),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.streakOrange.withOpacity(0.2),
              blurRadius: 30,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Warning icon
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.streakOrange.withOpacity(0.3),
                    Colors.red.withOpacity(0.3),
                  ],
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.streakOrange.withOpacity(0.4),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: const Center(
                child: StreakIcon(
                  type: StreakIconType.fire,
                  size: 44,
                ),
              ),
            ),

            AppSpacing.verticalSpaceLG,

            // Title
            Text(
              'Chuỗi ${data.currentStreak} ngày sắp hết!',
              style: TextStyle(
                color: AppColors.streakOrange,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),

            AppSpacing.verticalSpaceMD,

            // Description
            Text(
              'Hoàn thành một bài học hôm nay để giữ chuỗi học tập của bạn!',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 16,
              ),
              textAlign: TextAlign.center,
            ),

            AppSpacing.verticalSpaceLG,

            // Streak freeze info
            if (hasFreeze)
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.blue.withOpacity(0.3),
                  ),
                ),
                child: Row(
                  children: [
                    const StreakIcon(
                      type: StreakIconType.freeze,
                      size: 24,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Bạn có ${data.streakFreezes} đóng băng',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            'Sẽ tự động bảo vệ nếu bạn bỏ lỡ',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.6),
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

            AppSpacing.verticalSpaceLG,

            // Actions
            Row(
              children: [
                // Dismiss button
                Expanded(
                  child: TextButton(
                    onPressed: onDismiss,
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(
                      'Để sau',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.6),
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),

                const SizedBox(width: AppSpacing.md),

                // Start learning button
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: onStartLearning,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.streakOrange,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        StreakIcon(
                          type: StreakIconType.fire,
                          size: 18,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Học ngay',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

