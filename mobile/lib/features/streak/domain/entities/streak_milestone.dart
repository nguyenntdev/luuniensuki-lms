import 'package:equatable/equatable.dart';

/// Streak milestone rewards - Special bonuses at certain streak lengths
/// Inspired by Duolingo's streak milestone celebrations
class StreakMilestone extends Equatable {
  /// Predefined milestone thresholds
  static const List<int> milestones = [7, 30, 100, 365];

  /// Days required to reach this milestone
  final int days;

  /// Bonus gems awarded
  final int gemReward;

  /// Achievement name
  final String name;

  /// Description of the achievement
  final String description;

  /// Icon identifier
  final String icon;

  const StreakMilestone({
    required this.days,
    required this.gemReward,
    required this.name,
    required this.description,
    required this.icon,
  });

  /// Get milestone for a given streak count
  static StreakMilestone? forStreak(int streak) {
    if (streak >= 365) {
      return const StreakMilestone(
        days: 365,
        gemReward: 500,
        name: 'Chiến Binh Bất Bại',
        description: 'Hoàn thành 365 ngày liên tiếp!',
        icon: '👑',
      );
    } else if (streak >= 100) {
      return const StreakMilestone(
        days: 100,
        gemReward: 200,
        name: 'Bậc Thầy Kiên Trì',
        description: 'Hoàn thành 100 ngày liên tiếp!',
        icon: '🏆',
      );
    } else if (streak >= 30) {
      return const StreakMilestone(
        days: 30,
        gemReward: 75,
        name: 'Người Học Chăm Chỉ',
        description: 'Hoàn thành 30 ngày liên tiếp!',
        icon: '🎯',
      );
    } else if (streak >= 7) {
      return const StreakMilestone(
        days: 7,
        gemReward: 25,
        name: 'Tuần Hoàn Hảo',
        description: 'Hoàn thành 7 ngày liên tiếp!',
        icon: '⭐',
      );
    }
    return null;
  }

  /// Get next milestone for a given streak
  static StreakMilestone? nextMilestone(int currentStreak) {
    for (final days in milestones) {
      if (currentStreak < days) {
        return forStreak(days);
      }
    }
    return null;
  }

  /// Get days until next milestone
  static int? daysUntilNext(int currentStreak) {
    for (final days in milestones) {
      if (currentStreak < days) {
        return days - currentStreak;
      }
    }
    return null;
  }

  /// Check if a streak day is a milestone
  static bool isMilestone(int streak) {
    return milestones.contains(streak);
  }

  @override
  List<Object?> get props => [days, gemReward, name, description, icon];

  @override
  String toString() {
    return 'StreakMilestone(days: $days, name: $name, gemReward: $gemReward)';
  }
}

