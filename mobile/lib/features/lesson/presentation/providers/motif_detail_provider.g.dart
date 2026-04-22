// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'motif_detail_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$motifDetailHash() => r'c359737b52fa30f2228a53a8d4daf0cac52d76ff';

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

/// Provider for fetching motif detail with lesson and progress data.
///
/// Copied from [motifDetail].
@ProviderFor(motifDetail)
const motifDetailProvider = MotifDetailFamily();

/// Provider for fetching motif detail with lesson and progress data.
///
/// Copied from [motifDetail].
class MotifDetailFamily extends Family<AsyncValue<MotifDetailDto>> {
  /// Provider for fetching motif detail with lesson and progress data.
  ///
  /// Copied from [motifDetail].
  const MotifDetailFamily();

  /// Provider for fetching motif detail with lesson and progress data.
  ///
  /// Copied from [motifDetail].
  MotifDetailProvider call(
    String motifId,
  ) {
    return MotifDetailProvider(
      motifId,
    );
  }

  @override
  MotifDetailProvider getProviderOverride(
    covariant MotifDetailProvider provider,
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
  String? get name => r'motifDetailProvider';
}

/// Provider for fetching motif detail with lesson and progress data.
///
/// Copied from [motifDetail].
class MotifDetailProvider extends AutoDisposeFutureProvider<MotifDetailDto> {
  /// Provider for fetching motif detail with lesson and progress data.
  ///
  /// Copied from [motifDetail].
  MotifDetailProvider(
    String motifId,
  ) : this._internal(
          (ref) => motifDetail(
            ref as MotifDetailRef,
            motifId,
          ),
          from: motifDetailProvider,
          name: r'motifDetailProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$motifDetailHash,
          dependencies: MotifDetailFamily._dependencies,
          allTransitiveDependencies:
              MotifDetailFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  MotifDetailProvider._internal(
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
    FutureOr<MotifDetailDto> Function(MotifDetailRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: MotifDetailProvider._internal(
        (ref) => create(ref as MotifDetailRef),
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
  AutoDisposeFutureProviderElement<MotifDetailDto> createElement() {
    return _MotifDetailProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is MotifDetailProvider && other.motifId == motifId;
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
mixin MotifDetailRef on AutoDisposeFutureProviderRef<MotifDetailDto> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _MotifDetailProviderElement
    extends AutoDisposeFutureProviderElement<MotifDetailDto>
    with MotifDetailRef {
  _MotifDetailProviderElement(super.provider);

  @override
  String get motifId => (origin as MotifDetailProvider).motifId;
}

String _$lessonCompletionHash() => r'59a0ebb0feb86091698e4057fc096cab55d08916';

/// Provider for completing a lesson.
///
/// Copied from [LessonCompletion].
@ProviderFor(LessonCompletion)
final lessonCompletionProvider = AutoDisposeAsyncNotifierProvider<
    LessonCompletion, CompleteLessonResponseDto?>.internal(
  LessonCompletion.new,
  name: r'lessonCompletionProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$lessonCompletionHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$LessonCompletion
    = AutoDisposeAsyncNotifier<CompleteLessonResponseDto?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
