// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'review_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ReviewItemImpl _$$ReviewItemImplFromJson(Map<String, dynamic> json) =>
    _$ReviewItemImpl(
      motifId: json['motifId'] as String,
      easeFactor: (json['easeFactor'] as num?)?.toDouble() ?? 2.5,
      interval: (json['interval'] as num?)?.toInt() ?? 0,
      repetitions: (json['repetitions'] as num?)?.toInt() ?? 0,
      nextReviewDate: DateTime.parse(json['nextReviewDate'] as String),
      lastReviewDate: json['lastReviewDate'] == null
          ? null
          : DateTime.parse(json['lastReviewDate'] as String),
      qualityHistory: (json['qualityHistory'] as List<dynamic>?)
              ?.map((e) => (e as num).toInt())
              .toList() ??
          const [],
      motifTitle: json['motifTitle'] as String?,
      category: json['category'] as String?,
    );

Map<String, dynamic> _$$ReviewItemImplToJson(_$ReviewItemImpl instance) =>
    <String, dynamic>{
      'motifId': instance.motifId,
      'easeFactor': instance.easeFactor,
      'interval': instance.interval,
      'repetitions': instance.repetitions,
      'nextReviewDate': instance.nextReviewDate.toIso8601String(),
      'lastReviewDate': instance.lastReviewDate?.toIso8601String(),
      'qualityHistory': instance.qualityHistory,
      'motifTitle': instance.motifTitle,
      'category': instance.category,
    };
