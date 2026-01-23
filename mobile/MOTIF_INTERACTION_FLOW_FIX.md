# 3D Model Motif Interaction Flow Fix

## Problem Summary

The mobile app had several issues with the 3D model motif interaction flow:

1. ❌ **Motif not marked as explored** after touching in 3D model
2. ❌ **Progress numbers don't update** in 3D viewer after unlock
3. ✅ **Learned status** - Already working (via manual "Complete Lesson" button)
4. ✅ **Quiz prompt** - Already working (via completion dialog)

## Root Causes

1. **Discovery animation completion**: Provider invalidation happened AFTER navigation, and didn't wait for refresh
2. **Return from motif detail**: No refresh when user comes back from lesson/quiz screens
3. **Lesson completion**: Didn't invalidate urn-level providers for progress updates
4. **Progress display**: Already reactive (no fix needed)

## Solutions Implemented

### 1. Fixed Discovery Animation Completion Flow
**File**: `lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Change**: Reordered operations in `_onDiscoveryAnimationComplete()` to refresh providers BEFORE navigation:

```dart
void _onDiscoveryAnimationComplete() async {
  final discoveredMotif = _pendingDiscovery?.motif;
  
  setState(() {
    _showDiscoveryAnimation = false;
    _pendingDiscovery = null;
  });

  // Force refresh the urn data FIRST to update hotspot states and progress
  ref.invalidate(urnDetailProvider(widget.urnSlug));
  ref.invalidate(urnsProvider);
  
  // Wait a bit for the provider to refresh
  await Future.delayed(const Duration(milliseconds: 150));

  // Then navigate to motif detail
  if (discoveredMotif != null && mounted) {
    _openMotifDetail(discoveredMotif);
  }
}
```

### 2. Added Refresh on Navigation Return
**File**: `lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Change**: Made navigation methods async and refresh data when user returns:

```dart
void _openMotifDetail(Motif motif) async {
  // Navigate to motif detail and wait for return
  await context.push('/motifs/${motif.id}');
  
  // Refresh when user returns (they might have completed lesson/quiz)
  if (mounted) {
    ref.invalidate(urnDetailProvider(widget.urnSlug));
    ref.invalidate(urnsProvider);
  }
}

// Similar changes for _navigateToLesson() and _navigateToQuiz()
```

### 3. Enhanced Lesson Completion Provider
**File**: `lib/features/lesson/presentation/providers/motif_detail_provider.dart`

**Change**: Added urn provider invalidation when lesson is completed:

```dart
Future<CompleteLessonResponseDto?> completeLesson(String motifId) async {
  // ... existing code ...
  
  // Invalidate motif detail to refresh progress
  ref.invalidate(motifDetailProvider(motifId));
  
  // Also invalidate urn providers to update progress numbers in 3D viewer
  try {
    final motifDetail = await ref.read(motifDetailProvider(motifId).future);
    final urnSlug = motifDetail.urn.slug;
    ref.invalidate(urnDetailProvider(urnSlug));
    ref.invalidate(urnsProvider);
  } catch (e) {
    ref.invalidate(urnsProvider);
  }
  
  return result;
}
```

## Testing Checklist

- [ ] Touch a hidden motif in 3D viewer → Should show discovery animation
- [ ] After animation → Motif should be marked as "explored" (green checkmark)
- [ ] Progress numbers at bottom → Should update immediately (e.g., "1/15" → "2/15")
- [ ] Navigate to motif detail → Complete the lesson
- [ ] Return to 3D viewer → Progress should show updated "learned" count
- [ ] Quiz button → Should appear after completing lesson
- [ ] Complete quiz → Return to 3D viewer and verify "mastered" status

## Implementation Notes

1. **Provider invalidation**: Key to refreshing UI state across the app
2. **Async navigation**: Using `await context.push()` allows us to run code when user returns
3. **Mounted check**: Always check `mounted` before calling `setState` or navigation in async code
4. **Delay timing**: 150ms delay ensures providers have time to refresh before navigation

## Files Modified

1. `lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`
2. `lib/features/lesson/presentation/providers/motif_detail_provider.dart`

## Next Steps

1. Run build_runner to regenerate provider code:
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

2. Test the flow thoroughly on a device/simulator

3. Verify that all progress indicators update correctly

## Related Documentation

- See `3D_MODEL_VIEWER_ARCHITECTURE_DIAGRAM.md` for overall architecture
- See `3D_MODEL_VIEWER_ERROR_HANDLING.md` for error handling patterns

