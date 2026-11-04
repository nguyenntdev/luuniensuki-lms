import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../data/models/quest_model.dart';

/// State of the quests list
class QuestsState {
  final bool isLoading;
  final List<QuestModel> quests;
  final String? error;
  final bool isOffline;

  const QuestsState({
    this.isLoading = false,
    this.quests = const [],
    this.error,
    this.isOffline = false,
  });

  QuestsState copyWith({
    bool? isLoading,
    List<QuestModel>? quests,
    String? error,
    bool? isOffline,
  }) {
    return QuestsState(
      isLoading: isLoading ?? this.isLoading,
      quests: quests ?? this.quests,
      error: error,
      isOffline: isOffline ?? this.isOffline,
    );
  }

  List<QuestModel> get activeQuests =>
      quests.where((q) => !q.isCompleted && !q.isLocked).toList();

  List<QuestModel> get completedQuests =>
      quests.where((q) => q.isCompleted).toList();

  List<QuestModel> get lockedQuests =>
      quests.where((q) => q.isLocked).toList();

  QuestModel? get currentActiveQuest {
    final active = activeQuests;
    if (active.isEmpty) return null;
    return active.firstWhere(
      (q) => q.isInProgress,
      orElse: () => active.first,
    );
  }
}

/// Provider for Quests StateNotifier
final questsNotifierProvider =
    StateNotifierProvider<QuestsNotifier, QuestsState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final storage = ref.watch(hiveStorageProvider);
  return QuestsNotifier(apiClient: apiClient, storage: storage);
});

/// Notifier managing quests lifecycle, progression, and reward claiming
class QuestsNotifier extends StateNotifier<QuestsState> {
  final ApiClient _apiClient;
  final HiveStorage _storage;

  QuestsNotifier({
    required ApiClient apiClient,
    required HiveStorage storage,
  })  : _apiClient = apiClient,
        _storage = storage,
        super(const QuestsState(isLoading: true)) {
    loadQuests();
  }

  /// Load all quests from API with offline fallback
  Future<void> loadQuests() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final List<dynamic> data = await _apiClient.get<List<dynamic>>(
        ApiConstants.quests,
        parser: (json) => json as List<dynamic>,
      );

      final quests = data
          .map((item) => QuestModel.fromJson(item as Map<String, dynamic>))
          .toList();

      // Cache raw json list for offline resilience
      await _storage.cacheQuests(
        data.map((item) => Map<String, dynamic>.from(item as Map)).toList(),
      );

      state = state.copyWith(
        isLoading: false,
        quests: quests,
        isOffline: false,
      );
    } catch (e) {
      // Offline fallback: load from hive cache if available
      final cached = _storage.getCachedQuests();
      if (cached != null && cached.isNotEmpty) {
        final cachedQuests = cached
            .map((item) => QuestModel.fromJson(item))
            .toList();
        state = state.copyWith(
          isLoading: false,
          quests: cachedQuests,
          isOffline: true,
          error: 'Đang hiển thị dữ liệu lưu tạm. Vui lòng kết nối mạng để cập nhật.',
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Không thể tải danh sách nhiệm vụ: ${e.toString()}',
        );
      }
    }
  }

  /// Start a quest with server verification
  Future<bool> startQuest(String slug) async {
    try {
      await _apiClient.post<Map<String, dynamic>>(
        ApiConstants.questStart(slug),
        parser: (json) => json as Map<String, dynamic>,
      );
      await loadQuests();
      return true;
    } catch (e) {
      state = state.copyWith(error: 'Không thể bắt đầu nhiệm vụ: ${e.toString()}');
      return false;
    }
  }

  /// Claim rewards with strict server verification
  /// Rejects stale clients if server progress is incomplete (< 100%)
  Future<QuestClaimResponseModel?> claimReward(String slug) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        ApiConstants.questClaim(slug),
        parser: (json) => json as Map<String, dynamic>,
      );

      final claimResult = QuestClaimResponseModel.fromJson(response);
      await loadQuests();
      return claimResult;
    } catch (e) {
      rethrow;
    }
  }

  /// Fetch full quest detail including steps and objectives
  Future<QuestModel> getQuestDetail(String slug) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      ApiConstants.questDetail(slug),
      parser: (json) => json as Map<String, dynamic>,
    );
    return QuestModel.fromJson(response);
  }
}
