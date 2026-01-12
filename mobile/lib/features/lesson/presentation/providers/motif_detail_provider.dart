import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';

part 'motif_detail_provider.g.dart';

/// Provider for fetching motif detail with lesson and progress data.
@riverpod
Future<MotifDetailDto> motifDetail(MotifDetailRef ref, String motifId) async {
  final apiClient = ref.watch(apiClientProvider);

  final result = await apiClient.get<MotifDetailDto>(
    '/api/v1/motifs/$motifId',
    parser: (json) => MotifDetailDto.fromJson(json as Map<String, dynamic>),
  );

  return result;
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
