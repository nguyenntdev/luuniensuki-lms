// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'auth_dtos.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

LoginRequestDto _$LoginRequestDtoFromJson(Map<String, dynamic> json) {
  return _LoginRequestDto.fromJson(json);
}

/// @nodoc
mixin _$LoginRequestDto {
  String get email => throw _privateConstructorUsedError;
  String get password => throw _privateConstructorUsedError;

  /// Serializes this LoginRequestDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of LoginRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LoginRequestDtoCopyWith<LoginRequestDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LoginRequestDtoCopyWith<$Res> {
  factory $LoginRequestDtoCopyWith(
          LoginRequestDto value, $Res Function(LoginRequestDto) then) =
      _$LoginRequestDtoCopyWithImpl<$Res, LoginRequestDto>;
  @useResult
  $Res call({String email, String password});
}

/// @nodoc
class _$LoginRequestDtoCopyWithImpl<$Res, $Val extends LoginRequestDto>
    implements $LoginRequestDtoCopyWith<$Res> {
  _$LoginRequestDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LoginRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? email = null,
    Object? password = null,
  }) {
    return _then(_value.copyWith(
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      password: null == password
          ? _value.password
          : password // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$LoginRequestDtoImplCopyWith<$Res>
    implements $LoginRequestDtoCopyWith<$Res> {
  factory _$$LoginRequestDtoImplCopyWith(_$LoginRequestDtoImpl value,
          $Res Function(_$LoginRequestDtoImpl) then) =
      __$$LoginRequestDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String email, String password});
}

/// @nodoc
class __$$LoginRequestDtoImplCopyWithImpl<$Res>
    extends _$LoginRequestDtoCopyWithImpl<$Res, _$LoginRequestDtoImpl>
    implements _$$LoginRequestDtoImplCopyWith<$Res> {
  __$$LoginRequestDtoImplCopyWithImpl(
      _$LoginRequestDtoImpl _value, $Res Function(_$LoginRequestDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of LoginRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? email = null,
    Object? password = null,
  }) {
    return _then(_$LoginRequestDtoImpl(
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      password: null == password
          ? _value.password
          : password // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$LoginRequestDtoImpl implements _LoginRequestDto {
  const _$LoginRequestDtoImpl({required this.email, required this.password});

  factory _$LoginRequestDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$LoginRequestDtoImplFromJson(json);

  @override
  final String email;
  @override
  final String password;

  @override
  String toString() {
    return 'LoginRequestDto(email: $email, password: $password)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LoginRequestDtoImpl &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.password, password) ||
                other.password == password));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, email, password);

  /// Create a copy of LoginRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LoginRequestDtoImplCopyWith<_$LoginRequestDtoImpl> get copyWith =>
      __$$LoginRequestDtoImplCopyWithImpl<_$LoginRequestDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LoginRequestDtoImplToJson(
      this,
    );
  }
}

abstract class _LoginRequestDto implements LoginRequestDto {
  const factory _LoginRequestDto(
      {required final String email,
      required final String password}) = _$LoginRequestDtoImpl;

  factory _LoginRequestDto.fromJson(Map<String, dynamic> json) =
      _$LoginRequestDtoImpl.fromJson;

  @override
  String get email;
  @override
  String get password;

  /// Create a copy of LoginRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LoginRequestDtoImplCopyWith<_$LoginRequestDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RegisterRequestDto _$RegisterRequestDtoFromJson(Map<String, dynamic> json) {
  return _RegisterRequestDto.fromJson(json);
}

/// @nodoc
mixin _$RegisterRequestDto {
  String get email => throw _privateConstructorUsedError;
  String get password => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_name')
  String get displayName => throw _privateConstructorUsedError;

  /// Serializes this RegisterRequestDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RegisterRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RegisterRequestDtoCopyWith<RegisterRequestDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RegisterRequestDtoCopyWith<$Res> {
  factory $RegisterRequestDtoCopyWith(
          RegisterRequestDto value, $Res Function(RegisterRequestDto) then) =
      _$RegisterRequestDtoCopyWithImpl<$Res, RegisterRequestDto>;
  @useResult
  $Res call(
      {String email,
      String password,
      @JsonKey(name: 'display_name') String displayName});
}

/// @nodoc
class _$RegisterRequestDtoCopyWithImpl<$Res, $Val extends RegisterRequestDto>
    implements $RegisterRequestDtoCopyWith<$Res> {
  _$RegisterRequestDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RegisterRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? email = null,
    Object? password = null,
    Object? displayName = null,
  }) {
    return _then(_value.copyWith(
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      password: null == password
          ? _value.password
          : password // ignore: cast_nullable_to_non_nullable
              as String,
      displayName: null == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RegisterRequestDtoImplCopyWith<$Res>
    implements $RegisterRequestDtoCopyWith<$Res> {
  factory _$$RegisterRequestDtoImplCopyWith(_$RegisterRequestDtoImpl value,
          $Res Function(_$RegisterRequestDtoImpl) then) =
      __$$RegisterRequestDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String email,
      String password,
      @JsonKey(name: 'display_name') String displayName});
}

/// @nodoc
class __$$RegisterRequestDtoImplCopyWithImpl<$Res>
    extends _$RegisterRequestDtoCopyWithImpl<$Res, _$RegisterRequestDtoImpl>
    implements _$$RegisterRequestDtoImplCopyWith<$Res> {
  __$$RegisterRequestDtoImplCopyWithImpl(_$RegisterRequestDtoImpl _value,
      $Res Function(_$RegisterRequestDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of RegisterRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? email = null,
    Object? password = null,
    Object? displayName = null,
  }) {
    return _then(_$RegisterRequestDtoImpl(
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      password: null == password
          ? _value.password
          : password // ignore: cast_nullable_to_non_nullable
              as String,
      displayName: null == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RegisterRequestDtoImpl implements _RegisterRequestDto {
  const _$RegisterRequestDtoImpl(
      {required this.email,
      required this.password,
      @JsonKey(name: 'display_name') required this.displayName});

  factory _$RegisterRequestDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$RegisterRequestDtoImplFromJson(json);

  @override
  final String email;
  @override
  final String password;
  @override
  @JsonKey(name: 'display_name')
  final String displayName;

  @override
  String toString() {
    return 'RegisterRequestDto(email: $email, password: $password, displayName: $displayName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RegisterRequestDtoImpl &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.password, password) ||
                other.password == password) &&
            (identical(other.displayName, displayName) ||
                other.displayName == displayName));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, email, password, displayName);

  /// Create a copy of RegisterRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RegisterRequestDtoImplCopyWith<_$RegisterRequestDtoImpl> get copyWith =>
      __$$RegisterRequestDtoImplCopyWithImpl<_$RegisterRequestDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RegisterRequestDtoImplToJson(
      this,
    );
  }
}

abstract class _RegisterRequestDto implements RegisterRequestDto {
  const factory _RegisterRequestDto(
          {required final String email,
          required final String password,
          @JsonKey(name: 'display_name') required final String displayName}) =
      _$RegisterRequestDtoImpl;

  factory _RegisterRequestDto.fromJson(Map<String, dynamic> json) =
      _$RegisterRequestDtoImpl.fromJson;

  @override
  String get email;
  @override
  String get password;
  @override
  @JsonKey(name: 'display_name')
  String get displayName;

  /// Create a copy of RegisterRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RegisterRequestDtoImplCopyWith<_$RegisterRequestDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UserDto _$UserDtoFromJson(Map<String, dynamic> json) {
  return _UserDto.fromJson(json);
}

/// @nodoc
mixin _$UserDto {
  String get id => throw _privateConstructorUsedError;
  String get email => throw _privateConstructorUsedError;
  @JsonKey(name: 'display_name')
  String get displayName => throw _privateConstructorUsedError;
  @JsonKey(name: 'avatar_url')
  String? get avatarUrl => throw _privateConstructorUsedError;
  String? get username => throw _privateConstructorUsedError;
  String get role => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_xp')
  int get totalXp => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_profile_public')
  bool get isProfilePublic => throw _privateConstructorUsedError;
  @JsonKey(name: 'current_streak')
  int get currentStreak => throw _privateConstructorUsedError;
  @JsonKey(name: 'longest_streak')
  int get longestStreak => throw _privateConstructorUsedError;
  @JsonKey(name: 'streak_freezes')
  int get streakFreezes => throw _privateConstructorUsedError;
  @JsonKey(name: 'created_at')
  String? get createdAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'last_active_at')
  String? get lastActiveAt => throw _privateConstructorUsedError;

  /// Serializes this UserDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UserDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UserDtoCopyWith<UserDto> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UserDtoCopyWith<$Res> {
  factory $UserDtoCopyWith(UserDto value, $Res Function(UserDto) then) =
      _$UserDtoCopyWithImpl<$Res, UserDto>;
  @useResult
  $Res call(
      {String id,
      String email,
      @JsonKey(name: 'display_name') String displayName,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      String? username,
      String role,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'is_profile_public') bool isProfilePublic,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'streak_freezes') int streakFreezes,
      @JsonKey(name: 'created_at') String? createdAt,
      @JsonKey(name: 'last_active_at') String? lastActiveAt});
}

/// @nodoc
class _$UserDtoCopyWithImpl<$Res, $Val extends UserDto>
    implements $UserDtoCopyWith<$Res> {
  _$UserDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UserDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? email = null,
    Object? displayName = null,
    Object? avatarUrl = freezed,
    Object? username = freezed,
    Object? role = null,
    Object? totalXp = null,
    Object? isProfilePublic = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? streakFreezes = null,
    Object? createdAt = freezed,
    Object? lastActiveAt = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      displayName: null == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String,
      avatarUrl: freezed == avatarUrl
          ? _value.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      username: freezed == username
          ? _value.username
          : username // ignore: cast_nullable_to_non_nullable
              as String?,
      role: null == role
          ? _value.role
          : role // ignore: cast_nullable_to_non_nullable
              as String,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      isProfilePublic: null == isProfilePublic
          ? _value.isProfilePublic
          : isProfilePublic // ignore: cast_nullable_to_non_nullable
              as bool,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _value.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      streakFreezes: null == streakFreezes
          ? _value.streakFreezes
          : streakFreezes // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as String?,
      lastActiveAt: freezed == lastActiveAt
          ? _value.lastActiveAt
          : lastActiveAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UserDtoImplCopyWith<$Res> implements $UserDtoCopyWith<$Res> {
  factory _$$UserDtoImplCopyWith(
          _$UserDtoImpl value, $Res Function(_$UserDtoImpl) then) =
      __$$UserDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String email,
      @JsonKey(name: 'display_name') String displayName,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      String? username,
      String role,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'is_profile_public') bool isProfilePublic,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'streak_freezes') int streakFreezes,
      @JsonKey(name: 'created_at') String? createdAt,
      @JsonKey(name: 'last_active_at') String? lastActiveAt});
}

/// @nodoc
class __$$UserDtoImplCopyWithImpl<$Res>
    extends _$UserDtoCopyWithImpl<$Res, _$UserDtoImpl>
    implements _$$UserDtoImplCopyWith<$Res> {
  __$$UserDtoImplCopyWithImpl(
      _$UserDtoImpl _value, $Res Function(_$UserDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UserDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? email = null,
    Object? displayName = null,
    Object? avatarUrl = freezed,
    Object? username = freezed,
    Object? role = null,
    Object? totalXp = null,
    Object? isProfilePublic = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? streakFreezes = null,
    Object? createdAt = freezed,
    Object? lastActiveAt = freezed,
  }) {
    return _then(_$UserDtoImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      email: null == email
          ? _value.email
          : email // ignore: cast_nullable_to_non_nullable
              as String,
      displayName: null == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String,
      avatarUrl: freezed == avatarUrl
          ? _value.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      username: freezed == username
          ? _value.username
          : username // ignore: cast_nullable_to_non_nullable
              as String?,
      role: null == role
          ? _value.role
          : role // ignore: cast_nullable_to_non_nullable
              as String,
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      isProfilePublic: null == isProfilePublic
          ? _value.isProfilePublic
          : isProfilePublic // ignore: cast_nullable_to_non_nullable
              as bool,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _value.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      streakFreezes: null == streakFreezes
          ? _value.streakFreezes
          : streakFreezes // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: freezed == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as String?,
      lastActiveAt: freezed == lastActiveAt
          ? _value.lastActiveAt
          : lastActiveAt // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UserDtoImpl implements _UserDto {
  const _$UserDtoImpl(
      {required this.id,
      required this.email,
      @JsonKey(name: 'display_name') required this.displayName,
      @JsonKey(name: 'avatar_url') this.avatarUrl,
      this.username,
      required this.role,
      @JsonKey(name: 'total_xp') this.totalXp = 0,
      @JsonKey(name: 'is_profile_public') this.isProfilePublic = false,
      @JsonKey(name: 'current_streak') this.currentStreak = 0,
      @JsonKey(name: 'longest_streak') this.longestStreak = 0,
      @JsonKey(name: 'streak_freezes') this.streakFreezes = 0,
      @JsonKey(name: 'created_at') this.createdAt,
      @JsonKey(name: 'last_active_at') this.lastActiveAt});

  factory _$UserDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UserDtoImplFromJson(json);

  @override
  final String id;
  @override
  final String email;
  @override
  @JsonKey(name: 'display_name')
  final String displayName;
  @override
  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  @override
  final String? username;
  @override
  final String role;
  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  @override
  @JsonKey(name: 'is_profile_public')
  final bool isProfilePublic;
  @override
  @JsonKey(name: 'current_streak')
  final int currentStreak;
  @override
  @JsonKey(name: 'longest_streak')
  final int longestStreak;
  @override
  @JsonKey(name: 'streak_freezes')
  final int streakFreezes;
  @override
  @JsonKey(name: 'created_at')
  final String? createdAt;
  @override
  @JsonKey(name: 'last_active_at')
  final String? lastActiveAt;

  @override
  String toString() {
    return 'UserDto(id: $id, email: $email, displayName: $displayName, avatarUrl: $avatarUrl, username: $username, role: $role, totalXp: $totalXp, isProfilePublic: $isProfilePublic, currentStreak: $currentStreak, longestStreak: $longestStreak, streakFreezes: $streakFreezes, createdAt: $createdAt, lastActiveAt: $lastActiveAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UserDtoImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.displayName, displayName) ||
                other.displayName == displayName) &&
            (identical(other.avatarUrl, avatarUrl) ||
                other.avatarUrl == avatarUrl) &&
            (identical(other.username, username) ||
                other.username == username) &&
            (identical(other.role, role) || other.role == role) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.isProfilePublic, isProfilePublic) ||
                other.isProfilePublic == isProfilePublic) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak) &&
            (identical(other.longestStreak, longestStreak) ||
                other.longestStreak == longestStreak) &&
            (identical(other.streakFreezes, streakFreezes) ||
                other.streakFreezes == streakFreezes) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.lastActiveAt, lastActiveAt) ||
                other.lastActiveAt == lastActiveAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      email,
      displayName,
      avatarUrl,
      username,
      role,
      totalXp,
      isProfilePublic,
      currentStreak,
      longestStreak,
      streakFreezes,
      createdAt,
      lastActiveAt);

  /// Create a copy of UserDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UserDtoImplCopyWith<_$UserDtoImpl> get copyWith =>
      __$$UserDtoImplCopyWithImpl<_$UserDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UserDtoImplToJson(
      this,
    );
  }
}

abstract class _UserDto implements UserDto {
  const factory _UserDto(
          {required final String id,
          required final String email,
          @JsonKey(name: 'display_name') required final String displayName,
          @JsonKey(name: 'avatar_url') final String? avatarUrl,
          final String? username,
          required final String role,
          @JsonKey(name: 'total_xp') final int totalXp,
          @JsonKey(name: 'is_profile_public') final bool isProfilePublic,
          @JsonKey(name: 'current_streak') final int currentStreak,
          @JsonKey(name: 'longest_streak') final int longestStreak,
          @JsonKey(name: 'streak_freezes') final int streakFreezes,
          @JsonKey(name: 'created_at') final String? createdAt,
          @JsonKey(name: 'last_active_at') final String? lastActiveAt}) =
      _$UserDtoImpl;

  factory _UserDto.fromJson(Map<String, dynamic> json) = _$UserDtoImpl.fromJson;

  @override
  String get id;
  @override
  String get email;
  @override
  @JsonKey(name: 'display_name')
  String get displayName;
  @override
  @JsonKey(name: 'avatar_url')
  String? get avatarUrl;
  @override
  String? get username;
  @override
  String get role;
  @override
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @override
  @JsonKey(name: 'is_profile_public')
  bool get isProfilePublic;
  @override
  @JsonKey(name: 'current_streak')
  int get currentStreak;
  @override
  @JsonKey(name: 'longest_streak')
  int get longestStreak;
  @override
  @JsonKey(name: 'streak_freezes')
  int get streakFreezes;
  @override
  @JsonKey(name: 'created_at')
  String? get createdAt;
  @override
  @JsonKey(name: 'last_active_at')
  String? get lastActiveAt;

  /// Create a copy of UserDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UserDtoImplCopyWith<_$UserDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AuthResponseDto _$AuthResponseDtoFromJson(Map<String, dynamic> json) {
  return _AuthResponseDto.fromJson(json);
}

/// @nodoc
mixin _$AuthResponseDto {
  UserDto get user => throw _privateConstructorUsedError;
  StatsDto get stats => throw _privateConstructorUsedError;

  /// Serializes this AuthResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AuthResponseDtoCopyWith<AuthResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AuthResponseDtoCopyWith<$Res> {
  factory $AuthResponseDtoCopyWith(
          AuthResponseDto value, $Res Function(AuthResponseDto) then) =
      _$AuthResponseDtoCopyWithImpl<$Res, AuthResponseDto>;
  @useResult
  $Res call({UserDto user, StatsDto stats});

  $UserDtoCopyWith<$Res> get user;
  $StatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class _$AuthResponseDtoCopyWithImpl<$Res, $Val extends AuthResponseDto>
    implements $AuthResponseDtoCopyWith<$Res> {
  _$AuthResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? user = null,
    Object? stats = null,
  }) {
    return _then(_value.copyWith(
      user: null == user
          ? _value.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserDto,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as StatsDto,
    ) as $Val);
  }

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserDtoCopyWith<$Res> get user {
    return $UserDtoCopyWith<$Res>(_value.user, (value) {
      return _then(_value.copyWith(user: value) as $Val);
    });
  }

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $StatsDtoCopyWith<$Res> get stats {
    return $StatsDtoCopyWith<$Res>(_value.stats, (value) {
      return _then(_value.copyWith(stats: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AuthResponseDtoImplCopyWith<$Res>
    implements $AuthResponseDtoCopyWith<$Res> {
  factory _$$AuthResponseDtoImplCopyWith(_$AuthResponseDtoImpl value,
          $Res Function(_$AuthResponseDtoImpl) then) =
      __$$AuthResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({UserDto user, StatsDto stats});

  @override
  $UserDtoCopyWith<$Res> get user;
  @override
  $StatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class __$$AuthResponseDtoImplCopyWithImpl<$Res>
    extends _$AuthResponseDtoCopyWithImpl<$Res, _$AuthResponseDtoImpl>
    implements _$$AuthResponseDtoImplCopyWith<$Res> {
  __$$AuthResponseDtoImplCopyWithImpl(
      _$AuthResponseDtoImpl _value, $Res Function(_$AuthResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? user = null,
    Object? stats = null,
  }) {
    return _then(_$AuthResponseDtoImpl(
      user: null == user
          ? _value.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserDto,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as StatsDto,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AuthResponseDtoImpl implements _AuthResponseDto {
  const _$AuthResponseDtoImpl({required this.user, required this.stats});

  factory _$AuthResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$AuthResponseDtoImplFromJson(json);

  @override
  final UserDto user;
  @override
  final StatsDto stats;

  @override
  String toString() {
    return 'AuthResponseDto(user: $user, stats: $stats)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AuthResponseDtoImpl &&
            (identical(other.user, user) || other.user == user) &&
            (identical(other.stats, stats) || other.stats == stats));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, user, stats);

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AuthResponseDtoImplCopyWith<_$AuthResponseDtoImpl> get copyWith =>
      __$$AuthResponseDtoImplCopyWithImpl<_$AuthResponseDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AuthResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _AuthResponseDto implements AuthResponseDto {
  const factory _AuthResponseDto(
      {required final UserDto user,
      required final StatsDto stats}) = _$AuthResponseDtoImpl;

  factory _AuthResponseDto.fromJson(Map<String, dynamic> json) =
      _$AuthResponseDtoImpl.fromJson;

  @override
  UserDto get user;
  @override
  StatsDto get stats;

  /// Create a copy of AuthResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AuthResponseDtoImplCopyWith<_$AuthResponseDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StatsDto _$StatsDtoFromJson(Map<String, dynamic> json) {
  return _StatsDto.fromJson(json);
}

/// @nodoc
mixin _$StatsDto {
  @JsonKey(name: 'total_xp')
  int get totalXp => throw _privateConstructorUsedError;
  RankDto get rank => throw _privateConstructorUsedError;
  @JsonKey(name: 'xp_to_next_rank')
  int get xpToNextRank => throw _privateConstructorUsedError;
  @JsonKey(name: 'next_rank')
  RankDto? get nextRank => throw _privateConstructorUsedError;
  @JsonKey(name: 'motifs_discovered')
  int get motifsDiscovered => throw _privateConstructorUsedError;
  @JsonKey(name: 'motifs_learned')
  int get motifsLearned => throw _privateConstructorUsedError;
  @JsonKey(name: 'motifs_mastered')
  int get motifsMastered => throw _privateConstructorUsedError;
  @JsonKey(name: 'badges_earned')
  int get badgesEarned => throw _privateConstructorUsedError;
  @JsonKey(name: 'quizzes_completed')
  int get quizzesCompleted => throw _privateConstructorUsedError;
  @JsonKey(name: 'current_streak')
  int get currentStreak => throw _privateConstructorUsedError;

  /// Serializes this StatsDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $StatsDtoCopyWith<StatsDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StatsDtoCopyWith<$Res> {
  factory $StatsDtoCopyWith(StatsDto value, $Res Function(StatsDto) then) =
      _$StatsDtoCopyWithImpl<$Res, StatsDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'total_xp') int totalXp,
      RankDto rank,
      @JsonKey(name: 'xp_to_next_rank') int xpToNextRank,
      @JsonKey(name: 'next_rank') RankDto? nextRank,
      @JsonKey(name: 'motifs_discovered') int motifsDiscovered,
      @JsonKey(name: 'motifs_learned') int motifsLearned,
      @JsonKey(name: 'motifs_mastered') int motifsMastered,
      @JsonKey(name: 'badges_earned') int badgesEarned,
      @JsonKey(name: 'quizzes_completed') int quizzesCompleted,
      @JsonKey(name: 'current_streak') int currentStreak});

  $RankDtoCopyWith<$Res> get rank;
  $RankDtoCopyWith<$Res>? get nextRank;
}

/// @nodoc
class _$StatsDtoCopyWithImpl<$Res, $Val extends StatsDto>
    implements $StatsDtoCopyWith<$Res> {
  _$StatsDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalXp = null,
    Object? rank = null,
    Object? xpToNextRank = null,
    Object? nextRank = freezed,
    Object? motifsDiscovered = null,
    Object? motifsLearned = null,
    Object? motifsMastered = null,
    Object? badgesEarned = null,
    Object? quizzesCompleted = null,
    Object? currentStreak = null,
  }) {
    return _then(_value.copyWith(
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      rank: null == rank
          ? _value.rank
          : rank // ignore: cast_nullable_to_non_nullable
              as RankDto,
      xpToNextRank: null == xpToNextRank
          ? _value.xpToNextRank
          : xpToNextRank // ignore: cast_nullable_to_non_nullable
              as int,
      nextRank: freezed == nextRank
          ? _value.nextRank
          : nextRank // ignore: cast_nullable_to_non_nullable
              as RankDto?,
      motifsDiscovered: null == motifsDiscovered
          ? _value.motifsDiscovered
          : motifsDiscovered // ignore: cast_nullable_to_non_nullable
              as int,
      motifsLearned: null == motifsLearned
          ? _value.motifsLearned
          : motifsLearned // ignore: cast_nullable_to_non_nullable
              as int,
      motifsMastered: null == motifsMastered
          ? _value.motifsMastered
          : motifsMastered // ignore: cast_nullable_to_non_nullable
              as int,
      badgesEarned: null == badgesEarned
          ? _value.badgesEarned
          : badgesEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizzesCompleted: null == quizzesCompleted
          ? _value.quizzesCompleted
          : quizzesCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $RankDtoCopyWith<$Res> get rank {
    return $RankDtoCopyWith<$Res>(_value.rank, (value) {
      return _then(_value.copyWith(rank: value) as $Val);
    });
  }

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $RankDtoCopyWith<$Res>? get nextRank {
    if (_value.nextRank == null) {
      return null;
    }

    return $RankDtoCopyWith<$Res>(_value.nextRank!, (value) {
      return _then(_value.copyWith(nextRank: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$StatsDtoImplCopyWith<$Res>
    implements $StatsDtoCopyWith<$Res> {
  factory _$$StatsDtoImplCopyWith(
          _$StatsDtoImpl value, $Res Function(_$StatsDtoImpl) then) =
      __$$StatsDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'total_xp') int totalXp,
      RankDto rank,
      @JsonKey(name: 'xp_to_next_rank') int xpToNextRank,
      @JsonKey(name: 'next_rank') RankDto? nextRank,
      @JsonKey(name: 'motifs_discovered') int motifsDiscovered,
      @JsonKey(name: 'motifs_learned') int motifsLearned,
      @JsonKey(name: 'motifs_mastered') int motifsMastered,
      @JsonKey(name: 'badges_earned') int badgesEarned,
      @JsonKey(name: 'quizzes_completed') int quizzesCompleted,
      @JsonKey(name: 'current_streak') int currentStreak});

  @override
  $RankDtoCopyWith<$Res> get rank;
  @override
  $RankDtoCopyWith<$Res>? get nextRank;
}

/// @nodoc
class __$$StatsDtoImplCopyWithImpl<$Res>
    extends _$StatsDtoCopyWithImpl<$Res, _$StatsDtoImpl>
    implements _$$StatsDtoImplCopyWith<$Res> {
  __$$StatsDtoImplCopyWithImpl(
      _$StatsDtoImpl _value, $Res Function(_$StatsDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalXp = null,
    Object? rank = null,
    Object? xpToNextRank = null,
    Object? nextRank = freezed,
    Object? motifsDiscovered = null,
    Object? motifsLearned = null,
    Object? motifsMastered = null,
    Object? badgesEarned = null,
    Object? quizzesCompleted = null,
    Object? currentStreak = null,
  }) {
    return _then(_$StatsDtoImpl(
      totalXp: null == totalXp
          ? _value.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      rank: null == rank
          ? _value.rank
          : rank // ignore: cast_nullable_to_non_nullable
              as RankDto,
      xpToNextRank: null == xpToNextRank
          ? _value.xpToNextRank
          : xpToNextRank // ignore: cast_nullable_to_non_nullable
              as int,
      nextRank: freezed == nextRank
          ? _value.nextRank
          : nextRank // ignore: cast_nullable_to_non_nullable
              as RankDto?,
      motifsDiscovered: null == motifsDiscovered
          ? _value.motifsDiscovered
          : motifsDiscovered // ignore: cast_nullable_to_non_nullable
              as int,
      motifsLearned: null == motifsLearned
          ? _value.motifsLearned
          : motifsLearned // ignore: cast_nullable_to_non_nullable
              as int,
      motifsMastered: null == motifsMastered
          ? _value.motifsMastered
          : motifsMastered // ignore: cast_nullable_to_non_nullable
              as int,
      badgesEarned: null == badgesEarned
          ? _value.badgesEarned
          : badgesEarned // ignore: cast_nullable_to_non_nullable
              as int,
      quizzesCompleted: null == quizzesCompleted
          ? _value.quizzesCompleted
          : quizzesCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _value.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StatsDtoImpl implements _StatsDto {
  const _$StatsDtoImpl(
      {@JsonKey(name: 'total_xp') this.totalXp = 0,
      required this.rank,
      @JsonKey(name: 'xp_to_next_rank') this.xpToNextRank = 0,
      @JsonKey(name: 'next_rank') this.nextRank,
      @JsonKey(name: 'motifs_discovered') this.motifsDiscovered = 0,
      @JsonKey(name: 'motifs_learned') this.motifsLearned = 0,
      @JsonKey(name: 'motifs_mastered') this.motifsMastered = 0,
      @JsonKey(name: 'badges_earned') this.badgesEarned = 0,
      @JsonKey(name: 'quizzes_completed') this.quizzesCompleted = 0,
      @JsonKey(name: 'current_streak') this.currentStreak = 0});

  factory _$StatsDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$StatsDtoImplFromJson(json);

  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  @override
  final RankDto rank;
  @override
  @JsonKey(name: 'xp_to_next_rank')
  final int xpToNextRank;
  @override
  @JsonKey(name: 'next_rank')
  final RankDto? nextRank;
  @override
  @JsonKey(name: 'motifs_discovered')
  final int motifsDiscovered;
  @override
  @JsonKey(name: 'motifs_learned')
  final int motifsLearned;
  @override
  @JsonKey(name: 'motifs_mastered')
  final int motifsMastered;
  @override
  @JsonKey(name: 'badges_earned')
  final int badgesEarned;
  @override
  @JsonKey(name: 'quizzes_completed')
  final int quizzesCompleted;
  @override
  @JsonKey(name: 'current_streak')
  final int currentStreak;

  @override
  String toString() {
    return 'StatsDto(totalXp: $totalXp, rank: $rank, xpToNextRank: $xpToNextRank, nextRank: $nextRank, motifsDiscovered: $motifsDiscovered, motifsLearned: $motifsLearned, motifsMastered: $motifsMastered, badgesEarned: $badgesEarned, quizzesCompleted: $quizzesCompleted, currentStreak: $currentStreak)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StatsDtoImpl &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.rank, rank) || other.rank == rank) &&
            (identical(other.xpToNextRank, xpToNextRank) ||
                other.xpToNextRank == xpToNextRank) &&
            (identical(other.nextRank, nextRank) ||
                other.nextRank == nextRank) &&
            (identical(other.motifsDiscovered, motifsDiscovered) ||
                other.motifsDiscovered == motifsDiscovered) &&
            (identical(other.motifsLearned, motifsLearned) ||
                other.motifsLearned == motifsLearned) &&
            (identical(other.motifsMastered, motifsMastered) ||
                other.motifsMastered == motifsMastered) &&
            (identical(other.badgesEarned, badgesEarned) ||
                other.badgesEarned == badgesEarned) &&
            (identical(other.quizzesCompleted, quizzesCompleted) ||
                other.quizzesCompleted == quizzesCompleted) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalXp,
      rank,
      xpToNextRank,
      nextRank,
      motifsDiscovered,
      motifsLearned,
      motifsMastered,
      badgesEarned,
      quizzesCompleted,
      currentStreak);

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$StatsDtoImplCopyWith<_$StatsDtoImpl> get copyWith =>
      __$$StatsDtoImplCopyWithImpl<_$StatsDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StatsDtoImplToJson(
      this,
    );
  }
}

abstract class _StatsDto implements StatsDto {
  const factory _StatsDto(
          {@JsonKey(name: 'total_xp') final int totalXp,
          required final RankDto rank,
          @JsonKey(name: 'xp_to_next_rank') final int xpToNextRank,
          @JsonKey(name: 'next_rank') final RankDto? nextRank,
          @JsonKey(name: 'motifs_discovered') final int motifsDiscovered,
          @JsonKey(name: 'motifs_learned') final int motifsLearned,
          @JsonKey(name: 'motifs_mastered') final int motifsMastered,
          @JsonKey(name: 'badges_earned') final int badgesEarned,
          @JsonKey(name: 'quizzes_completed') final int quizzesCompleted,
          @JsonKey(name: 'current_streak') final int currentStreak}) =
      _$StatsDtoImpl;

  factory _StatsDto.fromJson(Map<String, dynamic> json) =
      _$StatsDtoImpl.fromJson;

  @override
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @override
  RankDto get rank;
  @override
  @JsonKey(name: 'xp_to_next_rank')
  int get xpToNextRank;
  @override
  @JsonKey(name: 'next_rank')
  RankDto? get nextRank;
  @override
  @JsonKey(name: 'motifs_discovered')
  int get motifsDiscovered;
  @override
  @JsonKey(name: 'motifs_learned')
  int get motifsLearned;
  @override
  @JsonKey(name: 'motifs_mastered')
  int get motifsMastered;
  @override
  @JsonKey(name: 'badges_earned')
  int get badgesEarned;
  @override
  @JsonKey(name: 'quizzes_completed')
  int get quizzesCompleted;
  @override
  @JsonKey(name: 'current_streak')
  int get currentStreak;

  /// Create a copy of StatsDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$StatsDtoImplCopyWith<_$StatsDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RankDto _$RankDtoFromJson(Map<String, dynamic> json) {
  return _RankDto.fromJson(json);
}

/// @nodoc
mixin _$RankDto {
  int get level => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  int get xp => throw _privateConstructorUsedError;

  /// Serializes this RankDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RankDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RankDtoCopyWith<RankDto> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RankDtoCopyWith<$Res> {
  factory $RankDtoCopyWith(RankDto value, $Res Function(RankDto) then) =
      _$RankDtoCopyWithImpl<$Res, RankDto>;
  @useResult
  $Res call({int level, String name, int xp});
}

/// @nodoc
class _$RankDtoCopyWithImpl<$Res, $Val extends RankDto>
    implements $RankDtoCopyWith<$Res> {
  _$RankDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RankDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? name = null,
    Object? xp = null,
  }) {
    return _then(_value.copyWith(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      xp: null == xp
          ? _value.xp
          : xp // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RankDtoImplCopyWith<$Res> implements $RankDtoCopyWith<$Res> {
  factory _$$RankDtoImplCopyWith(
          _$RankDtoImpl value, $Res Function(_$RankDtoImpl) then) =
      __$$RankDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int level, String name, int xp});
}

/// @nodoc
class __$$RankDtoImplCopyWithImpl<$Res>
    extends _$RankDtoCopyWithImpl<$Res, _$RankDtoImpl>
    implements _$$RankDtoImplCopyWith<$Res> {
  __$$RankDtoImplCopyWithImpl(
      _$RankDtoImpl _value, $Res Function(_$RankDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of RankDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? level = null,
    Object? name = null,
    Object? xp = null,
  }) {
    return _then(_$RankDtoImpl(
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as int,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      xp: null == xp
          ? _value.xp
          : xp // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RankDtoImpl implements _RankDto {
  const _$RankDtoImpl(
      {required this.level, required this.name, required this.xp});

  factory _$RankDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$RankDtoImplFromJson(json);

  @override
  final int level;
  @override
  final String name;
  @override
  final int xp;

  @override
  String toString() {
    return 'RankDto(level: $level, name: $name, xp: $xp)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RankDtoImpl &&
            (identical(other.level, level) || other.level == level) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.xp, xp) || other.xp == xp));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, level, name, xp);

  /// Create a copy of RankDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RankDtoImplCopyWith<_$RankDtoImpl> get copyWith =>
      __$$RankDtoImplCopyWithImpl<_$RankDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RankDtoImplToJson(
      this,
    );
  }
}

abstract class _RankDto implements RankDto {
  const factory _RankDto(
      {required final int level,
      required final String name,
      required final int xp}) = _$RankDtoImpl;

  factory _RankDto.fromJson(Map<String, dynamic> json) = _$RankDtoImpl.fromJson;

  @override
  int get level;
  @override
  String get name;
  @override
  int get xp;

  /// Create a copy of RankDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RankDtoImplCopyWith<_$RankDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

LoginResponseDto _$LoginResponseDtoFromJson(Map<String, dynamic> json) {
  return _LoginResponseDto.fromJson(json);
}

/// @nodoc
mixin _$LoginResponseDto {
  @JsonKey(name: 'access_token')
  String? get accessToken => throw _privateConstructorUsedError;
  @JsonKey(name: 'refresh_token')
  String? get refreshToken => throw _privateConstructorUsedError;
  @JsonKey(name: 'token_type')
  String get tokenType => throw _privateConstructorUsedError;
  UserDto get user => throw _privateConstructorUsedError;
  StatsDto get stats => throw _privateConstructorUsedError;

  /// Serializes this LoginResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LoginResponseDtoCopyWith<LoginResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LoginResponseDtoCopyWith<$Res> {
  factory $LoginResponseDtoCopyWith(
          LoginResponseDto value, $Res Function(LoginResponseDto) then) =
      _$LoginResponseDtoCopyWithImpl<$Res, LoginResponseDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'access_token') String? accessToken,
      @JsonKey(name: 'refresh_token') String? refreshToken,
      @JsonKey(name: 'token_type') String tokenType,
      UserDto user,
      StatsDto stats});

  $UserDtoCopyWith<$Res> get user;
  $StatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class _$LoginResponseDtoCopyWithImpl<$Res, $Val extends LoginResponseDto>
    implements $LoginResponseDtoCopyWith<$Res> {
  _$LoginResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? accessToken = freezed,
    Object? refreshToken = freezed,
    Object? tokenType = null,
    Object? user = null,
    Object? stats = null,
  }) {
    return _then(_value.copyWith(
      accessToken: freezed == accessToken
          ? _value.accessToken
          : accessToken // ignore: cast_nullable_to_non_nullable
              as String?,
      refreshToken: freezed == refreshToken
          ? _value.refreshToken
          : refreshToken // ignore: cast_nullable_to_non_nullable
              as String?,
      tokenType: null == tokenType
          ? _value.tokenType
          : tokenType // ignore: cast_nullable_to_non_nullable
              as String,
      user: null == user
          ? _value.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserDto,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as StatsDto,
    ) as $Val);
  }

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserDtoCopyWith<$Res> get user {
    return $UserDtoCopyWith<$Res>(_value.user, (value) {
      return _then(_value.copyWith(user: value) as $Val);
    });
  }

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $StatsDtoCopyWith<$Res> get stats {
    return $StatsDtoCopyWith<$Res>(_value.stats, (value) {
      return _then(_value.copyWith(stats: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$LoginResponseDtoImplCopyWith<$Res>
    implements $LoginResponseDtoCopyWith<$Res> {
  factory _$$LoginResponseDtoImplCopyWith(_$LoginResponseDtoImpl value,
          $Res Function(_$LoginResponseDtoImpl) then) =
      __$$LoginResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'access_token') String? accessToken,
      @JsonKey(name: 'refresh_token') String? refreshToken,
      @JsonKey(name: 'token_type') String tokenType,
      UserDto user,
      StatsDto stats});

  @override
  $UserDtoCopyWith<$Res> get user;
  @override
  $StatsDtoCopyWith<$Res> get stats;
}

/// @nodoc
class __$$LoginResponseDtoImplCopyWithImpl<$Res>
    extends _$LoginResponseDtoCopyWithImpl<$Res, _$LoginResponseDtoImpl>
    implements _$$LoginResponseDtoImplCopyWith<$Res> {
  __$$LoginResponseDtoImplCopyWithImpl(_$LoginResponseDtoImpl _value,
      $Res Function(_$LoginResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? accessToken = freezed,
    Object? refreshToken = freezed,
    Object? tokenType = null,
    Object? user = null,
    Object? stats = null,
  }) {
    return _then(_$LoginResponseDtoImpl(
      accessToken: freezed == accessToken
          ? _value.accessToken
          : accessToken // ignore: cast_nullable_to_non_nullable
              as String?,
      refreshToken: freezed == refreshToken
          ? _value.refreshToken
          : refreshToken // ignore: cast_nullable_to_non_nullable
              as String?,
      tokenType: null == tokenType
          ? _value.tokenType
          : tokenType // ignore: cast_nullable_to_non_nullable
              as String,
      user: null == user
          ? _value.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserDto,
      stats: null == stats
          ? _value.stats
          : stats // ignore: cast_nullable_to_non_nullable
              as StatsDto,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$LoginResponseDtoImpl implements _LoginResponseDto {
  const _$LoginResponseDtoImpl(
      {@JsonKey(name: 'access_token') this.accessToken,
      @JsonKey(name: 'refresh_token') this.refreshToken,
      @JsonKey(name: 'token_type') this.tokenType = 'bearer',
      required this.user,
      required this.stats});

  factory _$LoginResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$LoginResponseDtoImplFromJson(json);

  @override
  @JsonKey(name: 'access_token')
  final String? accessToken;
  @override
  @JsonKey(name: 'refresh_token')
  final String? refreshToken;
  @override
  @JsonKey(name: 'token_type')
  final String tokenType;
  @override
  final UserDto user;
  @override
  final StatsDto stats;

  @override
  String toString() {
    return 'LoginResponseDto(accessToken: $accessToken, refreshToken: $refreshToken, tokenType: $tokenType, user: $user, stats: $stats)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LoginResponseDtoImpl &&
            (identical(other.accessToken, accessToken) ||
                other.accessToken == accessToken) &&
            (identical(other.refreshToken, refreshToken) ||
                other.refreshToken == refreshToken) &&
            (identical(other.tokenType, tokenType) ||
                other.tokenType == tokenType) &&
            (identical(other.user, user) || other.user == user) &&
            (identical(other.stats, stats) || other.stats == stats));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, accessToken, refreshToken, tokenType, user, stats);

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LoginResponseDtoImplCopyWith<_$LoginResponseDtoImpl> get copyWith =>
      __$$LoginResponseDtoImplCopyWithImpl<_$LoginResponseDtoImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LoginResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _LoginResponseDto implements LoginResponseDto {
  const factory _LoginResponseDto(
      {@JsonKey(name: 'access_token') final String? accessToken,
      @JsonKey(name: 'refresh_token') final String? refreshToken,
      @JsonKey(name: 'token_type') final String tokenType,
      required final UserDto user,
      required final StatsDto stats}) = _$LoginResponseDtoImpl;

  factory _LoginResponseDto.fromJson(Map<String, dynamic> json) =
      _$LoginResponseDtoImpl.fromJson;

  @override
  @JsonKey(name: 'access_token')
  String? get accessToken;
  @override
  @JsonKey(name: 'refresh_token')
  String? get refreshToken;
  @override
  @JsonKey(name: 'token_type')
  String get tokenType;
  @override
  UserDto get user;
  @override
  StatsDto get stats;

  /// Create a copy of LoginResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LoginResponseDtoImplCopyWith<_$LoginResponseDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RefreshTokenResponseDto _$RefreshTokenResponseDtoFromJson(
    Map<String, dynamic> json) {
  return _RefreshTokenResponseDto.fromJson(json);
}

/// @nodoc
mixin _$RefreshTokenResponseDto {
  @JsonKey(name: 'access_token')
  String? get accessToken => throw _privateConstructorUsedError;
  @JsonKey(name: 'refresh_token')
  String? get refreshToken => throw _privateConstructorUsedError;
  @JsonKey(name: 'token_type')
  String get tokenType => throw _privateConstructorUsedError;

  /// Serializes this RefreshTokenResponseDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RefreshTokenResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RefreshTokenResponseDtoCopyWith<RefreshTokenResponseDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RefreshTokenResponseDtoCopyWith<$Res> {
  factory $RefreshTokenResponseDtoCopyWith(RefreshTokenResponseDto value,
          $Res Function(RefreshTokenResponseDto) then) =
      _$RefreshTokenResponseDtoCopyWithImpl<$Res, RefreshTokenResponseDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'access_token') String? accessToken,
      @JsonKey(name: 'refresh_token') String? refreshToken,
      @JsonKey(name: 'token_type') String tokenType});
}

/// @nodoc
class _$RefreshTokenResponseDtoCopyWithImpl<$Res,
        $Val extends RefreshTokenResponseDto>
    implements $RefreshTokenResponseDtoCopyWith<$Res> {
  _$RefreshTokenResponseDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RefreshTokenResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? accessToken = freezed,
    Object? refreshToken = freezed,
    Object? tokenType = null,
  }) {
    return _then(_value.copyWith(
      accessToken: freezed == accessToken
          ? _value.accessToken
          : accessToken // ignore: cast_nullable_to_non_nullable
              as String?,
      refreshToken: freezed == refreshToken
          ? _value.refreshToken
          : refreshToken // ignore: cast_nullable_to_non_nullable
              as String?,
      tokenType: null == tokenType
          ? _value.tokenType
          : tokenType // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RefreshTokenResponseDtoImplCopyWith<$Res>
    implements $RefreshTokenResponseDtoCopyWith<$Res> {
  factory _$$RefreshTokenResponseDtoImplCopyWith(
          _$RefreshTokenResponseDtoImpl value,
          $Res Function(_$RefreshTokenResponseDtoImpl) then) =
      __$$RefreshTokenResponseDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'access_token') String? accessToken,
      @JsonKey(name: 'refresh_token') String? refreshToken,
      @JsonKey(name: 'token_type') String tokenType});
}

/// @nodoc
class __$$RefreshTokenResponseDtoImplCopyWithImpl<$Res>
    extends _$RefreshTokenResponseDtoCopyWithImpl<$Res,
        _$RefreshTokenResponseDtoImpl>
    implements _$$RefreshTokenResponseDtoImplCopyWith<$Res> {
  __$$RefreshTokenResponseDtoImplCopyWithImpl(
      _$RefreshTokenResponseDtoImpl _value,
      $Res Function(_$RefreshTokenResponseDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of RefreshTokenResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? accessToken = freezed,
    Object? refreshToken = freezed,
    Object? tokenType = null,
  }) {
    return _then(_$RefreshTokenResponseDtoImpl(
      accessToken: freezed == accessToken
          ? _value.accessToken
          : accessToken // ignore: cast_nullable_to_non_nullable
              as String?,
      refreshToken: freezed == refreshToken
          ? _value.refreshToken
          : refreshToken // ignore: cast_nullable_to_non_nullable
              as String?,
      tokenType: null == tokenType
          ? _value.tokenType
          : tokenType // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RefreshTokenResponseDtoImpl implements _RefreshTokenResponseDto {
  const _$RefreshTokenResponseDtoImpl(
      {@JsonKey(name: 'access_token') this.accessToken,
      @JsonKey(name: 'refresh_token') this.refreshToken,
      @JsonKey(name: 'token_type') this.tokenType = 'bearer'});

  factory _$RefreshTokenResponseDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$RefreshTokenResponseDtoImplFromJson(json);

  @override
  @JsonKey(name: 'access_token')
  final String? accessToken;
  @override
  @JsonKey(name: 'refresh_token')
  final String? refreshToken;
  @override
  @JsonKey(name: 'token_type')
  final String tokenType;

  @override
  String toString() {
    return 'RefreshTokenResponseDto(accessToken: $accessToken, refreshToken: $refreshToken, tokenType: $tokenType)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RefreshTokenResponseDtoImpl &&
            (identical(other.accessToken, accessToken) ||
                other.accessToken == accessToken) &&
            (identical(other.refreshToken, refreshToken) ||
                other.refreshToken == refreshToken) &&
            (identical(other.tokenType, tokenType) ||
                other.tokenType == tokenType));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, accessToken, refreshToken, tokenType);

  /// Create a copy of RefreshTokenResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RefreshTokenResponseDtoImplCopyWith<_$RefreshTokenResponseDtoImpl>
      get copyWith => __$$RefreshTokenResponseDtoImplCopyWithImpl<
          _$RefreshTokenResponseDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RefreshTokenResponseDtoImplToJson(
      this,
    );
  }
}

abstract class _RefreshTokenResponseDto implements RefreshTokenResponseDto {
  const factory _RefreshTokenResponseDto(
          {@JsonKey(name: 'access_token') final String? accessToken,
          @JsonKey(name: 'refresh_token') final String? refreshToken,
          @JsonKey(name: 'token_type') final String tokenType}) =
      _$RefreshTokenResponseDtoImpl;

  factory _RefreshTokenResponseDto.fromJson(Map<String, dynamic> json) =
      _$RefreshTokenResponseDtoImpl.fromJson;

  @override
  @JsonKey(name: 'access_token')
  String? get accessToken;
  @override
  @JsonKey(name: 'refresh_token')
  String? get refreshToken;
  @override
  @JsonKey(name: 'token_type')
  String get tokenType;

  /// Create a copy of RefreshTokenResponseDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RefreshTokenResponseDtoImplCopyWith<_$RefreshTokenResponseDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

UpdateProfileRequestDto _$UpdateProfileRequestDtoFromJson(
    Map<String, dynamic> json) {
  return _UpdateProfileRequestDto.fromJson(json);
}

/// @nodoc
mixin _$UpdateProfileRequestDto {
  @JsonKey(name: 'display_name')
  String? get displayName => throw _privateConstructorUsedError;
  String? get username => throw _privateConstructorUsedError;
  @JsonKey(name: 'avatar_url')
  String? get avatarUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_profile_public')
  bool? get isProfilePublic => throw _privateConstructorUsedError;

  /// Serializes this UpdateProfileRequestDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of UpdateProfileRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $UpdateProfileRequestDtoCopyWith<UpdateProfileRequestDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UpdateProfileRequestDtoCopyWith<$Res> {
  factory $UpdateProfileRequestDtoCopyWith(UpdateProfileRequestDto value,
          $Res Function(UpdateProfileRequestDto) then) =
      _$UpdateProfileRequestDtoCopyWithImpl<$Res, UpdateProfileRequestDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'display_name') String? displayName,
      String? username,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      @JsonKey(name: 'is_profile_public') bool? isProfilePublic});
}

/// @nodoc
class _$UpdateProfileRequestDtoCopyWithImpl<$Res,
        $Val extends UpdateProfileRequestDto>
    implements $UpdateProfileRequestDtoCopyWith<$Res> {
  _$UpdateProfileRequestDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of UpdateProfileRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? displayName = freezed,
    Object? username = freezed,
    Object? avatarUrl = freezed,
    Object? isProfilePublic = freezed,
  }) {
    return _then(_value.copyWith(
      displayName: freezed == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String?,
      username: freezed == username
          ? _value.username
          : username // ignore: cast_nullable_to_non_nullable
              as String?,
      avatarUrl: freezed == avatarUrl
          ? _value.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isProfilePublic: freezed == isProfilePublic
          ? _value.isProfilePublic
          : isProfilePublic // ignore: cast_nullable_to_non_nullable
              as bool?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UpdateProfileRequestDtoImplCopyWith<$Res>
    implements $UpdateProfileRequestDtoCopyWith<$Res> {
  factory _$$UpdateProfileRequestDtoImplCopyWith(
          _$UpdateProfileRequestDtoImpl value,
          $Res Function(_$UpdateProfileRequestDtoImpl) then) =
      __$$UpdateProfileRequestDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'display_name') String? displayName,
      String? username,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      @JsonKey(name: 'is_profile_public') bool? isProfilePublic});
}

/// @nodoc
class __$$UpdateProfileRequestDtoImplCopyWithImpl<$Res>
    extends _$UpdateProfileRequestDtoCopyWithImpl<$Res,
        _$UpdateProfileRequestDtoImpl>
    implements _$$UpdateProfileRequestDtoImplCopyWith<$Res> {
  __$$UpdateProfileRequestDtoImplCopyWithImpl(
      _$UpdateProfileRequestDtoImpl _value,
      $Res Function(_$UpdateProfileRequestDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of UpdateProfileRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? displayName = freezed,
    Object? username = freezed,
    Object? avatarUrl = freezed,
    Object? isProfilePublic = freezed,
  }) {
    return _then(_$UpdateProfileRequestDtoImpl(
      displayName: freezed == displayName
          ? _value.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String?,
      username: freezed == username
          ? _value.username
          : username // ignore: cast_nullable_to_non_nullable
              as String?,
      avatarUrl: freezed == avatarUrl
          ? _value.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      isProfilePublic: freezed == isProfilePublic
          ? _value.isProfilePublic
          : isProfilePublic // ignore: cast_nullable_to_non_nullable
              as bool?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UpdateProfileRequestDtoImpl implements _UpdateProfileRequestDto {
  const _$UpdateProfileRequestDtoImpl(
      {@JsonKey(name: 'display_name') this.displayName,
      this.username,
      @JsonKey(name: 'avatar_url') this.avatarUrl,
      @JsonKey(name: 'is_profile_public') this.isProfilePublic});

  factory _$UpdateProfileRequestDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$UpdateProfileRequestDtoImplFromJson(json);

  @override
  @JsonKey(name: 'display_name')
  final String? displayName;
  @override
  final String? username;
  @override
  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  @override
  @JsonKey(name: 'is_profile_public')
  final bool? isProfilePublic;

  @override
  String toString() {
    return 'UpdateProfileRequestDto(displayName: $displayName, username: $username, avatarUrl: $avatarUrl, isProfilePublic: $isProfilePublic)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UpdateProfileRequestDtoImpl &&
            (identical(other.displayName, displayName) ||
                other.displayName == displayName) &&
            (identical(other.username, username) ||
                other.username == username) &&
            (identical(other.avatarUrl, avatarUrl) ||
                other.avatarUrl == avatarUrl) &&
            (identical(other.isProfilePublic, isProfilePublic) ||
                other.isProfilePublic == isProfilePublic));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, displayName, username, avatarUrl, isProfilePublic);

  /// Create a copy of UpdateProfileRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$UpdateProfileRequestDtoImplCopyWith<_$UpdateProfileRequestDtoImpl>
      get copyWith => __$$UpdateProfileRequestDtoImplCopyWithImpl<
          _$UpdateProfileRequestDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UpdateProfileRequestDtoImplToJson(
      this,
    );
  }
}

abstract class _UpdateProfileRequestDto implements UpdateProfileRequestDto {
  const factory _UpdateProfileRequestDto(
          {@JsonKey(name: 'display_name') final String? displayName,
          final String? username,
          @JsonKey(name: 'avatar_url') final String? avatarUrl,
          @JsonKey(name: 'is_profile_public') final bool? isProfilePublic}) =
      _$UpdateProfileRequestDtoImpl;

  factory _UpdateProfileRequestDto.fromJson(Map<String, dynamic> json) =
      _$UpdateProfileRequestDtoImpl.fromJson;

  @override
  @JsonKey(name: 'display_name')
  String? get displayName;
  @override
  String? get username;
  @override
  @JsonKey(name: 'avatar_url')
  String? get avatarUrl;
  @override
  @JsonKey(name: 'is_profile_public')
  bool? get isProfilePublic;

  /// Create a copy of UpdateProfileRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$UpdateProfileRequestDtoImplCopyWith<_$UpdateProfileRequestDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ChangePasswordRequestDto _$ChangePasswordRequestDtoFromJson(
    Map<String, dynamic> json) {
  return _ChangePasswordRequestDto.fromJson(json);
}

/// @nodoc
mixin _$ChangePasswordRequestDto {
  @JsonKey(name: 'current_password')
  String get currentPassword => throw _privateConstructorUsedError;
  @JsonKey(name: 'new_password')
  String get newPassword => throw _privateConstructorUsedError;

  /// Serializes this ChangePasswordRequestDto to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChangePasswordRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChangePasswordRequestDtoCopyWith<ChangePasswordRequestDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChangePasswordRequestDtoCopyWith<$Res> {
  factory $ChangePasswordRequestDtoCopyWith(ChangePasswordRequestDto value,
          $Res Function(ChangePasswordRequestDto) then) =
      _$ChangePasswordRequestDtoCopyWithImpl<$Res, ChangePasswordRequestDto>;
  @useResult
  $Res call(
      {@JsonKey(name: 'current_password') String currentPassword,
      @JsonKey(name: 'new_password') String newPassword});
}

/// @nodoc
class _$ChangePasswordRequestDtoCopyWithImpl<$Res,
        $Val extends ChangePasswordRequestDto>
    implements $ChangePasswordRequestDtoCopyWith<$Res> {
  _$ChangePasswordRequestDtoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChangePasswordRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentPassword = null,
    Object? newPassword = null,
  }) {
    return _then(_value.copyWith(
      currentPassword: null == currentPassword
          ? _value.currentPassword
          : currentPassword // ignore: cast_nullable_to_non_nullable
              as String,
      newPassword: null == newPassword
          ? _value.newPassword
          : newPassword // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChangePasswordRequestDtoImplCopyWith<$Res>
    implements $ChangePasswordRequestDtoCopyWith<$Res> {
  factory _$$ChangePasswordRequestDtoImplCopyWith(
          _$ChangePasswordRequestDtoImpl value,
          $Res Function(_$ChangePasswordRequestDtoImpl) then) =
      __$$ChangePasswordRequestDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'current_password') String currentPassword,
      @JsonKey(name: 'new_password') String newPassword});
}

/// @nodoc
class __$$ChangePasswordRequestDtoImplCopyWithImpl<$Res>
    extends _$ChangePasswordRequestDtoCopyWithImpl<$Res,
        _$ChangePasswordRequestDtoImpl>
    implements _$$ChangePasswordRequestDtoImplCopyWith<$Res> {
  __$$ChangePasswordRequestDtoImplCopyWithImpl(
      _$ChangePasswordRequestDtoImpl _value,
      $Res Function(_$ChangePasswordRequestDtoImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChangePasswordRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentPassword = null,
    Object? newPassword = null,
  }) {
    return _then(_$ChangePasswordRequestDtoImpl(
      currentPassword: null == currentPassword
          ? _value.currentPassword
          : currentPassword // ignore: cast_nullable_to_non_nullable
              as String,
      newPassword: null == newPassword
          ? _value.newPassword
          : newPassword // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChangePasswordRequestDtoImpl implements _ChangePasswordRequestDto {
  const _$ChangePasswordRequestDtoImpl(
      {@JsonKey(name: 'current_password') required this.currentPassword,
      @JsonKey(name: 'new_password') required this.newPassword});

  factory _$ChangePasswordRequestDtoImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChangePasswordRequestDtoImplFromJson(json);

  @override
  @JsonKey(name: 'current_password')
  final String currentPassword;
  @override
  @JsonKey(name: 'new_password')
  final String newPassword;

  @override
  String toString() {
    return 'ChangePasswordRequestDto(currentPassword: $currentPassword, newPassword: $newPassword)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChangePasswordRequestDtoImpl &&
            (identical(other.currentPassword, currentPassword) ||
                other.currentPassword == currentPassword) &&
            (identical(other.newPassword, newPassword) ||
                other.newPassword == newPassword));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, currentPassword, newPassword);

  /// Create a copy of ChangePasswordRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChangePasswordRequestDtoImplCopyWith<_$ChangePasswordRequestDtoImpl>
      get copyWith => __$$ChangePasswordRequestDtoImplCopyWithImpl<
          _$ChangePasswordRequestDtoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChangePasswordRequestDtoImplToJson(
      this,
    );
  }
}

abstract class _ChangePasswordRequestDto implements ChangePasswordRequestDto {
  const factory _ChangePasswordRequestDto(
      {@JsonKey(name: 'current_password') required final String currentPassword,
      @JsonKey(name: 'new_password')
      required final String newPassword}) = _$ChangePasswordRequestDtoImpl;

  factory _ChangePasswordRequestDto.fromJson(Map<String, dynamic> json) =
      _$ChangePasswordRequestDtoImpl.fromJson;

  @override
  @JsonKey(name: 'current_password')
  String get currentPassword;
  @override
  @JsonKey(name: 'new_password')
  String get newPassword;

  /// Create a copy of ChangePasswordRequestDto
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChangePasswordRequestDtoImplCopyWith<_$ChangePasswordRequestDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}
