# Lesson Unlock Flow - Before and After

## Before (Broken Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User discovers motif in 3D viewer                           │
│    Status: hidden → discovered (server-side)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Discovery animation completes                                │
│    - ref.invalidate(motifDetailProvider)                        │
│    - Wait 150ms                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Navigate to motif detail screen                             │
│    - Screen watches motifDetailProvider                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Provider fetches data                                        │
│    ❌ PROBLEM: Hive cache still has old data (status=hidden)   │
│    ❌ Provider serves cached data BEFORE API fetch completes   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. UI displays WRONG status                                    │
│    ❌ Shows: "Hãy khám phá họa tiết..." (locked)               │
│    ✓ Should show: "Hoàn thành bài học" button (unlocked)      │
└─────────────────────────────────────────────────────────────────┘
```

## After (Fixed Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User discovers motif in 3D viewer                           │
│    Status: hidden → discovered (server-side)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Discovery animation completes                                │
│    - Clear Hive cache: motifsBox.delete(motifId) ✓             │
│    - ref.invalidate(motifDetailProvider) ✓                      │
│    - Wait 300ms (increased from 150ms) ✓                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Navigate to motif detail screen                             │
│    - Screen watches motifDetailProvider                         │
│    - PostFrameCallback: ref.invalidate() AGAIN ✓               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Provider fetches data                                        │
│    ✓ Cache is empty → Forces fresh API call                    │
│    ✓ Gets latest data from server (status=discovered)          │
│    ✓ Updates cache with fresh data                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. UI displays CORRECT status                                  │
│    ✓ Shows: "Hoàn thành bài học" button (unlocked)            │
│    ✓ User can proceed with lesson                              │
└─────────────────────────────────────────────────────────────────┘
```

## Key Fixes

### 1. Explicit Cache Clearing
```dart
// Before: Only invalidated provider
ref.invalidate(lesson_provider.motifDetailProvider(discoveredMotif.id));

// After: Clear cache THEN invalidate provider
final hiveStorage = ref.read(hiveStorageProvider);
await hiveStorage.motifsBox.delete(discoveredMotif.id);
ref.invalidate(lesson_provider.motifDetailProvider(discoveredMotif.id));
```

### 2. Force Refresh on Screen Init
```dart
// New: PostFrameCallback ensures fresh data
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ref.invalidate(motifDetailProvider(widget.motifId));
  });
}
```

### 3. Longer Delay for Cache Operations
```dart
// Before: 150ms
await Future.delayed(const Duration(milliseconds: 150));

// After: 300ms (allows cache deletion to complete)
await Future.delayed(const Duration(milliseconds: 300));
```

## Status Display Logic (lesson_tab.dart)

```dart
final status = progress?.status ?? 'hidden';

// Status values:
// - 'hidden'     → Show lock message
// - 'discovered' → Show "Complete Lesson" button  ✓
// - 'learned'    → Show "Take Quiz" button
// - 'mastered'   → Show "Retake Quiz" button

if (status == 'discovered')
  _ActionButton(
    label: 'Hoàn thành bài học',
    icon: Icons.check_circle_outline,
    onPressed: () => _completeLesson(context, ref),
  ),
```

The fix ensures that `progress?.status` is correctly set to `'discovered'` after discovery!

