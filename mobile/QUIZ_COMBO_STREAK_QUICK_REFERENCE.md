# Quiz Combo Streak - Quick Reference

## 🎯 What It Does
Shows a fire emoji combo indicator when user gets 3+ consecutive correct answers in a quiz.

## 📍 Location
**File**: `/mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

## 🔧 Key Components

### State Variable (Line 42)
```dart
int _comboStreak = 0;
```

### Logic (Lines 587-601)
```dart
// On correct answer
if (isCorrect) {
  await soundService.playCorrect();
  setState(() { _comboStreak++; });
}
// On wrong answer
else {
  await soundService.playWrong();
  setState(() { _comboStreak = 0; });
}
```

### UI Indicator (Lines 740-792)
```dart
if (_comboStreak >= 3)
  Positioned(
    top: 20,
    right: 16,
    child: AnimatedContainer(
      // Fire icon + count + "combo" label
      // Orange-to-red gradient
      // 300ms animation
    ),
  ),
```

## 🎨 Visual

```
┌─────────────────────┐
│         🔥 5 combo  │ ← Top-right corner
│                     │
│  Question here...   │
└─────────────────────┘
```

## 🔄 Flow

```
Correct → Streak++
   ↓
Streak >= 3? → Show indicator
   ↓
Wrong → Streak = 0 → Hide indicator
```

## ✅ Testing Quick Checks

1. **Answer 1-2 correctly** → No indicator
2. **Answer 3 correctly** → Indicator appears: "🔥 3 combo"
3. **Answer 4 correctly** → Updates to: "🔥 4 combo"
4. **Answer wrong** → Indicator disappears
5. **Answer 3 more correctly** → Indicator reappears: "🔥 3 combo"

## 🎬 Animation

- **Appear**: 300ms fade-in when streak hits 3
- **Update**: 300ms smooth transition when count changes
- **Disappear**: Instant when wrong answer

## 🎨 Styling

- **Colors**: Orange → Red gradient
- **Shadow**: Orange glow
- **Text**: White, bold
- **Icon**: Fire (🔥)
- **Shape**: Rounded pill

## 💡 Future Enhancements

1. **Bonus XP**: Award extra XP for combo streaks
2. **Sound**: Special sound at milestone combos
3. **Achievements**: "Combo Master" badges
4. **Results**: Show highest combo in quiz results
5. **Analytics**: Track combo stats

## 📊 Behavior

| Streak | Indicator Shown? | Display         |
|--------|------------------|-----------------|
| 0      | ❌ No            | (none)          |
| 1      | ❌ No            | (none)          |
| 2      | ❌ No            | (none)          |
| 3      | ✅ Yes           | 🔥 3 combo      |
| 4      | ✅ Yes           | 🔥 4 combo      |
| 5      | ✅ Yes           | 🔥 5 combo      |
| ...    | ✅ Yes           | 🔥 N combo      |

## 🐛 Common Issues

**Issue**: Indicator doesn't appear
- Check: Is streak >= 3?
- Check: Is `_comboStreak` incrementing?

**Issue**: Indicator doesn't disappear on wrong answer
- Check: Is `_comboStreak` resetting to 0?

**Issue**: Indicator overlaps other UI
- Check: Positioning (top: 20, right: 16)
- Check: Z-index (Stack ordering)

## 📝 Code Summary

**Total Changes:**
- 1 state variable added
- 2 logic blocks updated (correct/wrong answer)
- 1 UI widget added (combo indicator)
- ~60 lines of code total

## 🚀 Deployment Notes

- No backend changes required
- No database migrations
- No API changes
- Client-side only feature
- Compatible with existing quiz system

## 📚 Documentation Files

1. `QUIZ_COMBO_STREAK_IMPLEMENTATION.md` - Full implementation details
2. `QUIZ_COMBO_STREAK_VISUAL_REFERENCE.md` - Visual design reference
3. `QUIZ_COMBO_STREAK_TESTING_GUIDE.md` - Testing procedures
4. `QUIZ_COMBO_STREAK_QUICK_REFERENCE.md` - This file

## 🎓 What's Next?

1. ✅ Test the feature
2. ✅ Verify visual design
3. ✅ Check animations
4. ⬜ Add bonus XP for combos
5. ⬜ Track combo in results
6. ⬜ Create combo achievements

