import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../domain/entities/daily_goal.dart';
import '../providers/daily_goal_provider.dart';

/// Widget showing daily goal progress
class DailyGoalWidget extends ConsumerWidget {
  const DailyGoalWidget({super.key});

  /// Format time remaining (e.g., "12h 30m")
  String _formatTimeRemaining(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    
    if (hours > 0) {
      return '${hours}h ${minutes}m còn lại';
    } else {
      return '${minutes}m còn lại';
    }
  }

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
    final timeRemaining = ref.read(dailyGoalNotifierProvider.notifier).getTimeUntilMidnight();
    final progressColor = _getProgressColor(goal);

    return InkWell(
      onTap: () => context.push('/daily-goal'),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Colors.white.withOpacity(0.1),
              Colors.white.withOpacity(0.05),
            ],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: Colors.white.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              children: [
                Icon(
                  goal.isCompleted ? Icons.check_circle : Icons.flag_outlined,
                  color: goal.isCompleted ? AppColors.success : Colors.white,
                  size: 24,
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    goal.isCompleted ? 'Mục tiêu hoàn thành!' : 'Mục tiêu hôm nay',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ),
                Text(
                  _formatTimeRemaining(timeRemaining),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.white60,
                      ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),

            // XP Progress
            Row(
              children: [
                Text(
                  '${goal.currentXp}',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: progressColor,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  ' / ${goal.level.xpRequired} XP',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white70,
                      ),
                ),
                const Spacer(),
                if (!goal.isCompleted)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.sm,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: progressColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${goal.remainingXp} XP nữa',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: progressColor,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),

            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: goal.progressPercentage,
                minHeight: 8,
                backgroundColor: Colors.white.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation<Color>(progressColor),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),

            // Goal level indicator
            Row(
              children: [
                Icon(
                  _getIconForLevel(goal.level),
                  color: Colors.white70,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  goal.level.name,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.white70,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  IconData _getIconForLevel(GoalLevel level) {
    switch (level) {
      case GoalLevel.casual:
        return Icons.self_improvement;
      case GoalLevel.regular:
        return Icons.directions_walk;
      case GoalLevel.serious:
        return Icons.directions_run;
      case GoalLevel.intense:
        return Icons.flash_on;
    }
  }
}

