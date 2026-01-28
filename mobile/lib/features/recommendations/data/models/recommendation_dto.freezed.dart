// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'recommendation_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

RecommendationItemDto _$RecommendationItemDtoFromJson(
    Map<String, dynamic> json) {
  return _RecommendationItemDto.fromJson(json);
}

/// @nodoc
mixin _$RecommendationItemDto {
  @JsonKey(name: 'content_type')
  String get contentType => throw _privateConstructorUsedError;
  @JsonKey(name: 'content_id')
  String get contentId => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get reason => throw _privateConstructorUsedError;
  double? get score => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_id')
  String? get motifId => throw _privateConstructorUsedError;
  String? get status => throw _privateConstructorUsedError;
  @JsonKey(name: 'last_completed')
  String? get lastCompleted => throw _privateConstructorUsedError;
  @JsonKey(name: 'popularity_score')
  int? get popularityScore => throw _privateConstructorUsedError;
  @JsonKey(name: 'similarity_score')
  double? get similarityScore => throw _privateConstructorUsedError;

  /// Serializes this RecommendationItemDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RecommendationItemDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RecommendationItemDtoCopyWith<RecommendationItemDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RecommendationItemDtoCopyWith<$Res> {
  factory $RecommendationItemDtoCopyWith(RecommendationItemDto value,
          $Res Function(RecommendationItemDto) then) =
      _$RecommendationItemDtoCopyWithImpl<$Res, RecommendationItemDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'content_type') String contentType,
      @JsonKey(name: 'content_id') String contentId,
      String title,
      String? description,
      String? reason,
      double? score,
      @JsonKey(name: 'motif_id') String? motifId,
      String? status,
      @JsonKey(name: 'last_completed') String? lastCompleted,
      @JsonKey(name: 'popularity_score') int? popularityScore,
      @JsonKey(name: 'similarity_score') double? similarityScore});
}

/// @nodoc
class _$RecommendationItemDtoCopyWithImpl<$Res,
        $Val extends RecommendationItemDto>
    implements $RecommendationItemDtoCopyWith<$Res> {
  _$RecommendationItemDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RecommendationItemDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? contentType = null,
    Object? contentId = null,
    Object? title = null,
    Object? description = freezed,
    Object? reason = freezed,
    Object? score = freezed,
    Object? motifId = freezed,
    Object? status = freezed,
    Object? lastCompleted = freezed,
    Object? popularityScore = freezed,
    Object? similarityScore = freezed,
  }) {
    return _then(_value.copyWith(
      contentType: null == contentType
          ? _value.contentType
          : contentType // ignore: cast_nullable_to_non_nullable
              as String,
      contentId: null == contentId
          ? _value.contentId
          : contentId // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      reason: freezed == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String?,
      score: freezed == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as double?,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      status: freezed == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String?,
      lastCompleted: freezed == lastCompleted
          ? _value.lastCompleted
          : lastCompleted // ignore: cast_nullable_to_non_nullable
              as String?,
      popularityScore: freezed == popularityScore
          ? _value.popularityScore
          : popularityScore // ignore: cast_nullable_to_non_nullable
              as int?,
      similarityScore: freezed == similarityScore
          ? _value.similarityScore
          : similarityScore // ignore: cast_nullable_to_non_nullable
              as double?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RecommendationItemDtoImplCopyWith<$Res>
    implements $RecommendationItemDtoCopyWith<$Res> {
  factory _$$RecommendationItemDtoImplCopyWith(
          _$RecommendationItemDtoImpl value,
          $Res Function(_$RecommendationItemDtoImpl) then) =
      __$$RecommendationItemDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'content_type') String contentType,
      @JsonKey(name: 'content_id') String contentId,
      String title,
      String? description,
      String? reason,
      double? score,
      @JsonKey(name: 'motif_id') String? motifId,
      String? status,
      @JsonKey(name: 'last_completed') String? lastCompleted,
      @JsonKey(name: 'popularity_score') int? popularityScore,
      @JsonKey(name: 'similarity_score') double? similarityScore});
}

/// @nodoc
class __$$RecommendationItemDtoImplCopyWithImpl<$Res>
    extends _$RecommendationItemDtoCopyWithImpl<$Res,
        _$RecommendationItemDtoImpl>
    implements _$$RecommendationItemDtoImplCopyWith<$Res> {
  __$$RecommendationItemDtoImplCopyWithImpl(_$RecommendationItemDtoImpl _value,
      $Res Function(_$RecommendationItemDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of RecommendationItemDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? contentType = null,
    Object? contentId = null,
    Object? title = null,
    Object? description = freezed,
    Object? reason = freezed,
    Object? score = freezed,
    Object? motifId = freezed,
    Object? status = freezed,
    Object? lastCompleted = freezed,
    Object? popularityScore = freezed,
    Object? similarityScore = freezed,
  }) {
    return _then(_$RecommendationItemDtoImpl(
      contentType: null == contentType
          ? _value.contentType
          : contentType // ignore: cast_nullable_to_non_nullable
              as String,
      contentId: null == contentId
          ? _value.contentId
          : contentId // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      reason: freezed == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String?,
      score: freezed == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as double?,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      status: freezed == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String?,
      lastCompleted: freezed == lastCompleted
          ? _value.lastCompleted
          : lastCompleted // ignore: cast_nullable_to_non_nullable
              as String?,
      popularityScore: freezed == popularityScore
          ? _value.popularityScore
          : popularityScore // ignore: cast_nullable_to_non_nullable
              as int?,
      similarityScore: freezed == similarityScore
          ? _value.similarityScore
          : similarityScore // ignore: cast_nullable_to_non_nullable
              as double?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RecommendationItemDtoImpl implements _RecommendationItemDto {
  const _$RecommendationItemDtoImpl(
      {@JsonKey(name: 'content_type') required this.contentType,
      @JsonKey(name: 'content_id') required this.contentId,
      required this.title,
      this.description,
      this.reason,
      this.score,
      @JsonKey(name: 'motif_id') this.motifId,
      this.status,
      @JsonKey(name: 'last_completed') this.lastCompleted,
      @JsonKey(name: 'popularity_score') this.popularityScore,
      @JsonKey(name: 'similarity_score') this.similarityScore});

  factory _$RecommendationItemDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$RecommendationItemDtoImplFromJson(json);

  @override
  @JsonKey(name: 'content_type')
  final String contentType;
  @override
  @JsonKey(name: 'content_id')
  final String contentId;
  @override
  final String title;
  @override
  final String? description;
  @override
  final String? reason;
  @override
  final double? score;
  @override
  @JsonKey(name: 'motif_id')
  final String? motifId;
  @override
  final String? status;
  @override
  @JsonKey(name: 'last_completed')
  final String? lastCompleted;
  @override
  @JsonKey(name: 'popularity_score')
  final int? popularityScore;
  @override
  @JsonKey(name: 'similarity_score')
  final double? similarityScore;

  @override
  String toString() {
    return 'RecommendationItemDto(contentType: $contentType, contentId: $contentId, title: $title, description: $description, reason: $reason, score: $score, motifId: $motifId, status: $status, lastCompleted: $lastCompleted, popularityScore: $popularityScore, similarityScore: $similarityScore)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RecommendationItemDtoImpl &&
            (identical(other.contentType, contentType) ||
                other.contentType == contentType) &&
            (identical(other.contentId, contentId) ||
                other.contentId == contentId) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.reason, reason) || other.reason == reason) &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.lastCompleted, lastCompleted) ||
                other.lastCompleted == lastCompleted) &&
            (identical(other.popularityScore, popularityScore) ||
                other.popularityScore == popularityScore) &&
            (identical(other.similarityScore, similarityScore) ||
                other.similarityScore == similarityScore));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      contentType,
      contentId,
      title,
      description,
      reason,
      score,
      motifId,
      status,
      lastCompleted,
      popularityScore,
      similarityScore);

  /// Create a copy of RecommendationItemDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RecommendationItemDtoImplCopyWith<_$RecommendationItemDtoImpl>
      get copyWith => __$$RecommendationItemDtoImplCopyWithImpl<
          _$RecommendationItemDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RecommendationItemDtoImplToJson(
      this,
    );
  }
}

abstract class _RecommendationItemDto implements RecommendationItemDto {
  const factory _RecommendationItemDto(
          {@JsonKey(name: 'content_type') required final String contentType,
          @JsonKey(name: 'content_id') required final String contentId,
          required final String title,
          final String? description,
          final String? reason,
          final double? score,
          @JsonKey(name: 'motif_id') final String? motifId,
          final String? status,
          @JsonKey(name: 'last_completed') final String? lastCompleted,
          @JsonKey(name: 'popularity_score') final int? popularityScore,
          @JsonKey(name: 'similarity_score') final double? similarityScore}) =
      _$RecommendationItemDtoImpl;

  factory _RecommendationItemDto.fromJson(Map<String, dynamic> json) =
      _$RecommendationItemDtoImpl.fromJson;

  @override
  @JsonKey(name: 'content_type')
  String get contentType;
  @override
  @JsonKey(name: 'content_id')
  String get contentId;
  @override
  String get title;
  @override
  String? get description;
  @override
  String? get reason;
  @override
  double? get score;
  @override
  @JsonKey(name: 'motif_id')
  String? get motifId;
  @override
  String? get status;
  @override
  @JsonKey(name: 'last_completed')
  String? get lastCompleted;
  @override
  @JsonKey(name: 'popularity_score')
  int? get popularityScore;
  @override
  @JsonKey(name: 'similarity_score')
  double? get similarityScore;

  /// Create a copy of RecommendationItemDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RecommendationItemDtoImplCopyWith<_$RecommendationItemDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

RecommendationsResponseDto _$RecommendationsResponseDtoFromJson(
    Map<String, dynamic> json) {
  return _RecommendationsResponseDto.fromJson(json);
}

/// @nodoc
mixin _$RecommendationsResponseDto {
  @JsonKey(name: 'continue_learning')
  List<RecommendationItemDto>? get continueLearning =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'discover_new')
  List<RecommendationItemDto>? get discoverNew =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'review_needed')
  List<RecommendationItemDto>? get reviewNeeded =>
      throw _privateConstructorUsedError;
  List<RecommendationItemDto>? get popular =>
      throw _privateConstructorUsedError;

  /// Serializes this RecommendationsResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RecommendationsResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RecommendationsResponseDtoCopyWith<RecommendationsResponseDto>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RecommendationsResponseDtoCopyWith<$Res> {
  factory $RecommendationsResponseDtoCopyWith(RecommendationsResponseDto value,
          $Res Function(RecommendationsResponseDto) then) =
      _$RecommendationsResponseDtoCopyWithImpl<$Res,
          RecommendationsResponseDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'continue_learning')
      List<RecommendationItemDto>? continueLearning,
      @JsonKey(name: 'discover_new') List<RecommendationItemDto>? discoverNew,
      @JsonKey(name: 'review_needed') List<RecommendationItemDto>? reviewNeeded,
      List<RecommendationItemDto>? popular});
}

/// @nodoc
class _$RecommendationsResponseDtoCopyWithImpl<$Res,
        $Val extends RecommendationsResponseDto>
    implements $RecommendationsResponseDtoCopyWith<$Res> {
  _$RecommendationsResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RecommendationsResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? continueLearning = freezed,
    Object? discoverNew = freezed,
    Object? reviewNeeded = freezed,
    Object? popular = freezed,
  }) {
    return _then(_value.copyWith(
      continueLearning: freezed == continueLearning
          ? _value.continueLearning
          : continueLearning // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      discoverNew: freezed == discoverNew
          ? _value.discoverNew
          : discoverNew // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      reviewNeeded: freezed == reviewNeeded
          ? _value.reviewNeeded
          : reviewNeeded // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      popular: freezed == popular
          ? _value.popular
          : popular // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RecommendationsResponseDtoImplCopyWith<$Res>
    implements $RecommendationsResponseDtoCopyWith<$Res> {
  factory _$$RecommendationsResponseDtoImplCopyWith(
          _$RecommendationsResponseDtoImpl value,
          $Res Function(_$RecommendationsResponseDtoImpl) then) =
      __$$RecommendationsResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'continue_learning')
      List<RecommendationItemDto>? continueLearning,
      @JsonKey(name: 'discover_new') List<RecommendationItemDto>? discoverNew,
      @JsonKey(name: 'review_needed') List<RecommendationItemDto>? reviewNeeded,
      List<RecommendationItemDto>? popular});
}

/// @nodoc
class __$$RecommendationsResponseDtoImplCopyWithImpl<$Res>
    extends _$RecommendationsResponseDtoCopyWithImpl<$Res,
        _$RecommendationsResponseDtoImpl>
    implements _$$RecommendationsResponseDtoImplCopyWith<$Res> {
  __$$RecommendationsResponseDtoImplCopyWithImpl(
      _$RecommendationsResponseDtoImpl _value,
      $Res Function(_$RecommendationsResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of RecommendationsResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? continueLearning = freezed,
    Object? discoverNew = freezed,
    Object? reviewNeeded = freezed,
    Object? popular = freezed,
  }) {
    return _then(_$RecommendationsResponseDtoImpl(
      continueLearning: freezed == continueLearning
          ? _value._continueLearning
          : continueLearning // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      discoverNew: freezed == discoverNew
          ? _value._discoverNew
          : discoverNew // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      reviewNeeded: freezed == reviewNeeded
          ? _value._reviewNeeded
          : reviewNeeded // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
      popular: freezed == popular
          ? _value._popular
          : popular // ignore: cast_nullable_to_non_nullable
              as List<RecommendationItemDto>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RecommendationsResponseDtoImpl implements _RecommendationsResponseDto {
  const _$RecommendationsResponseDtoImpl(
      {@JsonKey(name: 'continue_learning')
      final List<RecommendationItemDto>? continueLearning,
      @JsonKey(name: 'discover_new')
      final List<RecommendationItemDto>? discoverNew,
      @JsonKey(name: 'review_needed')
      final List<RecommendationItemDto>? reviewNeeded,
      final List<RecommendationItemDto>? popular})
      : _continueLearning = continueLearning,
        _discoverNew = discoverNew,
        _reviewNeeded = reviewNeeded,
        _popular = popular;

  factory _$RecommendationsResponseDtoImpl.fromJson(
          Map<String, dynamic> json) =>
      _$$RecommendationsResponseDtoImplFromJson(json);

  final List<RecommendationItemDto>? _continueLearning;
  @override
  @JsonKey(name: 'continue_learning')
  List<RecommendationItemDto>? get continueLearning {
    final value = _continueLearning;
    if (value == null) return null;
    if (_continueLearning is EqualUnmodifiableListView)
      return _continueLearning;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<RecommendationItemDto>? _discoverNew;
  @override
  @JsonKey(name: 'discover_new')
  List<RecommendationItemDto>? get discoverNew {
    final value = _discoverNew;
    if (value == null) return null;
    if (_discoverNew is EqualUnmodifiableListView) return _discoverNew;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<RecommendationItemDto>? _reviewNeeded;
  @override
  @JsonKey(name: 'review_needed')
  List<RecommendationItemDto>? get reviewNeeded {
    final value = _reviewNeeded;
    if (value == null) return null;
    if (_reviewNeeded is EqualUnmodifiableListView) return _reviewNeeded;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<RecommendationItemDto>? _popular;
  @override
  List<RecommendationItemDto>? get popular {
    final value = _popular;
    if (value == null) return null;
    if (_popular is EqualUnmodifiableListView) return _popular;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'RecommendationsResponseDto(continueLearning: $continueLearning, discoverNew: $discoverNew, reviewNeeded: $reviewNeeded, popular: $popular)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RecommendationsResponseDtoImpl &&
            const DeepCollectionEquality()
                .equals(other._continueLearning, _continueLearning) &&
            const DeepCollectionEquality()
                .equals(other._discoverNew, _discoverNew) &&
            const DeepCollectionEquality()
                .equals(other._reviewNeeded, _reviewNeeded) &&
            const DeepCollectionEquality().equals(other._popular, _popular));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_continueLearning),
      const DeepCollectionEquality().hash(_discoverNew),
      const DeepCollectionEquality().hash(_reviewNeeded),
      const DeepCollectionEquality().hash(_popular));

  /// Create a copy of RecommendationsResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RecommendationsResponseDtoImplCopyWith<_$RecommendationsResponseDtoImpl>
      get copyWith => __$$RecommendationsResponseDtoImplCopyWithImpl<
          _$RecommendationsResponseDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RecommendationsResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _RecommendationsResponseDto
    implements RecommendationsResponseDto {
  const factory _RecommendationsResponseDto(
          {@JsonKey(name: 'continue_learning')
          final List<RecommendationItemDto>? continueLearning,
          @JsonKey(name: 'discover_new')
          final List<RecommendationItemDto>? discoverNew,
          @JsonKey(name: 'review_needed')
          final List<RecommendationItemDto>? reviewNeeded,
          final List<RecommendationItemDto>? popular}) =
      _$RecommendationsResponseDtoImpl;

  factory _RecommendationsResponseDto.fromJson(Map<String, dynamic> json) =
      _$RecommendationsResponseDtoImpl.fromJson;

  @override
  @JsonKey(name: 'continue_learning')
  List<RecommendationItemDto>? get continueLearning;
  @override
  @JsonKey(name: 'discover_new')
  List<RecommendationItemDto>? get discoverNew;
  @override
  @JsonKey(name: 'review_needed')
  List<RecommendationItemDto>? get reviewNeeded;
  @override
  List<RecommendationItemDto>? get popular;

  /// Create a copy of RecommendationsResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RecommendationsResponseDtoImplCopyWith<_$RecommendationsResponseDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}
