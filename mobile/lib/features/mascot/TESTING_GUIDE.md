# 🧪 Mascot Feature Testing Guide

## Manual Testing Checklist

### ✅ Explore Screen
**Location**: Main explore screen header

1. Open the app and navigate to Explore screen
2. **Expected**: See animated owl emoji (🦉) in top left corner
3. **Test**: Tap the mascot
4. **Expected**: Speech bubble appears with encouragement message
5. **Test**: Wait 3 seconds
6. **Expected**: Bubble auto-dismisses
7. **Test**: Tap bubble while it's showing
8. **Expected**: Bubble dismisses immediately

**Status**: [ ] Pass [ ] Fail

---

### ✅ Quiz Results - Perfect Score
**Location**: Quiz result screen after completing quiz with 100%

1. Complete a quiz with all correct answers
2. **Expected**: Confetti animation plays
3. **Expected**: After ~500ms, mascot bubble appears
4. **Expected**: Message from `perfectScore` category (e.g., "Hoàn hảo 100%!")
5. **Expected**: Celebrating expression (🎉)

**Status**: [ ] Pass [ ] Fail

---

### ✅ Quiz Results - Pass (Not Perfect)
**Location**: Quiz result screen after passing (but not 100%)

1. Complete a quiz with passing score (e.g., 70%)
2. **Expected**: Confetti animation plays
3. **Expected**: After ~500ms, mascot bubble appears
4. **Expected**: Message from `celebration` category
5. **Expected**: Happy expression (🦉)

**Status**: [ ] Pass [ ] Fail

---

### ✅ Quiz Results - Fail
**Location**: Quiz result screen after failing

1. Complete a quiz with failing score (< 60%)
2. **Expected**: No confetti
3. **Expected**: After ~500ms, mascot bubble appears
4. **Expected**: Message from `motivation` category (e.g., "Đừng nản!")
5. **Expected**: Encouraging expression (💪)

**Status**: [ ] Pass [ ] Fail

---

### ✅ Lesson Completion
**Location**: After completing a lesson

1. Navigate to a lesson and complete it
2. **Expected**: Completion dialog appears
3. **Expected**: After ~500ms, mascot bubble appears
4. **Expected**: Message from `lessonComplete` category
5. **Expected**: Celebrating expression (🎉)

**Status**: [ ] Pass [ ] Fail

---

### ✅ Login Screen
**Location**: Login screen on app start

1. Launch app (ensure logged out)
2. **Expected**: See animated owl emoji (🦉) in center (replacing logo)
3. **Expected**: Mascot bounces and rotates continuously
4. **Expected**: Animation is smooth and non-intrusive

**Status**: [ ] Pass [ ] Fail

---

## Animation Testing

### Bounce Animation
1. Observe mascot on login screen or explore header
2. **Expected**: Mascot moves up slightly, then bounces back down
3. **Expected**: Cycle repeats every ~3 seconds
4. **Expected**: Movement is smooth (60fps)

**Status**: [ ] Pass [ ] Fail

---

### Rotation Animation
1. Observe mascot during animation cycle
2. **Expected**: Slight rotation left and right (~18 degrees)
3. **Expected**: Returns to neutral position
4. **Expected**: Synchronized with bounce

**Status**: [ ] Pass [ ] Fail

---

### Bubble Appearance
1. Trigger any mascot message
2. **Expected**: Bubble scales from 0 to 1 (grows)
3. **Expected**: Opacity fades in simultaneously
4. **Expected**: Animation takes ~300ms
5. **Expected**: Uses easeOutBack curve (slight overshoot)

**Status**: [ ] Pass [ ] Fail

---

## Message Variety Testing

### Random Message Selection
1. Complete same action multiple times (e.g., complete quiz)
2. **Expected**: Different messages each time
3. **Expected**: All messages from appropriate category

**Test Cases**:
- [ ] Completed quiz 3 times - saw different celebration messages
- [ ] Failed quiz 3 times - saw different motivation messages
- [ ] Tapped explore mascot 3 times - saw different encouragement

---

## Edge Cases

### Multiple Bubbles
1. Rapidly trigger multiple mascot messages
2. **Expected**: Only one bubble shows at a time
3. **Expected**: New bubble replaces old one

**Status**: [ ] Pass [ ] Fail

---

### Screen Rotation (Mobile)
1. Show mascot bubble
2. Rotate device
3. **Expected**: Bubble repositions correctly
4. **Expected**: Mascot remains visible

**Status**: [ ] Pass [ ] Fail [ ] N/A (Web only)

---

### Long Messages
1. (Developer) Add a very long message to test
2. **Expected**: Bubble expands vertically
3. **Expected**: Text wraps properly
4. **Expected**: Bubble stays on screen

**Status**: [ ] Pass [ ] Fail

---

### Dismiss Timing
1. Show mascot bubble
2. Don't interact
3. **Expected**: Auto-dismisses after exactly 3 seconds
4. **Test**: Dismiss manually before 3 seconds
5. **Expected**: Dismisses immediately on tap

**Status**: [ ] Pass [ ] Fail

---

## Accessibility Testing

### Screen Reader
1. Enable screen reader (TalkBack/VoiceOver)
2. Trigger mascot message
3. **Expected**: Message is announced
4. **Expected**: Can navigate to bubble
5. **Expected**: Can activate dismiss action

**Status**: [ ] Pass [ ] Fail [ ] Not Tested

---

### High Contrast Mode
1. Enable high contrast mode
2. Show mascot bubble
3. **Expected**: Text is readable
4. **Expected**: Contrast ratio > 4.5:1

**Status**: [ ] Pass [ ] Fail [ ] Not Tested

---

## Performance Testing

### Memory
1. Show and dismiss mascot 50 times
2. **Expected**: No memory leaks
3. **Expected**: Smooth performance throughout

**Status**: [ ] Pass [ ] Fail

---

### Animation Performance
1. Monitor frame rate during animations
2. **Expected**: Maintains 60fps
3. **Expected**: No jank or stuttering

**Status**: [ ] Pass [ ] Fail

---

## Integration Testing

### Navigation
1. Show mascot bubble
2. Navigate to different screen
3. **Expected**: Bubble dismisses automatically
4. **Expected**: No errors in console

**Status**: [ ] Pass [ ] Fail

---

## Bug Reporting Template

```
**Bug Title**: 

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:

**Actual Behavior**:

**Screenshots**:

**Device Info**:
- Platform: iOS / Android / Web
- Version: 
- Screen Size: 

**Console Errors**:
```

---

## Automated Test Scenarios (Future)

```dart
// Widget test example
testWidgets('Mascot bubble appears and dismisses', (tester) async {
  await tester.pumpWidget(MyApp());
  
  // Trigger mascot
  await tester.tap(find.byType(ElevatedButton));
  await tester.pump(Duration(milliseconds: 100));
  
  // Verify bubble appears
  expect(find.byType(MascotBubble), findsOneWidget);
  
  // Wait for auto-dismiss
  await tester.pump(Duration(seconds: 3));
  await tester.pump(Duration(milliseconds: 300)); // Animation
  
  // Verify bubble is gone
  expect(find.byType(MascotBubble), findsNothing);
});
```

---

## Test Summary

**Date Tested**: __________
**Tester**: __________
**Build**: __________

**Results**:
- [ ] All tests passed
- [ ] Some tests failed (see details above)
- [ ] Not all tests completed

**Notes**:
_______________________________________
_______________________________________
_______________________________________


