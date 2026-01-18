// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'error_handler.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$errorHandlerHash() => r'252cb936b9ba80731e60b6feaa687f2d2b0b909c';

/// See also [errorHandler].
@ProviderFor(errorHandler)
final errorHandlerProvider = Provider<ErrorHandler>.internal(
  errorHandler,
  name: r'errorHandlerProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$errorHandlerHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ErrorHandlerRef = ProviderRef<ErrorHandler>;
String _$errorHandlerWithContextHash() =>
    r'884b491bec85fcf0994a7b3ad5692af4f4731f09';

/// Copied from Dart SDK
class _SystemHash {
  _SystemHash._();

  static int combine(int hash, int value) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + value);
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x0007ffff & hash) << 10));
    return hash ^ (hash >> 6);
  }

  static int finish(int hash) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x03ffffff & hash) << 3));
    // ignore: parameter_assignments
    hash = hash ^ (hash >> 11);
    return 0x1fffffff & (hash + ((0x00003fff & hash) << 15));
  }
}

/// See also [errorHandlerWithContext].
@ProviderFor(errorHandlerWithContext)
const errorHandlerWithContextProvider = ErrorHandlerWithContextFamily();

/// See also [errorHandlerWithContext].
class ErrorHandlerWithContextFamily extends Family<ErrorHandler> {
  /// See also [errorHandlerWithContext].
  const ErrorHandlerWithContextFamily();

  /// See also [errorHandlerWithContext].
  ErrorHandlerWithContextProvider call(
    BuildContext context,
  ) {
    return ErrorHandlerWithContextProvider(
      context,
    );
  }

  @override
  ErrorHandlerWithContextProvider getProviderOverride(
    covariant ErrorHandlerWithContextProvider provider,
  ) {
    return call(
      provider.context,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'errorHandlerWithContextProvider';
}

/// See also [errorHandlerWithContext].
class ErrorHandlerWithContextProvider
    extends AutoDisposeProvider<ErrorHandler> {
  /// See also [errorHandlerWithContext].
  ErrorHandlerWithContextProvider(
    BuildContext context,
  ) : this._internal(
          (ref) => errorHandlerWithContext(
            ref as ErrorHandlerWithContextRef,
            context,
          ),
          from: errorHandlerWithContextProvider,
          name: r'errorHandlerWithContextProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$errorHandlerWithContextHash,
          dependencies: ErrorHandlerWithContextFamily._dependencies,
          allTransitiveDependencies:
              ErrorHandlerWithContextFamily._allTransitiveDependencies,
          context: context,
        );

  ErrorHandlerWithContextProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.context,
  }) : super.internal();

  final BuildContext context;

  @override
  Override overrideWith(
    ErrorHandler Function(ErrorHandlerWithContextRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: ErrorHandlerWithContextProvider._internal(
        (ref) => create(ref as ErrorHandlerWithContextRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        context: context,
      ),
    );
  }

  @override
  AutoDisposeProviderElement<ErrorHandler> createElement() {
    return _ErrorHandlerWithContextProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is ErrorHandlerWithContextProvider && other.context == context;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, context.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin ErrorHandlerWithContextRef on AutoDisposeProviderRef<ErrorHandler> {
  /// The parameter `context` of this provider.
  BuildContext get context;
}

class _ErrorHandlerWithContextProviderElement
    extends AutoDisposeProviderElement<ErrorHandler>
    with ErrorHandlerWithContextRef {
  _ErrorHandlerWithContextProviderElement(super.provider);

  @override
  BuildContext get context =>
      (origin as ErrorHandlerWithContextProvider).context;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
