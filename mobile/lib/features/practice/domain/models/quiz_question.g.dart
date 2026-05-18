// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'quiz_question.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$QuizQuestionImpl _$$QuizQuestionImplFromJson(Map<String, dynamic> json) =>
    _$QuizQuestionImpl(
      id: json['id'] as String,
      type: $enumDecode(_$QuizTypeEnumMap, json['type']),
      motifId: json['motifId'] as String,
      question: json['question'] as String,
      options:
          (json['options'] as List<dynamic>).map((e) => e as String).toList(),
      correctAnswer: json['correctAnswer'] as String,
      imageUrl: json['imageUrl'] as String?,
      hint: json['hint'] as String?,
      points: (json['points'] as num?)?.toInt() ?? 10,
      explanation: json['explanation'] as String?,
    );

Map<String, dynamic> _$$QuizQuestionImplToJson(_$QuizQuestionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'type': _$QuizTypeEnumMap[instance.type]!,
      'motifId': instance.motifId,
      'question': instance.question,
      'options': instance.options,
      'correctAnswer': instance.correctAnswer,
      'imageUrl': instance.imageUrl,
      'hint': instance.hint,
      'points': instance.points,
      'explanation': instance.explanation,
    };

const _$QuizTypeEnumMap = {
  QuizType.multipleChoice: 'multipleChoice',
  QuizType.imageMatching: 'imageMatching',
  QuizType.trueFalse: 'trueFalse',
  QuizType.fillInBlank: 'fillInBlank',
  QuizType.dragAndDrop: 'dragAndDrop',
};
