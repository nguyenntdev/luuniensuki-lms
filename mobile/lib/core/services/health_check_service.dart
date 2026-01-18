import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../network/api_client.dart';
import '../constants/api_constants.dart';

part 'health_check_service.g.dart';

/// Health check service for monitoring API connectivity and app version.
///
/// Features:
/// - API connectivity check
/// - App version verification
/// - Periodic health check
/// - Health status streaming
class HealthCheckService {
  final ApiClient _apiClient;
  
  // Configuration
  static const Duration checkInterval = Duration(minutes: 5);
  static const Duration checkTimeout = Duration(seconds: 10);
  
  // Health state
  bool _isHealthy = true;
  String? _latestVersion;
  bool _isUpdateAvailable = false;
  Timer? _healthCheckTimer;
  
  final _healthStateController = StreamController<HealthStatus>.broadcast();
  
  HealthCheckService(this._apiClient);
  
  /// Start periodic health checks
  void startPeriodicHealthCheck() {
    // Perform initial health check
    performHealthCheck();
    
    // Schedule periodic checks
    _healthCheckTimer = Timer.periodic(checkInterval, (_) {
      performHealthCheck();
    });
    
    debugPrint('Started periodic health checks (every ${checkInterval.inMinutes} minutes)');
  }
  
  /// Stop periodic health checks
  void stopPeriodicHealthCheck() {
    _healthCheckTimer?.cancel();
    _healthCheckTimer = null;
    debugPrint('Stopped periodic health checks');
  }
  
  /// Perform a health check
  Future<HealthStatus> performHealthCheck() async {
    debugPrint('Performing health check...');
    
    final status = HealthStatus(
      isHealthy: true,
      apiConnected: false,
      isUpdateAvailable: false,
      timestamp: DateTime.now(),
    );
    
    try {
      // Check API connectivity
      final apiConnected = await _checkApiConnectivity();
      status.apiConnected = apiConnected;
      
      // Check app version if API is connected
      if (apiConnected) {
        final updateAvailable = await _checkAppVersion();
        status.isUpdateAvailable = updateAvailable;
      }
      
      // Overall health is good if API is connected
      status.isHealthy = apiConnected;
      
    } catch (e) {
      debugPrint('Health check error: $e');
      status.isHealthy = false;
      status.error = e.toString();
    }
    
    // Update state
    _isHealthy = status.isHealthy;
    _isUpdateAvailable = status.isUpdateAvailable;
    
    // Emit status
    _healthStateController.add(status);
    
    debugPrint('Health check completed: ${status.isHealthy ? "Healthy" : "Unhealthy"}');
    
    return status;
  }
  
  /// Check API connectivity
  Future<bool> _checkApiConnectivity() async {
    try {
      // Try to hit a health endpoint (you may need to create this endpoint)
      // For now, we'll use a simple GET request to the base URL
      final response = await _apiClient.get<Map<String, dynamic>>(
        '/health',
        options: Options(
          sendTimeout: checkTimeout,
          receiveTimeout: checkTimeout,
        ),
      ).timeout(checkTimeout);
      
      debugPrint('API connectivity check: SUCCESS');
      return true;
    } catch (e) {
      debugPrint('API connectivity check: FAILED - $e');
      return false;
    }
  }
  
  /// Check app version and compare with server version
  Future<bool> _checkAppVersion() async {
    try {
      // Get current app version
      final packageInfo = await PackageInfo.fromPlatform();
      final currentVersion = packageInfo.version;
      
      // Check latest version from server
      // You may need to create an endpoint for this
      final response = await _apiClient.get<Map<String, dynamic>>(
        '/app-version',
        options: Options(
          sendTimeout: checkTimeout,
          receiveTimeout: checkTimeout,
        ),
      ).timeout(checkTimeout);
      
      _latestVersion = response['latest_version'] as String?;
      
      if (_latestVersion != null) {
        final updateAvailable = _compareVersions(currentVersion, _latestVersion!);
        
        if (updateAvailable) {
          debugPrint('Update available: $currentVersion -> $_latestVersion');
        }
        
        return updateAvailable;
      }
      
      return false;
    } catch (e) {
      debugPrint('Version check error: $e');
      return false;
    }
  }
  
  /// Compare versions (returns true if serverVersion is newer)
  bool _compareVersions(String currentVersion, String serverVersion) {
    try {
      final current = _parseVersion(currentVersion);
      final server = _parseVersion(serverVersion);

      // Compare major.minor.patch
      for (int i = 0; i < 3; i++) {
        if (server[i] > current[i]) return true;
        if (server[i] < current[i]) return false;
      }

      return false; // Versions are equal
    } catch (e) {
      debugPrint('Version comparison error: $e');
      return false;
    }
  }

  /// Parse version string to list of integers
  List<int> _parseVersion(String version) {
    final parts = version.split('.');
    return parts.map((p) => int.tryParse(p) ?? 0).toList();
  }

  /// Dispose resources
  void dispose() {
    stopPeriodicHealthCheck();
    _healthStateController.close();
  }

  /// Get current health status
  bool get isHealthy => _isHealthy;

  /// Get latest version
  String? get latestVersion => _latestVersion;

  /// Get update availability
  bool get isUpdateAvailable => _isUpdateAvailable;

  /// Stream of health status changes
  Stream<HealthStatus> get healthStatusStream => _healthStateController.stream;
}

/// Health status data class
class HealthStatus {
  bool isHealthy;
  bool apiConnected;
  bool isUpdateAvailable;
  DateTime timestamp;
  String? error;

  HealthStatus({
    required this.isHealthy,
    required this.apiConnected,
    required this.isUpdateAvailable,
    required this.timestamp,
    this.error,
  });
}

/// Options class stub for API client
class Options {
  final Duration? sendTimeout;
  final Duration? receiveTimeout;

  Options({this.sendTimeout, this.receiveTimeout});
}

/// Provider for health check service
@Riverpod(keepAlive: true)
HealthCheckService healthCheckService(HealthCheckServiceRef ref) {
  final apiClient = ref.watch(apiClientProvider);
  final service = HealthCheckService(apiClient);

  ref.onDispose(() {
    service.dispose();
  });

  return service;
}
