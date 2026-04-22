import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../../domain/entities/streak_data.dart';
import '../../domain/entities/streak_freeze.dart';
import '../../domain/entities/streak_milestone.dart';

part 'streak_provider.freezed.dart';
part 'streak_provider.g.dart';

/// Streak state model
@freezed
class StreakState with _$StreakState {
  const factory StreakState({
    @Default(StreakData.initial()) StreakData data,
    @Default(StreakFreeze.initial()) StreakFreeze freeze,
    @Default(false) bool isLoading,
    @Default(false) bool isRefreshing,
    String? error,
    StreakMilestone? justReachedMilestone,
  }) = _StreakState;
}

/// Streak provider - manages streak tracking and features
@Riverpod(keepAlive: true)
class StreakNotifier extends _$StreakNotifier {
  @override
  StreakState build() {
    // Load streak data on initialization
    loadStreak();
    return const StreakState();
  }

  /// Load streak data from API
  Future<void> loadStreak() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final apiClient = ref.read(apiClientProvider);
      final response = await apiClient.get<Map<String, dynamic>>(
        ApiConstants.streak,
        parser: (json) => json as Map<String, dynamic>,
      );

      final streakData = StreakData.fromJson(response);
      final freezeData = StreakFreeze(
        available: streakData.streakFreezes,
        isActive: false,
      );

      state = state.copyWith(
        data: streakData,
        freeze: freezeData,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Không thể tải dữ liệu chuỗi: $e',
      );
    }
  }

  /// Refresh streak data
  Future<void> refresh() async {
    state = state.copyWith(isRefreshing: true, error: null);

    try {
      final apiClient = ref.read(apiClientProvider);
      final response = await apiClient.get<Map<String, dynamic>>(
        ApiConstants.streak,
        parser: (json) => json as Map<String, dynamic>,
      );

      final streakData = StreakData.fromJson(response);
      final freezeData = StreakFreeze(
        available: streakData.streakFreezes,
        isActive: false,
      );

      state = state.copyWith(
        data: streakData,
        freeze: freezeData,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isRefreshing: false,
        error: 'Không thể làm mới dữ liệu: $e',
      );
    }
  }

  /// Purchase a streak freeze with gems
  Future<bool> purchaseStreakFreeze() async {
    // Check if user can purchase more
    if (!state.freeze.canPurchaseMore) {
      state = state.copyWith(
        error: 'Bạn đã có tối đa ${StreakFreeze.maxFreezes} đóng băng chuỗi',
      );
      return false;
    }

    // Check gems balance and spend
    final gemsNotifier = ref.read(gemsNotifierProvider.notifier);
    final success = await gemsNotifier.spendGems(
      amount: StreakFreeze.cost,
      type: GemTransactionType.spentStreakFreeze,
      description: 'Mua Đóng Băng Chuỗi',
    );

    if (!success) {
      state = state.copyWith(
        error: 'Không đủ Gems! Cần ${StreakFreeze.cost} gems.',
      );
      return false;
    }

    // Update local state
    state = state.copyWith(
      freeze: state.freeze.withPurchased(),
      data: state.data.copyWith(
        streakFreezes: state.freeze.available + 1,
      ),
    );

    return true;
  }

  /// Use a streak freeze to protect streak
  Future<bool> useStreakFreeze() async {
    if (!state.freeze.canUse) {
      state = state.copyWith(
        error: 'Không có đóng băng chuỗi để sử dụng',
      );
      return false;
    }

    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.post<Map<String, dynamic>>(
        ApiConstants.useStreakFreeze,
        parser: (json) => json as Map<String, dynamic>,
      );

      // Update local state
      state = state.copyWith(
        freeze: state.freeze.use(),
        data: state.data.copyWith(
          streakFreezes: state.freeze.available - 1,
        ),
      );

      return true;
    } catch (e) {
      state = state.copyWith(
        error: 'Không thể sử dụng đóng băng: $e',
      );
      return false;
    }
  }

  /// Check for milestone achievement and award gems
  Future<void> checkMilestone(int newStreak) async {
    final milestone = StreakMilestone.forStreak(newStreak);
    if (milestone == null) return;

    // Check if this is a new milestone (not previously reached)
    final previousMilestone = StreakMilestone.forStreak(newStreak - 1);
    if (milestone != previousMilestone) {
      // Award gems for milestone
      final gemsNotifier = ref.read(gemsNotifierProvider.notifier);
      await gemsNotifier.addGems(
        amount: milestone.gemReward,
        type: GemTransactionType.earnedStreak,
        description: 'Cột mốc chuỗi: ${milestone.name}',
      );

      // Show milestone celebration
      state = state.copyWith(
        justReachedMilestone: milestone,
      );

      // Clear milestone after 5 seconds
      Future.delayed(const Duration(seconds: 5), () {
        state = state.copyWith(justReachedMilestone: null);
      });
    }
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}
