import '../../../../core/errors/exceptions.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../../core/storage/secure_storage.dart';
import '../models/auth_dtos.dart';

/// Local data source for authentication-related data.
/// Handles token storage and user caching using secure storage and Hive.
abstract class AuthLocalDataSource {
  /// Save access token to secure storage
  Future<void> saveAccessToken(String token);

  /// Get access token from secure storage
  Future<String?> getAccessToken();

  /// Save refresh token to secure storage
  Future<void> saveRefreshToken(String token);

  /// Get refresh token from secure storage
  Future<String?> getRefreshToken();

  /// Clear all auth tokens
  Future<void> clearTokens();

  /// Cache user data locally
  Future<void> cacheUser(UserDto user);

  /// Get cached user data
  Future<UserDto?> getCachedUser();

  /// Clear cached user data
  Future<void> clearCachedUser();

  /// Check if user has a valid session (has tokens)
  Future<bool> hasValidSession();

  /// Clear all local auth data (tokens + cached user + cookies)
  Future<void> clearAll();

  /// Clear cookies from cookie jar
  Future<void> clearCookies();
}

/// Implementation of AuthLocalDataSource
class AuthLocalDataSourceImpl implements AuthLocalDataSource {
  final SecureStorage _secureStorage;
  final HiveStorage _hiveStorage;

  AuthLocalDataSourceImpl({
    required SecureStorage secureStorage,
    required HiveStorage hiveStorage,
  })  : _secureStorage = secureStorage,
        _hiveStorage = hiveStorage;

  @override
  Future<void> saveAccessToken(String token) async {
    try {
      await _secureStorage.saveAccessToken(token);
    } catch (e) {
      throw CacheException('Failed to save access token', originalError: e);
    }
  }

  @override
  Future<String?> getAccessToken() async {
    try {
      return await _secureStorage.getAccessToken();
    } catch (e) {
      throw CacheException('Failed to get access token', originalError: e);
    }
  }

  @override
  Future<void> saveRefreshToken(String token) async {
    try {
      await _secureStorage.saveRefreshToken(token);
    } catch (e) {
      throw CacheException('Failed to save refresh token', originalError: e);
    }
  }

  @override
  Future<String?> getRefreshToken() async {
    try {
      return await _secureStorage.getRefreshToken();
    } catch (e) {
      throw CacheException('Failed to get refresh token', originalError: e);
    }
  }

  @override
  Future<void> clearTokens() async {
    try {
      await _secureStorage.clearTokens();
    } catch (e) {
      throw CacheException('Failed to clear tokens', originalError: e);
    }
  }

  @override
  Future<void> cacheUser(UserDto user) async {
    try {
      await _hiveStorage.cacheUser(user.toJson());
    } catch (e) {
      throw CacheException('Failed to cache user', originalError: e);
    }
  }

  @override
  Future<UserDto?> getCachedUser() async {
    try {
      final userJson = _hiveStorage.getCachedUser();
      if (userJson == null) return null;

      return UserDto.fromJson(userJson);
    } catch (e) {
      // If parsing fails, clear the cached user and return null
      await clearCachedUser();
      return null;
    }
  }

  @override
  Future<void> clearCachedUser() async {
    try {
      await _hiveStorage.clearUser();
    } catch (e) {
      throw CacheException('Failed to clear cached user', originalError: e);
    }
  }

  @override
  Future<bool> hasValidSession() async {
    try {
      // Check if we have cookies for the API domain
      // CookieManager handles authentication via httpOnly cookies
      final cookies = await cookieJar.loadForRequest(
        Uri.parse('https://lms.histolab.icu'),
      );
      final hasAuthCookie = cookies.any(
        (cookie) => cookie.name == 'luuniensuki_access',
      );
      if (hasAuthCookie) return true;

      // Fallback: check if we have stored tokens
      final accessToken = await _secureStorage.getAccessToken();
      return accessToken != null && accessToken.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<void> clearAll() async {
    try {
      await Future.wait([
        clearTokens(),
        clearCachedUser(),
        clearCookies(),
      ]);
    } catch (e) {
      throw CacheException('Failed to clear all auth data', originalError: e);
    }
  }

  @override
  Future<void> clearCookies() async {
    try {
      await cookieJar.deleteAll();
    } catch (e) {
      // Ignore cookie clearing errors - not critical
    }
  }
}

/// Extension to convert UserDto to JSON for caching
extension UserDtoToJson on UserDto {
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'display_name': displayName,
      'avatar_url': avatarUrl,
      'username': username,
      'role': role,
      'total_xp': totalXp,
      'is_profile_public': isProfilePublic,
      'current_streak': currentStreak,
      'longest_streak': longestStreak,
      'streak_freezes': streakFreezes,
      'created_at': createdAt,
      'last_active_at': lastActiveAt,
    };
  }
}
