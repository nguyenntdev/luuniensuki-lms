// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'heart_state.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

HeartState _$HeartStateFromJson(Map<String, dynamic> json) {
  return _HeartState.fromJson(json);
}

/// @nodoc
mixin _$HeartState {
  /// Maximum number of hearts a user can have
  int get maxHearts => throw _privateConstructorUsedError;

  /// Current number of hearts
  int get currentHearts => throw _privateConstructorUsedError;

  /// Last time hearts were refilled (either auto or manual)
  DateTime get lastRefillTime => throw _privateConstructorUsedError;

  /// Refill interval in minutes (1 heart per 30 minutes)
  int get refillIntervalMinutes => throw _privateConstructorUsedError;

  /// Whether hearts are unlimited (e.g., premium feature)
  bool get isUnlimited => throw _privateConstructorUsedError;

  /// Serializes this HeartState to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of HeartState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $HeartStateCopyWith<HeartState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HeartStateCopyWith<$Res> {
  factory $HeartStateCopyWith(
          HeartState value, $Res Function(HeartState) then) =
      _$HeartStateCopyWithImpl<$Res, HeartState>;
  @useResult
  $Res call(
      {int maxHearts,
      int currentHearts,
      DateTime lastRefillTime,
      int refillIntervalMinutes,
      bool isUnlimited});
}

/// @nodoc
class _$HeartStateCopyWithImpl<$Res, $Val extends HeartState>
    implements $HeartStateCopyWith<$Res> {
  _$HeartStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of HeartState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? maxHearts = null,
    Object? currentHearts = null,
    Object? lastRefillTime = null,
    Object? refillIntervalMinutes = null,
    Object? isUnlimited = null,
  }) {
    return _then(_value.copyWith(
      maxHearts: null == maxHearts
          ? _value.maxHearts
          : maxHearts // ignore: cast_nullable_to_non_nullable
              as int,
      currentHearts: null == currentHearts
          ? _value.currentHearts
          : currentHearts // ignore: cast_nullable_to_non_nullable
              as int,
      lastRefillTime: null == lastRefillTime
          ? _value.lastRefillTime
          : lastRefillTime // ignore: cast_nullable_to_non_nullable
              as DateTime,
      refillIntervalMinutes: null == refillIntervalMinutes
          ? _value.refillIntervalMinutes
          : refillIntervalMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isUnlimited: null == isUnlimited
          ? _value.isUnlimited
          : isUnlimited // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HeartStateImplCopyWith<$Res>
    implements $HeartStateCopyWith<$Res> {
  factory _$$HeartStateImplCopyWith(
          _$HeartStateImpl value, $Res Function(_$HeartStateImpl) then) =
      __$$HeartStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int maxHearts,
      int currentHearts,
      DateTime lastRefillTime,
      int refillIntervalMinutes,
      bool isUnlimited});
}

/// @nodoc
class __$$HeartStateImplCopyWithImpl<$Res>
    extends _$HeartStateCopyWithImpl<$Res, _$HeartStateImpl>
    implements _$$HeartStateImplCopyWith<$Res> {
  __$$HeartStateImplCopyWithImpl(
      _$HeartStateImpl _value, $Res Function(_$HeartStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of HeartState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? maxHearts = null,
    Object? currentHearts = null,
    Object? lastRefillTime = null,
    Object? refillIntervalMinutes = null,
    Object? isUnlimited = null,
  }) {
    return _then(_$HeartStateImpl(
      maxHearts: null == maxHearts
          ? _value.maxHearts
          : maxHearts // ignore: cast_nullable_to_non_nullable
              as int,
      currentHearts: null == currentHearts
          ? _value.currentHearts
          : currentHearts // ignore: cast_nullable_to_non_nullable
              as int,
      lastRefillTime: null == lastRefillTime
          ? _value.lastRefillTime
          : lastRefillTime // ignore: cast_nullable_to_non_nullable
              as DateTime,
      refillIntervalMinutes: null == refillIntervalMinutes
          ? _value.refillIntervalMinutes
          : refillIntervalMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isUnlimited: null == isUnlimited
          ? _value.isUnlimited
          : isUnlimited // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$HeartStateImpl extends _HeartState {
  const _$HeartStateImpl(
      {this.maxHearts = 5,
      this.currentHearts = 5,
      required this.lastRefillTime,
      this.refillIntervalMinutes = 30,
      this.isUnlimited = false})
      : super._();

  factory _$HeartStateImpl.fromJson(Map<String, dynamic> json) =>
      _$$HeartStateImplFromJson(json);

  /// Maximum number of hearts a user can have
  @override
  @JsonKey()
  final int maxHearts;

  /// Current number of hearts
  @override
  @JsonKey()
  final int currentHearts;

  /// Last time hearts were refilled (either auto or manual)
  @override
  final DateTime lastRefillTime;

  /// Refill interval in minutes (1 heart per 30 minutes)
  @override
  @JsonKey()
  final int refillIntervalMinutes;

  /// Whether hearts are unlimited (e.g., premium feature)
  @override
  @JsonKey()
  final bool isUnlimited;

  @override
  String toString() {
    return 'HeartState(maxHearts: $maxHearts, currentHearts: $currentHearts, lastRefillTime: $lastRefillTime, refillIntervalMinutes: $refillIntervalMinutes, isUnlimited: $isUnlimited)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HeartStateImpl &&
            (identical(other.maxHearts, maxHearts) ||
                other.maxHearts == maxHearts) &&
            (identical(other.currentHearts, currentHearts) ||
                other.currentHearts == currentHearts) &&
            (identical(other.lastRefillTime, lastRefillTime) ||
                other.lastRefillTime == lastRefillTime) &&
            (identical(other.refillIntervalMinutes, refillIntervalMinutes) ||
                other.refillIntervalMinutes == refillIntervalMinutes) &&
            (identical(other.isUnlimited, isUnlimited) ||
                other.isUnlimited == isUnlimited));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, maxHearts, currentHearts,
      lastRefillTime, refillIntervalMinutes, isUnlimited);

  /// Create a copy of HeartState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$HeartStateImplCopyWith<_$HeartStateImpl> get copyWith =>
      __$$HeartStateImplCopyWithImpl<_$HeartStateImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$HeartStateImplToJson(
      this,
    );
  }
}

abstract class _HeartState extends HeartState {
  const factory _HeartState(
      {final int maxHearts,
      final int currentHearts,
      required final DateTime lastRefillTime,
      final int refillIntervalMinutes,
      final bool isUnlimited}) = _$HeartStateImpl;
  const _HeartState._() : super._();

  factory _HeartState.fromJson(Map<String, dynamic> json) =
      _$HeartStateImpl.fromJson;

  /// Maximum number of hearts a user can have
  @override
  int get maxHearts;

  /// Current number of hearts
  @override
  int get currentHearts;

  /// Last time hearts were refilled (either auto or manual)
  @override
  DateTime get lastRefillTime;

  /// Refill interval in minutes (1 heart per 30 minutes)
  @override
  int get refillIntervalMinutes;

  /// Whether hearts are unlimited (e.g., premium feature)
  @override
  bool get isUnlimited;

  /// Create a copy of HeartState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$HeartStateImplCopyWith<_$HeartStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
