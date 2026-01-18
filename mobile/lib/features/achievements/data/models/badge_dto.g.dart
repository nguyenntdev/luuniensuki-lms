// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'badge_dto.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$BadgeDtoImpl _$$BadgeDtoImplFromJson(Map<String, dynamic> json) =>
    _$BadgeDtoImpl(
      id: json['id'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      name: json['name'] as String? ?? '',
      nameEn: json['name_en'] as String?,
      description: json['description'] as String?,
      iconUrl: json['icon_url'] as String?,
      category: json['category'] as String? ?? 'achievement',
      xpBonus: (json['xp_bonus'] as num?)?.toInt() ?? 0,
      earnedAt: json['earned_at'] as String?,
    );

Map<String, dynamic> _$$BadgeDtoImplToJson(_$BadgeDtoImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'slug': instance.slug,
      'name': instance.name,
      'name_en': instance.nameEn,
      'description': instance.description,
      'icon_url': instance.iconUrl,
      'category': instance.category,
      'xp_bonus': instance.xpBonus,
      'earned_at': instance.earnedAt,
    };
