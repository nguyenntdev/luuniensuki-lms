import 'package:dio/dio.dart';

import '../../constants/api_constants.dart';
import '../../storage/secure_storage.dart';

/// Interceptor that handles authentication token injection for API requests.
///
/// Responsibilities:
/// - Adds Bearer token to Authorization header for authenticated requests
/// - Skips authentication for public endpoints (login, register, refresh)
/// - Works with SecureStorage to retrieve stored tokens
class AuthInterceptor extends Interceptor {
  final SecureStorage _secureStorage;

  AuthInterceptor(this._secureStorage);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth header for public endpoints
    if (_isPublicEndpoint(options.path)) {
      return handler.next(options);
    }

    // Try to get access token
    final accessToken = await _secureStorage.getAccessToken();

    if (accessToken != null && accessToken.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }

    return handler.next(options);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) {
    // Handle 401 errors - token might be expired
    if (err.response?.statusCode == 401) {
      // Token refresh is handled by TokenRefreshInterceptor
      // Just pass the error through here
    }

    return handler.next(err);
  }

  /// Check if the endpoint is public and doesn't require authentication
  bool _isPublicEndpoint(String path) {
    return ApiConstants.isPublicEndpoint(path);
  }
}
