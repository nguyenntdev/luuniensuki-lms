import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../routing/route_names.dart';
import '../../domain/entities/daily_goal.dart';
import '../providers/daily_goal_provider.dart';

/// Compact daily goal widget for explore screen header
class CompactDailyGoalWidget extends ConsumerWidget {
  const CompactDailyGoalWidget({super.key});

  Color _getProgressColor(DailyGoal goal) {
    if (goal.isCompleted) return AppColors.success;
    
    switch (goal.level) {
      case GoalLevel.casual:
        return AppColors.success;
      case GoalLevel.regular:
        return AppColors.primary;
      case GoalLevel.serious:
        return AppColors.warning;
      case GoalLevel.intense:
        return AppColors.error;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goal = ref.watch(dailyGoalNotifierProvider);
    final progressColor = _getProgressColor(goal);

    return InkWell(
      onTap: () => context.push(RoutePaths.dailyGoal),
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
            colors: [
              Colors.white.withOpacity(0.15),
              Colors.white.withOpacity(0.05),
            ],
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: Row(
          children: [
            // Icon
            Icon(
              goal.isCompleted ? Icons.check_circle : Icons.flag_outlined,
              color: goal.isCompleted ? AppColors.success : Colors.white,
              size: 20,
            ),
            const SizedBox(width: AppSpacing.sm),

            // Text and progress
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // XP Progress text
                  Row(
                    children: [
                      Text(
                        '${goal.currentXp}/${goal.level.xpRequired} XP',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      if (goal.isCompleted)
                        Icon(
                          Icons.verified,
                          color: AppColors.success,
                          size: 16,
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),

                  // Progress bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: goal.progressPercentage,
                      minHeight: 4,
                      backgroundColor: Colors.white.withOpacity(0.2),
                      valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: AppSpacing.sm),

            // Arrow indicator
            Icon(
              Icons.chevron_right,
              color: Colors.white60,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}
