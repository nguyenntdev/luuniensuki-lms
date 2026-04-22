/// Custom exception classes for error handling in the app.
/// These exceptions are thrown in data layer and converted to Failures in repositories.

/// Server-related exception for API errors
class ServerException implements Exception {
  final String message;
  final String? code;
  final int? statusCode;
  final Map<String, dynamic>? details;

  const ServerException({
    required this.message,
    this.code,
    this.statusCode,
    this.details,
  });

  /// Create from API error response format
  factory ServerException.fromJson(Map<String, dynamic> json, {int? statusCode}) {
    final error = json['error'] as Map<String, dynamic>?;
    if (error != null) {
      return ServerException(
        message: error['message'] as String? ?? 'Unknown error',
        code: error['code'] as String?,
        statusCode: statusCode,
        details: error['details'] as Map<String, dynamic>?,
      );
    }
    // Fallback for non-standard error format
    return ServerException(
      message: json['detail'] as String? ?? json['message'] as String? ?? 'Unknown error',
      statusCode: statusCode,
    );
  }

  @override
  String toString() => 'ServerException: $message (code: $code, status: $statusCode)';
}

/// Exception for local cache operations
class CacheException implements Exception {
  final String message;
  final dynamic originalError;

  const CacheException(this.message, {this.originalError});

  @override
  String toString() => 'CacheException: $message';
}

/// Exception for network connectivity issues
class NetworkException implements Exception {
  final String message;
  final dynamic originalError;

  const NetworkException(this.message, {this.originalError});

  @override
  String toString() => 'NetworkException: $message';
}

/// Exception for authentication errors
class AuthException implements Exception {
  final String message;
  final String? code;
  final bool shouldLogout;

  const AuthException(
    this.message, {
    this.code,
    this.shouldLogout = false,
  });

  @override
  String toString() => 'AuthException: $message (code: $code)';
}

/// Exception for validation errors (e.g., form validation)
class ValidationException implements Exception {
  final String message;
  final Map<String, List<String>> fieldErrors;

  const ValidationException(
    this.message, {
    this.fieldErrors = const {},
  });

  /// Get errors for a specific field
  List<String> errorsFor(String field) => fieldErrors[field] ?? [];

  /// Check if a specific field has errors
  bool hasErrorFor(String field) => fieldErrors.containsKey(field);

  @override
  String toString() => 'ValidationException: $message (fields: ${fieldErrors.keys.join(', ')})';
}

/// Exception for timeout errors
class TimeoutException implements Exception {
  final String message;
  final Duration? timeout;

  const TimeoutException(this.message, {this.timeout});

  @override
  String toString() => 'TimeoutException: $message (timeout: $timeout)';
}

/// Exception for permission/authorization errors
class ForbiddenException implements Exception {
  final String message;
  final String? requiredRole;

  const ForbiddenException(this.message, {this.requiredRole});

  @override
  String toString() => 'ForbiddenException: $message';
}

/// Exception for resource not found errors
class NotFoundException implements Exception {
  final String message;
  final String? resourceType;
  final String? resourceId;

  const NotFoundException(
    this.message, {
    this.resourceType,
    this.resourceId,
  });

  @override
  String toString() => 'NotFoundException: $message';
}
