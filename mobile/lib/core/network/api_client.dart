import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:path_provider/path_provider.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../constants/api_constants.dart';
import '../errors/exceptions.dart';
import '../storage/secure_storage.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/logging_interceptor.dart';

part 'api_client.g.dart';

/// API Client wrapper for making HTTP requests to the Luuniensuki LMS backend.
///
/// Features:
/// - Automatic token injection via AuthInterceptor
/// - Error handling and conversion via ErrorInterceptor
/// - Request/Response logging in debug mode via LoggingInterceptor
/// - Type-safe request methods with generic response parsing
class ApiClient {
  final Dio _dio;

  ApiClient(this._dio);

  /// GET request
  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        path,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// POST request
  Future<T> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.post<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// PUT request
  Future<T> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.put<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// PATCH request
  Future<T> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.patch<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// DELETE request
  Future<T> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.delete<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// POST request with form data (for file uploads)
  Future<T> postFormData<T>(
    String path, {
    required FormData data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    void Function(int sent, int total)? onSendProgress,
    T Function(dynamic json)? parser,
  }) async {
    try {
      final response = await _dio.post<dynamic>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options ?? Options(contentType: 'multipart/form-data'),
        cancelToken: cancelToken,
        onSendProgress: onSendProgress,
      );
      return _handleResponse<T>(response, parser);
    } on DioException catch (e) {
      throw _extractException(e);
    }
  }

  /// Handle response and parse if parser is provided
  T _handleResponse<T>(Response<dynamic> response, T Function(dynamic json)? parser) {
    final data = response.data;

    if (parser != null) {
      return parser(data);
    }

    // If no parser and T is dynamic or Object, return data as-is
    if (T == dynamic || T == Object) {
      return data as T;
    }

    // Try to cast directly
    if (data is T) {
      return data;
    }

    throw ServerException(
      message: 'Failed to parse response: expected $T but got ${data.runtimeType}',
    );
  }

  /// Extract our custom exception from DioException
  Exception _extractException(DioException error) {
    // If our ErrorInterceptor already attached a custom exception
    if (error.error is Exception) {
      return error.error as Exception;
    }

    // Fallback for unhandled cases
    return ServerException(
      message: error.message ?? 'An error occurred',
      statusCode: error.response?.statusCode,
    );
  }

  /// Get the underlying Dio instance for advanced usage
  Dio get dio => _dio;
}

/// Persistent cookie jar for session persistence across app restarts
PersistCookieJar? _persistCookieJar;

/// Initialize the persistent cookie jar - call this in main() before runApp
Future<void> initPersistCookieJar() async {
  if (_persistCookieJar != null) return;

  final directory = await getApplicationDocumentsDirectory();
  final cookiePath = '${directory.path}/.cookies/';
  _persistCookieJar = PersistCookieJar(
    ignoreExpires: true,
    storage: FileStorage(cookiePath),
  );
}

/// Get the cookie jar - returns persistent jar if initialized, otherwise temporary jar
CookieJar get cookieJar => _persistCookieJar ?? CookieJar();

/// Create and configure the Dio instance (synchronous - cookie jar must be initialized first)
Dio createDio(SecureStorage secureStorage) {
  // Use the pre-initialized persistent cookie jar
  final cookieJarInstance = cookieJar;

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
      validateStatus: (status) {
        // Only accept success status codes (2xx)
        // Let Dio throw exceptions for 4xx and 5xx so we can handle them properly
        return status != null && status >= 200 && status < 300;
      },
    ),
  );

  // Add interceptors in order:
  // 1. Cookie Manager - handles httpOnly cookies automatically with persistent storage
  // 2. Auth - adds token to requests (fallback if cookies not available)
  // 3. Logging - logs requests/responses (debug only)
  // NOTE: ErrorInterceptor temporarily removed for debugging
  dio.interceptors.addAll([
    CookieManager(cookieJarInstance),
    AuthInterceptor(secureStorage),
    LoggingInterceptor(),
    // ErrorInterceptor(), // Temporarily disabled for debugging
  ]);

  return dio;
}

/// Provides the configured Dio instance
/// Using keepAlive to prevent rebuilding and losing cookies
@Riverpod(keepAlive: true)
Dio dio(DioRef ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  return createDio(secureStorage);
}

/// Provides the ApiClient instance
/// Using keepAlive to prevent rebuilding
@Riverpod(keepAlive: true)
ApiClient apiClient(ApiClientRef ref) {
  final dioInstance = ref.watch(dioProvider);
  return ApiClient(dioInstance);
}
