import 'package:freezed_annotation/freezed_annotation.dart';

part 'collection_dtos.freezed.dart';
part 'collection_dtos.g.dart';

/// Collection stats DTO
@freezed
class CollectionStatsDto with _$CollectionStatsDto {
  const factory CollectionStatsDto({
    required int total,
    required int discovered,
    required int learned,
    required int mastered,
  }) = _CollectionStatsDto;

  factory CollectionStatsDto.fromJson(Map<String, dynamic> json) =>
      _$CollectionStatsDtoFromJson(json);
}

/// Collection motif DTO
@freezed
class CollectionMotifDto with _$CollectionMotifDto {
  const factory CollectionMotifDto({
    @JsonKey(name: 'motif_id') required String id,
    @JsonKey(name: 'mesh_name') required String meshName,
    required String name,
    @JsonKey(name: 'name_en') String? nameEn,
    required String category,
    required String rarity,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    required String status,
  }) = _CollectionMotifDto;

  factory CollectionMotifDto.fromJson(Map<String, dynamic> json) =>
      _$CollectionMotifDtoFromJson(json);
}

/// Collection response DTO
@freezed
class CollectionResponseDto with _$CollectionResponseDto {
  const factory CollectionResponseDto({
    required List<CollectionMotifDto> items,
    required CollectionStatsDto stats,
  }) = _CollectionResponseDto;

  factory CollectionResponseDto.fromJson(Map<String, dynamic> json) =>
      _$CollectionResponseDtoFromJson(json);
}

