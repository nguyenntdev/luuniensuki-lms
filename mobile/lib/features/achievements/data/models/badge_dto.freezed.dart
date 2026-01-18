// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'badge_dto.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

BadgeDto _$BadgeDtoFromJson(Map<String, dynamic> json) {
  return _BadgeDto.fromJson(json);
}

/// @nodoc
mixin _$BadgeDto {
  /// ID field - uses slug as fallback since API doesn't return id
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
  @JsonKey(name: 'earned_at')
  String? get earnedAt => throw _privateConstructorUsedError;

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
      @JsonKey(name: 'xp_bonus') int xpBonus,
      @JsonKey(name: 'earned_at') String? earnedAt});
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
    Object? earnedAt = freezed,
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
      earnedAt: freezed == earnedAt
          ? _value.earnedAt
          : earnedAt // ignore: cast_nullable_to_non_nullable
              as String?,
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
      @JsonKey(name: 'xp_bonus') int xpBonus,
      @JsonKey(name: 'earned_at') String? earnedAt});
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
    Object? earnedAt = freezed,
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
      earnedAt: freezed == earnedAt
          ? _value.earnedAt
          : earnedAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$BadgeDtoImpl implements _BadgeDto {
  const _$BadgeDtoImpl(
      {this.id = '',
      this.slug = '',
      this.name = '',
      @JsonKey(name: 'name_en') this.nameEn,
      this.description,
      @JsonKey(name: 'icon_url') this.iconUrl,
      this.category = 'achievement',
      @JsonKey(name: 'xp_bonus') this.xpBonus = 0,
      @JsonKey(name: 'earned_at') this.earnedAt});

  factory _$BadgeDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$BadgeDtoImplFromJson(json);

  /// ID field - uses slug as fallback since API doesn't return id
  @override
  @JsonKey()
  final String id;
  @override
  @JsonKey()
  final String slug;
  @override
  @JsonKey()
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
  @JsonKey()
  final String category;
  @override
  @JsonKey(name: 'xp_bonus')
  final int xpBonus;
  @override
  @JsonKey(name: 'earned_at')
  final String? earnedAt;

  @override
  String toString() {
    return 'BadgeDto(id: $id, slug: $slug, name: $name, nameEn: $nameEn, description: $description, iconUrl: $iconUrl, category: $category, xpBonus: $xpBonus, earnedAt: $earnedAt)';
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
            (identical(other.xpBonus, xpBonus) || other.xpBonus == xpBonus) &&
            (identical(other.earnedAt, earnedAt) ||
                other.earnedAt == earnedAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, slug, name, nameEn,
      description, iconUrl, category, xpBonus, earnedAt);

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
      {final String id,
      final String slug,
      final String name,
      @JsonKey(name: 'name_en') final String? nameEn,
      final String? description,
      @JsonKey(name: 'icon_url') final String? iconUrl,
      final String category,
      @JsonKey(name: 'xp_bonus') final int xpBonus,
      @JsonKey(name: 'earned_at') final String? earnedAt}) = _$BadgeDtoImpl;

  factory _BadgeDto.fromJson(Map<String, dynamic> json) =
      _$BadgeDtoImpl.fromJson;

  /// ID field - uses slug as fallback since API doesn't return id
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
  @override
  @JsonKey(name: 'earned_at')
  String? get earnedAt;

  /// Create a copy of BadgeDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$BadgeDtoImplCopyWith<_$BadgeDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
