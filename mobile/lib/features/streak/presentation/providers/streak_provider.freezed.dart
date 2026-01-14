// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'streak_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$StreakState {
  StreakData get data => throw _privateConstructorUsedError;
  StreakFreeze get freeze => throw _privateConstructorUsedError;
  bool get isLoading => throw _privateConstructorUsedError;
  bool get isRefreshing => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;
  StreakMilestone? get justReachedMilestone =>
      throw _privateConstructorUsedError;

  /// Create a copy of StreakState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $StreakStateCopyWith<StreakState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StreakStateCopyWith<$Res> {
  factory $StreakStateCopyWith(
          StreakState value, $Res Function(StreakState) then) =
      _$StreakStateCopyWithImpl<$Res, StreakState>;
  @useResult
  $Res call(
      {StreakData data,
      StreakFreeze freeze,
      bool isLoading,
      bool isRefreshing,
      String? error,
      StreakMilestone? justReachedMilestone});
}

/// @nodoc
class _$StreakStateCopyWithImpl<$Res, $Val extends StreakState>
    implements $StreakStateCopyWith<$Res> {
  _$StreakStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of StreakState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? data = null,
    Object? freeze = null,
    Object? isLoading = null,
    Object? isRefreshing = null,
    Object? error = freezed,
    Object? justReachedMilestone = freezed,
  }) {
    return _then(_value.copyWith(
      data: null == data
          ? _value.data
          : data // ignore: cast_nullable_to_non_nullable
              as StreakData,
      freeze: null == freeze
          ? _value.freeze
          : freeze // ignore: cast_nullable_to_non_nullable
              as StreakFreeze,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isRefreshing: null == isRefreshing
          ? _value.isRefreshing
          : isRefreshing // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      justReachedMilestone: freezed == justReachedMilestone
          ? _value.justReachedMilestone
          : justReachedMilestone // ignore: cast_nullable_to_non_nullable
              as StreakMilestone?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$StreakStateImplCopyWith<$Res>
    implements $StreakStateCopyWith<$Res> {
  factory _$$StreakStateImplCopyWith(
          _$StreakStateImpl value, $Res Function(_$StreakStateImpl) then) =
      __$$StreakStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {StreakData data,
      StreakFreeze freeze,
      bool isLoading,
      bool isRefreshing,
      String? error,
      StreakMilestone? justReachedMilestone});
}

/// @nodoc
class __$$StreakStateImplCopyWithImpl<$Res>
    extends _$StreakStateCopyWithImpl<$Res, _$StreakStateImpl>
    implements _$$StreakStateImplCopyWith<$Res> {
  __$$StreakStateImplCopyWithImpl(
      _$StreakStateImpl _value, $Res Function(_$StreakStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of StreakState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? data = null,
    Object? freeze = null,
    Object? isLoading = null,
    Object? isRefreshing = null,
    Object? error = freezed,
    Object? justReachedMilestone = freezed,
  }) {
    return _then(_$StreakStateImpl(
      data: null == data
          ? _value.data
          : data // ignore: cast_nullable_to_non_nullable
              as StreakData,
      freeze: null == freeze
          ? _value.freeze
          : freeze // ignore: cast_nullable_to_non_nullable
              as StreakFreeze,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isRefreshing: null == isRefreshing
          ? _value.isRefreshing
          : isRefreshing // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      justReachedMilestone: freezed == justReachedMilestone
          ? _value.justReachedMilestone
          : justReachedMilestone // ignore: cast_nullable_to_non_nullable
              as StreakMilestone?,
    ));
  }
}

/// @nodoc

class _$StreakStateImpl implements _StreakState {
  const _$StreakStateImpl(
      {this.data = const StreakData.initial(),
      this.freeze = const StreakFreeze.initial(),
      this.isLoading = false,
      this.isRefreshing = false,
      this.error,
      this.justReachedMilestone});

  @override
  @JsonKey()
  final StreakData data;
  @override
  @JsonKey()
  final StreakFreeze freeze;
  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool isRefreshing;
  @override
  final String? error;
  @override
  final StreakMilestone? justReachedMilestone;

  @override
  String toString() {
    return 'StreakState(data: $data, freeze: $freeze, isLoading: $isLoading, isRefreshing: $isRefreshing, error: $error, justReachedMilestone: $justReachedMilestone)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StreakStateImpl &&
            (identical(other.data, data) || other.data == data) &&
            (identical(other.freeze, freeze) || other.freeze == freeze) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.isRefreshing, isRefreshing) ||
                other.isRefreshing == isRefreshing) &&
            (identical(other.error, error) || other.error == error) &&
            (identical(other.justReachedMilestone, justReachedMilestone) ||
                other.justReachedMilestone == justReachedMilestone));
  }

  @override
  int get hashCode => Object.hash(runtimeType, data, freeze, isLoading,
      isRefreshing, error, justReachedMilestone);

  /// Create a copy of StreakState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$StreakStateImplCopyWith<_$StreakStateImpl> get copyWith =>
      __$$StreakStateImplCopyWithImpl<_$StreakStateImpl>(this, _$identity);
}

abstract class _StreakState implements StreakState {
  const factory _StreakState(
      {final StreakData data,
      final StreakFreeze freeze,
      final bool isLoading,
      final bool isRefreshing,
      final String? error,
      final StreakMilestone? justReachedMilestone}) = _$StreakStateImpl;

  @override
  StreakData get data;
  @override
  StreakFreeze get freeze;
  @override
  bool get isLoading;
  @override
  bool get isRefreshing;
  @override
  String? get error;
  @override
  StreakMilestone? get justReachedMilestone;

  /// Create a copy of StreakState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$StreakStateImplCopyWith<_$StreakStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
