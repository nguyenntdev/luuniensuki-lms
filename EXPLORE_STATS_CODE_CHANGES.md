# Code Changes - Quick Reference

## Summary
Fixed Explore screen statistics by fetching from `/api/v1/dashboard/summary` instead of relying on `/api/v1/urns`.

---

## File 1: api_constants.dart

### Added Dashboard Endpoint
```dart
// Dashboard Endpoints
static const String dashboardSummary = '$apiPath/dashboard/summary';
```

**Location**: After line 47 (User Endpoints section)

---

## File 2: explore_provider.dart

### Change 1: Added CollectionStats Class

```dart
/// Collection statistics from dashboard summary
class CollectionStats {
  final int total;
  final int discovered;
  final int learned;
  final int mastered;

  const CollectionStats({
    required this.total,
    required this.discovered,
    required this.learned,
    required this.mastered,
  });

  factory CollectionStats.fromJson(Map<String, dynamic> json) {
    return CollectionStats(
      total: json['total'] as int? ?? 0,
      discovered: json['discovered'] as int? ?? 0,
      learned: json['learned'] as int? ?? 0,
      mastered: json['mastered'] as int? ?? 0,
    );
  }
}
```

**Location**: Lines 46-68 (after ExploreState class)

---

### Change 2: Updated ExploreState

**Added field**:
```dart
final CollectionStats? collectionStats;
```

**Updated constructor**:
```dart
const ExploreState({
  this.urns = const [],
  this.isLoading = false,
  this.errorMessage,
  this.isRefreshing = false,
  this.collectionStats,  // NEW
});
```

**Updated copyWith**:
```dart
ExploreState copyWith({
  List<Urn>? urns,
  bool? isLoading,
  String? errorMessage,
  bool? isRefreshing,
  CollectionStats? collectionStats,  // NEW
}) {
  return ExploreState(
    urns: urns ?? this.urns,
    isLoading: isLoading ?? this.isLoading,
    errorMessage: errorMessage,
    isRefreshing: isRefreshing ?? this.isRefreshing,
    collectionStats: collectionStats ?? this.collectionStats,  // NEW
  );
}
```

---

### Change 3: Enhanced loadUrns() Method

**Added after loading urns** (around line 111):
```dart
// Fetch collection stats from dashboard summary
debugPrint('[EXPLORE] Fetching collection stats from dashboard summary...');
CollectionStats? collectionStats;
try {
  final dashboardResponse = await _apiClient.get<Map<String, dynamic>>(
    ApiConstants.dashboardSummary,
  );

  if (dashboardResponse.containsKey('collection_stats')) {
    collectionStats = CollectionStats.fromJson(
      dashboardResponse['collection_stats'] as Map<String, dynamic>,
    );
    debugPrint('[EXPLORE] Collection stats loaded: discovered=${collectionStats.discovered}, learned=${collectionStats.learned}, mastered=${collectionStats.mastered}');
  }
} catch (e) {
  debugPrint('[EXPLORE] Failed to load collection stats: $e');
  // Continue even if stats fail - we'll use defaults
}
```

**Updated state assignment**:
```dart
state = state.copyWith(
  urns: urns,
  isLoading: false,
  isRefreshing: false,
  collectionStats: collectionStats,  // NEW
);
```

---

### Change 4: Enhanced refreshUrns() Method

**Added similar stats fetching** (around line 167):
```dart
// Also refresh collection stats
CollectionStats? collectionStats;
try {
  final dashboardResponse = await _apiClient.get<Map<String, dynamic>>(
    ApiConstants.dashboardSummary,
  );

  if (dashboardResponse.containsKey('collection_stats')) {
    collectionStats = CollectionStats.fromJson(
      dashboardResponse['collection_stats'] as Map<String, dynamic>,
    );
  }
} catch (e) {
  debugPrint('[EXPLORE] Failed to refresh collection stats: $e');
  // Keep existing stats if refresh fails
  collectionStats = state.collectionStats;
}
```

---

### Change 5: Updated exploreProgress Provider

**New priority logic**:
```dart
@riverpod
ExploreProgress exploreProgress(ExploreProgressRef ref) {
  final state = ref.watch(exploreNotifierProvider);

  // Use collection stats from dashboard summary if available
  if (state.collectionStats != null) {
    return ExploreProgress(
      totalMotifs: state.collectionStats!.total,
      discoveredMotifs: state.collectionStats!.discovered,
      learnedMotifs: state.collectionStats!.learned,
      masteredMotifs: state.collectionStats!.mastered,
    );
  }

  // Fallback to calculating from urns (will show 0s if urns don't have stats)
  if (state.urns.isEmpty) {
    return const ExploreProgress(
      totalMotifs: 0,
      discoveredMotifs: 0,
      learnedMotifs: 0,
      masteredMotifs: 0,
    );
  }

  // ... rest of fallback logic
}
```

---

## Expected Debug Output

When working correctly, you should see:
```
[EXPLORE] Loading urns from API...
[EXPLORE] Got 9 urns
[EXPLORE] Fetching collection stats from dashboard summary...
[EXPLORE] Collection stats loaded: discovered=5, learned=2, mastered=1
[EXPLORE] Urns loaded successfully
```

---

## Testing Commands

After making changes, the code should work immediately without rebuilding generated files since we:
- Used plain Dart classes (not Freezed)
- Only modified existing provider (no new providers requiring generation)
- Maintained backward compatibility

Simply hot reload the app to test!

