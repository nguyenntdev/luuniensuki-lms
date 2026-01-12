import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_provider.dart';
import '../../data/models/leaderboard_dto.dart';

/// Provider for leaderboard data
final leaderboardNotifierProvider =
    StateNotifierProvider<LeaderboardNotifier, AsyncValue<List<LeaderboardEntryDto>>>(
  (ref) => LeaderboardNotifier(ref),
);

/// Notifier for managing leaderboard data
/// Fetches and caches the leaderboard from the API
class LeaderboardNotifier extends StateNotifier<AsyncValue<List<LeaderboardEntryDto>>> {
  final Ref _ref;

  LeaderboardNotifier(this._ref) : super(const AsyncValue.loading());

  /// Load leaderboard data from API
  ///
  /// [limit] - Maximum number of entries to fetch (default: 50)
  Future<void> loadLeaderboard({int limit = 50}) async {
    state = const AsyncValue.loading();
    try {
      final dio = _ref.read(dioProvider);
      final response = await dio.get(
        ApiConstants.leaderboard,
        queryParameters: {'limit': limit},
      );

      final List<dynamic> data = response.data as List<dynamic>;
      final entries = data
          .map((json) => LeaderboardEntryDto.fromJson(json as Map<String, dynamic>))
          .toList();

      state = AsyncValue.data(entries);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  /// Refresh the leaderboard data
  Future<void> refresh() => loadLeaderboard();
}

