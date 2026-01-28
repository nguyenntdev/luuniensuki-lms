import 'package:freezed_annotation/freezed_annotation.dart';

part 'recommendation_dto.freezed.dart';
part 'recommendation_dto.g.dart';

@freezed
class RecommendationItemDto with _$RecommendationItemDto {
  const factory RecommendationItemDto({
    @JsonKey(name: 'content_type') required String contentType,
    @JsonKey(name: 'content_id') required String contentId,
    required String title,
    String? description,
    String? reason,
    double? score,
    @JsonKey(name: 'motif_id') String? motifId,
    String? status,
    @JsonKey(name: 'last_completed') String? lastCompleted,
    @JsonKey(name: 'popularity_score') int? popularityScore,
    @JsonKey(name: 'similarity_score') double? similarityScore,
  }) = _RecommendationItemDto;

  factory RecommendationItemDto.fromJson(Map<String, dynamic> json) =>
      _$RecommendationItemDtoFromJson(json);
}

@freezed
class RecommendationsResponseDto with _$RecommendationsResponseDto {
  const factory RecommendationsResponseDto({
    @JsonKey(name: 'continue_learning') List<RecommendationItemDto>? continueLearning,
    @JsonKey(name: 'discover_new') List<RecommendationItemDto>? discoverNew,
    @JsonKey(name: 'review_needed') List<RecommendationItemDto>? reviewNeeded,
    List<RecommendationItemDto>? popular,
  }) = _RecommendationsResponseDto;

  factory RecommendationsResponseDto.fromJson(Map<String, dynamic> json) =>
      _$RecommendationsResponseDtoFromJson(json);
}

