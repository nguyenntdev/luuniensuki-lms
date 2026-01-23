# Lesson Unlock Display Issue - Fix Summary

## Problem Description

After discovering a motif in the 3D viewer, the lesson detail page was showing the "locked" status instead of the "unlocked/discovered" status. This prevented users from accessing the lesson content immediately after discovery.

## Root Cause Analysis

The issue was caused by **stale cache data** in the following flow:

1. User discovers a motif in the URN viewer (status changes from `hidden` to `discovered`)
2. Discovery animation completes and invalidates `motifDetailProvider`
3. User navigates to the motif detail screen
4. The screen watches `motifDetailProvider(motifId)` 
5. **Problem**: The provider was serving cached data from Hive storage before the fresh API data was fetched
6. Result: UI showed old status (`hidden`) instead of new status (`discovered`)

## Technical Details

### Cache Flow Issue

The `motifDetailProvider` in `/mobile/lib/features/lesson/presentation/providers/motif_detail_provider.dart`:

- Uses Hive storage for offline-first caching
- When invalidated, it triggers a refetch
- **BUT**: The cached data in Hive was not being cleared during invalidation
- So when the provider was immediately re-accessed after invalidation, it could serve stale cache data

### Timing Issue

The original code had a 150ms delay between invalidation and navigation:

```dart
ref.invalidate(lesson_provider.motifDetailProvider(discoveredMotif.id));
await Future.delayed(const Duration(milliseconds: 150));
_openMotifDetail(discoveredMotif);
```

This delay was insufficient to:
1. Clear the cache
2. Complete a new API fetch
3. Update the cached data

## Solution Implemented

### 1. Clear Cache Before Navigation

**File**: `/mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Changes**:
- Added explicit cache deletion before navigating to motif detail
- Increased delay from 150ms to 300ms to allow cache operations to complete
- Added import for `hiveStorageProvider`

```dart
void _onDiscoveryAnimationComplete() async {
  final discoveredMotif = _pendingDiscovery?.motif;
  
  // ... state updates ...
  
  if (discoveredMotif != null) {
    // Clear cached motif data
    final hiveStorage = ref.read(hiveStorageProvider);
    await hiveStorage.motifsBox.delete(discoveredMotif.id);
    
    // Invalidate the provider
    ref.invalidate(lesson_provider.motifDetailProvider(discoveredMotif.id));
  }
  
  // Wait longer for cache clearing and provider refresh
  await Future.delayed(const Duration(milliseconds: 300));
  
  // Then navigate
  if (discoveredMotif != null && mounted) {
    _openMotifDetail(discoveredMotif);
  }
}
```

### 2. Force Refresh on Screen Init

**File**: `/mobile/lib/features/lesson/presentation/screens/motif_detail_screen.dart`

**Changes**:
- Added `WidgetsBindingObserver` mixin to detect app lifecycle changes
- Added post-frame callback to force refresh when screen opens
- Added lifecycle observer to refresh when app resumes

```dart
class _MotifDetailScreenState extends ConsumerState<MotifDetailScreen>
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addObserver(this);
    
    // Force refresh when screen is first opened
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.invalidate(motifDetailProvider(widget.motifId));
    });
  }
  
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    // Refresh data when app resumes
    if (state == AppLifecycleState.resumed) {
      ref.invalidate(motifDetailProvider(widget.motifId));
    }
  }
  
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _tabController.dispose();
    super.dispose();
  }
}
```

## Benefits

1. **Immediate Cache Clearing**: Explicitly deletes cached motif data before navigation
2. **Guaranteed Fresh Data**: Post-frame callback ensures provider refetch when screen opens
3. **Better User Experience**: Users see the correct status immediately after discovery
4. **App Resume Handling**: Data refreshes when app comes back from background
5. **Longer Delay**: 300ms gives enough time for cache operations to complete

## Testing Checklist

- [ ] Discover a new motif in the 3D viewer
- [ ] Verify discovery animation plays
- [ ] Navigate to motif detail page
- [ ] Verify lesson tab shows "discovered" status (not "hidden")
- [ ] Verify "Complete Lesson" button is visible
- [ ] Complete the lesson
- [ ] Verify status updates to "learned"
- [ ] Background the app and return
- [ ] Verify data refreshes correctly

## Related Files Modified

1. `/mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`
   - Added Hive storage import
   - Modified `_onDiscoveryAnimationComplete()` method

2. `/mobile/lib/features/lesson/presentation/screens/motif_detail_screen.dart`
   - Added `WidgetsBindingObserver` mixin
   - Added `initState()` with post-frame refresh
   - Added `didChangeAppLifecycleState()` for app resume
   - Updated `dispose()` to remove observer

## Future Improvements

Consider these enhancements for better cache management:

1. Add cache versioning to detect stale data
2. Implement a cache invalidation strategy based on data freshness
3. Add explicit cache refresh UI control
4. Consider using a more sophisticated caching library like `dio_cache_interceptor`

