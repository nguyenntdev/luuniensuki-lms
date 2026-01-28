# 🧪 Pulsing Banner Testing Guide

## Quick Testing Checklist

### 1. Build & Run
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
flutter run
```

### 2. Navigate to Practice Screen
- From bottom navigation, tap **Practice** icon
- Banner should appear at the top of the screen

### 3. Visual Tests

#### ✅ Animation Verification
- [ ] Banner pulses subtly (grows ~2%)
- [ ] Border glows (opacity changes visible)
- [ ] Shadow expands and contracts
- [ ] Bell icon wobbles left-right
- [ ] All animations are smooth (60 FPS)
- [ ] Animation loops continuously

#### ✅ Timing Check
- [ ] Full cycle completes in 2 seconds
- [ ] Animations are synchronized
- [ ] No jerky or stuttering motion

#### ✅ Layout Tests
**Desktop/Tablet Mode (width ≥ 340px)**:
- [ ] Icon on left
- [ ] Text in center
- [ ] Arrow on right
- [ ] All elements aligned horizontally

**Mobile/Compact Mode (width < 340px)**:
- [ ] Icon on top
- [ ] Text below icon
- [ ] Layout stacks vertically

#### ✅ Interaction Tests
- [ ] Banner is tappable
- [ ] Tap shows "Bắt đầu ôn tập nhanh..." snackbar
- [ ] Animation continues during interaction
- [ ] No lag or delay on tap

#### ✅ Edge Cases
- [ ] When dueCount = 0, banner is hidden
- [ ] When dueCount > 0, banner is visible
- [ ] nextReviewTime displays correctly
- [ ] Time formatting works (minutes, hours, days)

### 4. Performance Tests

#### Memory
```bash
# Run app with memory profiling
flutter run --profile

# Check for memory leaks
# Animation controller should be disposed properly
```

#### Frame Rate
- Open DevTools → Performance
- Check FPS stays at 60
- No dropped frames during animation

#### CPU Usage
- Monitor CPU in DevTools
- Should be < 5% during animation
- No spikes or excessive usage

### 5. Device Testing Matrix

| Device Type | Screen Size | Test Status |
|-------------|-------------|-------------|
| iPhone 14 Pro | 393x852 | ⏳ Pending |
| iPad Pro | 1024x1366 | ⏳ Pending |
| Android Phone | 360x800 | ⏳ Pending |
| Android Tablet | 768x1024 | ⏳ Pending |

### 6. Code Quality Checks

```bash
# Format code
flutter format lib/features/practice/presentation/widgets/due_reviews_banner.dart

# Analyze code
flutter analyze lib/features/practice/presentation/widgets/due_reviews_banner.dart

# Run tests (if any)
flutter test
```

### 7. Accessibility Tests

- [ ] VoiceOver/TalkBack announces banner correctly
- [ ] Banner content is readable
- [ ] Tap target is large enough (minimum 48x48 dp)
- [ ] Color contrast meets WCAG AA standards
- [ ] No rapid flashing (safe for photosensitive users)

## Expected Results

### Visual Appearance
- Orange/amber gradient background (#F59E0B)
- White text with bold title
- Notification bell icon in orange circle
- Rounded corners (16px border radius)
- Subtle shadow underneath

### Animation Behavior
- Gentle, continuous pulsing
- Not distracting or annoying
- Draws attention without being jarring
- Professional and polished feel

## Common Issues & Solutions

### Issue: Animation stutters
**Solution**: Check if device is in low-power mode, ensure 60 FPS

### Issue: Icon doesn't wobble
**Solution**: Verify `_iconRotationAnimation` is applied correctly

### Issue: Border doesn't glow
**Solution**: Check `_borderOpacityAnimation` value range (0.3-0.7)

### Issue: Memory leak
**Solution**: Ensure `_controller.dispose()` is called in `dispose()`

## Performance Benchmarks

### Expected Metrics
- **FPS**: 60 (consistent)
- **Frame time**: ~16.67ms
- **Memory**: < 5 MB overhead
- **CPU**: < 5% usage
- **Battery**: < 1% per hour

## Sign-off

- [ ] Visual tests passed
- [ ] Performance tests passed
- [ ] Device tests passed
- [ ] Accessibility tests passed
- [ ] Code quality checks passed
- [ ] Ready for production

**Tested by**: _________________  
**Date**: _________________  
**Build**: _________________

