import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/errors/exceptions.dart';
import '../models/auth_dtos.dart';

/// Remote data source for authentication API calls.
/// Handles all network requests related to authentication.
abstract class AuthRemoteDataSource {
  /// Login with email and password
  Future<LoginResponseDto> login({
    required String email,
    required String password,
  });

  /// Register a new user
  Future<LoginResponseDto> register({
    required String email,
    required String password,
    required String displayName,
  });

  /// Get current authenticated user
  Future<AuthResponseDto> getCurrentUser();

  /// Logout current user
  Future<void> logout();

  /// Refresh access token
  Future<RefreshTokenResponseDto> refreshToken();

  /// Update user profile
  Future<AuthResponseDto> updateProfile({
    String? displayName,
    String? username,
    String? avatarUrl,
    bool? isProfilePublic,
  });

  /// Change password
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });

  /// Request password reset
  Future<void> requestPasswordReset({required String email});

  /// Use streak freeze
  Future<AuthResponseDto> useStreakFreeze();

  /// Get user stats
  Future<StatsDto> getUserStats();
}

/// Implementation of AuthRemoteDataSource using Dio
class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final Dio _dio;

  AuthRemoteDataSourceImpl(this._dio);

  @override
  Future<LoginResponseDto> login({
    required String email,
    required String password,
  }) async {
    try {
      debugPrint('[AUTH_REMOTE] ========== LOGIN START ==========');
      debugPrint('[AUTH_REMOTE] login() called for: $email');
      debugPrint('[AUTH_REMOTE] Base URL: ${_dio.options.baseUrl}');
      debugPrint('[AUTH_REMOTE] Full URL: ${_dio.options.baseUrl}${ApiConstants.login}');
      debugPrint('[AUTH_REMOTE] Request data: {email: $email, password: ***}');

      // Backend expects JSON body with 'email' and 'password' fields
      // Tokens are set as httpOnly cookies by the server
      final response = await _dio.post(
        ApiConstants.login,
        data: {
          'email': email,
          'password': password,
        },
      );

      debugPrint('[AUTH_REMOTE] ========== LOGIN SUCCESS ==========');
      debugPrint('[AUTH_REMOTE] Response status: ${response.statusCode}');
      debugPrint('[AUTH_REMOTE] Response headers: ${response.headers}');
      debugPrint('[AUTH_REMOTE] Response data type: ${response.data.runtimeType}');
      debugPrint('[AUTH_REMOTE] Response data: ${response.data}');

      // The backend returns {"user": {...}, "stats": {...}}
      final data = response.data as Map<String, dynamic>;

      debugPrint('[AUTH_REMOTE] Parsing user from response');
      final user = UserDto.fromJson(data['user'] as Map<String, dynamic>);
      debugPrint('[AUTH_REMOTE] User parsed: ${user.email}');

      debugPrint('[AUTH_REMOTE] Parsing stats from response');
      final stats = StatsDto.fromJson(data['stats'] as Map<String, dynamic>);
      debugPrint('[AUTH_REMOTE] Stats parsed, totalXp: ${stats.totalXp}');

      // Build LoginResponseDto - cookies are handled by CookieManager
      final result = LoginResponseDto(
        accessToken: null, // Handled by cookies
        refreshToken: null, // Handled by cookies
        user: user,
        stats: stats,
      );

      debugPrint('[AUTH_REMOTE] LoginResponseDto created successfully');
      return result;
    } on DioException catch (e) {
      debugPrint('[AUTH_REMOTE] ========== LOGIN DIO ERROR ==========');
      debugPrint('[AUTH_REMOTE] DioException type: ${e.type}');
      debugPrint('[AUTH_REMOTE] DioException message: ${e.message}');
      debugPrint('[AUTH_REMOTE] DioException error: ${e.error}');
      debugPrint('[AUTH_REMOTE] DioException requestUri: ${e.requestOptions.uri}');
      debugPrint('[AUTH_REMOTE] DioException response status: ${e.response?.statusCode}');
      debugPrint('[AUTH_REMOTE] DioException response data: ${e.response?.data}');

      // Handle 401 Unauthorized specifically for login
      if (e.response?.statusCode == 401) {
        final data = e.response?.data;
        debugPrint('[AUTH_REMOTE] 401 response data type: ${data.runtimeType}');
        if (data is Map<String, dynamic>) {
          final error = data['error'] as Map<String, dynamic>?;
          if (error != null) {
            final message = error['message'] as String? ?? 'Email hoặc mật khẩu không đúng';
            debugPrint('[AUTH_REMOTE] Throwing AuthException with message: $message');
            throw AuthException(message, code: 'INVALID_CREDENTIALS');
          }
        }
        debugPrint('[AUTH_REMOTE] Throwing default 401 AuthException');
        throw const AuthException('Email hoặc mật khẩu không đúng', code: 'INVALID_CREDENTIALS');
      }

      debugPrint('[AUTH_REMOTE] Calling _handleDioError');
      throw _handleDioError(e);
    } catch (e, stackTrace) {
      debugPrint('[AUTH_REMOTE] ========== LOGIN UNEXPECTED ERROR ==========');
      debugPrint('[AUTH_REMOTE] Error type: ${e.runtimeType}');
      debugPrint('[AUTH_REMOTE] Error: $e');
      debugPrint('[AUTH_REMOTE] StackTrace: $stackTrace');
      rethrow;
    }
  }

  @override
  Future<LoginResponseDto> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    try {
      debugPrint('[AUTH_REMOTE] register() called for: $email');
      debugPrint('[AUTH_REMOTE] POST ${ApiConstants.register}');

      // Backend expects JSON body
      // Tokens are set as httpOnly cookies by the server
      final response = await _dio.post(
        ApiConstants.register,
        data: {
          'email': email,
          'password': password,
          'display_name': displayName,
        },
      );

      debugPrint('[AUTH_REMOTE] Register response status: ${response.statusCode}');
      debugPrint('[AUTH_REMOTE] Register response data: ${response.data}');

      // The backend returns {"user": {...}, "stats": {...}}
      final data = response.data as Map<String, dynamic>;

      // Build LoginResponseDto - cookies are handled by CookieManager
      return LoginResponseDto(
        accessToken: null, // Handled by cookies
        refreshToken: null, // Handled by cookies
        user: UserDto.fromJson(data['user'] as Map<String, dynamic>),
        stats: StatsDto.fromJson(data['stats'] as Map<String, dynamic>),
      );
    } on DioException catch (e) {
      debugPrint('[AUTH_REMOTE] Register DioException: ${e.type}');
      debugPrint('[AUTH_REMOTE] Register DioException message: ${e.message}');
      debugPrint('[AUTH_REMOTE] Register DioException response: ${e.response?.data}');
      debugPrint('[AUTH_REMOTE] Register DioException status: ${e.response?.statusCode}');

      // Handle specific error codes
      final statusCode = e.response?.statusCode;
      final data = e.response?.data;

      if (data is Map<String, dynamic>) {
        final error = data['error'] as Map<String, dynamic>?;
        if (error != null) {
          final code = error['code'] as String? ?? 'UNKNOWN';
          final message = error['message'] as String? ?? 'Đăng ký thất bại';

          if (statusCode == 409 || code == 'EMAIL_EXISTS') {
            throw ServerException(message: 'Email đã được sử dụng', code: code, statusCode: statusCode);
          }
          throw AuthException(message, code: code);
        }
      }

      throw _handleDioError(e);
    } catch (e, stackTrace) {
      debugPrint('[AUTH_REMOTE] Register unexpected error: $e');
      debugPrint('[AUTH_REMOTE] Register StackTrace: $stackTrace');
      rethrow;
    }
  }

  @override
  Future<AuthResponseDto> getCurrentUser() async {
    try {
      final response = await _dio.get(ApiConstants.me);
      return AuthResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _dio.post(ApiConstants.logout);
    } on DioException catch (e) {
      // Ignore logout errors - we'll clear local state anyway
      if (e.response?.statusCode != 401) {
        throw _handleDioError(e);
      }
    }
  }

  @override
  Future<RefreshTokenResponseDto> refreshToken() async {
    try {
      final response = await _dio.post(ApiConstants.refreshToken);
      return RefreshTokenResponseDto.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<AuthResponseDto> updateProfile({
    String? displayName,
    String? username,
    String? avatarUrl,
    bool? isProfilePublic,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (displayName != null) data['display_name'] = displayName;
      if (username != null) data['username'] = username;
      if (avatarUrl != null) data['avatar_url'] = avatarUrl;
      if (isProfilePublic != null) data['is_profile_public'] = isProfilePublic;

      final response = await _dio.patch(
        ApiConstants.userProfile,
        data: data,
      );

      return AuthResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _dio.post(
        '${ApiConstants.userProfile}/change-password',
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<void> requestPasswordReset({required String email}) async {
    try {
      await _dio.post(
        '${ApiConstants.apiPath}/auth/forgot-password',
        data: {'email': email},
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<AuthResponseDto> useStreakFreeze() async {
    try {
      final response = await _dio.post(
        '${ApiConstants.userProfile}/use-streak-freeze',
      );
      return AuthResponseDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<StatsDto> getUserStats() async {
    try {
      final response = await _dio.get(ApiConstants.userStats);
      return StatsDto.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Convert DioException to our custom exceptions
  Exception _handleDioError(DioException error) {
    // If error already has our custom exception attached
    if (error.error is Exception) {
      return error.error as Exception;
    }

    final response = error.response;
    final statusCode = response?.statusCode;
    final data = response?.data;

    // Try to parse error from response
    if (data != null && data is Map<String, dynamic>) {
      try {
        return ServerException.fromJson(data, statusCode: statusCode);
      } catch (_) {
        // Fall through
      }
    }

    // Handle by status code
    switch (statusCode) {
      case 400:
        return ServerException(
          message: _extractMessage(data) ?? 'Bad request',
          code: 'BAD_REQUEST',
          statusCode: statusCode,
        );
      case 401:
        return const AuthException(
          'Invalid email or password',
          code: 'INVALID_CREDENTIALS',
        );
      case 403:
        return ForbiddenException(
          _extractMessage(data) ?? 'Access denied',
        );
      case 404:
        return NotFoundException(
          _extractMessage(data) ?? 'Resource not found',
        );
      case 409:
        return ServerException(
          message: _extractMessage(data) ?? 'Email already registered',
          code: 'CONFLICT',
          statusCode: statusCode,
        );
      case 422:
        return ValidationException(
          _extractMessage(data) ?? 'Validation failed',
        );
      case 429:
        return const ServerException(
          message: 'Too many requests. Please try again later.',
          code: 'RATE_LIMIT',
          statusCode: 429,
        );
      case 500:
      case 502:
      case 503:
      case 504:
        return const ServerException(
          message: 'Server error. Please try again later.',
          code: 'SERVER_ERROR',
          statusCode: 500,
        );
      default:
        if (error.type == DioExceptionType.connectionTimeout ||
            error.type == DioExceptionType.receiveTimeout ||
            error.type == DioExceptionType.sendTimeout) {
          return const NetworkException('Connection timed out');
        }
        if (error.type == DioExceptionType.connectionError) {
          return const NetworkException('No internet connection');
        }
        return ServerException(
          message: error.message ?? 'An unknown error occurred',
          statusCode: statusCode,
        );
    }
  }

  /// Extract error message from response data
  String? _extractMessage(dynamic data) {
    if (data == null) return null;
    if (data is String) return data;
    if (data is Map<String, dynamic>) {
      // Check nested error object (our API format)
      final error = data['error'];
      if (error is Map<String, dynamic>) {
        return error['message'] as String?;
      }
      // Check detail (FastAPI format)
      final detail = data['detail'];
      if (detail is String) return detail;
      // Check message directly
      return data['message'] as String?;
    }
    return null;
  }
}
