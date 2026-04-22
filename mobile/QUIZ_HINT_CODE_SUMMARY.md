## Quiz Hint System - Code Changes Summary

### 🆕 NEW FILE: hint_used_dialog.dart
```dart
// Dialog hiển thị khi sử dụng hint
class HintUsedDialog extends StatefulWidget {
  final int gemsDeducted;  // Số gems đã trừ
  final VoidCallback onDismiss;
  
  // Features:
  // - Scale + fade animations
  // - Lightbulb icon với glow effect
  // - Hiển thị số gems đã trừ
  // - Auto-dismiss sau 2 giây
}
```

### ✏️ MODIFIED: question_card.dart

**Thay đổi:**
```dart
// Before:
class QuestionCard {
  final QuizQuestionDto question;
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;
}

// After:
class QuestionCard {
  final QuizQuestionDto question;
  final String? selectedAnswer;
  final Function(String) onAnswerSelected;
  final Set<String>? hiddenOptions; // ← NEW: Track hidden options
}
```

**Animation cho hidden options:**
```dart
if (isHidden) {
  return AnimatedOpacity(
    opacity: 0.0,
    duration: Duration(milliseconds: 500),
    child: AnimatedContainer(
      duration: Duration(milliseconds: 500),
      height: 0, // Collapse to 0 height
    ),
  );
}
```

### ✏️ MODIFIED: quiz_screen.dart

**1. New Imports:**
```dart
import '../../../gems/presentation/providers/gems_provider.dart';
import '../../../gems/domain/entities/gem_transaction.dart';
import '../widgets/hint_used_dialog.dart';
```

**2. New State Variables:**
```dart
final Map<String, bool> _hintsUsed = {};
final Map<String, Set<String>> _hiddenOptions = {};
int _totalGemsSpentOnHints = 0;
static const int _hintCost = 5;
```

**3. AppBar - Gems Display:**
```dart
// Hiển thị số gems trong AppBar
Container(
  child: Row(
    children: [
      Text('💎'),
      Text('${ref.watch(gemsNotifierProvider).balance}'),
    ],
  ),
)
```

**4. Hint Button:**
```dart
Widget _buildHintButton() {
  return Container(
    // Glass container style
    decoration: BoxDecoration(...),
    child: Row(
      children: [
        // Lightbulb icon
        Icon(Icons.lightbulb_outline),
        // Status text
        Text(hasUsedHint ? 'Đã sử dụng' : 'Gợi ý'),
        // Cost button
        if (!hasUsedHint)
          ElevatedButton(
            child: Text('💎 5'),
            onPressed: _useHint,
          ),
      ],
    ),
  );
}
```

**5. Use Hint Logic:**
```dart
Future<void> _useHint(QuizQuestionDto question) async {
  // 1. Validate
  if (_hintsUsed[question.id] ?? false) return;
  if (!gemsNotifier.canAfford(_hintCost)) return;
  
  // 2. Deduct gems
  await gemsNotifier.spendGems(
    amount: _hintCost,
    type: GemTransactionType.spentHint,
  );
  
  // 3. Find wrong answers
  final wrongOptions = question.options
      .where((opt) => opt != question.correctAnswer)
      .toList();
  
  // 4. Hide 2 random wrong answers
  wrongOptions.shuffle();
  final optionsToHide = wrongOptions.take(2).toSet();
  
  // 5. Update state
  setState(() {
    _hintsUsed[question.id] = true;
    _hiddenOptions[question.id] = optionsToHide;
    _totalGemsSpentOnHints += _hintCost;
  });
  
  // 6. Show dialog
  showDialog(
    context: context,
    builder: (context) => HintUsedDialog(
      gemsDeducted: _hintCost,
      onDismiss: () => Navigator.pop(context),
    ),
  );
}
```

**6. Pass hiddenOptions to QuestionCard:**
```dart
QuestionCard(
  question: currentQuestion,
  selectedAnswer: _answers[currentQuestion.id],
  hiddenOptions: _hiddenOptions[currentQuestion.id], // ← NEW
  onAnswerSelected: (answer) { ... },
)
```

## 🔄 Data Flow

```
User clicks [💎 5] button
         ↓
    _useHint()
         ↓
Check: hasUsedHint? gems >= 5? isMultipleChoice?
         ↓
GemsProvider.spendGems(5)
         ↓
Find wrongOptions (filter correct answer)
         ↓
wrongOptions.shuffle()
         ↓
Take 2 options → _hiddenOptions[questionId]
         ↓
setState() → UI rebuilds
         ↓
QuestionCard receives hiddenOptions
         ↓
Options with opacity: 0, height: 0
         ↓
Show HintUsedDialog
         ↓
Auto-dismiss after 2s
         ↓
Gems display updates (-5 💎)
```

## 🎨 Visual States

**Before Hint:**
```
┌─────────────────────────────────┐
│ 💡 Gợi ý         [💎 5]         │
│    Loại bỏ 2 đáp án sai         │
└─────────────────────────────────┘

A. Answer 1   ✓ visible
B. Answer 2   ✓ visible
C. Answer 3   ✓ visible
D. Answer 4   ✓ visible
```

**After Hint:**
```
┌─────────────────────────────────┐
│ ⚫ Đã sử dụng gợi ý              │
│    2 đáp án sai đã bị loại      │
└─────────────────────────────────┘

A. Answer 1   ✓ visible
B. Answer 2   ✗ faded out
C. Answer 3   ✓ visible
D. Answer 4   ✗ faded out
```

## ✅ Features Completed

1. ✅ Hint button với icon lightbulb
2. ✅ Chi phí 5 gems
3. ✅ Loại bỏ 2 đáp án sai (multiple choice)
4. ✅ Max 1 hint per question
5. ✅ Disable button sau khi dùng
6. ✅ HintUsedDialog animation
7. ✅ Hiển thị gems deducted
8. ✅ Animation fade out wrong answers
9. ✅ Track hintsUsed per question
10. ✅ Track totalGems spent
11. ✅ Tích hợp GemsProvider
12. ✅ GlassContainer style
13. ✅ AppColors theme

## 📊 Metrics Tracked

- `_hintsUsed`: Map<String, bool>
  - Key: questionId
  - Value: true if used

- `_hiddenOptions`: Map<String, Set<String>>
  - Key: questionId
  - Value: Set of hidden option texts

- `_totalGemsSpentOnHints`: int
  - Total gems spent across all hints

