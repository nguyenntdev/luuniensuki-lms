import 'package:equatable/equatable.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/utils/url_utils.dart';

/// Urn entity representing one of the Nine Urns (Cửu Đỉnh)
class Urn extends Equatable {
  final String id;
  final String name;
  final String? nameEn;
  final String slug;
  final String? description;
  final String? descriptionEn;
  final String? thumbnailUrl;
  final String? modelUrl;
  final int displayOrder;
  final int motifCount;
  final int discoveredCount;
  final int learnedCount;
  final int masteredCount;
  final bool isDemo;
  final DateTime? createdAt;

  const Urn({
    required this.id,
    required this.name,
    this.nameEn,
    required this.slug,
    this.description,
    this.descriptionEn,
    this.thumbnailUrl,
    this.modelUrl,
    this.displayOrder = 0,
    this.motifCount = 0,
    this.discoveredCount = 0,
    this.learnedCount = 0,
    this.masteredCount = 0,
    this.isDemo = false,
    this.createdAt,
  });

  /// Calculate progress percentage (0.0 to 1.0)
  double get progressPercent {
    if (motifCount == 0) return 0.0;
    return masteredCount / motifCount;
  }

  /// Calculate discovery percentage (0.0 to 1.0)
  double get discoveryPercent {
    if (motifCount == 0) return 0.0;
    return discoveredCount / motifCount;
  }

  /// Check if all motifs are mastered
  bool get isCompleted => motifCount > 0 && masteredCount >= motifCount;

  /// Check if any motifs have been discovered
  bool get hasProgress => discoveredCount > 0;

  /// Get the effective model URL - uses remote URL for reliable loading
  String get effectiveModelUrl {
    // Use remote URL for model_viewer_plus compatibility
    // All 9 urn models are available on the remote server
    return remoteModelUrl;
  }

  /// Get the remote model URL
  String get remoteModelUrl {
    final normalized = UrlUtils.toFullUrl(modelUrl);
    if (normalized != null && normalized.isNotEmpty) {
      return normalized;
    }
    // Fallback to constructed URL
    return '${ApiConstants.modelsAssetsUrl}/${slug.toUpperCase()}-v1.glb';
  }

  /// Get display name (Vietnamese with optional English)
  String get displayName => name;

  /// Get full name with English
  String get fullDisplayName {
    if (nameEn != null && nameEn!.isNotEmpty) {
      return '$name ($nameEn)';
    }
    return name;
  }

  /// Create from JSON (API response)
  factory Urn.fromJson(Map<String, dynamic> json) {
    return Urn(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      nameEn: json['name_en'] as String?,
      slug: json['slug'] as String? ?? '',
      description: json['description'] as String?,
      descriptionEn: json['description_en'] as String?,
      thumbnailUrl: UrlUtils.toFullUrl(json['thumbnail_url'] as String?),
      modelUrl: UrlUtils.toFullUrl(json['model_url'] as String?),
      displayOrder: json['display_order'] as int? ?? 0,
      motifCount: json['motif_count'] as int? ?? 0,
      discoveredCount: json['discovered_count'] as int? ?? 0,
      learnedCount: json['learned_count'] as int? ?? 0,
      masteredCount: json['mastered_count'] as int? ?? 0,
      isDemo: json['is_demo'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  /// Convert to JSON for caching
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'name_en': nameEn,
      'slug': slug,
      'description': description,
      'description_en': descriptionEn,
      'thumbnail_url': thumbnailUrl,
      'model_url': modelUrl,
      'display_order': displayOrder,
      'motif_count': motifCount,
      'discovered_count': discoveredCount,
      'learned_count': learnedCount,
      'mastered_count': masteredCount,
      'is_demo': isDemo,
      'created_at': createdAt?.toIso8601String(),
    };
  }

  /// Create a copy with updated fields
  Urn copyWith({
    String? id,
    String? name,
    String? nameEn,
    String? slug,
    String? description,
    String? descriptionEn,
    String? thumbnailUrl,
    String? modelUrl,
    int? displayOrder,
    int? motifCount,
    int? discoveredCount,
    int? learnedCount,
    int? masteredCount,
    bool? isDemo,
    DateTime? createdAt,
  }) {
    return Urn(
      id: id ?? this.id,
      name: name ?? this.name,
      nameEn: nameEn ?? this.nameEn,
      slug: slug ?? this.slug,
      description: description ?? this.description,
      descriptionEn: descriptionEn ?? this.descriptionEn,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      modelUrl: modelUrl ?? this.modelUrl,
      displayOrder: displayOrder ?? this.displayOrder,
      motifCount: motifCount ?? this.motifCount,
      discoveredCount: discoveredCount ?? this.discoveredCount,
      learnedCount: learnedCount ?? this.learnedCount,
      masteredCount: masteredCount ?? this.masteredCount,
      isDemo: isDemo ?? this.isDemo,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        nameEn,
        slug,
        description,
        descriptionEn,
        thumbnailUrl,
        modelUrl,
        displayOrder,
        motifCount,
        discoveredCount,
        learnedCount,
        masteredCount,
        isDemo,
        createdAt,
      ];

  @override
  String toString() => 'Urn(id: $id, name: $name, slug: $slug)';
}
