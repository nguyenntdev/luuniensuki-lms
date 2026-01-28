import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../domain/entities/daily_mission.dart';

part 'daily_missions_repository.g.dart';

/// Repository for daily missions
class DailyMissionsRepository {
  final ApiClient _apiClient;

  DailyMissionsRepository(this._apiClient);

  /// Get today's missions
  Future<DailyMissionsSummary> getTodayMissions() async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>(
        '/api/v1/daily-missions',
      );

      return _parseDailyMissionsSummary(response);
    } on DioException catch (e) {
      throw Exception('Failed to fetch daily missions: ${e.message}');
    }
  }

  /// Update mission progress
  Future<DailyMission> updateMissionProgress({
    required String missionId,
    int increment = 1,
  }) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/api/v1/daily-missions/$missionId/progress',
        data: {'increment': increment},
      );

      // The response contains "mission" object
      final missionData = response['mission'] as Map<String, dynamic>;
      return _parseDailyMission(missionData);
    } on DioException catch (e) {
      throw Exception('Failed to update mission progress: ${e.message}');
    }
  }

  /// Parse DailyMissionsSummary from API response
  DailyMissionsSummary _parseDailyMissionsSummary(Map<String, dynamic> json) {
    final missionsJson = json['missions'] as List<dynamic>? ?? [];
    final missions = missionsJson
        .map((m) => _parseDailyMission(m as Map<String, dynamic>))
        .toList();

    return DailyMissionsSummary(
      missions: missions,
      totalXpToday: (json['total_xp_today'] as num?)?.toInt() ?? 0,
      completedCount: (json['completed_count'] as num?)?.toInt() ?? 0,
      totalCount: (json['total_count'] as num?)?.toInt() ?? 0,
    );
  }

  /// Parse DailyMission from API response
  DailyMission _parseDailyMission(Map<String, dynamic> json) {
    // The API returns nested structure: { mission: {...}, current_count, is_completed, ... }
    final missionData = json['mission'] as Map<String, dynamic>? ?? json;

    return DailyMission(
      id: json['id']?.toString() ?? '',
      slug: missionData['slug']?.toString() ?? '',
      name: missionData['name']?.toString() ?? '',
      description: missionData['description']?.toString() ?? '',
      missionType: MissionType.fromString(
        missionData['mission_type']?.toString() ?? 'lesson',
      ),
      targetCount: (missionData['target_count'] as num?)?.toInt() ?? 1,
      xpReward: (missionData['xp_reward'] as num?)?.toInt() ?? 0,
      isActive: missionData['is_active'] as bool? ?? true,
      currentCount: (json['current_count'] as num?)?.toInt() ?? 0,
      isCompleted: json['is_completed'] as bool? ?? false,
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'].toString())
          : null,
      xpAwarded: (json['xp_awarded'] as num?)?.toInt() ?? 0,
      progressPercentage: (json['progress_percentage'] as num?)?.toInt() ?? 0,
    );
  }
}

/// Provider for DailyMissionsRepository
@riverpod
DailyMissionsRepository dailyMissionsRepository(
  DailyMissionsRepositoryRef ref,
) {
  final apiClient = ref.watch(apiClientProvider);
  return DailyMissionsRepository(apiClient);
}

