# Test Examples - Visual Reference

## Quiz Scoring Tests

### ✅ Case-Insensitive Matching
```dart
// Question: "Capital of Vietnam?"
// Correct Answer: "Hanoi"

✅ "hanoi"   → CORRECT
✅ "HANOI"   → CORRECT
✅ "HaNoi"   → CORRECT
✅ "Hanoi"   → CORRECT
❌ "Saigon"  → INCORRECT
```

### ✅ Whitespace Trimming
```dart
// Correct Answer: "hello"

✅ "  hello  "  → CORRECT
✅ "hello   "   → CORRECT
✅ "   hello"   → CORRECT
✅ "\thello\n"  → CORRECT
```

### ✅ QuestionType Parsing
```dart
QuestionType.fromString('multiple_choice')  → multipleChoice
QuestionType.fromString('multipleChoice')   → multipleChoice
QuestionType.fromString('multiple-choice')  → multipleChoice
QuestionType.fromString('MULTIPLE_CHOICE')  → multipleChoice

QuestionType.fromString('fill_in_blank')   → fillBlank
QuestionType.fromString('fillInBlank')      → fillBlank
QuestionType.fromString('fill-in-blank')    → fillBlank

QuestionType.fromString('unknown')          → multipleChoice (default)
```

### ✅ Result Messages & Emojis
```dart
// Perfect Score (100%)
resultMessage: "Xuất sắc! Bạn đã trả lời đúng tất cả!"
resultEmoji: 🏆

// Passed (80-99%)
resultMessage: "Tuyệt vời! Bạn đã vượt qua bài trắc nghiệm!"
resultEmoji: 🎉

// Failed but >= 50%
resultMessage: "Chưa đạt. Hãy ôn lại bài học và thử lại nhé!"
resultEmoji: 📚

// Failed < 50%
resultMessage: "Chưa đạt. Hãy ôn lại bài học và thử lại nhé!"
resultEmoji: 💪
```

### ✅ Quiz Result Calculations
```dart
totalQuestions: 10
correctAnswers: 8
wrongAnswers: 2        // calculated: 10 - 8
percentage: 80
passed: true           // 80% >= passThreshold (80%)
isPerfect: false       // percentage != 100
```

### ✅ Time Formatting
```dart
timeTakenSeconds: 125  → formattedTime: "02:05"
timeTakenSeconds: 65   → formattedTime: "01:05"
timeTakenSeconds: null → formattedTime: null
```

---

## Spaced Repetition (SM-2) Tests

### ✅ Quality Ratings Impact

```dart
Initial State:
  EF: 2.5
  Interval: 0
  Repetitions: 0

Quality 5 (Perfect):
  EF: 2.6 ↑
  Interval: 1 day
  Repetitions: 1 ↑

Quality 4 (Hesitation):
  EF: 2.5 (same)
  Interval: 1 day
  Repetitions: 1 ↑

Quality 3 (Difficulty):
  EF: 2.36 ↓
  Interval: 1 day
  Repetitions: 1 ↑

Quality 2 (Incorrect):
  EF: 2.18 ↓
  Interval: 0 (reset)
  Repetitions: 0 (reset)

Quality 0 (Blackout):
  EF: 1.7 ↓↓
  Interval: 0 (reset)
  Repetitions: 0 (reset)
```

### ✅ Ease Factor Formula
```
EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))

Examples:
Quality 5: 2.5 + (0.1 - 0×0.08) = 2.5 + 0.1 = 2.6
Quality 4: 2.5 + (0.1 - 1×0.10) = 2.5 + 0.0 = 2.5
Quality 3: 2.5 + (0.1 - 2×0.12) = 2.5 - 0.14 = 2.36
Quality 2: 2.5 + (0.1 - 3×0.14) = 2.5 - 0.32 = 2.18
Quality 0: 2.5 + (0.1 - 5×0.18) = 2.5 - 0.80 = 1.7

Minimum EF: 1.3 (enforced)
```

### ✅ Interval Progression (EF=2.5)
```dart
Review 1 (Quality 4):
  Repetitions: 0 → 1
  Interval: 0 → 1 day
  Next Review: Tomorrow

Review 2 (Quality 4):
  Repetitions: 1 → 2
  Interval: 1 → 6 days
  Next Review: In 6 days

Review 3 (Quality 4):
  Repetitions: 2 → 3
  Interval: 6 → 15 days   (6 × 2.5)
  Next Review: In 15 days

Review 4 (Quality 4):
  Repetitions: 3 → 4
  Interval: 15 → 37.5 days   (15 × 2.5, rounded to 38)
  Next Review: In 38 days

Review 5 (Quality 2):  ← INCORRECT
  Repetitions: 4 → 0 (RESET)
  Interval: 37.5 → 0 (RESET)
  Next Review: Now
```

### ✅ EF Impact on Interval Growth

```dart
High EF (3.0):
  Review 1: 1 day
  Review 2: 6 days
  Review 3: 18 days   (6 × 3.0)
  Review 4: 54 days   (18 × 3.0)
  Review 5: 162 days  (54 × 3.0)

Normal EF (2.5):
  Review 1: 1 day
  Review 2: 6 days
  Review 3: 15 days   (6 × 2.5)
  Review 4: 37.5 days (15 × 2.5)
  Review 5: 93.75 days (37.5 × 2.5)

Low EF (1.5):
  Review 1: 1 day
  Review 2: 6 days
  Review 3: 9 days    (6 × 1.5)
  Review 4: 13.5 days (9 × 1.5)
  Review 5: 20.25 days (13.5 × 1.5)
```

### ✅ Quality History Management
```dart
Initial: []

After Review 1 (Q=4): [4]
After Review 2 (Q=5): [4, 5]
After Review 3 (Q=3): [4, 5, 3]
...
After 100 reviews: [q1, q2, ..., q100]
After 110 reviews: [q11, q12, ..., q110]  // First 10 trimmed

Maximum history length: 100 entries
```

### ✅ Reset Behavior
```dart
Before (Quality < 3):
  EF: 2.5
  Interval: 15 days
  Repetitions: 5
  Status: "Review in 15 days"

After (Quality 2):
  EF: 2.18 (adjusted by formula)
  Interval: 0 days ← RESET
  Repetitions: 0 ← RESET
  Status: "Review now"
```

---

## Test Validation

Run the validation script to verify test setup:

```bash
./test/validate_tests.sh
```

Expected output:
```
================================
Test File Validation
================================

✓ Checking test files...
  ✅ quiz_models_test.dart exists
  ✅ spaced_repetition_service_test.dart exists

✓ Checking source files...
  ✅ quiz_models.dart exists
  ✅ spaced_repetition_service.dart exists
  ✅ review_item.dart exists

✓ Test file statistics...
  📊 Quiz models tests: 36
  📊 Spaced repetition tests: 25
  📊 Total tests: 61

✓ Test groups...
  📦 Quiz test groups: 5
  📦 Spaced repetition groups: 3

================================
Validation Complete!
================================
```

