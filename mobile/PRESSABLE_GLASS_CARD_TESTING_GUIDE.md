# PressableGlassCard - Visual Testing Guide

## Testing Locations

### 1. Practice Home Screen
**File**: `lib/features/practice/presentation/screens/practice_home_screen.dart`

**Test Cases**:
- [ ] Info card (blue background) - Top of screen
  - Press and hold: Should scale to 0.97, move down 4px, reduce shadow
  - Release: Should animate back smoothly
  - Tap: Should show "💡 Tip acknowledged!" SnackBar
  - Feel: Haptic feedback on tap (device only)

### 2. Explore Screen  
**File**: `lib/features/explore/presentation/screens/explore_screen.dart`

**Test Cases**:
- [ ] Stats card - Below header
  - Press: Should show 3D depth effect
  - Release: Should return to normal
  - Haptic: Light impact on tap

### 3. Practice Mode Cards
**File**: `lib/features/practice/presentation/widgets/practice_mode_card.dart`

**Test Cases for UNLOCKED Cards**:
- [ ] Quick Review mode
  - Press: Scale down, move down, shadow reduces
  - Animation: Smooth 150ms transition
  - Tap: Navigates to practice session
  - Haptic: Feedback on tap

- [ ] Spaced Repetition mode
  - Same behavior as Quick Review

- [ ] Challenge mode
  - Same behavior as Quick Review

**Test Cases for LOCKED Cards**:
- [ ] Locked mode (if any)
  - Press: NO animation (enable3DEffect = false)
  - Tap: No navigation (onTap = null)
  - Visual: Should look disabled with lock overlay

## Visual Inspection Checklist

### Animation Quality
- [ ] Scale transition is smooth (not jerky)
- [ ] Depth effect is subtle but noticeable
- [ ] Shadow transition is visible
- [ ] Animation completes in ~150ms (feels instant but not abrupt)
- [ ] No visual glitches or flashing

### Visual Values to Verify
- [ ] **Scale**: Card shrinks to about 97% size
- [ ] **Depth**: Card moves down approximately 4 pixels
- [ ] **Shadow Blur**: 
  - Normal state: ~15px blur (soft shadow)
  - Pressed state: ~5px blur (sharper shadow)

### State Transitions
- [ ] Press → Release: Smooth reverse animation
- [ ] Press → Drag away → Cancel: Animation reverses
- [ ] Rapid taps: No animation stuttering
- [ ] Long press: Animation holds in pressed state

### Platform-Specific
**iOS**:
- [ ] Haptic feedback feels like a light "tap"
- [ ] Animation uses native curves
- [ ] No performance lag

**Android**:
- [ ] Haptic feedback works (if device supports)
- [ ] Animation is smooth
- [ ] Material design compliance

## Performance Testing

### Frame Rate
- [ ] Animations run at 60 FPS
- [ ] No dropped frames during press
- [ ] Smooth on lower-end devices

### Memory
- [ ] No memory leaks (check with DevTools)
- [ ] Animation controller properly disposed
- [ ] No unnecessary rebuilds

## Edge Cases

### Interaction Edge Cases
- [ ] Press and hold, then drag away: Should cancel animation
- [ ] Simultaneous presses on multiple cards: Each animates independently
- [ ] Screen rotation during press: Animation continues correctly
- [ ] Disabled state: No animation, no haptic

### Visual Edge Cases
- [ ] Very small cards: Animation still visible
- [ ] Very large cards: Animation feels proportional
- [ ] Cards with complex gradients: No color artifacts
- [ ] Cards with borders: Border animates smoothly

## Comparison: Before vs After

### BEFORE (InkWell + GlassContainer)
- Static click feedback
- Ripple effect only
- No 3D depth illusion
- No haptic feedback
- No scale animation

### AFTER (PressableGlassCard)
- Dynamic 3D press effect
- Scale + depth + shadow animations
- Haptic feedback on tap
- Smooth 150ms transitions
- Professional tactile feel

## Device Testing Matrix

| Device Type | Test | Expected Result |
|------------|------|-----------------|
| iOS Simulator | Visual animation | ✅ Smooth |
| iOS Simulator | Haptic feedback | ⚠️ No haptic (simulator limitation) |
| iOS Physical | Visual + Haptic | ✅ Full experience |
| Android Emulator | Visual animation | ✅ Smooth |
| Android Emulator | Haptic feedback | ⚠️ Limited (depends on emulator) |
| Android Physical | Visual + Haptic | ✅ Full experience |

## Debug Tools

### Flutter DevTools
```bash
flutter pub global activate devtools
flutter pub global run devtools
```

### Performance Overlay
```dart
MaterialApp(
  showPerformanceOverlay: true,
  // ...
)
```

### Print Animation Values (Debug)
Add to `pressable_glass_card.dart`:
```dart
_controller.addListener(() {
  print('Scale: ${_scaleAnimation.value}');
  print('Depth: ${_depthAnimation.value}');
  print('Shadow: ${_shadowAnimation.value}');
});
```

## Expected Behavior Summary

| Action | Scale | Depth (Y) | Shadow Blur | Haptic |
|--------|-------|-----------|-------------|--------|
| Normal | 1.0 | 0px | 15px | - |
| Pressed | 0.97 | +4px | 5px | ✅ Light |
| Released | 1.0 | 0px | 15px | - |

## Testing Notes
- Test in both light and dark mode
- Verify animation works with different background colors
- Check that locked/disabled states don't animate
- Ensure haptic feedback doesn't fire multiple times on single tap

