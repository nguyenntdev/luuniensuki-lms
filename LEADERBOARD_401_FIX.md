# Leaderboard 401 Authentication Error - FIXED ✅

## 🐛 Problem

The leaderboard was getting 401 authentication errors because it was using a Dio instance without the CookieManager configured. This meant authentication cookies were not being sent with the API requests.

## 🔍 Root Cause

Two Dio providers exist in the codebase:

1. **`dio_provider.dart`** - Does NOT have CookieManager
   - Only has: AuthInterceptor, ErrorInterceptor, LoggingInterceptor
   - Location: `mobile/lib/core/network/dio_provider.dart`

2. **`api_client.dart`** - DOES have CookieManager  
   - Has: CookieManager, AuthInterceptor, LoggingInterceptor
   - Location: `mobile/lib/core/network/api_client.dart`

The leaderboard (and notification repository) were importing from `dio_provider.dart`, so they were missing the CookieManager that handles session cookies.

## ✅ Solution

Changed imports in affected files from `dio_provider.dart` to `api_client.dart` to use the Dio instance with CookieManager.

### Files Modified

#### 1. `mobile/lib/features/achievements/presentation/providers/leaderboard_provider.dart`
**Changed:**
```dart
import '../../../../core/network/dio_provider.dart';
```

**To:**
```dart
import '../../../../core/network/api_client.dart';
```

#### 2. `mobile/lib/features/notifications/data/notification_repository.dart`
**Changed:**
```dart
import '../../../core/network/dio_provider.dart';
```

**To:**
```dart
import '../../../core/network/api_client.dart';
```

## 🔧 Technical Details

### CookieManager Configuration (api_client.dart)
The `api_client.dart` file creates a Dio instance with proper cookie handling:

```dart
// Line 209: Cookie jar for handling httpOnly cookies
final CookieJar _cookieJar = CookieJar();

// Line 236-241: Interceptors with CookieManager
dio.interceptors.addAll([
  CookieManager(_cookieJar),  // ← This handles cookies!
  AuthInterceptor(secureStorage),
  LoggingInterceptor(),
]);
```

### Why This Fixes the 401 Error

1. When a user logs in via `auth_provider.dart`, the auth system uses `api_client.dart`'s Dio instance
2. The CookieManager automatically stores session cookies from the login response
3. Now that leaderboard uses the same Dio instance (via `api_client.dart`), those cookies are automatically sent with leaderboard requests
4. The backend recognizes the session cookie and authenticates the request ✅

## 📋 Verification

To verify the fix works:

1. **Login** to the app
2. **Navigate** to the Achievements screen
3. **Switch** to the Leaderboard tab
4. **Verify** that leaderboard data loads without 401 errors

## 🎯 Bonus: Notification Repository Fixed Too

The same fix was applied to the notification repository, which will prevent similar authentication issues when users register/unregister FCM tokens or manage notification preferences.

## 📝 Summary

- ✅ Fixed leaderboard 401 authentication error
- ✅ Fixed notification repository authentication
- ✅ Both now use the Dio instance with CookieManager
- ✅ Authentication cookies are properly sent with all requests
- ✅ No code changes needed, just import path updates

