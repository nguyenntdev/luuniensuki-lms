// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'quiz_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$QuizQuestion {
  String get id => throw _privateConstructorUsedError;
  String get motifId => throw _privateConstructorUsedError;
  QuestionType get questionType => throw _privateConstructorUsedError;
  String get questionText => throw _privateConstructorUsedError;
  String get correctAnswer => throw _privateConstructorUsedError;
  List<String> get options => throw _privateConstructorUsedError;
  String? get imageUrl => throw _privateConstructorUsedError;
  String? get explanation => throw _privateConstructorUsedError;
  int get displayOrder => throw _privateConstructorUsedError;

  /// Create a copy of QuizQuestion
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizQuestionCopyWith<QuizQuestion> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizQuestionCopyWith<$Res> {
  factory $QuizQuestionCopyWith(
          QuizQuestion value, $Res Function(QuizQuestion) then) =
      _$QuizQuestionCopyWithImpl<$Res, QuizQuestion>;
  @useResult
  $Res call(
      {String id,
      String motifId,
      QuestionType questionType,
      String questionText,
      String correctAnswer,
      List<String> options,
      String? imageUrl,
      String? explanation,
      int displayOrder});
}

/// @nodoc
class _$QuizQuestionCopyWithImpl<$Res, $Val extends QuizQuestion>
    implements $QuizQuestionCopyWith<$Res> {
  _$QuizQuestionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizQuestion
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? questionType = null,
    Object? questionText = null,
    Object? correctAnswer = null,
    Object? options = null,
    Object? imageUrl = freezed,
    Object? explanation = freezed,
    Object? displayOrder = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      questionType: null == questionType
          ? _value.questionType
          : questionType // ignore: cast_nullable_to_non_nullable
              as QuestionType,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      correctAnswer: null == correctAnswer
          ? _value.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String,
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizQuestionImplCopyWith<$Res>
    implements $QuizQuestionCopyWith<$Res> {
  factory _$$QuizQuestionImplCopyWith(
          _$QuizQuestionImpl value, $Res Function(_$QuizQuestionImpl) then) =
      __$$QuizQuestionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String motifId,
      QuestionType questionType,
      String questionText,
      String correctAnswer,
      List<String> options,
      String? imageUrl,
      String? explanation,
      int displayOrder});
}

/// @nodoc
class __$$QuizQuestionImplCopyWithImpl<$Res>
    extends _$QuizQuestionCopyWithImpl<$Res, _$QuizQuestionImpl>
    implements _$$QuizQuestionImplCopyWith<$Res> {
  __$$QuizQuestionImplCopyWithImpl(
      _$QuizQuestionImpl _value, $Res Function(_$QuizQuestionImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizQuestion
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? questionType = null,
    Object? questionText = null,
    Object? correctAnswer = null,
    Object? options = null,
    Object? imageUrl = freezed,
    Object? explanation = freezed,
    Object? displayOrder = null,
  }) {
    return _then(_$QuizQuestionImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      questionType: null == questionType
          ? _value.questionType
          : questionType // ignore: cast_nullable_to_non_nullable
              as QuestionType,
      questionText: null == questionText
          ? _value.questionText
          : questionText // ignore: cast_nullable_to_non_nullable
              as String,
      correctAnswer: null == correctAnswer
          ? _value.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String,
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
    ));
  }
}

/// @nodoc

class _$QuizQuestionImpl extends _QuizQuestion {
  const _$QuizQuestionImpl(
      {required this.id,
      required this.motifId,
      required this.questionType,
      required this.questionText,
      required this.correctAnswer,
      final List<String> options = const [],
      this.imageUrl,
      this.explanation,
      this.displayOrder = 0})
      : _options = options,
        super._();

  @override
  final String id;
  @override
  final String motifId;
  @override
  final QuestionType questionType;
  @override
  final String questionText;
  @override
  final String correctAnswer;
  final List<String> _options;
  @override
  @JsonKey()
  List<String> get options {
    if (_options is EqualUnmodifiableListView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_options);
  }

  @override
  final String? imageUrl;
  @override
  final String? explanation;
  @override
  @JsonKey()
  final int displayOrder;

  @override
  String toString() {
    return 'QuizQuestion(id: $id, motifId: $motifId, questionType: $questionType, questionText: $questionText, correctAnswer: $correctAnswer, options: $options, imageUrl: $imageUrl, explanation: $explanation, displayOrder: $displayOrder)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizQuestionImpl &&
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
                other.displayOrder == displayOrder));
  }

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
      displayOrder);

  /// Create a copy of QuizQuestion
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizQuestionImplCopyWith<_$QuizQuestionImpl> get copyWith =>
      __$$QuizQuestionImplCopyWithImpl<_$QuizQuestionImpl>(this, _$identity);
}

abstract class _QuizQuestion extends QuizQuestion {
  const factory _QuizQuestion(
      {required final String id,
      required final String motifId,
      required final QuestionType questionType,
      required final String questionText,
      required final String correctAnswer,
      final List<String> options,
      final String? imageUrl,
      final String? explanation,
      final int displayOrder}) = _$QuizQuestionImpl;
  const _QuizQuestion._() : super._();

  @override
  String get id;
  @override
  String get motifId;
  @override
  QuestionType get questionType;
  @override
  String get questionText;
  @override
  String get correctAnswer;
  @override
  List<String> get options;
  @override
  String? get imageUrl;
  @override
  String? get explanation;
  @override
  int get displayOrder;

  /// Create a copy of QuizQuestion
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizQuestionImplCopyWith<_$QuizQuestionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$Quiz {
  String get motifId => throw _privateConstructorUsedError;
  String get motifName => throw _privateConstructorUsedError;
  List<QuizQuestion> get questions => throw _privateConstructorUsedError;

  /// Create a copy of Quiz
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizCopyWith<Quiz> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizCopyWith<$Res> {
  factory $QuizCopyWith(Quiz value, $Res Function(Quiz) then) =
      _$QuizCopyWithImpl<$Res, Quiz>;
  @useResult
  $Res call({String motifId, String motifName, List<QuizQuestion> questions});
}

/// @nodoc
class _$QuizCopyWithImpl<$Res, $Val extends Quiz>
    implements $QuizCopyWith<$Res> {
  _$QuizCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Quiz
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = null,
    Object? questions = null,
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
      questions: null == questions
          ? _value.questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestion>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizImplCopyWith<$Res> implements $QuizCopyWith<$Res> {
  factory _$$QuizImplCopyWith(
          _$QuizImpl value, $Res Function(_$QuizImpl) then) =
      __$$QuizImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String motifId, String motifName, List<QuizQuestion> questions});
}

/// @nodoc
class __$$QuizImplCopyWithImpl<$Res>
    extends _$QuizCopyWithImpl<$Res, _$QuizImpl>
    implements _$$QuizImplCopyWith<$Res> {
  __$$QuizImplCopyWithImpl(_$QuizImpl _value, $Res Function(_$QuizImpl) _then)
      : super(_value, _then);

  /// Create a copy of Quiz
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? motifName = null,
    Object? questions = null,
  }) {
    return _then(_$QuizImpl(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      motifName: null == motifName
          ? _value.motifName
          : motifName // ignore: cast_nullable_to_non_nullable
              as String,
      questions: null == questions
          ? _value._questions
          : questions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestion>,
    ));
  }
}

/// @nodoc

class _$QuizImpl extends _Quiz {
  const _$QuizImpl(
      {required this.motifId,
      required this.motifName,
      required final List<QuizQuestion> questions})
      : _questions = questions,
        super._();

  @override
  final String motifId;
  @override
  final String motifName;
  final List<QuizQuestion> _questions;
  @override
  List<QuizQuestion> get questions {
    if (_questions is EqualUnmodifiableListView) return _questions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_questions);
  }

  @override
  String toString() {
    return 'Quiz(motifId: $motifId, motifName: $motifName, questions: $questions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizImpl &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.motifName, motifName) ||
                other.motifName == motifName) &&
            const DeepCollectionEquality()
                .equals(other._questions, _questions));
  }

  @override
  int get hashCode => Object.hash(runtimeType, motifId, motifName,
      const DeepCollectionEquality().hash(_questions));

  /// Create a copy of Quiz
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizImplCopyWith<_$QuizImpl> get copyWith =>
      __$$QuizImplCopyWithImpl<_$QuizImpl>(this, _$identity);
}

abstract class _Quiz extends Quiz {
  const factory _Quiz(
      {required final String motifId,
      required final String motifName,
      required final List<QuizQuestion> questions}) = _$QuizImpl;
  const _Quiz._() : super._();

  @override
  String get motifId;
  @override
  String get motifName;
  @override
  List<QuizQuestion> get questions;

  /// Create a copy of Quiz
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizImplCopyWith<_$QuizImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$QuizAnswer {
  String get questionId => throw _privateConstructorUsedError;
  String get answer => throw _privateConstructorUsedError;

  /// Create a copy of QuizAnswer
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizAnswerCopyWith<QuizAnswer> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizAnswerCopyWith<$Res> {
  factory $QuizAnswerCopyWith(
          QuizAnswer value, $Res Function(QuizAnswer) then) =
      _$QuizAnswerCopyWithImpl<$Res, QuizAnswer>;
  @useResult
  $Res call({String questionId, String answer});
}

/// @nodoc
class _$QuizAnswerCopyWithImpl<$Res, $Val extends QuizAnswer>
    implements $QuizAnswerCopyWith<$Res> {
  _$QuizAnswerCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizAnswer
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
abstract class _$$QuizAnswerImplCopyWith<$Res>
    implements $QuizAnswerCopyWith<$Res> {
  factory _$$QuizAnswerImplCopyWith(
          _$QuizAnswerImpl value, $Res Function(_$QuizAnswerImpl) then) =
      __$$QuizAnswerImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String questionId, String answer});
}

/// @nodoc
class __$$QuizAnswerImplCopyWithImpl<$Res>
    extends _$QuizAnswerCopyWithImpl<$Res, _$QuizAnswerImpl>
    implements _$$QuizAnswerImplCopyWith<$Res> {
  __$$QuizAnswerImplCopyWithImpl(
      _$QuizAnswerImpl _value, $Res Function(_$QuizAnswerImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizAnswer
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? questionId = null,
    Object? answer = null,
  }) {
    return _then(_$QuizAnswerImpl(
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

class _$QuizAnswerImpl implements _QuizAnswer {
  const _$QuizAnswerImpl({required this.questionId, required this.answer});

  @override
  final String questionId;
  @override
  final String answer;

  @override
  String toString() {
    return 'QuizAnswer(questionId: $questionId, answer: $answer)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizAnswerImpl &&
            (identical(other.questionId, questionId) ||
                other.questionId == questionId) &&
            (identical(other.answer, answer) || other.answer == answer));
  }

  @override
  int get hashCode => Object.hash(runtimeType, questionId, answer);

  /// Create a copy of QuizAnswer
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizAnswerImplCopyWith<_$QuizAnswerImpl> get copyWith =>
      __$$QuizAnswerImplCopyWithImpl<_$QuizAnswerImpl>(this, _$identity);
}

abstract class _QuizAnswer implements QuizAnswer {
  const factory _QuizAnswer(
      {required final String questionId,
      required final String answer}) = _$QuizAnswerImpl;

  @override
  String get questionId;
  @override
  String get answer;

  /// Create a copy of QuizAnswer
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizAnswerImplCopyWith<_$QuizAnswerImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$QuizSubmission {
  String get motifId => throw _privateConstructorUsedError;
  List<QuizAnswer> get answers => throw _privateConstructorUsedError;
  int? get timeTakenSeconds => throw _privateConstructorUsedError;

  /// Create a copy of QuizSubmission
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizSubmissionCopyWith<QuizSubmission> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizSubmissionCopyWith<$Res> {
  factory $QuizSubmissionCopyWith(
          QuizSubmission value, $Res Function(QuizSubmission) then) =
      _$QuizSubmissionCopyWithImpl<$Res, QuizSubmission>;
  @useResult
  $Res call({String motifId, List<QuizAnswer> answers, int? timeTakenSeconds});
}

/// @nodoc
class _$QuizSubmissionCopyWithImpl<$Res, $Val extends QuizSubmission>
    implements $QuizSubmissionCopyWith<$Res> {
  _$QuizSubmissionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizSubmission
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? answers = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_value.copyWith(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      answers: null == answers
          ? _value.answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<QuizAnswer>,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizSubmissionImplCopyWith<$Res>
    implements $QuizSubmissionCopyWith<$Res> {
  factory _$$QuizSubmissionImplCopyWith(_$QuizSubmissionImpl value,
          $Res Function(_$QuizSubmissionImpl) then) =
      __$$QuizSubmissionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String motifId, List<QuizAnswer> answers, int? timeTakenSeconds});
}

/// @nodoc
class __$$QuizSubmissionImplCopyWithImpl<$Res>
    extends _$QuizSubmissionCopyWithImpl<$Res, _$QuizSubmissionImpl>
    implements _$$QuizSubmissionImplCopyWith<$Res> {
  __$$QuizSubmissionImplCopyWithImpl(
      _$QuizSubmissionImpl _value, $Res Function(_$QuizSubmissionImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizSubmission
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? motifId = null,
    Object? answers = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_$QuizSubmissionImpl(
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      answers: null == answers
          ? _value._answers
          : answers // ignore: cast_nullable_to_non_nullable
              as List<QuizAnswer>,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc

class _$QuizSubmissionImpl extends _QuizSubmission {
  const _$QuizSubmissionImpl(
      {required this.motifId,
      required final List<QuizAnswer> answers,
      this.timeTakenSeconds})
      : _answers = answers,
        super._();

  @override
  final String motifId;
  final List<QuizAnswer> _answers;
  @override
  List<QuizAnswer> get answers {
    if (_answers is EqualUnmodifiableListView) return _answers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_answers);
  }

  @override
  final int? timeTakenSeconds;

  @override
  String toString() {
    return 'QuizSubmission(motifId: $motifId, answers: $answers, timeTakenSeconds: $timeTakenSeconds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizSubmissionImpl &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            const DeepCollectionEquality().equals(other._answers, _answers) &&
            (identical(other.timeTakenSeconds, timeTakenSeconds) ||
                other.timeTakenSeconds == timeTakenSeconds));
  }

  @override
  int get hashCode => Object.hash(runtimeType, motifId,
      const DeepCollectionEquality().hash(_answers), timeTakenSeconds);

  /// Create a copy of QuizSubmission
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizSubmissionImplCopyWith<_$QuizSubmissionImpl> get copyWith =>
      __$$QuizSubmissionImplCopyWithImpl<_$QuizSubmissionImpl>(
          this, _$identity);
}

abstract class _QuizSubmission extends QuizSubmission {
  const factory _QuizSubmission(
      {required final String motifId,
      required final List<QuizAnswer> answers,
      final int? timeTakenSeconds}) = _$QuizSubmissionImpl;
  const _QuizSubmission._() : super._();

  @override
  String get motifId;
  @override
  List<QuizAnswer> get answers;
  @override
  int? get timeTakenSeconds;

  /// Create a copy of QuizSubmission
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizSubmissionImplCopyWith<_$QuizSubmissionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$QuizResult {
  bool get passed => throw _privateConstructorUsedError;
  int get score => throw _privateConstructorUsedError;
  int get totalQuestions => throw _privateConstructorUsedError;
  int get correctAnswers => throw _privateConstructorUsedError;
  int get percentage => throw _privateConstructorUsedError;
  int get xpEarned => throw _privateConstructorUsedError;
  int get totalXp => throw _privateConstructorUsedError;
  List<QuizBadge> get newBadges => throw _privateConstructorUsedError;
  bool get isNewBest => throw _privateConstructorUsedError;

  /// Create a copy of QuizResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizResultCopyWith<QuizResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizResultCopyWith<$Res> {
  factory $QuizResultCopyWith(
          QuizResult value, $Res Function(QuizResult) then) =
      _$QuizResultCopyWithImpl<$Res, QuizResult>;
  @useResult
  $Res call(
      {bool passed,
      int score,
      int totalQuestions,
      int correctAnswers,
      int percentage,
      int xpEarned,
      int totalXp,
      List<QuizBadge> newBadges,
      bool isNewBest});
}

/// @nodoc
class _$QuizResultCopyWithImpl<$Res, $Val extends QuizResult>
    implements $QuizResultCopyWith<$Res> {
  _$QuizResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizResult
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
              as List<QuizBadge>,
      isNewBest: null == isNewBest
          ? _value.isNewBest
          : isNewBest // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizResultImplCopyWith<$Res>
    implements $QuizResultCopyWith<$Res> {
  factory _$$QuizResultImplCopyWith(
          _$QuizResultImpl value, $Res Function(_$QuizResultImpl) then) =
      __$$QuizResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool passed,
      int score,
      int totalQuestions,
      int correctAnswers,
      int percentage,
      int xpEarned,
      int totalXp,
      List<QuizBadge> newBadges,
      bool isNewBest});
}

/// @nodoc
class __$$QuizResultImplCopyWithImpl<$Res>
    extends _$QuizResultCopyWithImpl<$Res, _$QuizResultImpl>
    implements _$$QuizResultImplCopyWith<$Res> {
  __$$QuizResultImplCopyWithImpl(
      _$QuizResultImpl _value, $Res Function(_$QuizResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizResult
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
  }) {
    return _then(_$QuizResultImpl(
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
              as List<QuizBadge>,
      isNewBest: null == isNewBest
          ? _value.isNewBest
          : isNewBest // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc

class _$QuizResultImpl extends _QuizResult {
  const _$QuizResultImpl(
      {required this.passed,
      required this.score,
      required this.totalQuestions,
      required this.correctAnswers,
      required this.percentage,
      this.xpEarned = 0,
      this.totalXp = 0,
      final List<QuizBadge> newBadges = const [],
      this.isNewBest = false})
      : _newBadges = newBadges,
        super._();

  @override
  final bool passed;
  @override
  final int score;
  @override
  final int totalQuestions;
  @override
  final int correctAnswers;
  @override
  final int percentage;
  @override
  @JsonKey()
  final int xpEarned;
  @override
  @JsonKey()
  final int totalXp;
  final List<QuizBadge> _newBadges;
  @override
  @JsonKey()
  List<QuizBadge> get newBadges {
    if (_newBadges is EqualUnmodifiableListView) return _newBadges;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_newBadges);
  }

  @override
  @JsonKey()
  final bool isNewBest;

  @override
  String toString() {
    return 'QuizResult(passed: $passed, score: $score, totalQuestions: $totalQuestions, correctAnswers: $correctAnswers, percentage: $percentage, xpEarned: $xpEarned, totalXp: $totalXp, newBadges: $newBadges, isNewBest: $isNewBest)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizResultImpl &&
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
                other.isNewBest == isNewBest));
  }

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
      isNewBest);

  /// Create a copy of QuizResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizResultImplCopyWith<_$QuizResultImpl> get copyWith =>
      __$$QuizResultImplCopyWithImpl<_$QuizResultImpl>(this, _$identity);
}

abstract class _QuizResult extends QuizResult {
  const factory _QuizResult(
      {required final bool passed,
      required final int score,
      required final int totalQuestions,
      required final int correctAnswers,
      required final int percentage,
      final int xpEarned,
      final int totalXp,
      final List<QuizBadge> newBadges,
      final bool isNewBest}) = _$QuizResultImpl;
  const _QuizResult._() : super._();

  @override
  bool get passed;
  @override
  int get score;
  @override
  int get totalQuestions;
  @override
  int get correctAnswers;
  @override
  int get percentage;
  @override
  int get xpEarned;
  @override
  int get totalXp;
  @override
  List<QuizBadge> get newBadges;
  @override
  bool get isNewBest;

  /// Create a copy of QuizResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizResultImplCopyWith<_$QuizResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$QuizBadge {
  String get id => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String? get nameEn => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get iconUrl => throw _privateConstructorUsedError;
  String get category => throw _privateConstructorUsedError;
  int get xpBonus => throw _privateConstructorUsedError;

  /// Create a copy of QuizBadge
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizBadgeCopyWith<QuizBadge> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizBadgeCopyWith<$Res> {
  factory $QuizBadgeCopyWith(QuizBadge value, $Res Function(QuizBadge) then) =
      _$QuizBadgeCopyWithImpl<$Res, QuizBadge>;
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      String? nameEn,
      String? description,
      String? iconUrl,
      String category,
      int xpBonus});
}

/// @nodoc
class _$QuizBadgeCopyWithImpl<$Res, $Val extends QuizBadge>
    implements $QuizBadgeCopyWith<$Res> {
  _$QuizBadgeCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizBadge
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
abstract class _$$QuizBadgeImplCopyWith<$Res>
    implements $QuizBadgeCopyWith<$Res> {
  factory _$$QuizBadgeImplCopyWith(
          _$QuizBadgeImpl value, $Res Function(_$QuizBadgeImpl) then) =
      __$$QuizBadgeImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String slug,
      String name,
      String? nameEn,
      String? description,
      String? iconUrl,
      String category,
      int xpBonus});
}

/// @nodoc
class __$$QuizBadgeImplCopyWithImpl<$Res>
    extends _$QuizBadgeCopyWithImpl<$Res, _$QuizBadgeImpl>
    implements _$$QuizBadgeImplCopyWith<$Res> {
  __$$QuizBadgeImplCopyWithImpl(
      _$QuizBadgeImpl _value, $Res Function(_$QuizBadgeImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizBadge
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
    return _then(_$QuizBadgeImpl(
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

class _$QuizBadgeImpl implements _QuizBadge {
  const _$QuizBadgeImpl(
      {required this.id,
      required this.slug,
      required this.name,
      this.nameEn,
      this.description,
      this.iconUrl,
      required this.category,
      this.xpBonus = 0});

  @override
  final String id;
  @override
  final String slug;
  @override
  final String name;
  @override
  final String? nameEn;
  @override
  final String? description;
  @override
  final String? iconUrl;
  @override
  final String category;
  @override
  @JsonKey()
  final int xpBonus;

  @override
  String toString() {
    return 'QuizBadge(id: $id, slug: $slug, name: $name, nameEn: $nameEn, description: $description, iconUrl: $iconUrl, category: $category, xpBonus: $xpBonus)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizBadgeImpl &&
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

  @override
  int get hashCode => Object.hash(runtimeType, id, slug, name, nameEn,
      description, iconUrl, category, xpBonus);

  /// Create a copy of QuizBadge
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizBadgeImplCopyWith<_$QuizBadgeImpl> get copyWith =>
      __$$QuizBadgeImplCopyWithImpl<_$QuizBadgeImpl>(this, _$identity);
}

abstract class _QuizBadge implements QuizBadge {
  const factory _QuizBadge(
      {required final String id,
      required final String slug,
      required final String name,
      final String? nameEn,
      final String? description,
      final String? iconUrl,
      required final String category,
      final int xpBonus}) = _$QuizBadgeImpl;

  @override
  String get id;
  @override
  String get slug;
  @override
  String get name;
  @override
  String? get nameEn;
  @override
  String? get description;
  @override
  String? get iconUrl;
  @override
  String get category;
  @override
  int get xpBonus;

  /// Create a copy of QuizBadge
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizBadgeImplCopyWith<_$QuizBadgeImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$QuizAttempt {
  String get id => throw _privateConstructorUsedError;
  String get motifId => throw _privateConstructorUsedError;
  int get score => throw _privateConstructorUsedError;
  int get percentage => throw _privateConstructorUsedError;
  bool get passed => throw _privateConstructorUsedError;
  DateTime get attemptedAt => throw _privateConstructorUsedError;
  int? get timeTakenSeconds => throw _privateConstructorUsedError;

  /// Create a copy of QuizAttempt
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $QuizAttemptCopyWith<QuizAttempt> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuizAttemptCopyWith<$Res> {
  factory $QuizAttemptCopyWith(
          QuizAttempt value, $Res Function(QuizAttempt) then) =
      _$QuizAttemptCopyWithImpl<$Res, QuizAttempt>;
  @useResult
  $Res call(
      {String id,
      String motifId,
      int score,
      int percentage,
      bool passed,
      DateTime attemptedAt,
      int? timeTakenSeconds});
}

/// @nodoc
class _$QuizAttemptCopyWithImpl<$Res, $Val extends QuizAttempt>
    implements $QuizAttemptCopyWith<$Res> {
  _$QuizAttemptCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of QuizAttempt
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? score = null,
    Object? percentage = null,
    Object? passed = null,
    Object? attemptedAt = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as int,
      passed: null == passed
          ? _value.passed
          : passed // ignore: cast_nullable_to_non_nullable
              as bool,
      attemptedAt: null == attemptedAt
          ? _value.attemptedAt
          : attemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuizAttemptImplCopyWith<$Res>
    implements $QuizAttemptCopyWith<$Res> {
  factory _$$QuizAttemptImplCopyWith(
          _$QuizAttemptImpl value, $Res Function(_$QuizAttemptImpl) then) =
      __$$QuizAttemptImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String motifId,
      int score,
      int percentage,
      bool passed,
      DateTime attemptedAt,
      int? timeTakenSeconds});
}

/// @nodoc
class __$$QuizAttemptImplCopyWithImpl<$Res>
    extends _$QuizAttemptCopyWithImpl<$Res, _$QuizAttemptImpl>
    implements _$$QuizAttemptImplCopyWith<$Res> {
  __$$QuizAttemptImplCopyWithImpl(
      _$QuizAttemptImpl _value, $Res Function(_$QuizAttemptImpl) _then)
      : super(_value, _then);

  /// Create a copy of QuizAttempt
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? motifId = null,
    Object? score = null,
    Object? percentage = null,
    Object? passed = null,
    Object? attemptedAt = null,
    Object? timeTakenSeconds = freezed,
  }) {
    return _then(_$QuizAttemptImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      motifId: null == motifId
          ? _value.motifId
          : motifId // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      percentage: null == percentage
          ? _value.percentage
          : percentage // ignore: cast_nullable_to_non_nullable
              as int,
      passed: null == passed
          ? _value.passed
          : passed // ignore: cast_nullable_to_non_nullable
              as bool,
      attemptedAt: null == attemptedAt
          ? _value.attemptedAt
          : attemptedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      timeTakenSeconds: freezed == timeTakenSeconds
          ? _value.timeTakenSeconds
          : timeTakenSeconds // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc

class _$QuizAttemptImpl extends _QuizAttempt {
  const _$QuizAttemptImpl(
      {required this.id,
      required this.motifId,
      required this.score,
      required this.percentage,
      required this.passed,
      required this.attemptedAt,
      this.timeTakenSeconds})
      : super._();

  @override
  final String id;
  @override
  final String motifId;
  @override
  final int score;
  @override
  final int percentage;
  @override
  final bool passed;
  @override
  final DateTime attemptedAt;
  @override
  final int? timeTakenSeconds;

  @override
  String toString() {
    return 'QuizAttempt(id: $id, motifId: $motifId, score: $score, percentage: $percentage, passed: $passed, attemptedAt: $attemptedAt, timeTakenSeconds: $timeTakenSeconds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuizAttemptImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.motifId, motifId) || other.motifId == motifId) &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.percentage, percentage) ||
                other.percentage == percentage) &&
            (identical(other.passed, passed) || other.passed == passed) &&
            (identical(other.attemptedAt, attemptedAt) ||
                other.attemptedAt == attemptedAt) &&
            (identical(other.timeTakenSeconds, timeTakenSeconds) ||
                other.timeTakenSeconds == timeTakenSeconds));
  }

  @override
  int get hashCode => Object.hash(runtimeType, id, motifId, score, percentage,
      passed, attemptedAt, timeTakenSeconds);

  /// Create a copy of QuizAttempt
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$QuizAttemptImplCopyWith<_$QuizAttemptImpl> get copyWith =>
      __$$QuizAttemptImplCopyWithImpl<_$QuizAttemptImpl>(this, _$identity);
}

abstract class _QuizAttempt extends QuizAttempt {
  const factory _QuizAttempt(
      {required final String id,
      required final String motifId,
      required final int score,
      required final int percentage,
      required final bool passed,
      required final DateTime attemptedAt,
      final int? timeTakenSeconds}) = _$QuizAttemptImpl;
  const _QuizAttempt._() : super._();

  @override
  String get id;
  @override
  String get motifId;
  @override
  int get score;
  @override
  int get percentage;
  @override
  bool get passed;
  @override
  DateTime get attemptedAt;
  @override
  int? get timeTakenSeconds;

  /// Create a copy of QuizAttempt
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$QuizAttemptImplCopyWith<_$QuizAttemptImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
