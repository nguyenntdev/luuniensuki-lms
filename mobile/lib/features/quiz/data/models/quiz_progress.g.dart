// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'quiz_progress.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$QuizProgressImpl _$$QuizProgressImplFromJson(Map<String, dynamic> json) =>
    _$QuizProgressImpl(
      motifId: json['motifId'] as String,
      motifName: json['motifName'] as String,
      currentQuestionIndex: (json['currentQuestionIndex'] as num).toInt(),
      answers: Map<String, String>.from(json['answers'] as Map),
      incorrectAnswers: Map<String, bool>.from(json['incorrectAnswers'] as Map),
      timeSpentSeconds: (json['timeSpentSeconds'] as num).toInt(),
      savedAt: DateTime.parse(json['savedAt'] as String),
      questionsHash: json['questionsHash'] as String,
    );

Map<String, dynamic> _$$QuizProgressImplToJson(_$QuizProgressImpl instance) =>
    <String, dynamic>{
      'motifId': instance.motifId,
      'motifName': instance.motifName,
      'currentQuestionIndex': instance.currentQuestionIndex,
      'answers': instance.answers,
      'incorrectAnswers': instance.incorrectAnswers,
      'timeSpentSeconds': instance.timeSpentSeconds,
      'savedAt': instance.savedAt.toIso8601String(),
      'questionsHash': instance.questionsHash,
    };
