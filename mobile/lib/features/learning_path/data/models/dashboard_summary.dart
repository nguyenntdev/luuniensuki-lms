class DashboardCollectionStats {
  final int total;
  final int discovered;
  final int learned;
  final int mastered;

  const DashboardCollectionStats({
    required this.total,
    required this.discovered,
    required this.learned,
    required this.mastered,
  });

  factory DashboardCollectionStats.fromJson(Map<String, dynamic> json) {
    return DashboardCollectionStats(
      total: json['total'] as int? ?? 0,
      discovered: json['discovered'] as int? ?? 0,
      learned: json['learned'] as int? ?? 0,
      mastered: json['mastered'] as int? ?? 0,
    );
  }
}

class DashboardStreak {
  final int currentStreak;
  final int longestStreak;
  final int streakFreezes;

  const DashboardStreak({
    required this.currentStreak,
    required this.longestStreak,
    required this.streakFreezes,
  });

  factory DashboardStreak.fromJson(Map<String, dynamic> json) {
    return DashboardStreak(
      currentStreak: json['current_streak'] as int? ?? 0,
      longestStreak: json['longest_streak'] as int? ?? 0,
      streakFreezes: json['streak_freezes'] as int? ?? 0,
    );
  }
}

class DashboardPathMotif {
  final String id;
  final String name;
  final String? nameEn;
  final int? displayOrder;
  final String status;
  final String? category;
  final String? thumbnailUrl;
  final String? silhouetteUrl;

  const DashboardPathMotif({
    required this.id,
    required this.name,
    required this.status,
    this.nameEn,
    this.displayOrder,
    this.category,
    this.thumbnailUrl,
    this.silhouetteUrl,
  });

  factory DashboardPathMotif.fromJson(Map<String, dynamic> json) {
    return DashboardPathMotif(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      nameEn: json['name_en']?.toString(),
      displayOrder: json['display_order'] as int?,
      status: json['status']?.toString() ?? 'hidden',
      category: json['category']?.toString(),
      thumbnailUrl: json['thumbnail_url']?.toString(),
      silhouetteUrl: json['silhouette_url']?.toString(),
    );
  }

  bool get isLearned => status == 'learned';
  bool get isMastered => status == 'mastered';
  bool get isDiscovered => status == 'discovered';
}

class DashboardSummary {
  final DashboardCollectionStats collectionStats;
  final DashboardStreak streak;
  final List<DashboardPathMotif> pathMotifs;

  const DashboardSummary({
    required this.collectionStats,
    required this.streak,
    required this.pathMotifs,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    final collectionStats = json['collection_stats'] is Map<String, dynamic>
        ? DashboardCollectionStats.fromJson(
            json['collection_stats'] as Map<String, dynamic>,
          )
        : const DashboardCollectionStats(
            total: 0,
            discovered: 0,
            learned: 0,
            mastered: 0,
          );

    final streak = json['streak'] is Map<String, dynamic>
        ? DashboardStreak.fromJson(json['streak'] as Map<String, dynamic>)
        : const DashboardStreak(
            currentStreak: 0,
            longestStreak: 0,
            streakFreezes: 0,
          );

    final rawPath = json['path_motifs'];
    final pathMotifs = <DashboardPathMotif>[];
    if (rawPath is List) {
      for (final item in rawPath) {
        if (item is Map<String, dynamic>) {
          final motif = DashboardPathMotif.fromJson(item);
          if (motif.id.isNotEmpty) {
            pathMotifs.add(motif);
          }
        }
      }
    }

    pathMotifs.sort((a, b) {
      final orderA = a.displayOrder ?? 9999;
      final orderB = b.displayOrder ?? 9999;
      if (orderA != orderB) return orderA.compareTo(orderB);
      return a.name.compareTo(b.name);
    });

    return DashboardSummary(
      collectionStats: collectionStats,
      streak: streak,
      pathMotifs: pathMotifs,
    );
  }
}
