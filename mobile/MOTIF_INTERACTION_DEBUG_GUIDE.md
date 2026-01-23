# Motif Interaction Debugging Guide

## Quick Debug Commands

### Check if providers are working
```dart
// In urn_viewer_screen.dart
@override
Widget build(BuildContext context) {
  final urnAsync = ref.watch(urnDetailProvider(widget.urnSlug));
  
  // Add debug logging
  debugPrint('[MOTIF_DEBUG] Building with data: ${urnAsync.value?.urn.discoveredCount}');
  
  return Scaffold(...);
}
```

### Verify provider invalidation
```dart
// In _onDiscoveryAnimationComplete
void _onDiscoveryAnimationComplete() async {
  debugPrint('[MOTIF_DEBUG] Starting animation complete');
  
  ref.invalidate(urnDetailProvider(widget.urnSlug));
  debugPrint('[MOTIF_DEBUG] Invalidated urnDetailProvider');
  
  ref.invalidate(urnsProvider);
  debugPrint('[MOTIF_DEBUG] Invalidated urnsProvider');
  
  await Future.delayed(const Duration(milliseconds: 150));
  debugPrint('[MOTIF_DEBUG] Delay complete, navigating...');
}
```

### Check API responses
```dart
// In motif_detail_provider.dart
Future<CompleteLessonResponseDto?> completeLesson(String motifId) async {
  final result = await apiClient.post<CompleteLessonResponseDto>(...);
  
  // Add debug logging
  debugPrint('[LESSON_DEBUG] Lesson completed: ${result.toJson()}');
  debugPrint('[LESSON_DEBUG] XP earned: ${result.xpEarned}');
  
  return result;
}
```

## Common Issues & Solutions

### Issue 1: Progress numbers don't update
**Symptom**: Bottom bar still shows "1/15" after unlocking motif

**Debug**:
```dart
// Add to _buildBottomBar
Widget _buildBottomBar(UrnDetail urnDetail) {
  debugPrint('[PROGRESS_DEBUG] Discovered: ${urnDetail.urn.discoveredCount}/${urnDetail.urn.motifCount}');
  
  final discovered = urnDetail.urn.discoveredCount;
  final total = urnDetail.urn.motifCount;
  // ...
}
```

**Solution**:
- Check if `ref.invalidate()` is being called
- Verify API returns updated progress
- Ensure build_runner has regenerated provider code

### Issue 2: Motif not marked as explored
**Symptom**: Hotspot still appears as hidden after discovery

**Debug**:
```dart
// In _handleHotspotTap
Future<void> _handleHotspotTap(Motif motif) async {
  debugPrint('[HOTSPOT_DEBUG] Tapped motif: ${motif.name} (${motif.status})');
  
  final result = await ref.read(discoveryNotifierProvider.notifier).unlockMotif(motif.id);
  
  debugPrint('[HOTSPOT_DEBUG] Unlock result: ${result?.toJson()}');
}
```

**Solution**:
- Verify unlock API call succeeds
- Check if invalidation happens before navigation
- Ensure 150ms delay is sufficient

### Issue 3: State not refreshing on return
**Symptom**: 3D viewer doesn't update when returning from motif detail

**Debug**:
```dart
// In _openMotifDetail
void _openMotifDetail(Motif motif) async {
  debugPrint('[NAV_DEBUG] Navigating to motif: ${motif.id}');
  
  await context.push('/motifs/${motif.id}');
  
  debugPrint('[NAV_DEBUG] Returned from motif detail');
  
  if (mounted) {
    debugPrint('[NAV_DEBUG] Invalidating providers...');
    ref.invalidate(urnDetailProvider(widget.urnSlug));
    ref.invalidate(urnsProvider);
  } else {
    debugPrint('[NAV_DEBUG] Widget not mounted, skipping invalidation');
  }
}
```

**Solution**:
- Ensure navigation is `async` with `await`
- Check `mounted` before invalidating
- Verify providers are being invalidated

## Testing Commands

### 1. Full clean rebuild
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
flutter run
```

### 2. Check generated files
```bash
# Verify provider code was regenerated
ls -la lib/features/lesson/presentation/providers/motif_detail_provider.g.dart

# Check modification time
stat lib/features/lesson/presentation/providers/motif_detail_provider.g.dart
```

### 3. View API calls in logs
```bash
# Run with debug logging
flutter run --debug

# Filter for specific logs
flutter logs | grep "MOTIF_DEBUG"
flutter logs | grep "URN_VIEWER"
```

## Expected Log Output

### Successful unlock flow:
```
[URN_VIEWER] Building viewer content
[URN_VIEWER] Discovered count: 1
[HOTSPOT_DEBUG] Tapped motif: Phoenix (hidden)
[API] POST /api/v1/progress/unlock → 200 OK
[HOTSPOT_DEBUG] Unlock result: {xp_earned: 10, status: discovered}
[MOTIF_DEBUG] Starting animation complete
[MOTIF_DEBUG] Invalidated urnDetailProvider
[MOTIF_DEBUG] Invalidated urnsProvider
[MOTIF_DEBUG] Delay complete, navigating...
[URN_VIEWER] Building viewer content
[URN_VIEWER] Discovered count: 2  ← Should increment!
```

### Successful lesson completion:
```
[LESSON_DEBUG] Completing lesson for motif: abc-123
[API] POST /api/v1/progress/complete-lesson → 200 OK
[LESSON_DEBUG] Lesson completed: {xp_earned: 20, status: learned}
[LESSON_DEBUG] XP earned: 20
[LESSON_DEBUG] Invalidating urn providers for slug: cao-dinh
[NAV_DEBUG] Returned from motif detail
[NAV_DEBUG] Invalidating providers...
[URN_VIEWER] Building viewer content
[PROGRESS_DEBUG] Discovered: 2/15  ← Should show updated numbers!
```

## Verification Checklist

- [ ] API calls return 200 status
- [ ] Provider invalidation logs appear
- [ ] Widget rebuilds after invalidation
- [ ] Progress numbers increment correctly
- [ ] Motif status changes (hidden → discovered → learned → mastered)
- [ ] Navigation return triggers refresh
- [ ] No errors in console

## Network Inspector

Use Flutter DevTools to inspect network calls:

1. Run app with `flutter run --debug`
2. Open DevTools → Network tab
3. Look for these endpoints:
   - `POST /api/v1/progress/unlock` (on motif tap)
   - `POST /api/v1/progress/complete-lesson` (on lesson complete)
   - `GET /api/v1/urns/{slug}` (on provider refresh)

## State Inspector

Use Riverpod DevTools to inspect provider state:

1. Add `riverpod_dev_tools` package (if not already)
2. Run app and open DevTools
3. Check provider states:
   - `urnDetailProvider(cao-dinh)` → Should show updated discoveredCount
   - `motifDetailProvider(motif-id)` → Should show updated progress
   - `discoveryNotifierProvider` → Should reset after animation

## Performance Monitoring

```dart
// Add to _onDiscoveryAnimationComplete
void _onDiscoveryAnimationComplete() async {
  final startTime = DateTime.now();
  
  // ... existing code ...
  
  final endTime = DateTime.now();
  final duration = endTime.difference(startTime);
  debugPrint('[PERFORMANCE] Animation complete took: ${duration.inMilliseconds}ms');
}
```

Expected timing:
- Animation complete: < 200ms
- Provider refresh: < 100ms
- Total flow: < 500ms

