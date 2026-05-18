import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/storage/hive_storage.dart';
import '../../../urn_viewer/data/models/urn_dtos.dart';
import '../../../lesson/presentation/providers/motif_detail_provider.dart';
import '../../data/models/quiz_progress.dart';

part 'quiz_provider.g.dart';

/// Quiz state data for a specific quiz session
class QuizStateData {
  final int currentQuestionIndex;
  final Map<String, String> answers;
  final Map<String, bool> incorrectAnswers;
  final DateTime startTime;
  final bool hasSavedProgress;
  final QuizProgress? savedProgress;

  const QuizStateData({
    required this.currentQuestionIndex,
    required this.answers,
    required this.incorrectAnswers,
    required this.startTime,
    required this.hasSavedProgress,
    this.savedProgress,
  });

  QuizStateData copyWith({
    int? currentQuestionIndex,
    Map<String, String>? answers,
    Map<String, bool>? incorrectAnswers,
    DateTime? startTime,
    bool? hasSavedProgress,
    QuizProgress? savedProgress,
  }) {
    return QuizStateData(
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      answers: answers ?? this.answers,
      incorrectAnswers: incorrectAnswers ?? this.incorrectAnswers,
      startTime: startTime ?? this.startTime,
      hasSavedProgress: hasSavedProgress ?? this.hasSavedProgress,
      savedProgress: savedProgress ?? this.savedProgress,
    );
  }
}

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

      // Clear saved progress on successful submission
      final storage = ref.read(hiveStorageProvider);
      await storage.clearQuizProgress(motifId);

      return result;
    } catch (e, s) {
      state = AsyncError(e, s);
      return null;
    }
  }
}

/// Provider for quiz state management with auto-save
@riverpod
class QuizState extends _$QuizState {
  @override
  QuizStateData build(String motifId) {
    // Try to load saved progress
    final storage = ref.read(hiveStorageProvider);
    final savedProgress = storage.getQuizProgress(motifId);

    if (savedProgress != null) {
      try {
        final progress = QuizProgress.fromJson(savedProgress);
        // Return saved state if valid
        if (progress.isValid()) {
          return QuizStateData(
            currentQuestionIndex: progress.currentQuestionIndex,
            answers: Map<String, String>.from(progress.answers),
            incorrectAnswers: Map<String, bool>.from(progress.incorrectAnswers),
            startTime: DateTime.now().subtract(
              Duration(seconds: progress.timeSpentSeconds),
            ),
            hasSavedProgress: true,
            savedProgress: progress,
          );
        }
      } catch (e) {
        // Invalid saved data, ignore
      }
    }

    // Return fresh state
    return QuizStateData(
      currentQuestionIndex: 0,
      answers: {},
      incorrectAnswers: {},
      startTime: DateTime.now(),
      hasSavedProgress: false,
    );
  }

  /// Update current question index
  void setQuestionIndex(int index) {
    state = state.copyWith(currentQuestionIndex: index);
    _autoSave();
  }

  /// Set answer for a question
  void setAnswer(String questionId, String answer) {
    final newAnswers = Map<String, String>.from(state.answers);
    newAnswers[questionId] = answer;
    state = state.copyWith(answers: newAnswers);
    _autoSave();
  }

  /// Mark answer as incorrect
  void markIncorrect(String questionId) {
    final newIncorrect = Map<String, bool>.from(state.incorrectAnswers);
    newIncorrect[questionId] = true;
    state = state.copyWith(incorrectAnswers: newIncorrect);
    _autoSave();
  }

  /// Start fresh quiz (clear saved progress)
  void startFresh(QuizResponseDto quiz) {
    final storage = ref.read(hiveStorageProvider);
    storage.clearQuizProgress(motifId);

    state = QuizStateData(
      currentQuestionIndex: 0,
      answers: {},
      incorrectAnswers: {},
      startTime: DateTime.now(),
      hasSavedProgress: false,
    );
  }

  /// Resume from saved progress
  void resumeProgress() {
    state = state.copyWith(hasSavedProgress: false);
  }

  /// Auto-save current state
  void _autoSave() {
    final storage = ref.read(hiveStorageProvider);

    // Get quiz data to create hash
    final quizAsync = ref.read(quizProvider(motifId));
    quizAsync.whenData((quiz) {
      final questionsHash = QuizProgress.createQuestionsHash(
        quiz.questions.map((q) => {'id': q.id}).toList(),
      );

      final progress = QuizProgress(
        motifId: motifId,
        motifName: quiz.motifName,
        currentQuestionIndex: state.currentQuestionIndex,
        answers: state.answers,
        incorrectAnswers: state.incorrectAnswers,
        timeSpentSeconds: DateTime.now().difference(state.startTime).inSeconds,
        savedAt: DateTime.now(),
        questionsHash: questionsHash,
      );

      storage.saveQuizProgress(motifId, progress.toStorage());
    });
  }

  /// Clear saved progress
  void clearProgress() {
    final storage = ref.read(hiveStorageProvider);
    storage.clearQuizProgress(motifId);
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
