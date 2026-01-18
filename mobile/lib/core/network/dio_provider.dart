import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../constants/api_constants.dart';
import '../storage/secure_storage.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/error_interceptor.dart';
import 'interceptors/logging_interceptor.dart';
import 'interceptors/token_refresh_interceptor.dart';

part 'dio_provider.g.dart';

/// Provides a configured Dio instance for making HTTP requests.
///
/// The Dio client is configured with:
/// - Base URL pointing to the production API
/// - Timeout settings for connection, send, and receive operations
/// - Auth interceptor for token injection
/// - Token refresh interceptor for automatic token refresh on 401
/// - Error interceptor for converting errors to exceptions
/// - Logging interceptor (debug mode only)
@Riverpod(keepAlive: true)
Dio dio(DioRef ref) {
  final secureStorage = ref.watch(secureStorageProvider);

  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      sendTimeout: ApiConstants.sendTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      // Handle cookies for web compatibility
      extra: {
        'withCredentials': true,
      },
    ),
  );

  // Add interceptors in order of execution
  // 1. Auth interceptor - adds bearer token
  dio.interceptors.add(AuthInterceptor(secureStorage));

  // 2. Token refresh interceptor - handles automatic token refresh on 401
  dio.interceptors.add(TokenRefreshInterceptor(dio, secureStorage));

  // 3. Error interceptor - converts Dio errors to custom exceptions
  dio.interceptors.add(ErrorInterceptor());

  // 4. Logging interceptor - only in debug mode
  if (kDebugMode) {
    dio.interceptors.add(
      LoggingInterceptor(
        logRequestHeaders: true,
        logRequestBody: true,
        logResponseHeaders: false,
        logResponseBody: true,
        logErrors: true,
      ),
    );
  }

  return dio;
}

/// Provides a Dio instance specifically for authentication requests.
/// This instance does NOT include the auth interceptor to avoid circular issues.
@Riverpod(keepAlive: true)
Dio authDio(AuthDioRef ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      sendTimeout: ApiConstants.sendTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  // Only error and logging interceptors for auth requests
  dio.interceptors.add(ErrorInterceptor());

  if (kDebugMode) {
    dio.interceptors.add(
      LoggingInterceptor(
        logRequestHeaders: true,
        // Don't log passwords
        logRequestBody: false,
        logResponseHeaders: false,
        logResponseBody: true,
        logErrors: true,
      ),
    );
  }

  return dio;
}
