// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'collection_dtos.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CollectionStatsDtoImpl _$$CollectionStatsDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$CollectionStatsDtoImpl(
      total: (json['total'] as num).toInt(),
      discovered: (json['discovered'] as num).toInt(),
      learned: (json['learned'] as num).toInt(),
      mastered: (json['mastered'] as num).toInt(),
    );

Map<String, dynamic> _$$CollectionStatsDtoImplToJson(
        _$CollectionStatsDtoImpl instance) =>
    <String, dynamic>{
      'total': instance.total,
      'discovered': instance.discovered,
      'learned': instance.learned,
      'mastered': instance.mastered,
    };

_$CollectionMotifDtoImpl _$$CollectionMotifDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$CollectionMotifDtoImpl(
      id: json['motif_id'] as String,
      meshName: json['mesh_name'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      category: json['category'] as String,
      rarity: json['rarity'] as String,
      thumbnailUrl: json['thumbnail_url'] as String?,
      status: json['status'] as String,
    );

Map<String, dynamic> _$$CollectionMotifDtoImplToJson(
        _$CollectionMotifDtoImpl instance) =>
    <String, dynamic>{
      'motif_id': instance.id,
      'mesh_name': instance.meshName,
      'name': instance.name,
      'name_en': instance.nameEn,
      'category': instance.category,
      'rarity': instance.rarity,
      'thumbnail_url': instance.thumbnailUrl,
      'status': instance.status,
    };

_$CollectionResponseDtoImpl _$$CollectionResponseDtoImplFromJson(
        Map<String, dynamic> json) =>
    _$CollectionResponseDtoImpl(
      items: (json['items'] as List<dynamic>)
          .map((e) => CollectionMotifDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      stats: CollectionStatsDto.fromJson(json['stats'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$CollectionResponseDtoImplToJson(
        _$CollectionResponseDtoImpl instance) =>
    <String, dynamic>{
      'items': instance.items,
      'stats': instance.stats,
    };
