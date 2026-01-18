# 🎯 Quick Reference - Unit Tests

## Files Created

```
✅ test/features/quiz/domain/quiz_models_test.dart (36 tests)
✅ test/features/practice/domain/services/spaced_repetition_service_test.dart (25 tests)
```

## Run Tests

```bash
# All tests
flutter test

# Quiz tests only
flutter test test/features/quiz/domain/quiz_models_test.dart

# Spaced repetition tests only
flutter test test/features/practice/domain/services/spaced_repetition_service_test.dart

# With coverage
flutter test --coverage

# Validate setup
./test/validate_tests.sh
```

## Quiz Test Coverage

| Feature | Tests | Status |
|---------|-------|--------|
| isCorrect() | 5 | ✅ Case-insensitive, whitespace |
| QuestionType.fromString() | 7 | ✅ All formats (snake, camel, kebab) |
| QuizResult | 12 | ✅ Calculations, messages, emojis |
| Quiz | 4 | ✅ Count, threshold (80%) |
| QuizAttempt | 3 | ✅ Time formatting |

## Spaced Repetition Test Coverage

| Feature | Tests | Status |
|---------|-------|--------|
| processReview() | 12 | ✅ Quality 0-5, dates, history |
| Ease Factor | 7 | ✅ Formula, min 1.3 |
| Interval | 6 | ✅ 1→6→EF×, reset on Q<3 |

## Key Formulas

### Ease Factor
```
EF' = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02))
Min: 1.3
```

### Interval Progression
```
Repetition 1: 1 day
Repetition 2: 6 days
Repetition 3+: previous_interval × EF
Reset if quality < 3
```

## Quick Examples

### Quiz Scoring
```dart
✅ "hanoi", "HANOI" → case-insensitive match
✅ "  hello  " → whitespace trimmed
🏆 100% → "Xuất sắc!"
🎉 80%+ → "Tuyệt vời!"
📚 50%+ → "Chưa đạt..."
💪 <50% → "Chưa đạt..."
```

### SM-2 Algorithm
```dart
Q5: EF 2.5→2.6, Interval 1→6→15
Q3: EF 2.5→2.36, Reps +1
Q2: EF 2.5→2.18, Reps→0, Interval→0
```

## Documentation

- 📄 `UNIT_TESTS_SUMMARY.md` - Overview
- 📘 `README_TESTS.md` - Full guide
- 📖 `TEST_EXAMPLES.md` - Visual examples
- ✅ `IMPLEMENTATION_COMPLETE.md` - Summary

## Stats

- **Total:** 61 tests
- **Groups:** 8
- **Coverage:** Quiz models + SR service

---

**Ready to run!** Execute `flutter test` 🚀

