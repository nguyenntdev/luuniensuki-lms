// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'quiz_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$quizHash() => r'68d7d47c6f312fff7605bb7dead291b960919aa8';

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

/// Provider for fetching quiz questions for a motif.
///
/// Copied from [quiz].
@ProviderFor(quiz)
const quizProvider = QuizFamily();

/// Provider for fetching quiz questions for a motif.
///
/// Copied from [quiz].
class QuizFamily extends Family<AsyncValue<QuizResponseDto>> {
  /// Provider for fetching quiz questions for a motif.
  ///
  /// Copied from [quiz].
  const QuizFamily();

  /// Provider for fetching quiz questions for a motif.
  ///
  /// Copied from [quiz].
  QuizProvider call(
    String motifId,
  ) {
    return QuizProvider(
      motifId,
    );
  }

  @override
  QuizProvider getProviderOverride(
    covariant QuizProvider provider,
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
  String? get name => r'quizProvider';
}

/// Provider for fetching quiz questions for a motif.
///
/// Copied from [quiz].
class QuizProvider extends AutoDisposeFutureProvider<QuizResponseDto> {
  /// Provider for fetching quiz questions for a motif.
  ///
  /// Copied from [quiz].
  QuizProvider(
    String motifId,
  ) : this._internal(
          (ref) => quiz(
            ref as QuizRef,
            motifId,
          ),
          from: quizProvider,
          name: r'quizProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product') ? null : _$quizHash,
          dependencies: QuizFamily._dependencies,
          allTransitiveDependencies: QuizFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  QuizProvider._internal(
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
    FutureOr<QuizResponseDto> Function(QuizRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: QuizProvider._internal(
        (ref) => create(ref as QuizRef),
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
  AutoDisposeFutureProviderElement<QuizResponseDto> createElement() {
    return _QuizProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is QuizProvider && other.motifId == motifId;
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
mixin QuizRef on AutoDisposeFutureProviderRef<QuizResponseDto> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _QuizProviderElement
    extends AutoDisposeFutureProviderElement<QuizResponseDto> with QuizRef {
  _QuizProviderElement(super.provider);

  @override
  String get motifId => (origin as QuizProvider).motifId;
}

String _$quizHistoryHash() => r'737956c607a731c8afd1ce50124e95de9ac3976f';

/// Provider for quiz attempt history.
///
/// Copied from [quizHistory].
@ProviderFor(quizHistory)
const quizHistoryProvider = QuizHistoryFamily();

/// Provider for quiz attempt history.
///
/// Copied from [quizHistory].
class QuizHistoryFamily extends Family<AsyncValue<List<QuizAttemptDto>>> {
  /// Provider for quiz attempt history.
  ///
  /// Copied from [quizHistory].
  const QuizHistoryFamily();

  /// Provider for quiz attempt history.
  ///
  /// Copied from [quizHistory].
  QuizHistoryProvider call(
    String motifId,
  ) {
    return QuizHistoryProvider(
      motifId,
    );
  }

  @override
  QuizHistoryProvider getProviderOverride(
    covariant QuizHistoryProvider provider,
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
  String? get name => r'quizHistoryProvider';
}

/// Provider for quiz attempt history.
///
/// Copied from [quizHistory].
class QuizHistoryProvider
    extends AutoDisposeFutureProvider<List<QuizAttemptDto>> {
  /// Provider for quiz attempt history.
  ///
  /// Copied from [quizHistory].
  QuizHistoryProvider(
    String motifId,
  ) : this._internal(
          (ref) => quizHistory(
            ref as QuizHistoryRef,
            motifId,
          ),
          from: quizHistoryProvider,
          name: r'quizHistoryProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$quizHistoryHash,
          dependencies: QuizHistoryFamily._dependencies,
          allTransitiveDependencies:
              QuizHistoryFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  QuizHistoryProvider._internal(
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
    FutureOr<List<QuizAttemptDto>> Function(QuizHistoryRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: QuizHistoryProvider._internal(
        (ref) => create(ref as QuizHistoryRef),
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
  AutoDisposeFutureProviderElement<List<QuizAttemptDto>> createElement() {
    return _QuizHistoryProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is QuizHistoryProvider && other.motifId == motifId;
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
mixin QuizHistoryRef on AutoDisposeFutureProviderRef<List<QuizAttemptDto>> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _QuizHistoryProviderElement
    extends AutoDisposeFutureProviderElement<List<QuizAttemptDto>>
    with QuizHistoryRef {
  _QuizHistoryProviderElement(super.provider);

  @override
  String get motifId => (origin as QuizHistoryProvider).motifId;
}

String _$quizSubmissionHash() => r'68f3de687de4d33362930f0ccefc576ecc45a0cb';

/// Provider for submitting quiz answers.
///
/// Copied from [QuizSubmission].
@ProviderFor(QuizSubmission)
final quizSubmissionProvider =
    AutoDisposeAsyncNotifierProvider<QuizSubmission, QuizResultDto?>.internal(
  QuizSubmission.new,
  name: r'quizSubmissionProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$quizSubmissionHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$QuizSubmission = AutoDisposeAsyncNotifier<QuizResultDto?>;
String _$quizStateHash() => r'ea5ce3f7993ef3fccc99c61caa3b4226783038ad';

abstract class _$QuizState extends BuildlessAutoDisposeNotifier<QuizStateData> {
  late final String motifId;

  QuizStateData build(
    String motifId,
  );
}

/// Provider for quiz state management with auto-save
///
/// Copied from [QuizState].
@ProviderFor(QuizState)
const quizStateProvider = QuizStateFamily();

/// Provider for quiz state management with auto-save
///
/// Copied from [QuizState].
class QuizStateFamily extends Family<QuizStateData> {
  /// Provider for quiz state management with auto-save
  ///
  /// Copied from [QuizState].
  const QuizStateFamily();

  /// Provider for quiz state management with auto-save
  ///
  /// Copied from [QuizState].
  QuizStateProvider call(
    String motifId,
  ) {
    return QuizStateProvider(
      motifId,
    );
  }

  @override
  QuizStateProvider getProviderOverride(
    covariant QuizStateProvider provider,
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
  String? get name => r'quizStateProvider';
}

/// Provider for quiz state management with auto-save
///
/// Copied from [QuizState].
class QuizStateProvider
    extends AutoDisposeNotifierProviderImpl<QuizState, QuizStateData> {
  /// Provider for quiz state management with auto-save
  ///
  /// Copied from [QuizState].
  QuizStateProvider(
    String motifId,
  ) : this._internal(
          () => QuizState()..motifId = motifId,
          from: quizStateProvider,
          name: r'quizStateProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$quizStateHash,
          dependencies: QuizStateFamily._dependencies,
          allTransitiveDependencies: QuizStateFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  QuizStateProvider._internal(
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
  QuizStateData runNotifierBuild(
    covariant QuizState notifier,
  ) {
    return notifier.build(
      motifId,
    );
  }

  @override
  Override overrideWith(QuizState Function() create) {
    return ProviderOverride(
      origin: this,
      override: QuizStateProvider._internal(
        () => create()..motifId = motifId,
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
  AutoDisposeNotifierProviderElement<QuizState, QuizStateData> createElement() {
    return _QuizStateProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is QuizStateProvider && other.motifId == motifId;
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
mixin QuizStateRef on AutoDisposeNotifierProviderRef<QuizStateData> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _QuizStateProviderElement
    extends AutoDisposeNotifierProviderElement<QuizState, QuizStateData>
    with QuizStateRef {
  _QuizStateProviderElement(super.provider);

  @override
  String get motifId => (origin as QuizStateProvider).motifId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
