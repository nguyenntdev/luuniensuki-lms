import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../domain/entities/quest.dart';

/// Quest filter enum
enum QuestFilter { all, inProgress, completed, locked }

/// Quests state holding current items and selected filter
class QuestsState {
  final List<Quest> quests;
  final QuestFilter filter;
  final bool isLoading;
  final String? errorMessage;

  const QuestsState({
    this.quests = const [],
    this.filter = QuestFilter.all,
    this.isLoading = false,
    this.errorMessage,
  });

  List<Quest> get filteredQuests {
    switch (filter) {
      case QuestFilter.all:
        return quests;
      case QuestFilter.inProgress:
        return quests.where((q) => q.status == QuestStatus.inProgress).toList();
      case QuestFilter.completed:
        return quests.where((q) => q.status == QuestStatus.completed).toList();
      case QuestFilter.locked:
        return quests.where((q) => q.isLocked || q.status == QuestStatus.locked).toList();
    }
  }

  int get completedCount =>
      quests.where((q) => q.status == QuestStatus.completed).length;

  int get inProgressCount =>
      quests.where((q) => q.status == QuestStatus.inProgress).length;

  QuestsState copyWith({
    List<Quest>? quests,
    QuestFilter? filter,
    bool? isLoading,
    String? errorMessage,
  }) {
    return QuestsState(
      quests: quests ?? this.quests,
      filter: filter ?? this.filter,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
    );
  }
}

/// Notifier managing quest list and lifecycle
class QuestsNotifier extends StateNotifier<QuestsState> {
  final HiveStorage _storage;
  final ApiClient? _apiClient;

  QuestsNotifier(this._storage, [this._apiClient])
      : super(const QuestsState(quests: kCanonicalQuests)) {
    loadQuests();
  }

  Future<void> loadQuests() async {
    state = state.copyWith(isLoading: true, errorMessage: null);

    try {
      // 1. Try remote API first for server-verified live progression
      if (_apiClient != null) {
        try {
          final listData = await _apiClient.get<List<dynamic>>(
            ApiConstants.quests,
            parser: (json) => json as List<dynamic>,
          );
          final list = listData
              .map((item) =>
                  Quest.fromJson(Map<String, dynamic>.from(item as Map)))
              .toList();
          if (list.isNotEmpty) {
            await _storage.cacheQuests(list.map((q) => q.toJson()).toList());
            state = state.copyWith(quests: list, isLoading: false);
            return;
          }
        } catch (_) {
          // Graceful fallback to cache
        }
      }

      // 2. Try local cache
      final cached = _storage.getCachedQuests();
      if (cached != null && cached.isNotEmpty) {
        final cachedQuests = cached.map((e) => Quest.fromJson(e)).toList();
        state = state.copyWith(quests: cachedQuests, isLoading: false);
        return;
      }

      // 3. Fallback to canonical heritage quests
      state = state.copyWith(quests: kCanonicalQuests, isLoading: false);
    } catch (e) {
      state = state.copyWith(
        quests: kCanonicalQuests,
        isLoading: false,
        errorMessage: e.toString(),
      );
    }
  }

  void setFilter(QuestFilter filter) {
    state = state.copyWith(filter: filter);
  }

  Quest? getQuest(String idOrSlug) {
    for (final q in state.quests) {
      if (q.id == idOrSlug || q.slug == idOrSlug) {
        return q;
      }
    }
    // Check canonical list as fallback
    for (final q in kCanonicalQuests) {
      if (q.id == idOrSlug || q.slug == idOrSlug) {
        return q;
      }
    }
    return null;
  }

  Future<void> startQuest(String idOrSlug) async {
    final quest = getQuest(idOrSlug);
    if (quest == null || quest.isLocked) return;

    if (_apiClient != null) {
      try {
        await _apiClient.post(
          ApiConstants.questStart(quest.slug),
          parser: (json) => json,
        );
        await loadQuests();
        return;
      } catch (_) {}
    }

    final updated = state.quests.map((q) {
      if (q.id == quest.id) {
        return q.copyWith(status: QuestStatus.inProgress);
      }
      return q;
    }).toList();

    state = state.copyWith(quests: updated);
    await _storage.cacheQuests(updated.map((q) => q.toJson()).toList());
  }

  /// Claim rewards with strict server-side verification
  /// Stale clients cannot claim rewards without 100% server-verified completion
  Future<Map<String, dynamic>?> claimReward(String idOrSlug) async {
    final quest = getQuest(idOrSlug);
    if (quest == null) return null;

    if (_apiClient != null) {
      try {
        final result = await _apiClient.post<Map<String, dynamic>>(
          ApiConstants.questClaim(quest.slug),
          parser: (json) => json as Map<String, dynamic>,
        );

        // Server verified and claimed! Refresh quests from server
        await loadQuests();
        return result;
      } catch (e) {
        // Re-throw server error (e.g. 400 incomplete or locked) for UI notification
        rethrow;
      }
    }

    return null;
  }

  /// Fetch full quest detail including steps and objectives
  Future<Quest?> fetchQuestDetail(String idOrSlug) async {
    final quest = getQuest(idOrSlug);
    final slug = quest?.slug ?? idOrSlug;

    if (_apiClient != null) {
      try {
        final data = await _apiClient.get<Map<String, dynamic>>(
          ApiConstants.questDetail(slug),
          parser: (json) => json as Map<String, dynamic>,
        );
        final detailedQuest = Quest.fromJson(data);
        final updated = state.quests.map((q) {
          if (q.id == detailedQuest.id || q.slug == detailedQuest.slug) {
            return detailedQuest;
          }
          return q;
        }).toList();
        state = state.copyWith(quests: updated);
        return detailedQuest;
      } catch (_) {}
    }
    return quest;
  }
}

/// Global provider for quests
final questsNotifierProvider =
    StateNotifierProvider<QuestsNotifier, QuestsState>((ref) {
  final storage = ref.watch(hiveStorageProvider);
  final apiClient = ref.watch(apiClientProvider);
  return QuestsNotifier(storage, apiClient);
});
