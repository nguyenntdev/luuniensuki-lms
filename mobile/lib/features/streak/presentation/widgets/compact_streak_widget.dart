import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/icons/streak_icon.dart';
import '../../../../shared/widgets/icons/milestone_icon.dart';
import '../../domain/entities/streak_milestone.dart';
import '../providers/streak_provider.dart';

/// Compact streak widget for explore screen header
/// Shows current streak with fire icon and progress to next milestone
class CompactStreakWidget extends ConsumerWidget {
  const CompactStreakWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streakState = ref.watch(streakNotifierProvider);
    final data = streakState.data;
    final hasStreak = data.currentStreak > 0;
    final isAtRisk = data.isAtRisk;

    // Get next milestone info
    final daysUntilNext = StreakMilestone.daysUntilNext(data.currentStreak);
    final nextMilestone = StreakMilestone.nextMilestone(data.currentStreak);

    return InkWell(
      onTap: () => context.push('/profile'),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: isAtRisk
                ? [
                    Colors.red.withOpacity(0.25),
                    Colors.red.withOpacity(0.1),
                  ]
                : hasStreak
                    ? [
                        AppColors.streakOrange.withOpacity(0.25),
                        AppColors.streakOrange.withOpacity(0.1),
                      ]
                    : [
                        Colors.white.withOpacity(0.15),
                        Colors.white.withOpacity(0.05),
                      ],
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isAtRisk
                ? Colors.red.withOpacity(0.4)
                : hasStreak
                    ? AppColors.streakOrange.withOpacity(0.4)
                    : Colors.white.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Fire icon with glow effect
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: isAtRisk
                    ? Colors.red.withOpacity(0.2)
                    : hasStreak
                        ? AppColors.streakOrange.withOpacity(0.2)
                        : Colors.white.withOpacity(0.1),
                shape: BoxShape.circle,
                boxShadow: hasStreak || isAtRisk
                    ? [
                        BoxShadow(
                          color: isAtRisk
                              ? Colors.red.withOpacity(0.3)
                              : AppColors.streakOrange.withOpacity(0.3),
                          blurRadius: 8,
                          spreadRadius: 1,
                        ),
                      ]
                    : null,
              ),
              child: Center(
                child: StreakIcon(
                  type: isAtRisk
                      ? StreakIconType.warning
                      : (hasStreak ? StreakIconType.fire : StreakIconType.freeze),
                  size: 18,
                ),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),

            // Streak info - wrapped in Flexible to prevent overflow
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${data.currentStreak}',
                        style: TextStyle(
                          color: isAtRisk
                              ? Colors.red
                              : hasStreak
                                  ? AppColors.streakOrange
                                  : Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          height: 1,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'ngày',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                  if (isAtRisk)
                    Text(
                      'Sắp mất chuỗi!',
                      style: TextStyle(
                        color: Colors.red.withOpacity(0.9),
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    )
                  else if (nextMilestone != null && daysUntilNext != null)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'Còn $daysUntilNext ngày đến ',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 10,
                          ),
                        ),
                        SimpleMilestoneIcon(
                          days: nextMilestone.days,
                          size: 12,
                        ),
                      ],
                    ),
                ],
              ),
            ),

            // Freeze count if available
            if (data.streakFreezes > 0) ...[
              const SizedBox(width: AppSpacing.sm),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const StreakIcon(
                      type: StreakIconType.freeze,
                      size: 14,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${data.streakFreezes}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

