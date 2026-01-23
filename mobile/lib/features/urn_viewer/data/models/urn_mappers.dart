import 'package:flutter/foundation.dart';
import '../../../../core/constants/api_constants.dart';
import '../../domain/entities/urn.dart';
import 'urn_dtos.dart';

/// Extension methods for converting Urn DTOs to domain entities

/// Helper function to convert relative URLs to full URLs
String? _toFullUrl(String? url) {
  if (url == null || url.isEmpty) return null;
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  // Prepend base URL for relative paths
  return '${ApiConstants.baseUrl}$url';
}

/// Extension for UrnDetailResponseDto (the wrapper from API)
extension UrnDetailResponseDtoMapper on UrnDetailResponseDto {
  /// Convert UrnDetailResponseDto to UrnDetail entity
  UrnDetail toEntity({Map<String, UserProgressDto>? progressByMotifId}) {
    final urnDto = urn;

    debugPrint('Converting urn ${urnDto.slug} to entity, progress map has ${progressByMotifId?.length ?? 0} entries');

    final urnEntity = Urn(
      id: urnDto.id,
      slug: urnDto.slug,
      name: urnDto.name,
      nameEn: urnDto.nameEn,
      description: urnDto.description,
      descriptionEn: urnDto.descriptionEn,
      displayOrder: urnDto.displayOrder,
      thumbnailUrl: _toFullUrl(urnDto.thumbnailUrl),
      modelUrl: _toFullUrl(urnDto.modelUrl),
      motifCount: motifs.length,
    );

    final motifEntities = motifs.map((m) {
      final progress = progressByMotifId?[m.id];
      debugPrint('Motif ${m.name} (${m.id}): progress = ${progress?.status ?? "null"}');
      return m.toEntity(progress: progress);
    }).toList();

    // Calculate counts from motifs
    // discovered = all non-hidden motifs (discovered + learned + mastered)
    // learned = learned + mastered motifs
    // mastered = only mastered motifs
    int discovered = 0;
    int learned = 0;
    int mastered = 0;
    for (final motif in motifEntities) {
      switch (motif.status) {
        case MotifStatus.discovered:
          discovered++;
          break;
        case MotifStatus.learned:
          discovered++;
          learned++;
          break;
        case MotifStatus.mastered:
          discovered++;
          learned++;
          mastered++;
          break;
        case MotifStatus.hidden:
          break;
      }
    }

    debugPrint('Calculated counts - Discovered: $discovered, Learned: $learned, Mastered: $mastered');

    return UrnDetail(
      urn: urnEntity.copyWith(
        discoveredCount: discovered,
        learnedCount: learned,
        masteredCount: mastered,
      ),
      motifs: motifEntities,
    );
  }
}

extension UrnListItemDtoMapper on UrnListItemDto {
  /// Convert UrnListItemDto to Urn entity
  Urn toEntity() {
    return Urn(
      id: id,
      slug: slug,
      name: name,
      nameEn: nameEn,
      displayOrder: displayOrder,
      thumbnailUrl: _toFullUrl(thumbnailUrl),
      modelUrl: _toFullUrl(modelUrl),
      motifCount: motifCount,
      discoveredCount: discoveredCount,
      learnedCount: learnedCount,
      masteredCount: masteredCount,
    );
  }
}

/// Extension for UrnDetailDto (kept for backward compatibility)
extension UrnDetailDtoMapper on UrnDetailDto {
  /// Convert to Urn entity (without motifs)
  Urn toUrnEntity() {
    return Urn(
      id: id,
      slug: slug,
      name: name,
      nameEn: nameEn,
      description: description,
      descriptionEn: descriptionEn,
      displayOrder: displayOrder,
      thumbnailUrl: _toFullUrl(thumbnailUrl),
      modelUrl: _toFullUrl(modelUrl),
      motifCount: 0,
    );
  }
}

extension MotifDtoMapper on MotifDto {
  /// Convert MotifDto to Motif entity
  Motif toEntity({UserProgressDto? progress}) {
    return Motif(
      id: id,
      urnId: urnId,
      meshName: meshName,
      name: name,
      nameEn: nameEn,
      category: MotifCategory.fromString(category),
      rarity: MotifRarity.fromString(rarity),
      posX: posX,
      posY: posY,
      posZ: posZ,
      boundingRadius: boundingRadius,
      thumbnailUrl: _toFullUrl(thumbnailUrl ?? imageUrl),
      isDemo: isDemo,
      status: progress != null
          ? MotifStatus.fromString(progress.status)
          : MotifStatus.hidden,
      xpEarned: progress?.xpEarned ?? 0,
    );
  }
}

extension MotifDetailDtoMapper on MotifDetailDto {
  /// Convert MotifDetailDto to Motif entity
  Motif toEntity() {
    return Motif(
      id: id,
      urnId: urn.id,
      meshName: meshName,
      name: name,
      nameEn: nameEn,
      category: MotifCategory.fromString(category),
      rarity: MotifRarity.fromString(rarity),
      posX: posX,
      posY: posY,
      posZ: posZ,
      boundingRadius: boundingRadius,
      thumbnailUrl: _toFullUrl(thumbnailUrl ?? imageUrl),
      isDemo: isDemo,
      status: progress != null
          ? MotifStatus.fromString(progress!.status)
          : MotifStatus.hidden,
      xpEarned: progress?.xpEarned ?? 0,
    );
  }
}

extension UnlockResponseDtoMapper on UnlockResponseDto {
  /// Convert UnlockResponseDto to UnlockResult entity
  UnlockResult toEntity(Motif motif) {
    return UnlockResult(
      motif: motif.copyWith(
        status: MotifStatus.fromString(progress.status),
        xpEarned: progress.xpEarned,
      ),
      xpEarned: xpEarned,
      totalXp: totalXp,
      badgesEarned: newBadges.map((b) => b.slug).toList(),
      isNewDiscovery: xpEarned > 0,
    );
  }
}

extension UserProgressDtoMapper on UserProgressDto {
  /// Get status as enum
  MotifStatus get statusEnum => MotifStatus.fromString(status);

  /// Check if discovered
  bool get isDiscovered => statusEnum != MotifStatus.hidden;

  /// Check if learned
  bool get isLearned =>
      statusEnum == MotifStatus.learned || statusEnum == MotifStatus.mastered;

  /// Check if mastered
  bool get isMastered => statusEnum == MotifStatus.mastered;
}

/// Extension for converting entity back to JSON for caching
extension UrnToJson on Urn {
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'slug': slug,
      'name': name,
      'name_en': nameEn,
      'description': description,
      'description_en': descriptionEn,
      'display_order': displayOrder,
      'thumbnail_url': thumbnailUrl,
      'model_url': modelUrl,
      'motif_count': motifCount,
      'discovered_count': discoveredCount,
      'learned_count': learnedCount,
      'mastered_count': masteredCount,
    };
  }

  static Urn fromJson(Map<String, dynamic> json) {
    return Urn(
      id: json['id'] as String,
      slug: json['slug'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      description: json['description'] as String?,
      descriptionEn: json['description_en'] as String?,
      displayOrder: json['display_order'] as int? ?? 0,
      thumbnailUrl: json['thumbnail_url'] as String?,
      modelUrl: json['model_url'] as String?,
      motifCount: json['motif_count'] as int? ?? 0,
      discoveredCount: json['discovered_count'] as int? ?? 0,
      learnedCount: json['learned_count'] as int? ?? 0,
      masteredCount: json['mastered_count'] as int? ?? 0,
    );
  }
}

extension MotifToJson on Motif {
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'urn_id': urnId,
      'mesh_name': meshName,
      'name': name,
      'name_en': nameEn,
      'category': category.value,
      'rarity': rarity.value,
      'pos_x': posX,
      'pos_y': posY,
      'pos_z': posZ,
      'bounding_radius': boundingRadius,
      'thumbnail_url': thumbnailUrl,
      'description': description,
      'is_demo': isDemo,
      'status': status.value,
      'xp_earned': xpEarned,
    };
  }

  static Motif fromJson(Map<String, dynamic> json) {
    return Motif(
      id: json['id'] as String,
      urnId: json['urn_id'] as String,
      meshName: json['mesh_name'] as String,
      name: json['name'] as String,
      nameEn: json['name_en'] as String?,
      category: MotifCategory.fromString(json['category'] as String),
      rarity: MotifRarity.fromString(json['rarity'] as String),
      posX: (json['pos_x'] as num?)?.toDouble() ?? 0.0,
      posY: (json['pos_y'] as num?)?.toDouble() ?? 0.0,
      posZ: (json['pos_z'] as num?)?.toDouble() ?? 0.0,
      boundingRadius: (json['bounding_radius'] as num?)?.toDouble() ?? 0.08,
      thumbnailUrl: json['thumbnail_url'] as String?,
      description: json['description'] as String?,
      isDemo: json['is_demo'] as bool? ?? false,
      status: MotifStatus.fromString(json['status'] as String? ?? 'hidden'),
      xpEarned: json['xp_earned'] as int? ?? 0,
    );
  }
}
