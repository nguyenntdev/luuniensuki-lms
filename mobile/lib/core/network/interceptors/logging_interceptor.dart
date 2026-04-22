import 'dart:developer' as developer;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Interceptor for logging HTTP requests and responses.
/// Only logs in debug mode to avoid exposing sensitive data in production.
class LoggingInterceptor extends Interceptor {
  final bool logRequestHeaders;
  final bool logRequestBody;
  final bool logResponseHeaders;
  final bool logResponseBody;
  final bool logErrors;

  LoggingInterceptor({
    this.logRequestHeaders = true,
    this.logRequestBody = true,
    this.logResponseHeaders = false,
    this.logResponseBody = true,
    this.logErrors = true,
  });

  static const String _tag = 'API';

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (kDebugMode) {
      final buffer = StringBuffer();
      buffer.writeln('┌─────────────────────────────────────────────────────────────');
      buffer.writeln('│ 📤 REQUEST');
      buffer.writeln('├─────────────────────────────────────────────────────────────');
      buffer.writeln('│ ${options.method.toUpperCase()} ${options.uri}');

      if (logRequestHeaders && options.headers.isNotEmpty) {
        buffer.writeln('│ Headers:');
        options.headers.forEach((key, value) {
          // Mask authorization header for security
          if (key.toLowerCase() == 'authorization') {
            buffer.writeln('│   $key: Bearer ***');
          } else {
            buffer.writeln('│   $key: $value');
          }
        });
      }

      if (logRequestBody && options.data != null) {
        buffer.writeln('│ Body:');
        final body = _formatBody(options.data);
        for (final line in body.split('\n')) {
          buffer.writeln('│   $line');
        }
      }

      buffer.writeln('└─────────────────────────────────────────────────────────────');
      _log(buffer.toString());
    }

    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (kDebugMode) {
      final buffer = StringBuffer();
      buffer.writeln('┌─────────────────────────────────────────────────────────────');
      buffer.writeln('│ 📥 RESPONSE');
      buffer.writeln('├─────────────────────────────────────────────────────────────');
      buffer.writeln('│ ${response.statusCode} ${response.statusMessage}');
      buffer.writeln('│ ${response.requestOptions.method.toUpperCase()} ${response.requestOptions.uri}');
      buffer.writeln('│ Duration: ${_getDuration(response.requestOptions)}');

      if (logResponseHeaders && response.headers.map.isNotEmpty) {
        buffer.writeln('│ Headers:');
        response.headers.forEach((name, values) {
          buffer.writeln('│   $name: ${values.join(', ')}');
        });
      }

      if (logResponseBody && response.data != null) {
        buffer.writeln('│ Body:');
        final body = _formatBody(response.data);
        // Truncate very long responses
        final truncatedBody = body.length > 2000 ? '${body.substring(0, 2000)}... [truncated]' : body;
        for (final line in truncatedBody.split('\n')) {
          buffer.writeln('│   $line');
        }
      }

      buffer.writeln('└─────────────────────────────────────────────────────────────');
      _log(buffer.toString());
    }

    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (kDebugMode && logErrors) {
      final buffer = StringBuffer();
      buffer.writeln('┌─────────────────────────────────────────────────────────────');
      buffer.writeln('│ ❌ ERROR');
      buffer.writeln('├─────────────────────────────────────────────────────────────');
      buffer.writeln('│ Type: ${err.type}');
      buffer.writeln('│ Message: ${err.message}');
      buffer.writeln('│ ${err.requestOptions.method.toUpperCase()} ${err.requestOptions.uri}');

      if (err.response != null) {
        buffer.writeln('│ Status: ${err.response?.statusCode} ${err.response?.statusMessage}');

        if (err.response?.data != null) {
          buffer.writeln('│ Response Body:');
          final body = _formatBody(err.response?.data);
          for (final line in body.split('\n')) {
            buffer.writeln('│   $line');
          }
        }
      }

      if (err.error != null) {
        buffer.writeln('│ Original Error: ${err.error}');
      }

      buffer.writeln('└─────────────────────────────────────────────────────────────');
      _log(buffer.toString(), isError: true);
    }

    handler.next(err);
  }

  String _formatBody(dynamic data) {
    if (data == null) return 'null';

    if (data is Map || data is List) {
      try {
        // Simple JSON-like formatting
        return data.toString();
      } catch (_) {
        return data.toString();
      }
    }

    if (data is FormData) {
      final buffer = StringBuffer('FormData:');
      for (final field in data.fields) {
        buffer.write(' ${field.key}=${field.value}');
      }
      for (final file in data.files) {
        buffer.write(' ${file.key}=[FILE: ${file.value.filename}]');
      }
      return buffer.toString();
    }

    return data.toString();
  }

  String _getDuration(RequestOptions options) {
    // If we stored the start time, we could calculate duration
    // For now, return placeholder
    return '-';
  }

  void _log(String message, {bool isError = false}) {
    // Using developer.log for better DevTools integration
    developer.log(
      message,
      name: _tag,
      level: isError ? 1000 : 800,
    );
  }
}
