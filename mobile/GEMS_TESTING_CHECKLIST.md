# Gems System Testing Checklist

## Manual Testing Guide

### 1. Initial Setup
- [ ] Launch the app
- [ ] Verify initial gems balance is 100
- [ ] Navigate to Profile screen
- [ ] Confirm gems display appears in profile header

### 2. Gems Shop
- [ ] Tap on gems display in profile
- [ ] Verify navigation to Gems Shop screen
- [ ] Check all 3 shop items display correctly:
  - [ ] Streak Freeze (50 gems)
  - [ ] Double XP (100 gems)  
  - [ ] Hint (25 gems)
- [ ] Tap "How to Earn Gems" section
- [ ] Verify it expands/collapses correctly
- [ ] Tap "Transaction History"
- [ ] Verify history modal displays

### 3. Purchase Items
- [ ] Try to purchase Streak Freeze (50 gems)
- [ ] Verify balance decreases to 50
- [ ] Verify transaction appears in history
- [ ] Try to purchase Double XP (100 gems) - should fail
- [ ] Verify error message shows
- [ ] Verify balance remains at 50

### 4. Earning Gems - Lesson Completion
- [ ] Complete a lesson
- [ ] Verify gems increase by +10
- [ ] Check transaction history shows "Hoàn thành bài học"
- [ ] Verify gems display animates

### 5. Earning Gems - Daily Goal
- [ ] Set daily goal to "Casual" (5 XP)
- [ ] Complete lessons to reach 5 XP
- [ ] Verify gems increase by +20 when goal completes
- [ ] Check transaction history shows "Hoàn thành mục tiêu hàng ngày"

### 6. Earning Gems - Perfect Quiz
- [ ] Take a quiz
- [ ] Answer all questions correctly (100%)
- [ ] Verify gems increase by +5 bonus
- [ ] Check transaction history shows "Hoàn hảo"

### 7. Earning Gems - 7-Day Streak
Note: This requires backend testing or mock data
- [ ] If user has 7-day streak, complete a lesson
- [ ] Verify gems increase by +50
- [ ] Check transaction history shows "Chuỗi học tập 7 ngày!"
- [ ] Repeat for 14, 21 day streaks

### 8. Navigation Tests
- [ ] Verify gems display in profile header is tappable
- [ ] Verify "Cửa Hàng Gems" menu card navigates to shop
- [ ] Verify back navigation works from shop
- [ ] Verify all transitions are smooth

### 9. UI/UX Tests
- [ ] Verify gems icon displays correctly
- [ ] Verify gem count displays correctly
- [ ] Verify glass morphism styling looks good
- [ ] Verify animations are smooth
- [ ] Verify all Vietnamese text displays correctly
- [ ] Test on different screen sizes
- [ ] Test in light/dark theme

### 10. Edge Cases
- [ ] Try to spend more gems than available
- [ ] Verify balance never goes negative
- [ ] Test with 0 gems
- [ ] Test with large gem amounts (9999+)
- [ ] Test transaction history with many items
- [ ] Test app restart (verify gems persist)

## Expected Behavior Summary

### Gem Earning Rules
| Action | Gems | Transaction Type |
|--------|------|------------------|
| Complete Lesson | +10 | earnedLesson |
| Complete Daily Goal | +20 | earnedBonus |
| Perfect Quiz (100%) | +5 | earnedPerfect |
| 7-Day Streak Milestone | +50 | earnedStreak |

### Shop Items
| Item | Cost | Description |
|------|------|-------------|
| Streak Freeze | 50 | Protect streak for 1 day |
| Double XP | 100 | 2x XP for 30 minutes |
| Hint | 25 | Get a hint for answer |

### Storage Keys
- `gems_balance` - Current balance
- `gems_transactions` - Transaction history array

## Known Issues / Limitations

1. **Backend Integration**: Currently local-only, no server sync
2. **Shop Item Functionality**: Purchasing works but items don't have effects yet
3. **Streak Detection**: 7-day streak gems only award on lesson completion
4. **Transaction Limit**: No limit on transaction history size

## Future Testing Needs

- [ ] Backend API integration tests
- [ ] Concurrent transaction handling
- [ ] Network error handling
- [ ] Data migration tests
- [ ] Performance with large transaction history

