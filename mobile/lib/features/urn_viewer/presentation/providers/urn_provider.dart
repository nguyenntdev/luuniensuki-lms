import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/errors/exceptions.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/network_info.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../data/models/urn_dtos.dart';
import '../../data/models/urn_mappers.dart';
import '../../domain/entities/urn.dart';

part 'urn_provider.g.dart';

/// Provider for fetching list of all urns
@riverpod
Future<List<Urn>> urns(Ref ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  // Try to get from cache first if offline
  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) {
      return cached.map((json) => UrnToJson.fromJson(json)).toList();
    }
    throw const NetworkException('No internet connection');
  }

  try {
    final response = await apiClient.get<List<dynamic>>(
      ApiConstants.urns,
    );

    final urns = (response as List)
        .map((json) => UrnListItemDto.fromJson(json as Map<String, dynamic>))
        .map((dto) => dto.toEntity())
        .toList();

    // Cache the results
    await hiveStorage.cacheUrns(
      urns.map((u) => u.toJson()).toList(),
    );

    return urns;
  } on ServerException catch (e) {
    throw ServerFailure(e.message, code: e.code, statusCode: e.statusCode);
  } catch (e) {
    // Try cache on error
    final cached = hiveStorage.getCachedUrns();
    if (cached != null) {
      return cached.map((json) => UrnToJson.fromJson(json)).toList();
    }
    rethrow;
  }
}

/// Provider for fetching urn detail with motifs
@riverpod
Future<UrnDetail> urnDetail(Ref ref, String slug) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  // Try to get user progress for this specific urn
  Map<String, UserProgressDto>? progressByMotifId;
  try {
    final progressResponse = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.urnProgress(slug),
    );

    debugPrint('Urn progress response: $progressResponse');

    // Parse the response format: { urn_id, urn_slug, motifs: [...] }
    final motifsList = progressResponse['motifs'] as List<dynamic>?;
    if (motifsList != null) {
      progressByMotifId = {};
      for (final motifProgress in motifsList) {
        final mp = motifProgress as Map<String, dynamic>;
        final motifId = mp['motif_id'] as String;

        // Parse datetime fields (they come as ISO strings from FastAPI)
        String? discoveredAt = mp['discovered_at']?.toString();
        String? learnedAt = mp['learned_at']?.toString();
        String? masteredAt = mp['mastered_at']?.toString();

        progressByMotifId[motifId] = UserProgressDto(
          id: motifId,
          userId: '',
          motifId: motifId,
          status: mp['status'] as String,
          discoveredAt: discoveredAt,
          learnedAt: learnedAt,
          masteredAt: masteredAt,
          xpEarned: (mp['xp_earned'] as num?)?.toInt() ?? 0,
          quizBestScore: (mp['quiz_best_score'] as num?)?.toInt(),
        );

        debugPrint('Parsed progress for motif $motifId: ${mp['status']}');
      }
      debugPrint('Total progress entries parsed: ${progressByMotifId.length}');
    } else {
      debugPrint('No motifs list in progress response');
    }
  } catch (e, stackTrace) {
    debugPrint('Failed to fetch urn progress: $e');
    debugPrint('Stack trace: $stackTrace');
  }

  // Try to get from cache first if offline
  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedUrn(slug);
    if (cached != null) {
      final dto = UrnDetailResponseDto.fromJson(cached);
      return dto.toEntity(progressByMotifId: progressByMotifId);
    }
    throw const NetworkException('No internet connection');
  }

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.urn(slug),
    );

    final dto = UrnDetailResponseDto.fromJson(response);
    final urnDetail = dto.toEntity(progressByMotifId: progressByMotifId);

    // Cache the result
    await hiveStorage.cacheUrn(slug, response);

    return urnDetail;
  } on ServerException catch (e) {
    throw ServerFailure(e.message, code: e.code, statusCode: e.statusCode);
  } catch (e) {
    // Try cache on error
    final cached = hiveStorage.getCachedUrn(slug);
    if (cached != null) {
      final dto = UrnDetailResponseDto.fromJson(cached);
      return dto.toEntity(progressByMotifId: progressByMotifId);
    }
    rethrow;
  }
}

/// Provider for fetching a single motif detail
@riverpod
Future<Motif> motifDetail(Ref ref, String motifId) async {
  final apiClient = ref.watch(apiClientProvider);
  final hiveStorage = ref.watch(hiveStorageProvider);
  final networkInfo = ref.watch(networkInfoProvider);

  // Try to get from cache first if offline
  if (!await networkInfo.isConnected) {
    final cached = hiveStorage.getCachedMotif(motifId);
    if (cached != null) {
      final dto = MotifDetailDto.fromJson(cached);
      return dto.toEntity();
    }
    throw const NetworkException('No internet connection');
  }

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.motif(motifId),
    );

    final dto = MotifDetailDto.fromJson(response);
    final motif = dto.toEntity();

    // Cache the result
    await hiveStorage.cacheMotif(motifId, response);

    return motif;
  } on ServerException catch (e) {
    throw ServerFailure(e.message, code: e.code, statusCode: e.statusCode);
  } catch (e) {
    // Try cache on error
    final cached = hiveStorage.getCachedMotif(motifId);
    if (cached != null) {
      final dto = MotifDetailDto.fromJson(cached);
      return dto.toEntity();
    }
    rethrow;
  }
}

/// State for discovery operations
class DiscoveryState {
  final bool isLoading;
  final UnlockResult? lastResult;
  final String? error;

  const DiscoveryState({
    this.isLoading = false,
    this.lastResult,
    this.error,
  });

  DiscoveryState copyWith({
    bool? isLoading,
    UnlockResult? lastResult,
    String? error,
  }) {
    return DiscoveryState(
      isLoading: isLoading ?? this.isLoading,
      lastResult: lastResult ?? this.lastResult,
      error: error,
    );
  }
}

/// Notifier for handling motif discovery/unlock actions
@riverpod
class DiscoveryNotifier extends _$DiscoveryNotifier {
  @override
  DiscoveryState build() {
    return const DiscoveryState();
  }

  /// Unlock/discover a motif
  Future<UnlockResult?> unlockMotif(String motifId) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final apiClient = ref.read(apiClientProvider);

      final response = await apiClient.post<Map<String, dynamic>>(
        ApiConstants.progressUnlock,
        data: {'motif_id': motifId},
      );

      final unlockDto = UnlockResponseDto.fromJson(response);

      // Get the motif to create the result
      final motifResponse = await apiClient.get<Map<String, dynamic>>(
        ApiConstants.motif(motifId),
      );
      final motifDto = MotifDetailDto.fromJson(motifResponse);
      final motif = motifDto.toEntity();

      final result = unlockDto.toEntity(motif);

      state = state.copyWith(
        isLoading: false,
        lastResult: result,
      );

      // Invalidate related providers to refresh data
      ref.invalidate(urnsProvider);
      // Note: urnDetailProvider needs slug, so we can't invalidate it directly here

      return result;
    } on ServerException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Đã xảy ra lỗi: $e',
      );
      return null;
    }
  }

  /// Complete lesson for a motif
  Future<UnlockResult?> completeLesson(String motifId) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final apiClient = ref.read(apiClientProvider);

      final response = await apiClient.post<Map<String, dynamic>>(
        ApiConstants.progressCompleteLesson(motifId),
      );

      final completeDto = CompleteLessonResponseDto.fromJson(response);

      // Get the motif to create the result
      final motifResponse = await apiClient.get<Map<String, dynamic>>(
        ApiConstants.motif(motifId),
      );
      final motifDto = MotifDetailDto.fromJson(motifResponse);
      final motif = motifDto.toEntity();

      final result = UnlockResult(
        motif: motif,
        xpEarned: completeDto.xpEarned,
        totalXp: completeDto.totalXp,
        badgesEarned: [], // TODO: Backend doesn't return badges yet
        isNewDiscovery: false,
      );

      state = state.copyWith(
        isLoading: false,
        lastResult: result,
      );

      // Invalidate related providers
      ref.invalidate(urnsProvider);

      return result;
    } on ServerException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Đã xảy ra lỗi: $e',
      );
      return null;
    }
  }

  /// Clear the last result
  void clearResult() {
    state = state.copyWith(lastResult: null, error: null);
  }
}

/// Provider for quiz questions
@riverpod
Future<List<QuizQuestionDto>> quizQuestions(Ref ref, String motifId) async {
  final apiClient = ref.watch(apiClientProvider);

  try {
    final response = await apiClient.get<Map<String, dynamic>>(
      ApiConstants.motifQuiz(motifId),
    );

    final quizResponse = QuizResponseDto.fromJson(response);
    return quizResponse.questions;
  } on ServerException catch (e) {
    throw ServerFailure(e.message, code: e.code, statusCode: e.statusCode);
  }
}

/// State for quiz submission
class QuizSubmissionState {
  final bool isSubmitting;
  final QuizResultDto? result;
  final String? error;

  const QuizSubmissionState({
    this.isSubmitting = false,
    this.result,
    this.error,
  });

  QuizSubmissionState copyWith({
    bool? isSubmitting,
    QuizResultDto? result,
    String? error,
  }) {
    return QuizSubmissionState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      result: result ?? this.result,
      error: error,
    );
  }
}

/// Notifier for quiz submission
@riverpod
class QuizSubmissionNotifier extends _$QuizSubmissionNotifier {
  @override
  QuizSubmissionState build() {
    return const QuizSubmissionState();
  }

  /// Submit quiz answers
  Future<QuizResultDto?> submitQuiz({
    required String motifId,
    required List<QuizAnswerDto> answers,
    int? timeTakenSeconds,
  }) async {
    state = state.copyWith(isSubmitting: true, error: null);

    try {
      final apiClient = ref.read(apiClientProvider);

      final request = QuizSubmitRequestDto(
        answers: answers,
        timeTakenSeconds: timeTakenSeconds,
      );

      final response = await apiClient.post<Map<String, dynamic>>(
        ApiConstants.motifQuizSubmit(motifId),
        data: request.toJson(),
      );

      final result = QuizResultDto.fromJson(response);

      state = state.copyWith(
        isSubmitting: false,
        result: result,
      );

      // Invalidate related providers if quiz was passed
      if (result.passed) {
        ref.invalidate(urnsProvider);
        ref.invalidate(motifDetailProvider(motifId));
      }

      return result;
    } on ServerException catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: 'Đã xảy ra lỗi: $e',
      );
      return null;
    }
  }

  /// Clear the result
  void clearResult() {
    state = state.copyWith(result: null, error: null);
  }
}

/// Extension to add toJson to QuizSubmitRequestDto
extension QuizSubmitRequestDtoToJson on QuizSubmitRequestDto {
  Map<String, dynamic> toJson() {
    return {
      'answers': answers.map((a) => a.toJson()).toList(),
      if (timeTakenSeconds != null) 'time_taken_seconds': timeTakenSeconds,
    };
  }
}

extension QuizAnswerDtoToJson on QuizAnswerDto {
  Map<String, dynamic> toJson() {
    return {
      'question_id': questionId,
      'answer': answer,
    };
  }
}
