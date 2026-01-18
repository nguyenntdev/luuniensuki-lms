# AuthRepository Unit Tests

## Overview
Comprehensive unit tests for `AuthRepositoryImpl` covering the core authentication methods with various scenarios including success cases, network failures, server errors, and validation errors.

## Test Coverage

### 1. Login Tests (`login()`)
- ✅ **Success case**: Valid credentials return User entity and save tokens
- ✅ **Network failure**: Returns NetworkFailure when offline
- ✅ **Invalid credentials**: Returns AuthFailure with code 'INVALID_CREDENTIALS'
- ✅ **Server error**: Returns ServerFailure with status code 500
- ✅ **Validation error**: Returns ValidationFailure with field-specific errors

### 2. Register Tests (`register()`)
- ✅ **Success case**: Valid data returns User entity
- ✅ **Duplicate email**: Returns AuthFailure with code 'EMAIL_EXISTS' when email already exists (409)
- ✅ **Validation error**: Returns ValidationFailure for invalid input

### 3. Logout Tests (`logout()`)
- ✅ **Success case**: Clears local data and calls remote logout
- ✅ **Server error but still clears local**: Even when server logout fails, local data is still cleared
- ✅ **Offline logout**: Still clears local data when offline

### 4. GetCurrentUser Tests (`getCurrentUser()`)
- ✅ **Online success**: Returns User from remote and caches it
- ✅ **Offline with cache**: Returns cached User when offline
- ✅ **Network error fallback**: Falls back to cache when network request fails
- ✅ **No cache offline**: Returns AuthFailure when offline with no cached user

## Test Structure

```dart
void main() {
  late AuthRepositoryImpl repository;
  late MockAuthRemoteDataSource mockRemoteDataSource;
  late MockAuthLocalDataSource mockLocalDataSource;
  late MockNetworkInfo mockNetworkInfo;

  setUp(() {
    // Initialize mocks and repository
  });

  group('method_name', () {
    test('scenario description', () async {
      // arrange - setup mocks
      // act - call the method
      // assert - verify results
    });
  });
}
```

## Mock Classes
- `MockAuthRemoteDataSource` - Mocks API calls
- `MockAuthLocalDataSource` - Mocks local storage operations
- `MockNetworkInfo` - Mocks network connectivity checks

## Running the Tests

### Run all auth repository tests:
```bash
flutter test test/features/auth/data/repositories/auth_repository_impl_test.dart
```

### Run with coverage:
```bash
flutter test --coverage test/features/auth/data/repositories/auth_repository_impl_test.dart
```

## Dependencies
The tests use:
- `flutter_test` - Flutter testing framework
- `mocktail` - Mocking library (already in pubspec.yaml dev_dependencies)
- `dartz` - For Either type (already in dependencies)

## Important Notes

1. **Code generation required**: The project uses `freezed` and `json_serializable`, so you may need to run:
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

2. **Type casting in tests**: When asserting on specific failure properties (like `statusCode` or `fieldErrors`), cast the failure to its specific type:
   ```dart
   final serverFailure = failure as ServerFailure;
   expect(serverFailure.statusCode, 500);
   ```

3. **Test data**: Uses realistic test data matching the actual DTOs and entities used in the app.

## What's NOT Covered Yet

These methods could be tested in future:
- `refreshToken()`
- `updateProfile()`
- `changePassword()`
- `deleteAccount()`
- `requestPasswordReset()`
- `useStreakFreeze()`
- `getUserStats()`

## Extending the Tests

To add more tests, follow this pattern:

```dart
test('should return expected result when condition occurs', () async {
  // arrange
  when(() => mockDependency.method(any())).thenAnswer((_) async => expectedValue);
  
  // act
  final result = await repository.methodUnderTest(params);
  
  // assert
  expect(result, isA<Right<Failure, SuccessType>>());
  verify(() => mockDependency.method(params)).called(1);
});
```

## Test Results

All tests should pass once the code generation is run successfully. If tests fail, ensure:
1. Generated files exist (.g.dart and .freezed.dart files)
2. All dependencies are installed (`flutter pub get`)
3. No syntax errors in the codebase

