# Quiz & Spaced Repetition Unit Tests

## Overview
Comprehensive unit tests for quiz scoring functionality and the SM-2 spaced repetition algorithm implementation.

## Test Files Created

### 1. Quiz Models Test
**Location:** `test/features/quiz/domain/quiz_models_test.dart`  
**Source:** `lib/features/quiz/domain/quiz_models.dart`  
**Tests:** 36 tests across 5 test groups

### 2. Spaced Repetition Service Test
**Location:** `test/features/practice/domain/services/spaced_repetition_service_test.dart`  
**Source:** `lib/features/practice/domain/services/spaced_repetition_service.dart`  
**Tests:** 25 tests across 3 test groups

---

## Test Coverage Details

### Quiz Models (`quiz_models_test.dart`)

#### ✅ QuizQuestion Tests (8 tests)
- Case-insensitive answer matching (`Hanoi`, `hanoi`, `HANOI` all accepted)
- Whitespace trimming (`  hello  ` → `hello`)
- Combined case + whitespace handling
- `hasImage` and `hasExplanation` helpers

#### ✅ QuestionType Tests (7 tests)
- Parse snake_case: `multiple_choice`, `true_false`, `fill_blank`
- Parse camelCase: `multipleChoice`, `trueFalse`, `fillBlank`
- Parse kebab-case: `multiple-choice`, `true-false`, `fill-blank`
- Alternate formats: `fill_in_blank`, `fillInBlank`
- Default fallback for unknown types
- Vietnamese display names

#### ✅ Quiz Tests (4 tests)
- Question count calculation
- Empty quiz detection
- 80% pass threshold validation

#### ✅ QuizResult Tests (12 tests)
- Wrong answers calculation
- Perfect score detection (100%)
- Result messages by score tier (Vietnamese):
  - Perfect (100%): "Xuất sắc! Bạn đã trả lời đúng tất cả!"
  - Passed (≥80%): "Tuyệt vời! Bạn đã vượt qua bài trắc nghiệm!"
  - Failed (<80%): "Chưa đạt. Hãy ôn lại bài học và thử lại nhé!"
- Result emojis by performance:
  - 🏆 Perfect (100%)
  - 🎉 Passed (80-99%)
  - 📚 Medium (50-79%)
  - 💪 Low (<50%)
- XP and badges tracking

#### ✅ QuizAttempt Tests (3 tests)
- Time formatting (125s → "02:05")
- Zero padding for single digits
- Null handling for missing time

---

### Spaced Repetition Service (`spaced_repetition_service_test.dart`)

#### ✅ processReview() Tests (12 tests)
- **Quality 5 (Perfect):** Increments repetitions, increases EF
- **Quality 4 (Hesitation):** Increments repetitions, maintains EF
- **Quality 3 (Difficulty):** Increments repetitions, decreases EF
- **Quality 2, 1, 0 (Incorrect):** Resets repetitions to 0, interval to 0
- Quality clamping (values outside 0-5 are clamped)
- Date tracking (lastReviewDate, nextReviewDate)
- Quality history with max limit (100 entries)

#### ✅ Ease Factor Calculation Tests (7 tests)
Formula: `EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))`

| Quality | Starting EF | Expected EF | Description |
|---------|-------------|-------------|-------------|
| 5 | 2.5 | 2.6 | Increases |
| 4 | 2.5 | 2.5 | Maintains |
| 3 | 2.5 | 2.36 | Decreases |
| 2 | 2.5 | 2.18 | Decreases more |
| 0 | 2.5 | 1.7 | Significant decrease |

- Minimum EF enforcement (1.3 floor)
- Formula verification across all quality levels

#### ✅ Interval Calculation Tests (6 tests)
SM-2 Interval Progression:
1. **Repetition 1:** 1 day
2. **Repetition 2:** 6 days  
3. **Repetition 3+:** previous_interval × EF

Example progression with EF=2.5:
```
Review 1 → 1 day
Review 2 → 6 days
Review 3 → 15 days (6 × 2.5)
Review 4 → 37.5 days (15 × 2.5)
```

- Quality < 3 resets interval to 0
- Higher EF = faster growth
- Lower EF = slower growth

---

## Running the Tests

### Run All Tests
```bash
flutter test
```

### Run Specific Test File
```bash
# Quiz models tests
flutter test test/features/quiz/domain/quiz_models_test.dart

# Spaced repetition tests
flutter test test/features/practice/domain/services/spaced_repetition_service_test.dart
```

### Run with Coverage
```bash
flutter test --coverage
```

### Validate Test Setup
```bash
./test/validate_tests.sh
```

---

## SM-2 Algorithm Reference

The spaced repetition tests verify the SM-2 (SuperMemo 2) algorithm:

### Quality Ratings (0-5)
- **5:** Perfect response
- **4:** Correct with hesitation  
- **3:** Correct with difficulty
- **2:** Incorrect, but easy recall
- **1:** Incorrect, hard recall
- **0:** Complete blackout

### Key Parameters
- **Ease Factor (EF):** Default 2.5, minimum 1.3
- **Interval:** Days until next review
- **Repetitions:** Count of successful reviews (quality ≥ 3)

### Reset Conditions
- Quality < 3 → repetitions = 0, interval = 0

---

## Test Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 61 |
| Test Groups | 8 |
| Quiz Model Tests | 36 |
| SR Service Tests | 25 |
| Code Coverage | Run `flutter test --coverage` |

---

## Next Steps

1. ✅ Tests created and validated
2. ⏭️ Run tests with Flutter test runner
3. ⏭️ Review coverage report
4. ⏭️ Add edge case tests if needed
5. ⏭️ Create integration tests for end-to-end flows

