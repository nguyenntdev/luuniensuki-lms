# 👥 Social Features - Testing Guide

## 🧪 Testing Overview

This guide helps you test the friend system implementation before backend integration.

---

## ✅ Pre-Testing Checklist

### 1. Generate Provider Code
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Hot Restart App
```bash
# In your IDE, press:
# - VS Code: Ctrl+Shift+F5 (Windows/Linux) or Cmd+Shift+F5 (Mac)
# - Android Studio: Shift+F5
```

### 3. Verify Files Exist
```
✓ mobile/lib/features/social/domain/entities/friend.dart
✓ mobile/lib/features/social/domain/entities/friend_request.dart
✓ mobile/lib/features/social/presentation/providers/friends_provider.dart
✓ mobile/lib/features/social/presentation/providers/friends_provider.g.dart
✓ mobile/lib/features/social/presentation/screens/friends_screen.dart
✓ mobile/lib/features/social/presentation/widgets/friend_card.dart
✓ mobile/lib/features/social/presentation/widgets/friend_request_card.dart
```

---

## 🎯 Test Scenarios

### Test 1: Navigation to Friends Screen

**Steps:**
1. Launch the app
2. Navigate to Profile tab (bottom navigation)
3. Scroll down to find "Bạn bè" menu item
4. Tap on "Bạn bè"

**Expected Result:**
- ✅ Friends screen opens
- ✅ Title shows "Bạn Bè"
- ✅ Two tabs visible: "Bạn Bè (0)" and "Lời Mời (0)"
- ✅ Empty state shows: "Chưa có bạn bè"
- ✅ Add friend button (👤) visible in app bar
- ✅ Refresh button (🔄) visible in app bar

**Screenshot Point:**
- Empty friends screen

---

### Test 2: Add Mock Data

**Steps:**
1. On Friends screen, tap the refresh button (🔄)
2. Wait for snackbar message

**Expected Result:**
- ✅ Snackbar shows: "Đã thêm dữ liệu mẫu"
- ✅ Friends tab shows "(3)" count
- ✅ Requests tab shows "(1)" count with red badge
- ✅ Three friend cards appear
- ✅ Friends sorted by XP (Lê Văn C first with 1500 XP)

**Screenshot Point:**
- Friends list with mock data

---

### Test 3: Friend Card Display

**Steps:**
1. Examine each friend card

**Expected Result for Lê Văn C (Top Card):**
- ✅ Avatar shows "L" initial
- ✅ Name: "Lê Văn C"
- ✅ XP chip: "🌟 1500" (gold)
- ✅ Streak chip: "🔥 12" (orange)
- ✅ Level chip: "🛡️ Cấp 6" (blue)
- ✅ Comparison: "⬆️ Hơn bạn XXX XP" (green) or "⬇️ Kém bạn XXX XP" (orange)
- ✅ Options menu (⋮) button visible

**Screenshot Point:**
- Individual friend card

---

### Test 4: Friend Requests Tab

**Steps:**
1. Tap on "Lời Mời" tab
2. Verify request card

**Expected Result:**
- ✅ Tab switches to requests
- ✅ Badge shows "1" in red
- ✅ Request card shows "Phạm Thị D"
- ✅ Time shows "X giờ trước" (hours ago)
- ✅ Green accept button (✓) visible
- ✅ Red reject button (✗) visible

**Screenshot Point:**
- Friend requests tab

---

### Test 5: Accept Friend Request

**Steps:**
1. On Requests tab, tap green accept button (✓)
2. Wait for animation

**Expected Result:**
- ✅ Request disappears from list
- ✅ Success snackbar: "Đã chấp nhận lời mời từ Phạm Thị D"
- ✅ Requests tab count decreases: "(0)"
- ✅ Friends tab count increases: "(4)"
- ✅ Switch to Friends tab shows new friend

**Screenshot Point:**
- After accepting request

---

### Test 6: Reject Friend Request

**Steps:**
1. Add mock data again (refresh button)
2. Go to Requests tab
3. Tap red reject button (✗)

**Expected Result:**
- ✅ Request disappears
- ✅ Snackbar: "Đã từ chối lời mời kết bạn"
- ✅ Requests count decreases
- ✅ Friend NOT added to friends list

**Screenshot Point:**
- After rejecting request

---

### Test 7: Remove Friend

**Steps:**
1. On Friends tab, tap options menu (⋮) on any friend card
2. Bottom sheet appears
3. Tap "Hủy kết bạn"
4. Confirm in dialog

**Expected Result:**
- ✅ Bottom sheet shows with red "Hủy kết bạn" option
- ✅ Confirmation dialog appears
- ✅ Dialog shows friend's name
- ✅ After confirm, friend removed from list
- ✅ Friends count decreases

**Screenshot Points:**
- Options bottom sheet
- Confirmation dialog

---

### Test 8: Add Friend Dialog (UI Only)

**Steps:**
1. Tap add friend button (👤) in app bar
2. Examine dialog

**Expected Result:**
- ✅ Dialog title: "Thêm bạn bè"
- ✅ Text input field with placeholder
- ✅ "Hủy" button
- ✅ "Gửi lời mời" button
- ✅ Tapping "Gửi lời mời" shows: "Tính năng đang phát triển"

**Screenshot Point:**
- Add friend dialog

---

### Test 9: Empty States

**Steps:**
1. Remove all friends (or start fresh)
2. Check both tabs

**Expected Results:**

**Friends Tab:**
- ✅ Icon: 👥 (people_outline)
- ✅ Title: "Chưa có bạn bè"
- ✅ Subtitle: "Thêm bạn bè để cùng học tập và thi đua!"

**Requests Tab:**
- ✅ Icon: 📥 (inbox_outlined)
- ✅ Title: "Không có lời mời"
- ✅ Subtitle: "Lời mời kết bạn sẽ hiển thị ở đây"

**Screenshot Points:**
- Both empty states

---

### Test 10: Data Persistence

**Steps:**
1. Add mock friends
2. Accept a request
3. Close app completely
4. Reopen app
5. Navigate to Friends screen

**Expected Result:**
- ✅ All friends still visible
- ✅ Accepted friend still in list
- ✅ Request no longer showing
- ✅ Counts correct
- ✅ Data persisted in HiveStorage

---

### Test 11: XP Comparison

**Steps:**
1. Note your current user's XP (check Profile screen)
2. View friends list
3. Check comparison indicators

**Expected Result:**
- ✅ Friends with higher XP show: "⬆️ Hơn bạn X XP" (green)
- ✅ Friends with lower XP show: "⬇️ Kém bạn X XP" (orange)
- ✅ Calculation is accurate
- ✅ Colors match status

---

### Test 12: Sorting

**Steps:**
1. Add mock friends
2. Observe order

**Expected Result:**
- ✅ Friends sorted by XP (highest to lowest)
- ✅ Order: Lê Văn C (1500) → Nguyễn Văn A (1250) → Trần Thị B (980)
- ✅ Order updates when friends change

---

## 🎨 Visual Testing

### Glass Morphism Design
- [ ] Background has animated gradient
- [ ] Cards have frosted glass effect
- [ ] Cards have subtle border
- [ ] Cards have blur effect
- [ ] Shadows visible on cards

### Color Accuracy
- [ ] XP chip: Gold (#FFD700)
- [ ] Streak chip: Orange (#FF6B35)
- [ ] Level chip: Blue (#4A90E2)
- [ ] Accept button: Green (#10B981)
- [ ] Reject button: Red (#EF4444)
- [ ] Primary accent: Purple (#6366F1)

### Typography
- [ ] Display names: 16px, bold, white
- [ ] Stats: 12px, bold, colored
- [ ] Time ago: 12px, gray
- [ ] Comparison: 11px, colored

### Spacing
- [ ] Cards have 16px padding
- [ ] 12px gap between cards
- [ ] Consistent alignment
- [ ] No overflow issues

---

## 🐛 Common Issues & Fixes

### Issue 1: Provider Not Found
```
Error: Provider not found
```
**Fix:**
```bash
flutter pub run build_runner build --delete-conflicting-outputs
# Then hot restart (not hot reload)
```

### Issue 2: Route Not Found
```
Error: Could not find a route for /friends
```
**Fix:**
- Verify app_router.dart has friends route
- Check import statement
- Hot restart app

### Issue 3: Empty Screen
```
Screen shows but no content
```
**Fix:**
- Tap refresh button to add mock data
- Check console for errors
- Verify HiveStorage initialized in main.dart

### Issue 4: Tab Not Switching
```
Tabs visible but won't switch
```
**Fix:**
- Check TabController initialization
- Verify TabBarView has correct children
- Hot restart

---

## 📊 Test Results Template

```
Date: _______________
Tester: _______________
Device: _______________
OS: _______________

Test Results:
[ ] Test 1: Navigation - PASS/FAIL
[ ] Test 2: Mock Data - PASS/FAIL
[ ] Test 3: Card Display - PASS/FAIL
[ ] Test 4: Requests Tab - PASS/FAIL
[ ] Test 5: Accept Request - PASS/FAIL
[ ] Test 6: Reject Request - PASS/FAIL
[ ] Test 7: Remove Friend - PASS/FAIL
[ ] Test 8: Add Dialog - PASS/FAIL
[ ] Test 9: Empty States - PASS/FAIL
[ ] Test 10: Persistence - PASS/FAIL
[ ] Test 11: XP Comparison - PASS/FAIL
[ ] Test 12: Sorting - PASS/FAIL

Visual Tests:
[ ] Glass Design - PASS/FAIL
[ ] Colors - PASS/FAIL
[ ] Typography - PASS/FAIL
[ ] Spacing - PASS/FAIL

Overall Status: PASS/FAIL
Notes: _______________
```

---

## 🎬 Demo Script

### For Stakeholder Demo

1. **Introduction** (30s)
   - "This is our new Duolingo-style friend system"

2. **Navigate** (10s)
   - Profile → Bạn bè

3. **Show Empty State** (15s)
   - "When user has no friends yet"

4. **Add Mock Data** (10s)
   - Tap refresh button

5. **Tour Friends List** (45s)
   - Point out sorting by XP
   - Show stat chips
   - Demonstrate XP comparison

6. **Friend Requests** (30s)
   - Switch to Requests tab
   - Show badge notification
   - Accept a request

7. **Remove Friend** (30s)
   - Show options menu
   - Confirm dialog
   - Friend removed

8. **Conclusion** (20s)
   - "Ready for backend integration"
   - "Full documentation included"

**Total Demo Time: ~3 minutes**

---

## ✅ Sign-Off Checklist

### Functionality
- [ ] All navigation works
- [ ] Mock data loads correctly
- [ ] Accept request works
- [ ] Reject request works
- [ ] Remove friend works
- [ ] Data persists
- [ ] Empty states show
- [ ] Dialogs work

### Design
- [ ] Glass morphism applied
- [ ] Colors correct
- [ ] Icons appropriate
- [ ] Typography consistent
- [ ] Spacing uniform

### UX
- [ ] Smooth animations
- [ ] Clear feedback (snackbars)
- [ ] Intuitive navigation
- [ ] Responsive interactions

### Code Quality
- [ ] No console errors
- [ ] No warnings
- [ ] Provider generated
- [ ] Clean code structure

### Documentation
- [ ] README complete
- [ ] Visual guide created
- [ ] Quick reference ready
- [ ] Testing guide done

---

**Ready for Production!** ✨

