import 'package:equatable/equatable.dart';

/// Streak freeze entity - Protects user's streak for 1 day if they miss
/// Similar to Duolingo's Streak Freeze feature
class StreakFreeze extends Equatable {
  /// Cost to purchase a streak freeze (in gems)
  static const int cost = 50;

  /// Maximum number of streak freezes a user can hold
  static const int maxFreezes = 2;

  /// Number of days protected by one freeze
  static const int protectionDays = 1;

  /// Number of streak freezes currently available
  final int available;

  /// Whether freeze is currently active (protecting streak)
  final bool isActive;

  /// When the current freeze was activated (if active)
  final DateTime? activatedAt;

  const StreakFreeze({
    this.available = 0,
    this.isActive = false,
    this.activatedAt,
  });

  /// Create initial state (no freezes)
  const StreakFreeze.initial()
      : available = 0,
        isActive = false,
        activatedAt = null;

  /// Create a streak freeze with purchased freezes
  StreakFreeze withPurchased() {
    if (available >= maxFreezes) return this;
    return StreakFreeze(
      available: available + 1,
      isActive: isActive,
      activatedAt: activatedAt,
    );
  }

  /// Use a streak freeze (activate it)
  StreakFreeze use() {
    if (available <= 0) return this;
    return StreakFreeze(
      available: available - 1,
      isActive: true,
      activatedAt: DateTime.now(),
    );
  }

  /// Deactivate current freeze
  StreakFreeze deactivate() {
    return StreakFreeze(
      available: available,
      isActive: false,
      activatedAt: null,
    );
  }

  /// Check if user can purchase more freezes
  bool get canPurchaseMore => available < maxFreezes;

  /// Check if user can use a freeze
  bool get canUse => available > 0 && !isActive;

  /// Create a copy with updated fields
  StreakFreeze copyWith({
    int? available,
    bool? isActive,
    DateTime? activatedAt,
  }) {
    return StreakFreeze(
      available: available ?? this.available,
      isActive: isActive ?? this.isActive,
      activatedAt: activatedAt ?? this.activatedAt,
    );
  }

  @override
  List<Object?> get props => [available, isActive, activatedAt];

  @override
  String toString() {
    return 'StreakFreeze(available: $available, isActive: $isActive, activatedAt: $activatedAt)';
  }
}

