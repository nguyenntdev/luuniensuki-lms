// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recommendation_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$RecommendationItemDtoImpl _$$RecommendationItemDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$RecommendationItemDtoImpl(
      contentType: json['content_type'] as String,
      contentId: json['content_id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      reason: json['reason'] as String?,
      score: (json['score'] as num?)?.toDouble(),
      motifId: json['motif_id'] as String?,
      status: json['status'] as String?,
      lastCompleted: json['last_completed'] as String?,
      popularityScore: (json['popularity_score'] as num?)?.toInt(),
      similarityScore: (json['similarity_score'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$$RecommendationItemDtoImplToJson(
        _$RecommendationItemDtoImpl instance) =>
    <String, dynamic>{
      'content_type': instance.contentType,
      'content_id': instance.contentId,
      'title': instance.title,
      'description': instance.description,
      'reason': instance.reason,
      'score': instance.score,
      'motif_id': instance.motifId,
      'status': instance.status,
      'last_completed': instance.lastCompleted,
      'popularity_score': instance.popularityScore,
      'similarity_score': instance.similarityScore,
    };

_$RecommendationsResponseDtoImpl _$$RecommendationsResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$RecommendationsResponseDtoImpl(
      continueLearning: (json['continue_learning'] as List<dynamic>?)
          ?.map(
              (e) => RecommendationItemDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      discoverNew: (json['discover_new'] as List<dynamic>?)
          ?.map(
              (e) => RecommendationItemDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      reviewNeeded: (json['review_needed'] as List<dynamic>?)
          ?.map(
              (e) => RecommendationItemDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      popular: (json['popular'] as List<dynamic>?)
          ?.map(
              (e) => RecommendationItemDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$RecommendationsResponseDtoImplToJson(
        _$RecommendationsResponseDtoImpl instance) =>
    <String, dynamic>{
      'continue_learning': instance.continueLearning,
      'discover_new': instance.discoverNew,
      'review_needed': instance.reviewNeeded,
      'popular': instance.popular,
    };
