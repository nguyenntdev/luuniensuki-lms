import 'package:equatable/equatable.dart';

/// Goal level options similar to Duolingo
enum GoalLevel {
  casual(5, 'Thoải mái', '5 phút/ngày'),
  regular(10, 'Thường xuyên', '10 phút/ngày'),
  serious(20, 'Nghiêm túc', '20 phút/ngày'),
  intense(30, 'Cao thủ', '30 phút/ngày');

  const GoalLevel(this.xpRequired, this.name, this.description);

  final int xpRequired;
  final String name;
  final String description;

  /// Get goal level from XP value
  static GoalLevel fromXp(int xp) {
    if (xp >= 30) return GoalLevel.intense;
    if (xp >= 20) return GoalLevel.serious;
    if (xp >= 10) return GoalLevel.regular;
    return GoalLevel.casual;
  }

  /// Get goal level from string name
  static GoalLevel fromString(String name) {
    return GoalLevel.values.firstWhere(
      (level) => level.toString().split('.').last == name,
      orElse: () => GoalLevel.regular,
    );
  }
}

/// Daily goal entity tracking progress
class DailyGoal extends Equatable {
  final GoalLevel level;
  final int currentXp;
  final DateTime lastUpdated;
  final bool isCompleted;

  const DailyGoal({
    required this.level,
    this.currentXp = 0,
    required this.lastUpdated,
    this.isCompleted = false,
  });

  /// Create initial goal with default values
  factory DailyGoal.initial() {
    return DailyGoal(
      level: GoalLevel.regular,
      currentXp: 0,
      lastUpdated: DateTime.now(),
      isCompleted: false,
    );
  }

  /// Create from JSON
  factory DailyGoal.fromJson(Map<String, dynamic> json) {
    return DailyGoal(
      level: GoalLevel.fromString(json['level'] as String),
      currentXp: json['currentXp'] as int? ?? 0,
      lastUpdated: DateTime.parse(json['lastUpdated'] as String),
      isCompleted: json['isCompleted'] as bool? ?? false,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'level': level.toString().split('.').last,
      'currentXp': currentXp,
      'lastUpdated': lastUpdated.toIso8601String(),
      'isCompleted': isCompleted,
    };
  }

  /// Copy with updated fields
  DailyGoal copyWith({
    GoalLevel? level,
    int? currentXp,
    DateTime? lastUpdated,
    bool? isCompleted,
  }) {
    return DailyGoal(
      level: level ?? this.level,
      currentXp: currentXp ?? this.currentXp,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }

  /// Get progress percentage
  double get progressPercentage {
    if (level.xpRequired == 0) return 0.0;
    return (currentXp / level.xpRequired).clamp(0.0, 1.0);
  }

  /// Get remaining XP to complete goal
  int get remainingXp {
    final remaining = level.xpRequired - currentXp;
    return remaining > 0 ? remaining : 0;
  }

  /// Check if this goal should be reset (different day)
  bool shouldReset(DateTime now) {
    final lastDate = DateTime(
      lastUpdated.year,
      lastUpdated.month,
      lastUpdated.day,
    );
    final currentDate = DateTime(now.year, now.month, now.day);
    return currentDate.isAfter(lastDate);
  }

  @override
  List<Object?> get props => [level, currentXp, lastUpdated, isCompleted];

  @override
  String toString() {
    return 'DailyGoal(level: ${level.name}, currentXp: $currentXp/${level.xpRequired}, isCompleted: $isCompleted)';
  }
}

