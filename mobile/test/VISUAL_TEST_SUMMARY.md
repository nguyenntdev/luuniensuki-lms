# Unit Tests Visual Summary (T-U1, T-U2, T-U3)

## Test Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile Flutter App Tests                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ T-U1: AuthRepository Tests (12 tests)                    │ │
│  │ Location: test/features/auth/auth_repository_test.dart   │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ ✓ Login Tests (3)                                        │ │
│  │   • Success with valid credentials                       │ │
│  │   • Failure with no internet                             │ │
│  │   • Failure with invalid credentials                     │ │
│  │                                                           │ │
│  │ ✓ Register Tests (3)                                     │ │
│  │   • Success with valid data                              │ │
│  │   • Failure with no internet                             │ │
│  │   • Failure when email exists                            │ │
│  │                                                           │ │
│  │ ✓ Logout Tests (3)                                       │ │
│  │   • Success clearing local data                          │ │
│  │   • Success even when remote fails                       │ │
│  │   • Success when offline                                 │ │
│  │                                                           │ │
│  │ ✓ Token Refresh Tests (3)                                │ │
│  │   • Success refreshing tokens                            │ │
│  │   • Failure when offline                                 │ │
│  │   • Clearing tokens on failure                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ T-U2: Progress Calculation Tests (29 tests)              │ │
│  │ Location: test/features/progress/                        │ │
│  │           progress_calculation_test.dart                 │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ ✓ XP Calculation (7 tests)                               │ │
│  │   • Discovery: 25 XP ⭐                                   │ │
│  │   • Lesson: 50 XP ⭐⭐                                     │ │
│  │   • Mastered: 75 XP ⭐⭐⭐                                 │ │
│  │   • Status-based XP verification                         │ │
│  │                                                           │ │
│  │ ✓ Rank Progression (11 tests)                            │ │
│  │   • Lính Mới (0 XP) → Học Viên (100 XP)                 │ │
│  │   • Thư Sinh (300) → Tri Huyện (600)                    │ │
│  │   • Tiến Sĩ (1000) → Thượng Thư (1500)                  │ │
│  │   • Thái Tử (2100) → Hoàng Đế (2800)                    │ │
│  │   • Sử Quan (3600) - Max Rank 👑                         │ │
│  │                                                           │ │
│  │ ✓ Next Rank & Level Up (7 tests)                         │ │
│  │   • Next rank calculation                                │ │
│  │   • Level up detection                                   │ │
│  │   • Multiple level jumps                                 │ │
│  │                                                           │ │
│  │ ✓ Progress Percentage (4 tests)                          │ │
│  │   • 0% at rank minimum                                   │ │
│  │   • 50% at midpoint                                      │ │
│  │   • 100% just before level up                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ T-U3: Quiz Scoring Tests (24 tests)                      │ │
│  │ Location: test/features/quiz/quiz_scoring_test.dart      │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ ✓ Correct Answer Counting (3 tests)                      │ │
│  │   • All correct ✅✅✅                                    │ │
│  │   • Partial correct ✅❌✅                                │ │
│  │   • All incorrect ❌❌❌                                  │ │
│  │                                                           │ │
│  │ ✓ Pass/Fail Threshold - 80% (7 tests)                   │ │
│  │   • 80% = PASS ✅ (threshold)                            │ │
│  │   • 90% = PASS ✅                                        │ │
│  │   • 70% = FAIL ❌                                        │ │
│  │   • Various question counts (5, 10, 100)                 │ │
│  │                                                           │ │
│  │ ✓ XP Bonuses (4 tests)                                   │ │
│  │   • 100% score: Mastered XP (75) 🏆                      │ │
│  │   • 80-99%: Lesson XP (50) 🎉                            │ │
│  │   • \u003c80%: No bonus XP                                   │ │
│  │                                                           │ │
│  │ ✓ Result Messages & Emojis (4 tests)                     │ │
│  │   • 100%: "Xuất sắc!" 🏆                                 │ │
│  │   • 80-99%: "Tuyệt vời!" 🎉                              │ │
│  │   • 50-79%: "Chưa đạt" 📚                                │ │
│  │   • \u003c50%: "Chưa đạt" 💪                                │ │
│  │                                                           │ │
│  │ ✓ Wrong Answers & Time (6 tests)                         │ │
│  │   • Wrong answer calculation                             │ │
│  │   • Time formatting (125s → 02:05)                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Test Coverage Matrix

| Feature | Tests | Success Cases | Failure Cases | Edge Cases |
|---------|-------|---------------|---------------|------------|
| **Auth Repository** | 12 | ✅ Login<br>✅ Register<br>✅ Logout<br>✅ Refresh | ❌ No Internet<br>❌ Invalid Creds<br>❌ Email Exists | Offline logout<br>Remote fail |
| **Progress Calc** | 29 | ✅ XP Calc<br>✅ Rank Progression<br>✅ Level Up | - | Max rank<br>Between thresholds |
| **Quiz Scoring** | 24 | ✅ Correct Count<br>✅ Pass (≥80%)<br>✅ Perfect (100%) | ❌ Fail (\u003c80%)<br>❌ All Wrong | Time format<br>Partial scores |

## XP System Flow

```
Discovery (25 XP)
      ↓
Lesson Complete (50 XP)
      ↓
Quiz Pass (75 XP)
      ↓
Total: 150 XP per Motif
```

## Rank Progression System

```
0 XP      → Lính Mới      (Level 1)
100 XP    → Học Viên      (Level 2)
300 XP    → Thư Sinh      (Level 3)
600 XP    → Tri Huyện     (Level 4)
1000 XP   → Tiến Sĩ       (Level 5)
1500 XP   → Thượng Thư    (Level 6)
2100 XP   → Thái Tử       (Level 7)
2800 XP   → Hoàng Đế      (Level 8)
3600+ XP  → Sử Quan       (Level 9) 👑
```

## Quiz Scoring Rules

```
Score ≥ 80%  → PASS ✅ → Award XP
Score \u003c 80%  → FAIL ❌ → No XP

Score = 100% → MASTERED 🏆 → 75 XP Bonus
Score ≥ 80%  → PASSED 🎉   → 50 XP Bonus
Score ≥ 50%  → FAILED 📚   → No XP
Score \u003c 50%  → FAILED 💪   → No XP
```

## Mock Dependencies

```
┌──────────────────────────────────┐
│   Auth Repository Tests          │
├──────────────────────────────────┤
│ Mocks:                           │
│ • MockAuthRemoteDataSource       │
│ • MockAuthLocalDataSource        │
│ • MockNetworkInfo                │
└──────────────────────────────────┘
```

## Test Execution Flow

```
1. setUp()
   ├─ Initialize mocks
   ├─ Create repository instance
   └─ Set up test data

2. Test Execution
   ├─ Arrange: Configure mock behavior
   ├─ Act: Execute method under test
   └─ Assert: Verify results

3. Verify Mock Interactions
   ├─ verify() - Method was called
   └─ verifyNever() - Method not called
```

## Key Test Patterns

### Either Pattern (Success/Failure)
```dart
result.fold(
  (failure) => // Handle failure
  (success) => // Handle success
)
```

### Mock Setup
```dart
when(() => mock.method())
  .thenAnswer((_) async => result)
```

### Async Testing
```dart
test('description', () async {
  // Test async methods
  final result = await repository.method();
  expect(result, expectedValue);
})
```

## Quick Commands

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/features/auth/auth_repository_test.dart

# Run with coverage
flutter test --coverage

# Run verbose
flutter test --verbose
```

## Test Statistics

```
┌─────────────────────────────┐
│   Overall Test Summary      │
├─────────────────────────────┤
│ Total Tests:      65        │
│ Auth Tests:       12 (18%)  │
│ Progress Tests:   29 (45%)  │
│ Quiz Tests:       24 (37%)  │
│                             │
│ Expected Time:    ~5 sec    │
│ Coverage Target:  \u003e 80%     │
└─────────────────────────────┘
```

