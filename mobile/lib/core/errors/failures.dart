import 'package:equatable/equatable.dart';

/// Base class for all failures in the domain layer.
/// Failures represent expected errors that can be handled gracefully.
abstract class Failure extends Equatable {
  final String message;
  final String? code;

  const Failure(this.message, {this.code});

  @override
  List<Object?> get props => [message, code];

  @override
  String toString() => '$runtimeType: $message (code: $code)';
}

/// Failure from server/API errors
class ServerFailure extends Failure {
  final int? statusCode;
  final Map<String, dynamic>? details;

  const ServerFailure(
    super.message, {
    super.code,
    this.statusCode,
    this.details,
  });

  @override
  List<Object?> get props => [message, code, statusCode, details];
}

/// Failure due to network connectivity issues
class NetworkFailure extends Failure {
  const NetworkFailure([String message = 'No internet connection'])
      : super(message, code: 'NETWORK_ERROR');
}

/// Failure when reading/writing cached data
class CacheFailure extends Failure {
  const CacheFailure([String message = 'Cache error'])
      : super(message, code: 'CACHE_ERROR');
}

/// Authentication-related failures
class AuthFailure extends Failure {
  const AuthFailure(super.message, {super.code});

  /// User is not logged in
  factory AuthFailure.unauthenticated() =>
      const AuthFailure('Not authenticated', code: 'UNAUTHENTICATED');

  /// Session has expired
  factory AuthFailure.sessionExpired() =>
      const AuthFailure('Session expired', code: 'SESSION_EXPIRED');

  /// Invalid credentials
  factory AuthFailure.invalidCredentials() =>
      const AuthFailure('Invalid email or password', code: 'INVALID_CREDENTIALS');

  /// Account locked or disabled
  factory AuthFailure.accountDisabled() =>
      const AuthFailure('Account is disabled', code: 'ACCOUNT_DISABLED');
}

/// Validation errors with field-specific messages
class ValidationFailure extends Failure {
  final Map<String, List<String>> fieldErrors;

  const ValidationFailure(
    super.message, {
    this.fieldErrors = const {},
    super.code = 'VALIDATION_ERROR',
  });

  /// Get error messages for a specific field
  List<String> errorsFor(String field) => fieldErrors[field] ?? [];

  /// Check if a field has errors
  bool hasErrorFor(String field) => fieldErrors.containsKey(field);

  /// Get the first error message for a field, or null if none
  String? firstErrorFor(String field) {
    final errors = errorsFor(field);
    return errors.isNotEmpty ? errors.first : null;
  }

  @override
  List<Object?> get props => [message, code, fieldErrors];
}

/// Failure when a requested resource is not found
class NotFoundFailure extends Failure {
  final String? resourceType;
  final String? resourceId;

  const NotFoundFailure(
    super.message, {
    this.resourceType,
    this.resourceId,
    super.code = 'NOT_FOUND',
  });

  factory NotFoundFailure.motif(String motifId) => NotFoundFailure(
        'Motif not found',
        resourceType: 'motif',
        resourceId: motifId,
      );

  factory NotFoundFailure.urn(String urnSlug) => NotFoundFailure(
        'Urn not found',
        resourceType: 'urn',
        resourceId: urnSlug,
      );

  @override
  List<Object?> get props => [message, code, resourceType, resourceId];
}

/// Failure when user doesn't have permission
class PermissionFailure extends Failure {
  const PermissionFailure([String message = 'Permission denied'])
      : super(message, code: 'PERMISSION_DENIED');

  /// Guest user trying to access premium content
  factory PermissionFailure.guestRestricted() =>
      const PermissionFailure('This content is not available for guest users');

  /// Content requires discovery first
  factory PermissionFailure.notDiscovered() =>
      const PermissionFailure('You must discover this motif first');
}

/// Unexpected/unknown failure
class UnexpectedFailure extends Failure {
  final Object? originalError;

  const UnexpectedFailure([
    String message = 'An unexpected error occurred',
    this.originalError,
  ]) : super(message, code: 'UNEXPECTED_ERROR');

  @override
  List<Object?> get props => [message, code, originalError];
}

/// Timeout failure
class TimeoutFailure extends Failure {
  const TimeoutFailure([String message = 'Request timed out'])
      : super(message, code: 'TIMEOUT');
}
