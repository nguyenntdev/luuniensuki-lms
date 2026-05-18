// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'urn_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$urnsHash() => r'9c9b5e9f7cbf58c431a002f119a19087488a01c5';

/// Provider for fetching list of all urns
///
/// Copied from [urns].
@ProviderFor(urns)
final urnsProvider = AutoDisposeFutureProvider<List<Urn>>.internal(
  urns,
  name: r'urnsProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$urnsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef UrnsRef = AutoDisposeFutureProviderRef<List<Urn>>;
String _$urnDetailHash() => r'61d7089eb67c4fc17487022eb7227100d6149926';

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

/// Provider for fetching urn detail with motifs
///
/// Copied from [urnDetail].
@ProviderFor(urnDetail)
const urnDetailProvider = UrnDetailFamily();

/// Provider for fetching urn detail with motifs
///
/// Copied from [urnDetail].
class UrnDetailFamily extends Family<AsyncValue<UrnDetail>> {
  /// Provider for fetching urn detail with motifs
  ///
  /// Copied from [urnDetail].
  const UrnDetailFamily();

  /// Provider for fetching urn detail with motifs
  ///
  /// Copied from [urnDetail].
  UrnDetailProvider call(
    String slug,
  ) {
    return UrnDetailProvider(
      slug,
    );
  }

  @override
  UrnDetailProvider getProviderOverride(
    covariant UrnDetailProvider provider,
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
  String? get name => r'urnDetailProvider';
}

/// Provider for fetching urn detail with motifs
///
/// Copied from [urnDetail].
class UrnDetailProvider extends AutoDisposeFutureProvider<UrnDetail> {
  /// Provider for fetching urn detail with motifs
  ///
  /// Copied from [urnDetail].
  UrnDetailProvider(
    String slug,
  ) : this._internal(
          (ref) => urnDetail(
            ref as UrnDetailRef,
            slug,
          ),
          from: urnDetailProvider,
          name: r'urnDetailProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$urnDetailHash,
          dependencies: UrnDetailFamily._dependencies,
          allTransitiveDependencies: UrnDetailFamily._allTransitiveDependencies,
          slug: slug,
        );

  UrnDetailProvider._internal(
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
    FutureOr<UrnDetail> Function(UrnDetailRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: UrnDetailProvider._internal(
        (ref) => create(ref as UrnDetailRef),
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
    return _UrnDetailProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is UrnDetailProvider && other.slug == slug;
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
mixin UrnDetailRef on AutoDisposeFutureProviderRef<UrnDetail> {
  /// The parameter `slug` of this provider.
  String get slug;
}

class _UrnDetailProviderElement
    extends AutoDisposeFutureProviderElement<UrnDetail> with UrnDetailRef {
  _UrnDetailProviderElement(super.provider);

  @override
  String get slug => (origin as UrnDetailProvider).slug;
}

String _$motifDetailHash() => r'cac6069ea95e5ff994578a4a6dba1b7f5ee25db3';

/// Provider for fetching a single motif detail
///
/// Copied from [motifDetail].
@ProviderFor(motifDetail)
const motifDetailProvider = MotifDetailFamily();

/// Provider for fetching a single motif detail
///
/// Copied from [motifDetail].
class MotifDetailFamily extends Family<AsyncValue<Motif>> {
  /// Provider for fetching a single motif detail
  ///
  /// Copied from [motifDetail].
  const MotifDetailFamily();

  /// Provider for fetching a single motif detail
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

/// Provider for fetching a single motif detail
///
/// Copied from [motifDetail].
class MotifDetailProvider extends AutoDisposeFutureProvider<Motif> {
  /// Provider for fetching a single motif detail
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
    FutureOr<Motif> Function(MotifDetailRef provider) create,
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
  AutoDisposeFutureProviderElement<Motif> createElement() {
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
mixin MotifDetailRef on AutoDisposeFutureProviderRef<Motif> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _MotifDetailProviderElement
    extends AutoDisposeFutureProviderElement<Motif> with MotifDetailRef {
  _MotifDetailProviderElement(super.provider);

  @override
  String get motifId => (origin as MotifDetailProvider).motifId;
}

String _$quizQuestionsHash() => r'8d1679ec26a669db4bf0c7549de7f476d2f3c5c8';

/// Provider for quiz questions
///
/// Copied from [quizQuestions].
@ProviderFor(quizQuestions)
const quizQuestionsProvider = QuizQuestionsFamily();

/// Provider for quiz questions
///
/// Copied from [quizQuestions].
class QuizQuestionsFamily extends Family<AsyncValue<List<QuizQuestionDto>>> {
  /// Provider for quiz questions
  ///
  /// Copied from [quizQuestions].
  const QuizQuestionsFamily();

  /// Provider for quiz questions
  ///
  /// Copied from [quizQuestions].
  QuizQuestionsProvider call(
    String motifId,
  ) {
    return QuizQuestionsProvider(
      motifId,
    );
  }

  @override
  QuizQuestionsProvider getProviderOverride(
    covariant QuizQuestionsProvider provider,
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
  String? get name => r'quizQuestionsProvider';
}

/// Provider for quiz questions
///
/// Copied from [quizQuestions].
class QuizQuestionsProvider
    extends AutoDisposeFutureProvider<List<QuizQuestionDto>> {
  /// Provider for quiz questions
  ///
  /// Copied from [quizQuestions].
  QuizQuestionsProvider(
    String motifId,
  ) : this._internal(
          (ref) => quizQuestions(
            ref as QuizQuestionsRef,
            motifId,
          ),
          from: quizQuestionsProvider,
          name: r'quizQuestionsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$quizQuestionsHash,
          dependencies: QuizQuestionsFamily._dependencies,
          allTransitiveDependencies:
              QuizQuestionsFamily._allTransitiveDependencies,
          motifId: motifId,
        );

  QuizQuestionsProvider._internal(
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
    FutureOr<List<QuizQuestionDto>> Function(QuizQuestionsRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: QuizQuestionsProvider._internal(
        (ref) => create(ref as QuizQuestionsRef),
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
  AutoDisposeFutureProviderElement<List<QuizQuestionDto>> createElement() {
    return _QuizQuestionsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is QuizQuestionsProvider && other.motifId == motifId;
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
mixin QuizQuestionsRef on AutoDisposeFutureProviderRef<List<QuizQuestionDto>> {
  /// The parameter `motifId` of this provider.
  String get motifId;
}

class _QuizQuestionsProviderElement
    extends AutoDisposeFutureProviderElement<List<QuizQuestionDto>>
    with QuizQuestionsRef {
  _QuizQuestionsProviderElement(super.provider);

  @override
  String get motifId => (origin as QuizQuestionsProvider).motifId;
}

String _$discoveryNotifierHash() => r'c3b4a53abebcdfc9492394a94951e6f425260da5';

/// Notifier for handling motif discovery/unlock actions
///
/// Copied from [DiscoveryNotifier].
@ProviderFor(DiscoveryNotifier)
final discoveryNotifierProvider =
    AutoDisposeNotifierProvider<DiscoveryNotifier, DiscoveryState>.internal(
  DiscoveryNotifier.new,
  name: r'discoveryNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$discoveryNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DiscoveryNotifier = AutoDisposeNotifier<DiscoveryState>;
String _$quizSubmissionNotifierHash() =>
    r'b4428b24564e084d48bafde09fa2189f7db9e9d2';

/// Notifier for quiz submission
///
/// Copied from [QuizSubmissionNotifier].
@ProviderFor(QuizSubmissionNotifier)
final quizSubmissionNotifierProvider = AutoDisposeNotifierProvider<
    QuizSubmissionNotifier, QuizSubmissionState>.internal(
  QuizSubmissionNotifier.new,
  name: r'quizSubmissionNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$quizSubmissionNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$QuizSubmissionNotifier = AutoDisposeNotifier<QuizSubmissionState>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
