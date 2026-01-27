import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'quiz_models.freezed.dart';

/// Quiz question entity
@freezed
class QuizQuestion with _$QuizQuestion {
  const factory QuizQuestion({
    required String id,
    required String motifId,
    required QuestionType questionType,
    required String questionText,
    required String correctAnswer,
    @Default([]) List<String> options,
    String? imageUrl,
    String? explanation,
    @Default(0) int displayOrder,
  }) = _QuizQuestion;

  const QuizQuestion._();

  /// Check if question has image
  bool get hasImage => imageUrl != null && imageUrl!.isNotEmpty;

  /// Check if question has explanation
  bool get hasExplanation => explanation != null && explanation!.isNotEmpty;

  /// Check if answer is correct
  bool isCorrect(String answer) =>
      answer.trim().toLowerCase() == correctAnswer.trim().toLowerCase();
}

/// Question type enum
enum QuestionType {
  multipleChoice,
  trueFalse,
  fillBlank,
  matching;

  /// Parse from string
  static QuestionType fromString(String value) {
    switch (value.toLowerCase().replaceAll('_', '').replaceAll('-', '')) {
      case 'multiplechoice':
        return QuestionType.multipleChoice;
      case 'truefalse':
        return QuestionType.trueFalse;
      case 'fillblank':
      case 'fillinblank':
        return QuestionType.fillBlank;
      case 'matching':
        return QuestionType.matching;
      default:
        return QuestionType.multipleChoice;
    }
  }

  /// Get display name in Vietnamese
  String get displayName {
    switch (this) {
      case QuestionType.multipleChoice:
        return 'Trắc nghiệm';
      case QuestionType.trueFalse:
        return 'Đúng/Sai';
      case QuestionType.fillBlank:
        return 'Điền vào chỗ trống';
      case QuestionType.matching:
        return 'Nối cặp';
    }
  }
}

/// Quiz data for a motif
@freezed
class Quiz with _$Quiz {
  const factory Quiz({
    required String motifId,
    required String motifName,
    required List<QuizQuestion> questions,
  }) = _Quiz;

  const Quiz._();

  /// Get total number of questions
  int get totalQuestions => questions.length;

  /// Check if quiz has questions
  bool get hasQuestions => questions.isNotEmpty;

  /// Get pass threshold percentage
  static const int passThreshold = 80;
}

/// Quiz answer submitted by user
@freezed
class QuizAnswer with _$QuizAnswer {
  const factory QuizAnswer({
    required String questionId,
    required String answer,
  }) = _QuizAnswer;
}

/// Quiz submission request
@freezed
class QuizSubmission with _$QuizSubmission {
  const factory QuizSubmission({
    required String motifId,
    required List<QuizAnswer> answers,
    int? timeTakenSeconds,
  }) = _QuizSubmission;

  const QuizSubmission._();

  /// Get number of answered questions
  int get answeredCount => answers.length;
}

/// Quiz result after submission
@freezed
class QuizResult with _$QuizResult {
  const factory QuizResult({
    required bool passed,
    required int score,
    required int totalQuestions,
    required int correctAnswers,
    required int percentage,
    @Default(0) int xpEarned,
    @Default(0) int totalXp,
    @Default([]) List<QuizBadge> newBadges,
    @Default(false) bool isNewBest,
  }) = _QuizResult;

  const QuizResult._();

  /// Get number of wrong answers
  int get wrongAnswers => totalQuestions - correctAnswers;

  /// Check if this is a perfect score
  bool get isPerfect => percentage == 100;

  /// Get result message in Vietnamese
  String get resultMessage {
    if (isPerfect) return 'Xuất sắc! Bạn đã trả lời đúng tất cả!';
    if (passed) return 'Tuyệt vời! Bạn đã vượt qua bài trắc nghiệm!';
    return 'Chưa đạt. Hãy ôn lại bài học và thử lại nhé!';
  }

  /// Get result icon (Material Icons) based on performance
  IconData getResultIcon() {
    if (isPerfect) return Icons.emoji_events_rounded;
    if (passed) return Icons.celebration_rounded;
    if (percentage >= 50) return Icons.menu_book_rounded;
    return Icons.fitness_center_rounded;
  }
}

/// Badge earned from quiz
@freezed
class QuizBadge with _$QuizBadge {
  const factory QuizBadge({
    required String id,
    required String slug,
    required String name,
    String? nameEn,
    String? description,
    String? iconUrl,
    required String category,
    @Default(0) int xpBonus,
  }) = _QuizBadge;
}

/// Quiz attempt history entry
@freezed
class QuizAttempt with _$QuizAttempt {
  const factory QuizAttempt({
    required String id,
    required String motifId,
    required int score,
    required int percentage,
    required bool passed,
    required DateTime attemptedAt,
    int? timeTakenSeconds,
  }) = _QuizAttempt;

  const QuizAttempt._();

  /// Format time taken as mm:ss
  String? get formattedTime {
    if (timeTakenSeconds == null) return null;
    final minutes = (timeTakenSeconds! ~/ 60).toString().padLeft(2, '0');
    final seconds = (timeTakenSeconds! % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}
