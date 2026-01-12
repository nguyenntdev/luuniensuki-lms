import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'network_info.g.dart';

/// Abstract interface for network connectivity checking.
/// Allows for easy mocking in tests.
abstract class NetworkInfo {
  /// Check if device is connected to the internet
  Future<bool> get isConnected;

  /// Stream of connectivity changes
  Stream<bool> get onConnectivityChanged;
}

/// Implementation of NetworkInfo using connectivity_plus package
class NetworkInfoImpl implements NetworkInfo {
  final Connectivity _connectivity;

  NetworkInfoImpl(this._connectivity);

  @override
  Future<bool> get isConnected async {
    final result = await _connectivity.checkConnectivity();
    return _isConnectedFromResult(result);
  }

  @override
  Stream<bool> get onConnectivityChanged {
    return _connectivity.onConnectivityChanged.map(_isConnectedFromResult);
  }

  bool _isConnectedFromResult(ConnectivityResult result) {
    // Connected if result is not 'none'
    return result != ConnectivityResult.none;
  }
}

/// Provides the Connectivity instance
@Riverpod(keepAlive: true)
Connectivity connectivity(Ref ref) {
  return Connectivity();
}

/// Provides the NetworkInfo implementation
@Riverpod(keepAlive: true)
NetworkInfo networkInfo(Ref ref) {
  final connectivity = ref.watch(connectivityProvider);
  return NetworkInfoImpl(connectivity);
}

/// Provider for watching connectivity status as a stream
@riverpod
Stream<bool> connectivityStatus(Ref ref) {
  final networkInfo = ref.watch(networkInfoProvider);
  return networkInfo.onConnectivityChanged;
}

/// Provider for checking current connectivity synchronously
/// Returns true by default, actual check is async
@riverpod
Future<bool> isConnected(Ref ref) async {
  final networkInfo = ref.watch(networkInfoProvider);
  return networkInfo.isConnected;
}
