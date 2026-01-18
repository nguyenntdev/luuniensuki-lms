// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'lesson_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$lessonRepositoryHash() => r'9ee0d8a69ce3191d6c09dcf6dd8ba9cbee4f2180';

/// See also [lessonRepository].
@ProviderFor(lessonRepository)
final lessonRepositoryProvider = Provider<LessonRepository>.internal(
  lessonRepository,
  name: r'lessonRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$lessonRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef LessonRepositoryRef = ProviderRef<LessonRepository>;
String _$motifDetailOfflineFirstHash() =>
    r'582c3e882c941b7f0bd02c63e71377b607737c84';

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

/// See also [motifDetailOfflineFirst].
@ProviderFor(motifDetailOfflineFirst)
const motifDetailOfflineFirstProvider = MotifDetailOfflineFirstFamily();

/// See also [motifDetailOfflineFirst].
class MotifDetailOfflineFirstFamily extends Family<AsyncValue<MotifDetailDto>> {
  /// See also [motifDetailOfflineFirst].
  const MotifDetailOfflineFirstFamily();

  /// See also [motifDetailOfflineFirst].
  MotifDetailOfflineFirstProvider call(
    String motifId,
  ) {
    return MotifDetailOfflineFirstProvider(
      motifId,
    );
  }

  @override
  MotifDetailOfflineFirstProvider getProviderOverride(
    covariant MotifDetailOfflineFirstProvider provider,
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
  String? get name => r'motifDetailOfflineFirstProvider';
}

/// See also [motifDetailOfflineFirst].
class MotifDetailOfflineFirstProvider
    extends AutoDisposeFutureProvider<MotifDetailDto> {
  /// See also [motifDetailOfflineFirst].
  MotifDetailOfflineFirstProvider(
    String motifId,
  ) : this._internal(
          (ref) => motifDetailOfflineFirst(
            ref as MotifDetailOfflineFirstRef,
            motifId,
          ),
          from: motifDetailOfflineFirstProvider,
          name: r'motifDetailOfflineFirstProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$motifDetailOfflineFirstHash,
          dependencies: MotifDetailOfflineFirstFamily._dependencies,
          allTransitiveDependencies:
              MotifDetailOfflineFirstFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  MotifDetailOfflineFirstProvider._internal(
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
    FutureOr<MotifDetailDto> Function(MotifDetailOfflineFirstRef provider)
        create,
  ) {
    return ProviderOverride(
      origin: this,
      override: MotifDetailOfflineFirstProvider._internal(
        (ref) => create(ref as MotifDetailOfflineFirstRef),
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
    return _MotifDetailOfflineFirstProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is MotifDetailOfflineFirstProvider && other.motifId == motifId;
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
mixin MotifDetailOfflineFirstRef
    on AutoDisposeFutureProviderRef<MotifDetailDto> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _MotifDetailOfflineFirstProviderElement
    extends AutoDisposeFutureProviderElement<MotifDetailDto>
    with MotifDetailOfflineFirstRef {
  _MotifDetailOfflineFirstProviderElement(super.provider);

  @override
  String get motifId => (origin as MotifDetailOfflineFirstProvider).motifId;
}

String _$lessonCompletionOfflineFirstHash() =>
    r'9914e7bb4a5c5e8ba6e2137488b01d727595e00b';

/// See also [LessonCompletionOfflineFirst].
@ProviderFor(LessonCompletionOfflineFirst)
final lessonCompletionOfflineFirstProvider = AutoDisposeAsyncNotifierProvider<
    LessonCompletionOfflineFirst, CompleteLessonResponseDto?>.internal(
  LessonCompletionOfflineFirst.new,
  name: r'lessonCompletionOfflineFirstProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$lessonCompletionOfflineFirstHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$LessonCompletionOfflineFirst
    = AutoDisposeAsyncNotifier<CompleteLessonResponseDto?>;
String _$quizSubmissionOfflineFirstHash() =>
    r'aaeb6b71be654299854f7cad4821a84f0f9a7af2';

/// See also [QuizSubmissionOfflineFirst].
@ProviderFor(QuizSubmissionOfflineFirst)
final quizSubmissionOfflineFirstProvider = AutoDisposeAsyncNotifierProvider<
    QuizSubmissionOfflineFirst, QuizResultDto?>.internal(
  QuizSubmissionOfflineFirst.new,
  name: r'quizSubmissionOfflineFirstProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$quizSubmissionOfflineFirstHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$QuizSubmissionOfflineFirst = AutoDisposeAsyncNotifier<QuizResultDto?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
