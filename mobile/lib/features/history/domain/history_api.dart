import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';

/// A canonical historical entity (urn / relief / person / place ...).
class HistoryEntity {
  const HistoryEntity({
    required this.id,
    required this.entityType,
    required this.slug,
    required this.nameVi,
    this.nameEn,
    this.summaryVi,
    this.publicationStatus,
  });

  final String id;
  final String entityType;
  final String slug;
  final String nameVi;
  final String? nameEn;
  final String? summaryVi;
  final String? publicationStatus;

  factory HistoryEntity.fromJson(Map<String, dynamic> json) {
    return HistoryEntity(
      id: json['id']?.toString() ?? '',
      entityType: json['entity_type']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      nameVi: json['name_vi']?.toString() ?? '',
      nameEn: json['name_en']?.toString(),
      summaryVi: json['summary_vi']?.toString(),
      publicationStatus: json['publication_status']?.toString(),
    );
  }
}

/// A block-based history story (public, published only).
class HistoryStory {
  const HistoryStory({
    required this.id,
    required this.slug,
    required this.titleVi,
    this.summaryVi,
    this.featured = false,
  });

  final String id;
  final String slug;
  final String titleVi;
  final String? summaryVi;
  final bool featured;

  factory HistoryStory.fromJson(Map<String, dynamic> json) {
    return HistoryStory(
      id: json['id']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      titleVi: json['title_vi']?.toString() ?? '',
      summaryVi: json['summary_vi']?.toString(),
      featured: json['featured'] == true,
    );
  }
}

/// Client for the public History-First API surface.
class HistoryApi {
  HistoryApi(this._client);

  final ApiClient _client;

  /// List entities (e.g. urns or reliefs) from the public endpoint.
  Future<List<HistoryEntity>> listEntities({
    String? entityType,
    int limit = 100,
  }) async {
    final data = await _client.get<Map<String, dynamic>>(
      '/api/v1/history/entities',
      queryParameters: {
        if (entityType != null && entityType.isNotEmpty)
          'entity_type': entityType,
        'limit': limit,
      },
    );
    final items = data['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(HistoryEntity.fromJson)
        .toList();
  }

  /// List published history stories.
  Future<List<HistoryStory>> listStories() async {
    final data = await _client.get<Map<String, dynamic>>(
      '/api/v1/history/stories',
    );
    final items = data['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(HistoryStory.fromJson)
        .toList();
  }

  /// Search historical entities by name/alias.
  Future<List<HistoryEntity>> search(String query, {int limit = 20}) async {
    final data = await _client.get<Map<String, dynamic>>(
      '/api/v1/history/search',
      queryParameters: {'q': query, 'limit': limit},
    );
    final items = data['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(HistoryEntity.fromJson)
        .toList();
  }
}

final historyApiProvider = Provider<HistoryApi>((ref) {
  return HistoryApi(ref.watch(apiClientProvider));
});

/// FutureProvider for the 9 canonical urns (no auth needed).
final historyUrnsProvider = FutureProvider<List<HistoryEntity>>((ref) async {
  return ref.watch(historyApiProvider).listEntities(entityType: 'urn');
});

/// FutureProvider for published history stories.
final historyStoriesProvider = FutureProvider<List<HistoryStory>>((ref) async {
  return ref.watch(historyApiProvider).listStories();
});
