import 'package:dartz/dartz.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/repositories/offline_first_repository.dart';
import '../../../../core/services/sync_service.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';

part 'lesson_repository.g.dart';

class LessonRepository extends OfflineFirstRepository<MotifDetailDto> {
  final ApiClient apiClient;
  final SyncService syncService;
  final _uuid = const Uuid();

  LessonRepository({
    required this.apiClient,
    required this.syncService,
    required super.networkInfo,
    required super.hiveStorage,
  });

  Future<Either<Failure, MotifDetailDto>> getMotifDetail(String motifId) async {
    return executeOfflineFirst<MotifDetailDto>(
      networkCall: () async {
        final response = await apiClient.get<Map<String, dynamic>>('/api/v1/motifs/$motifId');
        return MotifDetailDto.fromJson(_normalizeMotifPayload(response));
      },
      getCached: () async {
        final cached = hiveStorage.getCachedMotif(motifId);
        if (cached == null) return null;
        return MotifDetailDto.fromJson(_normalizeMotifPayload(cached));
      },
      saveCache: (motifDetail) async {
        await hiveStorage.cacheMotif(motifId, motifDetail.toJson());
      },
      operationName: 'GetMotifDetail($motifId)',
    );
  }

  Future<Either<Failure, CompleteLessonResponseDto>> completeLesson(String motifId) async {
    return executeWriteOperation<CompleteLessonResponseDto>(
      networkCall: () async {
        final response = await apiClient.post<Map<String, dynamic>>(
          ApiConstants.progressCompleteLesson,
          data: {'motif_id': motifId},
        );
        return CompleteLessonResponseDto.fromJson(response);
      },
      onSuccess: () async {
        await hiveStorage.updateProgressForMotif(motifId, {
          'completed': true,
          'completed_at': DateTime.now().toIso8601String(),
        });
      },
      operationName: 'CompleteLesson($motifId)',
    ).then((result) async {
      if (result.isLeft()) {
        await syncService.queueOperation(
          PendingSyncOperation(
            id: _uuid.v4(),
            type: SyncOperationType.lessonComplete,
            data: {'motif_id': motifId},
            timestamp: DateTime.now(),
          ),
        );
      }
      return result;
    });
  }

  Future<Either<Failure, QuizResultDto>> submitQuiz({
    required String motifId,
    required List<QuizAnswerDto> answers,
    int? timeTakenSeconds,
  }) async {
    final requestData = {
      'answers': answers.map((a) => a.toJson()).toList(),
      if (timeTakenSeconds != null) 'time_taken_seconds': timeTakenSeconds,
    };

    return executeWriteOperation<QuizResultDto>(
      networkCall: () async {
        final response = await apiClient.post<Map<String, dynamic>>(
          '/api/v1/motifs/$motifId/quiz/submit',
          data: requestData,
        );
        return QuizResultDto.fromJson(response);
      },
      onSuccess: () async {
        await hiveStorage.clearQuizProgress(motifId);
      },
      operationName: 'SubmitQuiz($motifId)',
    ).then((result) async {
      if (result.isLeft()) {
        await syncService.queueOperation(
          PendingSyncOperation(
            id: _uuid.v4(),
            type: SyncOperationType.quizSubmit,
            data: {
              'motif_id': motifId,
              ...requestData,
            },
            timestamp: DateTime.now(),
          ),
        );
      }
      return result;
    });
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

      if (normalizedLesson['audio_url'] == null && normalizedLesson['audio_narration_url'] != null) {
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
    if (item is String) return item;
    if (item is Map) {
      final candidate = item['url'] ?? item['path'] ?? item['image_url'];
      if (candidate is String) return candidate;
    }
    return null;
  }
}

@Riverpod(keepAlive: true)
LessonRepository lessonRepository(LessonRepositoryRef ref) {
  return LessonRepository(
    apiClient: ref.watch(apiClientProvider),
    syncService: ref.watch(syncServiceProvider),
    networkInfo: ref.watch(networkInfoProvider),
    hiveStorage: ref.watch(hiveStorageProvider),
  );
}

@riverpod
Future<MotifDetailDto> motifDetailOfflineFirst(
  MotifDetailOfflineFirstRef ref,
  String motifId,
) async {
  final repository = ref.watch(lessonRepositoryProvider);
  final result = await repository.getMotifDetail(motifId);

  return result.fold(
    (failure) => throw Exception(failure.message),
    (motifDetail) => motifDetail,
  );
}

@riverpod
class LessonCompletionOfflineFirst extends _$LessonCompletionOfflineFirst {
  @override
  FutureOr<CompleteLessonResponseDto?> build() => null;

  Future<CompleteLessonResponseDto?> completeLesson(String motifId) async {
    state = const AsyncLoading();

    final repository = ref.read(lessonRepositoryProvider);
    final result = await repository.completeLesson(motifId);

    return result.fold(
      (failure) {
        state = AsyncError(Exception(failure.message), StackTrace.current);
        return null;
      },
      (response) {
        state = AsyncData(response);
        ref.invalidate(motifDetailOfflineFirstProvider(motifId));
        return response;
      },
    );
  }
}

@riverpod
class QuizSubmissionOfflineFirst extends _$QuizSubmissionOfflineFirst {
  @override
  FutureOr<QuizResultDto?> build() => null;

  Future<QuizResultDto?> submitQuiz({
    required String motifId,
    required List<QuizAnswerDto> answers,
    int? timeTakenSeconds,
  }) async {
    state = const AsyncLoading();

    final repository = ref.read(lessonRepositoryProvider);
    final result = await repository.submitQuiz(
      motifId: motifId,
      answers: answers,
      timeTakenSeconds: timeTakenSeconds,
    );

    return result.fold(
      (failure) {
        state = AsyncError(Exception(failure.message), StackTrace.current);
        return null;
      },
      (quizResult) {
        state = AsyncData(quizResult);
        if (quizResult.passed) {
          ref.invalidate(motifDetailOfflineFirstProvider(motifId));
        }
        return quizResult;
      },
    );
  }

  void clearResult() {
    state = const AsyncData(null);
  }
}

