import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../../../shared/widgets/glass/animated_background.dart';
import '../../domain/entities/daily_goal.dart';
import '../providers/daily_goal_provider.dart';

/// Screen for selecting daily goal level
class DailyGoalScreen extends ConsumerWidget {
  const DailyGoalScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentGoal = ref.watch(dailyGoalNotifierProvider);

    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          title: const Text(
            'Mục tiêu hàng ngày',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => context.pop(),
          ),
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header text
                Text(
                  'Bạn muốn học bao nhiêu mỗi ngày?',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Đặt mục tiêu giúp bạn duy trì động lực học tập',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Colors.white70,
                      ),
                ),
                const SizedBox(height: AppSpacing.xl),

                // Goal options
                ...GoalLevel.values.map((level) {
                  final isSelected = currentGoal.level == level;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.md),
                    child: _GoalLevelCard(
                      level: level,
                      isSelected: isSelected,
                      onTap: () {
                        ref
                            .read(dailyGoalNotifierProvider.notifier)
                            .updateGoalLevel(level);
                      },
                    ),
                  );
                }).toList(),

                const SizedBox(height: AppSpacing.xl),

                // Info text
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.2),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.info_outline,
                        color: AppColors.info,
                        size: 24,
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Text(
                          'Bạn có thể thay đổi mục tiêu bất cứ lúc nào',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.white,
                              ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Card for displaying a goal level option
class _GoalLevelCard extends StatelessWidget {
  final GoalLevel level;
  final bool isSelected;
  final VoidCallback onTap;

  const _GoalLevelCard({
    required this.level,
    required this.isSelected,
    required this.onTap,
  });

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

  Color _getColorForLevel(GoalLevel level) {
    switch (level) {
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
  Widget build(BuildContext context) {
    final color = _getColorForLevel(level);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: isSelected 
              ? color.withOpacity(0.2)
              : Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? color : Colors.white.withOpacity(0.1),
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                _getIconForLevel(level),
                color: color,
                size: 32,
              ),
            ),
            const SizedBox(width: AppSpacing.md),

            // Text info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    level.name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    level.description,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white70,
                        ),
                  ),
                ],
              ),
            ),

            // Selection indicator
            if (isSelected)
              Icon(
                Icons.check_circle,
                color: color,
                size: 28,
              )
            else
              Icon(
                Icons.radio_button_unchecked,
                color: Colors.white.withOpacity(0.3),
                size: 28,
              ),
          ],
        ),
      ),
    );
  }
}

