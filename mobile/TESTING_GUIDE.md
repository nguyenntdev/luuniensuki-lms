# Testing Guide for Achievements Screen Enhancements

## Pre-Testing Checklist

### 1. Verify Code Quality
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
flutter analyze lib/features/achievements/presentation/screens/achievements_screen.dart
```

Expected: No errors or warnings

### 2. Check Imports
All required widgets should be imported:
- ✅ GradientText from `lib/shared/widgets/text/gradient_text.dart`
- ✅ PressableGlassCard from `lib/shared/widgets/glass/pressable_glass_card.dart`
- ✅ ShimmerWidget from `lib/shared/widgets/effects/shimmer_widget.dart`

## Visual Testing Scenarios

### Scenario 1: Initial Load
**Test:** Open Achievements screen for the first time

**Expected Behavior:**
1. Shimmer loading skeletons appear (6 badge cards)
2. Trophy icon pulses continuously
3. "Thành Tích" title shows gradient (purple → pink)
4. After data loads, badges appear with staggered animation
5. Each badge rotates and fades in with 100ms delay

### Scenario 2: Earned Badges
**Test:** View unlocked/earned achievements

**Expected Behavior:**
1. Badge card has pulsing glow effect (subtle, continuous)
2. Badge name shows gradient text (purple → pink)
3. Badge icon has gradient background
4. Border is highlighted with primary color
5. Status shows "Đã nhận" with green indicator

**Interaction:**
1. Tap badge → should scale down to 0.97
2. Feel haptic feedback
3. Badge moves down 4px (depth effect)
4. Badge detail sheet appears
5. On release → badge springs back

### Scenario 3: Locked Badges
**Test:** View locked achievements

**Expected Behavior:**
1. No glow effect
2. Badge name is plain text (grayed out)
3. Badge icon is grayed out with low opacity
4. Border is subtle
5. Status shows "+X XP" with lock icon

**Interaction:**
1. Tap badge → same press animation as earned
2. Haptic feedback
3. Badge detail sheet shows how to unlock

### Scenario 4: Header Elements
**Test:** Observe header animations

**Expected Behavior:**
1. "Thành Tích" title has gradient (primary colors)
2. Trophy icon pulses continuously (2-second cycle)
3. Glow spreads and contracts smoothly
4. Animation never stops (continuous loop)

### Scenario 5: Loading States
**Test:** Force reload by pulling to refresh or clearing cache

**Expected Behavior (Badges Tab):**
1. 6 skeleton cards appear in grid
2. Shimmer effect sweeps diagonally
3. Each skeleton has circular icon, text bars
4. Shimmer repeats every 1.5 seconds
5. Clean transition to real data

**Expected Behavior (Leaderboard Tab):**
1. 8 skeleton entries appear in list
2. Same shimmer effect as badges
3. Each skeleton has rank circle, avatar, name bars
4. Smooth transition to real data

### Scenario 6: Tab Switching
**Test:** Switch between "Huy Hiệu" and "Xếp Hạng" tabs

**Expected Behavior:**
1. Tab labels remain clear (no gradient - handled by TabBar)
2. Selected tab has gradient background
3. Unselected tab is white70
4. Tab switching is smooth
5. Content animates in when switching

## Performance Testing

### 1. Animation Performance
- Trophy icon pulse should be smooth (60fps)
- Badge glow should not cause lag
- Staggered entrance should be smooth
- Press animations should be responsive

### 2. Memory Usage
- No memory leaks from continuous animations
- AnimationControllers properly disposed
- Check with Flutter DevTools

### 3. Scroll Performance
- Grid scroll should be smooth with glows active
- No janks when scrolling fast
- Shimmer doesn't affect scroll performance

## Edge Cases

### 1. No Badges
- Empty state shows correctly
- No errors with empty list
- Proper message displayed

### 2. Many Badges
- Stagger animation works for 20+ badges
- Performance remains good
- Glow effects don't compound negatively

### 3. Rapid Tab Switching
- Animations don't conflict
- Loading states handle properly
- No crashes or errors

## Verification Checklist

After testing, verify:
- [ ] Header title has gradient
- [ ] Trophy icon pulses continuously
- [ ] Earned badges have pulsing glow
- [ ] Earned badge names have gradient
- [ ] Cards respond to press with animation
- [ ] Haptic feedback works on tap
- [ ] Loading shows shimmer skeletons
- [ ] Staggered entrance animation works
- [ ] No console errors or warnings
- [ ] Performance is smooth (60fps)
- [ ] Memory usage is stable

## Troubleshooting

### Issue: Trophy doesn't pulse
**Fix:** Check _PulsingTrophyIcon widget initialization

### Issue: Badge cards don't press
**Fix:** Verify PressableGlassCard import and onTap callback

### Issue: No gradient on title
**Fix:** Check GradientText import and AppColors.primaryGradient

### Issue: Shimmer doesn't animate
**Fix:** Verify ShimmerWidget enabled property is true

### Issue: Animations are choppy
**Fix:** Check device performance, reduce concurrent animations

