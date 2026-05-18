# Testing Guide - Entrance Animations

## Quick Test Checklist

### Collection Screen Tests

#### Basic Animation Test
1. Navigate to Collection screen from bottom navigation
2. **Expected**: Grid items should:
   - Fade in from transparent to fully visible
   - Slide up from slightly below their final position
   - Appear in staggered sequence (top-left to bottom-right)
   - Complete animation within ~1 second

#### Filter Change Test
1. Open Collection screen
2. Wait for initial animation to complete
3. Tap on a different filter (e.g., "Đã khám phá")
4. **Expected**: 
   - Items should update without re-animating
   - No flickering or layout jumps

#### Navigation Test
1. Navigate to Collection screen
2. Let animation play
3. Navigate away and return to Collection
4. **Expected**: Animation plays again on return

### Achievements Screen Tests

#### Basic Animation Test
1. Navigate to Achievements screen from bottom navigation
2. Ensure "Huy Hiệu" tab is selected
3. **Expected**: Badge cards should:
   - Fade in from transparent to fully visible
   - Slide up from slightly below their final position
   - Appear in staggered sequence
   - Complete animation within ~1 second

#### Tab Switch Test
1. Open Achievements screen (Huy Hiệu tab)
2. Wait for badge animation to complete
3. Switch to "Xếp Hạng" tab
4. Switch back to "Huy Hiệu" tab
5. **Expected**:
   - No re-animation when returning to badges tab
   - Tab switching is smooth

### Performance Tests

#### Scroll Test
1. Open Collection or Achievements screen
2. During animation, try scrolling
3. **Expected**:
   - Scroll should be smooth
   - No lag or jank
   - Animation continues smoothly while scrolling

#### Device Performance Test
Run on different devices:
- High-end device (e.g., recent iPhone/Android)
- Mid-range device
- Low-end device (if available)

**Expected**: Smooth 60 FPS animation on all devices

### Edge Cases

#### Empty State Test
1. Test Collection screen with no items
2. **Expected**: Empty state shows without animation issues

#### Single Item Test
1. Test with only 1 item in collection
2. **Expected**: Single item animates correctly

#### Many Items Test
1. Test with 20+ items in grid
2. **Expected**: All items animate smoothly with proper stagger

## Detailed Test Scenarios

### Scenario 1: First Time User
```
Steps:
1. Launch app
2. Navigate to Collection screen
3. Observe animation

Verify:
✓ Animation plays smoothly
✓ No items appear before animation
✓ All items are visible after animation
✓ No console errors
```

### Scenario 2: Returning User
```
Steps:
1. Open Collection screen
2. Navigate to Profile
3. Return to Collection
4. Observe animation

Verify:
✓ Animation plays again
✓ No memory issues
✓ Performance remains consistent
```

### Scenario 3: Rapid Navigation
```
Steps:
1. Quickly navigate: Explore → Collection → Profile → Collection
2. Repeat 5 times

Verify:
✓ No crashes
✓ Animations don't stack
✓ Memory usage stable
```

## Performance Monitoring

### Flutter DevTools Checklist
1. Open Flutter DevTools
2. Navigate to Performance tab
3. Record while opening Collection/Achievements
4. **Check**:
   - Frame rendering time (should be < 16ms for 60 FPS)
   - No dropped frames during animation
   - GPU usage is reasonable

### Memory Profiling
1. Open Memory profiler in DevTools
2. Navigate to screens multiple times
3. **Verify**:
   - Memory doesn't continuously increase
   - AnimationControllers are disposed
   - No memory leaks

## Visual Quality Checks

### Animation Smoothness
- [ ] No stuttering or jank
- [ ] Consistent timing across items
- [ ] Smooth curve (easeOutCubic visible)

### Visual Feedback
- [ ] Fade is noticeable but not jarring
- [ ] Slide distance is appropriate (not too much/little)
- [ ] Stagger timing feels natural

### Layout Integrity
- [ ] Items don't jump during animation
- [ ] Grid spacing remains consistent
- [ ] No overlapping during animation

## Debug Commands

### Enable Performance Overlay
```dart
// In app.dart or main.dart
MaterialApp(
  showPerformanceOverlay: true,  // Add this temporarily
  ...
)
```

### Check Animation Status
Add temporary debug prints:
```dart
_controller.addStatusListener((status) {
  print('Animation status: $status');
});
```

## Known Issues / Expected Behavior

### Not Bugs
- Animation only plays once per screen visit (by design)
- Filter changes don't re-animate (by design)
- Tab switching doesn't re-animate (by design)

### Report if Occurs
- Animation never completes
- Items appear before animation starts
- Memory leak warnings
- Performance degradation over time

## Success Criteria

All tests pass if:
1. ✅ Animations are smooth (60 FPS)
2. ✅ Stagger effect is visible and pleasant
3. ✅ No visual glitches or layout issues
4. ✅ No performance degradation
5. ✅ No memory leaks
6. ✅ Works on all tested devices
7. ✅ Existing functionality intact

