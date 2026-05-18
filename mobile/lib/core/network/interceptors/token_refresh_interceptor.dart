import 'dart:async';

import 'package:dio/dio.dart';

import '../../constants/api_constants.dart';
import '../../errors/exceptions.dart';
import '../../storage/secure_storage.dart';

/// Interceptor that handles automatic token refresh when access token expires.
///
/// Flow:
/// 1. Request fails with 401
/// 2. If not already refreshing, attempt to refresh token
/// 3. If refresh succeeds, retry original request with new token
/// 4. If refresh fails, throw AuthException to trigger logout
class TokenRefreshInterceptor extends Interceptor {
  final Dio _dio;
  final SecureStorage _secureStorage;

  // Track ongoing refresh to prevent multiple simultaneous refreshes
  Completer<bool>? _refreshCompleter;
  bool _isRefreshing = false;

  // Endpoints that should not trigger token refresh
  static const _noRefreshEndpoints = [
    ApiConstants.login,
    ApiConstants.register,
    ApiConstants.refreshToken,
  ];

  TokenRefreshInterceptor(this._dio, this._secureStorage);

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Only handle 401 errors
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    // Don't try to refresh for auth endpoints
    final requestPath = err.requestOptions.path;
    if (_noRefreshEndpoints.any((endpoint) => requestPath.contains(endpoint))) {
      return handler.next(err);
    }

    // Try to refresh the token
    try {
      final refreshed = await _refreshToken();

      if (refreshed) {
        // Retry the original request with new token
        final retryResponse = await _retryRequest(err.requestOptions);
        return handler.resolve(retryResponse);
      } else {
        // Refresh failed, propagate auth error
        return handler.reject(
          DioException(
            requestOptions: err.requestOptions,
            error: const AuthException(
              'Session expired. Please login again.',
              code: 'SESSION_EXPIRED',
              shouldLogout: true,
            ),
            type: DioExceptionType.unknown,
          ),
        );
      }
    } catch (e) {
      // Refresh failed with error
      return handler.reject(
        DioException(
          requestOptions: err.requestOptions,
          error: const AuthException(
            'Session expired. Please login again.',
            code: 'SESSION_EXPIRED',
            shouldLogout: true,
          ),
          type: DioExceptionType.unknown,
        ),
      );
    }
  }

  /// Refresh the access token using the refresh token.
  /// Returns true if refresh was successful.
  Future<bool> _refreshToken() async {
    // If already refreshing, wait for the result
    if (_isRefreshing) {
      return _refreshCompleter?.future ?? Future.value(false);
    }

    _isRefreshing = true;
    _refreshCompleter = Completer<bool>();

    try {
      final refreshToken = await _secureStorage.getRefreshToken();

      if (refreshToken == null || refreshToken.isEmpty) {
        _completeRefresh(false);
        return false;
      }

      // Make refresh request without going through interceptors
      // to avoid infinite loop
      final response = await _dio.post(
        '${ApiConstants.baseUrl}${ApiConstants.refreshToken}',
        options: Options(
          headers: {
            'Authorization': 'Bearer $refreshToken',
          },
        ),
      );

      if (response.statusCode == 200) {
        // Extract new tokens from response
        final data = response.data as Map<String, dynamic>?;

        // The API might return tokens in different formats
        // Check for access_token in body or extract from response
        String? newAccessToken;
        String? newRefreshToken;

        if (data != null) {
          newAccessToken = data['access_token'] as String?;
          newRefreshToken = data['refresh_token'] as String?;
        }

        // If tokens are in cookies, they'll be handled automatically
        // If in response body, save them
        if (newAccessToken != null) {
          await _secureStorage.saveAccessToken(newAccessToken);
        }
        if (newRefreshToken != null) {
          await _secureStorage.saveRefreshToken(newRefreshToken);
        }

        _completeRefresh(true);
        return true;
      }

      _completeRefresh(false);
      return false;
    } catch (e) {
      _completeRefresh(false);
      // Clear tokens on refresh failure
      await _secureStorage.clearTokens();
      return false;
    }
  }

  void _completeRefresh(bool success) {
    _isRefreshing = false;
    _refreshCompleter?.complete(success);
    _refreshCompleter = null;
  }

  /// Retry the original request with the new access token.
  Future<Response<dynamic>> _retryRequest(RequestOptions requestOptions) async {
    final accessToken = await _secureStorage.getAccessToken();

    // Clone the request options and update the auth header
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': accessToken != null ? 'Bearer $accessToken' : null,
      },
      contentType: requestOptions.contentType,
      responseType: requestOptions.responseType,
      validateStatus: requestOptions.validateStatus,
      receiveTimeout: requestOptions.receiveTimeout,
      sendTimeout: requestOptions.sendTimeout,
    );

    return _dio.request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }
}
