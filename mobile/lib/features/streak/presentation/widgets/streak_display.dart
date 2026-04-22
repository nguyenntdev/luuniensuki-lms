import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../domain/entities/streak_day.dart' as streak_day;
import '../../domain/entities/streak_milestone.dart';
import '../providers/streak_provider.dart';
import '../widgets/streak_calendar.dart' as calendar_widget;

/// Compact streak display widget for profile screen
class StreakDisplay extends ConsumerWidget {
  final VoidCallback? onTap;

  const StreakDisplay({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streakState = ref.watch(streakNotifierProvider);
    final data = streakState.data;

    // Generate calendar days
    final days = streak_day.StreakCalendar.generateLast7Days(
      lastActiveAt: data.lastActiveAt,
      currentStreak: data.currentStreak,
    );

    // Get next milestone info
    final daysUntilNext = StreakMilestone.daysUntilNext(data.currentStreak);
    final nextMilestone = StreakMilestone.nextMilestone(data.currentStreak);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.lg),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.streakOrange.withOpacity(0.2),
              AppColors.primaryDark.withOpacity(0.2),
            ],
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: AppColors.streakOrange.withOpacity(0.3),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.streakOrange.withOpacity(0.1),
              blurRadius: 15,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with fire icon and count
            Row(
              children: [
                // Fire icon
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    color: AppColors.streakOrange.withOpacity(0.2),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.streakOrange.withOpacity(0.3),
                        blurRadius: 10,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Center(
                    child: Text(
                      '🔥',
                      style: TextStyle(fontSize: 28),
                    ),
                  ),
                ),

                const SizedBox(width: 12),

                // Streak info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            '${data.currentStreak}',
                            style: TextStyle(
                              color: AppColors.streakOrange,
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              height: 1,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'ngày',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.8),
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Chuỗi hiện tại',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.6),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),

                // Freeze count badge
                if (data.streakFreezes > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: Colors.blue.withOpacity(0.5),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text(
                          '❄️',
                          style: TextStyle(fontSize: 16),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${data.streakFreezes}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),

            AppSpacing.verticalSpaceLG,

            // Calendar
            calendar_widget.StreakCalendar(
              days: days,
              currentStreak: data.currentStreak,
            ),

            AppSpacing.verticalSpaceMD,

            // Progress to next milestone
            if (nextMilestone != null && daysUntilNext != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Text(
                      nextMilestone.icon,
                      style: const TextStyle(fontSize: 20),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            nextMilestone.name,
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Còn $daysUntilNext ngày nữa',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.6),
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      '+${nextMilestone.gemReward} 💎',
                      style: TextStyle(
                        color: AppColors.gemYellow,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Longest streak
            if (data.longestStreak > data.currentStreak) ...[
              AppSpacing.verticalSpaceSM,
              Text(
                'Kỷ lục: ${data.longestStreak} ngày 🏆',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

