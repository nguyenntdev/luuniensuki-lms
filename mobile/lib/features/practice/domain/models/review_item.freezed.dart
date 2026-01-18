// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'review_item.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ReviewItem _$ReviewItemFromJson(Map<String, dynamic> json) {
  return _ReviewItem.fromJson(json);
}

/// @nodoc
mixin _$ReviewItem {
  /// Unique identifier of the motif being reviewed
  String get motifId => throw _privateConstructorUsedError;

  /// Ease Factor (EF) - Determines how quickly intervals increase
  /// Default: 2.5, Range: 1.3 to 2.5+
  /// Higher = easier item, intervals grow faster
  double get easeFactor => throw _privateConstructorUsedError;

  /// Current interval in days until next review
  /// Grows based on performance (SM-2 algorithm)
  int get interval => throw _privateConstructorUsedError;

  /// Number of consecutive successful reviews (quality >= 3)
  /// Resets to 0 when quality < 3
  int get repetitions => throw _privateConstructorUsedError;

  /// Next scheduled review date
  DateTime get nextReviewDate => throw _privateConstructorUsedError;

  /// Last review date (null if never reviewed)
  DateTime? get lastReviewDate => throw _privateConstructorUsedError;

  /// History of quality ratings (0-5) for analytics
  /// 5: Perfect, 4: Correct with hesitation, 3: Correct with difficulty
  /// 2: Incorrect but easy recall, 1: Incorrect hard recall, 0: Complete blackout
  List<int> get qualityHistory => throw _privateConstructorUsedError;

  /// Optional: motif title for display purposes
  String? get motifTitle => throw _privateConstructorUsedError;

  /// Optional: category for organization
  String? get category => throw _privateConstructorUsedError;

  /// Serializes this ReviewItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ReviewItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ReviewItemCopyWith<ReviewItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ReviewItemCopyWith<$Res> {
  factory $ReviewItemCopyWith(
          ReviewItem value, $Res Function(ReviewItem) then) =
      _$ReviewItemCopyWithImpl<$Res, ReviewItem>;
  @useResult
  $Res call(
      {String motifId,
      double easeFactor,
      int interval,
      int repetitions,
      DateTime nextReviewDate,
      DateTime? lastReviewDate,
      List<int> qualityHistory,
      String? motifTitle,
      String? category});
}

/// @nodoc
class _$ReviewItemCopyWithImpl<$Res, $Val extends ReviewItem>
    implements $ReviewItemCopyWith<$Res> {
  _$ReviewItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ReviewItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? easeFactor = null,
    Object? interval = null,
    Object? repetitions = null,
    Object? nextReviewDate = null,
    Object? lastReviewDate = freezed,
    Object? qualityHistory = null,
    Object? motifTitle = freezed,
    Object? category = freezed,
  }) {
    return _then(_value.copyWith(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      easeFactor: null == easeFactor
          ? _value.easeFactor
          : easeFactor // ignore: cast_nullable_to_non_nullable
              as double,
      interval: null == interval
          ? _value.interval
          : interval // ignore: cast_nullable_to_non_nullable
              as int,
      repetitions: null == repetitions
          ? _value.repetitions
          : repetitions // ignore: cast_nullable_to_non_nullable
              as int,
      nextReviewDate: null == nextReviewDate
          ? _value.nextReviewDate
          : nextReviewDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastReviewDate: freezed == lastReviewDate
          ? _value.lastReviewDate
          : lastReviewDate // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      qualityHistory: null == qualityHistory
          ? _value.qualityHistory
          : qualityHistory // ignore: cast_nullable_to_non_nullable
              as List<int>,
      motifTitle: freezed == motifTitle
          ? _value.motifTitle
          : motifTitle // ignore: cast_nullable_to_non_nullable
              as String?,
      category: freezed == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ReviewItemImplCopyWith<$Res>
    implements $ReviewItemCopyWith<$Res> {
  factory _$$ReviewItemImplCopyWith(
          _$ReviewItemImpl value, $Res Function(_$ReviewItemImpl) then) =
      __$$ReviewItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String motifId,
      double easeFactor,
      int interval,
      int repetitions,
      DateTime nextReviewDate,
      DateTime? lastReviewDate,
      List<int> qualityHistory,
      String? motifTitle,
      String? category});
}

/// @nodoc
class __$$ReviewItemImplCopyWithImpl<$Res>
    extends _$ReviewItemCopyWithImpl<$Res, _$ReviewItemImpl>
    implements _$$ReviewItemImplCopyWith<$Res> {
  __$$ReviewItemImplCopyWithImpl(
      _$ReviewItemImpl _value, $Res Function(_$ReviewItemImpl) _then)
      : super(_value, _then);

  /// Create a copy of ReviewItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? easeFactor = null,
    Object? interval = null,
    Object? repetitions = null,
    Object? nextReviewDate = null,
    Object? lastReviewDate = freezed,
    Object? qualityHistory = null,
    Object? motifTitle = freezed,
    Object? category = freezed,
  }) {
    return _then(_$ReviewItemImpl(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      easeFactor: null == easeFactor
          ? _value.easeFactor
          : easeFactor // ignore: cast_nullable_to_non_nullable
              as double,
      interval: null == interval
          ? _value.interval
          : interval // ignore: cast_nullable_to_non_nullable
              as int,
      repetitions: null == repetitions
          ? _value.repetitions
          : repetitions // ignore: cast_nullable_to_non_nullable
              as int,
      nextReviewDate: null == nextReviewDate
          ? _value.nextReviewDate
          : nextReviewDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastReviewDate: freezed == lastReviewDate
          ? _value.lastReviewDate
          : lastReviewDate // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      qualityHistory: null == qualityHistory
          ? _value._qualityHistory
          : qualityHistory // ignore: cast_nullable_to_non_nullable
              as List<int>,
      motifTitle: freezed == motifTitle
          ? _value.motifTitle
          : motifTitle // ignore: cast_nullable_to_non_nullable
              as String?,
      category: freezed == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ReviewItemImpl extends _ReviewItem {
  const _$ReviewItemImpl(
      {required this.motifId,
      this.easeFactor = 2.5,
      this.interval = 0,
      this.repetitions = 0,
      required this.nextReviewDate,
      this.lastReviewDate,
      final List<int> qualityHistory = const [],
      this.motifTitle,
      this.category})
      : _qualityHistory = qualityHistory,
        super._();

  factory _$ReviewItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$ReviewItemImplFromJson(json);

  /// Unique identifier of the motif being reviewed
  @override
  final String motifId;

  /// Ease Factor (EF) - Determines how quickly intervals increase
  /// Default: 2.5, Range: 1.3 to 2.5+
  /// Higher = easier item, intervals grow faster
  @override
  @JsonKey()
  final double easeFactor;

  /// Current interval in days until next review
  /// Grows based on performance (SM-2 algorithm)
  @override
  @JsonKey()
  final int interval;

  /// Number of consecutive successful reviews (quality >= 3)
  /// Resets to 0 when quality < 3
  @override
  @JsonKey()
  final int repetitions;

  /// Next scheduled review date
  @override
  final DateTime nextReviewDate;

  /// Last review date (null if never reviewed)
  @override
  final DateTime? lastReviewDate;

  /// History of quality ratings (0-5) for analytics
  /// 5: Perfect, 4: Correct with hesitation, 3: Correct with difficulty
  /// 2: Incorrect but easy recall, 1: Incorrect hard recall, 0: Complete blackout
  final List<int> _qualityHistory;

  /// History of quality ratings (0-5) for analytics
  /// 5: Perfect, 4: Correct with hesitation, 3: Correct with difficulty
  /// 2: Incorrect but easy recall, 1: Incorrect hard recall, 0: Complete blackout
  @override
  @JsonKey()
  List<int> get qualityHistory {
    if (_qualityHistory is EqualUnmodifiableListView) return _qualityHistory;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_qualityHistory);
  }

  /// Optional: motif title for display purposes
  @override
  final String? motifTitle;

  /// Optional: category for organization
  @override
  final String? category;

  @override
  String toString() {
    return 'ReviewItem(motifId: $motifId, easeFactor: $easeFactor, interval: $interval, repetitions: $repetitions, nextReviewDate: $nextReviewDate, lastReviewDate: $lastReviewDate, qualityHistory: $qualityHistory, motifTitle: $motifTitle, category: $category)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReviewItemImpl &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.easeFactor, easeFactor) ||
                other.easeFactor == easeFactor) &&
            (identical(other.interval, interval) ||
                other.interval == interval) &&
            (identical(other.repetitions, repetitions) ||
                other.repetitions == repetitions) &&
            (identical(other.nextReviewDate, nextReviewDate) ||
                other.nextReviewDate == nextReviewDate) &&
            (identical(other.lastReviewDate, lastReviewDate) ||
                other.lastReviewDate == lastReviewDate) &&
            const DeepCollectionEquality()
                .equals(other._qualityHistory, _qualityHistory) &&
            (identical(other.motifTitle, motifTitle) ||
                other.motifTitle == motifTitle) &&
            (identical(other.category, category) ||
                other.category == category));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      motifId,
      easeFactor,
      interval,
      repetitions,
      nextReviewDate,
      lastReviewDate,
      const DeepCollectionEquality().hash(_qualityHistory),
      motifTitle,
      category);

  /// Create a copy of ReviewItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ReviewItemImplCopyWith<_$ReviewItemImpl> get copyWith =>
      __$$ReviewItemImplCopyWithImpl<_$ReviewItemImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ReviewItemImplToJson(
      this,
    );
  }
}

abstract class _ReviewItem extends ReviewItem {
  const factory _ReviewItem(
      {required final String motifId,
      final double easeFactor,
      final int interval,
      final int repetitions,
      required final DateTime nextReviewDate,
      final DateTime? lastReviewDate,
      final List<int> qualityHistory,
      final String? motifTitle,
      final String? category}) = _$ReviewItemImpl;
  const _ReviewItem._() : super._();

  factory _ReviewItem.fromJson(Map<String, dynamic> json) =
      _$ReviewItemImpl.fromJson;

  /// Unique identifier of the motif being reviewed
  @override
  String get motifId;

  /// Ease Factor (EF) - Determines how quickly intervals increase
  /// Default: 2.5, Range: 1.3 to 2.5+
  /// Higher = easier item, intervals grow faster
  @override
  double get easeFactor;

  /// Current interval in days until next review
  /// Grows based on performance (SM-2 algorithm)
  @override
  int get interval;

  /// Number of consecutive successful reviews (quality >= 3)
  /// Resets to 0 when quality < 3
  @override
  int get repetitions;

  /// Next scheduled review date
  @override
  DateTime get nextReviewDate;

  /// Last review date (null if never reviewed)
  @override
  DateTime? get lastReviewDate;

  /// History of quality ratings (0-5) for analytics
  /// 5: Perfect, 4: Correct with hesitation, 3: Correct with difficulty
  /// 2: Incorrect but easy recall, 1: Incorrect hard recall, 0: Complete blackout
  @override
  List<int> get qualityHistory;

  /// Optional: motif title for display purposes
  @override
  String? get motifTitle;

  /// Optional: category for organization
  @override
  String? get category;

  /// Create a copy of ReviewItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ReviewItemImplCopyWith<_$ReviewItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
