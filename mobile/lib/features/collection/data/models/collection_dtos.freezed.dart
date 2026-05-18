// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'collection_dtos.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

CollectionStatsDto _$CollectionStatsDtoFromJson(Map<String, dynamic> json) {
  return _CollectionStatsDto.fromJson(json);
}

/// @nodoc
mixin _$CollectionStatsDto {
  int get total => throw _privateConstructorUsedError;
  int get discovered => throw _privateConstructorUsedError;
  int get learned => throw _privateConstructorUsedError;
  int get mastered => throw _privateConstructorUsedError;

  /// Serializes this CollectionStatsDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CollectionStatsDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CollectionStatsDtoCopyWith<CollectionStatsDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CollectionStatsDtoCopyWith<$Res> {
  factory $CollectionStatsDtoCopyWith(
          CollectionStatsDto value, $Res Function(CollectionStatsDto) then) =
      _$CollectionStatsDtoCopyWithImpl<$Res, CollectionStatsDto>;
  @useResult
  $Res call({int total, int discovered, int learned, int mastered});
}

/// @nodoc
class _$CollectionStatsDtoCopyWithImpl<$Res, $Val extends CollectionStatsDto>
    implements $CollectionStatsDtoCopyWith<$Res> {
  _$CollectionStatsDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CollectionStatsDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? total = null,
    Object? discovered = null,
    Object? learned = null,
    Object? mastered = null,
  }) {
    return _then(_value.copyWith(
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      discovered: null == discovered
          ? _value.discovered
          : discovered // ignore: cast_nullable_to_non_nullable
              as int,
      learned: null == learned
          ? _value.learned
          : learned // ignore: cast_nullable_to_non_nullable
              as int,
      mastered: null == mastered
          ? _value.mastered
          : mastered // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CollectionStatsDtoImplCopyWith<$Res>
    implements $CollectionStatsDtoCopyWith<$Res> {
  factory _$$CollectionStatsDtoImplCopyWith(_$CollectionStatsDtoImpl value,
          $Res Function(_$CollectionStatsDtoImpl) then) =
      __$$CollectionStatsDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int total, int discovered, int learned, int mastered});
}

/// @nodoc
class __$$CollectionStatsDtoImplCopyWithImpl<$Res>
    extends _$CollectionStatsDtoCopyWithImpl<$Res, _$CollectionStatsDtoImpl>
    implements _$$CollectionStatsDtoImplCopyWith<$Res> {
  __$$CollectionStatsDtoImplCopyWithImpl(_$CollectionStatsDtoImpl _value,
      $Res Function(_$CollectionStatsDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of CollectionStatsDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? total = null,
    Object? discovered = null,
    Object? learned = null,
    Object? mastered = null,
  }) {
    return _then(_$CollectionStatsDtoImpl(
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      discovered: null == discovered
          ? _value.discovered
          : discovered // ignore: cast_nullable_to_non_nullable
              as int,
      learned: null == learned
          ? _value.learned
          : learned // ignore: cast_nullable_to_non_nullable
              as int,
      mastered: null == mastered
          ? _value.mastered
          : mastered // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CollectionStatsDtoImpl implements _CollectionStatsDto {
  const _$CollectionStatsDtoImpl(
      {required this.total,
      required this.discovered,
      required this.learned,
      required this.mastered});

  factory _$CollectionStatsDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CollectionStatsDtoImplFromJson(json);

  @override
  final int total;
  @override
  final int discovered;
  @override
  final int learned;
  @override
  final int mastered;

  @override
  String toString() {
    return 'CollectionStatsDto(total: $total, discovered: $discovered, learned: $learned, mastered: $mastered)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CollectionStatsDtoImpl &&
            (identical(other.total, total) || other.total == total) &&
            (identical(other.discovered, discovered) ||
                other.discovered == discovered) &&
            (identical(other.learned, learned) || other.learned == learned) &&
            (identical(other.mastered, mastered) ||
                other.mastered == mastered));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, total, discovered, learned, mastered);

  /// Create a copy of CollectionStatsDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CollectionStatsDtoImplCopyWith<_$CollectionStatsDtoImpl> get copyWith =>
      __$$CollectionStatsDtoImplCopyWithImpl<_$CollectionStatsDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CollectionStatsDtoImplToJson(
      this,
    );
  }
}

abstract class _CollectionStatsDto implements CollectionStatsDto {
  const factory _CollectionStatsDto(
      {required final int total,
      required final int discovered,
      required final int learned,
      required final int mastered}) = _$CollectionStatsDtoImpl;

  factory _CollectionStatsDto.fromJson(Map<String, dynamic> json) =
      _$CollectionStatsDtoImpl.fromJson;

  @override
  int get total;
  @override
  int get discovered;
  @override
  int get learned;
  @override
  int get mastered;

  /// Create a copy of CollectionStatsDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CollectionStatsDtoImplCopyWith<_$CollectionStatsDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CollectionMotifDto _$CollectionMotifDtoFromJson(Map<String, dynamic> json) {
  return _CollectionMotifDto.fromJson(json);
}

/// @nodoc
mixin _$CollectionMotifDto {
  @JsonKey(name: 'motif_id')
  String get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'mesh_name')
  String get meshName => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  String get rarity => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;

  /// Serializes this CollectionMotifDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CollectionMotifDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CollectionMotifDtoCopyWith<CollectionMotifDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CollectionMotifDtoCopyWith<$Res> {
  factory $CollectionMotifDtoCopyWith(
          CollectionMotifDto value, $Res Function(CollectionMotifDto) then) =
      _$CollectionMotifDtoCopyWithImpl<$Res, CollectionMotifDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'motif_id') String id,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String status});
}

/// @nodoc
class _$CollectionMotifDtoCopyWithImpl<$Res, $Val extends CollectionMotifDto>
    implements $CollectionMotifDtoCopyWith<$Res> {
  _$CollectionMotifDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CollectionMotifDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? thumbnailUrl = freezed,
    Object? status = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
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
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CollectionMotifDtoImplCopyWith<$Res>
    implements $CollectionMotifDtoCopyWith<$Res> {
  factory _$$CollectionMotifDtoImplCopyWith(_$CollectionMotifDtoImpl value,
          $Res Function(_$CollectionMotifDtoImpl) then) =
      __$$CollectionMotifDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'motif_id') String id,
      @JsonKey(name: 'mesh_name') String meshName,
      String name,
      @JsonKey(name: 'name_en') String? nameEn,
      String category,
      String rarity,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String status});
}

/// @nodoc
class __$$CollectionMotifDtoImplCopyWithImpl<$Res>
    extends _$CollectionMotifDtoCopyWithImpl<$Res, _$CollectionMotifDtoImpl>
    implements _$$CollectionMotifDtoImplCopyWith<$Res> {
  __$$CollectionMotifDtoImplCopyWithImpl(_$CollectionMotifDtoImpl _value,
      $Res Function(_$CollectionMotifDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of CollectionMotifDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? meshName = null,
    Object? name = null,
    Object? nameEn = freezed,
    Object? category = null,
    Object? rarity = null,
    Object? thumbnailUrl = freezed,
    Object? status = null,
  }) {
    return _then(_$CollectionMotifDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
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
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CollectionMotifDtoImpl implements _CollectionMotifDto {
  const _$CollectionMotifDtoImpl(
      {@JsonKey(name: 'motif_id') required this.id,
      @JsonKey(name: 'mesh_name') required this.meshName,
      required this.name,
      @JsonKey(name: 'name_en') this.nameEn,
      required this.category,
      required this.rarity,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      required this.status});

  factory _$CollectionMotifDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CollectionMotifDtoImplFromJson(json);

  @override
  @JsonKey(name: 'motif_id')
  final String id;
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
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  final String status;

  @override
  String toString() {
    return 'CollectionMotifDto(id: $id, meshName: $meshName, name: $name, nameEn: $nameEn, category: $category, rarity: $rarity, thumbnailUrl: $thumbnailUrl, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CollectionMotifDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.meshName, meshName) ||
                other.meshName == meshName) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.rarity, rarity) || other.rarity == rarity) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.status, status) || other.status == status));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, meshName, name, nameEn,
      category, rarity, thumbnailUrl, status);

  /// Create a copy of CollectionMotifDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CollectionMotifDtoImplCopyWith<_$CollectionMotifDtoImpl> get copyWith =>
      __$$CollectionMotifDtoImplCopyWithImpl<_$CollectionMotifDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CollectionMotifDtoImplToJson(
      this,
    );
  }
}

abstract class _CollectionMotifDto implements CollectionMotifDto {
  const factory _CollectionMotifDto(
      {@JsonKey(name: 'motif_id') required final String id,
      @JsonKey(name: 'mesh_name') required final String meshName,
      required final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      required final String category,
      required final String rarity,
      @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
      required final String status}) = _$CollectionMotifDtoImpl;

  factory _CollectionMotifDto.fromJson(Map<String, dynamic> json) =
      _$CollectionMotifDtoImpl.fromJson;

  @override
  @JsonKey(name: 'motif_id')
  String get id;
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
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  String get status;

  /// Create a copy of CollectionMotifDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CollectionMotifDtoImplCopyWith<_$CollectionMotifDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CollectionResponseDto _$CollectionResponseDtoFromJson(
    Map<String, dynamic> json) {
  return _CollectionResponseDto.fromJson(json);
}

/// @nodoc
mixin _$CollectionResponseDto {
  List<CollectionMotifDto> get items => throw _privateConstructorUsedError;
  CollectionStatsDto get stats => throw _privateConstructorUsedError;

  /// Serializes this CollectionResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CollectionResponseDtoCopyWith<CollectionResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CollectionResponseDtoCopyWith<$Res> {
  factory $CollectionResponseDtoCopyWith(CollectionResponseDto value,
          $Res Function(CollectionResponseDto) then) =
      _$CollectionResponseDtoCopyWithImpl<$Res, CollectionResponseDto>;
  @useResult
  $Res call({List<CollectionMotifDto> items, CollectionStatsDto stats});

  $CollectionStatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class _$CollectionResponseDtoCopyWithImpl<$Res,
        $Val extends CollectionResponseDto>
    implements $CollectionResponseDtoCopyWith<$Res> {
  _$CollectionResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? stats = null,
  }) {
    return _then(_value.copyWith(
      items: null == items
          ? _value.items
          : items // ignore: cast_nullable_to_non_nullable
              as List<CollectionMotifDto>,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as CollectionStatsDto,
    ) as $Val);
  }

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $CollectionStatsDtoCopyWith<$Res> get stats {
    return $CollectionStatsDtoCopyWith<$Res>(_value.stats, (value) {
      return _then(_value.copyWith(stats: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$CollectionResponseDtoImplCopyWith<$Res>
    implements $CollectionResponseDtoCopyWith<$Res> {
  factory _$$CollectionResponseDtoImplCopyWith(
          _$CollectionResponseDtoImpl value,
          $Res Function(_$CollectionResponseDtoImpl) then) =
      __$$CollectionResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({List<CollectionMotifDto> items, CollectionStatsDto stats});

  @override
  $CollectionStatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class __$$CollectionResponseDtoImplCopyWithImpl<$Res>
    extends _$CollectionResponseDtoCopyWithImpl<$Res,
        _$CollectionResponseDtoImpl>
    implements _$$CollectionResponseDtoImplCopyWith<$Res> {
  __$$CollectionResponseDtoImplCopyWithImpl(_$CollectionResponseDtoImpl _value,
      $Res Function(_$CollectionResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? stats = null,
  }) {
    return _then(_$CollectionResponseDtoImpl(
      items: null == items
          ? _value._items
          : items // ignore: cast_nullable_to_non_nullable
              as List<CollectionMotifDto>,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as CollectionStatsDto,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CollectionResponseDtoImpl implements _CollectionResponseDto {
  const _$CollectionResponseDtoImpl(
      {required final List<CollectionMotifDto> items, required this.stats})
      : _items = items;

  factory _$CollectionResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CollectionResponseDtoImplFromJson(json);

  final List<CollectionMotifDto> _items;
  @override
  List<CollectionMotifDto> get items {
    if (_items is EqualUnmodifiableListView) return _items;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_items);
  }

  @override
  final CollectionStatsDto stats;

  @override
  String toString() {
    return 'CollectionResponseDto(items: $items, stats: $stats)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CollectionResponseDtoImpl &&
            const DeepCollectionEquality().equals(other._items, _items) &&
            (identical(other.stats, stats) || other.stats == stats));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, const DeepCollectionEquality().hash(_items), stats);

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CollectionResponseDtoImplCopyWith<_$CollectionResponseDtoImpl>
      get copyWith => __$$CollectionResponseDtoImplCopyWithImpl<
          _$CollectionResponseDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CollectionResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _CollectionResponseDto implements CollectionResponseDto {
  const factory _CollectionResponseDto(
      {required final List<CollectionMotifDto> items,
      required final CollectionStatsDto stats}) = _$CollectionResponseDtoImpl;

  factory _CollectionResponseDto.fromJson(Map<String, dynamic> json) =
      _$CollectionResponseDtoImpl.fromJson;

  @override
  List<CollectionMotifDto> get items;
  @override
  CollectionStatsDto get stats;

  /// Create a copy of CollectionResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CollectionResponseDtoImplCopyWith<_$CollectionResponseDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}
