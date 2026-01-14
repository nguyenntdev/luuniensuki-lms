// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'explore_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$urnBySlugHash() => r'33e2c1427948cb13e23c52945ecf960a2ddf71ec';

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

/// Provider for a single urn by slug
///
/// Copied from [urnBySlug].
@ProviderFor(urnBySlug)
const urnBySlugProvider = UrnBySlugFamily();

/// Provider for a single urn by slug
///
/// Copied from [urnBySlug].
class UrnBySlugFamily extends Family<Urn?> {
  /// Provider for a single urn by slug
  ///
  /// Copied from [urnBySlug].
  const UrnBySlugFamily();

  /// Provider for a single urn by slug
  ///
  /// Copied from [urnBySlug].
  UrnBySlugProvider call(
    String slug,
  ) {
    return UrnBySlugProvider(
      slug,
    );
  }

  @override
  UrnBySlugProvider getProviderOverride(
    covariant UrnBySlugProvider provider,
  ) {
    return call(
      provider.slug,
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
  String? get name => r'urnBySlugProvider';
}

/// Provider for a single urn by slug
///
/// Copied from [urnBySlug].
class UrnBySlugProvider extends AutoDisposeProvider<Urn?> {
  /// Provider for a single urn by slug
  ///
  /// Copied from [urnBySlug].
  UrnBySlugProvider(
    String slug,
  ) : this._internal(
          (ref) => urnBySlug(
            ref as UrnBySlugRef,
            slug,
          ),
          from: urnBySlugProvider,
          name: r'urnBySlugProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$urnBySlugHash,
          dependencies: UrnBySlugFamily._dependencies,
          allTransitiveDependencies: UrnBySlugFamily._allTransitiveDependencies,
          slug: slug,
        );

  UrnBySlugProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.slug,
  }) : super.internal();

  final String slug;

  @override
  Override overrideWith(
    Urn? Function(UrnBySlugRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: UrnBySlugProvider._internal(
        (ref) => create(ref as UrnBySlugRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        slug: slug,
      ),
    );
  }

  @override
  AutoDisposeProviderElement<Urn?> createElement() {
    return _UrnBySlugProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is UrnBySlugProvider && other.slug == slug;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, slug.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin UrnBySlugRef on AutoDisposeProviderRef<Urn?> {
  /// The parameter `slug` of this provider.
  String get slug;
}

class _UrnBySlugProviderElement extends AutoDisposeProviderElement<Urn?>
    with UrnBySlugRef {
  _UrnBySlugProviderElement(super.provider);

  @override
  String get slug => (origin as UrnBySlugProvider).slug;
}

String _$exploreProgressHash() => r'beee7503bfe2d5e85eb5370a44eb056ac6aec756';

/// Provider for total progress across all urns
///
/// Copied from [exploreProgress].
@ProviderFor(exploreProgress)
final exploreProgressProvider = AutoDisposeProvider<ExploreProgress>.internal(
  exploreProgress,
  name: r'exploreProgressProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$exploreProgressHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ExploreProgressRef = AutoDisposeProviderRef<ExploreProgress>;
String _$exploreNotifierHash() => r'b0137f6aaa9439f910f888bc082cafee6f510dbd';

/// Provider for explore screen state and actions
///
/// Copied from [ExploreNotifier].
@ProviderFor(ExploreNotifier)
final exploreNotifierProvider =
    NotifierProvider<ExploreNotifier, ExploreState>.internal(
  ExploreNotifier.new,
  name: r'exploreNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$exploreNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$ExploreNotifier = Notifier<ExploreState>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
