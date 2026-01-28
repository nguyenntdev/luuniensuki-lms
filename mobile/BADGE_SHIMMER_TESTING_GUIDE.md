# Badge Shimmer Effects - Quick Testing Guide

## 🎯 What to Test

### 1. **3D Flip Entrance Animation**

**How to Test**:
1. Navigate to Achievements screen (Trophy icon in bottom nav)
2. Go to "Huy Hiệu" tab
3. Watch badges appear with flip animation

**Expected Behavior**:
- ✅ Badges flip from side view (90°) to front view (0°)
- ✅ Each badge appears with ~100ms delay
- ✅ Animation lasts ~800ms total
- ✅ Smooth easeOutCubic curve

**Visual Check**:
```
Time 0ms:    Badge rotated 90° (invisible/side view)
Time 400ms:  Badge half-rotated (~45°)
Time 800ms:  Badge fully visible (0° front view)
```

---

### 2. **Shimmer Effect on LOCKED Badges**

**How to Test**:
1. Scroll through badge grid
2. Find badges WITHOUT "Đã nhận" status
3. Watch for shimmer sweep animation

**Expected Behavior**:
- ✅ Diagonal shimmer sweeps across card (top-left → bottom-right)
- ✅ Shimmer repeats every 2.8 seconds
- ✅ Subtle white glow (max 12% opacity)
- ✅ Badge icon is dimmed (40% opacity)
- ✅ Shows "+X XP" with lock icon

**Visual Check**:
```
┌─────────────────┐
│ →→→ Shimmer     │  ← Light sweep moving diagonally
│  [🔒 Icon]      │  ← Dimmed gray circle
│  Badge Name     │  ← Muted text (40% opacity)
│  [🔒 +50 XP]    │  ← Lock indicator
└─────────────────┘
```

---

### 3. **Pulsing Glow on EARNED Badges**

**How to Test**:
1. Find badges WITH "Đã nhận" status
2. Watch the golden glow effect
3. Observe the pulsing animation

**Expected Behavior**:
- ✅ Golden border (2px width, 60% opacity)
- ✅ Pulsing glow around entire card
- ✅ Glow pulses from 4px to 12px blur
- ✅ Pulse repeats every 2.5 seconds
- ✅ Badge icon has golden gradient
- ✅ Shows "✓ Đã nhận" with green checkmark

**Visual Check**:
```
    ✨ Glow Layer ✨
┌═══════════════════┐
║  [⭐ Golden Icon] ║  ← Golden gradient + dual shadow
║  Badge Name       ║  ← Bold white text
║  [✓ Đã nhận]      ║  ← Green success badge
└═══════════════════┘
    ↑ Golden border
    ↑ Pulsing glow (breathing effect)
```

---

### 4. **Badge Card Styling**

**Earned Badge Checklist**:
- [ ] Golden border (thicker, more visible)
- [ ] Gradient background (subtle primaryDark → primaryLight)
- [ ] Icon has golden gradient
- [ ] Icon has dual-layer shadow (primary + primaryLight)
- [ ] Higher glass opacity (0.15 vs 0.06)
- [ ] Success badge has green border

**Locked Badge Checklist**:
- [ ] Thin border (1.5px, subtle white)
- [ ] No gradient background
- [ ] Icon is gray with low opacity
- [ ] Icon opacity reduced to 40%
- [ ] Text is muted (40% opacity)
- [ ] Lower glass opacity (0.06)

---

## 📱 Device-Specific Testing

### Android:
- [ ] Test on Android 10+
- [ ] Check animation smoothness
- [ ] Verify glow renders correctly
- [ ] Test with dark system theme
- [ ] Check performance with 20+ badges

### iOS:
- [ ] Test on iOS 13+
- [ ] Verify Transform/Matrix4 works
- [ ] Check glow rendering
- [ ] Test with dark system theme
- [ ] Verify no animation lag

---

## ⚡ Performance Testing

### Smooth Scrolling:
1. Scroll through badge grid quickly
2. Animations should NOT cause lag
3. Shimmer should continue smoothly while scrolling

**Expected FPS**: 60fps consistently

### Memory:
1. Open Achievements screen
2. Let animations run for 1-2 minutes
3. Check memory usage doesn't increase
4. AnimationControllers should be properly disposed

---

## 🐛 Edge Cases to Test

### Empty State:
- [ ] No badges → Shows empty state (no animations)

### Single Badge:
- [ ] 1 badge → Animates correctly without errors

### Many Badges (20+):
- [ ] 20+ badges → All animate with stagger
- [ ] Performance remains smooth
- [ ] No dropped frames

### Mixed State:
- [ ] Mix of earned + locked badges
- [ ] Each type shows correct animation
- [ ] Effects don't interfere with each other

---

## 🎨 Visual Quality Checks

### Shimmer Effect:
- [ ] Visible on dark background
- [ ] Not too bright or distracting
- [ ] Smooth gradient transition
- [ ] Proper diagonal direction

### Pulsing Glow:
- [ ] Glow color matches golden theme
- [ ] Pulse is smooth (no jarring changes)
- [ ] Glow spreads evenly around card
- [ ] Not too intense or flashy

### 3D Flip:
- [ ] Perspective looks natural
- [ ] No visual glitches during rotation
- [ ] Badge content stays centered
- [ ] Flip direction is consistent

---

## 🔄 Interactive Testing

### Tap Behavior:
1. Tap earned badge → Detail sheet opens
2. Tap locked badge → Detail sheet opens
3. Animations don't prevent tapping
4. Detail sheet shows correct info

### Tab Switching:
1. Switch from "Huy Hiệu" to "Xếp Hạng"
2. Switch back to "Huy Hiệu"
3. Badges should re-animate (flip entrance)

---

## ✅ Success Criteria

**All animations work correctly**:
- ✅ 3D flip entrance plays on screen load
- ✅ Shimmer sweeps across locked badges
- ✅ Glow pulses on earned badges
- ✅ Staggered delay creates wave effect

**Visual polish**:
- ✅ Earned badges look prestigious (golden, glowing)
- ✅ Locked badges look aspirational (shimmer hints at unlock)
- ✅ Clear visual distinction between states
- ✅ Animations enhance UX without being distracting

**Performance**:
- ✅ 60fps during animations
- ✅ Smooth scrolling with many badges
- ✅ No memory leaks
- ✅ Works on low-end devices

---

## 🎥 Screen Recording Checklist

**Recommended recordings**:
1. Full entrance animation (all badges flipping)
2. Close-up of shimmer effect (locked badge)
3. Close-up of pulsing glow (earned badge)
4. Scrolling through grid (performance test)
5. Tab switching (re-animation test)

---

## 📞 Who to Contact

**Issues with**:
- **Animation jank**: Check device performance, reduce badge count
- **Glow not visible**: Verify BoxShadow support on device
- **Shimmer too bright**: Adjust opacity values in code
- **3D flip looks wrong**: Check Matrix4 perspective value

---

## 🚀 Quick Test Script

```bash
# Run the app
cd mobile
flutter run

# Navigate to Achievements
# 1. Tap Trophy icon (bottom nav)
# 2. Observe 3D flip entrance
# 3. Find locked badges → Check shimmer
# 4. Find earned badges → Check glow
# 5. Scroll grid → Check performance
# 6. Switch tabs → Check re-animation
```

---

**Ready to Test!** 🎉

Report any issues or visual inconsistencies for immediate fix.

