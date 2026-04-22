# Quiz Hint System - Quick Reference

## 🎯 Core Functionality

**What it does:**
- Users spend 5 gems to remove 2 wrong answers in multiple-choice questions

**Where:**
- Quiz screen, above question card

**Restrictions:**
- Only multiple-choice questions with 4+ options
- Max 1 hint per question
- Requires 5 gems balance

---

## 🗂️ File Structure

```
mobile/lib/features/quiz/presentation/
├── screens/
│   └── quiz_screen.dart          ← Modified (hint logic)
└── widgets/
    ├── question_card.dart        ← Modified (hide options)
    └── hint_used_dialog.dart     ← NEW (confirmation)
```

---

## 🔑 Key Code Snippets

### State Variables
```dart
final Map<String, bool> _hintsUsed = {};
final Map<String, Set<String>> _hiddenOptions = {};
int _totalGemsSpentOnHints = 0;
static const int _hintCost = 5;
```

### Use Hint
```dart
await gemsNotifier.spendGems(
  amount: 5,
  type: GemTransactionType.spentHint,
);
```

### Hide Options
```dart
final wrongOptions = question.options
    .where((opt) => opt != correctAnswer)
    .toList()
    ..shuffle();
    
_hiddenOptions[questionId] = wrongOptions.take(2).toSet();
```

---

## 🎨 UI Components

**AppBar:**
```dart
[💎 95] [❤️ 5] [3/10]
 Gems   Hearts Question
```

**Hint Button:**
```dart
Container(
  decoration: BoxDecoration(/* glass style */),
  child: Row([
    Icon(Icons.lightbulb_outline),
    Text('Gợi ý'),
    ElevatedButton(child: '💎 5'),
  ]),
)
```

**Dialog:**
```dart
HintUsedDialog(
  gemsDeducted: 5,
  onDismiss: () => Navigator.pop(context),
)
```

---

## ✅ Checklist for Implementation

**Code:**
- [x] Import GemsProvider
- [x] Add state variables
- [x] Build hint button UI
- [x] Implement _useHint() logic
- [x] Pass hiddenOptions to QuestionCard
- [x] Create HintUsedDialog

**UI:**
- [x] Gems display in AppBar
- [x] Hint button above question
- [x] Fade-out animation
- [x] Glass container style
- [x] Proper colors

**Integration:**
- [x] GemsProvider.spendGems()
- [x] Transaction history
- [x] Balance validation
- [x] Error handling

---

## 🧪 Test Commands

```bash
# Run app
flutter run

# Analyze code
flutter analyze

# Format code
flutter format lib/features/quiz/
```

---

## 🐛 Troubleshooting

**Hint button not showing?**
- Check question type (must be multiple_choice)
- Check options count (must be >= 4)

**Gems not deducting?**
- Check GemsProvider import
- Check spendGems() return value

**Options not hiding?**
- Check hiddenOptions passed to QuestionCard
- Check animation duration

**Dialog not appearing?**
- Check HintUsedDialog import
- Check showDialog() call

---

## 📚 Related Documentation

- `QUIZ_HINT_COMPLETE.md` - Full summary
- `QUIZ_HINT_TESTING.md` - Test cases
- `QUIZ_HINT_CODE_SUMMARY.md` - Code changes

---

## 💡 Tips

1. **Testing:** Use at least 5 gems
2. **Multiple choice:** Need 4+ options
3. **One time:** Can't reuse on same question
4. **Random:** Different wrong answers each time

---

## 🎯 Key Metrics

- **Cost:** 5 gems per hint
- **Removes:** 2 random wrong answers
- **Limit:** 1 hint per question
- **Animation:** 500ms fade-out
- **Dialog:** 2s auto-dismiss

