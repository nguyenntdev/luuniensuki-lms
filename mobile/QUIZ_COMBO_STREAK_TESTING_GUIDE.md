# Quiz Combo Streak - Testing Guide

## Test Scenarios

### Scenario 1: Basic Combo Activation
**Objective**: Verify combo indicator appears at 3 consecutive correct answers

**Steps:**
1. Navigate to any quiz
2. Answer first question correctly
3. Answer second question correctly
4. Answer third question correctly

**Expected Results:**
- ✅ After 1st correct: No combo indicator visible
- ✅ After 2nd correct: No combo indicator visible
- ✅ After 3rd correct: Combo indicator appears showing "🔥 3 combo"
- ✅ Indicator positioned at top-right corner
- ✅ Indicator has orange-to-red gradient background
- ✅ Indicator has fire icon 🔥

### Scenario 2: Combo Increment
**Objective**: Verify combo count increments correctly

**Steps:**
1. Achieve combo streak of 3 (see Scenario 1)
2. Answer 4th question correctly
3. Answer 5th question correctly
4. Continue answering correctly

**Expected Results:**
- ✅ After 4th correct: Indicator updates to "🔥 4 combo"
- ✅ After 5th correct: Indicator updates to "🔥 5 combo"
- ✅ Number updates smoothly with 300ms animation
- ✅ Indicator remains visible throughout

### Scenario 3: Combo Reset on Wrong Answer
**Objective**: Verify combo resets when user answers incorrectly

**Steps:**
1. Achieve combo streak of 5
2. Answer next question incorrectly
3. Observe indicator

**Expected Results:**
- ✅ Indicator shows "🔥 5 combo" before wrong answer
- ✅ After wrong answer, indicator disappears immediately
- ✅ Internal streak counter resets to 0

### Scenario 4: Rebuild Combo After Reset
**Objective**: Verify combo can be rebuilt after reset

**Steps:**
1. Achieve combo of 3+
2. Answer incorrectly to reset
3. Answer correctly 3 times again

**Expected Results:**
- ✅ Combo resets to 0 after wrong answer
- ✅ After 1st correct (post-reset): No indicator
- ✅ After 2nd correct (post-reset): No indicator
- ✅ After 3rd correct (post-reset): Indicator reappears with "🔥 3 combo"

### Scenario 5: First Wrong Answer (No Combo Yet)
**Objective**: Verify wrong answer before combo doesn't show anything

**Steps:**
1. Start quiz
2. Answer first question incorrectly

**Expected Results:**
- ✅ No combo indicator appears
- ✅ Streak remains at 0

### Scenario 6: Alternating Correct/Wrong
**Objective**: Verify combo never activates with alternating answers

**Steps:**
1. Answer correctly
2. Answer incorrectly
3. Answer correctly
4. Answer incorrectly
5. Repeat pattern

**Expected Results:**
- ✅ Combo indicator never appears
- ✅ Streak never reaches 3

### Scenario 7: Complete Quiz with Combo
**Objective**: Verify combo persists until quiz completion

**Steps:**
1. Achieve combo of 3
2. Continue answering correctly for remaining questions
3. Submit quiz

**Expected Results:**
- ✅ Combo indicator updates with each correct answer
- ✅ Final combo count visible before submission
- ✅ Quiz submits normally

### Scenario 8: Visual Position and Layout
**Objective**: Verify indicator doesn't overlap other UI elements

**Steps:**
1. Achieve combo of 3
2. Check indicator position relative to:
   - App bar (question counter, gems, hearts)
   - Hint button
   - Question card
   - Navigation buttons

**Expected Results:**
- ✅ Indicator doesn't overlap app bar elements
- ✅ Indicator doesn't overlap hint button
- ✅ Indicator doesn't overlap question content
- ✅ Indicator is fully visible on screen
- ✅ Indicator has proper padding/margins

### Scenario 9: Animation Smoothness
**Objective**: Verify animations are smooth and pleasant

**Steps:**
1. Achieve combo of 3 (watch appearance animation)
2. Continue to 4, 5, 6 (watch update animation)
3. Answer incorrectly (watch disappearance)

**Expected Results:**
- ✅ Appearance: Smooth fade-in (300ms)
- ✅ Updates: Smooth transition between numbers
- ✅ Disappearance: Instant (no animation needed)

### Scenario 10: Rapid Answer Changes
**Objective**: Verify combo handles rapid answer selection

**Steps:**
1. Quickly select and change answers multiple times
2. Observe combo behavior

**Expected Results:**
- ✅ Combo only counts final selected answer
- ✅ No duplicate increments
- ✅ Indicator updates correctly

## Edge Cases

### Edge Case 1: Resume Quiz with Existing Combo
**Current Behavior**: Combo resets when quiz is resumed
**Test:**
1. Achieve combo of 5
2. Exit quiz (progress saved)
3. Re-enter quiz
4. Resume from saved progress

**Expected**: Combo starts from 0 (no persistence across sessions)

### Edge Case 2: Last Question Correct
**Test:**
1. On last question, have combo of 5
2. Answer correctly
3. Submit quiz

**Expected**: Combo updates to 6 before submission screen

### Edge Case 3: First Question Correct
**Test:**
1. Start quiz
2. Answer first question correctly

**Expected**: Combo = 1, no indicator shown

## Manual Testing Checklist

- [ ] Combo appears at exactly 3 consecutive correct answers
- [ ] Combo increments correctly (4, 5, 6, ...)
- [ ] Combo resets to 0 on wrong answer
- [ ] Indicator disappears when combo resets
- [ ] Combo can be rebuilt after reset
- [ ] Indicator position is correct (top-right)
- [ ] Indicator doesn't overlap other UI elements
- [ ] Gradient background displays correctly
- [ ] Fire icon is visible and correct
- [ ] Text is readable (white on gradient)
- [ ] Animation is smooth (300ms)
- [ ] Works on different screen sizes
- [ ] Works in portrait and landscape
- [ ] No console errors or warnings

## Automated Test Ideas (Future)

```dart
testWidgets('Combo indicator appears after 3 correct answers', (tester) async {
  // Setup quiz with mock questions
  // Answer 2 questions correctly
  // Verify no combo indicator
  // Answer 3rd question correctly
  // Verify combo indicator appears with "3 combo"
});

testWidgets('Combo resets on wrong answer', (tester) async {
  // Achieve combo of 5
  // Answer incorrectly
  // Verify combo indicator disappears
});
```

## Performance Testing

**Memory:**
- [ ] No memory leaks when combo increments
- [ ] AnimatedContainer disposes properly

**Rendering:**
- [ ] Indicator renders without lag
- [ ] Animations don't drop frames

## Cross-Platform Testing

**iOS:**
- [ ] Indicator displays correctly
- [ ] Fire icon renders properly
- [ ] Gradient shows correctly

**Android:**
- [ ] Indicator displays correctly
- [ ] Fire icon renders properly
- [ ] Gradient shows correctly

## Accessibility Testing

**Visual:**
- [ ] High contrast between text and background
- [ ] Text is readable at various font sizes

**Screen Readers:**
- [ ] Indicator can be excluded from screen reader (decorative)

## Regression Testing

Ensure existing quiz functionality still works:
- [ ] Question navigation (previous/next)
- [ ] Answer selection
- [ ] Hearts system (lose heart on wrong answer)
- [ ] Gems system (spend gems on hints)
- [ ] Quiz submission
- [ ] Results screen
- [ ] Progress saving/resuming

## Test Data

**Recommended Test Quiz:**
- Minimum 10 questions
- Mix of easy and hard questions
- Multiple choice format
- Known correct answers

## Bug Reporting Template

```
**Title**: [Combo Streak] Brief description

**Environment:**
- Platform: iOS/Android
- Device: 
- App Version:

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**

**Actual Behavior:**

**Screenshots/Video:**

**Combo Streak State:**
- Current streak count:
- Expected streak count:
```

## Known Limitations

1. Combo doesn't persist across sessions (resets on app close/quiz exit)
2. No backend tracking of combo stats
3. No bonus XP awarded for combos (yet)
4. No achievements for high combos (yet)

## Next Steps After Testing

1. Fix any bugs found
2. Consider adding combo to results screen
3. Implement bonus XP for combos
4. Add combo achievements
5. Track combo analytics

