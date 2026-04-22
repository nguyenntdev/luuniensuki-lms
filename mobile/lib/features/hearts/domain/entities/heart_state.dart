import 'package:freezed_annotation/freezed_annotation.dart';

part 'heart_state.freezed.dart';
part 'heart_state.g.dart';

/// Heart state entity representing the user's current hearts/energy
@freezed
class HeartState with _$HeartState {
  const factory HeartState({
    /// Maximum number of hearts a user can have
    @Default(5) int maxHearts,
    
    /// Current number of hearts
    @Default(5) int currentHearts,
    
    /// Last time hearts were refilled (either auto or manual)
    required DateTime lastRefillTime,
    
    /// Refill interval in minutes (1 heart per 30 minutes)
    @Default(30) int refillIntervalMinutes,
    
    /// Whether hearts are unlimited (e.g., premium feature)
    @Default(false) bool isUnlimited,
  }) = _HeartState;

  const HeartState._();

  /// Create from JSON
  factory HeartState.fromJson(Map<String, dynamic> json) =>
      _$HeartStateFromJson(json);

  /// Create initial state with full hearts
  factory HeartState.initial() => HeartState(
        maxHearts: 5,
        currentHearts: 5,
        lastRefillTime: DateTime.now(),
        refillIntervalMinutes: 30,
        isUnlimited: false,
      );

  /// Check if user has any hearts left
  bool get hasHearts => currentHearts > 0 || isUnlimited;

  /// Check if hearts are full
  bool get isFull => currentHearts >= maxHearts || isUnlimited;

  /// Get number of hearts that can be refilled
  int get heartsToRefill => maxHearts - currentHearts;

  /// Calculate how many hearts should be refilled based on time passed
  int calculateRefillableHearts() {
    if (isUnlimited || isFull) return 0;

    final now = DateTime.now();
    final timePassed = now.difference(lastRefillTime);
    final minutesPassed = timePassed.inMinutes;

    // Calculate how many hearts can be refilled
    final heartsToAdd = minutesPassed ~/ refillIntervalMinutes;

    // Cap at max hearts
    return heartsToAdd.clamp(0, heartsToRefill);
  }

  /// Get time until next heart refill
  Duration getTimeUntilNextRefill() {
    if (isUnlimited || isFull) return Duration.zero;

    final now = DateTime.now();
    final timePassed = now.difference(lastRefillTime);
    final minutesPassed = timePassed.inMinutes;
    final minutesUntilNext = refillIntervalMinutes - (minutesPassed % refillIntervalMinutes);

    return Duration(minutes: minutesUntilNext);
  }

  /// Get formatted time string for next refill (e.g., "15:30")
  String getTimeUntilNextRefillFormatted() {
    if (isUnlimited || isFull) return "";

    final duration = getTimeUntilNextRefill();
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;

    if (hours > 0) {
      return "${hours}h ${minutes}m";
    } else {
      return "${minutes}m";
    }
  }

  /// Lose a heart (called when user answers incorrectly)
  HeartState loseHeart() {
    if (isUnlimited || currentHearts <= 0) return this;

    return copyWith(
      currentHearts: currentHearts - 1,
    );
  }

  /// Refill all hearts (called when user spends gems or watches ad)
  HeartState refillAll() {
    return copyWith(
      currentHearts: maxHearts,
      lastRefillTime: DateTime.now(),
    );
  }

  /// Auto-refill hearts based on time passed
  HeartState autoRefill() {
    if (isUnlimited || isFull) return this;

    final heartsToAdd = calculateRefillableHearts();
    if (heartsToAdd <= 0) return this;

    final newHearts = (currentHearts + heartsToAdd).clamp(0, maxHearts);

    // Update lastRefillTime to the timestamp of the last full interval
    final now = DateTime.now();
    final timePassed = now.difference(lastRefillTime);
    final fullIntervalsPassed = timePassed.inMinutes ~/ refillIntervalMinutes;
    final newLastRefillTime = lastRefillTime.add(
      Duration(minutes: fullIntervalsPassed * refillIntervalMinutes),
    );

    return copyWith(
      currentHearts: newHearts,
      lastRefillTime: newLastRefillTime,
    );
  }

  /// Add a single heart (for rewards, practice mode, etc.)
  HeartState addHeart() {
    if (isUnlimited || isFull) return this;

    return copyWith(
      currentHearts: (currentHearts + 1).clamp(0, maxHearts),
    );
  }

  /// Set unlimited hearts (e.g., for premium users)
  HeartState setUnlimited(bool unlimited) {
    return copyWith(
      isUnlimited: unlimited,
      currentHearts: unlimited ? maxHearts : currentHearts,
    );
  }
}

