# Explore Screen Blank White Screen - Fix Summary

## Problem
The Explore Screen was showing a blank white screen when users navigated to it.

## Root Causes Identified

1. **Auto-dispose provider issue**: The `ExploreNotifier` used `@riverpod` which generates an `AutoDisposeNotifier`. This means the provider would be disposed when not being listened to, losing its state.

2. **Race condition with auth**: The `loadUrns()` method was called via `Future.microtask()` in the build method, racing with auth initialization. Since both auth and explore load used microtasks, there was no guarantee auth would complete first.

3. **API requires authentication**: The `/api/v1/urns` endpoint requires authentication. If called before auth is ready, it returns a 401 error.

4. **Missing empty state**: When the urns list was empty (either due to error or genuinely empty data), the screen just showed an empty grid with no feedback to the user.

## Fixes Implemented

### 1. Changed Provider to Non-Auto-Dispose (explore_provider.dart)

**Before:**
```dart
@riverpod
class ExploreNotifier extends _$ExploreNotifier {
  @override
  ExploreState build() {
    Future.microtask(() => loadUrns());
    return const ExploreState(isLoading: true);
  }
```

**After:**
```dart
@Riverpod(keepAlive: true)
class ExploreNotifier extends _$ExploreNotifier {
  @override
  ExploreState build() {
    // Don't load immediately - wait for auth to be ready
    // Load will be triggered from UI when auth is ready
    return const ExploreState(isLoading: true);
  }
```

**Changes:**
- Added `keepAlive: true` to prevent auto-disposal
- Removed automatic loading in build method
- State will persist across navigation

### 2. Added Manual Initialization (explore_provider.dart)

Added new method to initialize data loading:

```dart
/// Initialize the provider - should be called when auth is ready
void initialize() {
  if (!state.hasData && !state.isLoading) {
    loadUrns();
  }
}
```

This allows the UI to trigger loading after auth is confirmed ready.

### 3. Added Auth-Aware Loading (explore_screen.dart)

**Added state tracking:**
```dart
bool _hasInitialized = false;
```

**Updated build method to wait for auth:**
```dart
// Trigger data load when auth is ready
if (!_hasInitialized && authState.isAuthenticated) {
  _hasInitialized = true;
  // Use addPostFrameCallback to avoid calling during build
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ref.read(exploreNotifierProvider.notifier).loadUrns();
  });
}
```

**Benefits:**
- Data loading only happens after auth is confirmed
- No race conditions
- Uses proper Flutter lifecycle (postFrameCallback)

### 4. Added Empty State UI (explore_screen.dart)

**Added check in `_buildContent()`:**
```dart
// Check for empty state
if (!state.isLoading && !state.hasError && state.urns.isEmpty) {
  return _buildEmptyState(ref);
}
```

**Added new widget:**
```dart
Widget _buildEmptyState(WidgetRef ref) {
  return Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_outlined, size: 64, ...),
          Text('Không có dữ liệu', ...),
          Text('Vui lòng thử lại sau.', ...),
          ElevatedButton.icon(
            onPressed: () => ref.read(exploreNotifierProvider.notifier).loadUrns(),
            icon: const Icon(Icons.refresh),
            label: const Text('Thử lại'),
          ),
        ],
      ),
    ),
  );
}
```

**Benefits:**
- Clear feedback when no data available
- Retry button for user action
- Consistent with error state UI

### 5. Updated Generated Code (explore_provider.g.dart)

**Changed from:**
```dart
final exploreNotifierProvider =
    AutoDisposeNotifierProvider<ExploreNotifier, ExploreState>.internal(...)

typedef _$ExploreNotifier = AutoDisposeNotifier<ExploreState>;
```

**To:**
```dart
final exploreNotifierProvider =
    NotifierProvider<ExploreNotifier, ExploreState>.internal(...)

typedef _$ExploreNotifier = Notifier<ExploreState>;
```

## Expected Behavior After Fix

1. **App Launch:**
   - Explore screen shows loading state
   - Auth initializes in background
   - Once auth ready, explore data loads
   - Screen shows 9 urns with smooth animation

2. **Auth Not Ready:**
   - Loading state remains until auth completes
   - No premature API calls

3. **API Error:**
   - Error state shown with message
   - Retry button available

4. **Empty Data:**
   - Empty state shown with message
   - Retry button available

5. **Navigation:**
   - State persists when navigating away and back
   - No re-loading on every visit (data cached)

## Testing Checklist

- [ ] App launches and explore screen loads data successfully
- [ ] 9 urns are displayed in a grid
- [ ] Pull-to-refresh works
- [ ] Navigation to urn detail works
- [ ] Progress summary shows correct counts
- [ ] Error handling works (can test by turning off wifi)
- [ ] Empty state shows if API returns no data
- [ ] State persists when navigating away and back

## Notes for Regenerating Code

The generated file (`explore_provider.g.dart`) was manually updated. If you need to regenerate it:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

Then manually update line 197 and 207 as shown in section 5 above, OR run the script:
```bash
cd mobile
chmod +x run_build_runner.sh
./run_build_runner.sh
```

## Files Modified

1. `mobile/lib/features/explore/presentation/providers/explore_provider.dart`
2. `mobile/lib/features/explore/presentation/screens/explore_screen.dart`
3. `mobile/lib/features/explore/presentation/providers/explore_provider.g.dart`
4. `mobile/run_build_runner.sh` (new file)

