import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../data/repositories/daily_missions_repository.dart';
import '../../domain/entities/daily_mission.dart';

part 'daily_missions_provider.g.dart';

/// State for daily missions
class DailyMissionsState {
  final DailyMissionsSummary? summary;
  final bool isLoading;
  final String? error;

  const DailyMissionsState({
    this.summary,
    this.isLoading = false,
    this.error,
  });

  DailyMissionsState copyWith({
    DailyMissionsSummary? summary,
    bool? isLoading,
    String? error,
  }) {
    return DailyMissionsState(
      summary: summary ?? this.summary,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Provider for daily missions
@riverpod
class DailyMissionsNotifier extends _$DailyMissionsNotifier {
  @override
  DailyMissionsState build() {
    // Auto-load missions on build
    loadMissions();
    return const DailyMissionsState(isLoading: true);
  }

  /// Load today's missions
  Future<void> loadMissions() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final repository = ref.read(dailyMissionsRepositoryProvider);
      final summary = await repository.getTodayMissions();

      state = DailyMissionsState(
        summary: summary,
        isLoading: false,
        error: null,
      );
    } catch (e) {
      state = DailyMissionsState(
        summary: state.summary,
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Update mission progress
  Future<bool> updateProgress(String missionId, {int increment = 1}) async {
    try {
      final repository = ref.read(dailyMissionsRepositoryProvider);
      final updatedMission = await repository.updateMissionProgress(
        missionId: missionId,
        increment: increment,
      );

      // Update the mission in the current state
      if (state.summary != null) {
        final updatedMissions = state.summary!.missions.map((mission) {
          if (mission.id == missionId) {
            return updatedMission;
          }
          return mission;
        }).toList();

        // Recalculate summary stats
        final completedCount = updatedMissions.where((m) => m.isCompleted).length;
        final totalXpToday = updatedMissions
            .where((m) => m.isCompleted)
            .fold<int>(0, (sum, m) => sum + m.xpAwarded);

        final updatedSummary = DailyMissionsSummary(
          missions: updatedMissions,
          totalXpToday: totalXpToday,
          completedCount: completedCount,
          totalCount: updatedMissions.length,
        );

        state = state.copyWith(summary: updatedSummary);
      }

      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Refresh missions
  Future<void> refresh() async {
    await loadMissions();
  }
}

/// Provider to get missions list
@riverpod
List<DailyMission> dailyMissionsList(DailyMissionsListRef ref) {
  final state = ref.watch(dailyMissionsNotifierProvider);
  return state.summary?.missions ?? [];
}

/// Provider to get completed missions count
@riverpod
int completedMissionsCount(CompletedMissionsCountRef ref) {
  final state = ref.watch(dailyMissionsNotifierProvider);
  return state.summary?.completedCount ?? 0;
}

/// Provider to get total XP earned today
@riverpod
int totalXpToday(TotalXpTodayRef ref) {
  final state = ref.watch(dailyMissionsNotifierProvider);
  return state.summary?.totalXpToday ?? 0;
}

