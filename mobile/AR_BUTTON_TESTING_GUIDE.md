# AR Button Fix - Testing Guide

## 🧪 Quick Testing Checklist

### ✅ Visual Testing

**1. AR Button Tooltip**
- [ ] Navigate to URN Viewer screen (tap on any urn in the collection)
- [ ] Long-press or hover over the AR button
- [ ] Verify tooltip shows: "Xem AR (Sắp ra mắt)"
- [ ] Check both AR buttons (one in expanded controls, one in collapsed)

**2. Dialog Appearance**
- [ ] Tap the AR button
- [ ] Dialog should appear centered on screen
- [ ] Check background color matches theme (dark surface)
- [ ] Verify glass border effect is visible
- [ ] Check border radius is smooth (16px)

**3. Dialog Content**
- [ ] Verify title shows "Chế độ AR" with AR icon
- [ ] AR icon should be in primary brand color
- [ ] Content text should be clear and readable (white70)
- [ ] Text should be in Vietnamese
- [ ] Message should explain feature is coming soon
- [ ] Message should mention ability to rotate/zoom model

**4. Dialog Interaction**
- [ ] Tap "Đã hiểu" button
- [ ] Dialog should close smoothly
- [ ] Tap AR button again - dialog should reappear
- [ ] Tap outside dialog - it should dismiss (default AlertDialog behavior)

**5. Edge Cases**
- [ ] Test in portrait mode
- [ ] Test in landscape mode
- [ ] Test on small screen devices
- [ ] Test on large screen devices/tablets
- [ ] Verify text doesn't overflow

---

## 🎯 Test Scenarios

### Scenario A: First-time User
**Goal:** User understands AR is a future feature

1. User opens URN viewer
2. User sees AR button with badge
3. User taps AR button
4. Dialog clearly explains feature is coming soon
5. User dismisses and continues exploring 3D model

**Expected Result:** ✅ User has clear expectations

---

### Scenario B: Existing User
**Goal:** User isn't confused by changed behavior

1. User who previously saw SnackBar taps AR button
2. New dialog appears instead
3. Message is clearer than before
4. User understands the change

**Expected Result:** ✅ Improved clarity

---

### Scenario C: Rapid Interaction
**Goal:** Dialog behaves correctly with quick taps

1. User taps AR button
2. Dialog appears
3. User taps "Đã hiểu"
4. Dialog closes
5. User immediately taps AR button again
6. Dialog appears again without issues

**Expected Result:** ✅ No crashes or UI glitches

---

## 📱 Device Testing Matrix

| Device Type | Screen Size | Orientation | Status |
|-------------|-------------|-------------|--------|
| Phone (Small) | < 5.5" | Portrait | [ ] |
| Phone (Small) | < 5.5" | Landscape | [ ] |
| Phone (Medium) | 5.5" - 6.5" | Portrait | [ ] |
| Phone (Medium) | 5.5" - 6.5" | Landscape | [ ] |
| Phone (Large) | > 6.5" | Portrait | [ ] |
| Phone (Large) | > 6.5" | Landscape | [ ] |
| Tablet | > 7" | Portrait | [ ] |
| Tablet | > 7" | Landscape | [ ] |

---

## 🐛 What to Look For

### ❌ Issues to Report
- Text overflow or cutoff
- Dialog not centered
- Colors don't match theme
- Button doesn't respond
- Dialog doesn't dismiss
- Crashes or errors
- Layout breaks in landscape
- Icon misalignment

### ✅ Expected Behavior
- Smooth dialog animation
- Proper theme colors
- Responsive button
- Clear, readable text
- Proper Vietnamese characters
- Consistent spacing
- Professional appearance

---

## 📸 Screenshots to Capture

1. **AR button with tooltip** (long-press)
2. **Dialog open** (full view)
3. **Dialog in landscape mode**
4. **Before tapping button** (for comparison)
5. **After dismissing dialog** (return to normal)

---

## 🔧 Developer Testing

### Check Console
```bash
# No errors should appear when:
- Tapping AR button
- Opening dialog
- Closing dialog
- Switching orientations
```

### Verify Build
```bash
# Ensure no compilation warnings
flutter analyze lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart
```

### Code Review
- [x] Method signature unchanged
- [x] No breaking changes
- [x] Uses existing AppColors
- [x] Follows Flutter best practices
- [x] Vietnamese text properly encoded
- [x] No hardcoded values

---

## ✨ Success Criteria

✅ All visual tests pass
✅ All scenarios work as expected
✅ No crashes or errors
✅ Dialog looks professional
✅ Text is clear and helpful
✅ Works on all device sizes
✅ Matches app theme
✅ Better UX than before

---

## 📝 Testing Notes

**Tester:** ________________
**Date:** ________________
**Device:** ________________
**OS Version:** ________________

**Notes:**
_______________________________________
_______________________________________
_______________________________________

