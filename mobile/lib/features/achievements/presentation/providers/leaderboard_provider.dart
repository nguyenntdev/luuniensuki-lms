import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
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

      // API returns { scope, entries, user_rank, user_entry, total_users }
      // We need to extract the 'entries' field
      List<dynamic> data;
      if (response.data is Map<String, dynamic>) {
        // New API format with nested entries
        final responseMap = response.data as Map<String, dynamic>;
        data = (responseMap['entries'] as List<dynamic>?) ?? [];
      } else if (response.data is List<dynamic>) {
        // Legacy format (direct list)
        data = response.data as List<dynamic>;
      } else {
        data = [];
      }

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

