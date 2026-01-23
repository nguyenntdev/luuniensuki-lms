// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'urn_dtos.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

UrnListItemDto _$UrnListItemDtoFromJson(Map<String, dynamic> json) {
  return _UrnListItemDto.fromJson(json);
}

/// @nodoc
mixin _$UrnListItemDto {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_order')
  int get displayOrder => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'model_url')
  String? get modelUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_count')
  int get motifCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'discovered_count')
  int get discoveredCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'learned_count')
  int get learnedCount => throw _privateConstructorUsedError;
  @JsonKey(name: 'mastered_count')
  int get masteredCount => throw _privateConstructorUsedError;

  /// Serializes this UrnListItemDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UrnListItemDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UrnListItemDtoCopyWith<UrnListItemDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UrnListItemDtoCopyWith<$Res> {
  factory $UrnListItemDtoCopyWith(
          UrnListItemDto value, $Res Function(UrnListItemDto) then) =
      _$UrnListItemDtoCopyWithImpl<$Res, UrnListItemDto>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'motif_count') int motifCount,
      @JsonKey(name: 'discovered_count') int discoveredCount,
      @JsonKey(name: 'learned_count') int learnedCount,
      @JsonKey(name: 'mastered_count') int masteredCount});
}

/// @nodoc
class _$UrnListItemDtoCopyWithImpl<$Res, $Val extends UrnListItemDto>
    implements $UrnListItemDtoCopyWith<$Res> {
  _$UrnListItemDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UrnListItemDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? displayOrder = null,
    Object? thumbnailUrl = freezed,
    Object? modelUrl = freezed,
    Object? motifCount = null,
    Object? discoveredCount = null,
    Object? learnedCount = null,
    Object? masteredCount = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      motifCount: null == motifCount
          ? _value.motifCount
          : motifCount // ignore: cast_nullable_to_non_nullable
              as int,
      discoveredCount: null == discoveredCount
          ? _value.discoveredCount
          : discoveredCount // ignore: cast_nullable_to_non_nullable
              as int,
      learnedCount: null == learnedCount
          ? _value.learnedCount
          : learnedCount // ignore: cast_nullable_to_non_nullable
              as int,
      masteredCount: null == masteredCount
          ? _value.masteredCount
          : masteredCount // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UrnListItemDtoImplCopyWith<$Res>
    implements $UrnListItemDtoCopyWith<$Res> {
  factory _$$UrnListItemDtoImplCopyWith(_$UrnListItemDtoImpl value,
          $Res Function(_$UrnListItemDtoImpl) then) =
      __$$UrnListItemDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'motif_count') int motifCount,
      @JsonKey(name: 'discovered_count') int discoveredCount,
      @JsonKey(name: 'learned_count') int learnedCount,
      @JsonKey(name: 'mastered_count') int masteredCount});
}

/// @nodoc
class __$$UrnListItemDtoImplCopyWithImpl<$Res>
    extends _$UrnListItemDtoCopyWithImpl<$Res, _$UrnListItemDtoImpl>
    implements _$$UrnListItemDtoImplCopyWith<$Res> {
  __$$UrnListItemDtoImplCopyWithImpl(
      _$UrnListItemDtoImpl _value, $Res Function(_$UrnListItemDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UrnListItemDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? displayOrder = null,
    Object? thumbnailUrl = freezed,
    Object? modelUrl = freezed,
    Object? motifCount = null,
    Object? discoveredCount = null,
    Object? learnedCount = null,
    Object? masteredCount = null,
  }) {
    return _then(_$UrnListItemDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      motifCount: null == motifCount
          ? _value.motifCount
          : motifCount // ignore: cast_nullable_to_non_nullable
              as int,
      discoveredCount: null == discoveredCount
          ? _value.discoveredCount
          : discoveredCount // ignore: cast_nullable_to_non_nullable
              as int,
      learnedCount: null == learnedCount
          ? _value.learnedCount
          : learnedCount // ignore: cast_nullable_to_non_nullable
              as int,
      masteredCount: null == masteredCount
          ? _value.masteredCount
          : masteredCount // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UrnListItemDtoImpl implements _UrnListItemDto {
  const _$UrnListItemDtoImpl(
      {required this.id,
      required this.slug,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      @JsonKey(name: 'display_order') this.displayOrder = 0,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      @JsonKey(name: 'model_url') this.modelUrl,
      @JsonKey(name: 'motif_count') this.motifCount = 0,
      @JsonKey(name: 'discovered_count') this.discoveredCount = 0,
      @JsonKey(name: 'learned_count') this.learnedCount = 0,
      @JsonKey(name: 'mastered_count') this.masteredCount = 0});

  factory _$UrnListItemDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UrnListItemDtoImplFromJson(json);

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  @JsonKey(name: 'display_order')
  final int displayOrder;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  @JsonKey(name: 'model_url')
  final String? modelUrl;
  @override
  @JsonKey(name: 'motif_count')
  final int motifCount;
  @override
  @JsonKey(name: 'discovered_count')
  final int discoveredCount;
  @override
  @JsonKey(name: 'learned_count')
  final int learnedCount;
  @override
  @JsonKey(name: 'mastered_count')
  final int masteredCount;

  @override
  String toString() {
    return 'UrnListItemDto(id: $id, slug: $slug, name: $name, nameEn: $nameEn, displayOrder: $displayOrder, thumbnailUrl: $thumbnailUrl, modelUrl: $modelUrl, motifCount: $motifCount, discoveredCount: $discoveredCount, learnedCount: $learnedCount, masteredCount: $masteredCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UrnListItemDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.displayOrder, displayOrder) ||
                other.displayOrder == displayOrder) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.modelUrl, modelUrl) ||
                other.modelUrl == modelUrl) &&
            (identical(other.motifCount, motifCount) ||
                other.motifCount == motifCount) &&
            (identical(other.discoveredCount, discoveredCount) ||
                other.discoveredCount == discoveredCount) &&
            (identical(other.learnedCount, learnedCount) ||
                other.learnedCount == learnedCount) &&
            (identical(other.masteredCount, masteredCount) ||
                other.masteredCount == masteredCount));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      slug,
      name,
      nameEn,
      displayOrder,
      thumbnailUrl,
      modelUrl,
      motifCount,
      discoveredCount,
      learnedCount,
      masteredCount);

  /// Create a copy of UrnListItemDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UrnListItemDtoImplCopyWith<_$UrnListItemDtoImpl> get copyWith =>
      __$$UrnListItemDtoImplCopyWithImpl<_$UrnListItemDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UrnListItemDtoImplToJson(
      this,
    );
  }
}

abstract class _UrnListItemDto implements UrnListItemDto {
  const factory _UrnListItemDto(
          {required final String id,
          required final String slug,
          required final String name,
          @JsonKey(name: 'name_en') final String? nameEn,
          @JsonKey(name: 'display_order') final int displayOrder,
          @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
          @JsonKey(name: 'model_url') final String? modelUrl,
          @JsonKey(name: 'motif_count') final int motifCount,
          @JsonKey(name: 'discovered_count') final int discoveredCount,
          @JsonKey(name: 'learned_count') final int learnedCount,
          @JsonKey(name: 'mastered_count') final int masteredCount}) =
      _$UrnListItemDtoImpl;

  factory _UrnListItemDto.fromJson(Map<String, dynamic> json) =
      _$UrnListItemDtoImpl.fromJson;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  @JsonKey(name: 'display_order')
  int get displayOrder;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  @JsonKey(name: 'model_url')
  String? get modelUrl;
  @override
  @JsonKey(name: 'motif_count')
  int get motifCount;
  @override
  @JsonKey(name: 'discovered_count')
  int get discoveredCount;
  @override
  @JsonKey(name: 'learned_count')
  int get learnedCount;
  @override
  @JsonKey(name: 'mastered_count')
  int get masteredCount;

  /// Create a copy of UrnListItemDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UrnListItemDtoImplCopyWith<_$UrnListItemDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UrnDetailResponseDto _$UrnDetailResponseDtoFromJson(Map<String, dynamic> json) {
  return _UrnDetailResponseDto.fromJson(json);
}

/// @nodoc
mixin _$UrnDetailResponseDto {
  UrnDetailDto get urn => throw _privateConstructorUsedError;
  List<MotifDto> get motifs => throw _privateConstructorUsedError;

  /// Serializes this UrnDetailResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UrnDetailResponseDtoCopyWith<UrnDetailResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UrnDetailResponseDtoCopyWith<$Res> {
  factory $UrnDetailResponseDtoCopyWith(UrnDetailResponseDto value,
          $Res Function(UrnDetailResponseDto) then) =
      _$UrnDetailResponseDtoCopyWithImpl<$Res, UrnDetailResponseDto>;
  @useResult
  $Res call({UrnDetailDto urn, List<MotifDto> motifs});

  $UrnDetailDtoCopyWith<$Res> get urn;
}

/// @nodoc
class _$UrnDetailResponseDtoCopyWithImpl<$Res,
        $Val extends UrnDetailResponseDto>
    implements $UrnDetailResponseDtoCopyWith<$Res> {
  _$UrnDetailResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? urn = null,
    Object? motifs = null,
  }) {
    return _then(_value.copyWith(
      urn: null == urn
          ? _value.urn
          : urn // ignore: cast_nullable_to_non_nullable
              as UrnDetailDto,
      motifs: null == motifs
          ? _value.motifs
          : motifs // ignore: cast_nullable_to_non_nullable
              as List<MotifDto>,
    ) as $Val);
  }

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UrnDetailDtoCopyWith<$Res> get urn {
    return $UrnDetailDtoCopyWith<$Res>(_value.urn, (value) {
      return _then(_value.copyWith(urn: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$UrnDetailResponseDtoImplCopyWith<$Res>
    implements $UrnDetailResponseDtoCopyWith<$Res> {
  factory _$$UrnDetailResponseDtoImplCopyWith(_$UrnDetailResponseDtoImpl value,
          $Res Function(_$UrnDetailResponseDtoImpl) then) =
      __$$UrnDetailResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({UrnDetailDto urn, List<MotifDto> motifs});

  @override
  $UrnDetailDtoCopyWith<$Res> get urn;
}

/// @nodoc
class __$$UrnDetailResponseDtoImplCopyWithImpl<$Res>
    extends _$UrnDetailResponseDtoCopyWithImpl<$Res, _$UrnDetailResponseDtoImpl>
    implements _$$UrnDetailResponseDtoImplCopyWith<$Res> {
  __$$UrnDetailResponseDtoImplCopyWithImpl(_$UrnDetailResponseDtoImpl _value,
      $Res Function(_$UrnDetailResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? urn = null,
    Object? motifs = null,
  }) {
    return _then(_$UrnDetailResponseDtoImpl(
      urn: null == urn
          ? _value.urn
          : urn // ignore: cast_nullable_to_non_nullable
              as UrnDetailDto,
      motifs: null == motifs
          ? _value._motifs
          : motifs // ignore: cast_nullable_to_non_nullable
              as List<MotifDto>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UrnDetailResponseDtoImpl implements _UrnDetailResponseDto {
  const _$UrnDetailResponseDtoImpl(
      {required this.urn, final List<MotifDto> motifs = const []})
      : _motifs = motifs;

  factory _$UrnDetailResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UrnDetailResponseDtoImplFromJson(json);

  @override
  final UrnDetailDto urn;
  final List<MotifDto> _motifs;
  @override
  @JsonKey()
  List<MotifDto> get motifs {
    if (_motifs is EqualUnmodifiableListView) return _motifs;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_motifs);
  }

  @override
  String toString() {
    return 'UrnDetailResponseDto(urn: $urn, motifs: $motifs)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UrnDetailResponseDtoImpl &&
            (identical(other.urn, urn) || other.urn == urn) &&
            const DeepCollectionEquality().equals(other._motifs, _motifs));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, urn, const DeepCollectionEquality().hash(_motifs));

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UrnDetailResponseDtoImplCopyWith<_$UrnDetailResponseDtoImpl>
      get copyWith =>
          __$$UrnDetailResponseDtoImplCopyWithImpl<_$UrnDetailResponseDtoImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UrnDetailResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _UrnDetailResponseDto implements UrnDetailResponseDto {
  const factory _UrnDetailResponseDto(
      {required final UrnDetailDto urn,
      final List<MotifDto> motifs}) = _$UrnDetailResponseDtoImpl;

  factory _UrnDetailResponseDto.fromJson(Map<String, dynamic> json) =
      _$UrnDetailResponseDtoImpl.fromJson;

  @override
  UrnDetailDto get urn;
  @override
  List<MotifDto> get motifs;

  /// Create a copy of UrnDetailResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UrnDetailResponseDtoImplCopyWith<_$UrnDetailResponseDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

UrnDetailDto _$UrnDetailDtoFromJson(Map<String, dynamic> json) {
  return _UrnDetailDto.fromJson(json);
}

/// @nodoc
mixin _$UrnDetailDto {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_han')
  String? get nameHan => throw _privateConstructorUsedError;
  String? get represents => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  @JsonKey(name: 'description_en')
  String? get descriptionEn => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_order')
  int get displayOrder => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'model_url')
  String? get modelUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_demo')
  bool get isDemo => throw _privateConstructorUsedError;

  /// Serializes this UrnDetailDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UrnDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UrnDetailDtoCopyWith<UrnDetailDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UrnDetailDtoCopyWith<$Res> {
  factory $UrnDetailDtoCopyWith(
          UrnDetailDto value, $Res Function(UrnDetailDto) then) =
      _$UrnDetailDtoCopyWithImpl<$Res, UrnDetailDto>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      @JsonKey(name: 'name_han') String? nameHan,
      String? represents,
      String? description,
      @JsonKey(name: 'description_en') String? descriptionEn,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'is_demo') bool isDemo});
}

/// @nodoc
class _$UrnDetailDtoCopyWithImpl<$Res, $Val extends UrnDetailDto>
    implements $UrnDetailDtoCopyWith<$Res> {
  _$UrnDetailDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UrnDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? nameHan = freezed,
    Object? represents = freezed,
    Object? description = freezed,
    Object? descriptionEn = freezed,
    Object? displayOrder = null,
    Object? thumbnailUrl = freezed,
    Object? modelUrl = freezed,
    Object? isDemo = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      nameHan: freezed == nameHan
          ? _value.nameHan
          : nameHan // ignore: cast_nullable_to_non_nullable
              as String?,
      represents: freezed == represents
          ? _value.represents
          : represents // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      descriptionEn: freezed == descriptionEn
          ? _value.descriptionEn
          : descriptionEn // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UrnDetailDtoImplCopyWith<$Res>
    implements $UrnDetailDtoCopyWith<$Res> {
  factory _$$UrnDetailDtoImplCopyWith(
          _$UrnDetailDtoImpl value, $Res Function(_$UrnDetailDtoImpl) then) =
      __$$UrnDetailDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      @JsonKey(name: 'name_han') String? nameHan,
      String? represents,
      String? description,
      @JsonKey(name: 'description_en') String? descriptionEn,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'is_demo') bool isDemo});
}

/// @nodoc
class __$$UrnDetailDtoImplCopyWithImpl<$Res>
    extends _$UrnDetailDtoCopyWithImpl<$Res, _$UrnDetailDtoImpl>
    implements _$$UrnDetailDtoImplCopyWith<$Res> {
  __$$UrnDetailDtoImplCopyWithImpl(
      _$UrnDetailDtoImpl _value, $Res Function(_$UrnDetailDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UrnDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? nameHan = freezed,
    Object? represents = freezed,
    Object? description = freezed,
    Object? descriptionEn = freezed,
    Object? displayOrder = null,
    Object? thumbnailUrl = freezed,
    Object? modelUrl = freezed,
    Object? isDemo = null,
  }) {
    return _then(_$UrnDetailDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      nameHan: freezed == nameHan
          ? _value.nameHan
          : nameHan // ignore: cast_nullable_to_non_nullable
              as String?,
      represents: freezed == represents
          ? _value.represents
          : represents // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      descriptionEn: freezed == descriptionEn
          ? _value.descriptionEn
          : descriptionEn // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UrnDetailDtoImpl implements _UrnDetailDto {
  const _$UrnDetailDtoImpl(
      {required this.id,
      required this.slug,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      @JsonKey(name: 'name_han') this.nameHan,
      this.represents,
      this.description,
      @JsonKey(name: 'description_en') this.descriptionEn,
      @JsonKey(name: 'display_order') this.displayOrder = 0,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      @JsonKey(name: 'model_url') this.modelUrl,
      @JsonKey(name: 'is_demo') this.isDemo = false});

  factory _$UrnDetailDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UrnDetailDtoImplFromJson(json);

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  @JsonKey(name: 'name_han')
  final String? nameHan;
  @override
  final String? represents;
  @override
  final String? description;
  @override
  @JsonKey(name: 'description_en')
  final String? descriptionEn;
  @override
  @JsonKey(name: 'display_order')
  final int displayOrder;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  @JsonKey(name: 'model_url')
  final String? modelUrl;
  @override
  @JsonKey(name: 'is_demo')
  final bool isDemo;

  @override
  String toString() {
    return 'UrnDetailDto(id: $id, slug: $slug, name: $name, nameEn: $nameEn, nameHan: $nameHan, represents: $represents, description: $description, descriptionEn: $descriptionEn, displayOrder: $displayOrder, thumbnailUrl: $thumbnailUrl, modelUrl: $modelUrl, isDemo: $isDemo)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UrnDetailDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.nameHan, nameHan) || other.nameHan == nameHan) &&
            (identical(other.represents, represents) ||
                other.represents == represents) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.descriptionEn, descriptionEn) ||
                other.descriptionEn == descriptionEn) &&
            (identical(other.displayOrder, displayOrder) ||
                other.displayOrder == displayOrder) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.modelUrl, modelUrl) ||
                other.modelUrl == modelUrl) &&
            (identical(other.isDemo, isDemo) || other.isDemo == isDemo));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      slug,
      name,
      nameEn,
      nameHan,
      represents,
      description,
      descriptionEn,
      displayOrder,
      thumbnailUrl,
      modelUrl,
      isDemo);

  /// Create a copy of UrnDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UrnDetailDtoImplCopyWith<_$UrnDetailDtoImpl> get copyWith =>
      __$$UrnDetailDtoImplCopyWithImpl<_$UrnDetailDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UrnDetailDtoImplToJson(
      this,
    );
  }
}

abstract class _UrnDetailDto implements UrnDetailDto {
  const factory _UrnDetailDto(
      {required final String id,
      required final String slug,
      required final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      @JsonKey(name: 'name_han') final String? nameHan,
      final String? represents,
      final String? description,
      @JsonKey(name: 'description_en') final String? descriptionEn,
      @JsonKey(name: 'display_order') final int displayOrder,
      @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
      @JsonKey(name: 'model_url') final String? modelUrl,
      @JsonKey(name: 'is_demo') final bool isDemo}) = _$UrnDetailDtoImpl;

  factory _UrnDetailDto.fromJson(Map<String, dynamic> json) =
      _$UrnDetailDtoImpl.fromJson;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  @JsonKey(name: 'name_han')
  String? get nameHan;
  @override
  String? get represents;
  @override
  String? get description;
  @override
  @JsonKey(name: 'description_en')
  String? get descriptionEn;
  @override
  @JsonKey(name: 'display_order')
  int get displayOrder;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  @JsonKey(name: 'model_url')
  String? get modelUrl;
  @override
  @JsonKey(name: 'is_demo')
  bool get isDemo;

  /// Create a copy of UrnDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UrnDetailDtoImplCopyWith<_$UrnDetailDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MotifDto _$MotifDtoFromJson(Map<String, dynamic> json) {
  return _MotifDto.fromJson(json);
}

/// @nodoc
mixin _$MotifDto {
  String get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'urn_id')
  String get urnId => throw _privateConstructorUsedError;
  @JsonKey(name: 'mesh_name')
  String get meshName => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  String get rarity => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_x')
  double get posX => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_y')
  double get posY => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_z')
  double get posZ => throw _privateConstructorUsedError;
  @JsonKey(name: 'bounding_radius')
  double get boundingRadius => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'image_url')
  String? get imageUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_demo')
  bool get isDemo => throw _privateConstructorUsedError;

  /// Serializes this MotifDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MotifDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MotifDtoCopyWith<MotifDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MotifDtoCopyWith<$Res> {
  factory $MotifDtoCopyWith(MotifDto value, $Res Function(MotifDto) then) =
      _$MotifDtoCopyWithImpl<$Res, MotifDto>;
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'urn_id') String urnId,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'pos_x') double posX,
      @JsonKey(name: 'pos_y') double posY,
      @JsonKey(name: 'pos_z') double posZ,
      @JsonKey(name: 'bounding_radius') double boundingRadius,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'image_url') String? imageUrl,
      @JsonKey(name: 'is_demo') bool isDemo});
}

/// @nodoc
class _$MotifDtoCopyWithImpl<$Res, $Val extends MotifDto>
    implements $MotifDtoCopyWith<$Res> {
  _$MotifDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MotifDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urnId = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urnId: null == urnId
          ? _value.urnId
          : urnId // ignore: cast_nullable_to_non_nullable
              as String,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MotifDtoImplCopyWith<$Res>
    implements $MotifDtoCopyWith<$Res> {
  factory _$$MotifDtoImplCopyWith(
          _$MotifDtoImpl value, $Res Function(_$MotifDtoImpl) then) =
      __$$MotifDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'urn_id') String urnId,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'pos_x') double posX,
      @JsonKey(name: 'pos_y') double posY,
      @JsonKey(name: 'pos_z') double posZ,
      @JsonKey(name: 'bounding_radius') double boundingRadius,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'image_url') String? imageUrl,
      @JsonKey(name: 'is_demo') bool isDemo});
}

/// @nodoc
class __$$MotifDtoImplCopyWithImpl<$Res>
    extends _$MotifDtoCopyWithImpl<$Res, _$MotifDtoImpl>
    implements _$$MotifDtoImplCopyWith<$Res> {
  __$$MotifDtoImplCopyWithImpl(
      _$MotifDtoImpl _value, $Res Function(_$MotifDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of MotifDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urnId = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
  }) {
    return _then(_$MotifDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urnId: null == urnId
          ? _value.urnId
          : urnId // ignore: cast_nullable_to_non_nullable
              as String,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MotifDtoImpl implements _MotifDto {
  const _$MotifDtoImpl(
      {required this.id,
      @JsonKey(name: 'urn_id') required this.urnId,
      @JsonKey(name: 'mesh_name') required this.meshName,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      required this.category,
      required this.rarity,
      @JsonKey(name: 'pos_x') this.posX = 0.0,
      @JsonKey(name: 'pos_y') this.posY = 0.0,
      @JsonKey(name: 'pos_z') this.posZ = 0.0,
      @JsonKey(name: 'bounding_radius') this.boundingRadius = 0.08,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      @JsonKey(name: 'image_url') this.imageUrl,
      @JsonKey(name: 'is_demo') this.isDemo = false});

  factory _$MotifDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$MotifDtoImplFromJson(json);

  @override
  final String id;
  @override
  @JsonKey(name: 'urn_id')
  final String urnId;
  @override
  @JsonKey(name: 'mesh_name')
  final String meshName;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  final String category;
  @override
  final String rarity;
  @override
  @JsonKey(name: 'pos_x')
  final double posX;
  @override
  @JsonKey(name: 'pos_y')
  final double posY;
  @override
  @JsonKey(name: 'pos_z')
  final double posZ;
  @override
  @JsonKey(name: 'bounding_radius')
  final double boundingRadius;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  @JsonKey(name: 'image_url')
  final String? imageUrl;
  @override
  @JsonKey(name: 'is_demo')
  final bool isDemo;

  @override
  String toString() {
    return 'MotifDto(id: $id, urnId: $urnId, meshName: $meshName, name: $name, nameEn: $nameEn, category: $category, rarity: $rarity, posX: $posX, posY: $posY, posZ: $posZ, boundingRadius: $boundingRadius, thumbnailUrl: $thumbnailUrl, imageUrl: $imageUrl, isDemo: $isDemo)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MotifDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.urnId, urnId) || other.urnId == urnId) &&
            (identical(other.meshName, meshName) ||
                other.meshName == meshName) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.rarity, rarity) || other.rarity == rarity) &&
            (identical(other.posX, posX) || other.posX == posX) &&
            (identical(other.posY, posY) || other.posY == posY) &&
            (identical(other.posZ, posZ) || other.posZ == posZ) &&
            (identical(other.boundingRadius, boundingRadius) ||
                other.boundingRadius == boundingRadius) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.isDemo, isDemo) || other.isDemo == isDemo));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      urnId,
      meshName,
      name,
      nameEn,
      category,
      rarity,
      posX,
      posY,
      posZ,
      boundingRadius,
      thumbnailUrl,
      imageUrl,
      isDemo);

  /// Create a copy of MotifDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MotifDtoImplCopyWith<_$MotifDtoImpl> get copyWith =>
      __$$MotifDtoImplCopyWithImpl<_$MotifDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MotifDtoImplToJson(
      this,
    );
  }
}

abstract class _MotifDto implements MotifDto {
  const factory _MotifDto(
      {required final String id,
      @JsonKey(name: 'urn_id') required final String urnId,
      @JsonKey(name: 'mesh_name') required final String meshName,
      required final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      required final String category,
      required final String rarity,
      @JsonKey(name: 'pos_x') final double posX,
      @JsonKey(name: 'pos_y') final double posY,
      @JsonKey(name: 'pos_z') final double posZ,
      @JsonKey(name: 'bounding_radius') final double boundingRadius,
      @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
      @JsonKey(name: 'image_url') final String? imageUrl,
      @JsonKey(name: 'is_demo') final bool isDemo}) = _$MotifDtoImpl;

  factory _MotifDto.fromJson(Map<String, dynamic> json) =
      _$MotifDtoImpl.fromJson;

  @override
  String get id;
  @override
  @JsonKey(name: 'urn_id')
  String get urnId;
  @override
  @JsonKey(name: 'mesh_name')
  String get meshName;
  @override
  String get name;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  String get category;
  @override
  String get rarity;
  @override
  @JsonKey(name: 'pos_x')
  double get posX;
  @override
  @JsonKey(name: 'pos_y')
  double get posY;
  @override
  @JsonKey(name: 'pos_z')
  double get posZ;
  @override
  @JsonKey(name: 'bounding_radius')
  double get boundingRadius;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  @JsonKey(name: 'image_url')
  String? get imageUrl;
  @override
  @JsonKey(name: 'is_demo')
  bool get isDemo;

  /// Create a copy of MotifDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MotifDtoImplCopyWith<_$MotifDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UrnInfoDto _$UrnInfoDtoFromJson(Map<String, dynamic> json) {
  return _UrnInfoDto.fromJson(json);
}

/// @nodoc
mixin _$UrnInfoDto {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'model_url')
  String? get modelUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_order')
  int get displayOrder => throw _privateConstructorUsedError;

  /// Serializes this UrnInfoDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UrnInfoDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UrnInfoDtoCopyWith<UrnInfoDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UrnInfoDtoCopyWith<$Res> {
  factory $UrnInfoDtoCopyWith(
          UrnInfoDto value, $Res Function(UrnInfoDto) then) =
      _$UrnInfoDtoCopyWithImpl<$Res, UrnInfoDto>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String? description,
      @JsonKey(name: 'display_order') int displayOrder});
}

/// @nodoc
class _$UrnInfoDtoCopyWithImpl<$Res, $Val extends UrnInfoDto>
    implements $UrnInfoDtoCopyWith<$Res> {
  _$UrnInfoDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UrnInfoDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? modelUrl = freezed,
    Object? thumbnailUrl = freezed,
    Object? description = freezed,
    Object? displayOrder = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UrnInfoDtoImplCopyWith<$Res>
    implements $UrnInfoDtoCopyWith<$Res> {
  factory _$$UrnInfoDtoImplCopyWith(
          _$UrnInfoDtoImpl value, $Res Function(_$UrnInfoDtoImpl) then) =
      __$$UrnInfoDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'model_url') String? modelUrl,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String? description,
      @JsonKey(name: 'display_order') int displayOrder});
}

/// @nodoc
class __$$UrnInfoDtoImplCopyWithImpl<$Res>
    extends _$UrnInfoDtoCopyWithImpl<$Res, _$UrnInfoDtoImpl>
    implements _$$UrnInfoDtoImplCopyWith<$Res> {
  __$$UrnInfoDtoImplCopyWithImpl(
      _$UrnInfoDtoImpl _value, $Res Function(_$UrnInfoDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UrnInfoDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? modelUrl = freezed,
    Object? thumbnailUrl = freezed,
    Object? description = freezed,
    Object? displayOrder = null,
  }) {
    return _then(_$UrnInfoDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      modelUrl: freezed == modelUrl
          ? _value.modelUrl
          : modelUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UrnInfoDtoImpl implements _UrnInfoDto {
  const _$UrnInfoDtoImpl(
      {required this.id,
      required this.slug,
      required this.name,
      @JsonKey(name: 'model_url') this.modelUrl,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      this.description,
      @JsonKey(name: 'display_order') this.displayOrder = 0});

  factory _$UrnInfoDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UrnInfoDtoImplFromJson(json);

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  @JsonKey(name: 'model_url')
  final String? modelUrl;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  final String? description;
  @override
  @JsonKey(name: 'display_order')
  final int displayOrder;

  @override
  String toString() {
    return 'UrnInfoDto(id: $id, slug: $slug, name: $name, modelUrl: $modelUrl, thumbnailUrl: $thumbnailUrl, description: $description, displayOrder: $displayOrder)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UrnInfoDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.modelUrl, modelUrl) ||
                other.modelUrl == modelUrl) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.displayOrder, displayOrder) ||
                other.displayOrder == displayOrder));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, slug, name, modelUrl,
      thumbnailUrl, description, displayOrder);

  /// Create a copy of UrnInfoDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UrnInfoDtoImplCopyWith<_$UrnInfoDtoImpl> get copyWith =>
      __$$UrnInfoDtoImplCopyWithImpl<_$UrnInfoDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UrnInfoDtoImplToJson(
      this,
    );
  }
}

abstract class _UrnInfoDto implements UrnInfoDto {
  const factory _UrnInfoDto(
          {required final String id,
          required final String slug,
          required final String name,
          @JsonKey(name: 'model_url') final String? modelUrl,
          @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
          final String? description,
          @JsonKey(name: 'display_order') final int displayOrder}) =
      _$UrnInfoDtoImpl;

  factory _UrnInfoDto.fromJson(Map<String, dynamic> json) =
      _$UrnInfoDtoImpl.fromJson;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  @JsonKey(name: 'model_url')
  String? get modelUrl;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  String? get description;
  @override
  @JsonKey(name: 'display_order')
  int get displayOrder;

  /// Create a copy of UrnInfoDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UrnInfoDtoImplCopyWith<_$UrnInfoDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MotifDetailDto _$MotifDetailDtoFromJson(Map<String, dynamic> json) {
  return _MotifDetailDto.fromJson(json);
}

/// @nodoc
mixin _$MotifDetailDto {
  String get id => throw _privateConstructorUsedError;
  UrnInfoDto get urn => throw _privateConstructorUsedError;
  @JsonKey(name: 'mesh_name')
  String get meshName => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  String get rarity => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_x')
  double get posX => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_y')
  double get posY => throw _privateConstructorUsedError;
  @JsonKey(name: 'pos_z')
  double get posZ => throw _privateConstructorUsedError;
  @JsonKey(name: 'bounding_radius')
  double get boundingRadius => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'image_url')
  String? get imageUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_demo')
  bool get isDemo => throw _privateConstructorUsedError;
  LessonContentDto? get lesson => throw _privateConstructorUsedError;
  UserProgressDto? get progress => throw _privateConstructorUsedError;

  /// Serializes this MotifDetailDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MotifDetailDtoCopyWith<MotifDetailDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MotifDetailDtoCopyWith<$Res> {
  factory $MotifDetailDtoCopyWith(
          MotifDetailDto value, $Res Function(MotifDetailDto) then) =
      _$MotifDetailDtoCopyWithImpl<$Res, MotifDetailDto>;
  @useResult
  $Res call(
      {String id,
      UrnInfoDto urn,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'pos_x') double posX,
      @JsonKey(name: 'pos_y') double posY,
      @JsonKey(name: 'pos_z') double posZ,
      @JsonKey(name: 'bounding_radius') double boundingRadius,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'image_url') String? imageUrl,
      @JsonKey(name: 'is_demo') bool isDemo,
      LessonContentDto? lesson,
      UserProgressDto? progress});

  $UrnInfoDtoCopyWith<$Res> get urn;
  $LessonContentDtoCopyWith<$Res>? get lesson;
  $UserProgressDtoCopyWith<$Res>? get progress;
}

/// @nodoc
class _$MotifDetailDtoCopyWithImpl<$Res, $Val extends MotifDetailDto>
    implements $MotifDetailDtoCopyWith<$Res> {
  _$MotifDetailDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urn = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
    Object? lesson = freezed,
    Object? progress = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urn: null == urn
          ? _value.urn
          : urn // ignore: cast_nullable_to_non_nullable
              as UrnInfoDto,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
      lesson: freezed == lesson
          ? _value.lesson
          : lesson // ignore: cast_nullable_to_non_nullable
              as LessonContentDto?,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto?,
    ) as $Val);
  }

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UrnInfoDtoCopyWith<$Res> get urn {
    return $UrnInfoDtoCopyWith<$Res>(_value.urn, (value) {
      return _then(_value.copyWith(urn: value) as $Val);
    });
  }

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $LessonContentDtoCopyWith<$Res>? get lesson {
    if (_value.lesson == null) {
      return null;
    }

    return $LessonContentDtoCopyWith<$Res>(_value.lesson!, (value) {
      return _then(_value.copyWith(lesson: value) as $Val);
    });
  }

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserProgressDtoCopyWith<$Res>? get progress {
    if (_value.progress == null) {
      return null;
    }

    return $UserProgressDtoCopyWith<$Res>(_value.progress!, (value) {
      return _then(_value.copyWith(progress: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MotifDetailDtoImplCopyWith<$Res>
    implements $MotifDetailDtoCopyWith<$Res> {
  factory _$$MotifDetailDtoImplCopyWith(_$MotifDetailDtoImpl value,
          $Res Function(_$MotifDetailDtoImpl) then) =
      __$$MotifDetailDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      UrnInfoDto urn,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'pos_x') double posX,
      @JsonKey(name: 'pos_y') double posY,
      @JsonKey(name: 'pos_z') double posZ,
      @JsonKey(name: 'bounding_radius') double boundingRadius,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      @JsonKey(name: 'image_url') String? imageUrl,
      @JsonKey(name: 'is_demo') bool isDemo,
      LessonContentDto? lesson,
      UserProgressDto? progress});

  @override
  $UrnInfoDtoCopyWith<$Res> get urn;
  @override
  $LessonContentDtoCopyWith<$Res>? get lesson;
  @override
  $UserProgressDtoCopyWith<$Res>? get progress;
}

/// @nodoc
class __$$MotifDetailDtoImplCopyWithImpl<$Res>
    extends _$MotifDetailDtoCopyWithImpl<$Res, _$MotifDetailDtoImpl>
    implements _$$MotifDetailDtoImplCopyWith<$Res> {
  __$$MotifDetailDtoImplCopyWithImpl(
      _$MotifDetailDtoImpl _value, $Res Function(_$MotifDetailDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? urn = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? posX = null,
    Object? posY = null,
    Object? posZ = null,
    Object? boundingRadius = null,
    Object? thumbnailUrl = freezed,
    Object? imageUrl = freezed,
    Object? isDemo = null,
    Object? lesson = freezed,
    Object? progress = freezed,
  }) {
    return _then(_$MotifDetailDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      urn: null == urn
          ? _value.urn
          : urn // ignore: cast_nullable_to_non_nullable
              as UrnInfoDto,
      meshName: null == meshName
          ? _value.meshName
          : meshName // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      rarity: null == rarity
          ? _value.rarity
          : rarity // ignore: cast_nullable_to_non_nullable
              as String,
      posX: null == posX
          ? _value.posX
          : posX // ignore: cast_nullable_to_non_nullable
              as double,
      posY: null == posY
          ? _value.posY
          : posY // ignore: cast_nullable_to_non_nullable
              as double,
      posZ: null == posZ
          ? _value.posZ
          : posZ // ignore: cast_nullable_to_non_nullable
              as double,
      boundingRadius: null == boundingRadius
          ? _value.boundingRadius
          : boundingRadius // ignore: cast_nullable_to_non_nullable
              as double,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isDemo: null == isDemo
          ? _value.isDemo
          : isDemo // ignore: cast_nullable_to_non_nullable
              as bool,
      lesson: freezed == lesson
          ? _value.lesson
          : lesson // ignore: cast_nullable_to_non_nullable
              as LessonContentDto?,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MotifDetailDtoImpl implements _MotifDetailDto {
  const _$MotifDetailDtoImpl(
      {required this.id,
      required this.urn,
      @JsonKey(name: 'mesh_name') required this.meshName,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      required this.category,
      required this.rarity,
      @JsonKey(name: 'pos_x') this.posX = 0.0,
      @JsonKey(name: 'pos_y') this.posY = 0.0,
      @JsonKey(name: 'pos_z') this.posZ = 0.0,
      @JsonKey(name: 'bounding_radius') this.boundingRadius = 0.08,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      @JsonKey(name: 'image_url') this.imageUrl,
      @JsonKey(name: 'is_demo') this.isDemo = false,
      this.lesson,
      this.progress});

  factory _$MotifDetailDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$MotifDetailDtoImplFromJson(json);

  @override
  final String id;
  @override
  final UrnInfoDto urn;
  @override
  @JsonKey(name: 'mesh_name')
  final String meshName;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  final String category;
  @override
  final String rarity;
  @override
  @JsonKey(name: 'pos_x')
  final double posX;
  @override
  @JsonKey(name: 'pos_y')
  final double posY;
  @override
  @JsonKey(name: 'pos_z')
  final double posZ;
  @override
  @JsonKey(name: 'bounding_radius')
  final double boundingRadius;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  @JsonKey(name: 'image_url')
  final String? imageUrl;
  @override
  @JsonKey(name: 'is_demo')
  final bool isDemo;
  @override
  final LessonContentDto? lesson;
  @override
  final UserProgressDto? progress;

  @override
  String toString() {
    return 'MotifDetailDto(id: $id, urn: $urn, meshName: $meshName, name: $name, nameEn: $nameEn, category: $category, rarity: $rarity, posX: $posX, posY: $posY, posZ: $posZ, boundingRadius: $boundingRadius, thumbnailUrl: $thumbnailUrl, imageUrl: $imageUrl, isDemo: $isDemo, lesson: $lesson, progress: $progress)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MotifDetailDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.urn, urn) || other.urn == urn) &&
            (identical(other.meshName, meshName) ||
                other.meshName == meshName) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.rarity, rarity) || other.rarity == rarity) &&
            (identical(other.posX, posX) || other.posX == posX) &&
            (identical(other.posY, posY) || other.posY == posY) &&
            (identical(other.posZ, posZ) || other.posZ == posZ) &&
            (identical(other.boundingRadius, boundingRadius) ||
                other.boundingRadius == boundingRadius) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.isDemo, isDemo) || other.isDemo == isDemo) &&
            (identical(other.lesson, lesson) || other.lesson == lesson) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      urn,
      meshName,
      name,
      nameEn,
      category,
      rarity,
      posX,
      posY,
      posZ,
      boundingRadius,
      thumbnailUrl,
      imageUrl,
      isDemo,
      lesson,
      progress);

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MotifDetailDtoImplCopyWith<_$MotifDetailDtoImpl> get copyWith =>
      __$$MotifDetailDtoImplCopyWithImpl<_$MotifDetailDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MotifDetailDtoImplToJson(
      this,
    );
  }
}

abstract class _MotifDetailDto implements MotifDetailDto {
  const factory _MotifDetailDto(
      {required final String id,
      required final UrnInfoDto urn,
      @JsonKey(name: 'mesh_name') required final String meshName,
      required final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      required final String category,
      required final String rarity,
      @JsonKey(name: 'pos_x') final double posX,
      @JsonKey(name: 'pos_y') final double posY,
      @JsonKey(name: 'pos_z') final double posZ,
      @JsonKey(name: 'bounding_radius') final double boundingRadius,
      @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
      @JsonKey(name: 'image_url') final String? imageUrl,
      @JsonKey(name: 'is_demo') final bool isDemo,
      final LessonContentDto? lesson,
      final UserProgressDto? progress}) = _$MotifDetailDtoImpl;

  factory _MotifDetailDto.fromJson(Map<String, dynamic> json) =
      _$MotifDetailDtoImpl.fromJson;

  @override
  String get id;
  @override
  UrnInfoDto get urn;
  @override
  @JsonKey(name: 'mesh_name')
  String get meshName;
  @override
  String get name;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  String get category;
  @override
  String get rarity;
  @override
  @JsonKey(name: 'pos_x')
  double get posX;
  @override
  @JsonKey(name: 'pos_y')
  double get posY;
  @override
  @JsonKey(name: 'pos_z')
  double get posZ;
  @override
  @JsonKey(name: 'bounding_radius')
  double get boundingRadius;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  @JsonKey(name: 'image_url')
  String? get imageUrl;
  @override
  @JsonKey(name: 'is_demo')
  bool get isDemo;
  @override
  LessonContentDto? get lesson;
  @override
  UserProgressDto? get progress;

  /// Create a copy of MotifDetailDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MotifDetailDtoImplCopyWith<_$MotifDetailDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

LessonContentDto _$LessonContentDtoFromJson(Map<String, dynamic> json) {
  return _LessonContentDto.fromJson(json);
}

/// @nodoc
mixin _$LessonContentDto {
  String? get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_id')
  String? get motifId => throw _privateConstructorUsedError;
  @JsonKey(name: 'intro_text')
  String? get introText => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  @JsonKey(name: 'historical_context')
  String? get historicalContext => throw _privateConstructorUsedError;
  String? get symbolism => throw _privateConstructorUsedError;
  @JsonKey(name: 'fun_fact')
  String? get funFact => throw _privateConstructorUsedError;
  @JsonKey(name: 'audio_url')
  String? get audioUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'video_url')
  String? get videoUrl => throw _privateConstructorUsedError;
  List<String> get images => throw _privateConstructorUsedError;

  /// Serializes this LessonContentDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of LessonContentDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LessonContentDtoCopyWith<LessonContentDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LessonContentDtoCopyWith<$Res> {
  factory $LessonContentDtoCopyWith(
          LessonContentDto value, $Res Function(LessonContentDto) then) =
      _$LessonContentDtoCopyWithImpl<$Res, LessonContentDto>;
  @useResult
  $Res call(
      {String? id,
      @JsonKey(name: 'motif_id') String? motifId,
      @JsonKey(name: 'intro_text') String? introText,
      String? description,
      @JsonKey(name: 'historical_context') String? historicalContext,
      String? symbolism,
      @JsonKey(name: 'fun_fact') String? funFact,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'video_url') String? videoUrl,
      List<String> images});
}

/// @nodoc
class _$LessonContentDtoCopyWithImpl<$Res, $Val extends LessonContentDto>
    implements $LessonContentDtoCopyWith<$Res> {
  _$LessonContentDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LessonContentDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = freezed,
    Object? motifId = freezed,
    Object? introText = freezed,
    Object? description = freezed,
    Object? historicalContext = freezed,
    Object? symbolism = freezed,
    Object? funFact = freezed,
    Object? audioUrl = freezed,
    Object? videoUrl = freezed,
    Object? images = null,
  }) {
    return _then(_value.copyWith(
      id: freezed == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String?,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      introText: freezed == introText
          ? _value.introText
          : introText // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      historicalContext: freezed == historicalContext
          ? _value.historicalContext
          : historicalContext // ignore: cast_nullable_to_non_nullable
              as String?,
      symbolism: freezed == symbolism
          ? _value.symbolism
          : symbolism // ignore: cast_nullable_to_non_nullable
              as String?,
      funFact: freezed == funFact
          ? _value.funFact
          : funFact // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _value.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      videoUrl: freezed == videoUrl
          ? _value.videoUrl
          : videoUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value.images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$LessonContentDtoImplCopyWith<$Res>
    implements $LessonContentDtoCopyWith<$Res> {
  factory _$$LessonContentDtoImplCopyWith(_$LessonContentDtoImpl value,
          $Res Function(_$LessonContentDtoImpl) then) =
      __$$LessonContentDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? id,
      @JsonKey(name: 'motif_id') String? motifId,
      @JsonKey(name: 'intro_text') String? introText,
      String? description,
      @JsonKey(name: 'historical_context') String? historicalContext,
      String? symbolism,
      @JsonKey(name: 'fun_fact') String? funFact,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'video_url') String? videoUrl,
      List<String> images});
}

/// @nodoc
class __$$LessonContentDtoImplCopyWithImpl<$Res>
    extends _$LessonContentDtoCopyWithImpl<$Res, _$LessonContentDtoImpl>
    implements _$$LessonContentDtoImplCopyWith<$Res> {
  __$$LessonContentDtoImplCopyWithImpl(_$LessonContentDtoImpl _value,
      $Res Function(_$LessonContentDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of LessonContentDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = freezed,
    Object? motifId = freezed,
    Object? introText = freezed,
    Object? description = freezed,
    Object? historicalContext = freezed,
    Object? symbolism = freezed,
    Object? funFact = freezed,
    Object? audioUrl = freezed,
    Object? videoUrl = freezed,
    Object? images = null,
  }) {
    return _then(_$LessonContentDtoImpl(
      id: freezed == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String?,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      introText: freezed == introText
          ? _value.introText
          : introText // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      historicalContext: freezed == historicalContext
          ? _value.historicalContext
          : historicalContext // ignore: cast_nullable_to_non_nullable
              as String?,
      symbolism: freezed == symbolism
          ? _value.symbolism
          : symbolism // ignore: cast_nullable_to_non_nullable
              as String?,
      funFact: freezed == funFact
          ? _value.funFact
          : funFact // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _value.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      videoUrl: freezed == videoUrl
          ? _value.videoUrl
          : videoUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value._images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$LessonContentDtoImpl implements _LessonContentDto {
  const _$LessonContentDtoImpl(
      {this.id,
      @JsonKey(name: 'motif_id') this.motifId,
      @JsonKey(name: 'intro_text') this.introText,
      this.description,
      @JsonKey(name: 'historical_context') this.historicalContext,
      this.symbolism,
      @JsonKey(name: 'fun_fact') this.funFact,
      @JsonKey(name: 'audio_url') this.audioUrl,
      @JsonKey(name: 'video_url') this.videoUrl,
      final List<String> images = const []})
      : _images = images;

  factory _$LessonContentDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$LessonContentDtoImplFromJson(json);

  @override
  final String? id;
  @override
  @JsonKey(name: 'motif_id')
  final String? motifId;
  @override
  @JsonKey(name: 'intro_text')
  final String? introText;
  @override
  final String? description;
  @override
  @JsonKey(name: 'historical_context')
  final String? historicalContext;
  @override
  final String? symbolism;
  @override
  @JsonKey(name: 'fun_fact')
  final String? funFact;
  @override
  @JsonKey(name: 'audio_url')
  final String? audioUrl;
  @override
  @JsonKey(name: 'video_url')
  final String? videoUrl;
  final List<String> _images;
  @override
  @JsonKey()
  List<String> get images {
    if (_images is EqualUnmodifiableListView) return _images;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_images);
  }

  @override
  String toString() {
    return 'LessonContentDto(id: $id, motifId: $motifId, introText: $introText, description: $description, historicalContext: $historicalContext, symbolism: $symbolism, funFact: $funFact, audioUrl: $audioUrl, videoUrl: $videoUrl, images: $images)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LessonContentDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.introText, introText) ||
                other.introText == introText) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.historicalContext, historicalContext) ||
                other.historicalContext == historicalContext) &&
            (identical(other.symbolism, symbolism) ||
                other.symbolism == symbolism) &&
            (identical(other.funFact, funFact) || other.funFact == funFact) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.videoUrl, videoUrl) ||
                other.videoUrl == videoUrl) &&
            const DeepCollectionEquality().equals(other._images, _images));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      motifId,
      introText,
      description,
      historicalContext,
      symbolism,
      funFact,
      audioUrl,
      videoUrl,
      const DeepCollectionEquality().hash(_images));

  /// Create a copy of LessonContentDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LessonContentDtoImplCopyWith<_$LessonContentDtoImpl> get copyWith =>
      __$$LessonContentDtoImplCopyWithImpl<_$LessonContentDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LessonContentDtoImplToJson(
      this,
    );
  }
}

abstract class _LessonContentDto implements LessonContentDto {
  const factory _LessonContentDto(
      {final String? id,
      @JsonKey(name: 'motif_id') final String? motifId,
      @JsonKey(name: 'intro_text') final String? introText,
      final String? description,
      @JsonKey(name: 'historical_context') final String? historicalContext,
      final String? symbolism,
      @JsonKey(name: 'fun_fact') final String? funFact,
      @JsonKey(name: 'audio_url') final String? audioUrl,
      @JsonKey(name: 'video_url') final String? videoUrl,
      final List<String> images}) = _$LessonContentDtoImpl;

  factory _LessonContentDto.fromJson(Map<String, dynamic> json) =
      _$LessonContentDtoImpl.fromJson;

  @override
  String? get id;
  @override
  @JsonKey(name: 'motif_id')
  String? get motifId;
  @override
  @JsonKey(name: 'intro_text')
  String? get introText;
  @override
  String? get description;
  @override
  @JsonKey(name: 'historical_context')
  String? get historicalContext;
  @override
  String? get symbolism;
  @override
  @JsonKey(name: 'fun_fact')
  String? get funFact;
  @override
  @JsonKey(name: 'audio_url')
  String? get audioUrl;
  @override
  @JsonKey(name: 'video_url')
  String? get videoUrl;
  @override
  List<String> get images;

  /// Create a copy of LessonContentDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LessonContentDtoImplCopyWith<_$LessonContentDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UserProgressDto _$UserProgressDtoFromJson(Map<String, dynamic> json) {
  return _UserProgressDto.fromJson(json);
}

/// @nodoc
mixin _$UserProgressDto {
  String get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'user_id')
  String get userId => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_id')
  String get motifId => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  @JsonKey(name: 'discovered_at')
  String? get discoveredAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'learned_at')
  String? get learnedAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'mastered_at')
  String? get masteredAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_earned')
  int get xpEarned => throw _privateConstructorUsedError;
  @JsonKey(name: 'quiz_best_score')
  int? get quizBestScore => throw _privateConstructorUsedError;

  /// Serializes this UserProgressDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UserProgressDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UserProgressDtoCopyWith<UserProgressDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UserProgressDtoCopyWith<$Res> {
  factory $UserProgressDtoCopyWith(
          UserProgressDto value, $Res Function(UserProgressDto) then) =
      _$UserProgressDtoCopyWithImpl<$Res, UserProgressDto>;
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'motif_id') String motifId,
      String status,
      @JsonKey(name: 'discovered_at') String? discoveredAt,
      @JsonKey(name: 'learned_at') String? learnedAt,
      @JsonKey(name: 'mastered_at') String? masteredAt,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'quiz_best_score') int? quizBestScore});
}

/// @nodoc
class _$UserProgressDtoCopyWithImpl<$Res, $Val extends UserProgressDto>
    implements $UserProgressDtoCopyWith<$Res> {
  _$UserProgressDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UserProgressDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? userId = null,
    Object? motifId = null,
    Object? status = null,
    Object? discoveredAt = freezed,
    Object? learnedAt = freezed,
    Object? masteredAt = freezed,
    Object? xpEarned = null,
    Object? quizBestScore = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      discoveredAt: freezed == discoveredAt
          ? _value.discoveredAt
          : discoveredAt // ignore: cast_nullable_to_non_nullable
              as String?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as String?,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as String?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizBestScore: freezed == quizBestScore
          ? _value.quizBestScore
          : quizBestScore // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UserProgressDtoImplCopyWith<$Res>
    implements $UserProgressDtoCopyWith<$Res> {
  factory _$$UserProgressDtoImplCopyWith(_$UserProgressDtoImpl value,
          $Res Function(_$UserProgressDtoImpl) then) =
      __$$UserProgressDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'motif_id') String motifId,
      String status,
      @JsonKey(name: 'discovered_at') String? discoveredAt,
      @JsonKey(name: 'learned_at') String? learnedAt,
      @JsonKey(name: 'mastered_at') String? masteredAt,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'quiz_best_score') int? quizBestScore});
}

/// @nodoc
class __$$UserProgressDtoImplCopyWithImpl<$Res>
    extends _$UserProgressDtoCopyWithImpl<$Res, _$UserProgressDtoImpl>
    implements _$$UserProgressDtoImplCopyWith<$Res> {
  __$$UserProgressDtoImplCopyWithImpl(
      _$UserProgressDtoImpl _value, $Res Function(_$UserProgressDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UserProgressDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? userId = null,
    Object? motifId = null,
    Object? status = null,
    Object? discoveredAt = freezed,
    Object? learnedAt = freezed,
    Object? masteredAt = freezed,
    Object? xpEarned = null,
    Object? quizBestScore = freezed,
  }) {
    return _then(_$UserProgressDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      discoveredAt: freezed == discoveredAt
          ? _value.discoveredAt
          : discoveredAt // ignore: cast_nullable_to_non_nullable
              as String?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as String?,
      masteredAt: freezed == masteredAt
          ? _value.masteredAt
          : masteredAt // ignore: cast_nullable_to_non_nullable
              as String?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizBestScore: freezed == quizBestScore
          ? _value.quizBestScore
          : quizBestScore // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UserProgressDtoImpl implements _UserProgressDto {
  const _$UserProgressDtoImpl(
      {required this.id,
      @JsonKey(name: 'user_id') required this.userId,
      @JsonKey(name: 'motif_id') required this.motifId,
      required this.status,
      @JsonKey(name: 'discovered_at') this.discoveredAt,
      @JsonKey(name: 'learned_at') this.learnedAt,
      @JsonKey(name: 'mastered_at') this.masteredAt,
      @JsonKey(name: 'xp_earned') this.xpEarned = 0,
      @JsonKey(name: 'quiz_best_score') this.quizBestScore});

  factory _$UserProgressDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UserProgressDtoImplFromJson(json);

  @override
  final String id;
  @override
  @JsonKey(name: 'user_id')
  final String userId;
  @override
  @JsonKey(name: 'motif_id')
  final String motifId;
  @override
  final String status;
  @override
  @JsonKey(name: 'discovered_at')
  final String? discoveredAt;
  @override
  @JsonKey(name: 'learned_at')
  final String? learnedAt;
  @override
  @JsonKey(name: 'mastered_at')
  final String? masteredAt;
  @override
  @JsonKey(name: 'xp_earned')
  final int xpEarned;
  @override
  @JsonKey(name: 'quiz_best_score')
  final int? quizBestScore;

  @override
  String toString() {
    return 'UserProgressDto(id: $id, userId: $userId, motifId: $motifId, status: $status, discoveredAt: $discoveredAt, learnedAt: $learnedAt, masteredAt: $masteredAt, xpEarned: $xpEarned, quizBestScore: $quizBestScore)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UserProgressDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.discoveredAt, discoveredAt) ||
                other.discoveredAt == discoveredAt) &&
            (identical(other.learnedAt, learnedAt) ||
                other.learnedAt == learnedAt) &&
            (identical(other.masteredAt, masteredAt) ||
                other.masteredAt == masteredAt) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.quizBestScore, quizBestScore) ||
                other.quizBestScore == quizBestScore));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, userId, motifId, status,
      discoveredAt, learnedAt, masteredAt, xpEarned, quizBestScore);

  /// Create a copy of UserProgressDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UserProgressDtoImplCopyWith<_$UserProgressDtoImpl> get copyWith =>
      __$$UserProgressDtoImplCopyWithImpl<_$UserProgressDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UserProgressDtoImplToJson(
      this,
    );
  }
}

abstract class _UserProgressDto implements UserProgressDto {
  const factory _UserProgressDto(
          {required final String id,
          @JsonKey(name: 'user_id') required final String userId,
          @JsonKey(name: 'motif_id') required final String motifId,
          required final String status,
          @JsonKey(name: 'discovered_at') final String? discoveredAt,
          @JsonKey(name: 'learned_at') final String? learnedAt,
          @JsonKey(name: 'mastered_at') final String? masteredAt,
          @JsonKey(name: 'xp_earned') final int xpEarned,
          @JsonKey(name: 'quiz_best_score') final int? quizBestScore}) =
      _$UserProgressDtoImpl;

  factory _UserProgressDto.fromJson(Map<String, dynamic> json) =
      _$UserProgressDtoImpl.fromJson;

  @override
  String get id;
  @override
  @JsonKey(name: 'user_id')
  String get userId;
  @override
  @JsonKey(name: 'motif_id')
  String get motifId;
  @override
  String get status;
  @override
  @JsonKey(name: 'discovered_at')
  String? get discoveredAt;
  @override
  @JsonKey(name: 'learned_at')
  String? get learnedAt;
  @override
  @JsonKey(name: 'mastered_at')
  String? get masteredAt;
  @override
  @JsonKey(name: 'xp_earned')
  int get xpEarned;
  @override
  @JsonKey(name: 'quiz_best_score')
  int? get quizBestScore;

  /// Create a copy of UserProgressDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UserProgressDtoImplCopyWith<_$UserProgressDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UnlockResponseDto _$UnlockResponseDtoFromJson(Map<String, dynamic> json) {
  return _UnlockResponseDto.fromJson(json);
}

/// @nodoc
mixin _$UnlockResponseDto {
  UserProgressDto get progress => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_earned')
  int get xpEarned => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_xp')
  int get totalXp => throw _privateConstructorUsedError;
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges => throw _privateConstructorUsedError;
  @JsonKey(name: 'streak_updated')
  bool get streakUpdated => throw _privateConstructorUsedError;
  @JsonKey(name: 'current_streak')
  int get currentStreak => throw _privateConstructorUsedError;

  /// Serializes this UnlockResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UnlockResponseDtoCopyWith<UnlockResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UnlockResponseDtoCopyWith<$Res> {
  factory $UnlockResponseDtoCopyWith(
          UnlockResponseDto value, $Res Function(UnlockResponseDto) then) =
      _$UnlockResponseDtoCopyWithImpl<$Res, UnlockResponseDto>;
  @useResult
  $Res call(
      {UserProgressDto progress,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'new_badges') List<BadgeDto> newBadges,
      @JsonKey(name: 'streak_updated') bool streakUpdated,
      @JsonKey(name: 'current_streak') int currentStreak});

  $UserProgressDtoCopyWith<$Res> get progress;
}

/// @nodoc
class _$UnlockResponseDtoCopyWithImpl<$Res, $Val extends UnlockResponseDto>
    implements $UnlockResponseDtoCopyWith<$Res> {
  _$UnlockResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? progress = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
    Object? streakUpdated = null,
    Object? currentStreak = null,
  }) {
    return _then(_value.copyWith(
      progress: null == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value.newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<BadgeDto>,
      streakUpdated: null == streakUpdated
          ? _value.streakUpdated
          : streakUpdated // ignore: cast_nullable_to_non_nullable
              as bool,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserProgressDtoCopyWith<$Res> get progress {
    return $UserProgressDtoCopyWith<$Res>(_value.progress, (value) {
      return _then(_value.copyWith(progress: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$UnlockResponseDtoImplCopyWith<$Res>
    implements $UnlockResponseDtoCopyWith<$Res> {
  factory _$$UnlockResponseDtoImplCopyWith(_$UnlockResponseDtoImpl value,
          $Res Function(_$UnlockResponseDtoImpl) then) =
      __$$UnlockResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {UserProgressDto progress,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'new_badges') List<BadgeDto> newBadges,
      @JsonKey(name: 'streak_updated') bool streakUpdated,
      @JsonKey(name: 'current_streak') int currentStreak});

  @override
  $UserProgressDtoCopyWith<$Res> get progress;
}

/// @nodoc
class __$$UnlockResponseDtoImplCopyWithImpl<$Res>
    extends _$UnlockResponseDtoCopyWithImpl<$Res, _$UnlockResponseDtoImpl>
    implements _$$UnlockResponseDtoImplCopyWith<$Res> {
  __$$UnlockResponseDtoImplCopyWithImpl(_$UnlockResponseDtoImpl _value,
      $Res Function(_$UnlockResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? progress = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
    Object? streakUpdated = null,
    Object? currentStreak = null,
  }) {
    return _then(_$UnlockResponseDtoImpl(
      progress: null == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value._newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<BadgeDto>,
      streakUpdated: null == streakUpdated
          ? _value.streakUpdated
          : streakUpdated // ignore: cast_nullable_to_non_nullable
              as bool,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UnlockResponseDtoImpl implements _UnlockResponseDto {
  const _$UnlockResponseDtoImpl(
      {required this.progress,
      @JsonKey(name: 'xp_earned') this.xpEarned = 0,
      @JsonKey(name: 'total_xp') this.totalXp = 0,
      @JsonKey(name: 'new_badges') final List<BadgeDto> newBadges = const [],
      @JsonKey(name: 'streak_updated') this.streakUpdated = false,
      @JsonKey(name: 'current_streak') this.currentStreak = 0})
      : _newBadges = newBadges;

  factory _$UnlockResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UnlockResponseDtoImplFromJson(json);

  @override
  final UserProgressDto progress;
  @override
  @JsonKey(name: 'xp_earned')
  final int xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  final List<BadgeDto> _newBadges;
  @override
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges {
    if (_newBadges is EqualUnmodifiableListView) return _newBadges;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_newBadges);
  }

  @override
  @JsonKey(name: 'streak_updated')
  final bool streakUpdated;
  @override
  @JsonKey(name: 'current_streak')
  final int currentStreak;

  @override
  String toString() {
    return 'UnlockResponseDto(progress: $progress, xpEarned: $xpEarned, totalXp: $totalXp, newBadges: $newBadges, streakUpdated: $streakUpdated, currentStreak: $currentStreak)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UnlockResponseDtoImpl &&
            (identical(other.progress, progress) ||
                other.progress == progress) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            const DeepCollectionEquality()
                .equals(other._newBadges, _newBadges) &&
            (identical(other.streakUpdated, streakUpdated) ||
                other.streakUpdated == streakUpdated) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      progress,
      xpEarned,
      totalXp,
      const DeepCollectionEquality().hash(_newBadges),
      streakUpdated,
      currentStreak);

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UnlockResponseDtoImplCopyWith<_$UnlockResponseDtoImpl> get copyWith =>
      __$$UnlockResponseDtoImplCopyWithImpl<_$UnlockResponseDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UnlockResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _UnlockResponseDto implements UnlockResponseDto {
  const factory _UnlockResponseDto(
          {required final UserProgressDto progress,
          @JsonKey(name: 'xp_earned') final int xpEarned,
          @JsonKey(name: 'total_xp') final int totalXp,
          @JsonKey(name: 'new_badges') final List<BadgeDto> newBadges,
          @JsonKey(name: 'streak_updated') final bool streakUpdated,
          @JsonKey(name: 'current_streak') final int currentStreak}) =
      _$UnlockResponseDtoImpl;

  factory _UnlockResponseDto.fromJson(Map<String, dynamic> json) =
      _$UnlockResponseDtoImpl.fromJson;

  @override
  UserProgressDto get progress;
  @override
  @JsonKey(name: 'xp_earned')
  int get xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @override
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges;
  @override
  @JsonKey(name: 'streak_updated')
  bool get streakUpdated;
  @override
  @JsonKey(name: 'current_streak')
  int get currentStreak;

  /// Create a copy of UnlockResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UnlockResponseDtoImplCopyWith<_$UnlockResponseDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

BadgeDto _$BadgeDtoFromJson(Map<String, dynamic> json) {
  return _BadgeDto.fromJson(json);
}

/// @nodoc
mixin _$BadgeDto {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  @JsonKey(name: 'icon_url')
  String? get iconUrl => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_bonus')
  int get xpBonus => throw _privateConstructorUsedError;

  /// Serializes this BadgeDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $BadgeDtoCopyWith<BadgeDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $BadgeDtoCopyWith<$Res> {
  factory $BadgeDtoCopyWith(BadgeDto value, $Res Function(BadgeDto) then) =
      _$BadgeDtoCopyWithImpl<$Res, BadgeDto>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String? description,
      @JsonKey(name: 'icon_url') String? iconUrl,
      String category,
      @JsonKey(name: 'xp_bonus') int xpBonus});
}

/// @nodoc
class _$BadgeDtoCopyWithImpl<$Res, $Val extends BadgeDto>
    implements $BadgeDtoCopyWith<$Res> {
  _$BadgeDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? description = freezed,
    Object? iconUrl = freezed,
    Object? category = null,
    Object? xpBonus = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      iconUrl: freezed == iconUrl
          ? _value.iconUrl
          : iconUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      xpBonus: null == xpBonus
          ? _value.xpBonus
          : xpBonus // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$BadgeDtoImplCopyWith<$Res>
    implements $BadgeDtoCopyWith<$Res> {
  factory _$$BadgeDtoImplCopyWith(
          _$BadgeDtoImpl value, $Res Function(_$BadgeDtoImpl) then) =
      __$$BadgeDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String? description,
      @JsonKey(name: 'icon_url') String? iconUrl,
      String category,
      @JsonKey(name: 'xp_bonus') int xpBonus});
}

/// @nodoc
class __$$BadgeDtoImplCopyWithImpl<$Res>
    extends _$BadgeDtoCopyWithImpl<$Res, _$BadgeDtoImpl>
    implements _$$BadgeDtoImplCopyWith<$Res> {
  __$$BadgeDtoImplCopyWithImpl(
      _$BadgeDtoImpl _value, $Res Function(_$BadgeDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? slug = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? description = freezed,
    Object? iconUrl = freezed,
    Object? category = null,
    Object? xpBonus = null,
  }) {
    return _then(_$BadgeDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      slug: null == slug
          ? _value.slug
          : slug // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameEn: freezed == nameEn
          ? _value.nameEn
          : nameEn // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      iconUrl: freezed == iconUrl
          ? _value.iconUrl
          : iconUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      xpBonus: null == xpBonus
          ? _value.xpBonus
          : xpBonus // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BadgeDtoImpl implements _BadgeDto {
  const _$BadgeDtoImpl(
      {required this.id,
      required this.slug,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      this.description,
      @JsonKey(name: 'icon_url') this.iconUrl,
      required this.category,
      @JsonKey(name: 'xp_bonus') this.xpBonus = 0});

  factory _$BadgeDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$BadgeDtoImplFromJson(json);

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  final String? description;
  @override
  @JsonKey(name: 'icon_url')
  final String? iconUrl;
  @override
  final String category;
  @override
  @JsonKey(name: 'xp_bonus')
  final int xpBonus;

  @override
  String toString() {
    return 'BadgeDto(id: $id, slug: $slug, name: $name, nameEn: $nameEn, description: $description, iconUrl: $iconUrl, category: $category, xpBonus: $xpBonus)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$BadgeDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.iconUrl, iconUrl) || other.iconUrl == iconUrl) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.xpBonus, xpBonus) || other.xpBonus == xpBonus));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, slug, name, nameEn,
      description, iconUrl, category, xpBonus);

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$BadgeDtoImplCopyWith<_$BadgeDtoImpl> get copyWith =>
      __$$BadgeDtoImplCopyWithImpl<_$BadgeDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$BadgeDtoImplToJson(
      this,
    );
  }
}

abstract class _BadgeDto implements BadgeDto {
  const factory _BadgeDto(
      {required final String id,
      required final String slug,
      required final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      final String? description,
      @JsonKey(name: 'icon_url') final String? iconUrl,
      required final String category,
      @JsonKey(name: 'xp_bonus') final int xpBonus}) = _$BadgeDtoImpl;

  factory _BadgeDto.fromJson(Map<String, dynamic> json) =
      _$BadgeDtoImpl.fromJson;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  String? get description;
  @override
  @JsonKey(name: 'icon_url')
  String? get iconUrl;
  @override
  String get category;
  @override
  @JsonKey(name: 'xp_bonus')
  int get xpBonus;

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$BadgeDtoImplCopyWith<_$BadgeDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CompleteLessonResponseDto _$CompleteLessonResponseDtoFromJson(
    Map<String, dynamic> json) {
  return _CompleteLessonResponseDto.fromJson(json);
}

/// @nodoc
mixin _$CompleteLessonResponseDto {
  @JsonKey(name: 'user_id')
  String get userId => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_id')
  String get motifId => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  @JsonKey(name: 'lesson_viewed_at')
  DateTime? get lessonViewedAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'learned_at')
  DateTime? get learnedAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_awarded')
  int get xpEarned => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_xp')
  int get totalXp => throw _privateConstructorUsedError;

  /// Serializes this CompleteLessonResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CompleteLessonResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CompleteLessonResponseDtoCopyWith<CompleteLessonResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CompleteLessonResponseDtoCopyWith<$Res> {
  factory $CompleteLessonResponseDtoCopyWith(CompleteLessonResponseDto value,
          $Res Function(CompleteLessonResponseDto) then) =
      _$CompleteLessonResponseDtoCopyWithImpl<$Res, CompleteLessonResponseDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'motif_id') String motifId,
      String status,
      @JsonKey(name: 'lesson_viewed_at') DateTime? lessonViewedAt,
      @JsonKey(name: 'learned_at') DateTime? learnedAt,
      @JsonKey(name: 'xp_awarded') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp});
}

/// @nodoc
class _$CompleteLessonResponseDtoCopyWithImpl<$Res,
        $Val extends CompleteLessonResponseDto>
    implements $CompleteLessonResponseDtoCopyWith<$Res> {
  _$CompleteLessonResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CompleteLessonResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? userId = null,
    Object? motifId = null,
    Object? status = null,
    Object? lessonViewedAt = freezed,
    Object? learnedAt = freezed,
    Object? xpEarned = null,
    Object? totalXp = null,
  }) {
    return _then(_value.copyWith(
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      lessonViewedAt: freezed == lessonViewedAt
          ? _value.lessonViewedAt
          : lessonViewedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CompleteLessonResponseDtoImplCopyWith<$Res>
    implements $CompleteLessonResponseDtoCopyWith<$Res> {
  factory _$$CompleteLessonResponseDtoImplCopyWith(
          _$CompleteLessonResponseDtoImpl value,
          $Res Function(_$CompleteLessonResponseDtoImpl) then) =
      __$$CompleteLessonResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'motif_id') String motifId,
      String status,
      @JsonKey(name: 'lesson_viewed_at') DateTime? lessonViewedAt,
      @JsonKey(name: 'learned_at') DateTime? learnedAt,
      @JsonKey(name: 'xp_awarded') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp});
}

/// @nodoc
class __$$CompleteLessonResponseDtoImplCopyWithImpl<$Res>
    extends _$CompleteLessonResponseDtoCopyWithImpl<$Res,
        _$CompleteLessonResponseDtoImpl>
    implements _$$CompleteLessonResponseDtoImplCopyWith<$Res> {
  __$$CompleteLessonResponseDtoImplCopyWithImpl(
      _$CompleteLessonResponseDtoImpl _value,
      $Res Function(_$CompleteLessonResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of CompleteLessonResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? userId = null,
    Object? motifId = null,
    Object? status = null,
    Object? lessonViewedAt = freezed,
    Object? learnedAt = freezed,
    Object? xpEarned = null,
    Object? totalXp = null,
  }) {
    return _then(_$CompleteLessonResponseDtoImpl(
      userId: null == userId
          ? _value.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      lessonViewedAt: freezed == lessonViewedAt
          ? _value.lessonViewedAt
          : lessonViewedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      learnedAt: freezed == learnedAt
          ? _value.learnedAt
          : learnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CompleteLessonResponseDtoImpl implements _CompleteLessonResponseDto {
  const _$CompleteLessonResponseDtoImpl(
      {@JsonKey(name: 'user_id') required this.userId,
      @JsonKey(name: 'motif_id') required this.motifId,
      required this.status,
      @JsonKey(name: 'lesson_viewed_at') this.lessonViewedAt,
      @JsonKey(name: 'learned_at') this.learnedAt,
      @JsonKey(name: 'xp_awarded') this.xpEarned = 0,
      @JsonKey(name: 'total_xp') this.totalXp = 0});

  factory _$CompleteLessonResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CompleteLessonResponseDtoImplFromJson(json);

  @override
  @JsonKey(name: 'user_id')
  final String userId;
  @override
  @JsonKey(name: 'motif_id')
  final String motifId;
  @override
  final String status;
  @override
  @JsonKey(name: 'lesson_viewed_at')
  final DateTime? lessonViewedAt;
  @override
  @JsonKey(name: 'learned_at')
  final DateTime? learnedAt;
  @override
  @JsonKey(name: 'xp_awarded')
  final int xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;

  @override
  String toString() {
    return 'CompleteLessonResponseDto(userId: $userId, motifId: $motifId, status: $status, lessonViewedAt: $lessonViewedAt, learnedAt: $learnedAt, xpEarned: $xpEarned, totalXp: $totalXp)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CompleteLessonResponseDtoImpl &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.lessonViewedAt, lessonViewedAt) ||
                other.lessonViewedAt == lessonViewedAt) &&
            (identical(other.learnedAt, learnedAt) ||
                other.learnedAt == learnedAt) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, userId, motifId, status,
      lessonViewedAt, learnedAt, xpEarned, totalXp);

  /// Create a copy of CompleteLessonResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CompleteLessonResponseDtoImplCopyWith<_$CompleteLessonResponseDtoImpl>
      get copyWith => __$$CompleteLessonResponseDtoImplCopyWithImpl<
          _$CompleteLessonResponseDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CompleteLessonResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _CompleteLessonResponseDto implements CompleteLessonResponseDto {
  const factory _CompleteLessonResponseDto(
          {@JsonKey(name: 'user_id') required final String userId,
          @JsonKey(name: 'motif_id') required final String motifId,
          required final String status,
          @JsonKey(name: 'lesson_viewed_at') final DateTime? lessonViewedAt,
          @JsonKey(name: 'learned_at') final DateTime? learnedAt,
          @JsonKey(name: 'xp_awarded') final int xpEarned,
          @JsonKey(name: 'total_xp') final int totalXp}) =
      _$CompleteLessonResponseDtoImpl;

  factory _CompleteLessonResponseDto.fromJson(Map<String, dynamic> json) =
      _$CompleteLessonResponseDtoImpl.fromJson;

  @override
  @JsonKey(name: 'user_id')
  String get userId;
  @override
  @JsonKey(name: 'motif_id')
  String get motifId;
  @override
  String get status;
  @override
  @JsonKey(name: 'lesson_viewed_at')
  DateTime? get lessonViewedAt;
  @override
  @JsonKey(name: 'learned_at')
  DateTime? get learnedAt;
  @override
  @JsonKey(name: 'xp_awarded')
  int get xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  int get totalXp;

  /// Create a copy of CompleteLessonResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CompleteLessonResponseDtoImplCopyWith<_$CompleteLessonResponseDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

QuizQuestionDto _$QuizQuestionDtoFromJson(Map<String, dynamic> json) {
  return _QuizQuestionDto.fromJson(json);
}

/// @nodoc
mixin _$QuizQuestionDto {
  String get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_id')
  String? get motifId => throw _privateConstructorUsedError;
  @JsonKey(name: 'question_type')
  String get questionType => throw _privateConstructorUsedError;
  @JsonKey(name: 'question_text')
  String get questionText => throw _privateConstructorUsedError;
  @JsonKey(name: 'correct_answer')
  String? get correctAnswer => throw _privateConstructorUsedError;
  @OptionsListConverter()
  List<String> get options => throw _privateConstructorUsedError;
  @JsonKey(name: 'image_url')
  String? get imageUrl => throw _privateConstructorUsedError;
  String? get explanation => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_order')
  int get displayOrder => throw _privateConstructorUsedError;
  @JsonKey(name: 'target_mesh_name')
  String? get targetMeshName => throw _privateConstructorUsedError;
  int get difficulty => throw _privateConstructorUsedError;

  /// Serializes this QuizQuestionDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizQuestionDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizQuestionDtoCopyWith<QuizQuestionDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizQuestionDtoCopyWith<$Res> {
  factory $QuizQuestionDtoCopyWith(
          QuizQuestionDto value, $Res Function(QuizQuestionDto) then) =
      _$QuizQuestionDtoCopyWithImpl<$Res, QuizQuestionDto>;
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'motif_id') String? motifId,
      @JsonKey(name: 'question_type') String questionType,
      @JsonKey(name: 'question_text') String questionText,
      @JsonKey(name: 'correct_answer') String? correctAnswer,
      @OptionsListConverter() List<String> options,
      @JsonKey(name: 'image_url') String? imageUrl,
      String? explanation,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'target_mesh_name') String? targetMeshName,
      int difficulty});
}

/// @nodoc
class _$QuizQuestionDtoCopyWithImpl<$Res, $Val extends QuizQuestionDto>
    implements $QuizQuestionDtoCopyWith<$Res> {
  _$QuizQuestionDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizQuestionDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = freezed,
    Object? questionType = null,
    Object? questionText = null,
    Object? correctAnswer = freezed,
    Object? options = null,
    Object? imageUrl = freezed,
    Object? explanation = freezed,
    Object? displayOrder = null,
    Object? targetMeshName = freezed,
    Object? difficulty = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      questionType: null == questionType
          ? _value.questionType
          : questionType // ignore: cast_nullable_to_non_nullable
              as String,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      correctAnswer: freezed == correctAnswer
          ? _value.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      options: null == options
          ? _value.options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      targetMeshName: freezed == targetMeshName
          ? _value.targetMeshName
          : targetMeshName // ignore: cast_nullable_to_non_nullable
              as String?,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizQuestionDtoImplCopyWith<$Res>
    implements $QuizQuestionDtoCopyWith<$Res> {
  factory _$$QuizQuestionDtoImplCopyWith(_$QuizQuestionDtoImpl value,
          $Res Function(_$QuizQuestionDtoImpl) then) =
      __$$QuizQuestionDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'motif_id') String? motifId,
      @JsonKey(name: 'question_type') String questionType,
      @JsonKey(name: 'question_text') String questionText,
      @JsonKey(name: 'correct_answer') String? correctAnswer,
      @OptionsListConverter() List<String> options,
      @JsonKey(name: 'image_url') String? imageUrl,
      String? explanation,
      @JsonKey(name: 'display_order') int displayOrder,
      @JsonKey(name: 'target_mesh_name') String? targetMeshName,
      int difficulty});
}

/// @nodoc
class __$$QuizQuestionDtoImplCopyWithImpl<$Res>
    extends _$QuizQuestionDtoCopyWithImpl<$Res, _$QuizQuestionDtoImpl>
    implements _$$QuizQuestionDtoImplCopyWith<$Res> {
  __$$QuizQuestionDtoImplCopyWithImpl(
      _$QuizQuestionDtoImpl _value, $Res Function(_$QuizQuestionDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizQuestionDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = freezed,
    Object? questionType = null,
    Object? questionText = null,
    Object? correctAnswer = freezed,
    Object? options = null,
    Object? imageUrl = freezed,
    Object? explanation = freezed,
    Object? displayOrder = null,
    Object? targetMeshName = freezed,
    Object? difficulty = null,
  }) {
    return _then(_$QuizQuestionDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: freezed == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String?,
      questionType: null == questionType
          ? _value.questionType
          : questionType // ignore: cast_nullable_to_non_nullable
              as String,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      correctAnswer: freezed == correctAnswer
          ? _value.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      options: null == options
          ? _value._options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _value.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
      displayOrder: null == displayOrder
          ? _value.displayOrder
          : displayOrder // ignore: cast_nullable_to_non_nullable
              as int,
      targetMeshName: freezed == targetMeshName
          ? _value.targetMeshName
          : targetMeshName // ignore: cast_nullable_to_non_nullable
              as String?,
      difficulty: null == difficulty
          ? _value.difficulty
          : difficulty // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizQuestionDtoImpl implements _QuizQuestionDto {
  const _$QuizQuestionDtoImpl(
      {required this.id,
      @JsonKey(name: 'motif_id') this.motifId,
      @JsonKey(name: 'question_type') required this.questionType,
      @JsonKey(name: 'question_text') required this.questionText,
      @JsonKey(name: 'correct_answer') this.correctAnswer,
      @OptionsListConverter() final List<String> options = const [],
      @JsonKey(name: 'image_url') this.imageUrl,
      this.explanation,
      @JsonKey(name: 'display_order') this.displayOrder = 0,
      @JsonKey(name: 'target_mesh_name') this.targetMeshName,
      this.difficulty = 1})
      : _options = options;

  factory _$QuizQuestionDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizQuestionDtoImplFromJson(json);

  @override
  final String id;
  @override
  @JsonKey(name: 'motif_id')
  final String? motifId;
  @override
  @JsonKey(name: 'question_type')
  final String questionType;
  @override
  @JsonKey(name: 'question_text')
  final String questionText;
  @override
  @JsonKey(name: 'correct_answer')
  final String? correctAnswer;
  final List<String> _options;
  @override
  @JsonKey()
  @OptionsListConverter()
  List<String> get options {
    if (_options is EqualUnmodifiableListView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_options);
  }

  @override
  @JsonKey(name: 'image_url')
  final String? imageUrl;
  @override
  final String? explanation;
  @override
  @JsonKey(name: 'display_order')
  final int displayOrder;
  @override
  @JsonKey(name: 'target_mesh_name')
  final String? targetMeshName;
  @override
  @JsonKey()
  final int difficulty;

  @override
  String toString() {
    return 'QuizQuestionDto(id: $id, motifId: $motifId, questionType: $questionType, questionText: $questionText, correctAnswer: $correctAnswer, options: $options, imageUrl: $imageUrl, explanation: $explanation, displayOrder: $displayOrder, targetMeshName: $targetMeshName, difficulty: $difficulty)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizQuestionDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.questionType, questionType) ||
                other.questionType == questionType) &&
            (identical(other.questionText, questionText) ||
                other.questionText == questionText) &&
            (identical(other.correctAnswer, correctAnswer) ||
                other.correctAnswer == correctAnswer) &&
            const DeepCollectionEquality().equals(other._options, _options) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            (identical(other.displayOrder, displayOrder) ||
                other.displayOrder == displayOrder) &&
            (identical(other.targetMeshName, targetMeshName) ||
                other.targetMeshName == targetMeshName) &&
            (identical(other.difficulty, difficulty) ||
                other.difficulty == difficulty));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      motifId,
      questionType,
      questionText,
      correctAnswer,
      const DeepCollectionEquality().hash(_options),
      imageUrl,
      explanation,
      displayOrder,
      targetMeshName,
      difficulty);

  /// Create a copy of QuizQuestionDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizQuestionDtoImplCopyWith<_$QuizQuestionDtoImpl> get copyWith =>
      __$$QuizQuestionDtoImplCopyWithImpl<_$QuizQuestionDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizQuestionDtoImplToJson(
      this,
    );
  }
}

abstract class _QuizQuestionDto implements QuizQuestionDto {
  const factory _QuizQuestionDto(
      {required final String id,
      @JsonKey(name: 'motif_id') final String? motifId,
      @JsonKey(name: 'question_type') required final String questionType,
      @JsonKey(name: 'question_text') required final String questionText,
      @JsonKey(name: 'correct_answer') final String? correctAnswer,
      @OptionsListConverter() final List<String> options,
      @JsonKey(name: 'image_url') final String? imageUrl,
      final String? explanation,
      @JsonKey(name: 'display_order') final int displayOrder,
      @JsonKey(name: 'target_mesh_name') final String? targetMeshName,
      final int difficulty}) = _$QuizQuestionDtoImpl;

  factory _QuizQuestionDto.fromJson(Map<String, dynamic> json) =
      _$QuizQuestionDtoImpl.fromJson;

  @override
  String get id;
  @override
  @JsonKey(name: 'motif_id')
  String? get motifId;
  @override
  @JsonKey(name: 'question_type')
  String get questionType;
  @override
  @JsonKey(name: 'question_text')
  String get questionText;
  @override
  @JsonKey(name: 'correct_answer')
  String? get correctAnswer;
  @override
  @OptionsListConverter()
  List<String> get options;
  @override
  @JsonKey(name: 'image_url')
  String? get imageUrl;
  @override
  String? get explanation;
  @override
  @JsonKey(name: 'display_order')
  int get displayOrder;
  @override
  @JsonKey(name: 'target_mesh_name')
  String? get targetMeshName;
  @override
  int get difficulty;

  /// Create a copy of QuizQuestionDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizQuestionDtoImplCopyWith<_$QuizQuestionDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuizResponseDto _$QuizResponseDtoFromJson(Map<String, dynamic> json) {
  return _QuizResponseDto.fromJson(json);
}

/// @nodoc
mixin _$QuizResponseDto {
  @JsonKey(name: 'motif_id')
  String get motifId => throw _privateConstructorUsedError;
  @JsonKey(name: 'motif_name')
  String? get motifName => throw _privateConstructorUsedError;
  List<QuizQuestionDto> get questions => throw _privateConstructorUsedError;
  int get attempts => throw _privateConstructorUsedError;
  @JsonKey(name: 'best_score')
  int get bestScore => throw _privateConstructorUsedError;
  @JsonKey(name: 'pass_percent')
  int get passPercent => throw _privateConstructorUsedError;

  /// Serializes this QuizResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizResponseDtoCopyWith<QuizResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizResponseDtoCopyWith<$Res> {
  factory $QuizResponseDtoCopyWith(
          QuizResponseDto value, $Res Function(QuizResponseDto) then) =
      _$QuizResponseDtoCopyWithImpl<$Res, QuizResponseDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'motif_id') String motifId,
      @JsonKey(name: 'motif_name') String? motifName,
      List<QuizQuestionDto> questions,
      int attempts,
      @JsonKey(name: 'best_score') int bestScore,
      @JsonKey(name: 'pass_percent') int passPercent});
}

/// @nodoc
class _$QuizResponseDtoCopyWithImpl<$Res, $Val extends QuizResponseDto>
    implements $QuizResponseDtoCopyWith<$Res> {
  _$QuizResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = freezed,
    Object? questions = null,
    Object? attempts = null,
    Object? bestScore = null,
    Object? passPercent = null,
  }) {
    return _then(_value.copyWith(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      motifName: freezed == motifName
          ? _value.motifName
          : motifName // ignore: cast_nullable_to_non_nullable
              as String?,
      questions: null == questions
          ? _value.questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestionDto>,
      attempts: null == attempts
          ? _value.attempts
          : attempts // ignore: cast_nullable_to_non_nullable
              as int,
      bestScore: null == bestScore
          ? _value.bestScore
          : bestScore // ignore: cast_nullable_to_non_nullable
              as int,
      passPercent: null == passPercent
          ? _value.passPercent
          : passPercent // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizResponseDtoImplCopyWith<$Res>
    implements $QuizResponseDtoCopyWith<$Res> {
  factory _$$QuizResponseDtoImplCopyWith(_$QuizResponseDtoImpl value,
          $Res Function(_$QuizResponseDtoImpl) then) =
      __$$QuizResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'motif_id') String motifId,
      @JsonKey(name: 'motif_name') String? motifName,
      List<QuizQuestionDto> questions,
      int attempts,
      @JsonKey(name: 'best_score') int bestScore,
      @JsonKey(name: 'pass_percent') int passPercent});
}

/// @nodoc
class __$$QuizResponseDtoImplCopyWithImpl<$Res>
    extends _$QuizResponseDtoCopyWithImpl<$Res, _$QuizResponseDtoImpl>
    implements _$$QuizResponseDtoImplCopyWith<$Res> {
  __$$QuizResponseDtoImplCopyWithImpl(
      _$QuizResponseDtoImpl _value, $Res Function(_$QuizResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = freezed,
    Object? questions = null,
    Object? attempts = null,
    Object? bestScore = null,
    Object? passPercent = null,
  }) {
    return _then(_$QuizResponseDtoImpl(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      motifName: freezed == motifName
          ? _value.motifName
          : motifName // ignore: cast_nullable_to_non_nullable
              as String?,
      questions: null == questions
          ? _value._questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestionDto>,
      attempts: null == attempts
          ? _value.attempts
          : attempts // ignore: cast_nullable_to_non_nullable
              as int,
      bestScore: null == bestScore
          ? _value.bestScore
          : bestScore // ignore: cast_nullable_to_non_nullable
              as int,
      passPercent: null == passPercent
          ? _value.passPercent
          : passPercent // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizResponseDtoImpl implements _QuizResponseDto {
  const _$QuizResponseDtoImpl(
      {@JsonKey(name: 'motif_id') required this.motifId,
      @JsonKey(name: 'motif_name') this.motifName,
      required final List<QuizQuestionDto> questions,
      this.attempts = 0,
      @JsonKey(name: 'best_score') this.bestScore = 0,
      @JsonKey(name: 'pass_percent') this.passPercent = 80})
      : _questions = questions;

  factory _$QuizResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizResponseDtoImplFromJson(json);

  @override
  @JsonKey(name: 'motif_id')
  final String motifId;
  @override
  @JsonKey(name: 'motif_name')
  final String? motifName;
  final List<QuizQuestionDto> _questions;
  @override
  List<QuizQuestionDto> get questions {
    if (_questions is EqualUnmodifiableListView) return _questions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questions);
  }

  @override
  @JsonKey()
  final int attempts;
  @override
  @JsonKey(name: 'best_score')
  final int bestScore;
  @override
  @JsonKey(name: 'pass_percent')
  final int passPercent;

  @override
  String toString() {
    return 'QuizResponseDto(motifId: $motifId, motifName: $motifName, questions: $questions, attempts: $attempts, bestScore: $bestScore, passPercent: $passPercent)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizResponseDtoImpl &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.motifName, motifName) ||
                other.motifName == motifName) &&
            const DeepCollectionEquality()
                .equals(other._questions, _questions) &&
            (identical(other.attempts, attempts) ||
                other.attempts == attempts) &&
            (identical(other.bestScore, bestScore) ||
                other.bestScore == bestScore) &&
            (identical(other.passPercent, passPercent) ||
                other.passPercent == passPercent));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      motifId,
      motifName,
      const DeepCollectionEquality().hash(_questions),
      attempts,
      bestScore,
      passPercent);

  /// Create a copy of QuizResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizResponseDtoImplCopyWith<_$QuizResponseDtoImpl> get copyWith =>
      __$$QuizResponseDtoImplCopyWithImpl<_$QuizResponseDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _QuizResponseDto implements QuizResponseDto {
  const factory _QuizResponseDto(
          {@JsonKey(name: 'motif_id') required final String motifId,
          @JsonKey(name: 'motif_name') final String? motifName,
          required final List<QuizQuestionDto> questions,
          final int attempts,
          @JsonKey(name: 'best_score') final int bestScore,
          @JsonKey(name: 'pass_percent') final int passPercent}) =
      _$QuizResponseDtoImpl;

  factory _QuizResponseDto.fromJson(Map<String, dynamic> json) =
      _$QuizResponseDtoImpl.fromJson;

  @override
  @JsonKey(name: 'motif_id')
  String get motifId;
  @override
  @JsonKey(name: 'motif_name')
  String? get motifName;
  @override
  List<QuizQuestionDto> get questions;
  @override
  int get attempts;
  @override
  @JsonKey(name: 'best_score')
  int get bestScore;
  @override
  @JsonKey(name: 'pass_percent')
  int get passPercent;

  /// Create a copy of QuizResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizResponseDtoImplCopyWith<_$QuizResponseDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuizSubmitRequestDto _$QuizSubmitRequestDtoFromJson(Map<String, dynamic> json) {
  return _QuizSubmitRequestDto.fromJson(json);
}

/// @nodoc
mixin _$QuizSubmitRequestDto {
  List<QuizAnswerDto> get answers => throw _privateConstructorUsedError;
  @JsonKey(name: 'time_taken_seconds')
  int? get timeTakenSeconds => throw _privateConstructorUsedError;

  /// Serializes this QuizSubmitRequestDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizSubmitRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizSubmitRequestDtoCopyWith<QuizSubmitRequestDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizSubmitRequestDtoCopyWith<$Res> {
  factory $QuizSubmitRequestDtoCopyWith(QuizSubmitRequestDto value,
          $Res Function(QuizSubmitRequestDto) then) =
      _$QuizSubmitRequestDtoCopyWithImpl<$Res, QuizSubmitRequestDto>;
  @useResult
  $Res call(
      {List<QuizAnswerDto> answers,
      @JsonKey(name: 'time_taken_seconds') int? timeTakenSeconds});
}

/// @nodoc
class _$QuizSubmitRequestDtoCopyWithImpl<$Res,
        $Val extends QuizSubmitRequestDto>
    implements $QuizSubmitRequestDtoCopyWith<$Res> {
  _$QuizSubmitRequestDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizSubmitRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answers = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_value.copyWith(
      answers: null == answers
          ? _value.answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<QuizAnswerDto>,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizSubmitRequestDtoImplCopyWith<$Res>
    implements $QuizSubmitRequestDtoCopyWith<$Res> {
  factory _$$QuizSubmitRequestDtoImplCopyWith(_$QuizSubmitRequestDtoImpl value,
          $Res Function(_$QuizSubmitRequestDtoImpl) then) =
      __$$QuizSubmitRequestDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<QuizAnswerDto> answers,
      @JsonKey(name: 'time_taken_seconds') int? timeTakenSeconds});
}

/// @nodoc
class __$$QuizSubmitRequestDtoImplCopyWithImpl<$Res>
    extends _$QuizSubmitRequestDtoCopyWithImpl<$Res, _$QuizSubmitRequestDtoImpl>
    implements _$$QuizSubmitRequestDtoImplCopyWith<$Res> {
  __$$QuizSubmitRequestDtoImplCopyWithImpl(_$QuizSubmitRequestDtoImpl _value,
      $Res Function(_$QuizSubmitRequestDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizSubmitRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? answers = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_$QuizSubmitRequestDtoImpl(
      answers: null == answers
          ? _value._answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<QuizAnswerDto>,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizSubmitRequestDtoImpl implements _QuizSubmitRequestDto {
  const _$QuizSubmitRequestDtoImpl(
      {required final List<QuizAnswerDto> answers,
      @JsonKey(name: 'time_taken_seconds') this.timeTakenSeconds})
      : _answers = answers;

  factory _$QuizSubmitRequestDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizSubmitRequestDtoImplFromJson(json);

  final List<QuizAnswerDto> _answers;
  @override
  List<QuizAnswerDto> get answers {
    if (_answers is EqualUnmodifiableListView) return _answers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_answers);
  }

  @override
  @JsonKey(name: 'time_taken_seconds')
  final int? timeTakenSeconds;

  @override
  String toString() {
    return 'QuizSubmitRequestDto(answers: $answers, timeTakenSeconds: $timeTakenSeconds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizSubmitRequestDtoImpl &&
            const DeepCollectionEquality().equals(other._answers, _answers) &&
            (identical(other.timeTakenSeconds, timeTakenSeconds) ||
                other.timeTakenSeconds == timeTakenSeconds));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType,
      const DeepCollectionEquality().hash(_answers), timeTakenSeconds);

  /// Create a copy of QuizSubmitRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizSubmitRequestDtoImplCopyWith<_$QuizSubmitRequestDtoImpl>
      get copyWith =>
          __$$QuizSubmitRequestDtoImplCopyWithImpl<_$QuizSubmitRequestDtoImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizSubmitRequestDtoImplToJson(
      this,
    );
  }
}

abstract class _QuizSubmitRequestDto implements QuizSubmitRequestDto {
  const factory _QuizSubmitRequestDto(
          {required final List<QuizAnswerDto> answers,
          @JsonKey(name: 'time_taken_seconds') final int? timeTakenSeconds}) =
      _$QuizSubmitRequestDtoImpl;

  factory _QuizSubmitRequestDto.fromJson(Map<String, dynamic> json) =
      _$QuizSubmitRequestDtoImpl.fromJson;

  @override
  List<QuizAnswerDto> get answers;
  @override
  @JsonKey(name: 'time_taken_seconds')
  int? get timeTakenSeconds;

  /// Create a copy of QuizSubmitRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizSubmitRequestDtoImplCopyWith<_$QuizSubmitRequestDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

QuizAnswerDto _$QuizAnswerDtoFromJson(Map<String, dynamic> json) {
  return _QuizAnswerDto.fromJson(json);
}

/// @nodoc
mixin _$QuizAnswerDto {
  @JsonKey(name: 'question_id')
  String get questionId => throw _privateConstructorUsedError;
  String get answer => throw _privateConstructorUsedError;

  /// Serializes this QuizAnswerDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizAnswerDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizAnswerDtoCopyWith<QuizAnswerDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizAnswerDtoCopyWith<$Res> {
  factory $QuizAnswerDtoCopyWith(
          QuizAnswerDto value, $Res Function(QuizAnswerDto) then) =
      _$QuizAnswerDtoCopyWithImpl<$Res, QuizAnswerDto>;
  @useResult
  $Res call({@JsonKey(name: 'question_id') String questionId, String answer});
}

/// @nodoc
class _$QuizAnswerDtoCopyWithImpl<$Res, $Val extends QuizAnswerDto>
    implements $QuizAnswerDtoCopyWith<$Res> {
  _$QuizAnswerDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizAnswerDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? answer = null,
  }) {
    return _then(_value.copyWith(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      answer: null == answer
          ? _value.answer
          : answer // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizAnswerDtoImplCopyWith<$Res>
    implements $QuizAnswerDtoCopyWith<$Res> {
  factory _$$QuizAnswerDtoImplCopyWith(
          _$QuizAnswerDtoImpl value, $Res Function(_$QuizAnswerDtoImpl) then) =
      __$$QuizAnswerDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({@JsonKey(name: 'question_id') String questionId, String answer});
}

/// @nodoc
class __$$QuizAnswerDtoImplCopyWithImpl<$Res>
    extends _$QuizAnswerDtoCopyWithImpl<$Res, _$QuizAnswerDtoImpl>
    implements _$$QuizAnswerDtoImplCopyWith<$Res> {
  __$$QuizAnswerDtoImplCopyWithImpl(
      _$QuizAnswerDtoImpl _value, $Res Function(_$QuizAnswerDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizAnswerDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? answer = null,
  }) {
    return _then(_$QuizAnswerDtoImpl(
      questionId: null == questionId
          ? _value.questionId
          : questionId // ignore: cast_nullable_to_non_nullable
              as String,
      answer: null == answer
          ? _value.answer
          : answer // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizAnswerDtoImpl implements _QuizAnswerDto {
  const _$QuizAnswerDtoImpl(
      {@JsonKey(name: 'question_id') required this.questionId,
      required this.answer});

  factory _$QuizAnswerDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizAnswerDtoImplFromJson(json);

  @override
  @JsonKey(name: 'question_id')
  final String questionId;
  @override
  final String answer;

  @override
  String toString() {
    return 'QuizAnswerDto(questionId: $questionId, answer: $answer)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizAnswerDtoImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.answer, answer) || other.answer == answer));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, questionId, answer);

  /// Create a copy of QuizAnswerDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizAnswerDtoImplCopyWith<_$QuizAnswerDtoImpl> get copyWith =>
      __$$QuizAnswerDtoImplCopyWithImpl<_$QuizAnswerDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizAnswerDtoImplToJson(
      this,
    );
  }
}

abstract class _QuizAnswerDto implements QuizAnswerDto {
  const factory _QuizAnswerDto(
      {@JsonKey(name: 'question_id') required final String questionId,
      required final String answer}) = _$QuizAnswerDtoImpl;

  factory _QuizAnswerDto.fromJson(Map<String, dynamic> json) =
      _$QuizAnswerDtoImpl.fromJson;

  @override
  @JsonKey(name: 'question_id')
  String get questionId;
  @override
  String get answer;

  /// Create a copy of QuizAnswerDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizAnswerDtoImplCopyWith<_$QuizAnswerDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuizResultDto _$QuizResultDtoFromJson(Map<String, dynamic> json) {
  return _QuizResultDto.fromJson(json);
}

/// @nodoc
mixin _$QuizResultDto {
  bool get passed => throw _privateConstructorUsedError;
  int get score => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_questions')
  int get totalQuestions => throw _privateConstructorUsedError;
  @JsonKey(name: 'correct_answers')
  int get correctAnswers => throw _privateConstructorUsedError;
  @JsonKey(name: 'percentage')
  int get percentage => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_earned')
  int get xpEarned => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_xp')
  int get totalXp => throw _privateConstructorUsedError;
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_new_best')
  bool get isNewBest => throw _privateConstructorUsedError;
  UserProgressDto? get progress => throw _privateConstructorUsedError;

  /// Serializes this QuizResultDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizResultDtoCopyWith<QuizResultDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizResultDtoCopyWith<$Res> {
  factory $QuizResultDtoCopyWith(
          QuizResultDto value, $Res Function(QuizResultDto) then) =
      _$QuizResultDtoCopyWithImpl<$Res, QuizResultDto>;
  @useResult
  $Res call(
      {bool passed,
      int score,
      @JsonKey(name: 'total_questions') int totalQuestions,
      @JsonKey(name: 'correct_answers') int correctAnswers,
      @JsonKey(name: 'percentage') int percentage,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'new_badges') List<BadgeDto> newBadges,
      @JsonKey(name: 'is_new_best') bool isNewBest,
      UserProgressDto? progress});

  $UserProgressDtoCopyWith<$Res>? get progress;
}

/// @nodoc
class _$QuizResultDtoCopyWithImpl<$Res, $Val extends QuizResultDto>
    implements $QuizResultDtoCopyWith<$Res> {
  _$QuizResultDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? passed = null,
    Object? score = null,
    Object? totalQuestions = null,
    Object? correctAnswers = null,
    Object? percentage = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
    Object? isNewBest = null,
    Object? progress = freezed,
  }) {
    return _then(_value.copyWith(
      passed: null == passed
          ? _value.passed
          : passed // ignore: cast_nullable_to_non_nullable
              as bool,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestions: null == totalQuestions
          ? _value.totalQuestions
          : totalQuestions // ignore: cast_nullable_to_non_nullable
              as int,
      correctAnswers: null == correctAnswers
          ? _value.correctAnswers
          : correctAnswers // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as int,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value.newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<BadgeDto>,
      isNewBest: null == isNewBest
          ? _value.isNewBest
          : isNewBest // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto?,
    ) as $Val);
  }

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserProgressDtoCopyWith<$Res>? get progress {
    if (_value.progress == null) {
      return null;
    }

    return $UserProgressDtoCopyWith<$Res>(_value.progress!, (value) {
      return _then(_value.copyWith(progress: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$QuizResultDtoImplCopyWith<$Res>
    implements $QuizResultDtoCopyWith<$Res> {
  factory _$$QuizResultDtoImplCopyWith(
          _$QuizResultDtoImpl value, $Res Function(_$QuizResultDtoImpl) then) =
      __$$QuizResultDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool passed,
      int score,
      @JsonKey(name: 'total_questions') int totalQuestions,
      @JsonKey(name: 'correct_answers') int correctAnswers,
      @JsonKey(name: 'percentage') int percentage,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'new_badges') List<BadgeDto> newBadges,
      @JsonKey(name: 'is_new_best') bool isNewBest,
      UserProgressDto? progress});

  @override
  $UserProgressDtoCopyWith<$Res>? get progress;
}

/// @nodoc
class __$$QuizResultDtoImplCopyWithImpl<$Res>
    extends _$QuizResultDtoCopyWithImpl<$Res, _$QuizResultDtoImpl>
    implements _$$QuizResultDtoImplCopyWith<$Res> {
  __$$QuizResultDtoImplCopyWithImpl(
      _$QuizResultDtoImpl _value, $Res Function(_$QuizResultDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? passed = null,
    Object? score = null,
    Object? totalQuestions = null,
    Object? correctAnswers = null,
    Object? percentage = null,
    Object? xpEarned = null,
    Object? totalXp = null,
    Object? newBadges = null,
    Object? isNewBest = null,
    Object? progress = freezed,
  }) {
    return _then(_$QuizResultDtoImpl(
      passed: null == passed
          ? _value.passed
          : passed // ignore: cast_nullable_to_non_nullable
              as bool,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      totalQuestions: null == totalQuestions
          ? _value.totalQuestions
          : totalQuestions // ignore: cast_nullable_to_non_nullable
              as int,
      correctAnswers: null == correctAnswers
          ? _value.correctAnswers
          : correctAnswers // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as int,
      xpEarned: null == xpEarned
          ? _value.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      newBadges: null == newBadges
          ? _value._newBadges
          : newBadges // ignore: cast_nullable_to_non_nullable
              as List<BadgeDto>,
      isNewBest: null == isNewBest
          ? _value.isNewBest
          : isNewBest // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as UserProgressDto?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizResultDtoImpl implements _QuizResultDto {
  const _$QuizResultDtoImpl(
      {required this.passed,
      required this.score,
      @JsonKey(name: 'total_questions') required this.totalQuestions,
      @JsonKey(name: 'correct_answers') required this.correctAnswers,
      @JsonKey(name: 'percentage') required this.percentage,
      @JsonKey(name: 'xp_earned') this.xpEarned = 0,
      @JsonKey(name: 'total_xp') this.totalXp = 0,
      @JsonKey(name: 'new_badges') final List<BadgeDto> newBadges = const [],
      @JsonKey(name: 'is_new_best') this.isNewBest = false,
      this.progress})
      : _newBadges = newBadges;

  factory _$QuizResultDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizResultDtoImplFromJson(json);

  @override
  final bool passed;
  @override
  final int score;
  @override
  @JsonKey(name: 'total_questions')
  final int totalQuestions;
  @override
  @JsonKey(name: 'correct_answers')
  final int correctAnswers;
  @override
  @JsonKey(name: 'percentage')
  final int percentage;
  @override
  @JsonKey(name: 'xp_earned')
  final int xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  final List<BadgeDto> _newBadges;
  @override
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges {
    if (_newBadges is EqualUnmodifiableListView) return _newBadges;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_newBadges);
  }

  @override
  @JsonKey(name: 'is_new_best')
  final bool isNewBest;
  @override
  final UserProgressDto? progress;

  @override
  String toString() {
    return 'QuizResultDto(passed: $passed, score: $score, totalQuestions: $totalQuestions, correctAnswers: $correctAnswers, percentage: $percentage, xpEarned: $xpEarned, totalXp: $totalXp, newBadges: $newBadges, isNewBest: $isNewBest, progress: $progress)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizResultDtoImpl &&
            (identical(other.passed, passed) || other.passed == passed) &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.totalQuestions, totalQuestions) ||
                other.totalQuestions == totalQuestions) &&
            (identical(other.correctAnswers, correctAnswers) ||
                other.correctAnswers == correctAnswers) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            const DeepCollectionEquality()
                .equals(other._newBadges, _newBadges) &&
            (identical(other.isNewBest, isNewBest) ||
                other.isNewBest == isNewBest) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      passed,
      score,
      totalQuestions,
      correctAnswers,
      percentage,
      xpEarned,
      totalXp,
      const DeepCollectionEquality().hash(_newBadges),
      isNewBest,
      progress);

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizResultDtoImplCopyWith<_$QuizResultDtoImpl> get copyWith =>
      __$$QuizResultDtoImplCopyWithImpl<_$QuizResultDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizResultDtoImplToJson(
      this,
    );
  }
}

abstract class _QuizResultDto implements QuizResultDto {
  const factory _QuizResultDto(
      {required final bool passed,
      required final int score,
      @JsonKey(name: 'total_questions') required final int totalQuestions,
      @JsonKey(name: 'correct_answers') required final int correctAnswers,
      @JsonKey(name: 'percentage') required final int percentage,
      @JsonKey(name: 'xp_earned') final int xpEarned,
      @JsonKey(name: 'total_xp') final int totalXp,
      @JsonKey(name: 'new_badges') final List<BadgeDto> newBadges,
      @JsonKey(name: 'is_new_best') final bool isNewBest,
      final UserProgressDto? progress}) = _$QuizResultDtoImpl;

  factory _QuizResultDto.fromJson(Map<String, dynamic> json) =
      _$QuizResultDtoImpl.fromJson;

  @override
  bool get passed;
  @override
  int get score;
  @override
  @JsonKey(name: 'total_questions')
  int get totalQuestions;
  @override
  @JsonKey(name: 'correct_answers')
  int get correctAnswers;
  @override
  @JsonKey(name: 'percentage')
  int get percentage;
  @override
  @JsonKey(name: 'xp_earned')
  int get xpEarned;
  @override
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @override
  @JsonKey(name: 'new_badges')
  List<BadgeDto> get newBadges;
  @override
  @JsonKey(name: 'is_new_best')
  bool get isNewBest;
  @override
  UserProgressDto? get progress;

  /// Create a copy of QuizResultDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizResultDtoImplCopyWith<_$QuizResultDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
