// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'urn_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$urnRepositoryHash() => r'999d3b63b2a9847dc5a5b9df1c08f17bca142a84';

/// See also [urnRepository].
@ProviderFor(urnRepository)
final urnRepositoryProvider = Provider<UrnRepository>.internal(
  urnRepository,
  name: r'urnRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$urnRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef UrnRepositoryRef = ProviderRef<UrnRepository>;
String _$urnsOfflineFirstHash() => r'3fb87bf21d1b327282552d1823b79b261cf591b1';

/// See also [urnsOfflineFirst].
@ProviderFor(urnsOfflineFirst)
final urnsOfflineFirstProvider = AutoDisposeFutureProvider<List<Urn>>.internal(
  urnsOfflineFirst,
  name: r'urnsOfflineFirstProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$urnsOfflineFirstHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef UrnsOfflineFirstRef = AutoDisposeFutureProviderRef<List<Urn>>;
String _$urnDetailOfflineFirstHash() =>
    r'7c1778f5e8bf301ecb689ae396cff1e000b446a4';

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

/// See also [urnDetailOfflineFirst].
@ProviderFor(urnDetailOfflineFirst)
const urnDetailOfflineFirstProvider = UrnDetailOfflineFirstFamily();

/// See also [urnDetailOfflineFirst].
class UrnDetailOfflineFirstFamily extends Family<AsyncValue<UrnDetail>> {
  /// See also [urnDetailOfflineFirst].
  const UrnDetailOfflineFirstFamily();

  /// See also [urnDetailOfflineFirst].
  UrnDetailOfflineFirstProvider call(
    String slug,
  ) {
    return UrnDetailOfflineFirstProvider(
      slug,
    );
  }

  @override
  UrnDetailOfflineFirstProvider getProviderOverride(
    covariant UrnDetailOfflineFirstProvider provider,
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
  String? get name => r'urnDetailOfflineFirstProvider';
}

/// See also [urnDetailOfflineFirst].
class UrnDetailOfflineFirstProvider
    extends AutoDisposeFutureProvider<UrnDetail> {
  /// See also [urnDetailOfflineFirst].
  UrnDetailOfflineFirstProvider(
    String slug,
  ) : this._internal(
          (ref) => urnDetailOfflineFirst(
            ref as UrnDetailOfflineFirstRef,
            slug,
          ),
          from: urnDetailOfflineFirstProvider,
          name: r'urnDetailOfflineFirstProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$urnDetailOfflineFirstHash,
          dependencies: UrnDetailOfflineFirstFamily._dependencies,
          allTransitiveDependencies:
              UrnDetailOfflineFirstFamily._allTransitiveDependencies,
          slug: slug,
        );

  UrnDetailOfflineFirstProvider._internal(
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
    FutureOr<UrnDetail> Function(UrnDetailOfflineFirstRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: UrnDetailOfflineFirstProvider._internal(
        (ref) => create(ref as UrnDetailOfflineFirstRef),
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
  AutoDisposeFutureProviderElement<UrnDetail> createElement() {
    return _UrnDetailOfflineFirstProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is UrnDetailOfflineFirstProvider && other.slug == slug;
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
mixin UrnDetailOfflineFirstRef on AutoDisposeFutureProviderRef<UrnDetail> {
  /// The parameter `slug` of this provider.
  String get slug;
}

class _UrnDetailOfflineFirstProviderElement
    extends AutoDisposeFutureProviderElement<UrnDetail>
    with UrnDetailOfflineFirstRef {
  _UrnDetailOfflineFirstProviderElement(super.provider);

  @override
  String get slug => (origin as UrnDetailOfflineFirstProvider).slug;
}

String _$motifOfflineFirstHash() => r'849696a2b161158eb11c9fde91851c730145d8aa';

/// See also [motifOfflineFirst].
@ProviderFor(motifOfflineFirst)
const motifOfflineFirstProvider = MotifOfflineFirstFamily();

/// See also [motifOfflineFirst].
class MotifOfflineFirstFamily extends Family<AsyncValue<Motif>> {
  /// See also [motifOfflineFirst].
  const MotifOfflineFirstFamily();

  /// See also [motifOfflineFirst].
  MotifOfflineFirstProvider call(
    String motifId,
  ) {
    return MotifOfflineFirstProvider(
      motifId,
    );
  }

  @override
  MotifOfflineFirstProvider getProviderOverride(
    covariant MotifOfflineFirstProvider provider,
  ) {
    return call(
      provider.motifId,
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
  String? get name => r'motifOfflineFirstProvider';
}

/// See also [motifOfflineFirst].
class MotifOfflineFirstProvider extends AutoDisposeFutureProvider<Motif> {
  /// See also [motifOfflineFirst].
  MotifOfflineFirstProvider(
    String motifId,
  ) : this._internal(
          (ref) => motifOfflineFirst(
            ref as MotifOfflineFirstRef,
            motifId,
          ),
          from: motifOfflineFirstProvider,
          name: r'motifOfflineFirstProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$motifOfflineFirstHash,
          dependencies: MotifOfflineFirstFamily._dependencies,
          allTransitiveDependencies:
              MotifOfflineFirstFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  MotifOfflineFirstProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.motifId,
  }) : super.internal();

  final String motifId;

  @override
  Override overrideWith(
    FutureOr<Motif> Function(MotifOfflineFirstRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: MotifOfflineFirstProvider._internal(
        (ref) => create(ref as MotifOfflineFirstRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        motifId: motifId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<Motif> createElement() {
    return _MotifOfflineFirstProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is MotifOfflineFirstProvider && other.motifId == motifId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, motifId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin MotifOfflineFirstRef on AutoDisposeFutureProviderRef<Motif> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _MotifOfflineFirstProviderElement
    extends AutoDisposeFutureProviderElement<Motif> with MotifOfflineFirstRef {
  _MotifOfflineFirstProviderElement(super.provider);

  @override
  String get motifId => (origin as MotifOfflineFirstProvider).motifId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
