import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

/// Model for practice urn data
class PracticeUrn {
  final String id;
  final String name;
  final String? thumbnailUrl;
  final int motifCount;
  final double progress; // 0.0 to 1.0

  PracticeUrn({
    required this.id,
    required this.name,
    this.thumbnailUrl,
    required this.motifCount,
    required this.progress,
  });

  factory PracticeUrn.fromJson(Map<String, dynamic> json) {
    return PracticeUrn(
      id: json['id']?.toString() ?? json['slug']?.toString() ?? '',
      name: json['name']?.toString() ?? 'Unknown',
      thumbnailUrl: json['thumbnail_url']?.toString(),
      motifCount: (json['motif_count'] as num?)?.toInt() ?? 0,
      progress: 0.0, // Will be calculated based on user progress
    );
  }
}

/// Provider to fetch urns for practice screen
final practiceUrnsProvider = FutureProvider<List<PracticeUrn>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);

  try {
    debugPrint('🔍 [PracticeUrns] Fetching urns from API...');
    final response = await apiClient.get<List<dynamic>>(
      '/api/v1/urns',
      parser: (json) => json as List<dynamic>,
    );

    debugPrint('✅ [PracticeUrns] API response received: ${response.length} urns');
    debugPrint('📝 [PracticeUrns] Raw response data: $response');

    final urns = response
        .map((item) {
          final urn = PracticeUrn.fromJson(item as Map<String, dynamic>);
          debugPrint('🏺 [PracticeUrns] Parsed urn: ${urn.name}, thumbnailUrl: ${urn.thumbnailUrl}');
          return urn;
        })
        .toList();

    return urns;
  } catch (e, stackTrace) {
    debugPrint('❌ [PracticeUrns] Error fetching urns: $e');
    debugPrint('📚 [PracticeUrns] Stack trace: $stackTrace');
    debugPrint('⚠️ [PracticeUrns] Falling back to mock data');
    // Return mock data as fallback
    return _getMockUrns();
  }
});

List<PracticeUrn> _getMockUrns() {
  return [
    PracticeUrn(
      id: 'cao-dinh',
      name: 'Cao Đỉnh',
      thumbnailUrl: 'https://lms.histolab.icu/assets/ban-duc-noi/CAO%20DINH/CAO%20DINH.jpg',
      motifCount: 18,
      progress: 0.0,
    ),
    PracticeUrn(
      id: 'nhan-dinh',
      name: 'Nhân Đỉnh',
      thumbnailUrl: 'https://lms.histolab.icu/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg',
      motifCount: 15,
      progress: 0.0,
    ),
    PracticeUrn(
      id: 'chuong-dinh',
      name: 'Chương Đỉnh',
      thumbnailUrl: 'https://lms.histolab.icu/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg',
      motifCount: 12,
      progress: 0.0,
    ),
  ];
}

