import 'package:equatable/equatable.dart';

/// Streak calendar day model - represents a single day's activity
class StreakDay extends Equatable {
  /// The date of this day
  final DateTime date;

  /// Whether user was active on this day
  final bool isActive;

  /// Whether this day used a streak freeze
  final bool usedFreeze;

  /// Whether this is today
  final bool isToday;

  /// Whether this is in the future
  final bool isFuture;

  const StreakDay({
    required this.date,
    this.isActive = false,
    this.usedFreeze = false,
    this.isToday = false,
    this.isFuture = false,
  });

  /// Create a streak day from date and activity status
  factory StreakDay.fromDate(
    DateTime date, {
    bool isActive = false,
    bool usedFreeze = false,
  }) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final dayDate = DateTime(date.year, date.month, date.day);

    return StreakDay(
      date: dayDate,
      isActive: isActive,
      usedFreeze: usedFreeze,
      isToday: dayDate.isAtSameMomentAs(today),
      isFuture: dayDate.isAfter(today),
    );
  }

  /// Get color for this day's status
  String get statusColor {
    if (isFuture) return 'gray';
    if (usedFreeze) return 'blue'; // Freeze protected
    if (isActive) return 'orange'; // Active day
    return 'gray'; // Missed day
  }

  /// Get icon type for this day's status
  /// This is used by the UI to determine which Material Icon to display
  /// Returns null if no icon should be displayed
  String? get iconType {
    if (isFuture) return null;
    if (usedFreeze) return 'freeze'; // Use StreakIconType.freeze
    if (isActive) return 'fire'; // Use StreakIconType.fire
    return null; // No icon for missed
  }

  /// Get label for this day
  String get label {
    final weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
    return weekdays[date.weekday - 1];
  }

  @override
  List<Object?> get props => [date, isActive, usedFreeze, isToday, isFuture];

  @override
  String toString() {
    return 'StreakDay(date: $date, active: $isActive, freeze: $usedFreeze)';
  }
}

/// Generate a list of streak days for calendar display
class StreakCalendar {
  /// Generate last N days for streak calendar
  static List<StreakDay> generateLast7Days({
    DateTime? lastActiveAt,
    int currentStreak = 0,
  }) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final days = <StreakDay>[];

    // Generate last 7 days
    for (int i = 6; i >= 0; i--) {
      final date = today.subtract(Duration(days: i));
      final lastActiveDate = lastActiveAt != null
          ? DateTime(
              lastActiveAt.year,
              lastActiveAt.month,
              lastActiveAt.day,
            )
          : null;

      // Calculate if this day was active
      bool isActive = false;
      if (lastActiveDate != null) {
        final daysDiff = today.difference(date).inDays;
        isActive = daysDiff < currentStreak &&
            date.isBefore(today.add(const Duration(days: 1)));
      }

      days.add(StreakDay.fromDate(date, isActive: isActive));
    }

    return days;
  }
}

