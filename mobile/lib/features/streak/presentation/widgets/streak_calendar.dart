import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../domain/entities/streak_day.dart';

/// Streak calendar widget - Shows last 7 days of activity
/// Inspired by Duolingo's streak calendar
class StreakCalendar extends StatelessWidget {
  final List<StreakDay> days;
  final int currentStreak;

  const StreakCalendar({
    super.key,
    required this.days,
    this.currentStreak = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.white.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final maxWidth = constraints.maxWidth;
          const dayCount = 7;
          final spacing = maxWidth < 320 ? 4.0 : 6.0;
          final rawSize =
              (maxWidth - (spacing * (dayCount - 1))) / dayCount;
          final circleSize = rawSize.clamp(26.0, 40.0);
          final labelSize = circleSize < 32 ? 9.0 : 10.0;
          final emojiSize = circleSize < 32 ? 16.0 : 18.0;

          final dayWidgets = <Widget>[];
          for (var i = 0; i < days.length; i += 1) {
            dayWidgets.add(
              _buildDayCircle(
                days[i],
                size: circleSize,
                labelSize: labelSize,
                emojiSize: emojiSize,
              ),
            );
            if (i < days.length - 1) {
              dayWidgets.add(SizedBox(width: spacing));
            }
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  const Icon(
                    Icons.calendar_today,
                    color: Colors.white,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Lịch Chuỗi',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  // Streak count
                  if (currentStreak > 0) ...[
                    Text(
                      '🔥',
                      style: const TextStyle(fontSize: 16),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$currentStreak ngày',
                      style: TextStyle(
                        color: AppColors.streakOrange,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ],
              ),

              AppSpacing.verticalSpaceMD,

              // Calendar days
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: dayWidgets,
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildDayCircle(
    StreakDay day, {
    required double size,
    required double labelSize,
    required double emojiSize,
  }) {
    Color circleColor;
    Color borderColor;
    String emoji = day.statusIcon;

    if (day.isFuture) {
      circleColor = Colors.white.withOpacity(0.1);
      borderColor = Colors.white.withOpacity(0.2);
    } else if (day.usedFreeze) {
      circleColor = Colors.blue.withOpacity(0.3);
      borderColor = Colors.blue;
    } else if (day.isActive) {
      circleColor = AppColors.streakOrange.withOpacity(0.3);
      borderColor = AppColors.streakOrange;
    } else {
      circleColor = Colors.white.withOpacity(0.05);
      borderColor = Colors.white.withOpacity(0.1);
    }

    return Column(
      children: [
        // Day label
        Text(
          day.label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.6),
            fontSize: labelSize,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        // Circle
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: day.isToday ? circleColor.withOpacity(0.5) : circleColor,
            shape: BoxShape.circle,
            border: Border.all(
              color: day.isToday ? Colors.white : borderColor,
              width: day.isToday ? 2 : 1,
            ),
            boxShadow: day.isToday
                ? [
                    BoxShadow(
                      color: Colors.white.withOpacity(0.3),
                      blurRadius: 8,
                      spreadRadius: 2,
                    ),
                  ]
                : null,
          ),
          child: Center(
            child: Text(
              emoji,
              style: TextStyle(fontSize: emojiSize),
            ),
          ),
        ),
      ],
    );
  }
}
