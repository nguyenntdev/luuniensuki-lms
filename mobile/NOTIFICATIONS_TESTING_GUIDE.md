# 🧪 Notifications Screen - Testing Guide

## Quick Start

1. **Run the app**
   ```bash
   cd mobile
   flutter run
   ```

2. **Navigate to notifications**
   - Go to Profile tab (bottom nav)
   - Tap "Thông báo" card
   - Notifications screen should appear

## Test Cases

### ✅ Test 1: Initial Load
**Expected:**
- Screen loads with 5 mock notifications
- Unread count shows "5 chưa đọc" in app bar
- First 2 notifications have glowing dots
- Staggered animation plays smoothly
- Each notification type has correct icon and color

**Steps:**
1. Navigate to notifications screen
2. Observe entrance animation
3. Check unread indicators
4. Verify icon colors match types

---

### ✅ Test 2: Mark Single as Read
**Expected:**
- Dot disappears
- Unread count decreases
- Title weight changes to semi-bold
- Navigation occurs if actionUrl exists

**Steps:**
1. Tap an unread notification (e.g., first one)
2. Observe dot disappearing
3. Check unread count updated
4. Verify navigation (if applicable)

---

### ✅ Test 3: Mark All as Read
**Expected:**
- All dots disappear
- Unread count becomes 0 or hides
- Snackbar shows "Đã đánh dấu tất cả là đã đọc"
- Mark all button may disappear

**Steps:**
1. Ensure some unread notifications exist
2. Tap checkmark icon (✓✓) in app bar
3. Observe all dots vanishing
4. Check snackbar appears
5. Verify unread count is 0

---

### ✅ Test 4: Swipe to Delete
**Expected:**
- Red gradient background appears during swipe
- Delete icon (🗑️) visible on right
- Notification slides out smoothly
- Snackbar shows "Đã xóa thông báo"
- Notification removed from list

**Steps:**
1. Swipe a notification left to right
2. Observe red background
3. Complete the swipe
4. Check notification is removed
5. Verify snackbar appears

---

### ✅ Test 5: Clear All
**Expected:**
- Menu opens when tapping (⋮)
- "Xóa tất cả" option in red
- Confirmation dialog appears
- All notifications removed on confirm
- Empty state shows after clearing

**Steps:**
1. Tap menu icon (⋮) in app bar
2. Select "Xóa tất cả"
3. Verify dialog appears with warning
4. Tap "Xóa tất cả" button
5. Check all notifications removed
6. Verify empty state displays

---

### ✅ Test 6: Pull to Refresh
**Expected:**
- Loading spinner appears (gold color)
- Notifications reload after ~800ms
- Original mock data returns
- Smooth animation

**Steps:**
1. Pull down from top of list
2. Observe loading indicator
3. Wait for completion
4. Verify notifications reloaded

---

### ✅ Test 7: Empty State
**Expected:**
- Large notification icon in circle
- "Chưa có thông báo" heading
- Descriptive text below
- Centered layout
- Beautiful gradient styling

**Steps:**
1. Clear all notifications (see Test 5)
2. Observe empty state
3. Check icon appearance
4. Verify text content
5. Test pull to refresh from empty state

---

### ✅ Test 8: Navigation & Back
**Expected:**
- Back button navigates to profile
- Route maintained in history
- State persists correctly

**Steps:**
1. From profile, go to notifications
2. Tap back arrow (←)
3. Verify return to profile
4. Navigate to notifications again
5. Check state is maintained

---

### ✅ Test 9: Notification Types
**Expected:**
- 5 different notification types visible
- Each has unique color and icon
- Colors match design spec

**Types to verify:**
- 🏆 Achievement (Purple #9C27B0)
- 🔥 Streak (Orange #FF6B35)
- 🎓 Lesson (Blue #60A5FA)
- 👥 Social (Green #34D399)
- ℹ️ System (Gold #E8B44C)

**Steps:**
1. View all 5 mock notifications
2. Check each icon and color
3. Verify gradient backgrounds
4. Test tap on each type

---

### ✅ Test 10: Animations
**Expected:**
- Screen fades in smoothly (600ms)
- List items stagger with 100ms delay
- Slide animation from right
- Swipe gesture is smooth
- No janky animations

**Steps:**
1. Navigate to screen (fresh load)
2. Observe entrance animation
3. Check stagger effect
4. Test swipe gesture
5. Look for any performance issues

---

## Visual Checklist

### Layout
- [ ] App bar properly styled
- [ ] Unread count visible (if > 0)
- [ ] Cards have proper spacing
- [ ] Icons centered in containers
- [ ] Text aligned correctly
- [ ] Time stamps formatted properly

### Colors
- [ ] Glass morphism effect visible
- [ ] Type colors match spec
- [ ] Unread dot glows
- [ ] Delete background is red
- [ ] Text opacity levels correct

### Typography
- [ ] Title sizes correct (16px)
- [ ] Message readable (14px)
- [ ] Time stamps clear (12px)
- [ ] Font weights appropriate
- [ ] No text overflow

### Interactions
- [ ] All tap targets ≥ 48px
- [ ] Swipe gesture responsive
- [ ] Buttons respond to tap
- [ ] Dialog animations smooth
- [ ] Snackbars appear/disappear correctly

---

## Performance Checks

### Memory
- [ ] No memory leaks
- [ ] List scrolls smoothly
- [ ] Animations don't stutter

### State
- [ ] State updates correctly
- [ ] No unnecessary rebuilds
- [ ] Provider working properly

### Responsiveness
- [ ] Works on different screen sizes
- [ ] Portrait orientation good
- [ ] Landscape orientation acceptable

---

## Edge Cases

### No Notifications
- [ ] Empty state displays correctly
- [ ] Pull to refresh works
- [ ] Menu/actions hidden appropriately

### All Read
- [ ] No unread indicators
- [ ] Unread count shows 0 or hides
- [ ] Mark all button hidden

### Single Notification
- [ ] Displays correctly
- [ ] Can be deleted
- [ ] Empty state after delete

### Many Notifications (10+)
- [ ] List scrolls smoothly
- [ ] Performance is good
- [ ] Animations still work

---

## Bug Report Template

If you find issues, report using:

```
### Bug: [Title]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**


**Actual Behavior:**


**Screenshots:**
[If applicable]

**Device Info:**
- OS: 
- Device: 
- Screen size: 
```

---

## Test Results Log

```
Date: ___________
Tester: ___________

[ ] Test 1: Initial Load
[ ] Test 2: Mark as Read
[ ] Test 3: Mark All as Read
[ ] Test 4: Swipe to Delete
[ ] Test 5: Clear All
[ ] Test 6: Pull to Refresh
[ ] Test 7: Empty State
[ ] Test 8: Navigation
[ ] Test 9: Notification Types
[ ] Test 10: Animations

Issues Found:
1. 
2. 
3. 

Overall Status: [ ] Pass [ ] Fail
Notes:

```

---

## Automated Testing (Future)

### Widget Tests
```dart
testWidgets('shows notifications list', (tester) async {
  // Test implementation
});

testWidgets('marks notification as read on tap', (tester) async {
  // Test implementation
});

testWidgets('deletes notification on swipe', (tester) async {
  // Test implementation
});
```

### Integration Tests
```dart
testWidgets('full notification flow', (tester) async {
  // Navigate, interact, verify
});
```

---

**Testing Status:** 🧪 Ready for Manual Testing
**Last Updated:** December 2024

