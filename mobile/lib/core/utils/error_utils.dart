import 'dart:async' show TimeoutException;
import 'dart:io' show SocketException;

import '../errors/exceptions.dart';

/// Centralized utility for formatting error messages into user-friendly Vietnamese text.
/// 
/// This class provides static methods to convert various error types (exceptions, 
/// HTTP status codes, network errors) into localized Vietnamese messages suitable 
/// for end users.
class ErrorUtils {
  ErrorUtils._();

  /// Formats any error into a user-friendly Vietnamese message.
  /// 
  /// Handles common error patterns:
  /// - Network errors (SocketException, NetworkException)
  /// - Timeout errors (TimeoutException)
  /// - HTTP status codes (401, 404, 500, etc.)
  /// - Custom app exceptions (AuthException, ServerException, etc.)
  /// 
  /// Example:
  /// ```dart
  /// try {
  ///   await fetchData();
  /// } catch (e) {
  ///   final message = ErrorUtils.formatForUser(e);
  ///   ScaffoldMessenger.of(context).showSnackBar(
  ///     SnackBar(content: Text(message)),
  ///   );
  /// }
  /// ```
  static String formatForUser(dynamic error) {
    // Handle typed exceptions
    if (error is NetworkException) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    
    if (error is SocketException) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    
    if (error is TimeoutException) {
      return 'Kết nối quá chậm. Vui lòng thử lại.';
    }
    
    if (error is AuthException) {
      return 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.';
    }
    
    if (error is NotFoundException) {
      return 'Không tìm thấy dữ liệu.';
    }
    
    if (error is ForbiddenException) {
      return 'Bạn không có quyền truy cập. Vui lòng liên hệ quản trị viên.';
    }
    
    if (error is ServerException) {
      final statusCode = error.statusCode;
      if (statusCode != null) {
        return _formatHttpStatusCode(statusCode);
      }
      return 'Lỗi máy chủ. Vui lòng thử lại sau.';
    }
    
    // Handle string error messages (for backward compatibility)
    final errorString = error.toString();
    
    // Network-related errors
    if (_containsAny(errorString, ['SocketException', 'NetworkException', 'Connection refused'])) {
      return 'Không có kết nối mạng. Vui lòng kiểm tra lại.';
    }
    
    // Timeout errors
    if (_containsAny(errorString, ['TimeoutException', 'timeout', 'timed out'])) {
      return 'Kết nối quá chậm. Vui lòng thử lại.';
    }
    
    // HTTP status codes in error messages
    if (_containsAny(errorString, ['401', 'Unauthorized'])) {
      return 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.';
    }
    
    if (_containsAny(errorString, ['404', 'Not Found', 'NotFoundException'])) {
      return 'Không tìm thấy dữ liệu.';
    }
    
    if (_containsAny(errorString, ['500', 'Internal Server Error'])) {
      return 'Lỗi máy chủ. Vui lòng thử lại sau.';
    }
    
    if (_containsAny(errorString, ['503', 'Service Unavailable'])) {
      return 'Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau.';
    }
    
    // Default fallback
    return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }

  /// Checks if the given error is a network-related error.
  /// 
  /// Returns `true` if the error is related to network connectivity issues,
  /// such as SocketException, NetworkException, or timeout errors.
  /// 
  /// Example:
  /// ```dart
  /// try {
  ///   await fetchData();
  /// } catch (e) {
  ///   if (ErrorUtils.isNetworkError(e)) {
  ///     // Show offline mode or retry button
  ///   }
  /// }
  /// ```
  static bool isNetworkError(dynamic error) {
    if (error is NetworkException || error is SocketException) {
      return true;
    }
    
    if (error is TimeoutException) {
      return true;
    }
    
    final errorString = error.toString();
    return _containsAny(errorString, [
      'SocketException',
      'NetworkException',
      'TimeoutException',
      'timeout',
      'timed out',
      'Connection refused',
      'Connection reset',
      'Connection closed',
      'No route to host',
    ]);
  }

  /// Formats HTTP status code into Vietnamese error message.
  static String _formatHttpStatusCode(int statusCode) {
    switch (statusCode) {
      case 400:
        return 'Yêu cầu không hợp lệ.';
      case 401:
        return 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.';
      case 403:
        return 'Bạn không có quyền truy cập.';
      case 404:
        return 'Không tìm thấy dữ liệu.';
      case 500:
        return 'Lỗi máy chủ. Vui lòng thử lại sau.';
      case 502:
        return 'Máy chủ tạm thời quá tải. Vui lòng thử lại sau.';
      case 503:
        return 'Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau.';
      default:
        return 'Đã xảy ra lỗi. Vui lòng thử lại.';
    }
  }

  /// Helper to check if a string contains any of the given substrings.
  static bool _containsAny(String text, List<String> patterns) {
    final lowerText = text.toLowerCase();
    return patterns.any((pattern) => lowerText.contains(pattern.toLowerCase()));
  }
}

