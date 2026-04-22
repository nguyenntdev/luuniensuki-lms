import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';

part 'motif_detail_provider.g.dart';

/// Provider for fetching motif detail with lesson and progress data.
@riverpod
Future<MotifDetailDto> motifDetail(MotifDetailRef ref, String motifId) async {
  final apiClient = ref.watch(apiClientProvider);

  final result = await apiClient.get<Map<String, dynamic>>(
    '/api/v1/motifs/$motifId',
    parser: (json) => json as Map<String, dynamic>,
  );

  return MotifDetailDto.fromJson(_normalizeMotifPayload(result));
}

Map<String, dynamic> _normalizeMotifPayload(Map<String, dynamic> json) {
  final lesson = json['lesson'];
  if (lesson is Map<String, dynamic>) {
    final normalizedLesson = Map<String, dynamic>.from(lesson);
    final additionalImages = normalizedLesson['additional_images'];
    final existingImages = normalizedLesson['images'];

    if (existingImages == null && additionalImages != null) {
      final images = _coerceImageList(additionalImages);
      if (images != null) {
        normalizedLesson['images'] = images;
      }
    }

    if (normalizedLesson['audio_url'] == null &&
        normalizedLesson['audio_narration_url'] != null) {
      normalizedLesson['audio_url'] = normalizedLesson['audio_narration_url'];
    }

    json = {
      ...json,
      'lesson': normalizedLesson,
    };
  }

  return json;
}

List<String>? _coerceImageList(dynamic rawImages) {
  if (rawImages is! List) return null;

  final urls = <String>[];
  for (final item in rawImages) {
    final url = _coerceImageUrl(item);
    if (url != null && url.trim().isNotEmpty) {
      urls.add(url.trim());
    }
  }

  return urls.isEmpty ? null : urls;
}

String? _coerceImageUrl(dynamic item) {
  if (item is String) {
    return item;
  }
  if (item is Map) {
    final candidate = item['url'] ?? item['path'] ?? item['image_url'];
    if (candidate is String) {
      return candidate;
    }
  }
  return null;
}

/// Provider for completing a lesson.
@riverpod
class LessonCompletion extends _$LessonCompletion {
  @override
  FutureOr<CompleteLessonResponseDto?> build() => null;

  Future<CompleteLessonResponseDto?> completeLesson(String motifId) async {
    state = const AsyncLoading();

    try {
      final apiClient = ref.read(apiClientProvider);

      final result = await apiClient.post<CompleteLessonResponseDto>(
        '/api/v1/progress/complete-lesson',
        data: {'motif_id': motifId},
        parser: (json) =>
            CompleteLessonResponseDto.fromJson(json as Map<String, dynamic>),
      );

      state = AsyncData(result);

      // Invalidate motif detail to refresh progress
      ref.invalidate(motifDetailProvider(motifId));

      return result;
    } catch (e, s) {
      state = AsyncError(e, s);
      return null;
    }
  }
}
