import 'package:freezed_annotation/freezed_annotation.dart';

part 'quiz_progress.freezed.dart';
part 'quiz_progress.g.dart';

/// Saved quiz progress for auto-save/resume functionality
@freezed
class QuizProgress with _$QuizProgress {
  const factory QuizProgress({
    required String motifId,
    required String motifName,
    required int currentQuestionIndex,
    required Map<String, String> answers,
    required Map<String, bool> incorrectAnswers,
    required int timeSpentSeconds,
    required DateTime savedAt,
    // Quiz content hash for validation
    required String questionsHash,
  }) = _QuizProgress;

  const QuizProgress._();

  factory QuizProgress.fromJson(Map<String, dynamic> json) =>
      _$QuizProgressFromJson(json);

  /// Convert to storage format
  Map<String, dynamic> toStorage() => toJson();

  /// Check if progress is still valid (not too old)
  bool isValid({Duration maxAge = const Duration(days: 7)}) {
    return DateTime.now().difference(savedAt) < maxAge;
  }

  /// Create a hash of questions for validation
  static String createQuestionsHash(List<dynamic> questions) {
    // Simple hash based on question IDs and order
    return questions
        .map((q) => q is Map ? q['id']?.toString() ?? '' : '')
        .join('_')
        .hashCode
        .toString();
  }
}

