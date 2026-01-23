# Testing Checklist - Lesson Unlock Display Fix

## Prerequisites
- [ ] Mobile app is running on device/simulator
- [ ] Backend is running and accessible
- [ ] User is logged in

## Test Scenario 1: New Motif Discovery

### Steps:
1. [ ] Navigate to a URN with undiscovered motifs
2. [ ] Tap on a motif mesh in the 3D viewer (should be locked/hidden)
3. [ ] Wait for discovery animation to complete
4. [ ] App automatically navigates to motif detail screen

### Expected Results:
- [ ] **Progress stepper shows "Đã khám phá" (Discovered) status**
- [ ] **Lesson tab is accessible (not locked)**
- [ ] **"Hoàn thành bài học" button is visible**
- [ ] **No "locked" message is shown**
- [ ] Lesson content is visible (intro, description, etc.)

### Bug Symptoms (if not fixed):
- ❌ Shows "Hãy khám phá họa tiết này trên mô hình 3D để mở khóa bài học"
- ❌ Progress stepper shows "Ẩn" or locked status
- ❌ Cannot proceed with lesson

## Test Scenario 2: Complete Lesson Flow

### Steps:
1. [ ] After discovering a motif, tap "Hoàn thành bài học"
2. [ ] Wait for completion dialog
3. [ ] Dismiss or take quiz

### Expected Results:
- [ ] Status updates to "Đã học" (Learned)
- [ ] XP is awarded (shown in dialog)
- [ ] Quiz button becomes available
- [ ] Progress stepper updates

## Test Scenario 3: App Resume

### Steps:
1. [ ] Discover a motif and navigate to detail screen
2. [ ] Press home button to background the app
3. [ ] Wait 5-10 seconds
4. [ ] Return to the app

### Expected Results:
- [ ] Data refreshes automatically
- [ ] Status remains correct (discovered/learned/mastered)
- [ ] No stale data is displayed

## Test Scenario 4: Already Discovered Motif

### Steps:
1. [ ] Navigate to a motif that was previously discovered
2. [ ] Open the motif detail screen

### Expected Results:
- [ ] Correct status is shown (discovered/learned/mastered)
- [ ] Appropriate action button is displayed
- [ ] No "locked" message if already discovered

## Test Scenario 5: Cache Verification

### Steps:
1. [ ] Discover a motif
2. [ ] Navigate away and return to detail screen
3. [ ] Repeat 3-4 times

### Expected Results:
- [ ] Status remains consistent
- [ ] No flickering between statuses
- [ ] Data loads quickly (from cache when appropriate)

## Debugging Tips

If test fails, check:

### 1. Console Logs
Look for these debug messages:
```
[URN_VIEWER] Discovery animation complete for motif: {id}
[MOTIF_DETAIL] Post-frame callback - invalidating provider
[MOTIF_DETAIL] Lifecycle resumed - refreshing data
```

### 2. Provider State
Check Riverpod DevTools to verify:
- `motifDetailProvider` is invalidated
- Provider refetches from network (not cache)
- Progress status is correctly updated

### 3. Cache State
Check Hive storage:
```dart
// In debug console
final hiveStorage = ref.read(hiveStorageProvider);
final cached = hiveStorage.getCachedMotif(motifId);
print('Cached status: ${cached?['progress']?['status']}');
```

### 4. Network Calls
Use Charles Proxy or Flutter DevTools Network tab to verify:
- `/api/v1/motifs/{id}` is called after discovery
- Response contains `progress.status = 'discovered'`
- Cache is not serving stale data

## Performance Checks

- [ ] Screen loads within 1 second
- [ ] No janky animations
- [ ] Cache operations don't block UI
- [ ] 300ms delay is not noticeable to user

## Edge Cases

- [ ] **Poor network**: What happens if API call fails?
  - Should show cached data if available
  - Should show error state if no cache

- [ ] **Offline mode**: Can user view already-discovered lessons offline?
  - Cache should preserve lesson data
  - Status should be readable from cache

- [ ] **Multiple discoveries in succession**: Discover 3-4 motifs quickly
  - Each should show correct status
  - No race conditions

## Regression Tests

Ensure fix doesn't break existing functionality:

- [ ] Home screen still loads correctly
- [ ] URN list still works
- [ ] 3D viewer still performs well
- [ ] Other providers not affected
- [ ] Quiz flow still works
- [ ] Profile screen unchanged

## Sign-off

- [ ] All tests pass
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] Ready for production

---

**Tester**: ________________  
**Date**: ________________  
**Build**: ________________  
**Notes**: ________________

