import 'dart:async';
import 'dart:math';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'retry_service.g.dart';

/// Network retry service with exponential backoff for failed requests.
///
/// Features:
/// - Exponential backoff with jitter
/// - Configurable retry count and delays
/// - Offline detection
/// - Automatic retry on network recovery
class RetryService {
  final Connectivity _connectivity;
  
  // Configuration
  static const int defaultMaxRetries = 3;
  static const Duration defaultInitialDelay = Duration(milliseconds: 500);
  static const Duration defaultMaxDelay = Duration(seconds: 10);
  static const double backoffMultiplier = 2.0;
  
  // Network state
  bool _isOnline = true;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  final _networkStateController = StreamController<bool>.broadcast();
  
  RetryService({Connectivity? connectivity})
      : _connectivity = connectivity ?? Connectivity() {
    _initializeNetworkMonitoring();
  }
  
  /// Initialize network monitoring
  void _initializeNetworkMonitoring() {
    // Check initial connectivity
    _connectivity.checkConnectivity().then((results) {
      _updateNetworkState(results);
    });
    
    // Listen to connectivity changes
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      (results) {
        _updateNetworkState(results);
      },
    );
  }
  
  /// Update network state based on connectivity results
  void _updateNetworkState(List<ConnectivityResult> results) {
    final wasOnline = _isOnline;
    _isOnline = results.isNotEmpty && !results.contains(ConnectivityResult.none);
    
    if (wasOnline != _isOnline) {
      debugPrint('Network state changed: ${_isOnline ? "Online" : "Offline"}');
      _networkStateController.add(_isOnline);
    }
  }
  
  /// Get current network state
  bool get isOnline => _isOnline;
  
  /// Stream of network state changes
  Stream<bool> get networkStateStream => _networkStateController.stream;
  
  /// Execute a request with retry logic
  Future<T> execute<T>(
    Future<T> Function() request, {
    int? maxRetries,
    Duration? initialDelay,
    Duration? maxDelay,
    bool Function(Exception)? shouldRetry,
  }) async {
    final retryCount = maxRetries ?? defaultMaxRetries;
    final baseDelay = initialDelay ?? defaultInitialDelay;
    final maximumDelay = maxDelay ?? defaultMaxDelay;
    
    int attempt = 0;
    Exception? lastException;
    
    while (attempt <= retryCount) {
      try {
        // Check if we're offline
        if (!_isOnline && attempt > 0) {
          debugPrint('Offline - waiting for network...');
          await _waitForNetwork();
        }
        
        debugPrint('Attempt ${attempt + 1}/${retryCount + 1}');
        return await request();
      } catch (e) {
        lastException = e is Exception ? e : Exception(e.toString());
        
        // Check if we should retry this exception
        if (shouldRetry != null && !shouldRetry(lastException)) {
          debugPrint('Exception not retryable: $e');
          rethrow;
        }
        
        // Don't wait after the last attempt
        if (attempt >= retryCount) {
          debugPrint('Max retries reached');
          rethrow;
        }
        
        // Calculate delay with exponential backoff and jitter
        final delay = _calculateDelay(
          attempt,
          baseDelay,
          maximumDelay,
        );
        
        debugPrint('Request failed (attempt ${attempt + 1}), retrying in ${delay.inMilliseconds}ms: $e');
        await Future.delayed(delay);
        
        attempt++;
      }
    }
    
    // This should never be reached, but just in case
    throw lastException ?? Exception('Request failed after $retryCount retries');
  }
  
  /// Calculate delay with exponential backoff and jitter
  Duration _calculateDelay(
    int attempt,
    Duration baseDelay,
    Duration maxDelay,
  ) {
    // Exponential backoff: baseDelay * (2^attempt)
    final exponentialDelay = baseDelay.inMilliseconds * pow(backoffMultiplier, attempt);
    
    // Add jitter (±25% random variation)
    final jitter = Random().nextDouble() * 0.5 + 0.75; // 0.75 to 1.25
    final delayWithJitter = (exponentialDelay * jitter).toInt();
    
    // Cap at max delay
    final cappedDelay = min(delayWithJitter, maxDelay.inMilliseconds);
    
    return Duration(milliseconds: cappedDelay);
  }
  
  /// Wait for network to become available
  Future<void> _waitForNetwork({Duration timeout = const Duration(seconds: 30)}) async {
    if (_isOnline) return;

    try {
      await networkStateStream
          .firstWhere((isOnline) => isOnline)
          .timeout(timeout);
    } on TimeoutException {
      debugPrint('Timeout waiting for network');
      throw Exception('Network timeout');
    }
  }

  /// Check if an exception is retryable
  static bool isRetryableException(Exception exception) {
    if (exception is DioException) {
      // Retry on network errors
      if (exception.type == DioExceptionType.connectionTimeout ||
          exception.type == DioExceptionType.sendTimeout ||
          exception.type == DioExceptionType.receiveTimeout ||
          exception.type == DioExceptionType.connectionError) {
        return true;
      }

      // Retry on specific HTTP status codes
      final statusCode = exception.response?.statusCode;
      if (statusCode != null) {
        // Retry on 5xx server errors and 429 (too many requests)
        if (statusCode >= 500 || statusCode == 429) {
          return true;
        }
      }

      return false;
    }

    // Retry on timeout exceptions
    if (exception is TimeoutException) {
      return true;
    }

    return false;
  }

  /// Dispose resources
  void dispose() {
    _connectivitySubscription?.cancel();
    _networkStateController.close();
  }
}

/// Provides the RetryService instance
@Riverpod(keepAlive: true)
RetryService retryService(RetryServiceRef ref) {
  final service = RetryService();
  ref.onDispose(() => service.dispose());
  return service;
}

