import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../data/models/badge_dto.dart';

/// Provider for badge data
final badgeNotifierProvider =
    StateNotifierProvider<BadgeNotifier, AsyncValue<List<BadgeDto>>>(
  (ref) => BadgeNotifier(ref),
);

/// Notifier for managing badge data
/// Fetches all badges and user's earned badges, with Hive caching
class BadgeNotifier extends StateNotifier<AsyncValue<List<BadgeDto>>> {
  final Ref _ref;
  static const Duration _cacheMaxAge = Duration(hours: 1);

  BadgeNotifier(this._ref) : super(const AsyncValue.loading());

  /// Load all badges with user's earned status
  /// Combines data from /api/v1/badges and /api/v1/users/me/badges
  Future<void> loadBadges({bool forceRefresh = false}) async {
    debugPrint('[BadgeProvider] Starting loadBadges (forceRefresh: $forceRefresh)');

    // Check cache first if not forcing refresh
    if (!forceRefresh) {
      final cachedBadges = _loadFromCache();
      if (cachedBadges != null) {
        debugPrint('[BadgeProvider] Loaded ${cachedBadges.length} badges from cache');
        state = AsyncValue.data(cachedBadges);
        return;
      }
    }

    state = const AsyncValue.loading();
    try {
      final dio = _ref.read(dioProvider);

      // Fetch all badges first (requires auth)
      debugPrint('[BadgeProvider] Fetching all badges from ${ApiConstants.badges}');
      final allBadgesResponse = await dio.get(ApiConstants.badges);
      final allBadgesData = allBadgesResponse.data as List<dynamic>;
      debugPrint('[BadgeProvider] Received ${allBadgesData.length} badges from API');

      // Try to fetch user badges (requires auth) - handle failure gracefully
      List<dynamic> userBadgesData = [];
      try {
        debugPrint('[BadgeProvider] Fetching user badges from ${ApiConstants.userBadges}');
        final userBadgesResponse = await dio.get(ApiConstants.userBadges);
        userBadgesData = userBadgesResponse.data as List<dynamic>? ?? [];
        debugPrint('[BadgeProvider] Received ${userBadgesData.length} user badges from API');
      } catch (e) {
        // User not logged in or endpoint failed - continue without earned badges
        debugPrint('[BadgeProvider] Failed to fetch user badges: $e');
      }

      // Create a map of user badges by badge slug for quick lookup
      // API response structure: { badge: { slug, name, ... }, earned_at: ... }
      // Note: Backend currently doesn't return 'id' field, so we use 'slug' as identifier
      final Map<String, String> earnedBadgeMap = {};
      for (final badge in userBadgesData) {
        if (badge == null) continue;

        final badgeMap = badge as Map<String, dynamic>;

        // Handle nested badge structure from API
        // API returns: { badge: {...}, earned_at: "..." }
        final badgeData = badgeMap['badge'];
        final earnedAt = badgeMap['earned_at'];

        if (badgeData != null && earnedAt != null) {
          final badgeSlug =
              badgeData is Map<String, dynamic> ? badgeData['slug'] : null;

          if (badgeSlug != null && earnedAt is String) {
            earnedBadgeMap[badgeSlug.toString()] = earnedAt;
          }
        }
      }
      debugPrint('[BadgeProvider] Mapped ${earnedBadgeMap.length} earned badges');

      // Merge the data: add earnedAt to badges that user has earned
      final badges = allBadgesData.map((json) {
        final badgeJson = json as Map<String, dynamic>;

        // Use slug as identifier since backend doesn't return id
        final badgeSlug = badgeJson['slug']?.toString();

        // Add earnedAt if user has earned this badge
        if (badgeSlug != null && earnedBadgeMap.containsKey(badgeSlug)) {
          badgeJson['earned_at'] = earnedBadgeMap[badgeSlug];
        }

        // Generate id from slug if not present (backend issue workaround)
        if (badgeJson['id'] == null) {
          badgeJson['id'] = badgeSlug ?? 'unknown';
        }

        return BadgeDto.fromJson(badgeJson);
      }).toList();

      debugPrint('[BadgeProvider] Successfully loaded ${badges.length} badges');

      // Cache the result
      await _saveToCache(badges);

      state = AsyncValue.data(badges);
    } catch (e, st) {
      debugPrint('[BadgeProvider] Error loading badges: $e');
      debugPrint('[BadgeProvider] Stack trace: $st');
      state = AsyncValue.error(e, st);
    }
  }

  /// Refresh badge data
  Future<void> refresh() => loadBadges(forceRefresh: true);

  /// Load badges from Hive cache
  List<BadgeDto>? _loadFromCache() {
    final storage = _ref.read(hiveStorageProvider);

    // Check if cache is valid
    if (!storage.isBadgesCacheValid(_cacheMaxAge)) {
      debugPrint('[BadgeProvider] Cache is not valid or expired');
      return null;
    }

    final cachedData = storage.getCachedBadges();
    if (cachedData == null) {
      debugPrint('[BadgeProvider] No cached data found');
      return null;
    }

    try {
      debugPrint('[BadgeProvider] Parsing ${cachedData.length} badges from cache');
      final badges = cachedData.map((json) => BadgeDto.fromJson(json)).toList();
      debugPrint('[BadgeProvider] Successfully parsed ${badges.length} badges from cache');
      return badges;
    } catch (e, st) {
      debugPrint('[BadgeProvider] Error parsing cached badges: $e');
      debugPrint('[BadgeProvider] Stack trace: $st');
      debugPrint('[BadgeProvider] First item data: ${cachedData.isNotEmpty ? cachedData.first : 'empty'}');
      return null;
    }
  }

  /// Save badges to Hive cache
  Future<void> _saveToCache(List<BadgeDto> badges) async {
    final storage = _ref.read(hiveStorageProvider);
    final jsonList = badges.map((badge) => badge.toJson()).toList();
    await storage.cacheBadges(jsonList);
  }
}

/// Provider for earned badges count
final earnedBadgesCountProvider = Provider<int>((ref) {
  final badgesAsync = ref.watch(badgeNotifierProvider);
  return badgesAsync.maybeWhen(
    data: (badges) => badges.where((badge) => badge.earnedAt != null).length,
    orElse: () => 0,
  );
});

/// Provider for earned badges only
final earnedBadgesProvider = Provider<List<BadgeDto>>((ref) {
  final badgesAsync = ref.watch(badgeNotifierProvider);
  return badgesAsync.maybeWhen(
    data: (badges) => badges.where((badge) => badge.earnedAt != null).toList(),
    orElse: () => [],
  );
});

/// Provider for unearned badges only
final unearnedBadgesProvider = Provider<List<BadgeDto>>((ref) {
  final badgesAsync = ref.watch(badgeNotifierProvider);
  return badgesAsync.maybeWhen(
    data: (badges) => badges.where((badge) => badge.earnedAt == null).toList(),
    orElse: () => [],
  );
});
