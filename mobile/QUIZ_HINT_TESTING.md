# Quiz Hint System - Testing Guide

## 🧪 Manual Test Cases

### Test Case 1: Hint Button Visibility
**Steps:**
1. Start a quiz with multiple-choice questions (4+ options)
2. Navigate to first question

**Expected:**
- ✅ Hint button appears above question card
- ✅ Shows lightbulb icon (💡)
- ✅ Shows cost "💎 5"
- ✅ Button is enabled if gems >= 5
- ✅ Button text: "Gợi ý" and "Loại bỏ 2 đáp án sai"

---

### Test Case 2: Use Hint Successfully
**Precondition:** User has >= 5 gems

**Steps:**
1. Navigate to multiple-choice question
2. Click hint button [💎 5]

**Expected:**
- ✅ Gems deducted by 5 (check AppBar counter)
- ✅ HintUsedDialog appears with animation
- ✅ Dialog shows lightbulb icon with glow
- ✅ Dialog shows "-5 Gems" in red badge
- ✅ Dialog auto-dismisses after 2 seconds
- ✅ 2 answer options fade out to invisible
- ✅ Correct answer still visible
- ✅ Hint button changes to "Đã sử dụng gợi ý"
- ✅ Hint button is now disabled (gray icon)

---

### Test Case 3: Insufficient Gems
**Precondition:** User has < 5 gems

**Steps:**
1. Navigate to multiple-choice question
2. Click hint button

**Expected:**
- ✅ SnackBar appears with error message
- ✅ Message: "Không đủ gems để sử dụng gợi ý!"
- ✅ No gems deducted
- ✅ No options hidden
- ✅ Hint button remains available but disabled

---

### Test Case 4: Hint Already Used
**Steps:**
1. Use hint on a question successfully
2. Try to click hint button again

**Expected:**
- ✅ Button is disabled
- ✅ Shows "Đã sử dụng gợi ý"
- ✅ Gray icon instead of yellow
- ✅ No action when clicked

---

### Test Case 5: Navigate Between Questions
**Steps:**
1. Use hint on Question 1
2. Navigate to Question 2
3. Navigate back to Question 1

**Expected:**
- ✅ Question 1: Hint remains used, options still hidden
- ✅ Question 2: Hint available (new question)
- ✅ State persists during navigation

---

### Test Case 6: True/False Question
**Steps:**
1. Navigate to True/False question

**Expected:**
- ✅ Hint button does NOT appear
- ✅ Only shows Đúng/Sai buttons

---

### Test Case 7: Fill-in-Blank Question
**Steps:**
1. Navigate to Fill-in-Blank question

**Expected:**
- ✅ Hint button does NOT appear
- ✅ Only shows text input field

---

### Test Case 8: Multiple Choice with < 4 Options
**Steps:**
1. Navigate to multiple-choice with only 2-3 options

**Expected:**
- ✅ Hint button does NOT appear
- ✅ (Not enough options to remove 2)

---

### Test Case 9: Gems Transaction History
**Steps:**
1. Use hint (costs 5 gems)
2. Navigate to Gems Shop → Transaction History

**Expected:**
- ✅ New transaction appears
- ✅ Type: "Sử dụng gợi ý trong quiz"
- ✅ Amount: -5 gems
- ✅ Timestamp: current time

---

### Test Case 10: AppBar Gems Display
**Steps:**
1. Start quiz
2. Observe AppBar

**Expected:**
- ✅ Gems counter visible: 💎 [count]
- ✅ Positioned before hearts display
- ✅ Updates in real-time when gems spent

---

### Test Case 11: Hidden Options Animation
**Steps:**
1. Use hint on question
2. Observe option fade-out

**Expected:**
- ✅ 2 wrong options fade to opacity: 0
- ✅ Height animates to 0
- ✅ Smooth transition (500ms)
- ✅ Remaining options stay visible

---

### Test Case 12: Correct Answer Never Hidden
**Repeat 10 times:**
1. Use hint on same question type
2. Check which options are hidden

**Expected:**
- ✅ Correct answer NEVER hidden
- ✅ Only wrong answers removed
- ✅ Random selection of 2 wrong answers

---

## 🎯 Edge Cases

### Edge Case 1: Spam Click Hint Button
**Steps:**
1. Rapidly click hint button multiple times

**Expected:**
- ✅ Only 1 hint processed
- ✅ Only 5 gems deducted (not 5 × clicks)
- ✅ Button disabled after first use

---

### Edge Case 2: Network Interruption
**Steps:**
1. Use hint
2. Simulate network error during gems deduction

**Expected:**
- ✅ Error handling active
- ✅ Shows error message if transaction fails
- ✅ State rollback if needed

---

### Edge Case 3: Multiple Quizzes
**Steps:**
1. Complete Quiz A with hints used
2. Start Quiz B

**Expected:**
- ✅ Hints reset for Quiz B
- ✅ Each quiz has independent hint state

---

## 📱 Device Testing

Test on:
- [ ] iOS Simulator
- [ ] Android Emulator
- [ ] Physical iOS device
- [ ] Physical Android device
- [ ] Different screen sizes (small, medium, large)
- [ ] Dark mode / Light mode

---

## 🔍 Visual Inspection Checklist

**Hint Button:**
- [ ] Correct spacing and padding
- [ ] Glass container effect visible
- [ ] Border color matches theme
- [ ] Icon color: yellow (available) / gray (used)
- [ ] Text readable and aligned

**HintUsedDialog:**
- [ ] Centered on screen
- [ ] Backdrop blur effect
- [ ] Lightbulb icon has glow
- [ ] "-5 Gems" badge has red color
- [ ] Animations smooth (no jank)

**Hidden Options:**
- [ ] Fade-out smooth
- [ ] No layout shift
- [ ] Remaining options maintain position

**AppBar:**
- [ ] Gems counter visible
- [ ] Updates reflect immediately
- [ ] Proper spacing between elements

---

## 🐛 Known Issues / Limitations

1. Hint only works for multiple-choice with 4+ options
2. Cannot use hint after answering question
3. Hint state resets on app restart (not persisted)
4. No undo for used hint

---

## ✅ Acceptance Criteria

All test cases must pass:
- [x] Hint button appears correctly
- [x] Deducts 5 gems per use
- [x] Hides 2 wrong answers only
- [x] One-time use per question
- [x] Proper animations
- [x] Error handling
- [x] State management
- [x] UI/UX polish

