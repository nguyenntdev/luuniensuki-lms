# Authentication Session Persistence Bug Fix

## Summary
Fixed the authentication session persistence bug in the Flutter app by changing all auth-related Riverpod providers from auto-dispose to keep-alive mode.

## Root Cause
The AuthNotifier and related providers used `@riverpod` which generates `AutoDisposeNotifierProvider`. When users navigated between pages, the provider would get disposed and recreated with an unauthenticated state, causing users to be logged out unexpectedly.

## Solution
Changed all auth-related providers to use `@Riverpod(keepAlive: true)` to prevent auto-disposal and maintain authentication state across navigation.

## Files Modified

### 1. mobile/lib/features/auth/presentation/providers/auth_provider.dart
Changed the following providers to use `@Riverpod(keepAlive: true)`:
- `authRemoteDataSource` (line 21)
- `authLocalDataSource` (line 28)
- `authRepository` (line 39)
- `AuthNotifier` class (line 54)
- `currentUser` (line 343)
- `isAuthenticated` (line 350)
- `isAuthLoading` (line 357)
- `authError` (line 364)

### 2. mobile/lib/core/storage/secure_storage.dart
Changed the following providers to use `@Riverpod(keepAlive: true)`:
- `flutterSecureStorage` (line 105)
- `secureStorage` (line 118)

### 3. mobile/lib/core/storage/hive_storage.dart
Changed the following provider to use `@Riverpod(keepAlive: true)`:
- `hiveStorage` (line 299)

### 4. mobile/lib/core/network/network_info.dart
Changed the following providers to use `@Riverpod(keepAlive: true)`:
- `connectivity` (line 41)
- `networkInfo` (line 47)

Note: `connectivityStatus` and `isConnected` remain auto-dispose as they are stream/future providers.

### 5. mobile/lib/core/network/dio_provider.dart
Changed the following providers to use `@Riverpod(keepAlive: true)`:
- `dio` (line 21)
- `authDio` (line 67)

### 6. mobile/lib/core/network/api_client.dart
Note: These providers were already using `@Riverpod(keepAlive: true)`:
- `dio` (line 251)
- `apiClient` (line 259)

## Next Steps

### Code Generation Required
After these changes, you need to regenerate the Riverpod provider files:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

Or for continuous watching during development:

```bash
cd mobile
flutter pub run build_runner watch --delete-conflicting-outputs
```

## Expected Behavior After Fix
- User authentication state will persist across page navigation
- Users will remain logged in when navigating between different screens
- The auth session will only be cleared on explicit logout or session expiration
- The AuthNotifier will maintain its state throughout the app lifecycle

## Testing
To verify the fix works:
1. Login to the app
2. Navigate to different screens (Home → Profile → Settings, etc.)
3. Verify that the user remains authenticated
4. Check that user data persists across navigation
5. Verify logout still works correctly

