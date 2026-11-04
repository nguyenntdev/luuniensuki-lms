import 'package:equatable/equatable.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/utils/url_utils.dart';

/// The 9 canonical Cửu Đỉnh Urn slugs in spatial order.
const List<String> canonicalUrnSlugs = [
  'cao-dinh',
  'nhan-dinh',
  'chuong-dinh',
  'anh-dinh',
  'nghi-dinh',
  'thuan-dinh',
  'tuyen-dinh',
  'du-dinh',
  'huyen-dinh',
];

/// Canonical Motif entity on a Cửu Đỉnh Urn (162 total, strictly 18 per urn)
class ExploreMotif extends Equatable {
  final String id;
  final String slug;
  final String urnSlug;
  final int order;
  final String name;
  final String? nameEn;
  final String? nameHanNom;
  final String? category;
  final String? rarity;
  final String? meshName;
  final double? posX;
  final double? posY;
  final double? posZ;
  final double boundingRadius;
  final String evidenceStatus;
  final int revision;
  final String? thumbnailUrl;

  const ExploreMotif({
    required this.id,
    required this.slug,
    required this.urnSlug,
    required this.order,
    required this.name,
    this.nameEn,
    this.nameHanNom,
    this.category,
    this.rarity,
    this.meshName,
    this.posX,
    this.posY,
    this.posZ,
    this.boundingRadius = 0.08,
    this.evidenceStatus = 'verified',
    this.revision = 1,
    this.thumbnailUrl,
  });

  /// Check if the motif evidence has been confirmed / verified
  bool get isVerified => evidenceStatus == 'verified';

  /// Check if the motif requires further archival review (e.g. 4 unconfirmed Hán-Nôm motifs)
  bool get needsReview => evidenceStatus == 'needs_review';

  factory ExploreMotif.fromJson(Map<String, dynamic> json) {
    return ExploreMotif(
      id: json['id']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      urnSlug: json['urn_slug']?.toString() ?? '',
      order: (json['order'] as num?)?.toInt() ?? 0,
      name: (json['name_vi'] ?? json['name']) as String? ?? '',
      nameEn: json['name_en'] as String?,
      nameHanNom: json['name_han_nom'] as String?,
      category: json['category'] as String?,
      rarity: json['rarity'] as String?,
      meshName: json['mesh_name'] as String?,
      posX: (json['pos_x'] as num?)?.toDouble(),
      posY: (json['pos_y'] as num?)?.toDouble(),
      posZ: (json['pos_z'] as num?)?.toDouble(),
      boundingRadius: (json['bounding_radius'] as num?)?.toDouble() ?? 0.08,
      evidenceStatus: json['evidence_status'] as String? ?? 'verified',
      revision: (json['revision'] as num?)?.toInt() ?? 1,
      thumbnailUrl: UrlUtils.toFullUrl(json['thumbnail_url'] as String?),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'slug': slug,
      'urn_slug': urnSlug,
      'order': order,
      'name': name,
      'name_en': nameEn,
      'name_han_nom': nameHanNom,
      'category': category,
      'rarity': rarity,
      'mesh_name': meshName,
      'pos_x': posX,
      'pos_y': posY,
      'pos_z': posZ,
      'bounding_radius': boundingRadius,
      'evidence_status': evidenceStatus,
      'revision': revision,
      'thumbnail_url': thumbnailUrl,
    };
  }

  @override
  List<Object?> get props => [
        id,
        slug,
        urnSlug,
        order,
        name,
        nameEn,
        nameHanNom,
        category,
        rarity,
        meshName,
        posX,
        posY,
        posZ,
        boundingRadius,
        evidenceStatus,
        revision,
        thumbnailUrl,
      ];
}

/// Urn entity representing one of the Nine Urns (Cửu Đỉnh)
class Urn extends Equatable {
  final String id;
  final String name;
  final String? nameEn;
  final String? nameHanNom;
  final String? reignTitle;
  final String? templeName;
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
  final String evidenceStatus;
  final int revision;
  final List<ExploreMotif> motifs;
  final DateTime? createdAt;

  const Urn({
    required this.id,
    required this.name,
    this.nameEn,
    this.nameHanNom,
    this.reignTitle,
    this.templeName,
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
    this.evidenceStatus = 'verified',
    this.revision = 1,
    this.motifs = const [],
    this.createdAt,
  });

  /// Check whether this urn belongs to the 9 canonical Cửu Đỉnh
  bool get isCanonical => canonicalUrnSlugs.contains(slug);

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

  /// Check if this urn has an official published 3D mesh (Cao Đỉnh only)
  bool get has3dMesh => slug == 'cao-dinh';

  /// Get the effective model URL - uses remote URL for Cao Đỉnh, empty string for missing meshes
  String get effectiveModelUrl {
    return remoteModelUrl ?? '';
  }

  /// Get the remote model URL if 3D mesh is present.
  /// Anti-abuse: Missing meshes strictly return null to prevent phantom 3D requests.
  String? get remoteModelUrl {
    if (!has3dMesh) {
      return null;
    }
    final normalized = UrlUtils.toFullUrl(modelUrl);
    if (normalized != null && normalized.isNotEmpty) {
      return normalized;
    }
    return '${ApiConstants.modelsAssetsUrl}/CAO-DINH-v1.glb';
  }

  /// Get 2D rubbing fallback URL from verified ban-duc-noi archival archive
  String get fallbackRubbingUrl {
    final folderName = slug.toUpperCase().replaceAll('-', ' ');
    return '${ApiConstants.assetsUrl}/ban-duc-noi/$folderName/$name.jpg';
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
    final rawMotifs = json['motifs'];
    List<ExploreMotif> motifsList = const [];
    if (rawMotifs is List) {
      motifsList = rawMotifs
          .whereType<Map<String, dynamic>>()
          .map(ExploreMotif.fromJson)
          .toList();
    }

    return Urn(
      id: json['id']?.toString() ?? '',
      name: (json['name_vi'] ?? json['name']) as String? ?? '',
      nameEn: json['name_en'] as String?,
      nameHanNom: (json['name_han_nom'] ?? json['name_han']) as String?,
      reignTitle: json['reign_title'] as String?,
      templeName: json['temple_name'] as String?,
      slug: json['slug'] as String? ?? '',
      description: json['description'] as String?,
      descriptionEn: json['description_en'] as String?,
      thumbnailUrl: UrlUtils.toFullUrl(json['thumbnail_url'] as String?),
      modelUrl: UrlUtils.toFullUrl(json['model_url'] as String?),
      displayOrder: (json['order'] ?? json['display_order']) as int? ?? 0,
      motifCount: json['motif_count'] as int? ?? (motifsList.isNotEmpty ? motifsList.length : 0),
      discoveredCount: json['discovered_count'] as int? ?? 0,
      learnedCount: json['learned_count'] as int? ?? 0,
      masteredCount: json['mastered_count'] as int? ?? 0,
      isDemo: json['is_demo'] as bool? ?? false,
      evidenceStatus: json['evidence_status'] as String? ?? 'verified',
      revision: (json['revision'] as num?)?.toInt() ?? 1,
      motifs: motifsList,
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
      'name_han_nom': nameHanNom,
      'reign_title': reignTitle,
      'temple_name': templeName,
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
      'evidence_status': evidenceStatus,
      'revision': revision,
      'motifs': motifs.map((m) => m.toJson()).toList(),
      'created_at': createdAt?.toIso8601String(),
    };
  }

  /// Create a copy with updated fields
  Urn copyWith({
    String? id,
    String? name,
    String? nameEn,
    String? nameHanNom,
    String? reignTitle,
    String? templeName,
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
    String? evidenceStatus,
    int? revision,
    List<ExploreMotif>? motifs,
    DateTime? createdAt,
  }) {
    return Urn(
      id: id ?? this.id,
      name: name ?? this.name,
      nameEn: nameEn ?? this.nameEn,
      nameHanNom: nameHanNom ?? this.nameHanNom,
      reignTitle: reignTitle ?? this.reignTitle,
      templeName: templeName ?? this.templeName,
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
      evidenceStatus: evidenceStatus ?? this.evidenceStatus,
      revision: revision ?? this.revision,
      motifs: motifs ?? this.motifs,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        nameEn,
        nameHanNom,
        reignTitle,
        templeName,
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
        evidenceStatus,
        revision,
        motifs,
        createdAt,
      ];

  @override
  String toString() => 'Urn(id: $id, name: $name, slug: $slug)';
}
