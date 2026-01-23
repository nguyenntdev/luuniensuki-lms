# Login Session Persistence Fix

## Problem
The Flutter mobile app was using an in-memory `CookieJar` that gets cleared when the app restarts, causing users to have to login again every time they open the app.

## Solution Implemented
Replaced the in-memory `CookieJar` with `PersistCookieJar` to save authentication cookies to persistent storage on disk.

## Files Modified

### 1. `mobile/lib/core/network/api_client.dart`

**Changes:**
- Added import for `path_provider` package
- Removed unused imports (`flutter/foundation.dart`, `error_interceptor.dart`)
- Replaced `final CookieJar _cookieJar = CookieJar();` with persistent cookie jar implementation
- Added `PersistCookieJar? _persistCookieJar;` - nullable global variable for persistent cookie jar
- Added `getPersistCookieJar()` function - lazy initialization of persistent cookie jar with file storage
- Modified `createDio()` to be async and initialize persistent cookie jar before creating Dio instance
- Updated `dio` provider to return `Future<Dio>` instead of `Dio`
- Updated `apiClient` provider to return `Future<ApiClient>` and await `dioProvider.future`
- Kept `cookieJar` getter for backward compatibility (used by auth_local_datasource.dart)

**Key Implementation Details:**
```dart
// Persistent cookie jar with lazy initialization
PersistCookieJar? _persistCookieJar;

Future<PersistCookieJar> getPersistCookieJar() async {
  if (_persistCookieJar != null) return _persistCookieJar!;
  
  final directory = await getApplicationDocumentsDirectory();
  final cookiePath = '${directory.path}/.cookies/';
  _persistCookieJar = PersistCookieJar(
    ignoreExpires: true,
    storage: FileStorage(cookiePath),
  );
  return _persistCookieJar!;
}
```

### 2. `mobile/lib/main.dart`

**Changes:**
- Added import for `core/network/api_client.dart`
- Added initialization of persistent cookie jar before running the app:
  ```dart
  void main() async {
    WidgetsFlutterBinding.ensureInitialized();
    
    // Initialize Hive storage
    await HiveStorage.init();
    
    // Initialize persistent cookie jar for session persistence across app restarts
    await getPersistCookieJar();
    
    runApp(const ProviderScope(child: LuuniensukiApp()));
  }
  ```

### 3. `mobile/lib/features/auth/presentation/providers/auth_provider.dart`

**Changes:**
- Updated provider signatures to handle async Dio and ApiClient providers
- Changed `authRemoteDataSource` provider to return `Future<AuthRemoteDataSource>`
- Changed `authRepository` provider to return `Future<AuthRepository>`
- Updated `AuthNotifier._repository` getter to be async: `Future<AuthRepository> get _repository async`
- Updated all methods using `_repository` to await it first:
  - `initialize()`, `login()`, `register()`, `logout()`, `refreshUser()`
  - `updateProfile()`, `changePassword()`, `useStreakFreeze()`

### 4. Generated Files (Auto-updated by build_runner)
- `mobile/lib/core/network/api_client.g.dart`
- `mobile/lib/features/auth/presentation/providers/auth_provider.g.dart`

## Dependencies
All required dependencies were already present in `pubspec.yaml`:
- ✅ `cookie_jar: ^4.0.8` (includes `PersistCookieJar`)
- ✅ `path_provider: ^2.1.1`

## Testing
1. Code generation completed successfully with `flutter pub run build_runner build`
2. Static analysis passed with only expected deprecation warnings
3. Key areas to verify in manual testing:
   - Users remain logged in after closing and reopening the app
   - Cookies persist across app restarts
   - Logout properly clears cookies
   - Session expiration handling still works correctly

## Technical Details

### Cookie Storage Location
Cookies are stored at: `{ApplicationDocumentsDirectory}/.cookies/`

### Cookie Jar Configuration
- `ignoreExpires: true` - Keeps cookies even if they expire (server-side session management)
- `storage: FileStorage(cookiePath)` - Persists cookies to disk

### Backward Compatibility
The `cookieJar` getter is maintained for use by `auth_local_datasource.dart` which:
- Checks for valid session by loading cookies for the API domain
- Clears cookies on logout via `cookieJar.deleteAll()`

## Benefits
1. **Improved UX**: Users no longer need to login every time they open the app
2. **Session Persistence**: Authentication cookies survive app restarts
3. **Minimal Changes**: Implementation required changes to only 3 source files
4. **No New Dependencies**: Uses existing packages already in the project

## Next Steps
1. Test the implementation on real devices
2. Verify cookie persistence works correctly
3. Ensure logout properly clears persistent cookies
4. Monitor for any session-related issues

## Related Documentation
- Previous fix: `AUTH_SESSION_FIX_SUMMARY.md` - Fixed in-memory session loss during navigation
- This fix: Session persistence across app restarts

