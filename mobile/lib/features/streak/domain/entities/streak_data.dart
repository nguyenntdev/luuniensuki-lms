import 'package:equatable/equatable.dart';

/// Streak data model representing a user's daily activity streak
class StreakData extends Equatable {
  /// Current active streak (consecutive days)
  final int currentStreak;

  /// Longest streak ever achieved
  final int longestStreak;

  /// Number of streak freezes available
  final int streakFreezes;

  /// Last active date
  final DateTime? lastActiveAt;

  /// Days since last active
  final int? daysSinceLastActive;

  /// Whether streak is at risk (missed yesterday)
  final bool isAtRisk;

  const StreakData({
    required this.currentStreak,
    required this.longestStreak,
    required this.streakFreezes,
    this.lastActiveAt,
    this.daysSinceLastActive,
    this.isAtRisk = false,
  });

  /// Create initial/empty streak data
  const StreakData.initial()
      : currentStreak = 0,
        longestStreak = 0,
        streakFreezes = 0,
        lastActiveAt = null,
        daysSinceLastActive = null,
        isAtRisk = false;

  /// Create from JSON (API response)
  factory StreakData.fromJson(Map<String, dynamic> json) {
    final lastActive = json['last_active_at'] != null
        ? DateTime.parse(json['last_active_at'] as String)
        : null;

    final daysSince = json['days_since_last_active'] as int?;
    final isAtRisk = daysSince != null && daysSince > 0;

    return StreakData(
      currentStreak: json['current_streak'] as int? ?? 0,
      longestStreak: json['longest_streak'] as int? ?? 0,
      streakFreezes: json['streak_freezes'] as int? ?? 0,
      lastActiveAt: lastActive,
      daysSinceLastActive: daysSince,
      isAtRisk: isAtRisk,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'current_streak': currentStreak,
      'longest_streak': longestStreak,
      'streak_freezes': streakFreezes,
      'last_active_at': lastActiveAt?.toIso8601String(),
      'days_since_last_active': daysSinceLastActive,
    };
  }

  /// Create a copy with updated fields
  StreakData copyWith({
    int? currentStreak,
    int? longestStreak,
    int? streakFreezes,
    DateTime? lastActiveAt,
    int? daysSinceLastActive,
    bool? isAtRisk,
  }) {
    return StreakData(
      currentStreak: currentStreak ?? this.currentStreak,
      longestStreak: longestStreak ?? this.longestStreak,
      streakFreezes: streakFreezes ?? this.streakFreezes,
      lastActiveAt: lastActiveAt ?? this.lastActiveAt,
      daysSinceLastActive: daysSinceLastActive ?? this.daysSinceLastActive,
      isAtRisk: isAtRisk ?? this.isAtRisk,
    );
  }

  @override
  List<Object?> get props => [
        currentStreak,
        longestStreak,
        streakFreezes,
        lastActiveAt,
        daysSinceLastActive,
        isAtRisk,
      ];

  @override
  String toString() {
    return 'StreakData(current: $currentStreak, longest: $longestStreak, freezes: $streakFreezes)';
  }
}

