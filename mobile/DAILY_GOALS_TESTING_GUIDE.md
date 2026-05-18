# Daily Goals Feature - Testing Guide

## Prerequisites
Before testing, ensure you have:
1. Generated provider files: `flutter pub run build_runner build --delete-conflicting-outputs`
2. App running on emulator/device
3. Logged in as a test user

## Quick Test Checklist

### ✅ Basic Functionality

#### 1. Initial Setup
- [ ] App launches without errors
- [ ] Explore screen shows compact daily goal widget
- [ ] Default goal is "Regular" (10 XP)
- [ ] Progress shows "0/10 XP" on first launch

#### 2. Goal Selection
- [ ] Tap compact widget → navigates to Daily Goal screen
- [ ] All 4 goal levels are visible:
  - 🧘 Thoải mái (5 XP) - Green
  - 🚶 Thường xuyên (10 XP) - Blue
  - 🏃 Nghiêm túc (20 XP) - Orange
  - ⚡ Cao thủ (30 XP) - Red
- [ ] Current selection shows checkmark (✓)
- [ ] Tap different level → selection changes
- [ ] Info banner shows: "Bạn có thể thay đổi mục tiêu bất cứ lúc nào"
- [ ] Back button returns to Explore screen

#### 3. Settings Navigation
- [ ] Open Settings from Profile
- [ ] "Learning Goals" section appears at top
- [ ] Tap "Mục tiêu hàng ngày" → navigates to Daily Goal screen
- [ ] Same functionality as from Explore screen

#### 4. XP Tracking
- [ ] Complete a lesson (earns 50 XP)
- [ ] Compact widget updates immediately
- [ ] Progress bar fills correctly
- [ ] XP count increases (e.g., "50/10 XP")
- [ ] Completion status updates (✓ appears if goal met)

#### 5. Goal Completion
- [ ] Earn enough XP to meet goal
- [ ] Widget changes to completed state:
  - Icon: 🚩 → ✅
  - Text: "Mục tiêu hoàn thành!"
  - Progress bar: 100% (green)
- [ ] Celebration overlay shows (if implemented)
- [ ] Can still earn more XP after completion

### 🔄 Advanced Tests

#### 6. Persistence
- [ ] Set goal to "Nghiêm túc" (20 XP)
- [ ] Close app completely
- [ ] Reopen app
- [ ] Goal level is still "Nghiêm túc"
- [ ] Progress is preserved

#### 7. Daily Reset
**Manual Test (Time Travel):**
- [ ] Set device time to 23:55
- [ ] Earn some XP (e.g., 15/20)
- [ ] Change device time to 00:05 next day
- [ ] Kill and restart app
- [ ] Progress resets to 0/20
- [ ] Goal level stays "Nghiêm túc"
- [ ] isCompleted resets to false

**Note:** Reset device time after testing!

#### 8. Edge Cases
- [ ] Set goal to Casual (5 XP)
- [ ] Earn 100 XP in one lesson
- [ ] Widget shows "100/5 XP ✓"
- [ ] Progress bar at 100% (not overflow)
- [ ] No errors in console

#### 9. Multiple XP Sources
- [ ] Start with 0/20 XP
- [ ] Discover a motif (+25 XP) → "25/20 XP ✓"
- [ ] Complete a lesson (+50 XP) → "75/20 XP ✓"
- [ ] Pass a quiz (+75 XP) → "150/20 XP ✓"
- [ ] All updates work correctly

#### 10. Rapid Changes
- [ ] Quickly change goal levels multiple times
- [ ] No crashes or state corruption
- [ ] Final selection persists correctly

### 🎨 UI/UX Tests

#### 11. Visual States
- [ ] Compact widget (not completed):
  - Flag icon visible
  - Blue progress bar
  - "X/Y XP" text clear
  - Arrow icon visible
- [ ] Compact widget (completed):
  - Check icon visible
  - Green progress bar
  - "Mục tiêu hoàn thành!" text
  - Verified icon present

#### 12. Colors & Icons
- [ ] Casual: Green tint, 🧘 icon
- [ ] Regular: Blue tint, 🚶 icon
- [ ] Serious: Orange tint, 🏃 icon
- [ ] Intense: Red tint, ⚡ icon
- [ ] Selected card has bright border
- [ ] Unselected cards have subtle border

#### 13. Animations
- [ ] Tap widget → smooth navigation
- [ ] Select goal → smooth checkmark appearance
- [ ] Progress bar fills smoothly (if animated)
- [ ] Celebration appears with elastic bounce

#### 14. Responsive Layout
- [ ] Test on small screen (< 360px width)
- [ ] Test on medium screen (360-600px)
- [ ] Test on tablet (> 600px)
- [ ] All text is readable
- [ ] No overflow or clipping

### ⚠️ Error Handling

#### 15. No Internet
- [ ] Turn off WiFi/data
- [ ] Open Daily Goal screen
- [ ] Should still work (offline feature)
- [ ] Can change goal level
- [ ] Turn internet back on
- [ ] Earn XP → syncs correctly

#### 16. Storage Errors
- [ ] Clear app data
- [ ] Restart app
- [ ] Goal resets to default (Regular, 10 XP)
- [ ] No crashes

#### 17. Invalid Data
- [ ] Manually corrupt storage (via dev tools if possible)
- [ ] Restart app
- [ ] App recovers with default goal
- [ ] No crashes

### 🔧 Developer Tests

#### 18. Provider State
```dart
// In Dart DevTools or test code
final goal = ref.read(dailyGoalNotifierProvider);
print(goal.level);           // Should print: GoalLevel.regular
print(goal.currentXp);       // Should print: 0 (or current XP)
print(goal.isCompleted);     // Should print: false (or true if completed)
print(goal.progressPercentage); // Should print: 0.0 to 1.0
```

#### 19. XP Sync Provider
```dart
// Ensure XP sync is listening
final user = ref.watch(currentUserProvider);
print('User XP: ${user?.totalXp}');
// Earn XP through lesson
// Check if daily goal updates automatically
```

#### 20. Storage Inspection
```dart
final storage = ref.read(hiveStorageProvider);
final goalJson = storage.getSetting('daily_goal');
print(goalJson); // Should print Map with goal data
```

## Test Scenarios

### Scenario 1: New User Journey
1. First app launch
2. Default goal: Regular (10 XP)
3. Navigate to Settings → Daily Goals
4. Change to Casual (5 XP)
5. Complete a lesson (+50 XP)
6. See celebration
7. Check widget shows ✅ completion

**Expected:** Smooth onboarding, clear visuals, celebration works

### Scenario 2: Dedicated Learner
1. Set goal to Intense (30 XP)
2. Complete 3 lessons throughout day
3. Each lesson updates progress
4. Reach 30 XP → celebration
5. Continue learning (goal already met)
6. Widget shows ✅ but allows more XP

**Expected:** No issues with exceeding goal

### Scenario 3: Casual Learner
1. Set goal to Casual (5 XP)
2. One lesson per day
3. Always meets goal
4. Daily reset works correctly
5. Streak of completions

**Expected:** Motivating for light users

### Scenario 4: Goal Adjustment
1. Start with Regular (10 XP)
2. Too easy → change to Serious (20 XP)
3. Progress preserved: "8/20 XP" (was "8/10 XP")
4. Need 12 more XP instead of 2
5. Complete goal eventually

**Expected:** Can adjust difficulty mid-day

### Scenario 5: Multi-Day Tracking
1. Day 1: Set Serious (20 XP), earn 15 XP
2. Day 2: Auto-reset, earn 25 XP ✓
3. Day 3: Auto-reset, earn 5 XP
4. Day 4: Auto-reset, earn 30 XP ✓
5. Goal level stays Serious throughout

**Expected:** Daily cycle works correctly

## Performance Tests

### 21. XP Update Speed
- [ ] Earn XP → widget updates < 500ms
- [ ] No lag in UI
- [ ] Smooth progress bar animation

### 22. Storage Speed
- [ ] Change goal level → saves < 100ms
- [ ] No blocking UI
- [ ] Instant feedback

### 23. Memory
- [ ] Monitor memory usage
- [ ] No leaks when navigating
- [ ] Celebration overlay disposes correctly

## Accessibility Tests

### 24. Screen Reader
- [ ] Enable TalkBack/VoiceOver
- [ ] Widget announces: "Daily goal, 15 of 20 XP"
- [ ] Goal cards announce level and XP
- [ ] Navigation is clear

### 25. High Contrast
- [ ] Enable high contrast mode
- [ ] Colors still distinguishable
- [ ] Progress bar visible
- [ ] Text readable

## Regression Tests

### 26. Existing Features
- [ ] Explore screen still works
- [ ] Lessons still award XP
- [ ] Quizzes still work
- [ ] Profile still shows total XP
- [ ] Settings other options work

### 27. Auth Flow
- [ ] Logout → daily goal preserved locally
- [ ] Login → daily goal restored
- [ ] Different users have different goals

## Bug Report Template

If you find an issue:

```
**Bug:** [Brief description]
**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected:** [What should happen]
**Actual:** [What actually happened]
**Device:** [Device/emulator info]
**Logs:** [Console output if available]
```

## Success Criteria

All tests pass ✅:
- Core functionality works
- No crashes or errors
- XP tracking is accurate
- UI is polished and responsive
- Daily reset works correctly
- Goal persistence works
- Celebration triggers appropriately

Ready for production! 🚀

