import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/storage/hive_storage.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../auth/presentation/providers/auth_state.dart';
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../../domain/entities/daily_goal.dart';

part 'daily_goal_provider.g.dart';

/// Daily goal state management
@Riverpod(keepAlive: true)
class DailyGoalNotifier extends _$DailyGoalNotifier {
  static const String _storageKey = 'daily_goal';

  HiveStorage get _storage => ref.read(hiveStorageProvider);

  @override
  DailyGoal build() {
    // Load saved goal or create initial one
    final saved = _loadFromStorage();
    final now = DateTime.now();

    // Reset if it's a new day
    if (saved != null && saved.shouldReset(now)) {
      final reset = DailyGoal(
        level: saved.level, // Keep the same level
        currentXp: 0,
        lastUpdated: now,
        isCompleted: false,
      );
      _saveToStorage(reset);
      return reset;
    }

    return saved ?? DailyGoal.initial();
  }

  /// Load goal from storage
  DailyGoal? _loadFromStorage() {
    try {
      final json = _storage.getSetting<Map>(_storageKey);
      if (json == null) return null;
      return DailyGoal.fromJson(Map<String, dynamic>.from(json));
    } catch (e) {
      // If there's an error, return null and use initial goal
      return null;
    }
  }

  /// Save goal to storage
  Future<void> _saveToStorage(DailyGoal goal) async {
    await _storage.setSetting(_storageKey, goal.toJson());
  }

  /// Update goal level
  Future<void> updateGoalLevel(GoalLevel newLevel) async {
    final now = DateTime.now();
    
    // Check if we need to reset for a new day
    final shouldReset = state.shouldReset(now);
    
    final updated = state.copyWith(
      level: newLevel,
      currentXp: shouldReset ? 0 : state.currentXp,
      lastUpdated: now,
      isCompleted: shouldReset ? false : state.isCompleted,
    );
    
    state = updated;
    await _saveToStorage(updated);
  }

  /// Add XP progress to daily goal
  /// Returns true if the goal was just completed
  Future<bool> addXp(int xpGained) async {
    if (xpGained <= 0) return false;

    final now = DateTime.now();

    // Reset if it's a new day
    if (state.shouldReset(now)) {
      state = DailyGoal(
        level: state.level,
        currentXp: 0,
        lastUpdated: now,
        isCompleted: false,
      );
    }

    final newXp = state.currentXp + xpGained;
    final wasCompleted = state.isCompleted;
    final isNowCompleted = newXp >= state.level.xpRequired;

    final updated = state.copyWith(
      currentXp: newXp,
      lastUpdated: now,
      isCompleted: isNowCompleted,
    );

    state = updated;
    await _saveToStorage(updated);

    // Award gems when daily goal is completed
    if (!wasCompleted && isNowCompleted) {
      await ref.read(gemsNotifierProvider.notifier).addGems(
            amount: 20,
            type: GemTransactionType.earnedBonus,
            description: 'Hoàn thành mục tiêu hàng ngày',
          );
    }

    // Return whether goal was just completed
    return !wasCompleted && isNowCompleted;
  }

  /// Reset daily goal (for new day or manual reset)
  Future<void> reset() async {
    final now = DateTime.now();
    final reset = DailyGoal(
      level: state.level,
      currentXp: 0,
      lastUpdated: now,
      isCompleted: false,
    );
    
    state = reset;
    await _saveToStorage(reset);
  }

  /// Get time remaining until midnight (for display)
  Duration getTimeUntilMidnight() {
    final now = DateTime.now();
    final tomorrow = DateTime(now.year, now.month, now.day + 1);
    return tomorrow.difference(now);
  }
}

/// Provider that watches for XP changes and updates daily goal
@riverpod
class DailyGoalXpSync extends _$DailyGoalXpSync {
  int? _previousTotalXp;

  @override
  void build() {
    // Watch for auth state changes
    ref.listen(
      authNotifierProvider,
      (previous, next) {
        // Update XP when user data changes
        if (next.isAuthenticated && next.user != null) {
          _checkXpChange(next.user!.totalXp);
        }
      },
    );

    // Initial check
    final user = ref.watch(currentUserProvider);
    if (user != null) {
      _checkXpChange(user.totalXp);
    }
  }

  void _checkXpChange(int currentTotalXp) {
    if (_previousTotalXp != null) {
      final xpGained = currentTotalXp - _previousTotalXp!;
      if (xpGained > 0) {
        // Update daily goal with gained XP
        ref.read(dailyGoalNotifierProvider.notifier).addXp(xpGained);
      }
    }
    _previousTotalXp = currentTotalXp;
  }
}

