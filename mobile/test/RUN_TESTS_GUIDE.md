# Quick Guide to Run Unit Tests (T-U1, T-U2, T-U3)

## Prerequisites

Ensure Flutter is installed and in your PATH:
```bash
flutter --version
```

## Quick Start

### 1. Run All Three Test Files
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile

# Run all tests
flutter test test/features/auth/auth_repository_test.dart test/features/progress/progress_calculation_test.dart test/features/quiz/quiz_scoring_test.dart
```

### 2. Run Individual Test Files

**T-U1: Auth Repository Tests**
```bash
flutter test test/features/auth/auth_repository_test.dart
```

**T-U2: Progress Calculation Tests**
```bash
flutter test test/features/progress/progress_calculation_test.dart
```

**T-U3: Quiz Scoring Tests**
```bash
flutter test test/features/quiz/quiz_scoring_test.dart
```

### 3. Run with Verbose Output
```bash
flutter test --verbose test/features/auth/auth_repository_test.dart
```

### 4. Run Specific Test Groups
```bash
# Run only login tests
flutter test test/features/auth/auth_repository_test.dart --name "login"

# Run only XP calculation tests
flutter test test/features/progress/progress_calculation_test.dart --name "XP Calculation"

# Run only threshold tests
flutter test test/features/quiz/quiz_scoring_test.dart --name "Pass/Fail Threshold"
```

## Coverage Report

### Generate Coverage
```bash
flutter test --coverage
```

### View Coverage (macOS/Linux)
```bash
# Install lcov if not already installed
# macOS: brew install lcov
# Linux: sudo apt-get install lcov

# Generate HTML report
genhtml coverage/lcov.info -o coverage/html

# Open in browser
open coverage/html/index.html
```

## Expected Test Results

### T-U1: AuthRepository Tests
```
✓ should return User when login is successful
✓ should return NetworkFailure when there is no internet connection
✓ should return AuthFailure when credentials are invalid
✓ should return User when registration is successful
✓ should return NetworkFailure when there is no internet connection
✓ should return AuthFailure when email already exists
✓ should clear local data when logout is successful
✓ should clear local data even when remote logout fails
✓ should clear local data when offline
✓ should return true when token refresh is successful
✓ should return NetworkFailure when offline
✓ should clear tokens when refresh fails

12 tests passed
```

### T-U2: Progress Calculation Tests
```
✓ should calculate XP for discovery action (25 XP)
✓ should calculate XP for lesson completion (50 XP)
✓ should calculate XP for quiz mastery (75 XP)
... (29 tests total)

29 tests passed
```

### T-U3: Quiz Scoring Tests
```
✓ should count all correct answers
✓ should count partial correct answers
✓ should handle all incorrect answers
✓ should pass with exactly 80% score
... (24 tests total)

24 tests passed
```

## Troubleshooting

### Issue: "Command not found: flutter"
**Solution:** Add Flutter to your PATH or use full path:
```bash
export PATH="$PATH:/path/to/flutter/bin"
```

### Issue: "MissingStubError"
**Solution:** The mock is missing a stub. Check that all methods called in the test have corresponding `when()` stubs.

### Issue: Tests fail with "Bad state"
**Solution:** Ensure setUp() is properly initializing mocks and repository instances.

### Issue: "No tests ran"
**Solution:** Check test file paths are correct and tests are properly structured with `test()` or `group()`.

## Test Development Tips

### Add New Test
```dart
test('should do something specific', () async {
  // Arrange
  when(() => mock.method()).thenAnswer((_) async => result);
  
  // Act
  final result = await repository.method();
  
  // Assert
  expect(result, expectedValue);
  verify(() => mock.method()).called(1);
});
```

### Debug Failing Test
```bash
# Run single test with verbose output
flutter test test/features/auth/auth_repository_test.dart --name "login success" --verbose
```

### Check Test Coverage for Specific File
```bash
flutter test --coverage test/features/auth/auth_repository_test.dart
```

## CI/CD Integration

Add to your CI/CD pipeline:
```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: |
    flutter test test/features/auth/auth_repository_test.dart
    flutter test test/features/progress/progress_calculation_test.dart
    flutter test test/features/quiz/quiz_scoring_test.dart

- name: Generate Coverage
  run: flutter test --coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Performance

Expected test execution times:
- T-U1 (Auth): ~2-3 seconds
- T-U2 (Progress): ~1-2 seconds
- T-U3 (Quiz): ~1-2 seconds
- **Total:** ~4-7 seconds

## Additional Commands

### Run all tests in project
```bash
flutter test
```

### Run tests matching pattern
```bash
flutter test --name "XP"
```

### Run tests excluding pattern
```bash
flutter test --exclude-tags slow
```

### Watch mode (requires fswatch or similar)
```bash
# Install fswatch: brew install fswatch
fswatch -o test/ lib/ | xargs -n1 -I{} flutter test
```

---

For more details, see: `test/UNIT_TESTS_T-U1_T-U2_T-U3_README.md`

