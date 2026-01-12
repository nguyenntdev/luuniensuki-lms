import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../lesson/presentation/providers/motif_detail_provider.dart';

part 'quiz_provider.g.dart';

/// Provider for fetching quiz questions for a motif.
@riverpod
Future<QuizResponseDto> quiz(QuizRef ref, String motifId) async {
  final apiClient = ref.watch(apiClientProvider);

  final result = await apiClient.get<QuizResponseDto>(
    '/api/v1/motifs/$motifId/quiz',
    parser: (json) => QuizResponseDto.fromJson(json as Map<String, dynamic>),
  );

  return result;
}

/// Provider for submitting quiz answers.
@riverpod
class QuizSubmission extends _$QuizSubmission {
  @override
  FutureOr<QuizResultDto?> build() => null;

  Future<QuizResultDto?> submit({
    required String motifId,
    required Map<String, String> answers,
    int? timeSpentSeconds,
  }) async {
    state = const AsyncLoading();

    try {
      final apiClient = ref.read(apiClientProvider);

      // Convert answers map to list of QuizAnswerDto
      final answersList = answers.entries
          .map((e) => {
                'question_id': e.key,
                'answer': e.value,
              })
          .toList();

      final result = await apiClient.post<QuizResultDto>(
        '/api/v1/motifs/$motifId/quiz/submit',
        data: {
          'answers': answersList,
          if (timeSpentSeconds != null) 'time_taken_seconds': timeSpentSeconds,
        },
        parser: (json) => QuizResultDto.fromJson(json as Map<String, dynamic>),
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

/// Provider for quiz attempt history.
@riverpod
Future<List<QuizAttemptDto>> quizHistory(
  QuizHistoryRef ref,
  String motifId,
) async {
  final apiClient = ref.watch(apiClientProvider);

  final result = await apiClient.get<List<QuizAttemptDto>>(
    '/api/v1/motifs/$motifId/quiz/history',
    parser: (json) => (json as List)
        .map((e) => QuizAttemptDto.fromJson(e as Map<String, dynamic>))
        .toList(),
  );

  return result;
}

/// Quiz attempt DTO for history
class QuizAttemptDto {
  final String id;
  final String motifId;
  final int score;
  final int percentage;
  final bool passed;
  final String attemptedAt;
  final int? timeTakenSeconds;

  QuizAttemptDto({
    required this.id,
    required this.motifId,
    required this.score,
    required this.percentage,
    required this.passed,
    required this.attemptedAt,
    this.timeTakenSeconds,
  });

  factory QuizAttemptDto.fromJson(Map<String, dynamic> json) {
    return QuizAttemptDto(
      id: json['id'] as String,
      motifId: json['motif_id'] as String,
      score: json['score'] as int,
      percentage: json['percentage'] as int,
      passed: json['passed'] as bool,
      attemptedAt: json['attempted_at'] as String,
      timeTakenSeconds: json['time_taken_seconds'] as int?,
    );
  }

  String? get formattedTime {
    if (timeTakenSeconds == null) return null;
    final minutes = (timeTakenSeconds! ~/ 60).toString().padLeft(2, '0');
    final seconds = (timeTakenSeconds! % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}
