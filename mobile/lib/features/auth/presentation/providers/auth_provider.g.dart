// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$authRemoteDataSourceHash() =>
    r'35fba3917eadb8d98080f1a6d5ff590ea4ae6b8d';

/// Provides the AuthRemoteDataSource
///
/// Copied from [authRemoteDataSource].
@ProviderFor(authRemoteDataSource)
final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>.internal(
  authRemoteDataSource,
  name: r'authRemoteDataSourceProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$authRemoteDataSourceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthRemoteDataSourceRef = ProviderRef<AuthRemoteDataSource>;
String _$authLocalDataSourceHash() =>
    r'bdd2f6ed28c93393e312dfdf0e10fca43c7430b4';

/// Provides the AuthLocalDataSource
///
/// Copied from [authLocalDataSource].
@ProviderFor(authLocalDataSource)
final authLocalDataSourceProvider = Provider<AuthLocalDataSource>.internal(
  authLocalDataSource,
  name: r'authLocalDataSourceProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$authLocalDataSourceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthLocalDataSourceRef = ProviderRef<AuthLocalDataSource>;
String _$authRepositoryHash() => r'd434bf8664b18b89ab65c0dc05073fb433af00eb';

/// Provides the AuthRepository implementation
///
/// Copied from [authRepository].
@ProviderFor(authRepository)
final authRepositoryProvider = Provider<AuthRepository>.internal(
  authRepository,
  name: r'authRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$authRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthRepositoryRef = ProviderRef<AuthRepository>;
String _$currentUserHash() => r'cb194043f35f13412064b043917456099f44cec2';

/// Convenience providers for accessing auth state
/// Provider that returns the current authenticated user, or null
///
/// Copied from [currentUser].
@ProviderFor(currentUser)
final currentUserProvider = Provider<User?>.internal(
  currentUser,
  name: r'currentUserProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$currentUserHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CurrentUserRef = ProviderRef<User?>;
String _$isAuthenticatedHash() => r'7fb0c32f05965e237dac2f3640a3995f50649cde';

/// Provider that returns whether the user is authenticated
///
/// Copied from [isAuthenticated].
@ProviderFor(isAuthenticated)
final isAuthenticatedProvider = Provider<bool>.internal(
  isAuthenticated,
  name: r'isAuthenticatedProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$isAuthenticatedHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef IsAuthenticatedRef = ProviderRef<bool>;
String _$isAuthLoadingHash() => r'09120d21538e56a33bd1c561bab2513204be522c';

/// Provider that returns whether auth is loading
///
/// Copied from [isAuthLoading].
@ProviderFor(isAuthLoading)
final isAuthLoadingProvider = Provider<bool>.internal(
  isAuthLoading,
  name: r'isAuthLoadingProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$isAuthLoadingHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef IsAuthLoadingRef = ProviderRef<bool>;
String _$authErrorHash() => r'bc8ef728e24f93a65b9863302be9c77fdd544b9e';

/// Provider that returns the auth error message, if any
///
/// Copied from [authError].
@ProviderFor(authError)
final authErrorProvider = Provider<String?>.internal(
  authError,
  name: r'authErrorProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$authErrorHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthErrorRef = ProviderRef<String?>;
String _$authNotifierHash() => r'8bf8bfee6d6071e6232c1002d751e2cb296df896';

/// Auth state notifier that manages authentication state.
/// Handles login, registration, logout, and session management.
///
/// Copied from [AuthNotifier].
@ProviderFor(AuthNotifier)
final authNotifierProvider = NotifierProvider<AuthNotifier, AuthState>.internal(
  AuthNotifier.new,
  name: r'authNotifierProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$authNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$AuthNotifier = Notifier<AuthState>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
