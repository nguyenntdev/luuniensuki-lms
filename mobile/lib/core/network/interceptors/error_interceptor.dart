import 'dart:io';

import 'package:dio/dio.dart';

import '../../errors/exceptions.dart';

/// Interceptor that converts Dio errors to custom exceptions.
/// Handles different error types and extracts meaningful error messages.
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final exception = _convertToException(err);

    // Create a new DioException with our custom exception attached
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        response: err.response,
        type: err.type,
        error: exception,
        message: exception.toString(),
      ),
    );
  }

  /// Convert DioException to our custom exception types
  Exception _convertToException(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return TimeoutException(
          'Connection timed out. Please check your internet connection.',
          timeout: error.requestOptions.connectTimeout,
        );

      case DioExceptionType.connectionError:
        return const NetworkException(
          'Unable to connect to server. Please check your internet connection.',
        );

      case DioExceptionType.badCertificate:
        return const NetworkException(
          'Security certificate error. Please update the app.',
        );

      case DioExceptionType.badResponse:
        return _handleBadResponse(error);

      case DioExceptionType.cancel:
        return const NetworkException('Request was cancelled.');

      case DioExceptionType.unknown:
        if (error.error is SocketException) {
          return const NetworkException(
            'No internet connection. Please check your network.',
          );
        }
        return ServerException(
          message: error.message ?? 'An unknown error occurred',
        );
    }
  }

  /// Handle HTTP error responses
  Exception _handleBadResponse(DioException error) {
    final response = error.response;
    final statusCode = response?.statusCode;
    final data = response?.data;

    // Try to parse error from response body
    if (data != null && data is Map<String, dynamic>) {
      try {
        return ServerException.fromJson(data, statusCode: statusCode);
      } catch (_) {
        // Fall through to status code handling
      }
    }

    // Handle by status code
    switch (statusCode) {
      case 400:
        return _handleBadRequest(data);

      case 401:
        return const AuthException(
          'Session expired. Please login again.',
          code: 'SESSION_EXPIRED',
          shouldLogout: true,
        );

      case 403:
        return ForbiddenException(
          _extractMessage(data) ?? 'You don\'t have permission to access this resource.',
        );

      case 404:
        return NotFoundException(
          _extractMessage(data) ?? 'Resource not found.',
        );

      case 409:
        return ServerException(
          message: _extractMessage(data) ?? 'Conflict with existing data.',
          code: 'CONFLICT',
          statusCode: statusCode,
        );

      case 422:
        return _handleValidationError(data);

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
        return ServerException(
          message: 'Server error. Please try again later.',
          code: 'SERVER_ERROR',
          statusCode: statusCode,
        );

      default:
        return ServerException(
          message: _extractMessage(data) ?? 'An error occurred (status: $statusCode)',
          statusCode: statusCode,
        );
    }
  }

  /// Handle 400 Bad Request errors
  Exception _handleBadRequest(dynamic data) {
    final message = _extractMessage(data) ?? 'Invalid request';
    final code = _extractCode(data);

    // Check if it's a validation error in disguise
    if (data is Map<String, dynamic>) {
      final details = data['error']?['details'] as Map<String, dynamic>?;
      if (details != null && details.isNotEmpty) {
        return ValidationException(
          message,
          fieldErrors: _parseFieldErrors(details),
        );
      }
    }

    return ServerException(
      message: message,
      code: code,
      statusCode: 400,
    );
  }

  /// Handle 422 Validation errors
  Exception _handleValidationError(dynamic data) {
    if (data is Map<String, dynamic>) {
      final error = data['error'] as Map<String, dynamic>?;
      if (error != null) {
        final details = error['details'] as Map<String, dynamic>?;
        return ValidationException(
          error['message'] as String? ?? 'Validation failed',
          fieldErrors: details != null ? _parseFieldErrors(details) : {},
        );
      }

      // Handle FastAPI-style validation errors
      final detail = data['detail'];
      if (detail is List) {
        final fieldErrors = <String, List<String>>{};
        for (final item in detail) {
          if (item is Map<String, dynamic>) {
            final loc = item['loc'] as List?;
            final msg = item['msg'] as String?;
            if (loc != null && loc.isNotEmpty && msg != null) {
              final field = loc.last.toString();
              fieldErrors.putIfAbsent(field, () => []).add(msg);
            }
          }
        }
        return ValidationException('Validation failed', fieldErrors: fieldErrors);
      }
    }

    return ValidationException(
      _extractMessage(data) ?? 'Validation failed',
    );
  }

  /// Parse field errors from API response
  Map<String, List<String>> _parseFieldErrors(Map<String, dynamic> details) {
    final fieldErrors = <String, List<String>>{};

    for (final entry in details.entries) {
      final value = entry.value;
      if (value is String) {
        fieldErrors[entry.key] = [value];
      } else if (value is List) {
        fieldErrors[entry.key] = value.map((e) => e.toString()).toList();
      }
    }

    return fieldErrors;
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

  /// Extract error code from response data
  String? _extractCode(dynamic data) {
    if (data is Map<String, dynamic>) {
      final error = data['error'];
      if (error is Map<String, dynamic>) {
        return error['code'] as String?;
      }
      return data['code'] as String?;
    }
    return null;
  }
}
