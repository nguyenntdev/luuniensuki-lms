import 'package:equatable/equatable.dart';

/// Urn entity representing one of the Nine Urns (Cửu Đỉnh).
class Urn extends Equatable {
  final String id;
  final String slug;
  final String name;
  final String? nameEn;
  final String? description;
  final String? descriptionEn;
  final int displayOrder;
  final String? thumbnailUrl;
  final String? modelUrl;
  final int motifCount;
  final int discoveredCount;
  final int learnedCount;
  final int masteredCount;

  const Urn({
    required this.id,
    required this.slug,
    required this.name,
    this.nameEn,
    this.description,
    this.descriptionEn,
    required this.displayOrder,
    this.thumbnailUrl,
    this.modelUrl,
    this.motifCount = 0,
    this.discoveredCount = 0,
    this.learnedCount = 0,
    this.masteredCount = 0,
  });

  /// Calculate overall progress for this urn (0.0 - 1.0)
  double get progress {
    if (motifCount == 0) return 0.0;
    return masteredCount / motifCount;
  }

  /// Check if all motifs are mastered
  bool get isComplete => motifCount > 0 && masteredCount == motifCount;

  /// Check if any motifs have been discovered
  bool get hasProgress => discoveredCount > 0 || learnedCount > 0 || masteredCount > 0;

  /// Get the effective model URL - uses remote URL for reliable loading
  String get effectiveModelUrl {
    // Use remote URL since local assets have path issues with model_viewer_plus
    // The remote server has all 9 urn models available
    return remoteModelUrl;
  }

  /// Get the remote model URL as fallback
  String get remoteModelUrl {
    if (modelUrl != null && modelUrl!.isNotEmpty) {
      return modelUrl!;
    }
    // Fallback to constructed URL
    return 'https://lms.histolab.icu/assets/models/${slug.toUpperCase()}-v1.glb';
  }

  Urn copyWith({
    String? id,
    String? slug,
    String? name,
    String? nameEn,
    String? description,
    String? descriptionEn,
    int? displayOrder,
    String? thumbnailUrl,
    String? modelUrl,
    int? motifCount,
    int? discoveredCount,
    int? learnedCount,
    int? masteredCount,
  }) {
    return Urn(
      id: id ?? this.id,
      slug: slug ?? this.slug,
      name: name ?? this.name,
      nameEn: nameEn ?? this.nameEn,
      description: description ?? this.description,
      descriptionEn: descriptionEn ?? this.descriptionEn,
      displayOrder: displayOrder ?? this.displayOrder,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      modelUrl: modelUrl ?? this.modelUrl,
      motifCount: motifCount ?? this.motifCount,
      discoveredCount: discoveredCount ?? this.discoveredCount,
      learnedCount: learnedCount ?? this.learnedCount,
      masteredCount: masteredCount ?? this.masteredCount,
    );
  }

  @override
  List<Object?> get props => [
        id,
        slug,
        name,
        nameEn,
        description,
        displayOrder,
        thumbnailUrl,
        modelUrl,
        motifCount,
        discoveredCount,
        learnedCount,
        masteredCount,
      ];

  @override
  String toString() => 'Urn(slug: $slug, name: $name, motifs: $motifCount)';
}

/// Motif entity representing a decorative pattern on an urn.
class Motif extends Equatable {
  final String id;
  final String urnId;
  final String meshName;
  final String name;
  final String? nameEn;
  final MotifCategory category;
  final MotifRarity rarity;
  final double posX;
  final double posY;
  final double posZ;
  final double boundingRadius;
  final String? thumbnailUrl;
  final String? description;
  final bool isDemo;
  final MotifStatus status;
  final int xpEarned;

  const Motif({
    required this.id,
    required this.urnId,
    required this.meshName,
    required this.name,
    this.nameEn,
    required this.category,
    required this.rarity,
    required this.posX,
    required this.posY,
    required this.posZ,
    required this.boundingRadius,
    this.thumbnailUrl,
    this.description,
    this.isDemo = false,
    this.status = MotifStatus.hidden,
    this.xpEarned = 0,
  });

  /// Check if motif has been discovered
  bool get isDiscovered => status != MotifStatus.hidden;

  /// Check if lesson has been completed
  bool get isLearned =>
      status == MotifStatus.learned || status == MotifStatus.mastered;

  /// Check if quiz has been passed
  bool get isMastered => status == MotifStatus.mastered;

  /// Check if motif has valid 3D position
  bool get hasValidPosition =>
      posX != 0.0 || posY != 0.0 || posZ != 0.0;

  /// Get 3D position as a list [x, y, z]
  List<double> get position => [posX, posY, posZ];

  Motif copyWith({
    String? id,
    String? urnId,
    String? meshName,
    String? name,
    String? nameEn,
    MotifCategory? category,
    MotifRarity? rarity,
    double? posX,
    double? posY,
    double? posZ,
    double? boundingRadius,
    String? thumbnailUrl,
    String? description,
    bool? isDemo,
    MotifStatus? status,
    int? xpEarned,
  }) {
    return Motif(
      id: id ?? this.id,
      urnId: urnId ?? this.urnId,
      meshName: meshName ?? this.meshName,
      name: name ?? this.name,
      nameEn: nameEn ?? this.nameEn,
      category: category ?? this.category,
      rarity: rarity ?? this.rarity,
      posX: posX ?? this.posX,
      posY: posY ?? this.posY,
      posZ: posZ ?? this.posZ,
      boundingRadius: boundingRadius ?? this.boundingRadius,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      description: description ?? this.description,
      isDemo: isDemo ?? this.isDemo,
      status: status ?? this.status,
      xpEarned: xpEarned ?? this.xpEarned,
    );
  }

  @override
  List<Object?> get props => [
        id,
        urnId,
        meshName,
        name,
        nameEn,
        category,
        rarity,
        posX,
        posY,
        posZ,
        boundingRadius,
        thumbnailUrl,
        description,
        isDemo,
        status,
        xpEarned,
      ];

  @override
  String toString() =>
      'Motif(name: $name, category: $category, status: $status)';
}

/// Urn detail entity with full motif list
class UrnDetail extends Equatable {
  final Urn urn;
  final List<Motif> motifs;

  const UrnDetail({
    required this.urn,
    required this.motifs,
  });

  /// Get motifs by status
  List<Motif> get discoveredMotifs =>
      motifs.where((m) => m.isDiscovered).toList();

  List<Motif> get hiddenMotifs =>
      motifs.where((m) => !m.isDiscovered).toList();

  List<Motif> get masteredMotifs =>
      motifs.where((m) => m.isMastered).toList();

  /// Get motif by ID
  Motif? getMotifById(String id) {
    try {
      return motifs.firstWhere((m) => m.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  List<Object?> get props => [urn, motifs];
}

/// Motif category enum matching backend
enum MotifCategory {
  thaoMoc('thao_moc', 'Thảo Mộc', 'Flora'),
  dongVat('dong_vat', 'Động Vật', 'Fauna'),
  diaLy('dia_ly', 'Địa Lý', 'Geography'),
  voBi('vo_bi', 'Võ Bị', 'Military'),
  thienVan('thien_van', 'Thiên Văn', 'Astronomy'),
  kienTruc('kien_truc', 'Kiến Trúc', 'Architecture'),
  nongNghiep('nong_nghiep', 'Nông Nghiệp', 'Agriculture'),
  linhThu('linh_thu', 'Linh Thú', 'Mythical Creatures'),
  giaoThuong('giao_thuong', 'Giao Thương', 'Trade');

  final String value;
  final String nameVi;
  final String nameEn;

  const MotifCategory(this.value, this.nameVi, this.nameEn);

  static MotifCategory fromString(String value) {
    return MotifCategory.values.firstWhere(
      (c) => c.value == value || c.name == value,
      orElse: () => MotifCategory.thaoMoc,
    );
  }
}

/// Motif rarity enum matching backend
enum MotifRarity {
  common('common', 'Phổ Thông', 'Common'),
  uncommon('uncommon', 'Không Phổ Biến', 'Uncommon'),
  rare('rare', 'Hiếm', 'Rare'),
  epic('epic', 'Sử Thi', 'Epic'),
  legendary('legendary', 'Huyền Thoại', 'Legendary');

  final String value;
  final String nameVi;
  final String nameEn;

  const MotifRarity(this.value, this.nameVi, this.nameEn);

  static MotifRarity fromString(String value) {
    return MotifRarity.values.firstWhere(
      (r) => r.value == value || r.name == value,
      orElse: () => MotifRarity.common,
    );
  }
}

/// Motif progress status enum
enum MotifStatus {
  hidden('hidden'),
  discovered('discovered'),
  learned('learned'),
  mastered('mastered');

  final String value;

  const MotifStatus(this.value);

  static MotifStatus fromString(String value) {
    return MotifStatus.values.firstWhere(
      (s) => s.value == value || s.name == value,
      orElse: () => MotifStatus.hidden,
    );
  }
}

/// Unlock result from discovery action
class UnlockResult extends Equatable {
  final Motif motif;
  final int xpEarned;
  final int totalXp;
  final List<String> badgesEarned;
  final bool isNewDiscovery;

  const UnlockResult({
    required this.motif,
    required this.xpEarned,
    required this.totalXp,
    this.badgesEarned = const [],
    this.isNewDiscovery = true,
  });

  @override
  List<Object?> get props => [motif, xpEarned, totalXp, badgesEarned, isNewDiscovery];
}
