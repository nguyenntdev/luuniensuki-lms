// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recommendations_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$recommendationsHash() => r'bec7af2ec36999813b4c86e95ddd6e737af41fd6';

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

/// See also [recommendations].
@ProviderFor(recommendations)
const recommendationsProvider = RecommendationsFamily();

/// See also [recommendations].
class RecommendationsFamily
    extends Family<AsyncValue<RecommendationsResponseDto>> {
  /// See also [recommendations].
  const RecommendationsFamily();

  /// See also [recommendations].
  RecommendationsProvider call({
    String? type,
    int limit = 10,
  }) {
    return RecommendationsProvider(
      type: type,
      limit: limit,
    );
  }

  @override
  RecommendationsProvider getProviderOverride(
    covariant RecommendationsProvider provider,
  ) {
    return call(
      type: provider.type,
      limit: provider.limit,
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
  String? get name => r'recommendationsProvider';
}

/// See also [recommendations].
class RecommendationsProvider
    extends AutoDisposeFutureProvider<RecommendationsResponseDto> {
  /// See also [recommendations].
  RecommendationsProvider({
    String? type,
    int limit = 10,
  }) : this._internal(
          (ref) => recommendations(
            ref as RecommendationsRef,
            type: type,
            limit: limit,
          ),
          from: recommendationsProvider,
          name: r'recommendationsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$recommendationsHash,
          dependencies: RecommendationsFamily._dependencies,
          allTransitiveDependencies:
              RecommendationsFamily._allTransitiveDependencies,
          type: type,
          limit: limit,
        );

  RecommendationsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.type,
    required this.limit,
  }) : super.internal();

  final String? type;
  final int limit;

  @override
  Override overrideWith(
    FutureOr<RecommendationsResponseDto> Function(RecommendationsRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: RecommendationsProvider._internal(
        (ref) => create(ref as RecommendationsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        type: type,
        limit: limit,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<RecommendationsResponseDto> createElement() {
    return _RecommendationsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is RecommendationsProvider &&
        other.type == type &&
        other.limit == limit;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, type.hashCode);
    hash = _SystemHash.combine(hash, limit.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin RecommendationsRef
    on AutoDisposeFutureProviderRef<RecommendationsResponseDto> {
  /// The parameter `type` of this provider.
  String? get type;

  /// The parameter `limit` of this provider.
  int get limit;
}

class _RecommendationsProviderElement
    extends AutoDisposeFutureProviderElement<RecommendationsResponseDto>
    with RecommendationsRef {
  _RecommendationsProviderElement(super.provider);

  @override
  String? get type => (origin as RecommendationsProvider).type;
  @override
  int get limit => (origin as RecommendationsProvider).limit;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
