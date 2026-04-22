import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'secure_storage.g.dart';

/// Abstract interface for secure storage operations.
/// Allows for easy mocking in tests.
abstract class SecureStorage {
  /// Save access token
  Future<void> saveAccessToken(String token);

  /// Get access token
  Future<String?> getAccessToken();

  /// Save refresh token
  Future<void> saveRefreshToken(String token);

  /// Get refresh token
  Future<String?> getRefreshToken();

  /// Clear all auth tokens
  Future<void> clearTokens();

  /// Save arbitrary key-value pair
  Future<void> write(String key, String value);

  /// Read value for key
  Future<String?> read(String key);

  /// Delete a specific key
  Future<void> delete(String key);

  /// Check if a key exists
  Future<bool> containsKey(String key);

  /// Clear all stored data
  Future<void> clearAll();
}

/// Implementation of SecureStorage using flutter_secure_storage
class SecureStorageImpl implements SecureStorage {
  final FlutterSecureStorage _storage;

  // Storage keys
  static const _accessTokenKey = 'luuniensuki_access_token';
  static const _refreshTokenKey = 'luuniensuki_refresh_token';

  SecureStorageImpl(this._storage);

  @override
  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }

  @override
  Future<String?> getAccessToken() async {
    return _storage.read(key: _accessTokenKey);
  }

  @override
  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  @override
  Future<String?> getRefreshToken() async {
    return _storage.read(key: _refreshTokenKey);
  }

  @override
  Future<void> clearTokens() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
    ]);
  }

  @override
  Future<void> write(String key, String value) async {
    await _storage.write(key: key, value: value);
  }

  @override
  Future<String?> read(String key) async {
    return _storage.read(key: key);
  }

  @override
  Future<void> delete(String key) async {
    await _storage.delete(key: key);
  }

  @override
  Future<bool> containsKey(String key) async {
    return _storage.containsKey(key: key);
  }

  @override
  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}

/// Provides the FlutterSecureStorage instance with Android-specific options
@Riverpod(keepAlive: true)
FlutterSecureStorage flutterSecureStorage(FlutterSecureStorageRef ref) {
  return const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock,
    ),
  );
}

/// Provides the SecureStorage implementation
@Riverpod(keepAlive: true)
SecureStorage secureStorage(SecureStorageRef ref) {
  final storage = ref.watch(flutterSecureStorageProvider);
  return SecureStorageImpl(storage);
}
