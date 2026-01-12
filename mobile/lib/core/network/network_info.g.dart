// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'network_info.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$connectivityHash() => r'15246627d0ae599bcd01382c80d3d25b9e9b4e18';

/// Provides the Connectivity instance
///
/// Copied from [connectivity].
@ProviderFor(connectivity)
final connectivityProvider = Provider<Connectivity>.internal(
  connectivity,
  name: r'connectivityProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$connectivityHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ConnectivityRef = ProviderRef<Connectivity>;
String _$networkInfoHash() => r'40947ae7ad95274c0332c9e389b188c77834e388';

/// Provides the NetworkInfo implementation
///
/// Copied from [networkInfo].
@ProviderFor(networkInfo)
final networkInfoProvider = Provider<NetworkInfo>.internal(
  networkInfo,
  name: r'networkInfoProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$networkInfoHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef NetworkInfoRef = ProviderRef<NetworkInfo>;
String _$connectivityStatusHash() =>
    r'4d47a845c4ca9ee4ba6655cd5739653d6985486d';

/// Provider for watching connectivity status as a stream
///
/// Copied from [connectivityStatus].
@ProviderFor(connectivityStatus)
final connectivityStatusProvider = AutoDisposeStreamProvider<bool>.internal(
  connectivityStatus,
  name: r'connectivityStatusProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$connectivityStatusHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ConnectivityStatusRef = AutoDisposeStreamProviderRef<bool>;
String _$isConnectedHash() => r'f17a5f373ef95358cfa9a530f353481ea71efa6c';

/// Provider for checking current connectivity synchronously
/// Returns true by default, actual check is async
///
/// Copied from [isConnected].
@ProviderFor(isConnected)
final isConnectedProvider = AutoDisposeFutureProvider<bool>.internal(
  isConnected,
  name: r'isConnectedProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$isConnectedHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef IsConnectedRef = AutoDisposeFutureProviderRef<bool>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
