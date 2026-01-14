# Profile Menu Testing Guide

## 🚀 Quick Start

```bash
cd mobile
flutter run
```

Then navigate to the Profile tab (4th tab in bottom navigation).

---

## 🧪 Testing Scenarios

### Scenario 1: Personal Info Navigation

**Steps:**
1. Open app and login
2. Navigate to Profile screen (bottom nav, 4th icon)
3. Scroll down to "Cài đặt & Tài khoản" section
4. Tap on "Thông tin cá nhân" (blue card, person icon)

**Expected Results:**
- ✅ Screen slides in from right
- ✅ Personal Info screen appears
- ✅ Current user data is displayed
- ✅ Display name field shows current name
- ✅ Username field shows current username
- ✅ Back button works

**Test Edge Cases:**
- Edit name and tap back → Shows unsaved changes dialog
- Save with empty name → Shows validation error
- Cancel button → Discards changes

---

### Scenario 2: Notifications Navigation

**Steps:**
1. From Profile screen
2. Tap on "Thông báo" (amber card, bell icon)

**Expected Results:**
- ✅ Navigates to Notifications screen
- ✅ Shows list of notifications
- ✅ Back button returns to Profile
- ✅ Notifications can be marked as read
- ✅ Filter tabs work correctly

**Test Edge Cases:**
- No notifications → Shows empty state
- Delete notification → Updates list
- Mark as read → Updates badge count

---

### Scenario 3: Settings Navigation

**Steps:**
1. From Profile screen
2. Tap on "Cài đặt" (gray card, gear icon)

**Expected Results:**
- ✅ Navigates to Settings screen
- ✅ All settings sections are visible
- ✅ Toggles work correctly
- ✅ Back button returns to Profile
- ✅ Changes are persisted

**Test Edge Cases:**
- Toggle notification → Persists after restart
- Change language → Updates UI
- Clear cache → Shows confirmation dialog

---

### Scenario 4: Help & Support Navigation

**Steps:**
1. From Profile screen
2. Tap on "Trợ giúp & Hỗ trợ" (green card, help icon)

**Expected Results:**
- ✅ Navigates to Help & Support screen
- ✅ FAQ items are expandable
- ✅ Contact buttons work
- ✅ Email link opens mail app
- ✅ Social links open browser
- ✅ Back button returns to Profile

---

## 🎯 Visual Verification

### Check These UI Elements:

1. **Menu Cards**
   - [ ] Cards have glass effect
   - [ ] Icons have gradient backgrounds
   - [ ] Colors match theme (blue, amber, gray, green)
   - [ ] Chevron arrows visible
   - [ ] Tap feedback works

2. **Animations**
   - [ ] Cards fade in on scroll
   - [ ] Screens slide in smoothly
   - [ ] Back navigation is smooth
   - [ ] No jank or stutters

3. **Text & Icons**
   - [ ] All text is readable
   - [ ] Icons are properly sized
   - [ ] Subtitles are visible
   - [ ] No text overflow

---

## 📊 Performance Testing

### Check These Metrics:

1. **Navigation Speed**
   - Should complete in < 300ms
   - No lag or delay

2. **Memory Usage**
   - No memory leaks when navigating
   - Screens properly disposed

3. **Animation Performance**
   - 60 FPS during transitions
   - No dropped frames

---

## 🐛 Known Issues & Limitations

None! All features are working as expected. ✨

---

## 💡 Tips

- Use hot reload during development: Press `r` in terminal
- Use hot restart for state changes: Press `R` in terminal
- Check logs for navigation events: Look for GoRouter messages
- Enable Flutter DevTools for performance monitoring


