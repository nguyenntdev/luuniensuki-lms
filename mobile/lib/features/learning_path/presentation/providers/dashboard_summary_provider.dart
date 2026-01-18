import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../data/models/dashboard_summary.dart';

final dashboardSummaryProvider = FutureProvider<DashboardSummary>((ref) async {
  final apiClient = ref.read(apiClientProvider);

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.dashboardSummary,
      parser: (json) => json as Map<String, dynamic>,
    );

    return DashboardSummary.fromJson(response);
  } catch (e) {
    // On error, return empty dashboard summary with defaults
    return const DashboardSummary(
      collectionStats: DashboardCollectionStats(
        total: 0,
        discovered: 0,
        learned: 0,
        mastered: 0,
      ),
      streak: DashboardStreak(
        currentStreak: 0,
        longestStreak: 0,
        streakFreezes: 0,
      ),
      pathMotifs: [],
    );
  }
});
