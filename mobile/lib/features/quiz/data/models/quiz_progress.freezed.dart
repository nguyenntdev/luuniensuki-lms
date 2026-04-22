// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'quiz_progress.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

QuizProgress _$QuizProgressFromJson(Map<String, dynamic> json) {
  return _QuizProgress.fromJson(json);
}

/// @nodoc
mixin _$QuizProgress {
  String get motifId => throw _privateConstructorUsedError;
  String get motifName => throw _privateConstructorUsedError;
  int get currentQuestionIndex => throw _privateConstructorUsedError;
  Map<String, String> get answers => throw _privateConstructorUsedError;
  Map<String, bool> get incorrectAnswers => throw _privateConstructorUsedError;
  int get timeSpentSeconds => throw _privateConstructorUsedError;
  DateTime get savedAt =>
      throw _privateConstructorUsedError; // Quiz content hash for validation
  String get questionsHash => throw _privateConstructorUsedError;

  /// Serializes this QuizProgress to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of QuizProgress
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizProgressCopyWith<QuizProgress> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizProgressCopyWith<$Res> {
  factory $QuizProgressCopyWith(
          QuizProgress value, $Res Function(QuizProgress) then) =
      _$QuizProgressCopyWithImpl<$Res, QuizProgress>;
  @useResult
  $Res call(
      {String motifId,
      String motifName,
      int currentQuestionIndex,
      Map<String, String> answers,
      Map<String, bool> incorrectAnswers,
      int timeSpentSeconds,
      DateTime savedAt,
      String questionsHash});
}

/// @nodoc
class _$QuizProgressCopyWithImpl<$Res, $Val extends QuizProgress>
    implements $QuizProgressCopyWith<$Res> {
  _$QuizProgressCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizProgress
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = null,
    Object? currentQuestionIndex = null,
    Object? answers = null,
    Object? incorrectAnswers = null,
    Object? timeSpentSeconds = null,
    Object? savedAt = null,
    Object? questionsHash = null,
  }) {
    return _then(_value.copyWith(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      motifName: null == motifName
          ? _value.motifName
          : motifName // ignore: cast_nullable_to_non_nullable
              as String,
      currentQuestionIndex: null == currentQuestionIndex
          ? _value.currentQuestionIndex
          : currentQuestionIndex // ignore: cast_nullable_to_non_nullable
              as int,
      answers: null == answers
          ? _value.answers
          : answers // ignore: cast_nullable_to_non_nullable
              as Map<String, String>,
      incorrectAnswers: null == incorrectAnswers
          ? _value.incorrectAnswers
          : incorrectAnswers // ignore: cast_nullable_to_non_nullable
              as Map<String, bool>,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      savedAt: null == savedAt
          ? _value.savedAt
          : savedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      questionsHash: null == questionsHash
          ? _value.questionsHash
          : questionsHash // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizProgressImplCopyWith<$Res>
    implements $QuizProgressCopyWith<$Res> {
  factory _$$QuizProgressImplCopyWith(
          _$QuizProgressImpl value, $Res Function(_$QuizProgressImpl) then) =
      __$$QuizProgressImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String motifId,
      String motifName,
      int currentQuestionIndex,
      Map<String, String> answers,
      Map<String, bool> incorrectAnswers,
      int timeSpentSeconds,
      DateTime savedAt,
      String questionsHash});
}

/// @nodoc
class __$$QuizProgressImplCopyWithImpl<$Res>
    extends _$QuizProgressCopyWithImpl<$Res, _$QuizProgressImpl>
    implements _$$QuizProgressImplCopyWith<$Res> {
  __$$QuizProgressImplCopyWithImpl(
      _$QuizProgressImpl _value, $Res Function(_$QuizProgressImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizProgress
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = null,
    Object? currentQuestionIndex = null,
    Object? answers = null,
    Object? incorrectAnswers = null,
    Object? timeSpentSeconds = null,
    Object? savedAt = null,
    Object? questionsHash = null,
  }) {
    return _then(_$QuizProgressImpl(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      motifName: null == motifName
          ? _value.motifName
          : motifName // ignore: cast_nullable_to_non_nullable
              as String,
      currentQuestionIndex: null == currentQuestionIndex
          ? _value.currentQuestionIndex
          : currentQuestionIndex // ignore: cast_nullable_to_non_nullable
              as int,
      answers: null == answers
          ? _value._answers
          : answers // ignore: cast_nullable_to_non_nullable
              as Map<String, String>,
      incorrectAnswers: null == incorrectAnswers
          ? _value._incorrectAnswers
          : incorrectAnswers // ignore: cast_nullable_to_non_nullable
              as Map<String, bool>,
      timeSpentSeconds: null == timeSpentSeconds
          ? _value.timeSpentSeconds
          : timeSpentSeconds // ignore: cast_nullable_to_non_nullable
              as int,
      savedAt: null == savedAt
          ? _value.savedAt
          : savedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      questionsHash: null == questionsHash
          ? _value.questionsHash
          : questionsHash // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuizProgressImpl extends _QuizProgress {
  const _$QuizProgressImpl(
      {required this.motifId,
      required this.motifName,
      required this.currentQuestionIndex,
      required final Map<String, String> answers,
      required final Map<String, bool> incorrectAnswers,
      required this.timeSpentSeconds,
      required this.savedAt,
      required this.questionsHash})
      : _answers = answers,
        _incorrectAnswers = incorrectAnswers,
        super._();

  factory _$QuizProgressImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuizProgressImplFromJson(json);

  @override
  final String motifId;
  @override
  final String motifName;
  @override
  final int currentQuestionIndex;
  final Map<String, String> _answers;
  @override
  Map<String, String> get answers {
    if (_answers is EqualUnmodifiableMapView) return _answers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_answers);
  }

  final Map<String, bool> _incorrectAnswers;
  @override
  Map<String, bool> get incorrectAnswers {
    if (_incorrectAnswers is EqualUnmodifiableMapView) return _incorrectAnswers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_incorrectAnswers);
  }

  @override
  final int timeSpentSeconds;
  @override
  final DateTime savedAt;
// Quiz content hash for validation
  @override
  final String questionsHash;

  @override
  String toString() {
    return 'QuizProgress(motifId: $motifId, motifName: $motifName, currentQuestionIndex: $currentQuestionIndex, answers: $answers, incorrectAnswers: $incorrectAnswers, timeSpentSeconds: $timeSpentSeconds, savedAt: $savedAt, questionsHash: $questionsHash)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizProgressImpl &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.motifName, motifName) ||
                other.motifName == motifName) &&
            (identical(other.currentQuestionIndex, currentQuestionIndex) ||
                other.currentQuestionIndex == currentQuestionIndex) &&
            const DeepCollectionEquality().equals(other._answers, _answers) &&
            const DeepCollectionEquality()
                .equals(other._incorrectAnswers, _incorrectAnswers) &&
            (identical(other.timeSpentSeconds, timeSpentSeconds) ||
                other.timeSpentSeconds == timeSpentSeconds) &&
            (identical(other.savedAt, savedAt) || other.savedAt == savedAt) &&
            (identical(other.questionsHash, questionsHash) ||
                other.questionsHash == questionsHash));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      motifId,
      motifName,
      currentQuestionIndex,
      const DeepCollectionEquality().hash(_answers),
      const DeepCollectionEquality().hash(_incorrectAnswers),
      timeSpentSeconds,
      savedAt,
      questionsHash);

  /// Create a copy of QuizProgress
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizProgressImplCopyWith<_$QuizProgressImpl> get copyWith =>
      __$$QuizProgressImplCopyWithImpl<_$QuizProgressImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuizProgressImplToJson(
      this,
    );
  }
}

abstract class _QuizProgress extends QuizProgress {
  const factory _QuizProgress(
      {required final String motifId,
      required final String motifName,
      required final int currentQuestionIndex,
      required final Map<String, String> answers,
      required final Map<String, bool> incorrectAnswers,
      required final int timeSpentSeconds,
      required final DateTime savedAt,
      required final String questionsHash}) = _$QuizProgressImpl;
  const _QuizProgress._() : super._();

  factory _QuizProgress.fromJson(Map<String, dynamic> json) =
      _$QuizProgressImpl.fromJson;

  @override
  String get motifId;
  @override
  String get motifName;
  @override
  int get currentQuestionIndex;
  @override
  Map<String, String> get answers;
  @override
  Map<String, bool> get incorrectAnswers;
  @override
  int get timeSpentSeconds;
  @override
  DateTime get savedAt; // Quiz content hash for validation
  @override
  String get questionsHash;

  /// Create a copy of QuizProgress
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizProgressImplCopyWith<_$QuizProgressImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
