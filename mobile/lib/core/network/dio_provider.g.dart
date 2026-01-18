// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dio_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$dioHash() => r'4fd8babf476bbd700a3188569ce3e51c0423aec5';

/// Provides a configured Dio instance for making HTTP requests.
///
/// The Dio client is configured with:
/// - Base URL pointing to the production API
/// - Timeout settings for connection, send, and receive operations
/// - Auth interceptor for token injection
/// - Token refresh interceptor for automatic token refresh on 401
/// - Error interceptor for converting errors to exceptions
/// - Logging interceptor (debug mode only)
///
/// Copied from [dio].
@ProviderFor(dio)
final dioProvider = Provider<Dio>.internal(
  dio,
  name: r'dioProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$dioHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DioRef = ProviderRef<Dio>;
String _$authDioHash() => r'ed2d147a2cd605e89203f8849afd86fa27ad22ea';

/// Provides a Dio instance specifically for authentication requests.
/// This instance does NOT include the auth interceptor to avoid circular issues.
///
/// Copied from [authDio].
@ProviderFor(authDio)
final authDioProvider = Provider<Dio>.internal(
  authDio,
  name: r'authDioProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$authDioHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthDioRef = ProviderRef<Dio>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
